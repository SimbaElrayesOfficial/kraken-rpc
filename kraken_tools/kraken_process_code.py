"""Provides references for enums used in the Kraken process properties.

"""

from enum import Enum

class KrakenProcessCode(object):
    """Contains references for enums used in Kraken process properties.

    Currently contains ``LoopStat`` and ``Control`` enums.

    """
    class LoopStat(Enum):
        """Refers to the loopStat property.
        
        """
        DONE = 1
        ADDPERTUVOLT = 10
        RMPERTUVOLT  = 11
        ENABLEPERTUVOLT = 12
        DISABLEPERTUVOLT = 13
        SETPERTUVOLT = 14
        CLOSELOOP = 15
        OPENLOOP = 16
        RESET = 17

    class Control(Enum):
        """Refers to the CTRLval property.
        
        """
        RUNNING = 0
        PAUSED = 1
        STEP = 2
        EXIT = 3
        NO_COMPUTE = 5
