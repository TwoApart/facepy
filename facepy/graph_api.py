import abc
import base64
import hashlib
import hmac
try:
    import simplejson as json
except ImportError:
    import json  # flake8: noqa
import os
import requests
import sys
import time
import traceback

from urllib import urlencode

from facepy.exceptions import *


class BaseGraphAPI(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, oauth_token=False, url='https://graph.facebook.com'):
        """
        Initialize GraphAPI with an OAuth access token.

        :param oauth_token: A string describing an OAuth access token.
        :param url: A string describing the GraphAPI endpoint.
        """
        self.oauth_token = oauth_token
        self.session = requests.session()
        self.url = url.strip('/')

    def _parse(self, data):
        """
        Parse the response from Facebook's Graph API.

        :param data: A string describing the Graph API's response.
        """
        try:
            data = json.loads(data)
        except ValueError:
            return data

        # Facebook's Graph API sometimes responds with 'true' or 'false'.
        # Facebook offers no documentation as to the prerequisites for this
        # type of response, though it seems that it responds with 'true' when
        # objects are successfully deleted and 'false' upon attempting to
        # delete or access an item that one does not have access to.
        #
        # For example, the API would respond with 'false' upon attempting to
        # query a feed item without having the 'read_stream' extended
        # permission. If you were to query the entire feed, however, it would
        # respond with an empty list instead.
        #
        # Genius.
        #
        # We'll handle this discrepancy as gracefully as we can by
        # implementing logic to deal with this behavior in the high-level
        # access functions (get, post, delete etc.).
        if type(data) is dict:
            if 'error' in data:
                error = data['error']

                if error.get('type') == "OAuthException":
                    exception = OAuthError
                else:
                    exception = FacebookError

                raise exception(
                    error.get('message'),
                    error.get('code', None)
                )

            # Facebook occasionally reports errors in its legacy error format.
            if 'error_msg' in data:
                raise FacebookError(
                    data.get('error_msg'),
                    data.get('error_code', None)
                )

        return data

    def _query(self, method, path, data=None, page=False, retry=0):
        """
        Fetch an object from the Graph API and parse the output, returning a tuple where the first item
        is the object yielded by the Graph API and the second is the URL for the next page of results, or
        ``None`` if results have been exhausted.

        :param method: A string describing the HTTP method.
        :param path: A string describing the object in the Graph API.
        :param data: A dictionary of HTTP GET parameters (for GET requests) or POST data (for POST requests).
        :param page: A boolean describing whether to return an iterator that iterates over each page of results.
        :param retry: An integer describing how many times the request may be retried.
        """
        data = data or {}

        def load(method, url, data):
            try:
                if method in ['GET', 'DELETE']:
                    response = self.session.request(method, url, params=data, allow_redirects=True)

                if method in ['POST', 'PUT']:
                    files = {}

                    for key in data:
                        if hasattr(data[key], 'read'):
                            files[key] = data[key]

                    for key in files:
                        data.pop(key)

                    response = self.session.request(method, url, data=data, files=files)
            except requests.RequestException as exception:
                raise HTTPError(exception.message)

            result = self._parse(response.content)

            try:
                next_url = result['paging']['next']
            except (KeyError, TypeError):
                next_url = None

            return result, next_url

        def paginate(method, url, data):
            while url:
                result, url = load(method, url, data)

                # Reset pagination parameters.
                for key in ['offset', 'until', 'since']:
                    if key in data:
                        del data[key]

                yield result

        # Convert option lists to comma-separated values.
        for key in data:
            if isinstance(data[key], (list, set, tuple)) and all([isinstance(item, basestring) for item in data[key]]):
                data[key] = ','.join(data[key])

        # Support absolute paths too
        if not path.startswith('/'):
            path = '/' + str(path)

        url = '%s%s' % (self.url, path)

        if self.oauth_token:
            data['access_token'] = self.oauth_token

        try:
            if page:
                return paginate(method, url, data)
            else:
                return load(method, url, data)[0]
        except FacepyError:
            if retry:
                return self._query(method, path, data, page, retry - 1)
            else:
                raise

    def get(self, path='', page=False, retry=3, **options):
        """
        Get an item from the Graph API.

        :param path: A string describing the path to the item.
        :param page: A boolean describing whether to return a generator that
                     iterates over each page of results.
        :param retry: An integer describing how many times the request may be retried.
        :param options: Graph API parameters such as 'limit', 'offset' or 'since'.

        See `Facebook's Graph API documentation <http://developers.facebook.com/docs/reference/api/>`_
        for an exhaustive list of parameters.
        """
        response = self._query(
            method='GET',
            path=path,
            data=options,
            page=page,
            retry=retry
        )

        if response is False:
            raise FacebookError('Could not get "%s".' % path)

        return response

    def post(self, path='', retry=0, **data):
        """
        Post an item to the Graph API.

        :param path: A string describing the path to the item.
        :param retry: An integer describing how many times the request may be retried.
        :param data: Graph API parameters such as 'message' or 'source'.

        See `Facebook's Graph API documentation <http://developers.facebook.com/docs/reference/api/>`_
        for an exhaustive list of options.
        """
        response = self._query(
            method='POST',
            path=path,
            data=data,
            retry=retry
        )

        if response is False:
            raise FacebookError('Could not post to "%s"' % path)

        return response

    def delete(self, path, retry=3, **data):
        """
        Delete an item in the Graph API.

        :param path: A string describing the path to the item.
        :param retry: An integer describing how many times the request may be retried.
        :param data: Graph API parameters.
        """
        response = self._query(
            method='DELETE',
            path=path,
            data=data,
            retry=retry
        )

        if response is False:
            raise FacebookError('Could not delete "%s"' % path)

        return response

    # Proxy exceptions for ease of use and backwards compatibility.
    FacebookError = FacebookError
    OAuthError = OAuthError
    HTTPError = HTTPError


