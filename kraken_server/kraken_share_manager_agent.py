"""Provides a class that RPC requests are made to.

"""

from kraken_tools import KrakenShareManager
import aiomas
import logging
import time


class KrakenShareManagerAgent(KrakenShareManager, aiomas.Agent):
    """Exposes ``KrakenShareManager`` methods for RPC.
    
    Args:
        container (aiomas.Container): The container the agent is using.
        rate_limit (float, optional): The time interval required in seconds between calls of 
            exposed methods. Defaults to 0 (unlimited).
    
    Attributes:
        log (logging.Logger): The logger object.
        rate_limit (float): The time interval required between calls of exposed methods.
        last_call (float): The last time an exposed method was called. Used for rate limiting.

    """
    def __init__(self, container, rate_limit=0, share_dir="/milk/share"):
        self.log = logging.getLogger(__file__)
        KrakenShareManager.__init__(self, share_dir)
        aiomas.Agent.__init__(self, container)
        self.rate_limit = rate_limit
        if rate_limit > 0:
            self.log.info("Rate limiting activated, max 1 call per {} s".format(rate_limit))
        self.last_call = 0

    def check_call_limit(self):
        """Checks if a call was made within the last ``rate_limit`` interval.

        This method should be called in all exposed methods to rate limit their call rate.
        
        Returns:
            bool: True if rate limit period has expired. False if not.

        """
        if self.rate_limit > 0:
            current_time = time.time()
            if current_time - self.last_call < self.rate_limit:
                self.log.warning("RPC was prevented by rate limiting.")
                return False

            self.last_call = current_time
        return True

    @aiomas.expose
    def generate_digest(self):
        """Generates a digest containing the available logs and kernel files.
        
        See Also:
            :meth:`kraken_tools.kraken_share_manager.KrakenShareManager.generate_digest`

        Returns:
            Any: The return value of the base function or None if rate limited.

        """
        self.log.debug("{} generate digest called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenShareManager.generate_digest(self)
        return None

    @aiomas.expose
    def read_log(self, log_file, from_byte=0, to_byte=None):
        """Reads the log file.

        See Also:
            :meth:`kraken_tools.kraken_share_manager.KrakenShareManager.read_log`
        
        Args:
            log_file (str): Filepath of the log file.
            from_byte (int, optional): Read from specified byte. Defaults to 0.
            to_byte (int, optional): Read to specified byte. Set to None to read to end. 
                Defaults to None.
        
        Returns:
            Any: The return value of the base function or None if rate limited.

        """
        self.log.debug("{} read log called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenShareManager.read_log(self, log_file, from_byte=from_byte, to_byte=to_byte)
        return None

    @aiomas.expose
    def read_kernel_info(self, kernel_file):
        """Reads the kernel file.

        See Also:
            :meth:`kraken_tools.kraken_share_manager.KrakenShareManager.read_kernel_info`

        Args:
            kernel_file (str): Filepath of the log file.
        
        Returns:
            Any: The return value of the base function or None if rate limited.

        """
        self.log.debug("{} read kernel info called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenShareManager.read_kernel_info(self, kernel_file)
        return None
