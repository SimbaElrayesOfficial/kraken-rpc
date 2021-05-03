"""Provides a class that RPC requests are made to.

"""


from kraken_tools import KrakenProcessManager
import aiomas
import logging
import time


class KrakenProcessManagerAgent(KrakenProcessManager, aiomas.Agent):
    """Exposes ``KrakenProcessManager`` methods for RPC.
    
    Args:
        container (aiomas.Container): The container the agent is using.
        rate_limit (float, optional): The time interval required in seconds between calls of 
            exposed methods. Defaults to 0 (unlimited).
    
    Attributes:
        log (logging.Logger): The logger object.
        rate_limit (float): The time interval required between calls of exposed methods.
        last_call (float): The last time an exposed method was called. Used for rate limiting.

    """
    def __init__(self, container, rate_limit=0):
        self.log = logging.getLogger(__file__)
        KrakenProcessManager.__init__(self)
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
        """Generates a digest containing statistics for all tracked processes.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcessManager.generate_digest`

        Returns:
            Any: The return value of the base function or None if rate limited.

        """
        self.log.debug("{} generate digest called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.generate_digest(self)
        return None

    @aiomas.expose
    def process_run(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.RUNNING``.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcessManager.process_run`
        
        Args:
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} run called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_run(self, filenames)
        return None

    @aiomas.expose
    def process_step(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.STEP``.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcesses.process_step`

        Args:
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} step called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_step(self, filenames)
        return None

    @aiomas.expose
    def process_pause(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.PAUSE``.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcesses.process_pause`

        Args:
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} pause called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_pause(self, filenames)
        return None

    @aiomas.expose
    def process_no_compute(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.NO_COMPUTE``.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcesses.process_no_compute`

        Args:
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} no compute called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_no_compute(self, filenames)
        return None

    @aiomas.expose
    def process_exit(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.EXIT``.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcesses.process_exit`

        Args:
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} no compute called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_exit(self, filenames)
        return None

    @aiomas.expose
    def process_signal(self, signal, filenames):
        """Sends a signal to the processes.
        
        See Also:
            :meth:`kraken_tools.kraken_process_manager.KrakenProcesses.process_signal`

        Args:
            signal (int): The signal number.
            filenames (list): List of linked shm filepaths.

        Returns:
            Any: The return value of the base function or None if rate limited.
            
        """
        self.log.debug("{} signal called.".format(repr(self)))
        if self.check_call_limit():
            return KrakenProcessManager.process_signal(self, signal, filenames)
        return None
