# -*- coding: utf-8 -*-
import json

from nose.tools import *
from mock import patch

from facepy.api import GraphApi


patch = patch('requests.session')


def mock():
    global mock_request

    mock_request = patch.start()().request


def unmock():
    patch.stop()


@with_setup(mock, unmock)
def test_graphapi_search():
    api = GraphApi('<access token>')

    mock_request.return_value.content = json.dumps({
        'data': [
            {
                'message': 'I don\'t like your chair.'
            },
            {
                'message': 'Don\'t let your mouth get your ass in trouble.'
            }
        ]
    })

    api.search(
        term='shaft quotes',
        type='post'
    )

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/search',
        allow_redirects=True,
        params={
            'q': 'shaft quotes',
            'type': 'post',
            'access_token': '<access token>'
        }
    )


@with_setup(mock, unmock)
def test_graphapi_search_invalid():
    api = GraphApi('<access token>')

    assert_raises(api.Error, api.search, 'shaft', 'movies')


@with_setup(mock, unmock)
def test_graphapi_fql():
    api = GraphApi('<access token>')

    mock_request.return_value.content = json.dumps({
        'id': 1,
        'name': 'Thomas \'Herc\' Hauk',
        'first_name': 'Thomas',
        'last_name': 'Hauk',
        'link': 'http://facebook.com/herc',
        'username': 'herc',
    })

    try:
        api.fql('SELECT id,name,first_name,last_name,username FROM user WHERE uid=me()')
    except api.FacebookError:
        pass

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/fql?q=SELECT+id%2Cname%2Cfirst_name%2Clast_name%2Cusername+FROM+user+WHERE+uid%3Dme%28%29',
        allow_redirects=True,
        params={
            'access_token': '<access token>'
        }
    )
