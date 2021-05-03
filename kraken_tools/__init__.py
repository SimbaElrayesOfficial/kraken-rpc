"""Provides the ability to monitor Kraken started processes.

This module provides classes to monitor the MILK proc directory for shared memory files. These 
files can be used to gather statistics on the processes themselves through the use of 
``CacaoProcessTools``.

"""


from .kraken_process_code import KrakenProcessCode
from .kraken_process_info import KrakenProcessInfo
from .kraken_process_manager import KrakenProcessManager
from .kraken_share_manager import KrakenShareManager
from .file_trackers import MilkProcFileTracker, KrakenShareFileTracker
