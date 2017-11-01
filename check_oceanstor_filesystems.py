#!/usr/bin/python
"""Check free space on OceanStor storage devices using API."""
#
#
# Toni Comerma
# October 2017
#
# Changes:
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


def signal_handler(signal, frame):
    """Handle timeouts, exiting with a nice message."""
    print('Execution aborted: Timeout or Ctrl+C')
    sys.exit(3)


def us(warning, critical):
    """Print usage information."""
    print 'check_oceanstor_filesystems.py -H -s -u -p -n [-w] [-c] [-t] [-h]'
    print "  -H, --host     : IP or DNS address"
    print "  -s, --system   : System_id of the OceanStor"
    print "  -u, --username : username to log into"
    print "  -p, --password : password"
    print "  -n, --name     : Name of the filesystem to check."
    print "                   You can add a '*' at the end to match longer"
    print "                   prefixes. No regexp allowed"
    print "  -w, --warning  : Minimun % of free space expected before warning"
    print "                   defaults to {0}".format(warning)
    print "  -c, --critical : Minimun % of free space expected before critical"
    print "                   defaults to {0}".format(critical)
    print "  -t, --timeout  : timeout in seconds"
    print "  -h, --help     : This text"


def main(argv):
    """Do the checking."""
    # Parametres
    host = None
    system_id = None
    username = None
    password = None
    timeout = 10
    warning = 75
    critical = 90

    #   Llegir parametres de linia de comandes
    try:
        opts, args = getopt.getopt(argv,
                                   "hH:s:u:p:t:n:w:c:",
                                   ["host=",
                                    "help",
                                    "system=",
                                    "username=",
                                    "password=",
                                    "timeout=",
                                    "name=",
                                    "warning",
                                    "critical"])
    except getopt.GetoptError:
        sys.exit(3)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            us(warning, critical)
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
            timeout = arg
        elif opt in ("-w", "--warning"):
            warning = int(arg)
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-c", "--critical"):
            critical = int(arg)

    #   Verificacions sobre els parametres
    for i in [host, system_id, username, password, timeout, name]:
        if i is None:
            print 'ERROR: Missing mandatory parameter'
            us(warning, critical)
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

    # Checking...
    text = ""
    performance = "|"
    warnings = 0
    criticals = 0
    criticalfs = ""
    warningfs = ""
    okfs = ""
    fs = os.filesystems(name)
    if fs is None:
        print "ERROR: filesystem {0} not found" . format(name)
        sys.exit(2)
    for i in fs:
        prefix = "OK:"
        if i[3] < critical:
            criticals = criticals + 1
            criticalfs = criticalfs + " " + i[0]
            prefix = "CRITICAL:"
        elif i[3] < warning:
            warnings = warnings + 1
            warningfs = warningfs + " " + i[0]
            prefix = "WARNING:"
        else:
            okfs = okfs + " " + i[0]
        text = text + "{0} filesystem {1}: size:{2:6.0f}, free:{3:6.0f}, pctfree: {4:5.2f}%\n"\
              .format(prefix, i[0], i[1], i[2], i[3])
        performance = performance + " '{0}'={1:5.2f}%".format(i[0], i[3])
    if criticals > 0:
        print "CRITICAL: [{0}] in CRITICAL state, [{1}] in WARNING state, [{2}] OK"\
              .format(criticalfs, warningfs, okfs)
        print text + performance
        exit(2)
    elif warnings > 0:
        print "WARNING: [{0}] in WARNING state, [{1}] OK"\
              .format(warningfs, okfs)
        print text + performance
        sys.exit(1)
    else:
        print "OK: [{0}] OK".format(okfs)
        print text + performance
        sys.exit(0)

    # No s'hauria d'arribar aqui, pero per si les mosques
    print "OK. Nothing monitored so far."
    sys.exit(0)


####################################################
# Crida al programa principal
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main(sys.argv[1:])
