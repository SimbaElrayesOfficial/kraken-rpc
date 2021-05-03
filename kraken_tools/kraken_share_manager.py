"""Provides options to manage the files inside the Kraken share folder

The Kraken share folder includes logs and kernel connection files.

"""


import os
import logging
from .file_trackers import KrakenShareFileTracker
import bisect
import time


class KrakenShareManager(object):
    """Allows tracking and reporting of Kraken share functionality.

    Args:
        share_dir (str, optional): The filepath to the share folder.
    
    Attributes:
        log (logging.Logger): The logger object.
        log_files (list): List of sorted log filepaths.
        kernel_files (list): List of sorted kernel filepaths.
        tracker (KrakenShareFileTracker): The file tracker for the share directory.

    """
    def __init__(self, share_dir="/milk/share"):
        self.log = logging.getLogger(__file__)
        self.log_files = []
        self.kernel_files = []
        self.tracker = KrakenShareFileTracker(event_callback=self.share_file_event, share_dir=share_dir)

    def dispose(self):
        """Performs the shutdown sequence.

        """
        self.stop_tracking()
        self.tracker = None

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

    def share_file_event(self, event, filename, filetype):
        """Handles the file events.

        Used as a callback registered on the file tracker. This method will link newly created 
        files and remove deleted files.
        
        Args:
            event (KrakenShareFileTracker.Event): The event type that occured.
            filename (str): Filename of the file that triggered the event.
            filetype (KrakenShareFileTracker.FileType): The file type of the file.

        """
        if event == KrakenShareFileTracker.Event.FILE_CREATED:
            self.log.info("File created event received by {}. File: {}".format(repr(self), filename))
            if filetype == KrakenShareFileTracker.FileType.KERNEL:
                bisect.insort_right(self.kernel_files, filename)
            elif filetype == KrakenShareFileTracker.FileType.LOG:
                bisect.insort_right(self.log_files, filename)
        elif event == KrakenShareFileTracker.Event.FILE_DELETED:
            self.log.info("File deleted event received by {}. File: {}".format(repr(self), filename))
            if filetype == KrakenShareFileTracker.FileType.KERNEL:
                self.kernel_files.remove(filename)
            elif filetype == KrakenShareFileTracker.FileType.LOG:
                self.log_files.remove(filename)

    def generate_digest(self):
        """Generate a digest containing a list of the log files and kernel files.

        The digest is formatted as a dictionary with the logFiles key and kernelFiles key to 
        represent their respective lists.

        """
        return {
            "logFiles": self.log_files.copy(),
            "kernelFiles": self.kernel_files.copy()
        }

    def read_log(self, log_file, from_byte=0, to_byte=None):
        """Reads the log file.
        
        Args:
            log_file (str): Filepath of the log file.
            from_byte (int, optional): Read from specified byte. Defaults to 0.
            to_byte (int, optional): Read to specified byte. Set to None to read to end. 
                Defaults to None.
        
        Returns:
            (int, bytes): Tuple of filesize and the byte string.

        """
        filesize = os.path.getsize(log_file)
        if filesize == 0:
            return b""
        
        if to_byte is None or to_byte > filesize:
            to_byte = filesize

        with open(log_file, "rb") as fp:
            if from_byte > 0:
                fp.seek(from_byte)
            readsize = to_byte - from_byte

            if readsize <= 0:
                return b""
            
            data = fp.read(readsize)
            return data

    def read_kernel_info(self, kernel_file):
        """Reads the kernel file.

        Args:
            kernel_file (str): Filepath of the log file.
        
        Returns:
            (int, bytes): Tuple of filesize and the byte string.

        """
        with open(kernel_file, "rb") as fp:
            data = fp.read()
            return data
