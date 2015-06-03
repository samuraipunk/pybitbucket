import types
from uritemplate import expand

from pybitbucket.bitbucket import Client
from pybitbucket.user import User


class TeamRole(object):
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [ADMIN, CONTRIBUTOR, MEMBER]


class Team(object):
    @staticmethod
    def find_teams_for_role(role=TeamRole.ADMIN, client=Client()):
        if role not in TeamRole.roles:
            raise NameError("role '%s' is not in [%s]" %
                            (role, '|'.join(str(x) for x in TeamRole.roles)))
        template = 'https://{+bitbucket_url}/2.0/teams{?role}'
        url = expand(template, {'bitbucket_url': client.get_bitbucket_url(),
                                'role': role})
        for team in client.paginated_get(url):
            yield Team(team, client=client)

    @staticmethod
    def find_team_by_username(username, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/teams/{username}'
        url = expand(template, {'bitbucket_url': client.get_bitbucket_url(),
                                'username': username})
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return Team(response.json(), client=client)

    @staticmethod
    def remote_relationship(url, client=Client()):
        # TODO: avatar
        for item in client.paginated_get(url):
            if item['type'] == 'user':
                # followers, following, members
                yield User(item, client=client)
            else:
                # repositories
                yield item

    def __init__(self, dict, client=Client()):
        self.dict = dict
        self.client = client
        self.__dict__.update(dict)
        for link, href in dict['links'].iteritems():
            for head, url in href.iteritems():
                setattr(self, link, types.MethodType(
                    Team.remote_relationship, url, self.client))

    def __repr__(self):
        return "Team({})".repr(self.dict)

    def __unicode__(self):
        return "Team username:{}".format(self.username)

    def __str__(self):
        return unicode(self).encode('utf-8')
