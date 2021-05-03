"""Provides a wrapper around CacaoProcessInfo.

The classes in this module wrap around ``CacaoProcessTools`` to resolve instablity issues in the 
tools and to provide checks for validity of arguments that would otherwise crash the Python process.

"""


import CacaoProcessTools
import os
import signal
from enum import Enum
import logging
import psutil
from threading import Timer, Thread


class KrakenProcessInfo(CacaoProcessTools.processinfo):
    """Wrapper for ``CacaoProcessTools.processinfo``.

    The wrapper allows for the passive recording of psutil stats along with safe access to most of 
    processinfo's methods. Although processinfo's methods that are not overriden are exposed, it is 
    not recommended to use them due to stablity issues.
    
    Args:
        proc_file (str): Filepath of the proc shm file to link.

    Attributes:
        props (list): Class attribute. This is a list of properties available for the process. Some 
            properties listed may be generated from methods instead.
        log (logging.Logger): The logger object.
        linked (bool): Indicates whether the instance is linked to a shm file.
        cpu (float): The cpu utilisation in %. Is the same as top's display divided by number of 
            CPUs.
        memory (int): The amount of RSS memory used in bytes.
        cpu_affinity (list): List of integers indicating the process's cpu affinities.
        cpu_count (int): The number of CPUs of this machine.
        ps (psutil.Process): The process object from psutil.
        monitoring_frequency (float): The interval for polling psutil for the process stats.
        cpu_context_switches (int): The total number of context switches performed.
        thread_count (int): The number of threads currently used by the process.
        monitoring_timer (threading.Timer): The timer running psutil monitoring.
        proc_file (str): The filepath of the linked shm file.

    """
    props = [
        "PID",
        "name",
        "cpu",
        "memory",
        "cpu_affinity",
        "cpu_context_switches",
        "thread_count",
        "loopcnt",
        "CTRLval",
        "tmuxname",
        "loopstat",
        "statuscode",
        "statusmsg",
        "description",
        "get_creation_time",
        "get_status"
    ]

    def __init__(self, proc_file=None):
        self.log = logging.getLogger(__file__)
        self.linked = False
        self.cpu = 0.0
        self.memory = 0
        self.cpu_affinity = []
        self.cpu_count = psutil.cpu_count()
        self.ps = None
        self.monitoring_frequency = 1
        self.cpu_context_switches = 0
        self.thread_count = 0
        self.monitoring_timer = None
        if proc_file is not None:
            if self.check_link(proc_file):
                self.link(proc_file)
                self.linked = True
            else:
                raise ValueError("Invalid arguments to create class.")
        self.proc_file = proc_file

    def check_link(self, file):
        """Checks for if the file is a valid filepath.

        This method does checking of the filepath to see if it ends in .shm and has proc. in it. 
        Unfortunately this is not failproof. The server will hard crash if given an invalid file 
        due to CacaoProcessTool's handling.
        
        Returns:
            bool: True if valid. False if not.

        """
        if not os.path.isfile(file):
            return False

        filename = os.path.basename(file)
        name, ext = os.path.splitext(filename)
        return ext == ".shm" and name.find("proc.") == 0

    def wait_task(self):
        """Waits until the process dies and unlinks the shm file automatically.

        """
        if self.linked and self.ps is not None:
            self.ps.wait()
            self.log.info("Process {} has ended.".format(self.proc_file))
            self.close()

    def link(self, file):
        """Performs the linking to a proc shm file.

        Starts the monitoring and wait threads.
        
        Args:
            file (str): Filepath to a proc shm file.
        
        Raises:
            ValueError: If the filename check fails, a ValueError will occur.
        
        Returns:
            bool: True if successfil. False if not.
            
        """
        if not self.linked and self.ps is None:
            if not self.check_link(file):
                raise ValueError("Invalid file provided.")

            # Use the CacaoProcessTools.processinfo to link, risky.
            super().link(file)
            self.proc_file = file
            try:
                self.ps = psutil.Process(self.PID)
                self.wait_thread = Thread(target=self.wait_task, daemon=True)
                self.wait_thread.start()
                self.monitoring_timer = Timer(self.monitoring_frequency, self.monitoring_handler)
                self.monitoring_timer.setDaemon(True)
                self.monitoring_timer.start()
            except (psutil.NoSuchProcess, psutil.ZombieProcess) as error:
                self.log.debug("Error ignored in linking: {}".format(error))
            self.log.debug("{} linked {}.".format(repr(self), file))
            return True
        return False

    def close(self):
        """Closes the linked shm file.

        This method uses ``CacaoProcessTools.processinfo`` to unlink the shm file. All monitoring 
        and other threads are stopped.
        
        Returns:
            bool: True if successful. False if not.

        """
        if self.linked:
            if self.monitoring_timer is not None:
                self.monitoring_timer.cancel()
            super().close("")
            self.log.debug("{} closed {}.".format(repr(self), self.proc_file))
            self.proc_file = None
            self.monitoring_timer = None
            self.wait_thread = None
            self.cpu = 0.0
            self.memory = 0.0
            return True
        return False

    def signal(self, signal):
        """Sends a signal to the process.
        
        Args:
            signal (int): The signal number.
        
        Returns:
            Any: The result of ``send_signal``, otherwise False on failure.

        """
        if self.linked and self.ps is not None:
            try:
                self.log.debug("{} sending {}".format(repr(self), signal))
                return self.ps.send_signal(signal)
            except psutil.NoSuchProcess as error:
                self.log.debug("Error ignored in signal: {}".format(error))
        return False

    def get_creation_time(self):
        """Gets the creation time of the shm file.

        This is in epoch with nanoseconds.
        
        Returns:
            int: The creation time in nanoseconds since epoch.

        """
        return int(str(self.createtime.tv_sec) + "{0:09d}".format(self.createtime.tv_nsec))

    def get_status(self):
        """Gets the process status.
        
        Returns:
            str: The process status. "dead" on failure.

        """
        if self.linked and self.ps is not None:
            try:
                return self.ps.status()
            except (KeyError, AttributeError, psutil.NoSuchProcess) as error:
                # Keyerror and AttributeError is exempt due to 
                # some psutil issue when disconnecting on client
                self.log.debug("Error ignored in get_status: {}".format(error))
        return psutil.STATUS_DEAD

    def monitoring_handler(self):
        """Performs the gathering of psutil data.

        The ``ps.oneshot`` context manager is used to speed up psutil data gathering. This is 
        intended to run as a polling method.

        """
        if self.linked and self.ps is not None:
            try:
                with self.ps.oneshot():
                    self.cpu = self.ps.cpu_percent() / self.cpu_count
                    self.memory = self.ps.memory_info().rss
                    self.cpu_affinity = self.ps.cpu_affinity()
                    self.thread_count = self.ps.num_threads()
                    self.cpu_context_switches = sum(self.ps.num_ctx_switches()) # This is a tuple (voluntary_switches, involuntary_switches)
                self.monitoring_timer = Timer(self.monitoring_frequency, self.monitoring_handler)
                self.monitoring_timer.start()
            except (psutil.NoSuchProcess, psutil.ZombieProcess) as error:
                self.log.debug("Error ignored in monitoring handler: {}".format(error))

    def set_cpu_affinity(self, cpus):
        """Sets the cpu affinity for this process.
        
        Args:
            cpus (list): List of integers representing CPU numbers.
        
        Returns:
            bool: True if successful. False if not.
            
        """
        if self.linked and self.ps is not None:
            try:
                self.ps.cpu_affinity(cpus)
                return True
            except (psutil.NoSuchProcess, psutil.ZombieProcess) as error:
                self.log.debug("Error ignored in set_cpu_affinity: {}".format(error))
        return False
        
