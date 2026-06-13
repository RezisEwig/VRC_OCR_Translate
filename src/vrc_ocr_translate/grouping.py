from __future__ import annotations

from collections import deque

from .models import BoundingBox, OcrRegion


def group_ocr_lines(
    regions: list[OcrRegion],
    eps: float = 0.65,
    max_gap_ratio: float = 4.0,
) -> list[OcrRegion]:
    """Merge OCR fragments only when DBSCAN considers them the same text line."""
    if not regions:
        return []

    labels = _dbscan_labels(regions, max(0.1, eps), max(0.5, max_gap_ratio))
    clusters: dict[int, list[OcrRegion]] = {}
    for region, label in zip(regions, labels, strict=True):
        clusters.setdefault(label, []).append(region)

    merged = [_merge_line(items) for items in clusters.values()]
    return sorted(merged, key=lambda item: (item.bounds.top, item.bounds.left))


def _dbscan_labels(
    regions: list[OcrRegion],
    eps: float,
    max_gap_ratio: float,
) -> list[int]:
    # DBSCAN with min_samples=1 is a useful fit here: isolated OCR boxes remain
    # independent while chains of neighboring word boxes become one line.
    unvisited = -1
    labels = [unvisited] * len(regions)
    cluster_id = 0
    for seed in range(len(regions)):
        if labels[seed] != unvisited:
            continue
        labels[seed] = cluster_id
        queue = deque(_neighbors(regions, seed, eps, max_gap_ratio))
        while queue:
            index = queue.popleft()
            if labels[index] != unvisited:
                continue
            labels[index] = cluster_id
            queue.extend(_neighbors(regions, index, eps, max_gap_ratio))
        cluster_id += 1
    return labels


def _neighbors(
    regions: list[OcrRegion],
    index: int,
    eps: float,
    max_gap_ratio: float,
) -> list[int]:
    current = regions[index]
    return [
        other_index
        for other_index, other in enumerate(regions)
        if other_index != index
        and _same_line(current.bounds, other.bounds, eps, max_gap_ratio)
    ]


def _same_line(
    first: BoundingBox,
    second: BoundingBox,
    eps: float,
    max_gap_ratio: float,
) -> bool:
    height = max(1, first.height, second.height)
    first_center = (first.top + first.bottom) / 2
    second_center = (second.top + second.bottom) / 2
    if abs(first_center - second_center) > height * eps:
        return False

    vertical_overlap = min(first.bottom, second.bottom) - max(first.top, second.top)
    if vertical_overlap < min(first.height, second.height) * 0.2:
        return False

    horizontal_gap = max(
        0,
        max(first.left, second.left) - min(first.right, second.right),
    )
    return horizontal_gap <= height * max_gap_ratio


def _merge_line(regions: list[OcrRegion]) -> OcrRegion:
    ordered = sorted(regions, key=lambda item: item.bounds.left)
    bounds = BoundingBox(
        left=min(item.bounds.left for item in ordered),
        top=min(item.bounds.top for item in ordered),
        right=max(item.bounds.right for item in ordered),
        bottom=max(item.bounds.bottom for item in ordered),
    )
    confidence = sum(item.confidence for item in ordered) / len(ordered)
    return OcrRegion(
        text=_join_fragments([item.text for item in ordered]),
        confidence=confidence,
        bounds=bounds,
    )


def _join_fragments(parts: list[str]) -> str:
    result = ""
    for part in parts:
        if (
            result
            and result[-1].isascii()
            and result[-1].isalnum()
            and part
            and part[0].isascii()
            and part[0].isalnum()
        ):
            result += " "
        result += part
    return result
