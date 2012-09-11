# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
try:
    import simplejson as json
except ImportError:
    import json  # flake8: noqa

from facepy.utils.exceptions import SignedRequestError


class SignedRequest(object):
    """
    https://developers.facebook.com/docs/authentication/signed_request/
    """
    def __init__(self, application_secret_key):
        self.application_secret_key = application_secret_key

    def _sign(self, data):
        return hmac.new(
            self.application_secret_key,
            msg=data,
            digestmod=hashlib.sha256
        ).digest()

    def encode(self, payload):
        """
        Encodes a signed request from the given payload.

        :param payload: A dictionary with the payload to encode.
        """
        def encode(decoded):
            return base64.urlsafe_b64encode(decoded)

        encoded_payload = encode(json.dumps(payload, separators=(',', ':')))
        encoded_signature = encode(self._sign(encoded_payload))

        return '%s.%s' % (encoded_signature, encoded_payload)
    encode.ALGORITHM = 'HMAC-SHA256'

    def decode(self, signed_request):
        """
        Decode a signed request, returning a dictionary with its payload.

        :param signed_request: A string with the signed request.
        """
        def decode(encoded):
            padding = '=' * (len(encoded) % 4)
            return base64.urlsafe_b64decode(encoded + padding)

        try:
            encoded_signature, encoded_payload = signed_request.split('.')
            signature = decode(str(encoded_signature))
            payload = json.loads(decode(str(encoded_payload)))
        except (TypeError, ValueError):
            raise self.Error("Corrupt payload")

        if payload.get('algorithm', '').upper() != self.encode.ALGORITHM:
            raise self.Error("Unknown algorithm")

        if signature != self._sign(encoded_payload):
            raise self.Error("Signature mismatch")

        return payload

    Error = SignedRequestError
