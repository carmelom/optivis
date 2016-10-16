from __future__ import unicode_literals, division

from unittest import TestCase
import math

from optivis.geometry import Coordinates

class TestCoordinates(TestCase):
    def setUp(self):
        self.a = Coordinates.origin()
        self.b = Coordinates(1.5, 8.3)
        self.unit_vector = Coordinates(1, 1)
        self.anti_unit_vector = Coordinates(-1, -1)

    def test_coordinates_init(self):
        # valid
        Coordinates(-1, 2)
        Coordinates(1, -2)
        Coordinates(4.61, -9.01)
        Coordinates("-3.141", "5.91")

        # not enough inputs
        self.assertRaises(ValueError, Coordinates, "invalid")

        # invalid input types
        self.assertRaises(ValueError, Coordinates, "inv", "inv")
        self.assertRaises(TypeError, Coordinates, [], [])
        self.assertRaises(TypeError, Coordinates, {}, {})

        # test copy constructor
        self.assertEqual(self.a, Coordinates(self.a))
        self.assertEqual(self.b, Coordinates(self.b))

    def test_translate(self):
        self.assertEqual(self.a + self.b, self.b)
        self.assertEqual(self.b - self.b, self.a)

    def test_rotate(self):
        # rotation forward and back
        self.assertEqual(self.b.rotate(50).rotate(-50), self.b)

        # rotation through full circle
        self.assertEqual(self.b.rotate(360), self.b)

    def test_division(self):
        self.assertEqual(self.b / 2, Coordinates(self.b.x / 2, self.b.y / 2))
        self.assertEqual(self.b / -3436.128115, \
        Coordinates(self.b.x / -3436.128115, self.b.y / -3436.128115))

    def test_hypot(self):
        self.assertEqual(self.a.length(), math.sqrt(self.a.x ** 2 + self.a.y ** 2))
        self.assertEqual(self.b.length(), math.sqrt(self.b.x ** 2 + self.b.y ** 2))
        self.assertEqual(self.unit_vector.length(), math.sqrt(2))
        self.assertEqual(self.anti_unit_vector.length(), math.sqrt(2))

    def test_azimuth(self):
        # angle
        self.assertEqual(self.a.azimuth, \
        math.degrees(math.atan2(self.a.y, self.a.x)))
        self.assertEqual(self.b.azimuth, \
        math.degrees(math.atan2(self.b.y, self.b.x)))

    def test_flip(self):
        self.assertEqual(self.unit_vector.flip(), self.anti_unit_vector)
        self.assertEqual(self.b.flip(), Coordinates(-self.b.x, -self.b.y))

    def test_vector_calculus(self):
        # (1,1) - (1,1) - (1,1) = -(1,1)
        self.assertEqual(self.unit_vector - self.unit_vector \
        - self.unit_vector, self.unit_vector.flip())

    def test_n_sided_polygons(self):
        # test a whole bunch of polygons
        for i in xrange(3, 100):
            self._do_test_n_sided_polygon(i)

    def _do_test_n_sided_polygon(self, n):
        # external angle of each side w.r.t. last
        external_angle = 180 - (180 * (n - 2)) / n

        # side length
        side_vec = Coordinates(10.023522718, 0)

        # start vector
        vec = self.a

        # loop over the sides
        for i in range(n):
            # add the next side
            vec += side_vec.rotate(external_angle * i)

        # assert the vector is back at the origin
        self.assertEqual(vec, self.a, \
        "{0} != {1} ({2} sided polygon)".format(vec, self.a, n))

    def test_is_positive(self):
        self.assertTrue(Coordinates(1, 1).is_positive())
        self.assertTrue(Coordinates(0, 1000).is_positive())
        self.assertTrue(Coordinates(1000, 0).is_positive())
        self.assertTrue(Coordinates(294.1327, 1.95347).is_positive())
        self.assertTrue(Coordinates(0, 0).is_positive())
        self.assertFalse(Coordinates(-1, -1).is_positive())
        self.assertFalse(Coordinates(0, -1).is_positive())
        self.assertFalse(Coordinates(-1, 0).is_positive())
        self.assertFalse(Coordinates(-23592, -910.02436).is_positive())
