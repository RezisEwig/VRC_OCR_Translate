from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path


def _enable_vr_view() -> None:
    try:
        import openvr
    except ImportError as exc:
        raise RuntimeError("Run 'uv sync' before preparing VR recording") from exc

    openvr.init(openvr.VRApplication_Overlay)
    try:
        openvr.VRSettings().setBool("steamvr", "showMirrorView", True)
    finally:
        openvr.shutdown()


def _find_window(titles: tuple[str, ...]) -> int | None:
    user32 = ctypes.windll.user32
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    @callback_type
    def visit(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        text = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, text, len(text))
        if any(title.casefold() in text.value.casefold() for title in titles):
            matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(visit, 0)
    return matches[0] if matches else None


def _show_window(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)


def _obs_path() -> Path | None:
    candidates = (
        Path("C:/Program Files/obs-studio/bin/64bit/obs64.exe"),
        Path("C:/Program Files (x86)/obs-studio/bin/64bit/obs64.exe"),
    )
    return next((path for path in candidates if path.exists()), None)


def _start_obs() -> None:
    existing = _find_window(("OBS ", "OBS Studio"))
    if existing is not None:
        _show_window(existing)
        return
    executable = _obs_path()
    if executable is None:
        print("OBS Studio was not found. Install it from https://obsproject.com/")
        return
    subprocess.Popen(
        [str(executable)],
        cwd=executable.parent,
        creationflags=subprocess.DETACHED_PROCESS,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        _enable_vr_view()
    except Exception as exc:
        print(f"Could not enable SteamVR VR View: {exc}", file=sys.stderr)
        return 1

    time.sleep(1.0)
    vr_view = _find_window(("VR View", "VR 뷰"))
    if vr_view is not None:
        _show_window(vr_view)
        print("SteamVR VR View is ready.")
    else:
        status = _find_window(("SteamVR Status", "SteamVR 상태", "SteamVR"))
        if status is not None:
            _show_window(status)
        print(
            "Open the SteamVR status menu and select 'Display VR View' "
            "('VR 뷰 표시')."
        )

    _start_obs()
    print("In VR View, choose Left Eye or Both Eyes - Left Dominant.")
    print("In OBS, capture the 'VR View' window. See RECORDING.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
