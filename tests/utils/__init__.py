# -*- coding: utf-8 -*-
from nose.tools import *

from facepy.utils import SignedRequest


TEST_FACEBOOK_APPLICATION_SECRET_KEY = '<application secret key>'

TEST_PAYLOAD = {
    'user_id': '123456789',
    'algorithm': 'HMAC-SHA256',
    'expires': 0,
    'oauth_token': '<oauth token>',
    'user': {
        'locale': 'en_US',
        'country': 'no',
        'age': {'min': 21}
    },
    'issued_at': 1234567890,
}

TEST_SIGNED_REQUEST = u'' \
    '2yyrlvRGMor7fXj3nugvUZsBeBpc_9cNGIeNS4-5rFY=' + '.' + \
    'eyJ1c2VyX2lkIjoiMTIzNDU2Nzg5IiwiYWxnb3JpdGhtIjoiSE1B' \
    'Qy1TSEEyNTYiLCJleHBpcmVzIjowLCJvYXV0aF90b2tlbiI6Ijxv' \
    'YXV0aCB0b2tlbj4iLCJ1c2VyIjp7ImxvY2FsZSI6ImVuX1VTIiwi' \
    'Y291bnRyeSI6Im5vIiwiYWdlIjp7Im1pbiI6MjF9fSwiaXNzdWVk' \
    'X2F0IjoxMjM0NTY3ODkwfQ=='

TEST_SIGNED_REQUEST__UNKNOWN_ALGORITHM = u'' \
    '-6I6Qg1DQnbDcwkPEzgWhNvJWsazy6mZ-XjOdtGM-HI=' + '.' + \
    'eyJ1c2VyX2lkIjoiMTIzNDU2Nzg5IiwiYWxnb3JpdGhtIjoiPHVu' \
    'a25vd24gYWxnb3JpdGhtPiIsImV4cGlyZXMiOjAsIm9hdXRoX3Rv' \
    'a2VuIjoiPG9hdXRoIHRva2VuPiIsInVzZXIiOnsibG9jYWxlIjoi' \
    'ZW5fVVMiLCJjb3VudHJ5Ijoibm8iLCJhZ2UiOnsibWluIjoyMX19' \
    'LCJpc3N1ZWRfYXQiOjEyMzQ1Njc4OTB9'


def test_signedrequest_encode():
    sr = SignedRequest(TEST_FACEBOOK_APPLICATION_SECRET_KEY)

    signed_request = sr.encode(TEST_PAYLOAD)

    assert signed_request == TEST_SIGNED_REQUEST


def test_signedrequest_decode():
    sr = SignedRequest(TEST_FACEBOOK_APPLICATION_SECRET_KEY)

    payload = sr.decode(TEST_SIGNED_REQUEST)

    assert payload == TEST_PAYLOAD


def test_signedrequest_decode_invalid_signed_request():
    sr = SignedRequest(TEST_FACEBOOK_APPLICATION_SECRET_KEY)

    assert_raises(
        SignedRequest.Error,
        sr.decode,
        "<invalid signed request>"
    )


def test_signedrequest_decode_unknown_algorithm():
    sr = SignedRequest(TEST_FACEBOOK_APPLICATION_SECRET_KEY)

    assert_raises(
        SignedRequest.Error,
        sr.decode,
        TEST_SIGNED_REQUEST__UNKNOWN_ALGORITHM
    )


def test_signedrequest_decode_incorrect_signature():
    sr = SignedRequest(TEST_FACEBOOK_APPLICATION_SECRET_KEY)

    encoded_signature, _ = TEST_SIGNED_REQUEST__UNKNOWN_ALGORITHM.split('.')
    _, encoded_payload = TEST_SIGNED_REQUEST.split('.')

    assert_raises(
        SignedRequest.Error,
        sr.decode,
        u"%s.%s" % (encoded_signature, encoded_payload)
    )
