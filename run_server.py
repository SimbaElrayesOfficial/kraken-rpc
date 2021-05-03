#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kraken RPC Server - Serve statistics on Kraken monitored processes.

This file is the entrypoint for starting the Kraken RPC Server application via command line. It 
provides a range of connection and logging options in its arguments. By default, the server will 
bind to the address ``"0.0.0.0"`` and port ``20000``. For more information, run 
``python run_server.py --help``.

Examples:

    $ python run_server.py
    $ python run_server.py --verbose
"""

import argparse
from kraken_server import KrakenServer
import time
import logging
import psutil
import asyncio
import os

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Kraken RPC Server - Serve statistics on Kraken monitored processes.")
    parser.add_argument("-p", "--port", default=20000, type=int, help="Specify RPC server port. Defaults to 20000.")
    parser.add_argument("-a", "--address", default="0.0.0.0", type=str, help="Specify RPC server bind address. Defaults to '0.0.0.0'.")
    parser.add_argument("-r", "--real-time", default=[], type=int, nargs="+", help="Specify list of CPUs to run on (e.g. -r 0 2 3). Defaults to all.")
    parser.add_argument("-l", "--rate-limit", default=0, type=float, help="Limit the frequency of calls to this server (e.g. Max 1 call per 0.1s). Defaults to 0.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable logging (logging.INFO).")
    parser.add_argument("-vv", "--extra-verbose", action="store_true", help="Enable debug logging (logging.DEBUG).")
    parser.add_argument("-q", "--quiet", action="store_true", help="Disable logging (logging.CRITICAL).")
    parser.add_argument("-b", "--no-blosc", action="store_true", help="Disable blosc compression for data transport.")
    parser.add_argument("--log-file", default=None, type=str, help="Specify a log file to stream logging data.")
    parser.add_argument("--share-dir", default="/milk/share", type=str, help="Specify the share directory to track logs and kernel files.")
    args = parser.parse_args()

    # Setup logging
    log = logging.getLogger(__file__)

    if args.quiet:
        log_level = logging.CRITICAL
    if args.extra_verbose:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    if args.log_file is not None:
        log_file = os.path.abspath(args.log_file)
    else:
        log_file = None

    logging.basicConfig(filename=log_file, filemode="a", level=log_level)

    # Set real-time CPU affinity if enabled
    if len(args.real_time) > 0:
        log.info("Real time mode enabled, CPU affinity set to {}".format(args.real_time))
        process = psutil.Process()
        process.cpu_affinity(args.real_time)
    
    # Start the KrakenServer
    server = KrakenServer(args.address, args.port, rate_limit=args.rate_limit, blosc=not args.no_blosc, share_dir=args.share_dir)
    server.start()

    # Run the asyncio event loop
    loop = asyncio.get_event_loop()

    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        log.info("Caught keyboard interrupt. Canceling tasks...")
        server.stop()
    finally:
        loop.stop()
        loop.close()
