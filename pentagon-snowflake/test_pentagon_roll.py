#!/usr/bin/env python3
"""Basic geometric and SVG regression tests (standard library only)."""

import math
import unittest
import xml.etree.ElementTree as ET

from pentagon_roll import SCALE, reflection_matrix, regular_pentagon, render_svg


def transformed(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


class PentagonRollTests(unittest.TestCase):
    def test_regular_pentagon_has_unit_sides(self):
        p = regular_pentagon()
        self.assertEqual(len(p), 5)
        for i in range(5):
            self.assertAlmostEqual(math.dist(p[i], p[(i + 1) % 5]), 1.0)

    def test_reflection_fixes_edge_and_is_involution(self):
        p = regular_pentagon()
        m = reflection_matrix(p[0], p[1])
        for end in p[:2]:
            t = transformed(m, end)
            self.assertAlmostEqual(t[0], end[0])
            self.assertAlmostEqual(t[1], end[1])
        q = (0.2, -0.4)
        twice = transformed(m, transformed(m, q))
        self.assertAlmostEqual(twice[0], q[0])
        self.assertAlmostEqual(twice[1], q[1])

    def test_golden_ratio_scale(self):
        self.assertAlmostEqual(SCALE, (3 + math.sqrt(5)) / 2)

    def test_svg_is_valid_and_every_generation_has_six_copies(self):
        ns = {"svg": "http://www.w3.org/2000/svg"}
        for n in range(5):
            root = ET.fromstring(render_svg(n))
            self.assertEqual(root.tag, f"{{{ns['svg']}}}svg")
            self.assertIn(str(6**n), root.find("svg:desc", ns).text)
            for generation in range(1, n + 1):
                group = root.find(
                    f".//svg:g[@id='generation{generation}']", ns
                )
                self.assertIsNotNone(group)
                self.assertEqual(len(group.findall("svg:use", ns)), 6)


if __name__ == "__main__":
    unittest.main()
