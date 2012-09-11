# -*- coding: utf-8 -*-
from nose.tools import *
from mock import patch

from facepy.client import GraphClient
from facepy.api import TestUser


@patch.object(GraphClient, 'get')
def test_get(get):
    get.return_value = {'data': [
        {
            'id': '<testuser id 1>',
            'access_token': '<testuser access token 1>',
            'login_url': '<testuser login url 1>',
        },
        {
            'id': '<testuser id 2>',
            'access_token': '<testuser access token 2>',
            'login_url': '<testuser login url 2>',
        },
    ]}

    tu = TestUser('<application id>', '<access token>')

    test_users = tu.get()

    get.assert_called_with(
        path='<application id>/accounts/test-users',
        retry=3
    )

    assert test_users == get.return_value


@patch.object(GraphClient, 'post')
def test_create(post):
    post.return_value = {
        'id': '<id>',
        'access_token': '<access token>',
        'login_url': '<login url>',
        'email': '<email>',
        'password': '<password>',
    }

    tu = TestUser('<application id>', '<access token>')

    data = {
        'installed': True,
        'permissions': 'read_stream',
        'name': 'John Doe',
        'locale': 'en_US',
    }

    test_user = tu.create(**data)

    post.assert_called_with(
        path='<application id>/accounts/test-users',
        data=data,
        retry=3
    )

    assert test_user == post.return_value


@patch.object(GraphClient, 'post')
def test_add(post):
    post.return_value = {
        'id': '<id>',
        'access_token': '<access token>',
        'login_url': '<login url>',
        'email': '<email>',
        'password': '<password>',
    }

    tu = TestUser('<application id>', '<access token>')

    data = {
        'uid': '<id>',
        'owner_access_token': '<owner access token>',
        'installed': True,
        'permissions': 'read_stream',
    }

    test_user = tu.add(**data)

    post.assert_called_with(
        path='<application id>/accounts/test-users',
        data=data,
        retry=3
    )

    assert test_user == post.return_value
