import types
from uritemplate import expand

from pybitbucket.bitbucket import Client


def open_files(filelist):
    files = []
    for filename in filelist:
        files.append(('file', (filename, open(filename, 'rb'))))
    return files


class Role(object):
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, CONTRIBUTOR, MEMBER]


class Snippet(object):
    @staticmethod
    def make_payload(
            is_private=None,
            is_unlisted=None,
            title=None,
            scm=None):
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        payload = {}
        if is_private is not None:
            payload.update({'is_private': is_private})
        if is_unlisted is not None:
            payload.update({'is_unlisted': is_unlisted})
        if title is not None:
            payload.update({'title': title})
        if scm is not None:
            payload.update({'scm': scm})
        return payload

    @staticmethod
    def create_snippet(
            files,
            is_private=None,
            is_unlisted=None,
            title=None,
            scm=None,
            client=Client()):
        template = 'https://{+bitbucket_url}/2.0/snippets/{username}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username()
            })
        payload = Snippet.make_payload(is_private, is_unlisted, title, scm)
        response = client.session.post(url, data=payload, files=files)
        Client.expect_ok(response)
        return Snippet(response.json(), client=client)

    @staticmethod
    def find_snippets_for_role(role=Role.OWNER, client=Client()):
        if role not in Role.roles:
            raise NameError("role '%s' is not in [%s]" %
                            (role, '|'.join(str(x) for x in Role.roles)))
        template = 'https://{+bitbucket_url}/2.0/snippets{?role}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'role': role})
        for snip in client.remote_relationship(url):
            yield snip

    @staticmethod
    def find_snippet_by_id(id, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/snippets/{username}/{id}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username(),
                'id': id
            })
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return Snippet(response.json(), client=client)

    @staticmethod
    def is_type(data):
        return data.get('id') and not data.get('destination')

    def __init__(self, data, client=Client()):
        self.data = data
        # Need some special handling for booleans.
        # Might be workaround for bug in the response JSON?
        for (is_a, value) in data.iteritems():
            if is_a.startswith('is_'):
                data[is_a] = (value in ('True', 'true'))
        self.client = client
        self.__dict__.update(data)
        for link, body in data['links'].iteritems():
            if link == 'clone':
                self.clone = {item['name']: item['href'] for item in body}
            else:
                for head, url in body.iteritems():
                    setattr(
                        self,
                        link,
                        types.MethodType(
                            self.client.remote_relationship,
                            url))
        if data.get('files'):
            self.filenames = [str(f) for f in data['files']]

    def __repr__(self):
        return "Snippet({})".repr(self.data)

    def __unicode__(self):
        return "Snippet id:{}".format(self.id)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def modify(
            self,
            files=open_files([]),
            is_private=None,
            is_unlisted=None,
            title=None):
        payload = self.make_payload(is_private, is_unlisted, title)
        response = self.client.session.put(
            self.links['self']['href'],
            data=payload,
            files=files)
        Client.expect_ok(response)
        return Snippet(response.json(), client=self.client)

    def delete(self):
        response = self.client.session.delete(self.links['self']['href'])
        # Deletes the snippet and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return

    def content(self, filename):
        if not self.files.get(filename):
            return
        url = self.files[filename]['links']['self']['href']
        response = self.client.session.get(url)
        Client.expect_ok(response)
        return response.content

Client.bitbucket_types.add(Snippet)
