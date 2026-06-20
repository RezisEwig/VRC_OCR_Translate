# VRChat 로컬 OCR 번역 오버레이 설계

## 목표

Meta Quest Pro를 Virtual Desktop과 SteamVR로 PC에 연결한 환경에서 VRChat 화면의 여러 언어를 찾고, 각 원문 위치에 가까운 사용자 선택 언어 번역 상자를 OpenVR 오버레이로 표시한다. VRChat 프로세스나 월드 파일은 수정하지 않는다.

## 구현 구조

```text
Windows Graphics Capture (VRChat Unity HWND client area)
  -> FrameChangeDetector
  -> RapidMultilingualOcr (PP-OCRv5 / ONNX Runtime CPU)
       -> one text detection pass
       -> japanese + east_asia + korean + latin recognition packs
  -> OcrRegion(text, confidence, BoundingBox)
  -> group_ocr_lines (DBSCAN min_samples=1)
  -> TranslateGemmaTranslator
       -> persistent llama-server sidecar
       -> GGUF Q4_K_M
       -> Vulkan / RTX 5070 Ti
       -> target language + source text LRU cache
  -> TranslationBlock(source, target, bounds)
  -> PositionedTranslationRenderer
  -> SteamVROverlay
```

OpenVR 액션 매니페스트는 왼손 트리거를 1회 번역, 왼손 그립을 오버레이 삭제에 연결한다. 메인 루프는 컨트롤러 입력을 짧은 주기로 확인하지만 자동 OCR/번역은 `capture.interval_ms` 간격과 화면 변화 조건을 만족할 때만 실행한다. `Ctrl+Alt+T`로 자동/수동 모드를 전환하며, 수동 모드의 위치 보정 중에는 최대 1초 간격으로 강제 번역한다.

현재 코어와 사이드카 제어는 모두 Python으로 구현했다. C# 코어로 분리하면 Direct3D 공유 텍스처와 더 낮은 복사 비용을 얻을 수 있지만, 현재 환경에는 .NET SDK가 없고 기존 Python/OpenVR 코드가 동작하므로 우선 기능과 지연 시간을 검증하는 구조를 선택했다.

## OCR

RapidOCR의 모바일 모델을 ONNX Runtime CPU에서 실행한다. 한 프레임에서 글자 위치는 PP-OCRv5로 한 번만 검출한 뒤 같은 잘라낸 영역을 일본어 전용 PP-OCRv4, 동아시아·한국어·라틴 PP-OCRv5 인식 모델에 배치로 전달한다. 각 결과의 신뢰도와 실제 문자 구성을 함께 점수화해 가장 알맞은 결과를 선택한다. 입력이 `ocr.max_dimension`보다 크면 축소하고, 검출 좌표는 원래 캡처 크기로 복원한다.

`translation.source_language`가 `auto`이면 네 인식 결과를 비교한다. 특정 언어를 선택하면 해당 언어에 필요한 인식기만 실행한다. 일본어는 전용 모델, 중국어는 동아시아 모델, 한국어는 한국어 모델, 영어·스페인어·프랑스어·독일어·포르투갈어·이탈리아어는 라틴 모델을 공유한다. 라틴 문자 언어끼리는 OCR 단계에서 완전히 구분할 수 없으므로 사용자의 선택을 TranslateGemma 프롬프트에 정확한 원문 언어로 전달한다.

필터 조건은 다음과 같다.

- 신뢰도가 `ocr.confidence_threshold` 이상
- 자동 감지 대상인 한글, 가나, 한자 또는 라틴 문자가 포함
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
- 요청: 자동 감지한 원문 전체를 사용자가 고른 언어로 번역하도록 `/completion`에 전달
- 캐시: 대상 언어와 정규화된 원문 기준 LRU 512개

현재 목표 언어는 한국어, 일본어, 간체/번체 중국어, 영어, 스페인어, 프랑스어, 독일어, 포르투갈어, 이탈리아어다. 원문의 정확한 언어는 TranslateGemma가 자동 판단하며, 여러 언어가 섞인 문장도 빠뜨리지 않고 전체를 번역하도록 지시한다. 목표 언어 변경 시 이전 번역 캐시를 비우고 자막 폰트를 해당 문자권에 맞게 다시 선택한다.

첫 실행에는 Vulkan 셰이더 캐시 생성이 필요할 수 있다. 검증 환경에서는 캐시 생성 후 짧은 문장 번역이 약 0.13~0.17초, RapidOCR가 약 0.19~0.22초였다.

## 렌더링

각 `TranslationBlock.bounds` 중심에 반투명 번역 상자를 그린다. 전체 결과는 캡처와 같은 크기의 투명 RGBA 이미지이며 OpenVR `SetOverlayRaw`로 전달한다. 이 좌표는 화면 기준 2D 좌표이므로 월드 오브젝트 표면에 고정되는 3D 앵커는 아니다.

## 컨트롤 패널과 언어 설정

컨트롤 패널은 결과 언어와 원문 언어를 별도 드롭다운으로 보여준다. 결과 언어 선택은 TranslateGemma의 목표 언어, 자막 폰트, 패널의 모든 버튼과 상태 문구를 함께 전환한다. 원문 언어 선택은 자동 감지 또는 10개 개별 언어 중 하나이며 OCR 인식기와 번역 프롬프트를 함께 전환한다. 두 값은 `config.json`의 `translation.target_language`와 `translation.source_language`에 즉시 저장된다.

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
