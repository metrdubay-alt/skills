"""Тесты чистой логики этапа scenes: выбор таймстампов кадров и дедуп по phash."""
import pytest

from video_analyzer.stages.scenes import frame_timestamps, dedupe_hashes


class TestFrameTimestamps:
    def test_short_scene_gets_single_middle_frame(self):
        assert frame_timestamps(10.0, 20.0, max_interval=20.0) == [15.0]

    def test_long_scene_gets_extra_frames_at_interval(self):
        # сцена 60 c при интервале 20 c -> 3 кадра, равномерно внутри сцены
        ts = frame_timestamps(0.0, 60.0, max_interval=20.0)
        assert len(ts) == 3
        assert ts == sorted(ts)
        assert all(0.0 < t < 60.0 for t in ts)

    def test_boundary_scene_exactly_max_interval_single_frame(self):
        assert frame_timestamps(0.0, 20.0, max_interval=20.0) == [10.0]

    def test_zero_length_scene_returns_start(self):
        assert frame_timestamps(5.0, 5.0, max_interval=20.0) == [5.0]


class TestDedupeHashes:
    def test_identical_hashes_deduped(self):
        # два одинаковых хэша -> остаётся первый
        keep = dedupe_hashes(["0" * 16, "0" * 16], max_distance=6)
        assert keep == [0]

    def test_distinct_hashes_kept(self):
        # хэши, отличающиеся на много бит -> оба остаются
        keep = dedupe_hashes(["0000000000000000", "ffffffffffffffff"], max_distance=6)
        assert keep == [0, 1]

    def test_near_duplicate_within_distance_dropped(self):
        # отличие в 1 бит (hamming=1 <= 6) -> дубликат
        keep = dedupe_hashes(["0000000000000000", "0000000000000001"], max_distance=6)
        assert keep == [0]

    def test_duplicate_compared_against_all_kept(self):
        # третий хэш близок к первому, хоть и далёк от второго -> дубликат
        keep = dedupe_hashes(
            ["0000000000000000", "ffffffffffffffff", "0000000000000003"],
            max_distance=6,
        )
        assert keep == [0, 1]

    def test_empty_input(self):
        assert dedupe_hashes([], max_distance=6) == []
