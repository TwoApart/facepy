# -*- coding: utf-8 -*-
from facepy.client import GraphClient
from facepy.exceptions import FacepyError


class BaseApi(object):
    def __init__(self, access_token=False, url='https://graph.facebook.com'):
        self.client = GraphClient(oauth_token=access_token, url=url)

    class Error(FacepyError):
        """Base class for exceptions raised by BaseApi."""

    FacebookError = GraphClient.FacebookError
