# -*- coding: utf-8 -*-
from facepy.exceptions import FacepyError


class GraphClientError(FacepyError):
    """Base class for exceptions raised by GraphClient."""


class HTTPError(GraphClientError):
    """Exception for transport errors."""


class FacebookError(GraphClientError):
    """Exception for Facebook errors."""


class OAuthError(FacebookError):
    """Exception for Facebook OAuth errors."""
