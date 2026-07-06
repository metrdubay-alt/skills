"""Тесты merge: выравнивание транскрипт-сегментов по сценам."""
from video_analyzer.models import (
    Entity,
    Frame,
    Scene,
    SceneVision,
    Transcript,
    TranscriptSegment,
)
from video_analyzer.stages.merge import build_segments


def scene(scene_id, start, end, frames=()):
    return Scene(scene_id=scene_id, start=start, end=end,
                 frames=[Frame(path=p, timestamp=start) for p in frames])


def vision(scene_id, **kw):
    defaults = dict(scene_type="dashboard", description="описание",
                    screen_text=[], entities=[], notable=None)
    defaults.update(kw)
    return SceneVision(scene_id=scene_id, **defaults)


class TestBuildSegments:
    def test_speech_assigned_to_scene_by_midpoint(self):
        transcript = Transcript(language="ru", segments=[
            TranscriptSegment(start=0.0, end=4.0, text="первая фраза"),
            TranscriptSegment(start=12.0, end=16.0, text="вторая фраза"),
        ])
        scenes = [scene(0, 0.0, 10.0), scene(1, 10.0, 20.0)]
        segments = build_segments(transcript, scenes, [])
        assert len(segments) == 2
        assert segments[0].speech == "первая фраза"
        assert segments[1].speech == "вторая фраза"

    def test_segment_spanning_boundary_goes_to_midpoint_scene(self):
        # сегмент 8-14, середина 11 -> вторая сцена
        transcript = Transcript(language="ru", segments=[
            TranscriptSegment(start=8.0, end=14.0, text="на границе"),
        ])
        scenes = [scene(0, 0.0, 10.0), scene(1, 10.0, 20.0)]
        segments = build_segments(transcript, scenes, [])
        assert segments[0].speech == ""
        assert segments[1].speech == "на границе"

    def test_multiple_speech_segments_joined_in_order(self):
        transcript = Transcript(language="ru", segments=[
            TranscriptSegment(start=1.0, end=2.0, text="раз."),
            TranscriptSegment(start=3.0, end=4.0, text="два."),
        ])
        scenes = [scene(0, 0.0, 10.0)]
        segments = build_segments(transcript, scenes, [])
        assert segments[0].speech == "раз. два."

    def test_vision_data_attached_to_matching_scene(self):
        transcript = Transcript(language="ru", segments=[])
        scenes = [scene(0, 0.0, 10.0, frames=["frames/a.jpg"])]
        visions = [vision(0, scene_type="chart", description="график APR",
                          screen_text=["APR 12%"],
                          entities=[Entity(type="metric", name="APR", value="12%")],
                          notable="высокий APR")]
        segments = build_segments(transcript, scenes, visions)
        seg = segments[0]
        assert seg.scene_type == "chart"
        assert seg.screen_summary == "график APR"
        assert seg.screen_text == ["APR 12%"]
        assert seg.entities[0].name == "APR"
        assert seg.notable == "высокий APR"
        assert seg.frame_refs == ["frames/a.jpg"]

    def test_scene_without_vision_has_empty_visual_fields(self):
        transcript = Transcript(language="ru", segments=[])
        scenes = [scene(0, 0.0, 10.0)]
        segments = build_segments(transcript, scenes, [])
        seg = segments[0]
        assert seg.scene_type is None
        assert seg.screen_summary is None
        assert seg.screen_text == []
        assert seg.entities == []

    def test_speech_outside_all_scenes_clamped_to_nearest(self):
        # речь после конца последней сцены не должна теряться
        transcript = Transcript(language="ru", segments=[
            TranscriptSegment(start=25.0, end=30.0, text="хвост"),
        ])
        scenes = [scene(0, 0.0, 10.0), scene(1, 10.0, 20.0)]
        segments = build_segments(transcript, scenes, [])
        assert segments[1].speech == "хвост"

    def test_segment_ids_and_times_follow_scenes(self):
        transcript = Transcript(language="ru", segments=[])
        scenes = [scene(0, 0.0, 10.0), scene(1, 10.0, 20.0)]
        segments = build_segments(transcript, scenes, [])
        assert [s.segment_id for s in segments] == [0, 1]
        assert segments[1].start == 10.0
        assert segments[1].end == 20.0
