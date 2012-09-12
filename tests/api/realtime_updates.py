# -*- coding: utf-8 -*-
import json

from nose.tools import *
from mock import patch

from facepy.api import RealtimeUpdates
from facepy.api.realtime_updates import handle_callbacks_and_exceptions


patch = patch('requests.session')


def mock():
    global mock_request

    mock_request = patch.start()().request


def unmock():
    patch.stop()


class MockTime(object):
    def __init__(self, delta=0):
        self._now = 1234567890 + delta

    def __enter__(self, *args, **kwargs):
        time = __import__('time', globals(), locals(), [], -1)
        time.time = lambda: self._now

    def __exit__(self, *args, **kwargs):
        time = __import__('time', globals(), locals(), [], -1)  # flake8: noqa


class StdRedirector(object):
    """std[out|err] redirector"""
    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout or None
        self.stderr = stderr or None

    def __enter__(self, *args, **kwargs):
        sys = __import__('sys', globals(), locals(), [], -1)

        if self.stdout:
            sys.stdout = self.stdout

        if self.stderr:
            sys.stderr = self.stderr

    def __exit__(self, *args, **kwargs):
        sys = __import__('sys', globals(), locals(), [], -1)  # flake8: noqa


def test_encode_token():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')
    token = '<token>'
    ## '<token>+1234567890@<signature>'
    expected_encoded_token = 'PHRva2VuPisxMjM0NTY3ODkwQFy4wfO2tbXyLltUUusqT2yeJfCr'

    with MockTime():
        encoded_token = updates._encode_token(token)

    assert encoded_token == expected_encoded_token


def test_decode_token():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')
    ## '<token>+1234567890@<signature>'
    encoded_token = 'PHRva2VuPisxMjM0NTY3ODkwQFy4wfO2tbXyLltUUusqT2yeJfCr'
    expected_token = '<token>'

    with MockTime(delta=30):
        assert expected_token == updates._decode_token(encoded_token)


def test_decode_token_expired_time():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')
    ## '<token>+1234567890@<signature>'
    encoded_token = 'PHRva2VuPisxMjM0NTY3ODkwQFy4wfO2tbXyLltUUusqT2yeJfCr'
    expected_token = '<token>'

    with MockTime(delta=31):
        assert_raises(
            RealtimeUpdates.SignedTokenError,
            updates._decode_token,
            encoded_token
        )


def test_decode_token_infinite_time():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')
    ## '<token>+1234567890@<signature>'
    encoded_token = 'PHRva2VuPisxMjM0NTY3ODkwQFy4wfO2tbXyLltUUusqT2yeJfCr'
    expected_token = '<token>'

    with MockTime(delta=3600):
        assert expected_token == updates._decode_token(encoded_token, max_delta=float('Inf'))


def test_decode_token_signature_mismatch():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')
    ## '<token>+1234567890@<malformed signature>'
    encoded_token_bad_signature = 'PHRva2VuPisxMjM0NTY3ODkwQDxtYWxmb3JtZWQgc2lnbmF0dXJlPg'

    with MockTime():
        assert_raises(
            RealtimeUpdates.SignedTokenError,
            updates._decode_token,
            encoded_token_bad_signature
        )


def test_decode_token_malformed_encoded_token():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    assert_raises(
        RealtimeUpdates.SignedTokenError,
        updates._decode_token,
        '<malformed encoded token>'
    )


@with_setup(mock, unmock)
def test_updates_get():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    mock_request.return_value.content = json.dumps({
        'data': [
            {
                "object": "user",
                "callback_url": "http://www.xyz.com/sub_endpoint?xyz_token=123",
                "fields": ["email", "friends", "name", "picture"],
                "active": True
            },
            {
                "object": "permissions",
                "callback_url": "http://www.xyz.com/sub_endpoint?xyz_token=123",
                "fields": ["email", "read_stream"],
                "active": True
            },
            {
                "object": "errors",
                "callback_url": "http://www.otherdomain.com/sub_endpoint?xyz_token=456",
                "fields": ["canvas"],
                "active": True
            }
        ]
    })

    try:
        response = updates.get()
    except RealtimeUpdates.FacebookError:
        pass

    mock_request.assert_called_with(
        'GET',
        'https://graph.facebook.com/<app id>/subscriptions',
        allow_redirects=True,
        params={
            'access_token': updates.client.oauth_token
        }
    )


