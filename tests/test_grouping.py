from vrc_ocr_translate.grouping import group_ocr_lines
from vrc_ocr_translate.models import BoundingBox, OcrRegion


def test_merges_fragments_on_same_line_but_keeps_other_lines_separate():
    regions = [
        OcrRegion("出口", 0.9, BoundingBox(100, 100, 180, 140)),
        OcrRegion("はこちら", 0.8, BoundingBox(190, 102, 310, 142)),
        OcrRegion("立入禁止", 0.95, BoundingBox(110, 190, 280, 232)),
    ]

    grouped = group_ocr_lines(regions, eps=0.65, max_gap_ratio=4.0)

    assert len(grouped) == 2
    assert grouped[0].text == "出口はこちら"
    assert grouped[0].bounds == BoundingBox(100, 100, 310, 142)
    assert grouped[1].text == "立入禁止"


def test_does_not_merge_distant_labels_on_same_height():
    regions = [
        OcrRegion("赤", 0.9, BoundingBox(10, 50, 40, 90)),
        OcrRegion("青", 0.9, BoundingBox(500, 50, 530, 90)),
    ]

    assert len(group_ocr_lines(regions, max_gap_ratio=4.0)) == 2


def test_adds_space_between_english_fragments():
    regions = [
        OcrRegion("Press", 0.9, BoundingBox(10, 10, 80, 40)),
        OcrRegion("START", 0.9, BoundingBox(90, 10, 170, 40)),
    ]

    assert group_ocr_lines(regions)[0].text == "Press START"
