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
