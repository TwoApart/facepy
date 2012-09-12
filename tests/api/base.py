# -*- coding: utf-8 -*-
from nose.tools import *

from facepy import FacepyError
from facepy.api.base import BaseApi


def test_baseapierror_inherits_from_facepyerror():
    exception = BaseApi.Error('<message>', '<code>')
    assert isinstance(exception, FacepyError)
