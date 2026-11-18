import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))

import classes.topology as ct  # noqa: E402


class CacheTest(unittest.TestCase):

    def topology(self, policy):
        node = {
            "id": 1,
            "type": "chost",
            "name": "worker",
            "layers": [],
            "storageSize": 4800,
            "cache": [0, 0],
            "cachePolicy": policy,
            "scheduledLayers": 0,
        }
        return ct.Topology([node], [])

    def add(self, topo, layer, size_mb, time):
        topo._Topology__control_cache(1, layer, size_mb * 8, time)

    def test_units_and_capacity(self):
        topo = self.topology("FIFO")
        for i, layer in enumerate(["a", "b", "c", "d"]):
            self.add(topo, layer, 200, i + 1)
        layers = topo.topo.nodes[1]["layers"]
        self.assertEqual(len(layers), 3)
        self.assertEqual(sum(x[1] for x in layers), 4800)

    def test_fifo_hit_does_not_refresh(self):
        topo = self.topology("FIFO")
        self.add(topo, "a", 200, 1)
        self.add(topo, "b", 200, 2)
        self.add(topo, "c", 200, 3)
        self.add(topo, "a", 200, 4)   # hit, FIFO keeps original time
        self.add(topo, "d", 200, 5)
        layers = [x[0] for x in topo.topo.nodes[1]["layers"]]
        self.assertEqual(layers, ["b", "c", "d"])
        self.assertEqual(topo.topo.nodes[1]["cache"], [1, 4])

    def test_lru_hit_refreshes(self):
        topo = self.topology("LRU")
        self.add(topo, "a", 200, 1)
        self.add(topo, "b", 200, 2)
        self.add(topo, "c", 200, 3)
        self.add(topo, "a", 200, 4)   # hit, LRU refreshes a
        self.add(topo, "d", 200, 5)
        layers = [x[0] for x in topo.topo.nodes[1]["layers"]]
        self.assertEqual(layers, ["a", "c", "d"])
        self.assertEqual(topo.topo.nodes[1]["cache"], [1, 4])


if __name__ == "__main__":
    unittest.main()
