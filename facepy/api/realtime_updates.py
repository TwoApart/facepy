# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import os
import sys
import time
import traceback

from facepy.api.base import BaseApi
from facepy.exceptions import FacepyError


def handle_callbacks_and_exceptions(f):
    """
    Decorator to handle the `on_success` and `on_error` callbacks that might
    be passed to the handlers.

    If given, the `on_success` callback will always execute after the handler.
    Also, if given, the `on_error` callback will always execute after a known
    exception (`UpdatesHandlerError` exceptions).

    The results from these callbacks, if any, are passed along in the result
    (as the last two parameters of the result tuple).

    Finally, the decorator handles the potential known exceptions as 403's and
    passes the exception info (`sys.exc_info()`) as the last argument to the
    on_error callback. This way, the `on_error` callback can decide what to do
    with it (re-raise it, ignore it, log it, etc.).
    """
    def do_handler(*args, **kwargs):
        on_success = kwargs.pop('on_success') if 'on_success' in kwargs else None
        on_error = kwargs.pop('on_error') if 'on_error' in kwargs else None

        success = error = None
        try:
            http_code, http_content, http_content_type = f(*args, **kwargs)

            if on_success:
                success = on_success(*args[1:], **kwargs)
        except RealtimeUpdates.UpdatesHandlerError:
            exc_info = sys.exc_info()
            try:
                if on_error:
                    error = on_error(*(args[1:] + (exc_info,)), **kwargs)
            except:
                print >> sys.stderr, "Error processing on_error() callback:"
                traceback.print_exc()
            finally:
                http_code, http_content, http_content_type = (403, None, None)

        return (
            http_code,
            http_content,
            http_content_type,
            success,
            error
        )

    return do_handler


