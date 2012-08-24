"""Tests for the ``exceptions`` module."""

import cPickle

from nose.tools import *

from facepy import *


def test_facepy_error():
    try:
        raise FacepyError('<message>')
    except FacepyError as exception:
        assert exception.message == '<message>'
        assert exception.__str__() == '<message>'
        assert exception.__repr__() == "FacepyError('<message>',)"
        assert exception.__unicode__() == u'<message>'


def test_facebook_error():
    try:
        raise GraphAPI.FacebookError('<message>', 100)
    except GraphAPI.FacebookError as exception:
        assert exception.message == '<message>'
        assert exception.code == 100
        assert exception.__str__() == '[100] <message>'
        assert exception.__repr__() == "FacebookError('[100] <message>',)"
        assert exception.__unicode__() == u'[100] <message>'


def test_facebookerror_can_be_pickled():
    try:
        raise GraphAPI.FacebookError('<message>', '<code>')
    except FacepyError as exception:
        cPickle.dumps(exception)


def test_oautherror_can_be_pickled():
    try:
        raise GraphAPI.OAuthError('<message>', '<code>')
    except FacepyError as exception:
        cPickle.dumps(exception)


def test_httperror_can_be_pickled():
    try:
        raise GraphAPI.HTTPError('<message>')
    except FacepyError as exception:
        cPickle.dumps(exception)
