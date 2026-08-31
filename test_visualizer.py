import unittest

from visualizer import heading_to_audio_dot_normalized, heading_to_display_angle_deg


class HeadingToAudioDotNormalizedTests(unittest.TestCase):
    def test_center_wraparound_remains_continuous(self):
        self.assertAlmostEqual(heading_to_audio_dot_normalized(355), 5.0 / 85.0, places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(0), 0.0, places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(5), -(5.0 / 85.0), places=6)

    def test_left_side_interpolates_to_left_edge(self):
        self.assertAlmostEqual(heading_to_audio_dot_normalized(10), -(10.0 / 85.0), places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(45), -(45.0 / 85.0), places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(85), -1.0, places=6)

    def test_right_side_interpolates_to_right_edge(self):
        self.assertAlmostEqual(heading_to_audio_dot_normalized(350), 10.0 / 85.0, places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(315), 45.0 / 85.0, places=6)
        self.assertAlmostEqual(heading_to_audio_dot_normalized(275), 1.0, places=6)

    def test_left_side_clamps_past_edge(self):
        self.assertEqual(heading_to_audio_dot_normalized(90), -1.0)
        self.assertEqual(heading_to_audio_dot_normalized(120), -1.0)

    def test_right_side_clamps_past_edge(self):
        self.assertEqual(heading_to_audio_dot_normalized(260), 1.0)
        self.assertEqual(heading_to_audio_dot_normalized(240), 1.0)

    def test_wraparound_sequence_is_monotonic_through_center(self):
        headings = [340, 350, 355, 0, 5, 10, 20]
        normalized = [heading_to_audio_dot_normalized(heading) for heading in headings]
        self.assertTrue(
            all(previous > current for previous, current in zip(normalized, normalized[1:])),
            normalized,
        )


class HeadingToDisplayAngleDegTests(unittest.TestCase):
    def test_center_wraparound_is_signed(self):
        self.assertAlmostEqual(heading_to_display_angle_deg(355), -5.0, places=6)
        self.assertAlmostEqual(heading_to_display_angle_deg(0), 0.0, places=6)
        self.assertAlmostEqual(heading_to_display_angle_deg(5), 5.0, places=6)

    def test_left_and_right_edges_map_to_signed_ninety(self):
        self.assertAlmostEqual(heading_to_display_angle_deg(85), 85.0, places=6)
        self.assertAlmostEqual(heading_to_display_angle_deg(275), -85.0, places=6)

    def test_values_beyond_front_arc_clamp_to_signed_ninety(self):
        self.assertEqual(heading_to_display_angle_deg(120), 90.0)
        self.assertEqual(heading_to_display_angle_deg(240), -90.0)


if __name__ == "__main__":
    unittest.main()
