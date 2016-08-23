# coding=utf-8
from tam.views.check.taxi2check import run_tests as run_taxi2_tests, tests as arte_tests
from tam.views.check.artecheck import run_tests as run_arte_tests, tests as taxi2_tests


def test_known_taxi2():
    run_taxi2_tests(taxi2_tests)

def test_known_arte():
    run_arte_tests(arte_tests)
