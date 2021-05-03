Quickstart
==========

Make sure you have Python 3.7+ installed. This server should be running on a machine that has 
OCEAN setup, and the Kraken Manager should have been used to start the processes. To connect to 
this server, the Kraken Monitor GUI can be used.

Python Packages
---------------

Install the required pip packages by running:

```
pip install -r requirements.txt
```

If developing this tool, install the dev dependencies by running:

```
pip install -r requirements-dev.txt
```

Running the Application
-----------------------

To start the application, simply start the ``run_server`` script. It's as easy as that.

```
python run_server.py
```

Additional options can be accessed via ``--help``:

```
usage: run_server.py [-h] [-p PORT] [-a ADDRESS]
                    [-r REAL_TIME [REAL_TIME ...]] [-l RATE_LIMIT] [-v] [-vv]
                    [-q] [-b] [--log-file LOG_FILE]

Kraken RPC Server - Serve statistics on Kraken monitored processes.

optional arguments:
-h, --help            show this help message and exit
-p PORT, --port PORT  Specify RPC server port.
-a ADDRESS, --address ADDRESS
                        Specify RPC server bind address.
-r REAL_TIME [REAL_TIME ...], --real-time REAL_TIME [REAL_TIME ...]
                        Specify list of CPUs to run on (e.g. -r 0 2 3).
-l RATE_LIMIT, --rate-limit RATE_LIMIT
                        Limit the frequency of calls to this server (e.g. Max
                        1 call per 0.1s).
-v, --verbose         Enable logging (logging.INFO).
-vv, --extra-verbose  Enable debug logging (logging.DEBUG).
-q, --quiet           Disable logging (logging.CRITICAL).
-b, --no-blosc        Disable blosc compression for data transport.
--log-file LOG_FILE   Specify a log file to stream logging data.
--share-dir SHARE_DIR
                        Specify the share directory to track logs and kernel
                        files.
```
