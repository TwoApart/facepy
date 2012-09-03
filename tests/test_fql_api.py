"""Tests for the ``fql_api`` module."""

import json

from nose.tools import *
from mock import patch

from facepy import GraphAPI, FqlAPI


patch = patch('requests.session')


def mock():
    global mock_request

    mock_request = patch.start()().request


def unmock():
    patch.stop()


@with_setup(mock, unmock)
def test_legacy_fql():
    graph = GraphAPI('<access token>')

    mock_request.return_value.content = json.dumps({
        'id': 1,
        'name': 'Thomas \'Herc\' Hauk',
        'first_name': 'Thomas',
        'last_name': 'Hauk',
        'link': 'http://facebook.com/herc',
        'username': 'herc',
    })

    try:
        graph.fql('SELECT id,name,first_name,last_name,username FROM user WHERE uid=me()')
    except GraphAPI.FacebookError:
        pass

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/fql?q=SELECT+id%2Cname%2Cfirst_name%2Clast_name%2Cusername+FROM+user+WHERE+uid%3Dme%28%29',
        allow_redirects=True,
        params={
            'access_token': '<access token>'
        }
    )


@with_setup(mock, unmock)
def test_fql():
    fql = FqlAPI('<access token>')

    mock_request.return_value.content = json.dumps({
        'id': 1,
        'name': 'Thomas \'Herc\' Hauk',
        'first_name': 'Thomas',
        'last_name': 'Hauk',
        'link': 'http://facebook.com/herc',
        'username': 'herc',
    })

    try:
        fql.get('SELECT id,name,first_name,last_name,username FROM user WHERE uid=me()')
    except FqlAPI.FacebookError:
        pass

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/fql?q=SELECT+id%2Cname%2Cfirst_name%2Clast_name%2Cusername+FROM+user+WHERE+uid%3Dme%28%29',
        allow_redirects=True,
        params={
            'access_token': '<access token>'
        }
    )
