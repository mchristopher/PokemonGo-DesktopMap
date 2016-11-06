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

import six
import logging

from pgoapi.auth import Auth
from pgoapi.exceptions import AuthException
from gpsoauth import perform_master_login, perform_oauth

class AuthGoogle(Auth):

    GOOGLE_LOGIN_ANDROID_ID = '9774d56d682e549c'
    GOOGLE_LOGIN_SERVICE= 'audience:server:client_id:848232511240-7so421jotr2609rmqakceuu1luuq0ptb.apps.googleusercontent.com'
    GOOGLE_LOGIN_APP = 'com.nianticlabs.pokemongo'
    GOOGLE_LOGIN_CLIENT_SIG = '321187995bc7cdc2b5fc91b11a96e2baa8602c62'

    def __init__(self):
        Auth.__init__(self)

        self._auth_provider = 'google'
        self._refresh_token = None
        self._proxy = None

    def set_proxy(self, proxy_config):
        self._proxy = proxy_config

    def user_login(self, username, password):
        self.log.info('Google User Login for: {}'.format(username))

        if not isinstance(username, six.string_types) or not isinstance(password, six.string_types):
            raise AuthException("Username/password not correctly specified")

        user_login = perform_master_login(username, password, self.GOOGLE_LOGIN_ANDROID_ID, proxy=self._proxy)

        try:
            refresh_token = user_login.get('Token', None)
        except ConnectionError as e:
            raise AuthException("Caught ConnectionError: %s", e)

        if refresh_token is not None:
            self._refresh_token = refresh_token
            self.log.info('Google User Login successful.')
        else:
            self._refresh_token = None
            raise AuthException("Invalid Google Username/password")

        self.get_access_token()
        return self._login

    def set_refresh_token(self, refresh_token):
        self.log.info('Google Refresh Token provided by user')
        self._refresh_token = refresh_token

    def get_access_token(self, force_refresh = False):
        token_validity = self.check_access_token()

        if token_validity is True and force_refresh is False:
            self.log.debug('Using cached Google Access Token')
            return self._access_token
        else:
            if force_refresh:
                self.log.info('Forced request of Google Access Token!')
            else:
                self.log.info('Request Google Access Token...')

            token_data = perform_oauth(None, self._refresh_token, self.GOOGLE_LOGIN_ANDROID_ID, self.GOOGLE_LOGIN_SERVICE, self.GOOGLE_LOGIN_APP,
                self.GOOGLE_LOGIN_CLIENT_SIG, proxy=self._proxy)

            access_token = token_data.get('Auth', None)
            if access_token is not None:
                self._access_token = access_token
                self._access_token_expiry = int(token_data.get('Expiry', 0))
                self._login = True

                self.log.info('Google Access Token successfully received.')
                self.log.debug('Google Access Token: %s...', self._access_token[:25])
                return self._access_token
            else:
                self._access_token = None
                self._login = False
                raise AuthException("Could not receive a Google Access Token")