@with_setup(mock, unmock)
def test_updates_subscribe():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    mock_request.return_value.content = json.dumps({})

    retry = 0
    obj = '<object>'
    fields = ['<field1>', '<field2>']
    callback_url = '<callback URL>'
    verify_token = '<random data>'

    try:
        response = updates.subscribe(
            obj=obj,
            fields=fields,
            callback_url=callback_url,
            verify_token=verify_token
        )
    except RealtimeUpdates.FacebookError:
        pass

    mock_request.assert_called_with(
        'POST',
        'https://graph.facebook.com/%s' % updates.path,
        files={},
        data={
            'access_token': updates.client.oauth_token,
            'object': obj,
            'fields': ','.join(fields),
            'callback_url': callback_url,
            'verify_token': updates._encode_token(verify_token),
        }
    )


@with_setup(mock, unmock)
def test_updates_delete_object():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    mock_request.return_value.content = json.dumps({})

    obj = '<object>'

    try:
        response = updates.delete(obj=obj)
    except RealtimeUpdates.FacebookError:
        pass

    mock_request.assert_called_with(
        'DELETE',
        'https://graph.facebook.com/%s' % updates.path,
        allow_redirects=True,
        params={
            'access_token': updates.client.oauth_token,
            'object': obj,
        }
    )


@with_setup(mock, unmock)
def test_updates_delete_all():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    mock_request.return_value.content = json.dumps({})

    try:
        response = updates.delete()
    except RealtimeUpdates.FacebookError:
        pass

    mock_request.assert_called_with(
        'DELETE',
        'https://graph.facebook.com/%s' % updates.path,
        allow_redirects=True,
        params={
            'access_token': updates.client.oauth_token,
        }
    )


def test_handle_callbacks_and_exceptions():
    handler_result = (
        200,
        '<http content>',
        '<http content type>',
    )

    def handler():
        return handler_result

    noop = lambda *args, **kwargs: None
    expected_result = handler_result + (noop(), noop(),)

    decorated = handle_callbacks_and_exceptions(handler)

    assert expected_result == decorated(on_success=noop, on_error=noop)


def test_handle_callbacks_and_exceptions_with_errors():
    def handler():
        raise RealtimeUpdates.UpdatesHandlerError('<some error>')

    noop = lambda *args, **kwargs: None
    expected_result = (403, None, None, noop(), noop(),)

    decorated = handle_callbacks_and_exceptions(handler)

    assert_equals(decorated(on_success=noop, on_error=noop), expected_result)


def test_handle_callbacks_and_exceptions_with_double_errors():
    def handler():
        raise RealtimeUpdates.UpdatesHandlerError('<some error>')

    noop = lambda *args, **kwargs: None

    expected_exception = '<some other error>'

    def on_error(*args, **kwargs):
        raise Exception(expected_exception)

    expected_result = (403, None, None, noop(), None,)

    decorated = handle_callbacks_and_exceptions(handler)

    from cStringIO import StringIO
    stderr = StringIO()

    with StdRedirector(stderr=stderr):
        result = decorated(on_success=noop, on_error=on_error)
        assert_equals(result, expected_result)
        assert expected_exception in stderr.getvalue()


def test_handler_get():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    challenge = '<challenge>'
    verify_token = 'PHRva2VuPisxMjM0NTY3ODkwQFy4wfO2tbXyLltUUusqT2yeJfCr'
    expected_result = (200, challenge, 'text/plain', None, None)

    assert_equals(expected_result, updates.handler_get(
        'subscribe',
        challenge,
        verify_token
    ))


def test_handler_get_unexpected_mode():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    challenge = verify_token = '<irrelevant>'
    expected_result = (422, None, None, None, None)

    assert_equals(expected_result, updates.handler_get(
        '<unexpected mode>',
        challenge,
        verify_token
    ))


def test_handler_post():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    payload = '<payload>'
    signature = 'sha1=9c1603f6f4da3ff063dff0692c0fe02f1b5b990a'
    expected_result = (200, None, None, None, None)

    assert_equals(expected_result, updates.handler_post(
        payload,
        signature
    ))


def test_handler_post_missing_signature_header():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    payload = '<irrelevant>'
    signature = None
    expected_result = (422, None, None, None, None)

    assert_equals(expected_result, updates.handler_post(
        payload,
        signature
    ))


def test_handler_post_invalid_signature_algorithm():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    payload = '<irrelevant>'
    signature = '<invalid algorithm>=<irrelevant>'
    expected_result = (422, None, None, None, None)

    assert_equals(expected_result, updates.handler_post(
        payload,
        signature
    ))


def test_handler_post_invalid_signature():
    updates = RealtimeUpdates('<app id>', '<app secret>', access_token='<access token>')

    payload = '<payload>'
    signature = 'sha1=<invalid signature>'
    expected_result = (403, None, None, None, None)

    assert_equals(expected_result, updates.handler_post(
        payload,
        signature
    ))
