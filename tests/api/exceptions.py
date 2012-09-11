# -*- coding: utf-8 -*-
from nose.tools import *

from facepy import FacepyError
from facepy.api.exceptions import BaseApiError


def test_baseapierror_inherits_from_facepyerror():
    exception = BaseApiError('<message>', '<code>')
    assert isinstance(exception, FacepyError)
