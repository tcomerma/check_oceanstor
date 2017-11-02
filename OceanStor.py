"""Connect to OceanStor device and get information."""
#
# There are implemented just a few functions for our monitoring needs, but
# the capabilitites are huge. EVERYTHING on an OceanStor can be done using
# the API. If not convinced, connect the browser to the device and fire up
# developer tools. You will see the browser is using the API for doing the
# job.
# Google "Huawei OceanStor REST API" for the documentation
#
# Toni Comerma
# Octubre 2017
#
# Modifications
import urllib
import urllib2
import ssl
import json
import datetime
from cookielib import CookieJar


class OceanStorError(Exception):
    """Class for OceanStor derived errors."""

    def __init__(self, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "An error occured connecting to OceanStor"
        super(OceanStorError, self).__init__(msg)


class OceanStor(object):
    """Class that connects to OceanStor device and gets information."""

    def __init__(self, host, system_id, username, password, timeout):
        self.host = host
        self.system_id = system_id
        self.username = username
        self.password = password
        self.timeout = timeout
        # Create reusable http components
        self.cookies = CookieJar()
        ###### Comment out following lines for python 2.6 ######
        self.ctx = ssl.create_default_context()
        # Ignorar validesa del certificat
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        # Afegir debuglevel=1 a HTTPSHandler per depurar crides
        self.opener = urllib2.build_opener(urllib2.HTTPSHandler(context=self.ctx),
                                           urllib2.HTTPCookieProcessor(self.cookies))
        ###### Until here and uncomment these #####
        ######
        #self.opener = urllib2.build_opener(urllib2.HTTPSHandler(),
        #                                   urllib2.HTTPCookieProcessor(self.cookies))
        ###### Until #####
        self.opener.addheaders = [('Content-Type', 'application/json; charset=utf-8')]


    def alarm_level_text(self, level):
        if level == 3:
            return "warning"
        elif level == 4:
            return "major"
        elif level == 5:
            return "critical"
        else:
            return "unknown"

    def date_to_human(self, timestamp):
        return datetime.datetime.fromtimestamp(
                        int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    def login(self):
        try:
            formdata = {"username": self.username, "password": self.password, "scope": "0"}
            url = "https://{0}:8088/deviceManager/rest/{1}/sessions".\
                  format(self.host, self.system_id)
            response = self.opener.open(url, json.dumps(formdata))
            content = response.read()
            response_json = json.loads(content)
            # Comprvar login ok
            if response_json['error']['code'] != 0:
                print "ERROR: Got an error response from system ({0})".\
                      format(response_json['error']['code'])
                return False
            self.iBaseToken = response_json['data']['iBaseToken']
            self.opener.addheaders = [('iBaseToken', self.iBaseToken)]
        except Exception as e:
            print "HTTP Exception: {0}".format(e)
            return False
        return True

    def logout(self):
        try:
            url = "https://{0}:8088/deviceManager/rest/{1}/sessions".\
                  format(self.host, self.system_id)
            request = urllib2.Request(url)
            request.get_method = lambda: 'DELETE'
            f = self.opener.open(request)
            content = f.read()
        except:
            # No error control. We are quitting anyway
            return


    def alarms(self):
        a = list()
        try:
            url = "https://{0}:8088/deviceManager/rest/{1}/alarm/currentalarm".\
                  format(self.host, self.system_id)
            response = self.opener.open(url)
            content = response.read()
            response_json = json.loads(content)
            # Comprovar si alarmes
            if response_json['error']['code'] != 0:
                return [["warning", "now", "Got an error response from system ({0})".\
                        response_json['error']['code']]]
            for i in response_json["data"]:
                a.append([self.alarm_level_text(i["level"]),
                          self.date_to_human(i["startTime"]),
                          i["description"]])
        except Exception as e:
            return [["warning", "now", "HTTP Exception: {0}".format(e)]]
        return a


    def filesystems(self, pattern):
        a = list()
        try:
            if "*" in pattern:
                wildcard = True
                pattern = pattern.replace('*', '')
            else:
                wildcard = False
            url = "https://{0}:8088/deviceManager/rest/{1}/filesystem?".\
                  format(self.host, self.system_id)
            url = url + urllib.urlencode({'filter': 'NAME:{0}'.
                                          format(pattern)})
            response = self.opener.open(url)
            content = response.read()
            response_json = json.loads(content)
            # Comprovar si request ok
            if response_json['error']['code'] != 0:
                return None
            # Get interesting data into list
            for i in response_json["data"]:
                if (
                    (wildcard and i["NAME"].startswith(pattern)) or
                    (not wildcard and i["NAME"] == pattern)
                   ):
                    if i["ISCLONEFS"] == "false":
                        size = float(i["CAPACITY"])/1024/1024  # To GB
                        free = float(i["AVAILABLECAPCITY"])/1024/1024  # To GB
                        pctused = (1-(free/size))*100
                        a.append([i["NAME"],
                                  size,
                                  size-free,
                                  pctused])
        except Exception as e:
            print format(e)
            return None
        return a
