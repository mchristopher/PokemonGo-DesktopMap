"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

from __future__ import absolute_import
from future.standard_library import install_aliases
install_aliases()

import re
import six
import json
import logging
import requests

from urllib.parse import parse_qs

from pgoapi.auth import Auth
from pgoapi.utilities import get_time
from pgoapi.exceptions import AuthException

from requests.exceptions import ConnectionError

class AuthPtc(Auth):

    PTC_LOGIN_URL = 'https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
    PTC_LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'
    PTC_LOGIN_CLIENT_SECRET = 'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR'

    def __init__(self):
        Auth.__init__(self)

        self._auth_provider = 'ptc'

        self._session = requests.session()
        self._session.verify = True

    def set_proxy(self, proxy_config):
        self._session.proxies = proxy_config

    def user_login(self, username, password):
        self.log.info('PTC User Login for: {}'.format(username))

        if not isinstance(username, six.string_types) or not isinstance(password, six.string_types):
            raise AuthException("Username/password not correctly specified")

        head = {'User-Agent': 'niantic'}

        try:
            r = self._session.get(self.PTC_LOGIN_URL, headers=head)
        except ConnectionError as e:
            raise AuthException("Caught ConnectionError: %s", e)

        try:
            jdata = json.loads(r.content.decode('utf-8'))
            data = {
                'lt': jdata['lt'],
                'execution': jdata['execution'],
                '_eventId': 'submit',
                'username': username,
                'password': password,
            }
        except ValueError as e:
            self.log.error('PTC User Login Error - Field missing in response: %s', e)
            return False
        except KeyError as e:
            self.log.error('PTC User Login Error - Field missing in response.content: %s', e)
            return False

        r1 = self._session.post(self.PTC_LOGIN_URL, data=data, headers=head)

        ticket = None
        try:
            ticket = re.sub('.*ticket=', '', r1.history[0].headers['Location'])
        except Exception as e:
            try:
                self.log.error('Could not retrieve token: %s', r1.json()['errors'][0])
            except Exception as e:
                self.log.error('Could not retrieve token! (%s)', e)
            return False

        self._refresh_token = ticket
        self.log.info('PTC User Login successful.')

        self.get_access_token()
        return self._login

    def set_refresh_token(self, refresh_token):
        self.log.info('PTC Refresh Token provided by user')
        self._refresh_token = refresh_token

    def get_access_token(self, force_refresh = False):
        token_validity = self.check_access_token()

        if token_validity is True and force_refresh is False:
            self.log.debug('Using cached PTC Access Token')
            return self._access_token
        else:
            if force_refresh:
                self.log.info('Forced request of PTC Access Token!')
            else:
                self.log.info('Request PTC Access Token...')

            data1 = {
                'client_id': 'mobile-app_pokemon-go',
                'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
                'client_secret': self.PTC_LOGIN_CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'code': self._refresh_token,
            }

            r2 = self._session.post(self.PTC_LOGIN_OAUTH, data=data1)

            qs = r2.content.decode('utf-8')
            token_data = parse_qs(qs)

            access_token = token_data.get('access_token', None)
            if access_token is not None:
                self._access_token = access_token[0]

                now_s = get_time()
                # set expiration to an hour less than value received because Pokemon OAuth
                # login servers return an access token with an explicit expiry time of
                # three hours, however, the token stops being valid after two hours.
                # See issue #86
                expires = int(token_data.get('expires', [0])[0]) - 3600
                if expires > 0:
                    self._access_token_expiry = expires + now_s
                else:
                    self._access_token_expiry = 0

                self._login = True

                self.log.info('PTC Access Token successfully retrieved.')
                self.log.debug('PTC Access Token: %s...', self._access_token[:25])
            else:
                self._access_token = None
                self._login = False
                raise AuthException("Could not retrieve a PTC Access Token")



