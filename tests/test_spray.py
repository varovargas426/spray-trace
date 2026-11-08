import unittest
from spray import investigate


def event(m, user, outcome="failure", ip="192.0.2.1"):
    return dict(time=f"2026-01-01T00:{m:02}:00+00:00", user=user, outcome=outcome, ip=ip)


class InvestigationTests(unittest.TestCase):
    def test_boundary_and_attribution(self):
        rows = [event(0, "a"), event(1, "a"), event(10, "b"), event(11, "a", "success"),
                event(11, "b", "success", "192.0.2.2"), event(21, "b", "success")]
        alert, = investigate(reversed(rows), 2)
        self.assertEqual(alert["targeted"], ["a", "b"])
        self.assertEqual(alert["later_success"], ["a"])

    def test_expired_and_repeated_attempts(self):
        self.assertEqual(investigate([event(0, "a"), event(11, "b"), event(12, "b")], 2), [])

    def test_rejects_naive_clock(self):
        with self.assertRaises(ValueError):
            investigate([dict(event(0, "a"), time="2026-01-01T00:00:00")])
