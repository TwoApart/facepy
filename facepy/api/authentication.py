# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from urlparse import parse_qs

from facepy.api.base import BaseApi
from facepy.client import GraphClient


class OAuth(BaseApi):
    """
    This class mediates in getting application OAuth tokens from Facebook.

    Relevant links:

    https://developers.facebook.com/docs/authentication/
    https://developers.facebook.com/roadmap/offline-access-removal/
    """
    def __init__(self, url='https://graph.facebook.com'):
        self.path = 'oauth/access_token'
        super(OAuth, self).__init__(access_token=False, url=url)

    def get_application_access_token(self, application_id, application_secret_key):
        """
        Get an OAuth access token for the given application.

        :param application_id: An integer describing a Facebook application
        ID.
        :param application_secret_key: A string describing a Facebook
        application secret key.

        NOTE: it seems this will be deprecated from Oct 3rd 2012 onwards:
        https://developers.facebook.com/roadmap/offline-access-removal/
        """
        response = self.client.get(
            path=self.path,
            client_id=application_id,
            client_secret=application_secret_key,
            grant_type='client_credentials'
        )

        data = parse_qs(response)

        try:
            token = data['access_token'][0]
        except KeyError:
            raise self.OAuthError('No access token given')

        return token

    def get_extended_access_token(self, application_id, application_secret_key, access_token):
        """
        Get an extended OAuth access token.

        :param application_id: An integer describing a Facebook application
        ID.
        :param application_secret_key: A string describing a Facebook
        application secret key.
        :param access_token: A string describing an OAuth access token.

        Returns a (token, expires_at) where:
            - token is a string describing the extended access token
            - expires_at is a datetime instance describing when the token
              expires.
        """
        response = self.client.get(
            path=self.path,
            client_id=application_id,
            client_secret=application_secret_key,
            grant_type='fb_exchange_token',
            fb_exchange_token=access_token
        )

        data = parse_qs(response)

        try:
            token = data['access_token'][0]
            expires_at = datetime.now() + timedelta(seconds=int(data['expires'][0]))
        except KeyError:
            raise self.OAuthError('No access token or expiration given')

        return token, expires_at

    OAuthError = GraphClient.OAuthError
