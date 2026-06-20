from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

from .config import TranslationConfig
from .languages import (
    AUTO_SOURCE_LANGUAGE,
    get_language,
    normalize_language_code,
    normalize_source_language,
)
from .stability import TranslationCache
from .text import (
    contains_japanese_kana,
    normalize_text,
    source_language_description,
)

LOGGER = logging.getLogger(__name__)


class LlamaServer:
    def __init__(self, config: TranslationConfig) -> None:
        self._config = config
        self._process: subprocess.Popen[str] | None = None
        self._log_file: Any = None
        self._owns_process = False

    @property
    def base_url(self) -> str:
        return f"http://{self._config.local_server_host}:{self._config.local_server_port}"

    def start(self) -> None:
        executable = Path(self._config.local_server_executable).resolve()
        model = Path(self._config.local_model_path).resolve()
        if not executable.exists():
            raise FileNotFoundError(
                f"llama-server was not found: {executable}. Run SETUP_LOCAL_AI.bat."
            )
        if not model.exists():
            raise FileNotFoundError(
                f"TranslateGemma model was not found: {model}. Run SETUP_LOCAL_AI.bat."
            )
        try:
            response = requests.get(f"{self.base_url}/health", timeout=0.5)
        except requests.RequestException:
            pass
        else:
            if response.ok and response.json().get("status") == "ok":
                LOGGER.info("Reusing existing TranslateGemma server: %s", self.base_url)
                self._owns_process = False
                return
            raise RuntimeError(f"Port {self._config.local_server_port} is already in use")

        log_path = Path("logs/llama-server.log")
        log_path.parent.mkdir(exist_ok=True)
        self._log_file = log_path.open("a", encoding="utf-8")
        command = [
            str(executable),
            "-m",
            str(model),
            "-ngl",
            self._config.local_gpu_layers,
            "--ctx-size",
            str(self._config.local_context_size),
            "--parallel",
            "1",
            "--cache-ram",
            "256",
            "--split-mode",
            "none",
            "--main-gpu",
            "0",
            "--host",
            self._config.local_server_host,
            "--port",
            str(self._config.local_server_port),
            "--no-jinja",
            "--chat-template",
            "chatml",
        ]
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        started = time.monotonic()
        self._process = subprocess.Popen(
            command,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creation_flags,
        )
        self._owns_process = True
        deadline = started + self._config.local_startup_timeout_seconds
        try:
            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    raise RuntimeError(
                        "llama-server exited during startup. Check logs/llama-server.log"
                    )
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=0.5)
                    if response.ok and response.json().get("status") == "ok":
                        LOGGER.info(
                            "TranslateGemma Vulkan server ready in %.2fs: %s",
                            time.monotonic() - started,
                            model.name,
                        )
                        return
                except (requests.RequestException, ValueError):
                    pass
                time.sleep(0.2)
            raise TimeoutError("Timed out waiting for llama-server to start")
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._owns_process and self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        self._process = None
        self._owns_process = False
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

    def __enter__(self) -> "LlamaServer":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class TranslateGemmaTranslator:
    def __init__(
        self,
        config: TranslationConfig,
        server: LlamaServer,
        session: requests.Session | None = None,
    ) -> None:
        self._config = config
        self._server = server
        self._session = session or requests.Session()
        self._cache = TranslationCache(config.local_cache_capacity)

    def translate(self, source_text: str) -> str:
        source = normalize_text(source_text)
        target_language = normalize_language_code(self._config.target_language)
        source_language = normalize_source_language(self._config.source_language)
        cache_key = f"{source_language}\0{target_language}\0{source}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            LOGGER.debug("Translation cache hit: %s", source)
            return cached

        prompt = build_translation_prompt(
            source,
            self._config.source_languages,
            target_language,
            source_language,
        )
        started = time.monotonic()
        response = self._session.post(
            f"{self._server.base_url}/completion",
            json={
                "prompt": prompt,
                "n_predict": self._config.local_max_tokens,
                "temperature": 0,
                "stop": ["<end_of_turn>"],
                "cache_prompt": True,
            },
            timeout=self._config.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        raw_content = str(payload.get("content", ""))
        translated = normalize_text(raw_content.split("<end_of_turn>", 1)[0])
        if not translated:
            raise RuntimeError("TranslateGemma returned an empty translation")
        self._cache.put(cache_key, translated)
        LOGGER.info(
            "TranslateGemma: %.3fs source=%s target=%s",
            time.monotonic() - started,
            source,
            translated,
        )
        return translated

    def set_target_language(self, language_code: str) -> None:
        normalized = normalize_language_code(language_code)
        if normalized == self._config.target_language:
            return
        self._config.target_language = normalized
        self._cache.clear()
        LOGGER.info("Translation target changed: %s", normalized)

    def set_source_language(self, language_code: str) -> None:
        normalized = normalize_source_language(language_code)
        if normalized == self._config.source_language:
            return
        self._config.source_language = normalized
        self._cache.clear()
        LOGGER.info("Translation source changed: %s", normalized)


def build_translation_prompt(
    source_text: str,
    source_languages: list[str] | None = None,
    target_language: str = "ko",
    source_language: str = AUTO_SOURCE_LANGUAGE,
) -> str:
    target = get_language(target_language)
    normalized_source = normalize_source_language(source_language)
    if target.code == "ko" and normalized_source != "ko":
        if normalized_source != AUTO_SOURCE_LANGUAGE:
            return _build_korean_translation_prompt(
                source_text,
                get_language(normalized_source).english_name,
            )
        if contains_japanese_kana(source_text):
            return _build_korean_translation_prompt(source_text, "Japanese")

    if normalized_source == AUTO_SOURCE_LANGUAGE:
        source_description = source_language_description(
            source_text, source_languages or ["JA", "EN"]
        )
        source_instruction = (
            f"The source is {source_description}; detect its exact language "
            "automatically. "
        )
    else:
        source = get_language(normalized_source)
        source_instruction = f"The source language is {source.english_name}. "
    return (
        "<start_of_turn>user\n"
        f"You are a professional translator into {target.english_name}. "
        f"{source_instruction}"
        "Translate the complete text, including words embedded in another language. "
        "Preserve proper names only when they should not be translated. If the source "
        f"is already {target.english_name}, reproduce it unchanged. Accurately convey "
        f"the meaning while following natural {target.english_name} grammar.\n"
        f"Produce only the {target.english_name} translation without explanations or "
        f"commentary. Translate the following text into {target.english_name}:\n\n\n"
        f"{source_text}<end_of_turn>\n<start_of_turn>model\n"
    )


def _build_korean_translation_prompt(source_text: str, source_name: str) -> str:
    if source_name == "Japanese":
        return (
            "<start_of_turn>user\n"
            "You are a professional Japanese to Korean translator. "
            "Translate the complete text, including any English embedded in Japanese "
            "sentences. Preserve proper names only when they should not be translated. "
            "Accurately convey the meaning and nuances while following Korean grammar.\n"
            "Produce only the Korean translation, without any additional explanations or "
            "commentary. Translate the following Japanese text into Korean:\n\n\n"
            f"{source_text}<end_of_turn>\n<start_of_turn>model\n"
        )
    return (
        "<start_of_turn>user\n"
        f"You are a professional {source_name} to Korean translator. "
        "Translate the complete text, including any words from another language "
        f"embedded in the {source_name} text. Preserve proper names only when they "
        "should not be translated. Accurately convey the meaning and nuances while "
        "following natural Korean grammar.\n"
        "Produce only the Korean translation without explanations or commentary. "
        f"Translate the following {source_name} text into Korean:\n\n\n"
        f"{source_text}<end_of_turn>\n<start_of_turn>model\n"
    )
