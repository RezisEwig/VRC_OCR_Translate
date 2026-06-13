# Third-party notices

VRC OCR Translate의 자체 코드는 [MIT License](LICENSE)로 배포됩니다. 설치 과정에서 내려받거나 Python 패키지로 설치되는 구성 요소는 각각의 라이선스를 따릅니다.

## AI model

- [TranslateGemma 4B](https://huggingface.co/google/translategemma-4b-it): Gemma Terms of Use
- [GGUF quantization by mradermacher](https://huggingface.co/mradermacher/translategemma-4b-it-GGUF): Gemma license, based on `google/translategemma-4b-it`

모델 파일은 이 저장소에 포함되지 않으며 `SETUP_LOCAL_AI.bat` 실행 시 별도로 다운로드됩니다. 모델을 사용하면 [Google Gemma Terms of Use](https://ai.google.dev/gemma/terms)에 동의하고 이를 준수할 책임이 사용자에게 있습니다.

## Runtime and libraries

- [llama.cpp](https://github.com/ggml-org/llama.cpp): MIT
- [RapidOCR](https://github.com/RapidAI/RapidOCR): Apache-2.0
- [OpenVR SDK](https://github.com/ValveSoftware/openvr): BSD-3-Clause
- [windows-capture](https://github.com/NiiightmareXD/windows-capture): MIT
- [ONNX Runtime](https://github.com/microsoft/onnxruntime): MIT
- [NumPy](https://github.com/numpy/numpy): BSD-3-Clause
- [Pillow](https://github.com/python-pillow/Pillow): HPND
- [Requests](https://github.com/psf/requests): Apache-2.0
- [python-mss](https://github.com/BoboTiG/python-mss): MIT

전체 전이 의존성과 정확한 버전은 `uv.lock`에 기록되어 있습니다. 재배포 시 각 패키지 배포본에 포함된 라이선스 문서도 함께 확인하십시오.
