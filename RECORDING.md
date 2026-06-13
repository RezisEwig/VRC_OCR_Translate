# VR 최종 화면 녹화

VRChat 데스크톱 창이 아니라 SteamVR의 **VR View**를 녹화해야 합니다. VR View는 SteamVR이 최종 합성한 눈 화면이므로 게임과 한국어 번역 오버레이가 함께 표시됩니다.

## 빠른 설정

1. Virtual Desktop, SteamVR, VRChat, `RUN_TRANSLATOR.bat`를 실행합니다.
2. `PREPARE_RECORDING.bat`를 실행합니다.
3. SteamVR 상태 창만 열리면 메뉴에서 **VR 뷰 표시**(`Display VR View`)를 선택합니다.
4. VR View 메뉴에서 **왼쪽 눈** 또는 **양쪽 눈 - 왼쪽 우선**을 선택합니다.
5. OBS Studio에서 **소스 추가 > 창 캡처**를 선택하고 `VR View` 창을 지정합니다.
6. 마우스 커서 캡처를 끄고 소스를 화면에 맞춘 뒤 녹화를 시작합니다.

RTX 5070 Ti 권장 OBS 출력 설정:

- 해상도: 1920x1080
- FPS: 60, VR View 자체가 30 FPS라면 30
- 인코더: NVIDIA NVENC H.264 또는 AV1
- 녹화 형식: MKV 또는 Hybrid MP4
- 품질: High Quality, CQP 18-22

## 주의 사항

- `VRChat.exe` 창만 캡처하면 SteamVR 번역 오버레이가 녹화되지 않습니다.
- 모니터 전체 캡처는 다른 창과 알림이 노출될 수 있습니다.
- Meta/Oculus 계열 스트리밍 헤드셋에서는 SteamVR VR View가 낮은 프레임률로 표시될 수 있지만 번역 오버레이는 포함됩니다.
- 오래된 OBS OpenVR Capture 플러그인은 2020년 이후 유지보수가 중단되어 최신 SteamVR에서 검은 화면이 발생할 수 있으므로 기본 방법으로 사용하지 않습니다.