class RealtimeUpdates(BaseApi):
    """
    The Graph API supports real-time updates to enable your application using
    Facebook to subscribe to changes in data in Facebook.

    See `Facebook's realtime subscriptions API documentation
    <http://developers.facebook.com/docs/reference/api/realtime/>`_ for
    detailed documentation.
    """

    def __init__(self, app_id, app_secret, access_token=False, url='https://graph.facebook.com'):
        """
        Initialize RealtimeUpdates with the application ID, the application
        secret and the application OAuth access token.

        :param app_id: A string describing an application ID.
        :param app_secret: A string describing an application secret.
        :param access_token: A string describing an application OAuth access
        token.
        :param url: A string describing the GraphAPI endpoint.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.path = '%s/subscriptions' % self.app_id
        super(RealtimeUpdates, self).__init__(access_token=access_token, url=url)

    def get(self, retry=3):
        """
        List each of your subscribed objects and their subscribed fields.
        """
        return self.client.get(
            path=self.path,
            retry=retry
        )

    def _encode_token(self, token, timestamp=None):
        """
        Encode the given token adding tampering and replay protection through
        a signed timestamp.

        :param token: A string representing the `verify_token`.
        :param timestamp: The timestamp in seconds since the epoch. If none
        given, it defaults to the now() epoch.
        """
        def encode(decoded):
            return base64.urlsafe_b64encode(decoded).rstrip('=')

        timestamp = timestamp or int(time.time())
        timestamped_token = '%s+%s' % (token, timestamp)

        signature = hmac.new(self.app_secret, timestamped_token, hashlib.sha1).digest()

        return encode("%s@%s" % (timestamped_token, signature))

    def _decode_token(self, signed_token, max_delta=30):
        """
        Decode the given signed token, checking the timestamp and tampering
        protection.

        :param signed_token: A string with the signed token.
        :param max_delta: The maximum allowed deviation from the encoded
        timestamp, in seconds. If none given, it defaults to 30 seconds.
        """
        def decode(encoded):
            padding = '=' * (len(encoded) % 4)
            return base64.urlsafe_b64decode(encoded + padding)

        try:
            timestamped_token, signature = decode(signed_token).split('@')
            token, t = timestamped_token.split('+')
        except:
            raise self.SignedTokenError("Malformed signed token")

        now = int(time.time())
        if abs(now - int(t)) > max_delta:
            raise self.SignedTokenError("Invalid time in token")

        if signed_token != self._encode_token(token, t):
            raise self.SignedTokenError("Signed token signature mismatch")

        return token

    def subscribe(self, obj, fields, callback_url, verify_token=None, retry=0):
        """
        Sets up a realtime update subscription to the given `fields` of the
        given `obj`. Facebook will use the provided `callback_url` and
        `verify_token` (if given) to approve the subscription.

        See `"Add or Modify a subscription" in Facebook's realtime updates API
        documentation
        <https://developers.facebook.com/docs/reference/api/realtime/>`_ for
        further details.

        :param obj: A string describing the type of object to subscribe
        :param fields: A list of properties or connections on the specified
        object to monitor.
        :param callback_url: A callback URL to which Facebook will post
        subscription updates.
        :param verify_token: A string token that Facebook will send back in
        the verification request to assist in the verification of the
        authenticity of the request.
        """
        verify_token = verify_token or os.urandom(8)  # 64 entropy bits

        verify_token = self._encode_token(verify_token)

        return self.client.post(
            path=self.path,
            retry=retry,
            object=obj,
            fields=','.join(fields),
            callback_url=callback_url,
            verify_token=verify_token
        )

    def delete(self, obj=None, retry=3):
        """
        Deletes all of your subscriptions. If `obj` is set, it will only
        delete the corresponding object's subscription.

        :param obj: A string specifying the type of subscribed object to
        delete.
        """
        options = {} if not obj else {'object': obj}

        return self.client.delete(
            path=self.path,
            retry=retry,
            **options
        )

    @handle_callbacks_and_exceptions
    def handler_get(self, mode, challenge, verify_token):
        """
        GET Subscription server handler.

        :param mode: A string describing the subscription mode. Only
        'subscribe' is supported at the moment.
        :param challenge: A random string.
        :param verify_token: A string token that Facebook is sending back in
        the verification request to assist in the verification of the
        authenticity of the request.

        See `"Subscription Verification" in
        Facebook's realtime subscriptions API documentation
        <https://developers.facebook.com/docs/reference/api/realtime/>`_ for
        further details.
        """
        if mode != 'subscribe':
            # 422 Unprocessable Entity
            # http://tools.ietf.org/html/rfc4918#section-11.2
            return (422, None, None)

        # If decoding the verify_token does not raise any exceptions,
        # everything is OK
        self._decode_token(verify_token)

        return (200, challenge, 'text/plain')

    @handle_callbacks_and_exceptions
    def handler_post(self, payload, signature):
        """
        POST Subscription server handler.

        :param payload: A JSON-encoded string containing one or more updates.
        :param signature: A string with the signature of the payload and the
        algorithm used for signing.

        See `"Change Notifications" in Facebook's realtime subscriptions API
        documentation
        <https://developers.facebook.com/docs/reference/api/realtime/>`_ for
        further details.
        """
        if not signature:
            # 422 Unprocessable Entity
            # http://tools.ietf.org/html/rfc4918#section-11.2
            return (422, None, None)

        algorithm, payload_signature = signature.split('=')

        # Although FB indicates support for SHA1 only, it doesn't hurt to
        # support other algorithms as long as our system knows about it :)
        if algorithm not in hashlib.algorithms:
            # 422 Unprocessable Entity
            # http://tools.ietf.org/html/rfc4918#section-11.2
            return (422, None, None)

        digestmod = getattr(hashlib, algorithm)
        expected_signature = hmac.new(
            self.app_secret,
            payload,
            digestmod
        ).hexdigest()

        if expected_signature != payload_signature:
            raise self.UpdatesHandlerError("Invalid signature in payload")

        return (200, None, None)

    class SignedTokenError(FacepyError):
        """Exception for invalid signed tokens."""

    class UpdatesHandlerError(FacepyError):
        """Base exception for errors in the subscriptions handlers."""
