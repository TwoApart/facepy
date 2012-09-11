# -*- coding: utf-8 -*-
import cPickle

from nose.tools import *

from facepy import FacepyError


def test_facepyerror():
    exception = FacepyError('<message>')

    assert_equal(exception.message, '<message>')
    assert_equal(exception.__str__(), '<message>')
    assert_equal(exception.__repr__(), 'FacepyError(\'<message>\',)')
    assert_equal(exception.__unicode__(), u'<message>')


def test_facepyerror_with_code():
    exception = FacepyError('<message>', '<code>')

    assert_equal(exception.message, '[<code>] <message>')
    assert_equal(exception.__str__(), '[<code>] <message>')
    assert_equal(exception.__repr__(), 'FacepyError(\'[<code>] <message>\',)')
    assert_equal(exception.__unicode__(), u'[<code>] <message>')


def test_facepyerror_can_be_pickled():
    exception = FacepyError('<message>', '<code>')
    cPickle.dumps(exception)
