# VRChat 로컬 OCR 번역 오버레이 설계

## 목표

Meta Quest Pro를 Virtual Desktop과 SteamVR로 PC에 연결한 환경에서 VRChat 미러 화면의 일본어를 찾고, 각 원문 위치에 가까운 한국어 번역 상자를 OpenVR 오버레이로 표시한다. VRChat 프로세스나 월드 파일은 수정하지 않는다.

## 구현 구조

```text
Windows Graphics Capture (VRChat Unity HWND client area)
  -> FrameChangeDetector
  -> RapidJapaneseOcr (ONNX Runtime CPU)
  -> OcrRegion(text, confidence, BoundingBox)
  -> group_ocr_lines (DBSCAN min_samples=1)
  -> TranslateGemmaTranslator
       -> persistent llama-server sidecar
       -> GGUF Q4_K_M
       -> Vulkan / RTX 5070 Ti
       -> source text LRU cache
  -> TranslationBlock(source, target, bounds)
  -> PositionedTranslationRenderer
  -> SteamVROverlay
```

OpenVR 액션 매니페스트는 왼손 트리거를 1회 번역, 왼손 그립을 오버레이 삭제에 연결한다. 메인 루프는 컨트롤러 입력을 짧은 주기로 확인하지만 자동 OCR/번역은 `capture.interval_ms` 간격과 화면 변화 조건을 만족할 때만 실행한다. `Ctrl+Alt+T`로 자동/수동 모드를 전환하며, 수동 모드의 위치 보정 중에는 최대 1초 간격으로 강제 번역한다.

현재 코어와 사이드카 제어는 모두 Python으로 구현했다. C# 코어로 분리하면 Direct3D 공유 텍스처와 더 낮은 복사 비용을 얻을 수 있지만, 현재 환경에는 .NET SDK가 없고 기존 Python/OpenVR 코드가 동작하므로 우선 기능과 지연 시간을 검증하는 구조를 선택했다.

## OCR

RapidOCR의 PP-OCRv4 모바일 검출 모델과 일본어 인식 모델을 ONNX Runtime CPU에서 실행한다. 일본어 인식 모델은 영문도 인식하므로 `ocr.languages` 필터로 일본어와 영어를 함께 허용한다. 입력이 `ocr.max_dimension`보다 크면 축소하고, 검출 좌표는 원래 캡처 크기로 복원한다.

필터 조건은 다음과 같다.

- 신뢰도가 `ocr.confidence_threshold` 이상
- `ocr.languages`에 설정된 일본어 또는 영어가 포함
- 복원된 경계 상자의 폭과 높이가 2픽셀 이상

## 라인 그룹핑

OCR 엔진이 한 줄을 여러 단어 상자로 나눌 수 있으므로 DBSCAN과 같은 연결 확장을 사용한다. `min_samples=1`이라 고립된 상자는 독립적인 한 줄로 남는다.

두 상자는 아래 조건을 모두 만족할 때만 이웃이다.

- 세로 중심 차이가 글자 높이의 `line_cluster_eps` 이내
- 세로 영역이 최소 20% 이상 겹침
- 가로 간격이 글자 높이의 `line_max_gap_ratio` 이내

서로 다른 줄은 블록으로 다시 합치지 않는다. 따라서 화면 여러 위치의 글자가 하나의 큰 번역 상자로 합쳐지는 현상을 피한다.

## 로컬 번역

- 모델: `TranslateGemma 4B IT`, GGUF `Q4_K_M`
- 런타임: 공식 llama.cpp Windows Vulkan 빌드
- GPU: Vulkan 장치 0, 단일 GPU, 모든 레이어 오프로딩
- 서버: `127.0.0.1:18765`, 앱 실행 중에만 유지
- 요청: TranslateGemma 공식 일본어→한국어 지시문을 `/completion`에 전달
- 캐시: 정규화된 원문 기준 LRU 512개

문자 구성에 따라 일본어, 영어, 일·영 혼합 입력을 판별하고 해당 설명을 TranslateGemma 프롬프트에 넣는다. 혼합 문장은 영문 부분까지 포함해 전체를 한국어로 번역하도록 지시한다.

첫 실행에는 Vulkan 셰이더 캐시 생성이 필요할 수 있다. 검증 환경에서는 캐시 생성 후 짧은 문장 번역이 약 0.13~0.17초, RapidOCR가 약 0.19~0.22초였다.

## 렌더링

각 `TranslationBlock.bounds` 중심에 반투명 한국어 상자를 그린다. 전체 결과는 캡처와 같은 크기의 투명 RGBA 이미지이며 OpenVR `SetOverlayRaw`로 전달한다. 이 좌표는 화면 기준 2D 좌표이므로 월드 오브젝트 표면에 고정되는 3D 앵커는 아니다.

모든 상자의 크기를 먼저 계산하고, 원문 중심에서 가까운 순서로 화면 후보 좌표를 검사한다. 이미 배치한 상자와 `collision_gap_px` 간격을 확보하는 첫 위치를 사용하며, 빈 공간이 전혀 없으면 겹침 면적이 가장 작은 위치를 선택한다.

VRChat 데스크톱 렌더와 HMD 실제 시야 중심이 다를 수 있으므로, 원본 중심 좌표에 `position_scale_x/y`를 적용한 뒤 `position_offset_x/y_ratio`를 더한다. 실행 중 `Ctrl+Alt` 보정 단축키로 값을 변경하며 `config.json`에 즉시 저장한다. 캡처는 VRChat의 HWND만 대상으로 하므로 OpenVR 오버레이는 입력 프레임에 포함되지 않는다.

## 장애 격리와 로그

- OCR 또는 개별 번역 실패는 해당 블록만 건너뛴다.
- 모델 서버가 시작되지 않으면 앱 시작을 중단하고 `logs/llama-server.log`를 안내한다.
- 콘솔과 `logs/vrc-ocr-translate.log`에 단계별 처리 시간을 기록한다.
- 모델과 런타임은 `SETUP_LOCAL_AI.bat`에서 크기 및 SHA-256을 검증한다.

## Quest Pro 시선 추적 확장

Virtual Desktop이 노출하는 Quest Pro 시선 데이터를 안정적으로 읽을 수 있으면 다음 단계로 관심 영역(ROI)을 적용할 수 있다.

1. 시선 방향을 미러 화면 좌표로 투영한다.
2. 시선 주변 영역만 고해상도 OCR한다.
3. 주변부는 낮은 빈도로 전체 OCR해 놓친 문구를 보완한다.
4. 시선이 일정 시간 머문 블록의 번역 우선순위를 높인다.

시선 좌표계와 SteamVR 미러 투영의 보정이 필요하므로, 현재 구현에는 잘못된 ROI로 글자를 누락시키지 않도록 포함하지 않았다.
