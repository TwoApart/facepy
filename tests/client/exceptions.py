# -*- coding: utf-8 -*-
import cPickle

from nose.tools import *

from facepy import FacepyError
from facepy.client import GraphClient


def test_graphclienterror_inherits_from_facepyerror():
    exception = GraphClient.Error('<message>', '<code>')
    assert isinstance(exception, FacepyError)


def test_graphclienterror_can_be_pickled():
    exception = GraphClient.Error('<message>', '<code>')
    cPickle.dumps(exception)


def test_httperror_inherits_from_graphclienterror():
    exception = GraphClient.HTTPError('<message>', '<code>')
    assert isinstance(exception, GraphClient.Error)


def test_httperror_can_be_pickled():
    exception = GraphClient.HTTPError('<message>', '<code>')
    cPickle.dumps(exception)


def test_facebookerror_inherits_from_graphclienterror():
    exception = GraphClient.FacebookError('<message>', '<code>')
    assert isinstance(exception, GraphClient.Error)


def test_facebookerror_can_be_pickled():
    exception = GraphClient.FacebookError('<message>', '<code>')
    cPickle.dumps(exception)


def test_oautherror_inherits_from_facebookerror():
    exception = GraphClient.OAuthError('<message>', '<code>')
    assert isinstance(exception, GraphClient.FacebookError)


def test_oautherror_can_be_pickled():
    exception = GraphClient.OAuthError('<message>', '<code>')
    cPickle.dumps(exception)
