from __future__ import annotations

import ctypes

from PIL import Image

from .config import OverlayConfig


def calibration_translation(
    config: OverlayConfig,
    image_size: tuple[int, int],
) -> tuple[float, float]:
    width, height = image_size
    aspect_height_m = config.width_m * height / max(1, width)
    return (
        config.position_offset_x_ratio * config.width_m,
        config.vertical_offset_m - config.position_offset_y_ratio * aspect_height_m,
    )


class SteamVROverlay:
    KEY = "com.rezis.vrc-ocr-translate.subtitle"
    NAME = "VRC OCR Translate"

    def __init__(self, config: OverlayConfig) -> None:
        try:
            import openvr
        except ImportError as exc:
            raise RuntimeError("SteamVR overlay requires the 'openvr' package") from exc
        self._openvr = openvr
        self._config = config
        self._handle: int | None = None
        self._buffer: ctypes.Array[ctypes.c_ubyte] | None = None

    def start(self) -> None:
        self._openvr.init(self._openvr.VRApplication_Overlay)
        overlay = self._openvr.VROverlay()
        self._handle = overlay.createOverlay(self.KEY, self.NAME)
        overlay.setOverlayWidthInMeters(self._handle, self._config.width_m)
        overlay.setOverlayAlpha(self._handle, 1.0)
        self.update_position((16, 9))

    def update_position(self, image_size: tuple[int, int]) -> None:
        if self._handle is None:
            raise RuntimeError("Overlay has not been started")
        x_m, y_m = calibration_translation(self._config, image_size)
        matrix = self._openvr.HmdMatrix34_t()
        matrix.m[0][0] = 1.0
        matrix.m[1][1] = 1.0
        matrix.m[2][2] = 1.0
        matrix.m[0][3] = x_m
        matrix.m[1][3] = y_m
        matrix.m[2][3] = -self._config.distance_m
        self._openvr.VROverlay().setOverlayTransformTrackedDeviceRelative(
            self._handle,
            self._openvr.k_unTrackedDeviceIndex_Hmd,
            matrix,
        )

    def show(self, image: Image.Image) -> None:
        if self._handle is None:
            raise RuntimeError("Overlay has not been started")
        rgba = image.convert("RGBA")
        raw = rgba.tobytes("raw", "RGBA")
        buffer_type = ctypes.c_ubyte * len(raw)
        self._buffer = buffer_type.from_buffer_copy(raw)
        overlay = self._openvr.VROverlay()
        self.update_position(rgba.size)
        try:
            overlay.setOverlayRaw(
                self._handle,
                self._buffer,
                rgba.width,
                rgba.height,
                4,
            )
        except Exception:
            # SteamVR can transiently reject frequent raw texture replacement.
            overlay.clearOverlayTexture(self._handle)
            overlay.setOverlayRaw(
                self._handle,
                self._buffer,
                rgba.width,
                rgba.height,
                4,
            )
        overlay.showOverlay(self._handle)

    def hide(self) -> None:
        if self._handle is not None:
            self._openvr.VROverlay().hideOverlay(self._handle)

    def close(self) -> None:
        if self._handle is not None:
            overlay = self._openvr.VROverlay()
            overlay.hideOverlay(self._handle)
            overlay.destroyOverlay(self._handle)
            self._handle = None
        self._openvr.shutdown()

    def __enter__(self) -> "SteamVROverlay":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
