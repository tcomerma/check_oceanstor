check_oceanstor

Nagios plugin for monitoring Huawei OceanStor storage devices using the API

Commands implemented
    check_oceanstor_alarms.py: Checks for active alarms
    check_oceanstor_filesystems.py: Checks free space on filesystems

Just an small subset of what is possible is implemented, but it's what we need.
EVERYTHING on an OceanStor can be done using the API. If not convinced,
connect the browser to the device and fire up developer tools. You will see
the browser is using the API for doing the job.
Google "Huawei OceanStor REST API" for the documentation

Feel free to fork and extend

Author: Toni Comerma
        CCMA, SA
