#!/usr/bin/python
#!/# -*- coding: utf-8 -*-
"""Check alarms on OceanStor storage devices using API."""
#
#
# Toni Comerma
# October 2017
#
# Modificacions
#
# TODO:
#   https port number (8088) as parameter
#   verify thar numeric parameters are really numbers
#   better handling of exception situations in general

import sys
import getopt
import signal
import atexit
from OceanStor import OceanStor

# Constants


# Globals

def signal_handler(signal, frame):
    """Handle timeouts, exiting with a nice message."""
    print('UNKNOWN: Timeout contacting device or Ctrl+C')
    sys.exit(3)


def us():
    """Print usage information."""
    print 'check_oceanstor_alarms.py -H -s -u -p [-t] [-h]'
    print "  -H, --host     : IP or DNS address"
    print "  -s, --system   : System_id of the OceanStor"
    print "  -u, --username : username to log into"
    print "  -p, --password : password"
    print "  -t, --timeout  : timeout in seconds"
    print "  -h, --help     : This text"


def main(argv):

    # Parametres
    host = None
    system_id = None
    username = None
    password = None
    timeout = 10

    #   Llegir parametres de linia de comandes
    try:
        opts, args = getopt.getopt(argv,
                                   "hH:s:u:p:t:",
                                   ["host=",
                                    "help",
                                    "system=",
                                    "username=",
                                    "password=",
                                    "timeout="])
    except getopt.GetoptError:
        sys.exit(3)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            us()
            sys.exit()
        elif opt in ("-H", "--host"):
            host = arg
        elif opt in ("-s", "--system"):
            system_id = arg
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-t", "--timeout"):
            timeout = int(arg)

    #   Verificacions sobre els parametres
    for i in [host, system_id, username, password, timeout]:
        if i is None:
            print 'ERROR: Missing mandatory parameter'
            us()
            sys.exit(3)

    # Handle timeout
    signal.alarm(timeout)

    os = OceanStor(host, system_id, username, password, timeout)
    # Connectar
    if not os.login():
        print 'ERROR: Unable to login'
        sys.exit(3)
    # cleaup if logged in
    atexit.register(os.logout)

    num = 0
    text = ""
    severity = dict()
    for i in os.alarms():
        num = num + 1
        text = "{0}Severity:{1},Date={2},Description:{3}\n".format(
                text,
                i[0],
                i[1],
                i[2])
        if i[0] not in severity:
            severity[i[0]] = 1
        else:
            severity[i[0]] = severity[i[0]] + 1
    if num > 0:
        print "ERROR: {0} alarms found {1} | alarms={0}".format(num,
                                                                severity)
        print text
        exit(2)
    else:
        print "OK: no alarms found | alarms=0"
        exit(0)

    # No s'hauria d'arribar aqui, pero per si les mosques
    print "OK. Nothing monitored so far."
    sys.exit(0)


####################################################
# Crida al programa principal
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGALRM, signal_handler)
    main(sys.argv[1:])
