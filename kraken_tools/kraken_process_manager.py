"""Provides ways to track Kraken processes and link them with ``KrakenProcessInfo``.

Todo:
    * Add gpu process stats (see commented: generate_gpu_processes_digest).

"""


import CacaoProcessTools as cpt
import os
import logging
from .file_trackers import MilkProcFileTracker
from .kraken_process_info import KrakenProcessInfo
from .kraken_process_code import KrakenProcessCode
import bisect
import time
# import nvsmi


class KrakenProcessManager(object):
    """Allows tracking and reporting of Kraken processes.
    
    Attributes:
        log (logging.Logger): The logger object.
        process_info_keys (list): The sorted keys for processes stored in process_info dict.
        tracker (MilkProcFileTracker): The file tracker for the MILK proc directory.

    """
    def __init__(self):
        self.log = logging.getLogger(__file__)
        self.process_info_keys = []
        self.process_info = {}
        self.tracker = MilkProcFileTracker(event_callback=self.proc_file_event)

    def dispose(self):
        """Performs the shutdown sequence and releases file handles.

        Stops the tracking of files and closes files that have been linked.

        """
        self.stop_tracking()
        self.tracker = None
        for pinfo in self.process_info.values():
            pinfo.close()

    def start_tracking(self):
        """Starts the tracker.

        Returns:
            bool: True if successful, False if not.

        """
        return self.tracker.start()
    
    def stop_tracking(self):
        """Stops the tracker.

        Returns:
            bool: True if successful, False if not.
        
        """
        return self.tracker.stop()

    def proc_file_event(self, event, filename):
        """Handles the file events.

        Used as a callback registered on the file tracker. This method will link newly created 
        files and remove deleted files.
        
        Args:
            event (MilkProcFileTracker.Event): The event type that occured.
            filename (str): Filename of the file that triggered the event.

        """
        if event == MilkProcFileTracker.Event.FILE_CREATED:
            self.log.info("File created event received by {}. File: {}".format(repr(self), filename))
            if filename not in self.process_info:
                try:
                    info = KrakenProcessInfo(filename)
                    self.process_info[filename] = info
                    # Insert the key into the sorted list
                    bisect.insort_right(self.process_info_keys, filename)
                    self.log.debug("Created new KrakenProcessInfo for {}.".format(filename))
                except ValueError as error:
                    self.log.exception("Failed to create new KrakenProcessInfo for {}. {}.".format(filename, error))
                
        elif event == MilkProcFileTracker.Event.FILE_DELETED:
            self.log.info("File deleted event received by {}. File: {}".format(repr(self), filename))
            if filename in self.process_info:
                del self.process_info[filename]
                self.process_info_keys.remove(filename)
                self.log.debug("Removed KrakenProcessInfo for {}.".format(filename))

    def list_proc_files(self):
        """List the currently tracked files.
        
        Returns:
            set: The tracked files. 

        """
        self.log.debug("Listing proc files.")
        return self.tracker.files.copy()

    def remove_proc_file(self, filename):
        """Removes a proc file from the filesystem.
        
        Args:
            filename (str): Filepath of the file.
        
        Returns:
            bool: True if successful, False if not.

        """
        self.process_info[filename].close()
        try:
            os.remove(filename)
            self.log.debug("Removed proc file {}.".format(filename))
            return True
        except OSError as error:
            self.log.exception("Unable to remove proc file {}. {}.".format(filename, error))
        return False

    def generate_digest(self):
        """Generates a digest containing all tracked processes and their properties.

        The digest is formatted as a two level dictionary, with keys on the first level being the 
        proc filenames, with values of the property dictionary. The second level keys are the 
        property names as mapped from ``KrakenProcessInfo.props`` to the following:

        .. code-block:: python

            # Mapping KrakenProcessInfo's info_props to the following
            process_info_columns = [
                "pid", 
                "name",
                "cpu",
                "memory",
                "cpuAffinity",
                "cpuContextSwitches",
                "threadCount",
                "loopCount", 
                "control", 
                "tmuxSession", 
                "loopStat",  # Does not work as advertised
                "statusCode",  # Does not work as advertised
                "message",
                "description",
                "creationTime",
                "status"
            ]

        If properties are updated on ``KrakenProcessInfo``, this must be changed.
        
        Returns:
            dict: The digest.
        """
        t1 = time.perf_counter()
        digest_index = self.process_info_keys.copy()

        # Mapping KrakenProcessInfo's info_props to the following
        process_info_columns = [
            "pid", 
            "name",
            "cpu",
            "memory",
            "cpuAffinity",
            "cpuContextSwitches",
            "threadCount",
            "loopCount", 
            "control", 
            "tmuxSession", 
            "loopStat",  # Does not work as advertised
            "statusCode",  # Does not work as advertised
            "message",
            "description",
            "creationTime",
            "status"
        ]

        digest_columns = process_info_columns

        digest = {
            "index": digest_index,
            "columns": digest_columns,
            "data" : {}
        }

        for index in digest_index:
            digest["data"][index] = {}
            for column, prop in zip(process_info_columns, KrakenProcessInfo.props):
                value = getattr(self.process_info[index], prop)
                digest["data"][index][column] = value() if callable(value) else value

        t2 = time.perf_counter()
        self.log.debug("Digest generated in {} seconds.".format(t2 - t1))
        return digest

    # def generate_gpu_processes_digest(self):
    #     nvsmi_props = [
    #         "gpu_name",
    #         "gpu_id",
    #         "gpu_uuid",
    #         "used_memory"
    #     ]

    #     nvsmi_columns = [
    #         "gpuName",
    #         "gpuId",
    #         "gpuUuid",
    #         "gpuMemory"
    #     ]

    #     nv_info = nvsmi.get_gpu_processes()
    #     nv_pids = [info.pid for info in nv_info]

    #     digest = {
    #         "index": nv_pids,
    #         "columns": nvsmi_columns,
    #         "data" : {}
    #     }

    #     for info in nv_info:
    #         data[info.pid] = {}
    #         for col in nvsmi_columns:
    #             data[info.pid][col] = getattr(nv_info, col)

    #     return digest


    def process_move_to_other_cpuset(self, filenames):
        """Not implemented.
        
        Todo:
            * Requires CacaoProcessTools to expose cpusets method.

        Raises:
            NotImplementedError: Not implemented.
            
        """
        # TODO: 
        raise NotImplementedError()

    def process_move_to_same_cpuset(self, filenames):
        """Not implemented.
        
        Todo:
            * Requires CacaoProcessTools to expose cpusets method.

        Raises:
            NotImplementedError: Not implemented.
            
        """
        raise NotImplementedError()

    def process_set_iteration_time_limit(self, filenames):
        """Not implemented.
        
        Todo:
            * Requires CacaoProcessTools to expose dtiter_limit_enable properties

        Raises:
            NotImplementedError: Not implemented.
            
        """
        raise NotImplementedError()

    def process_set_execution_time_limit(self, filenames):
        """Not implemented.
        
        Todo:
            * Requires CacaoProcessTools to expose dtexec_limit_enable properties

        Raises:
            NotImplementedError: Not implemented.
            
        """
        raise NotImplementedError()

    def process_read_message(self, filenames):
        """Not implemented.
        
        Todo:
            * Requires CacaoProcessTools to expose dtexec_limit_enable properties

        Raises:
            NotImplementedError: Not implemented.
            
        """
        # sprintf(syscommand, "clear; tail -f %s", procinfoproc.pinfoarray[pindex]->logfilename);
        raise NotImplementedError()

    def process_run(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.RUNNING``.

        Args:
            filenames (list): List of linked shm filepaths.
        
        Returns:
            bool: True.

        """
        for filename in filenames:
            self.process_info[filename].CTRLval = KrakenProcessCode.Control.RUNNING.value
            self.log.debug("Set CTRLval for {} to RUNNING".format(filename))
        return True

    def process_step(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.STEP``.

        Args:
            filenames (list): List of linked shm filepaths.
        
        Returns:
            bool: True.
            
        """
        for filename in filenames:
            self.process_info[filename].CTRLval = KrakenProcessCode.Control.STEP.value
            self.log.debug("Set CTRLval for {} to STEP.".format(filename))
        return True
            
    def process_pause(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.PAUSED``.

        Args:
            filenames (list): List of linked shm filepaths.
        
        Returns:
            bool: True.
            
        """
        for filename in filenames:
            self.process_info[filename].CTRLval = KrakenProcessCode.Control.PAUSED.value
            self.log.debug("Set CTRLval for {} to PAUSED.".format(filename))
        return True
            
    def process_no_compute(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.NO_COMPUTE``.

        Args:
            filenames (list): List of linked shm filepaths.
        
        Returns:
            bool: True.
            
        """
        for filename in filenames:
            self.process_info[filename].CTRLval = KrakenProcessCode.Control.NO_COMPUTE.value
            self.log.debug("Set CTRLval for {} to NO_COMPUTE.".format(filename))
        return True

    def process_exit(self, filenames):
        """Changes the control value for the processes to ``KrakenProcessCode.Control.EXIT``.

        This method does not seem to work properly for non config processes due to 
        ``CacaoProcessTools`` issues.

        Args:
            filenames (list): List of linked shm filepaths.
        
        Returns:
            bool: True.
            
        """
        for filename in filenames:
            self.process_info[filename].CTRLval = KrakenProcessCode.Control.EXIT.value
            self.log.debug("Set CTRLval for {} to EXIT.".format(filename))
        return True

    def process_signal(self, signal, filenames):
        """Sends a signal to the processes.

        Args:
            signal (int): The signal number.
            filenames (list): List of linked shm filepaths.
        
        Returns:
            list: List of return values from the signal. Values are False on failure.

        """
        results = []
        for filename in filenames:
            self.log.debug("Sending signal {} to {}.".format(signal, filename))
            results.append(self.process_info[filename].signal(signal))
        return results
