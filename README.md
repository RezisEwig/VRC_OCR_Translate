<div align="center">

![VRC OCR Translate](assets/vrc-ocr-translate-hero.png)

# VRC OCR Translate

**VRChat 속 일본어와 영어를 읽어서, 그 자리에 한국어 자막을 띄워주는 로컬 AI 도구입니다.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SteamVR](https://img.shields.io/badge/SteamVR-OpenVR-1A1A1A?logo=steam&logoColor=white)](https://store.steampowered.com/app/250820/SteamVR/)
[![Local AI](https://img.shields.io/badge/Translation-Local_AI-7C3AED)](#-어떻게-작동하나요)
[![MIT License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)

API 키도, 번역 서버도 필요 없습니다. 번역은 전부 내 PC에서 돌아갑니다. ✨

</div>

## 🎬 사용 영상

[![자동 번역, 수동 번역, 자막 위치 조정 미리보기](assets/demo-preview.gif)](assets/demo.mp4)

GIF는 README에서 바로 재생되는 짧은 미리보기입니다. **이미지를 누르면 1080p 전체 영상**을 볼 수 있습니다.

시연 순서는 `자동 번역` → `수동 번역` → `자막 위치 조정`입니다.

## 🌟 이런 프로그램이에요

- 일본어와 영어를 찾아 한국어로 번역합니다.
- 번역문을 원문이 있던 위치 근처에 띄웁니다.
- 자막끼리 겹치면 읽기 편한 빈 공간으로 살짝 이동합니다.
- 2초마다 확인하는 자동 모드와 컨트롤러로 요청하는 수동 모드를 지원합니다.
- 실행하면 작은 컨트롤 패널이 떠서 버튼으로도 조작할 수 있습니다.
- VRChat 게임 창만 읽기 때문에 바탕화면이나 번역 자막이 다시 번역되는 일을 막습니다.
- Papago나 DeepL 같은 외부 API를 사용하지 않습니다. 🔒

## 🚀 정말 쉬운 설치

PowerShell 명령어나 Python 설치 방법을 몰라도 괜찮습니다.

1. GitHub 위쪽의 **Code → Download ZIP**을 누릅니다.
2. 받은 ZIP 파일의 압축을 풉니다.
3. 폴더 안의 **`INSTALL.bat`을 더블클릭**합니다.
4. 설치가 끝나면 Virtual Desktop, SteamVR, VRChat을 실행합니다.
5. **`RUN_TRANSLATOR.bat`을 더블클릭**합니다.

첫 설치에는 약 3GB를 내려받으므로 시간이 조금 걸릴 수 있습니다. `INSTALL.bat`이 아래 작업을 알아서 처리합니다.

- 프로젝트 전용 실행 도구 설치
- Python 3.12와 필요한 패키지 준비
- 개인 설정 파일 `config.json` 생성
- TranslateGemma 모델과 llama.cpp Vulkan 런타임 다운로드
- 모델 파일 무결성 확인

설치 중 문제가 생기면 인터넷 연결을 확인한 뒤 `INSTALL.bat`을 다시 실행해 주세요.

<details>
<summary>Git으로 받고 싶은 사용자</summary>

```text
git clone https://github.com/RezisEwig/VRC_OCR_Translate.git
cd VRC_OCR_Translate
```

그다음 `INSTALL.bat`을 실행하면 됩니다.

</details>

## 🎮 조작법

`RUN_TRANSLATOR.bat`을 실행하면 작은 컨트롤 패널이 함께 열립니다. 여기서 **자동/수동 전환**, **한 번 번역**, **자막 지우기**, **자막 위치 조정**, **배율 조정**을 버튼으로 누를 수 있습니다.

| 입력 | 동작 |
| --- | --- |
| 왼쪽 컨트롤러 트리거 | 지금 보고 있는 화면을 한 번 번역하고 유지 |
| 왼쪽 컨트롤러 그립 | 떠 있는 번역 자막 모두 지우기 |
| `Ctrl+Alt+T` | 자동 번역 ↔ 수동 번역 전환 |
| `Ctrl+Alt+왼쪽/오른쪽` | 자막 전체를 좌우로 이동 |
| `Ctrl+Alt+위/아래` | 자막 전체를 위아래로 이동 |
| `Ctrl+Alt+숫자패드 + / -` | 자막 위치의 가로·세로 배율 조정 |
| `Ctrl+Alt+Home` | 자막 위치와 배율 초기화 |

위치 조정값은 `config.json`에 자동 저장됩니다. 한 번 눈에 맞게 조절해 두면 다음 실행에도 그대로 유지됩니다. 👍

트리거와 그립 입력은 가로채지 않고 읽기만 합니다. 따라서 번역을 요청하거나 자막을 지우는 동시에 VRChat 안에서도 기존 트리거·그립 동작이 그대로 실행됩니다.

컨트롤 패널이 필요 없다면 `config.json`에서 `controls.show_panel`을 `false`로 바꾸면 됩니다.

## 🖥️ 테스트 환경과 권장 사양

| 항목 | 내용 |
| --- | --- |
| 테스트한 헤드셋 | Meta Quest Pro |
| PC 연결 | Virtual Desktop |
| VR 환경 | SteamVR / OpenVR |
| 테스트 GPU | NVIDIA GeForce RTX 5070 Ti |
| 운영체제 | Windows 11 |
| RAM | 16GB 이상 권장 |
| VRAM | 8GB 이상 권장 |
| 저장 공간 | 약 4GB 여유 공간 |

RapidOCR는 CPU를 사용하고 TranslateGemma 번역은 Vulkan GPU를 사용합니다. 번역기 자체는 VRAM을 약 3GB 안팎 사용하지만 VRChat과 함께 실행해야 하므로 여유 있는 GPU가 좋습니다.

## ⚠️ 알아둘 점

- 현재 **Quest Pro + Virtual Desktop + SteamVR** 조합에서만 실사용 테스트했습니다.
- 다른 Quest 기기, Steam Link, 유선 PC VR에서도 동작할 가능성은 있지만 아직 확인하지 못했습니다.
- 자막은 VR 월드의 실제 3D 표면이 아니라 눈에 보이는 2D 화면 위치를 기준으로 붙습니다.
- 세로쓰기, 장식 글꼴, 너무 작거나 흐린 글자는 놓칠 수 있습니다.
- 로컬 4B 모델이라 긴 문맥, 고유명사, 복잡한 문장은 가끔 엉뚱하게 번역할 수 있습니다.
- Quest Pro 시선 추적 번역은 아직 구현되지 않았습니다.
- VRChat, SteamVR, Virtual Desktop, Meta의 공식 프로젝트가 아닙니다.

## 🧩 어떻게 작동하나요

간단히 말하면 이렇습니다.

```text
VRChat 화면
  → RapidOCR가 글자와 위치 찾기
  → TranslateGemma가 한국어로 번역
  → SteamVR 위에 번역 자막 표시
```

조금 더 깊은 구조가 궁금하다면 [DESIGN.md](DESIGN.md)를 참고해 주세요.

<details>
<summary>설정과 진단 기능 보기</summary>

- `CHECK_LOCAL_AI.bat`: OCR와 GPU 번역 준비 상태 확인
- `TEST_OVERLAY.bat`: SteamVR 자막 표시만 테스트
- `OPEN_LOG.bat`: 최근 실행 로그 열기
- `config.example.json`: 바꿀 수 있는 전체 설정 예시

자주 조정하는 값:

- `capture.interval_ms`: 자동 번역 주기, 기본 2000ms
- `ocr.confidence_threshold`: OCR 최소 신뢰도
- `ocr.languages`: 인식할 언어, 기본 일본어와 영어
- `overlay.background_alpha`: 자막 배경 투명도
- `overlay.collision_gap_px`: 자막끼리 떨어질 간격
- `controls.show_panel`: 데스크톱 컨트롤 패널 표시 여부

</details>

## 📜 라이선스

이 저장소의 코드와 문서는 [MIT License](LICENSE)로 공개됩니다.

TranslateGemma 모델은 별도의 [Gemma Terms of Use](https://ai.google.dev/gemma/terms)를 따릅니다. llama.cpp, RapidOCR, OpenVR 등 외부 구성 요소의 라이선스는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 정리했습니다.

## 🤖 이 레포를 만든 방식

이 저장소의 **코드, 스크립트, 테스트, 문서는 OpenAI Codex가 100% 작성했습니다.**

RezisEwig는 아이디어와 요구사항을 제시하고 Quest Pro 안에서 직접 테스트하며 피드백을 담당했습니다. 사람이 VR에서 느낀 불편을 이야기하고, AI가 구현하고, 다시 실제 VR에서 확인하는 방식으로 함께 완성한 프로젝트입니다.

버그를 발견했다면 사용 중인 헤드셋, 연결 방식, GPU와 함께 GitHub Issue에 알려주세요. 더 많은 VR 환경에서 잘 돌아가도록 만드는 데 큰 도움이 됩니다! 🙌
