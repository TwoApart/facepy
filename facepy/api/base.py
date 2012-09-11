# -*- coding: utf-8 -*-
from facepy.client import GraphClient
from facepy.api.exceptions import BaseApiError


class BaseApi(object):
    def __init__(self, access_token=False, url='https://graph.facebook.com'):
        self.client = GraphClient(access_token, url)

    Error = BaseApiError
