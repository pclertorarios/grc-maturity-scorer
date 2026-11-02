import csv
import tempfile
import unittest
from pathlib import Path

from csf_score import load_assessment, summarize


def write_csv(rows):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="")
    writer = csv.writer(handle)
    writer.writerow(["function", "category", "current", "target", "weight"])
    writer.writerows(rows)
    handle.close()
    return Path(handle.name)


class ScorerTests(unittest.TestCase):
    def test_weighted_function_average(self):
        path = write_csv([["GV", "GV.OC", 1, 3, 1], ["GV", "GV.RM", 3, 3, 3]])
        summary = summarize(load_assessment(path))
        self.assertEqual(summary["functions"]["GV"]["current"], 2.5)
        self.assertEqual(summary["functions"]["GV"]["gap"], 0.5)

    def test_priorities_sorted_by_weighted_gap(self):
        path = write_csv([["ID", "ID.AM", 1, 3, 1], ["PR", "PR.AA", 2, 3, 3]])
        priorities = summarize(load_assessment(path))["priorities"]
        self.assertEqual([p["category"] for p in priorities], ["PR.AA", "ID.AM"])

    def test_rejects_out_of_range_score(self):
        path = write_csv([["DE", "DE.CM", 5, 3, 1]])
        with self.assertRaises(ValueError):
            load_assessment(path)

    def test_rejects_category_outside_function(self):
        path = write_csv([["RS", "PR.AA", 1, 3, 1]])
        with self.assertRaises(ValueError):
            load_assessment(path)

    def test_sample_file_runs(self):
        summary = summarize(load_assessment(Path(__file__).with_name("sample_assessment.csv")))
        self.assertEqual(len(summary["functions"]), 6)


if __name__ == "__main__":
    unittest.main()
