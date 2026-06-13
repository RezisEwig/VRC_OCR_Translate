<div align="center">

![VRC OCR Translate](assets/vrc-ocr-translate-hero.png)

# VRC OCR Translate

**VRChat 속 일본어와 영어를 읽고, 한국어 번역을 원문 위치에 그대로 띄우는 로컬 AI SteamVR 오버레이**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SteamVR](https://img.shields.io/badge/SteamVR-OpenVR-1A1A1A?logo=steam&logoColor=white)](https://store.steampowered.com/app/250820/SteamVR/)
[![Local AI](https://img.shields.io/badge/Translation-100%25_Local-7C3AED)](#어떻게-동작하나요)
[![License MIT](https://img.shields.io/badge/Code_License-MIT-22C55E)](LICENSE)

API 키도, 번역 서버도 필요 없습니다. VR에서 보이는 문장을 RapidOCR가 찾고 TranslateGemma가 번역하면, 문장이 있던 자리 근처에 한국어 자막이 떠오릅니다.

</div>

## 사용 영상

[![자동 번역, 수동 번역, 자막 위치 조정 시연](assets/vrc-ocr-translate-hero.png)](assets/demo.mp4)

위 이미지를 누르면 약 52초짜리 시연 영상을 볼 수 있습니다. 영상은 **자동 번역 -> 왼쪽 컨트롤러 수동 번역 -> 자막 위치 조정** 순서입니다.

## 이 프로그램이 하는 일

- VRChat 게임 창만 캡처해 다른 데스크톱 창이나 번역 오버레이가 다시 OCR되는 셀프 루프를 피합니다.
- 일본어와 영어를 함께 인식하고 문장별 원래 위치를 유지합니다.
- 겹치는 자막은 가까운 빈 공간으로 옮겨 읽기 좋게 배치합니다.
- 자동 번역과 컨트롤러 기반 수동 번역을 즉시 전환할 수 있습니다.
- OCR, 번역, 캐시, 오버레이가 모두 PC 안에서 동작합니다.
- Papago, DeepL 같은 외부 번역 API와 API 키를 사용하지 않습니다.

## 테스트한 환경

| 항목 | 테스트 환경 |
| --- | --- |
| 헤드셋 | Meta Quest Pro |
| PC VR 연결 | Virtual Desktop |
| VR 런타임 | SteamVR / OpenVR |
| 게임 | VRChat PC 버전 |
| GPU | NVIDIA GeForce RTX 5070 Ti |
| 운영체제 | Windows 11 |
| 번역 모델 | TranslateGemma 4B IT, Q4_K_M GGUF |

Quest Pro + Virtual Desktop 조합에서 집중적으로 만들고 테스트했습니다. 다른 Quest 기기, Steam Link, 유선 PC VR 헤드셋도 OpenVR 입력과 오버레이를 지원하면 동작할 가능성은 있지만 아직 검증하지 않았습니다.

## 필요 사양

정식 최소 사양을 측정한 프로젝트는 아니므로 아래는 현실적인 권장선입니다.

| 구성 | 권장 수준 |
| --- | --- |
| OS | Windows 10/11 64-bit |
| Python | 3.12, `uv`가 자동으로 관리 |
| CPU | 최근 6코어급 이상 권장, RapidOCR는 CPU 사용 |
| RAM | 16GB 이상 권장 |
| GPU | Vulkan 지원 NVIDIA/AMD GPU |
| VRAM | 번역기만 약 3GB 안팎, VRChat까지 함께 쓸 경우 8GB 이상 권장 |
| 저장 공간 | 모델과 런타임을 포함해 약 4GB 여유 공간 |
| VR 환경 | SteamVR와 OpenVR 오버레이 지원 환경 |

GPU가 없어도 이론상 CPU 번역 구성이 가능하지만 현재 실행 스크립트는 Vulkan GPU 가속을 기준으로 만들어졌습니다. 내장 그래픽이나 저사양 GPU에서는 번역 지연과 VR 프레임 저하가 커질 수 있습니다.

## 다운로드와 설치

### 1. 저장소 받기

Git을 사용한다면:

```powershell
git clone https://github.com/RezisEwig/VRC_OCR_Translate.git
cd VRC_OCR_Translate
```

Git이 없다면 GitHub의 **Code -> Download ZIP**으로 내려받고 압축을 풀어도 됩니다.

### 2. uv 설치

PowerShell에서 한 번 실행합니다.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 방법 원문은 [uv 공식 문서](https://docs.astral.sh/uv/getting-started/installation/)에서 확인할 수 있습니다.

### 3. 설정 파일 만들기

```powershell
Copy-Item config.example.json config.json
```

`config.json`은 개인 설정 파일이라 Git에 올라가지 않습니다.

### 4. 로컬 AI 설치

`SETUP_LOCAL_AI.bat`를 실행합니다. 약 2.49GB의 TranslateGemma 모델과 llama.cpp Vulkan 런타임을 내려받고 SHA-256을 검증합니다.

모델은 이 저장소의 MIT 라이선스가 아니라 [Gemma Terms of Use](https://ai.google.dev/gemma/terms)를 따릅니다. 설치 전에 조건을 확인하십시오.

### 5. 실행

1. Virtual Desktop, SteamVR, VRChat을 순서대로 실행합니다.
2. VRChat이 실제 VR 모드로 열린 것을 확인합니다.
3. `RUN_TRANSLATOR.bat`를 실행합니다.
4. 콘솔에 `Positioned translation started`가 나오면 준비 완료입니다.
5. 종료할 때 콘솔에서 `Ctrl+C`를 누릅니다.

필요한 파일이 없다면 `RUN_TRANSLATOR.bat`가 설치 과정도 안내합니다. SteamVR 오버레이만 시험하려면 `TEST_OVERLAY.bat`, 최근 로그를 보려면 `OPEN_LOG.bat`를 사용합니다.

## 키 조작

| 입력 | 동작 |
| --- | --- |
| 왼쪽 컨트롤러 트리거 | 현재 화면을 한 번 번역하고 다음 요청까지 유지 |
| 왼쪽 컨트롤러 그립 | 떠 있는 번역 자막을 모두 삭제 |
| `Ctrl+Alt+T` | 2초 자동 번역 / 수동 번역 모드 전환 |
| `Ctrl+Alt+왼쪽/오른쪽` | 모든 자막을 좌우로 이동 |
| `Ctrl+Alt+위/아래` | 모든 자막을 위아래로 이동 |
| `Ctrl+Alt+숫자패드 + / -` | 화면 중심을 기준으로 자막 좌표 배율 조정 |
| `Ctrl+Alt+Home` | 위치와 배율을 기본값으로 초기화 |

수동 모드에서는 평소 OCR와 번역을 쉬게 둡니다. 위치 조정 키를 누르는 동안만 결과를 확인하기 쉽도록 최대 1초 간격으로 다시 번역합니다. 보정값은 즉시 `config.json`에 저장됩니다.

## 어떻게 동작하나요

```text
VRChat Unity 게임 창 (Windows Graphics Capture)
  -> 화면 변화 감지
  -> RapidOCR (CPU, 일본어/영어와 좌표 인식)
  -> 같은 줄의 OCR 조각 병합
  -> TranslateGemma 4B Q4 (Vulkan GPU)
  -> 위치 기반 투명 자막 텍스처 생성
  -> OpenVR Overlay
  -> Quest Pro
```

`vrchat_window` 캡처는 제목이 `VRChat`, 클래스가 `UnityWndClass`인 게임 창의 클라이언트 영역만 읽습니다. 최소화된 창은 포커스를 빼앗지 않고 복원하며 프로그램 종료 시 원래 상태로 돌려놓습니다.

## 주요 설정

`config.example.json`에서 전체 기본값을 볼 수 있습니다.

| 설정 | 설명 |
| --- | --- |
| `capture.interval_ms` | 자동 모드 캡처 주기, 기본 2000ms |
| `capture.change_threshold` | 화면 변화 감도 |
| `controls.start_mode` | `automatic` 또는 `manual` |
| `ocr.confidence_threshold` | OCR 최소 신뢰도 |
| `ocr.languages` | 기본 `ja`, `en` |
| `ocr.line_max_gap_ratio` | 같은 줄로 합칠 최대 가로 간격 |
| `translation.local_max_tokens` | 번역 한 건의 최대 출력 토큰 |
| `overlay.background_alpha` | 자막 배경 투명도 |
| `overlay.position_offset_x_ratio` | HMD/미러 화면 가로 오프셋 |
| `overlay.position_offset_y_ratio` | HMD/미러 화면 세로 오프셋 |
| `overlay.collision_gap_px` | 겹침 방지용 자막 간격 |

## VR 최종 화면 녹화

`PREPARE_RECORDING.bat`를 실행하고 SteamVR 메뉴에서 **VR 뷰 표시**를 선택한 다음, OBS에 `VR View` 창을 **창 캡처**로 추가합니다. VRChat 데스크톱 창이 아니라 SteamVR 최종 합성 화면을 잡아야 한국어 오버레이까지 함께 녹화됩니다.

자세한 OBS 설정은 [RECORDING.md](RECORDING.md)에 정리되어 있습니다.

## 로그와 문제 확인

- `logs/vrc-ocr-translate.log`: 캡처, OCR, 번역 시간, 검출 영역, 자막 좌표
- `logs/llama-server.log`: llama.cpp 모델 로드와 Vulkan GPU 로그
- `CHECK_LOCAL_AI.bat`: 모델, RapidOCR, GPU 번역 준비 상태 확인
- `OPEN_LOG.bat`: 최근 애플리케이션 로그 열기

```powershell
uv run vrc-ocr-translate --config config.json --check-local
uv run vrc-ocr-translate --config config.json --capture-preview capture-preview.png
uv run vrc-ocr-translate --config config.json --ocr-image capture-preview.png
uv run vrc-ocr-translate --config config.json --translate-image capture-preview.png
```

## 제약사항

- Quest Pro + Virtual Desktop + SteamVR에서만 실사용 테스트했습니다.
- 자막 좌표는 VR 월드의 3D 표면 좌표가 아니라 VRChat 미러 화면의 2D 좌표입니다.
- 머리를 크게 움직이면 화면 전체가 변해 자동 모드 OCR가 자주 실행될 수 있습니다.
- 세로쓰기, 장식 글꼴, 흐리거나 작은 글자, OCR가 놓친 문장은 번역할 수 없습니다.
- TranslateGemma 4B는 가볍고 빠른 대신 문맥이 긴 대화나 고유명사에서 오역할 수 있습니다.
- Quest Pro 시선 추적 기반 관심 영역 번역은 아직 구현하지 않았습니다.
- SteamVR/OpenVR 입력 바인딩이 다른 컨트롤러에서는 수동 버튼이 바로 동작하지 않을 수 있습니다.
- VRChat, SteamVR, Virtual Desktop, Meta와 제휴하거나 공식 승인을 받은 프로젝트가 아닙니다.

## 라이선스

이 저장소의 자체 코드와 문서는 [MIT License](LICENSE)로 사용할 수 있습니다.

TranslateGemma 모델은 별도의 [Gemma Terms of Use](https://ai.google.dev/gemma/terms)를 따르며 저장소에 포함되지 않습니다. llama.cpp, RapidOCR, OpenVR 등 제3자 구성 요소의 라이선스는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에서 확인할 수 있습니다.

## 이 레포를 만든 방식

이 저장소의 **코드, 스크립트, 테스트, 문서는 OpenAI Codex가 100% 작성했습니다.** RezisEwig는 아이디어와 요구사항을 제시하고, Quest Pro를 직접 쓰면서 실제 VR 테스트와 피드백을 담당했습니다. 로고와 공개용 영상 편집 구성도 Codex와 함께 만들었습니다.

사람이 VR 안에서 실제로 불편했던 지점을 말하고, AI가 코드를 만들고, 다시 VR에서 바로 검증하는 방식으로 완성한 작은 실험입니다. 아직 거칠 수 있지만 누군가의 VR 생활을 조금 더 편하게 만든다면 이 프로젝트는 이미 제 몫을 한 셈입니다.

구조와 구현 배경이 궁금하다면 [DESIGN.md](DESIGN.md)를 읽어보세요. 문제를 발견했다면 재현 환경과 로그를 담아 GitHub Issue로 알려주세요.
