"""Provides file tracking ablities.

This module holds several classes that allows for asynchronous notifications to be generated 
through the use of ``watchdog``. These notifications trigger callbacks that can be registered 
on to different change events.

"""
import time
import os
import logging
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from enum import Enum

class MilkProcFileTracker(object):  
    """Tracks file changes in the MILK proc directory.

    When a change event (addition or removal) occurs in the MILK proc directory, a callback to a 
    handler method defined in this class is called. The callbacks are registed when the class is 
    initialised. A callback can be passed in to this class during initialisation to receive 
    notifications when events happen in its event handler. This class handles the lifecycle of 
    the watchdog observer and event handler objects.
    
    Args:
        proc_dir (str, optional): The path to the MILK proc directory. Defaults to MILK_PROC_DIR 
            as specified in environment variables, or ``/milk/proc`` if not specified.
        event_callback (Callable, optional): A callback function taking an argument of 
            ``MilkProcFileTracker.Event`` that indicates the type of event that happened.
    
    Attributes:
        log (logging.Logger): The logger object.
        event_callback (Callable, optional): If supplied, this callback will be called when files 
            are created or deleted with an argument of ``MilkProcFileTracker.Event``.
        started (bool): Indicates whether file tracking is active.
        proc_dir (str): The path to the MILK proc directory.
        files (set): The set of files currently registered in the tracker.
        event_handler (FileSystemEventHandler): An instance of ``FileSystemEventHandler``.
        observer (Observer): The ``watchdog`` observer object.

    """
    class Event(Enum):
        """Events registered to ``MilkProcFileTracker``.

        """
        FILE_CREATED = 0
        FILE_DELETED = 1

    def __init__(self, proc_dir=None, event_callback=None,):
        self.log = logging.getLogger(__file__)
        self.event_callback = event_callback
        self.started = False
        if proc_dir is None:
            self.proc_dir = os.path.abspath(os.environ.get("MILK_PROC_DIR", "/milk/proc"))
        else:
            self.proc_dir = os.path.abspath(proc_dir)
        self.log.debug("Milk file tracker set to track {}.".format(self.proc_dir))
        self.files = set()
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_created = self.file_created_action
        self.event_handler.on_deleted = self.file_deleted_action

        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.proc_dir, recursive=False)

    def is_tracked(self, file):
        """Determines if the file is a MLIK proc shared memory file.
        
        Args:
            file (str): Filepath of the file.
        
        Returns:
            bool: True if tracked. False if not.

        """
        filename = os.path.basename(file)
        name, ext = os.path.splitext(filename)
        return ext == ".shm" and name.find("proc.") == 0

    def file_created_action(self, event):
        """Runs when a file is created in the MILK proc directory.

        This callback method should override ``on_created`` on a ``FileSystemEventHandler``. 
        This method will activate the callback assigned to this class and add the file to the 
        tracked file set.
        
        Args:
            event (watchdog.events.FileSystemEvent): The event.

        """
        filepath = event.src_path
        
        if not event.is_directory and self.is_tracked(filepath) and filepath not in self.files:
            self.log.debug("New tracked file, file {}.".format(filepath))
            self.files.add(filepath)
            if self.event_callback is not None:
                self.event_callback(MilkProcFileTracker.Event.FILE_CREATED, filepath)

    def file_deleted_action(self, event):
        """Runs when a file is deleted in the MILK proc directory.

        This callback method should override ``on_deleted`` on a ``FileSystemEventHandler``. This 
        method will activate the callback assigned to this class and remove the file from the 
        tracked file set.
        
        Args:
            event (watchdog.events.FileSystemEvent): The event.

        """
        filepath = event.src_path

        if not event.is_directory and self.is_tracked(filepath) and filepath in self.files:
            self.log.debug("Tracked file deleted, file {}.".format(filepath))
            self.files.remove(filepath)
            if self.event_callback is not None:
                self.event_callback(MilkProcFileTracker.Event.FILE_DELETED, filepath)

    def start(self):
        """Starts file tracking.

        This method will start the watchdog observer as a daemon thread. The observer will 
        asynchronously monitor the specified MILK proc directory. A manual scan will be performed 
        beforehand to ensure existing files raise events.
        
        Returns:
            bool: True if successful, False if not.
            
        """
        self.log.info("Starting file tracking.")
        if not self.started:
            self.observer.setDaemon(True)
            self.observer.start()
            self.scan()
            return True
        return False

    def stop(self):
        """Stops file tracking.

        This method will stop the watchdog observer thread. The tracked file list is untouched.
        
        Returns:
            bool: True if successful, False if not.

        """
        if self.started:
            self.log.info("Stopping file tracking.")
            self.observer.stop()
            self.observer.join()
            self.log.info("File tracking stopped.")
            return True
        return False

    def scan(self, trigger_callback=True):
        """Scans the MILK proc directory for files.

        This method will compare the files discovered and the files currently tracked. Untracked 
        files will be added to tracked and trigger the callback if enabled. Tracked files that 
        are no longer present will be removed from the tracked list and trigger the callback if 
        enabled.
        
        Args:
            trigger_callback (bool, optional): If True, will run the ``event_callback`` for each 
            discovered file. Defaults to True.

        """
        self.log.debug("Scanning for new proc files.")
        new_files = set()
        for file in os.listdir(self.proc_dir):
            if self.is_tracked(file):
                filename = os.path.join(self.proc_dir, file)
                new_files.add(filename)
            
        removed_files = self.files.difference(new_files)
        added_files = new_files.difference(self.files)
        self.log.debug("{} files to be removed from current list, {} files to be added.".format(len(removed_files), len(added_files)))

        # Remove from tracked and trigger callbacks
        for filename in removed_files:
            self.files.remove(filename)
            if trigger_callback and self.event_callback is not None:
                self.event_callback(MilkProcFileTracker.Event.FILE_DELETED, filename)

        # Add to tracked and trigger callbacks
        for filename in added_files:
            self.files.add(filename)
            if trigger_callback and self.event_callback is not None:
                self.event_callback(MilkProcFileTracker.Event.FILE_CREATED, filename)


