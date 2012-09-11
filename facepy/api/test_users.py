# -*- coding: utf-8 -*-
from facepy.api.base import BaseApi


class TestUser(BaseApi):
    def __init__(self, app_id, access_token=False, url='https://graph.facebook.com'):
        self.app_id = app_id
        self.path = '%s/accounts/test-users' % self.app_id
        super(TestUser, self).__init__(access_token=access_token, url=url)

    def get(self, retry=3):
        return self.client.get(path=self.path, retry=retry)

    def create(self, installed=True, permissions=None, name=None, locale='en_US', retry=3):
        data = {
            'installed': installed,
            'locale': locale,
        }

        if permissions:
            if not isinstance(permissions, (list, set, tuple)):
                permissions = (permissions,)
            data['permissions'] = ','.join(permissions)

        if name:
            data['name'] = name

        return self.client.post(
            path=self.path,
            data=data,
            retry=retry
        )

    def add(self, uid, owner_access_token, installed=True, permissions=None, retry=3):
        data = {
            'uid': uid,
            'owner_access_token': owner_access_token,
            'installed': installed,
        }

        if permissions:
            if not isinstance(permissions, (list, set, tuple)):
                permissions = (permissions,)
            data['permissions'] = ','.join(permissions)

        return self.client.post(
            path=self.path,
            data=data,
            retry=retry
        )