class GraphAPI(BaseGraphAPI):
    def search(self, term, type, page=False, retry=3, **options):
        """
        Search for an item in the Graph API.

        :param term: A string describing the search term.
        :param type: A string describing the type of items to search for.
        :param page: A boolean describing whether to return a generator that
                     iterates over each page of results.
        :param retry: An integer describing how many times the request may be retried.
        :param options: Graph API parameters, such as 'center' and 'distance'.

        Supported types are ``post``, ``user``, ``page``, ``event``, ``group``, ``place`` and ``checkin``.

        See `Facebook's Graph API documentation <http://developers.facebook.com/docs/reference/api/>`_
        for an exhaustive list of options.
        """
        SUPPORTED_TYPES = ['post', 'user', 'page', 'event', 'group', 'place', 'checkin']

        if type not in SUPPORTED_TYPES:
            raise ValueError('Unsupported type "%s". Supported types are %s' % (type, ', '.join(SUPPORTED_TYPES)))

        options = dict({
            'q': term,
            'type': type,
        }, **options)

        response = self._query('GET', 'search', options, page, retry)

        return response

    def batch(self, requests):
        """
        Make a batch request.

        :param requests: A list of dictionaries with keys 'method', 'relative_url' and optionally 'body'.

        Yields a list of responses and/or exceptions.
        """

        for request in requests:
            if 'body' in request:
                request['body'] = urlencode(request['body'])

        responses = self.post(
            batch=json.dumps(requests)
        )

        for response, request in zip(responses, requests):
            # Facilitate for empty Graph API responses.
            #
            # https://github.com/jgorset/facepy/pull/30
            if not response:
                yield None
                continue

            try:
                yield self._parse(response['body'])
            except FacepyError as exception:
                exception.request = request
                yield exception

    def fql(self, query, retry=3):
        """
        Backwards compatibility wrapper.
        -- WILL BE DEPRECATED SOON --
        """
        fql = FqlAPI(self.oauth_token)
        return fql.get(query, retry)


class FqlAPI(BaseGraphAPI):
    def get(self, query, retry=3):
        """
        Use FQL to powerfully extract data from Facebook.

        :param query: A FQL query or FQL multiquery ({'query_name': "query",...})
        :param retry: An integer describing how many times the request may be retried.

        See `Facebook's FQL documentation <http://developers.facebook.com/docs/reference/fql/>`_
        for an exhaustive list of details.
        """
        path = 'fql?%s' % urlencode({'q': query})
        return super(FqlAPI, self).get(path=path, retry=retry)


def handle_callbacks_and_exceptions(f):
    """
    Decorator to handle the `on_success` and `on_error` callbacks that might
    be passed to the handlers.

    If given, the `on_success` callback will always execute after the handler.
    Also, if given, the `on_error` callback will always execute after a known
    exception (`SubscriptionsHandlerError` exceptions).

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
        except SubscriptionsHandlerError:
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


class SubscriptionsAPI(BaseGraphAPI):
    """
    The Graph API supports real-time updates to enable your application using
    Facebook to subscribe to changes in data in Facebook.

    See `Facebook's realtime subscriptions API documentation
    <http://developers.facebook.com/docs/reference/api/realtime/>`_ for
    detailed documentation.
    """

    def __init__(self, app_id, app_secret, oauth_token=False, url='https://graph.facebook.com'):
        """
        Initialize SubscriptionsAPI with the application ID, the application
        secret and the application OAuth access token.

        :param app_id: A string describing an application ID.
        :param app_secret: A string describing an application secret.
        :param oauth_token: A string describing an application OAuth access
        token.
        :param url: A string describing the GraphAPI endpoint.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.path = '%s/subscriptions' % self.app_id
        super(SubscriptionsAPI, self).__init__(oauth_token, url)

    def get(self, retry=3):
        """
        List each of your subscribed objects and their subscribed fields.
        """
        return super(SubscriptionsAPI, self).get(
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
            raise SignedTokenError("Malformed signed token")

        now = int(time.time())
        if abs(now - int(t)) > max_delta:
            raise SignedTokenError("Invalid time in token (expired or future)")

        if signed_token != self._encode_token(token, t):
            raise SignedTokenError("Signed token signature mismatch")

        return token

    def post(self, obj, fields, callback_url, verify_token=None, retry=0):
        """
        Sets up a realtime subscription to the given `fields` of the given
        `obj`. Facebook will use the provided `callback_url` and
        `verify_token` (if given) to approve the subscription.

        See `"Add or Modify a Subscription" in Facebook's realtime
        subscriptions API documentation
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

        return super(SubscriptionsAPI, self).post(
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

        return super(SubscriptionsAPI, self).delete(
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
        algorithm, payload_signature = signature.split('=')

        # Although FB indicates support for SHA1 only, it doesn't hurt to
        # support other algorithms as long as our system knows about it :)
        if algorithm not in hashlib.algorithms:
            # 422 Unprocessable Entity
            # http://tools.ietf.org/html/rfc4918#section-11.2
            return (422, None, None)

        digestmod = getattr(hashlib, algorithm)
        expected_signature = hmac.new(self.app_secret, payload, digestmod).hexdigest()

        if expected_signature != payload_signature:
            raise SubscriptionsHandlerError("Invalid signature in payload")

        return (200, None, None)

    # Proxy exceptions for ease of use and backwards compatibility.
    SignedTokenError = SignedTokenError
    SubscriptionsHandlerError = SubscriptionsHandlerError
