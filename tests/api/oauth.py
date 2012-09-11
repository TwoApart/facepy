# -*- coding: utf-8 -*-
from datetime import datetime

from nose.tools import *
from mock import patch

from facepy.api import OAuth


patch = patch('requests.session')


def mock():
    global mock_request

    mock_request = patch.start()().request


def unmock():
    patch.stop()


@with_setup(mock, unmock)
def test_oauth_get_application_access_token():
    oauth = OAuth()

    mock_request.return_value.content = 'access_token=...'

    access_token = oauth.get_application_access_token(
        '<application id>',
        '<application secret key>'
    )

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/oauth/access_token',
        allow_redirects=True,
        params={
            'client_id': '<application id>',
            'client_secret': '<application secret key>',
            'grant_type': 'client_credentials'
        }
    )

    assert_equal(access_token, '...')


@with_setup(mock, unmock)
def test_oauth_get_application_access_token_raises_error():
    oauth = OAuth()

    mock_request.return_value.content = 'An unknown error occurred'

    assert_raises(
        oauth.OAuthError,
        oauth.get_application_access_token,
        '<application id>',
        '<application secret key>'
    )


@with_setup(mock, unmock)
def test_oauth_get_extended_access_token():
    oauth = OAuth()

    mock_request.return_value.content = 'access_token=<extended access token>&expires=5183994'

    access_token, expires_at = oauth.get_extended_access_token(
        '<application id>',
        '<application secret key>',
        '<access token>'
    )

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/oauth/access_token',
        allow_redirects=True,
        params={
            'client_id': '<application id>',
            'client_secret': '<application secret key>',
            'grant_type': 'fb_exchange_token',
            'fb_exchange_token': '<access token>'
        }
    )

    assert_equal(access_token, '<extended access token>')
    assert isinstance(expires_at, datetime)


@with_setup(mock, unmock)
def test_oauth_get_extended_access_token_raises_error():
    oauth = OAuth()

    mock_request.return_value.content = 'An unknown error occurred'

    assert_raises(
        oauth.OAuthError,
        oauth.get_extended_access_token,
        '<application id>',
        '<application secret key>',
        '<access token>'
    )
