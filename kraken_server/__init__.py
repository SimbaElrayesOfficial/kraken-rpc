"""Allows remote access to ``KrakenTools`` functionality.

Classes in this module provide remote users with the ability to connect to the Kraken server and 
call on the classes in the ``KrakenTools`` module.

"""


from .kraken_process_manager_agent import KrakenProcessManagerAgent
from .kraken_share_manager_agent import KrakenShareManagerAgent
from .kraken_server import KrakenServer
