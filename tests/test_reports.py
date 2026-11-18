import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

import classes.report as rp  # noqa: E402
import classes.topology as ct  # noqa: E402


class ReportTest(unittest.TestCase):

    def setUp(self):
        self.old = os.getcwd()
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)
        os.mkdir("reports")

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.dir)

    def topology(self):
        worker = {
            "id": 1, "type": "chost", "name": "worker", "layers": [],
            "storageSize": 4800, "cache": [0, 0], "cachePolicy": "FIFO",
            "scheduledLayers": 0,
        }
        registry = {
            "id": 2, "type": "chost", "name": "registry", "layers": [],
            "storageSize": 0, "cache": [0, 0], "cachePolicy": "FIFO",
            "scheduledLayers": 0,
        }
        return ct.Topology([worker, registry], [])

    def test_registry_usage_counts_first_request(self):
        topo = self.topology()
        messages = [
            ct.Message(src=2, name="a"),
            ct.Message(src=2, name="b"),
        ]
        rp.registry_usage(messages, topo.topo, "t")
        with open("reports/t-registry_usage.json") as f:
            data = json.load(f)
        self.assertEqual(data["registries"][0]["name"], "registry")
        self.assertEqual(data["registries"][0]["numberOfRequests"], 2)

    def test_host_occupation_cache_hit(self):
        topo = self.topology()
        message = ct.Message(src=2, dst=1, name="a", size=100,
                             transmitted=100)
        message.path = [2, 1]
        message.start_time = 5
        message.finish_time = 5
        rp.host_occupation([message], topo.topo, "t")
        with open("reports/t-host_occupation.csv") as f:
            rows = list(csv.reader(f, delimiter=";"))
        self.assertEqual(rows[1][0], "worker")
        self.assertEqual(rows[1][4], "0.00")


if __name__ == "__main__":
    unittest.main()
