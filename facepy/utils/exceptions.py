# -*- coding: utf-8 -*-
from facepy.exceptions import FacepyError


class SignedRequestError(FacepyError):
    """Exception for invalid signed requests."""
