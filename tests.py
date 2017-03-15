#!/usr/bin/env python

from unittest import TestCase
from lazy_streams import stream
from time import sleep
from datetime import datetime
from random import random

class TestBase(TestCase):

    def test_size(self):
        # given
        sut = stream(range(5000))

        # when
        result = sut.size()

        # then
        self.assertEqual(result, 5000)

    def test_to_list(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.to_list()

        # then
        self.assertEqual(result, [0, 1, 2, 3 ,4])

    def test_to_string(self):
        # given
        sut = stream(range(5))

        # when
        result_1 = sut.to_string()
        result_2 = sut.to_string('-')

        # then
        self.assertEqual(result_1, '0, 1, 2, 3, 4')
        self.assertEqual(result_2, '0-1-2-3-4')

    def test_min(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.min()

        # then
        self.assertEqual(result, 0)


    def test_max(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.max()

        # then
        self.assertEqual(result, 4)

    def test_reduce(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.reduce(lambda x, y: "%s%s" % (x, y))

        # then
        self.assertEqual(result, '01234')

    def test_take(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.take(3).to_list()

        # then
        self.assertEqual(result, [0, 1, 2])

    def test_first_or_else(self):
        # given
        sut_1 = stream(range(5))
        sut_2 = stream([])

        # when
        result_1 = sut_1.first_or_else()
        result_2 = sut_2.first_or_else()
        result_3 = sut_2.first_or_else('nothing')

        # then
        self.assertEqual(result_1, 0)
        self.assertIsNone(result_2)
        self.assertEqual(result_3, 'nothing')


    def test_last_or_else(self):
        # given
        sut_1 = stream(range(5))
        sut_2 = stream([])

        # when
        result_1 = sut_1.last_or_else()
        result_2 = sut_2.last_or_else()
        result_3 = sut_2.last_or_else('nothing')

        # then
        self.assertEqual(result_1, 4)
        self.assertIsNone(result_2)
        self.assertEqual(result_3, 'nothing')

    def test_for_each(self):
        # given
        class Person:
            def __init__(self, name):
                self.name = name
            def upper_name(self):
                self.name = self.name.upper()
        sut = stream([Person('John'), Person('Paul'), \
                      Person('George'), Person('rinGo')])

        # when
        sut.for_each(lambda x: x.upper_name())
        result = sut.to_list()

        # then
        self.assertEquals(result[0].name, 'JOHN')
        self.assertEquals(result[1].name, 'PAUL')
        self.assertEquals(result[2].name, 'GEORGE')
        self.assertEquals(result[3].name, 'RINGO')


class TestReverse(TestCase):

    def test_to_list(self):
        # given
        sut = stream(range(5))

        # when
        result = sut.reverse().to_list()

        # then
        self.assertEqual(result, [4, 3, 2, 1, 0])


class TestMap(TestCase):

    def test_size(self):
        # given
        sut = stream(range(50)).map(lambda x: x*0.5)

        # when
        result = sut.size()

        # then
        self.assertEqual(result, 50)

    def test_map_to_list(self):
        # given
        sut = stream(range(5)).map(lambda x: x+1)

        # when
        result = sut.to_list()

        # then
        self.assertEqual(result, [1, 2, 3 ,4, 5])


class TestFilter(TestCase):

    def test_size(self):
        # given
        sut = stream(range(50)).filter(lambda x: x%2 == 0)

        # when
        result_1 = sut.size()
        result_2 = sut.size() # test cached result

        # then
        self.assertEqual(result_1, 25)
        self.assertEqual(result_2, 25)

    def test_filter_to_list(self):
        # given
        sut = stream(range(10))

        # when
        result = sut.filter(lambda x: (x+1)%2 == 0).to_list()

        # then
        self.assertEqual(result, [1, 3, 5, 7, 9])

    def test_filter_take(self):
        # given
        sut = stream(range(10))

        # when
        result = sut.filter(lambda x: (x+1)%2 == 0).take(20).to_list()

        # then
        self.assertEqual(result, [1, 3, 5, 7, 9])


class TestFlatten(TestCase):

    def test_size(self):
        # given
        sut = stream([1, [2, 3], 4, [5, [6, 7], 8]]).flatten()

        # when
        result = sut.size()
            
        # then
        self.assertEqual(result, 8)

    def test_to_list(self):
        # given
        sut = stream([1, [2, 3], 4, [5, [6, 7], 8]]).flatten()

        # when
        result = sut.to_list()
            
        # then
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8])


class TestChaining(TestCase):

    def test_filter_map(self):
        # given
        sut = stream(range(10))

        # when
        result = sut \
            .filter(lambda x: x%2 == 0) \
            .map(lambda x: x / 2) \
            .to_string()

        # then
        self.assertEqual(result, "0, 1, 2, 3, 4")

    def test_map_filter(self):
        # given
        sut = stream(range(10))

        # when
        result = sut \
            .map(lambda x: x / 2) \
            .filter(lambda x: x%2 == 0) \
            .to_string()

        # then
        self.assertEqual(result, "0, 0, 2, 2, 4, 4")


class TestParallel(TestCase):

    def test_speed(self):
        def slow_is_even(x):
            sleep(0.01 + random()*0.1)
            return x%2 == 0
        def slow_negative(x):
            sleep(0.01 + random()*0.1)
            return -x
        def time_it(func, threads):
            start = datetime.now()
            result = func(threads)
            return datetime.now() - start, result

        s = stream(range(10)).filter(slow_is_even).map(slow_negative)
        results_serial = time_it(s.to_list, 0)
        results_parallel = time_it(s.to_list, 5)
        self.assertEqual(results_serial[1], results_parallel[1])
        self.assertGreater(results_serial[0], results_parallel[0])

    def test_size(self):
        def slow_is_even(x):
            sleep(0.01 + random()*0.1)
            return x%2 == 0
        def slow_negative(x):
            sleep(0.01 + random()*0.1)
            return -x
        def time_it(func, threads):
            start = datetime.now()
            result = func(threads)
            return datetime.now() - start, result

        s = stream(range(10)).filter(slow_is_even).map(slow_negative)
        results_serial = time_it(s.size, 0)
        results_parallel = time_it(s.size, 5)
        self.assertEqual(results_serial[1], results_parallel[1])
        self.assertGreater(results_serial[0], results_parallel[0])