class KrakenShareFileTracker(object):
    """Tracks Kraken log files and kernel connection files.

    When a change event occurs in the logs or kernel connection directory, a callback to a 
    handler method defined in this class is called. The callbacks are registed when the class is 
    initialised. A callback can be passed in to this class during initialisation to receive 
    notifications when events happen in its event handler. This class handles the lifecycle of 
    the watchdog observer and event handler objects.
    
    Args:
        share_dir (str, optional): The path to the share directory. Defaults to /milk/share.
        event_callback (Callable, optional): A callback function taking an argument of,
            ``KrakenShareFileTracker.Event`` and ``KrakenShareFileTracker.FileType`` and the 
            filename that indicates the type of event that happened, and whether it is a log or 
            kernel connection file.
        
    Attributes:
        log (logging.Logger): The logger object.
        event_callback (Callable, optional): A callback function taking an argument of,
            ``KrakenShareFileTracker.Event`` and ``KrakenShareFileTracker.FileType`` and the 
            filename that indicates the type of event that happened, and whether it is a log or 
            kernel connection file.
        started (bool): Indicates whether file tracking is active.
        share_dir (str): The path to the share directory.
        files (set): The set of files currently registered in the tracker.
        event_handler (FileSystemEventHandler): An instance of ``FileSystemEventHandler``.
        observer (Observer): The ``watchdog`` observer object.

    """
    class Event(Enum):
        """Events registered to ``KrakenShareFileTracker``.

        """
        FILE_CREATED = 0
        FILE_DELETED = 1
        # FILE_MODIFIED = 2  # Disabled as not used

    class FileType(Enum):
        """FileTypes registered to ``KrakenShareFileTracker``.

        """
        LOG = 0
        KERNEL = 1

    def __init__(self, share_dir="/milk/share", event_callback=None):
        self.log = logging.getLogger(__file__)
        self.event_callback = event_callback
        self.started = False
        self.share_dir = os.path.abspath(share_dir)
        self.log.debug("Share file tracker set to track {}.".format(self.share_dir))
        self.log_files = set()
        self.kernel_files = set()
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_any_event = self.file_event_action
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.share_dir, recursive=True)

    def filetype(self, file):
        """Determines the filetype of the file.
        
        Args:
            file (str): Filepath of the file.
        
        Returns:
            KrakenShareFileTracker.FileType: The file type or False if not tracked. 

        """
        filename = os.path.basename(file)
        name, ext = os.path.splitext(filename)

        if name.startswith("log.") and ext == ".txt":
            return KrakenShareFileTracker.FileType.LOG
        elif name.startswith("kernel.") and ext == ".json":
            return KrakenShareFileTracker.FileType.KERNEL
        return False

    def file_event_action(self, event):
        """Runs when a change occurs in the share folder.

        This callback method should override ``on_any_event`` on a ``FileSystemEventHandler``. 
        This method will activate the callback assigned to this class and update the log files set 
        provided that the event type is accepted and the filetype is valid.
        
        Args:
            filename (str): The filename of the created file.

        """
        filepath = event.src_path

        if not event.is_directory:
            filetype = self.filetype(filepath)
            if filetype is not None:
                event_accepted = False
                if event.event_type == watchdog.events.EVENT_TYPE_CREATED:
                    self.log.debug("New tracked file, file {}.".format(filepath))
                    event_type = KrakenShareFileTracker.Event.FILE_CREATED
                    if filetype == KrakenShareFileTracker.FileType.KERNEL:
                        self.kernel_files.add(filepath)
                        event_accepted = True
                    elif filetype == KrakenShareFileTracker.FileType.LOG:
                        self.log_files.add(filepath)
                        event_accepted = True
                elif event.event_type == watchdog.events.EVENT_TYPE_DELETED:
                    self.log.debug("Tracked file deleted, file {}.".format(filepath))
                    event_type = KrakenShareFileTracker.Event.FILE_DELETED
                    if filetype == KrakenShareFileTracker.FileType.KERNEL and filepath in self.kernel_files:
                        self.kernel_files.remove(filepath)
                        event_accepted = True
                    elif filetype == KrakenShareFileTracker.FileType.LOG and filepath in self.log_files:
                        self.log_files.remove(filepath)
                        event_accepted = True
                # elif event.event_type == watchdog.events.EVENT_TYPE_MODIFIED:
                #     self.log.debug("Tracked file modified, file {}.".format(filepath))
                #     event_type = KrakenShareFileTracker.Event.FILE_MODIFIED
                #     if filetype == KrakenShareFileTracker.FileType.KERNEL and filepath in self.kernel_files:
                #         event_accepted = True
                #     elif filetype == KrakenShareFileTracker.FileType.LOG and filepath in self.log_files:
                #         event_accepted = True
                if event_accepted and self.event_callback is not None:
                    self.event_callback(event_type, filepath, filetype)

    def start(self):
        """Starts file tracking.

        This method will start the watchdog observer as a daemon thread. The observer will 
        asynchronously monitor the share directory. A manual scan will be performed beforehand to 
        ensure existing files raise events.
        
        Returns:
            bool: True if successful, False if not.
            
        """
        self.log.info("Starting file tracking.")
        if not self.started:
            self.observer.setDaemon(True)
            self.observer.start()
            self.scan()
            return True
        return False

    def stop(self):
        """Stops file tracking.

        This method will stop the watchdog observer thread. The tracked file list is untouched.
        
        Returns:
            bool: True if successful, False if not.

        """
        if self.started:
            self.log.info("Stopping file tracking.")
            self.observer.stop()
            self.observer.join()
            self.log.info("File tracking stopped.")
            return True
        return False

    def scan(self, trigger_callback=True):
        """Scans the share directory for files.

        This method will compare the files discovered and the files currently tracked. Untracked 
        files will be added to tracked and trigger the callback if enabled. Tracked files that 
        are no longer present will be removed from the tracked list and trigger the callback if 
        enabled. This method does NOT check for file modifications.
        
        Args:
            trigger_callback (bool, optional): If True, will run the ``event_callback`` for each 
            discovered file. Defaults to True.

        """
        self.log.debug("Scanning for new share files.")
        new_log_files = set()
        new_kernel_files = set()

        files = [os.path.join(self.share_dir, dp, f) 
                    for dp, dn, fn in os.walk(self.share_dir) 
                        for f in fn]
        
        for file in files:
            filetype = self.filetype(file)
            if filetype == KrakenShareFileTracker.FileType.KERNEL:
                new_kernel_files.add(file)
            elif filetype == KrakenShareFileTracker.FileType.LOG:
                new_log_files.add(file)
            
        removed_log_files = self.log_files.difference(new_log_files)
        added_log_files = new_log_files.difference(self.log_files)
        self.log.debug("{} files to be removed from current log file list, {} files to be added.".format(len(removed_log_files), len(added_log_files)))
        removed_kernel_files = self.kernel_files.difference(new_kernel_files)
        added_kernel_files = new_kernel_files.difference(self.kernel_files)
        self.log.debug("{} files to be removed from current kernel file list, {} files to be added.".format(len(removed_kernel_files), len(added_kernel_files)))

        # Remove from tracked and trigger callbacks
        for file_type, remove_list, files_set in [
            (KrakenShareFileTracker.FileType.LOG, removed_log_files, self.log_files), 
            (KrakenShareFileTracker.FileType.KERNEL, removed_kernel_files, self.kernel_files)
        ]:
            for filename in remove_list:
                files_set.remove(filename)
                if trigger_callback and self.event_callback is not None:
                    self.event_callback(KrakenShareFileTracker.Event.FILE_DELETED, filename, file_type)

        # Add to tracked and trigger callbacks
        for file_type, add_list, files_set in [
            (KrakenShareFileTracker.FileType.LOG, added_log_files, self.log_files), 
            (KrakenShareFileTracker.FileType.KERNEL, added_kernel_files, self.kernel_files)
        ]:
            for filename in add_list:
                files_set.add(filename)
                if trigger_callback and self.event_callback is not None:
                    self.event_callback(KrakenShareFileTracker.Event.FILE_CREATED, filename, file_type)
