"""Provides the ability to start a server to provide KrakenTools functionality.

"""


import aiomas
import asyncio
import logging
from .kraken_process_manager_agent import KrakenProcessManagerAgent
from .kraken_share_manager_agent import KrakenShareManagerAgent

class KrakenServer(object):
    """Allows starting a server to control Kraken processes via ``KrakenTools``.

    The server is started using the ``aiomas`` containers and agents. Msgpack is used for encoding 
    and compression of messages. The server allows RPC requests to be processed and responded to.

    The ``KrakenProcessManagerAgent`` and ``KrakenShareAgent`` are assigned with an index of 0 and 
    1 in the container respectively.
    
    Args:
        host (str, optional): IP address to host the server on.
        port (int, optional): Port to bind the server to.
        rate_limit (float, optional): Interval in seconds to wait per RPC. Set to 0 to disable.
        blosc (bool, optional): Indicates whether blosc compression is used for messaging. Must be 
            enabled on both the server and client.
        share_dir (str, optional): Path to the share folder for Kraken. Defaults to /milk/share.

    Attributes:
        log (logging.Logger): The logger object.
        container (aiomas.Container): The container the server agent runs in. 
        host (str): The IP address to host the server on.
        port (int): The port to bind the server to.
        rate_limit (float): Interval in seconds to wait per RPC. Set to 0 to disable.
        blosc (bool): Indicates whether blosc compression is used for messaging. Must be 
            enabled on both the server and client.
        share_dir (str): Path to the share folder for Kraken.
        process_agent (KrakenProcessManagerAgent): The process manager agent.
        share_agent (KrakenShareManagerAgent): The share manager agent.

    """
    def __init__(self, host="0.0.0.0", port=20000, rate_limit=0, blosc=True, share_dir="/milk/share"):
        self.log = logging.getLogger(__file__)
        self.container = None
        self.host = host
        self.port = port
        self.rate_limit = rate_limit
        self.blosc = blosc
        self.share_dir = share_dir
        self.process_agent = None
        self.share_agent = None

    def start(self):
        """Starts the server.

        This allows a remote agent to access local agents on the server.
        
        Returns:
            bool: True if successful. False if not.

        """
        if self.container is None:
            self.container = aiomas.Container.create(
                (self.host, self.port), 
                codec=aiomas.MsgPack if not self.blosc else aiomas.MsgPackBlosc
            )
            self.process_agent = KrakenProcessManagerAgent(self.container, rate_limit=self.rate_limit)
            self.process_agent.start_tracking()
            self.log.info("Started process agent at {}".format(self.process_agent.addr))
            self.share_agent = KrakenShareManagerAgent(self.container, rate_limit=self.rate_limit, share_dir=self.share_dir)
            self.share_agent.start_tracking()
            self.log.info("Started share agent at {}".format(self.share_agent.addr))
            return True
        return False

    def stop(self):
        """Stops the server.

        This disconnects all remote clients and stops the file tracking.
        
        Returns:
            bool: True if successful. False if not.

        """
        if self.container is not None:
            self.process_agent.stop_tracking()
            self.share_agent.stop_tracking()
            self.log.info("Cleaning up remaining tasks.")
            loop = asyncio.get_event_loop()
            remaining = asyncio.all_tasks(loop)
            for task in remaining:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*remaining))
            self.log.info("Shutting down container.")
            self.container.shutdown()
            self.container = None
            self.log.info("Container shutdown complete.")
            self.process_agent.dispose()
            self.process_agent = None
            self.share_agent.dispose()
            self.share_agent = None
            return True
        return False
