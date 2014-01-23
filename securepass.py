#!/usr/bin/python
##
## Generic SecurePass Class to access APIs of Dreamliner
## www.secure-pass.net
##
## Contains some code from Ganeti project (c) Google Inc.
##
## (c) 2013 Giuseppe Paterno' (gpaterno@gpaterno.com)
##          GARL Sagl (www.garl.ch)
##

import logging
import pycurl
import json
import urllib
from StringIO import StringIO

HTTP_APP_JSON = "application/json"
USER_AGENT = "SecurePass CLI"
HTTP_GET = "GET"
HTTP_PUT = "PUT"
HTTP_POST = "POST"

# Older pycURL versions don't have all error constants
try:
  _CURLE_SSL_CACERT = pycurl.E_SSL_CACERT
  _CURLE_SSL_CACERT_BADFILE = pycurl.E_SSL_CACERT_BADFILE
except AttributeError:
  _CURLE_SSL_CACERT = 60
  _CURLE_SSL_CACERT_BADFILE = 77

_CURL_SSL_CERT_ERRORS = frozenset([
  _CURLE_SSL_CACERT,
  _CURLE_SSL_CACERT_BADFILE,
  ])

class SecurePass(object):

    def __init__(self, app_id=None, app_secret=None, endpoint=None, logger=logging):
        """ Inizialize the class
        """

        self.app_id = app_id
        self.app_secret = app_secret
        self._logger = logger

        if endpoint is not None:
            self.endpoint = endpoint
        else:
            self.endpoint = "https://beta.secure-pass.net/"


    def _SendRequest(self, method, path, content=None):

        """Sending CURL request
           Method is GET/POST
           Path is the subpath of the request
           Content is a dictionary
        """
        assert path.startswith("/")

        curl = pycurl.Curl()

        # Default cURL settings
        curl.setopt(pycurl.VERBOSE, False)
        curl.setopt(pycurl.FOLLOWLOCATION, False)
        curl.setopt(pycurl.MAXREDIRS, 5)
        curl.setopt(pycurl.NOSIGNAL, True)
        curl.setopt(pycurl.USERAGENT, USER_AGENT)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)
        curl.setopt(pycurl.SSL_VERIFYPEER, False)
        curl.setopt(pycurl.HTTPHEADER, [
          "Accept: %s" % HTTP_APP_JSON,
          "Content-type: %s" % HTTP_APP_JSON,
          "X-SecurePass-App-ID: %s" % self.app_id,
          "X-SecurePass-App-Secret: %s" % self.app_secret,
          ])

        url = "%s%s" % (self.endpoint, path)

        self._logger.debug("Sending request %s %s (content=%r)",
                           method, url, content)

        # Buffer for response
        encoded_resp_body = StringIO()

        # Configure cURL
        curl.setopt(pycurl.CUSTOMREQUEST, str(method))
        curl.setopt(pycurl.URL, str(url))
        curl.setopt(pycurl.WRITEFUNCTION, encoded_resp_body.write)

        if content is not None:
            curl.setopt(pycurl.POSTFIELDS, urllib.urlencode(content))

        try:
          # Send request and wait for response
          try:
            curl.perform()
          except pycurl.error, err:
            if err.args[0] in _CURL_SSL_CERT_ERRORS:
              self._logger.error("SSL certificate error %s" % err,
                                  code=err.args[0])

        finally:
          # Reset settings to not keep references to large objects in memory
          # between requests
          curl.setopt(pycurl.POSTFIELDS, "")
          curl.setopt(pycurl.WRITEFUNCTION, lambda _: None)

        # Was anything written to the response buffer?
        if encoded_resp_body.tell():
          response_content = json.loads(encoded_resp_body.getvalue())
        else:
          response_content = None

        return response_content


    ##
    ## SecurePass Utilities
    ##

    def ping(self):
        """ Ping the SecurePass server and get some information
        """
        response = self._SendRequest(HTTP_GET, "/api/v1/ping")

        if response['rc'] == 0:
            return "Ping from IPv%s address %s" % (response['ip_version'], response['ip'])
        else:
            raise Exception(response['errorMsg'])

    def log(self, message=""):
        """ Log a message to the central logging facility
        """

        request = {}
        request['MESSAGE'] = message
        response = self._SendRequest(HTTP_POST, "/api/v1/log", content=request)

        if response['rc'] == 0:
            print "Log sent"
        else:
            print response['errorMsg']

    ##
    ## SecurePass Application handling
    ##

    # List apps
    def app_list(self, realm=None):
        """ Get the list of applications in your realm
        """

        request = {}
        tmpapp = []

        if realm is not None:
            request['REALM'] = realm

        response = self._SendRequest(HTTP_POST, "/api/v1/apps/list", content=request)

        if response['rc'] == 0:
            for app in response['APP_ID']:
                tmpapp.append(app)

            return tmpapp
        else:
            raise Exception(response['errorMsg'])


    # Application info
    def app_info(self, app_id=None):
        """ Get information about given application
        """

        request = {}
        if app_id is not None:
            request['APP_ID'] = app_id

        response = self._SendRequest(HTTP_POST, "/api/v1/apps/info", content=request)

        if response['rc'] == 0:

            del response['rc']
            del response['errorMsg']

            return response

        else:
            raise Exception(response['errorMsg'])

    # Create application
    def app_add(self, label="", allow_network_ipv4=None, allow_network_ipv6=None,
                write=False, group=None, realm=None):
        """ Add an application to SecurePass
        """

        request = {}

        request['LABEL'] = label
        request['WRITE'] = write

        if allow_network_ipv4 is not None:
            request['ALLOW_NETWORK_IPv4'] = allow_network_ipv4

        if allow_network_ipv6 is not None:
            request['ALLOW_NETWORK_IPv6'] = allow_network_ipv6

        if group is not None:
            request['GROUP'] = group

        if realm is not None:
            request['REALM'] = realm


        response = self._SendRequest(HTTP_POST, "/api/v1/apps/add", content=request)

        if response['rc'] == 0:

            del response['rc']
            del response['errorMsg']

            return response

        else:
            raise Exception(response['errorMsg'])


    # Delete The application
    def app_delete(self, app_id=None):
        """ Delete an application
        """

        request = {}
        if app_id is not None:
            request['APP_ID'] = app_id

        response = self._SendRequest(HTTP_POST, "/api/v1/apps/delete", content=request)

        if response['rc'] == 0:

            del response['rc']
            del response['errorMsg']

            return response

        else:
            raise Exception(response['errorMsg'])


    ## Modify the application
    # Create application
    def app_modify(self, app_id=None, label=None, allow_network_ipv4=None, allow_network_ipv6=None,
                write=None, group=None, realm=None):
        """ Add an application to SecurePass
        """

        request = {}

        if app_id is not None:
            request['APP_ID'] = app_id

        if label is not None:
            request['LABEL'] = label

        if write is not None:
            request['WRITE'] = write

        if allow_network_ipv4 is not None:
            request['ALLOW_NETWORK_IPv4'] = allow_network_ipv4

        if allow_network_ipv6 is not None:
            request['ALLOW_NETWORK_IPv6'] = allow_network_ipv6

        if group is not None:
            request['GROUP'] = group

        if realm is not None:
            request['REALM'] = realm


        response = self._SendRequest(HTTP_POST, "/api/v1/apps/modify", content=request)

        if response['rc'] == 0:

            del response['rc']
            del response['errorMsg']

            return response

        else:
            raise Exception(response['errorMsg'])


    ##
    ## SecurePass Users handling
    ##

    # List users
    def user_list(self, realm=None):
        """ Get the list of applications in your realm
        """

        request = {}
        tmpuser = []

        if realm is not None:
            request['REALM'] = realm

        response = self._SendRequest(HTTP_POST, "/api/v1/users/list", content=request)

        if response['rc'] == 0:
            for user in response['username']:
                tmpuser.append(user)

            return tmpuser
        else:
            raise Exception(response['errorMsg'])

    ## Get user info
    def user_info(self, realm=None, user=None):
        """ Get the details of a user in your realm
        """

        request = {}

        if realm is not None:
            request['REALM'] = realm

        if user is not None:
            request['USERNAME'] = user

        response = self._SendRequest(HTTP_POST, "/api/v1/users/info", content=request)

        if response['rc'] == 0:
            del response['rc']
            del response['errorMsg']

            return response

        else:
            raise Exception(response['errorMsg'])

    ## Authenticate user
    def user_auth(self, user=None, secret=None):
        """ Authenticate the user
        """

        request = {}

        if user is not None:
            request['USERNAME'] = user

        if secret is not None:
            request['SECRET'] = secret


        response = self._SendRequest(HTTP_POST, "/api/v1/users/auth", content=request)

        if response['rc'] == 0:
            return response['authenticated']

        else:
            raise Exception(response['errorMsg'])


    ## Add a user
    def user_add(self, user=None, name=None, surname=None,
                 email=None, mobile=None, nin=None, rfid=None, manager=None):
        """ Add a user into the realm
        """

        request = {}

        if user is not None:
            request['USERNAME'] = user

        if name is not None:
            request['NAME'] = name

        if surname is not None:
            request['SURNAME'] = surname

        if email is not None:
            request['EMAIL'] = email

        if mobile is not None:
            request['MOBILE'] = mobile

        if nin is not None:
            request['NIN'] = nin

        if rfid is not None:
            request['RFID'] = rfid

        if manager is not None:
            request['MANAGER'] = manager

        response = self._SendRequest(HTTP_POST, "/api/v1/users/add", content=request)

        if response['rc'] == 0:
            return response['username']

        else:
            raise Exception(response['errorMsg'])


    ## Remove a user
    def user_del(self, user=None):
        """ Remove a user
        """

        request = {}

        if user is not None:
            request['USERNAME'] = user

        response = self._SendRequest(HTTP_POST, "/api/v1/users/del", content=request)

        if response['rc'] == 0:
            return True

        else:
            raise Exception(response['errorMsg'])


    ## Remove a user
    def user_provision(self, user=None, swtoken=None):
        """ Remove a user
        """

        request = {}
        SWTOKENS = ('iphone', 'android', 'blackberry', 'software')

        if user is not None:
            request['USERNAME'] = user

        if swtoken is not None and swtoken.lower() in SWTOKENS:
            request['SWTOKEN'] = swtoken.lower()

        response = self._SendRequest(HTTP_POST, "/api/v1/users/provision", content=request)

        if response['rc'] == 0:
            return True

        else:
            raise Exception(response['errorMsg'])