# -*- coding: utf-8 -*-
import json
from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client, enum


PermissionScope = enum(
    'PermissionScope',
    EMAIL='email',
    ACCOUNT_READ='account',
    ACCOUNT_WRITE='account:write',
    TEAM_READ='team',
    TEAM_WRITE='team:write',
    REPOSITORY_READ='repository',
    REPOSITORY_WRITE='repository:write',
    REPOSITORY_ADMIN='repository:admin',
    PULLREQUEST_READ='pullrequest',
    PULLREQUEST_WRITE='pullrequest:write',
    ISSUE_READ='issue',
    ISSUE_WRITE='issue:write',
    WIKI='wiki',
    SNIPPET_READ='snippet',
    SNIPPET_WRITE='snippet:write',
    WEBHOOK='webhook')


class Consumer(BitbucketBase):
    id_attribute = 'id'
    links_json = """
{
  "_links": {
    "self": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers{/consumer_id}"
    },
    "owner": {
      "href": "{+bitbucket_url}/1.0/users{/username}"
    },
    "consumers": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers"
    }
  }
}
"""

    @staticmethod
    def is_type(data):
        return (
            (data.get('id') is not None) and
            (data.get('name') is not None) and
            (data.get('secret') is not None) and
            (data.get('key') is not None))

    @staticmethod
    def expand_link_urls(data, **kwargs):
        payload = {}
        for name, template in BitbucketBase.links_from(data):
            url = expand(template, kwargs)
            payload.update({name: {'href': url}})
        return payload

    def __init__(self, data, client=Client()):
        super(Consumer, self).__init__(data, client=client)
        self.links = Consumer.expand_link_urls(
            json.loads(self.links_json),
            bitbucket_url=client.get_bitbucket_url(),
            username=client.get_username(),
            consumer_id=data.get('id'))
        self.add_remote_relationship_methods(
            json.loads(Consumer.links_json))

    @staticmethod
    def get_link(name):
        links = json.loads(Consumer.links_json)
        template = links.get('_links', {}).get(name, {}).get('href')
        return template

    @staticmethod
    def payload(
            name=None,
            scopes=None,
            description=None,
            url=None,
            callback_url=None):
        payload = []
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        if name is not None:
            payload.append(('name', name))
        if scopes is not None:
            Consumer.expect_list('scopes', scopes)
            [PermissionScope.expect_valid_value(s) for s in scopes]
            [payload.append(('scope', s)) for s in scopes]
        if description is not None:
            payload.append(('description', description))
        if url is not None:
            payload.append(('url', url))
        if callback_url is not None:
            payload.append(('callback_url', callback_url))
        return payload

    @staticmethod
    def create(
            name,
            scopes,
            description=None,
            url=None,
            callback_url=None,
            client=Client()):
        post_url = expand(
            Consumer.get_link('consumers'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        payload = Consumer.payload(
            name=name,
            scopes=scopes,
            description=description,
            url=url,
            callback_url=callback_url)
        # Note: The Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return Consumer.post(post_url, data=payload, client=client)

    """
    A convenience method for changing the current consumer.
    The parameters make it easier to know what can be changed.
    """
    def update(
            self,
            name=None,
            scopes=None,
            description=None,
            url=None,
            callback_url=None):
        kwargs = {k: v for k, v in locals().items() if k != 'self'}
        payload = self.payload(**kwargs)
        # Note: The Bitbucket API expects a urlencoded-form, not json.
        # Hence, use `data` instead of `json`.
        return self.put(data=payload)

    """
    Find consumers for the authenticated user.
    The method is a generator Consumer objects.
    """
    @staticmethod
    def find_consumers(client=Client()):
        url = expand(
            Consumer.get_link('consumers'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        # Can't use typical `remote_relationship` on lists from 1.0 API.
        # Instead, we assume the shape is a list of Consumer resources.
        response = client.session.get(url)
        client.expect_ok(response)
        json_data = response.json()
        for item in json_data:
            yield client.convert_to_object(item)

    """
    Finding a specific consumer by id for the authenticated user.
    """
    @staticmethod
    def find_consumer_by_id(consumer_id, client=Client()):
        url = expand(
            Consumer.get_link('self'), {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username(),
                'consumer_id': consumer_id,
            })
        return next(client.remote_relationship(url))


Client.bitbucket_types.add(Consumer)
