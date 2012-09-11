# -*- coding: utf-8 -*-
from urllib import urlencode

from facepy.api.base import BaseApi
from facepy.client import GraphClient


class GraphApi(BaseApi):
    def search(self, term, type, page=False, retry=3, **options):
        """
        Search for an item in the Graph API.

        :param term: A string describing the search term.
        :param type: A string describing the type of GraphAPI object to search
        for.
        :param page: A boolean describing whether to return a generator that
        iterates over each page of results.
        :param retry: An integer describing how many times the request may be
        retried.
        :param options: Graph API parameters, such as 'center' and 'distance'.

        Supported types are ``post``, ``user``, ``page``, ``event``,
        ``group``, ``place`` and ``checkin``.

        See `Facebook's Graph API documentation
        <http://developers.facebook.com/docs/reference/api/>`_ for an
        exhaustive list of options.
        """
        if type not in self.search.SUPPORTED_OBJECTS:
            raise self.Error(
                'Unsupported type "%s". Supported types are %s' %
                (type, self.search.SUPPORTED_OBJECTS)
            )

        options = dict({
            'q': term,
            'type': type,
        }, **options)

        return self.client.get(
            'search',
            page=page,
            retry=retry,
            **options
        )
    search.SUPPORTED_OBJECTS = [
        'post', 'user', 'page', 'event', 'group', 'place', 'checkin',
    ]

    def fql(self, query, retry=3):
        """
        Use FQL to powerfully extract data from Facebook.

        :param query: A FQL query or FQL multiquery ({'query_name':
        "query",...})
        :param retry: An integer describing how many times the request may be
        retried.

        See `Facebook's FQL documentation
        <http://developers.facebook.com/docs/reference/fql/>`_ for an
        exhaustive list of details.
        """
        return self.client.get(
            path='fql?%s' % urlencode({'q': query}),
            retry=retry
        )

    FacebookError = GraphClient.FacebookError
