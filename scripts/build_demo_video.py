from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = Path("C:/Windows/Fonts/malgunbd.ttf")


def _ffmpeg_executable() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "Install FFmpeg or run this script with "
            "'uv run --with imageio-ffmpeg python scripts/build_demo_video.py'."
        ) from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _make_intro(hero_path: Path, output: Path) -> None:
    hero = Image.open(hero_path).convert("RGB")
    background = ImageOps.fit(hero, (1920, 1080), method=Image.Resampling.LANCZOS)
    background.save(output)


def _make_badge(title: str, detail: str, accent: tuple[int, int, int], output: Path) -> None:
    image = Image.new("RGBA", (940, 126), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((0, 0, 940, 126), radius=24, fill=(5, 10, 25, 225))
    draw.rounded_rectangle((0, 0, 15, 126), radius=7, fill=(*accent, 255))
    draw.text((38, 17), title, font=_font(42), fill=(255, 255, 255, 255))
    draw.text((340, 28), detail, font=_font(30), fill=(200, 215, 235, 255))
    image.save(output)


def _make_preview(ffmpeg: str, video: Path, output: Path) -> None:
    filters = (
        "[0:v]trim=start=3:end=7,setpts=PTS-STARTPTS[v0];"
        "[0:v]trim=start=26:end=30,setpts=PTS-STARTPTS[v1];"
        "[0:v]trim=start=35:end=39,setpts=PTS-STARTPTS[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0,fps=10,"
        "scale=640:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=128[p];"
        "[s1][p]paletteuse=dither=bayer:bayer_scale=4[v]"
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video),
            "-filter_complex",
            filters,
            "-map",
            "[v]",
            "-loop",
            "0",
            str(output),
        ]
    )


def build(source: Path, hero: Path, output: Path, preview: Path) -> None:
    ffmpeg = _ffmpeg_executable()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="vrc-demo-") as temporary:
        work = Path(temporary)
        intro_image = work / "intro.png"
        intro_video = work / "intro.mp4"
        body_video = work / "body.mp4"
        auto_badge = work / "auto.png"
        manual_badge = work / "manual.png"
        position_badge = work / "position.png"

        _make_intro(hero, intro_image)
        _make_badge("1. 자동 번역", "2초 간격으로 화면 변화를 확인", (0, 226, 255), auto_badge)
        _make_badge("2. 수동 번역", "왼쪽 트리거: 번역 / 그립: 지우기", (172, 106, 255), manual_badge)
        _make_badge("3. 위치 조정", "Ctrl + Alt + 방향키", (255, 111, 97), position_badge)

        _run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-t",
                "2.4",
                "-i",
                str(intro_image),
                "-f",
                "lavfi",
                "-t",
                "2.4",
                "-i",
                "anullsrc=r=48000:cl=stereo",
                "-vf",
                "fade=t=in:st=0:d=0.35,fade=t=out:st=2.05:d=0.35",
                "-r",
                "60",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                str(intro_video),
            ]
        )

        filters = (
            "[0:v][1:v]overlay=60:60:enable='between(t,0,17.99)'[v1];"
            "[v1][2:v]overlay=60:60:enable='between(t,18,31.99)'[v2];"
            "[v2][3:v]overlay=60:60:enable='gte(t,32)'[vout]"
        )
        _run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-loop",
                "1",
                "-i",
                str(auto_badge),
                "-loop",
                "1",
                "-i",
                str(manual_badge),
                "-loop",
                "1",
                "-i",
                str(position_badge),
                "-filter_complex",
                filters,
                "-map",
                "[vout]",
                "-map",
                "0:a:0",
                "-r",
                "60",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                str(body_video),
            ]
        )

        _run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(intro_video),
                "-i",
                str(body_video),
                "-filter_complex",
                "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "21",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        _make_preview(ffmpeg, output, preview)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the public demonstration video")
    parser.add_argument("source", type=Path, help="Original 1920x1080 demonstration video")
    parser.add_argument(
        "--hero",
        type=Path,
        default=ROOT / "assets/vrc-ocr-translate-hero.png",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "assets/demo.mp4",
    )
    parser.add_argument(
        "--preview",
        type=Path,
        default=ROOT / "assets/demo-preview.gif",
    )
    args = parser.parse_args()
    build(
        args.source.resolve(),
        args.hero.resolve(),
        args.output.resolve(),
        args.preview.resolve(),
    )
    print(f"Demo video written to {args.output.resolve()}")
    print(f"GIF preview written to {args.preview.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
