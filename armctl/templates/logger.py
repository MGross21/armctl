import logging

SEND_LEVEL = logging.INFO + 1
RECEIVE_LEVEL = logging.INFO + 2

logging.addLevelName(SEND_LEVEL, "SEND")
logging.addLevelName(RECEIVE_LEVEL, "RECV")


def send(self, message, *args, **kws):
    if self.isEnabledFor(SEND_LEVEL):
        self._log(SEND_LEVEL, message, args, **kws)


def receive(self, message, *args, **kws):
    if self.isEnabledFor(RECEIVE_LEVEL):
        self._log(RECEIVE_LEVEL, message, args, **kws)


logging.Logger.send = send
logging.Logger.receive = receive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
