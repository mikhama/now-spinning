import unittest

from exp.spinning_detection_calibration import RpmSample, is_spinning, is_stopped


class SpinningDetectionCalibrationTestCase(unittest.TestCase):
    def test_spin_up_below_or_equal_to_minimum_rpm_is_not_spinning(self):
        samples = [
            RpmSample(0, 400),
            RpmSample(3, 1000),
        ]

        self.assertFalse(is_spinning(samples))

    def test_spin_up_with_insufficient_increase_is_not_spinning(self):
        samples = [
            RpmSample(0, 800),
            RpmSample(3, 1300),
        ]

        self.assertFalse(is_spinning(samples))

    def test_already_spinning_steady_rpm_is_spinning(self):
        samples = [
            RpmSample(0, 5939.55),
            RpmSample(1, 6118.88),
            RpmSample(2, 6058.97),
            RpmSample(3, 6119.03),
        ]

        self.assertTrue(is_spinning(samples))

    def test_decreasing_too_much_over_observation_window_is_not_spinning(self):
        samples = [
            RpmSample(0, 6200),
            RpmSample(3, 5600),
        ]

        self.assertFalse(is_spinning(samples))

    def test_strictly_decreasing_within_steady_delta_is_not_spinning(self):
        samples = [
            RpmSample(4, 4559.10),
            RpmSample(5, 4438.73),
            RpmSample(6, 4259.20),
            RpmSample(7, 4019.27),
            RpmSample(8, 3959.26),
        ]

        self.assertFalse(is_spinning(samples))

    def test_spin_up_with_valid_increase_over_observation_window_is_spinning(self):
        samples = [
            RpmSample(0, 800),
            RpmSample(1, 900),
            RpmSample(3, 1301),
        ]

        self.assertTrue(is_spinning(samples))

    def test_stopped_when_latest_rpm_is_below_threshold(self):
        samples = [
            RpmSample(0, 2200),
            RpmSample(1, 999),
        ]

        self.assertTrue(is_stopped(samples))

    def test_stopped_when_latest_readings_strictly_decrease_with_sufficient_drop(self):
        samples = [
            RpmSample(0, 3100),
            RpmSample(1, 2600),
            RpmSample(2, 2200),
            RpmSample(3, 2000),
        ]

        self.assertTrue(is_stopped(samples))

    def test_non_decreasing_latest_readings_are_not_stopped(self):
        samples = [
            RpmSample(0, 3100),
            RpmSample(1, 2600),
            RpmSample(2, 2700),
            RpmSample(3, 2000),
        ]

        self.assertFalse(is_stopped(samples))

    def test_decreasing_latest_readings_with_insufficient_drop_are_not_stopped(self):
        samples = [
            RpmSample(0, 3100),
            RpmSample(1, 2900),
            RpmSample(2, 2700),
            RpmSample(3, 2300),
        ]

        self.assertFalse(is_stopped(samples))


if __name__ == "__main__":
    unittest.main()
