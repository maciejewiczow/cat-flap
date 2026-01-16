import asyncio
from logging import Logger
import pickle
from typing import Any, AsyncGenerator
import zmq
import zmq.asyncio
from .messages import Message


class MessageHub:
    def __init__(self, socket_dir: str):
        self.context = zmq.asyncio.Context()

        self.pub_address = f"ipc://{socket_dir}/message_hub_pub.sock"
        self.sub_address = f"ipc://{socket_dir}/message_hub_sub.sock"


class HubProcessMessageHub(MessageHub):
    def run_hub(self):
        xpub = self.context.socket(zmq.XPUB)
        xsub = self.context.socket(zmq.XSUB)

        xpub.setsockopt(zmq.XPUB_VERBOSE, 1)

        xpub.bind(self.pub_address)
        xsub.bind(self.sub_address)

        try:
            zmq.proxy(xsub, xpub)
        finally:
            xpub.close()
            xsub.close()
            self.context.term()


class WorkerMessageHub(MessageHub):
    def __init__(self, socket_dir: str, log: Logger):
        super().__init__(socket_dir)
        self.log = log

        self.sub_socket = self.context.socket(zmq.SUB)
        self.pub_socket = self.context.socket(zmq.PUB)

        self.sub_socket.connect(self.pub_address)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.pub_socket.connect(self.sub_address)

        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.sub_socket, zmq.POLLIN)

    async def send(self, message: Message):
        await self.pub_socket.send(pickle.dumps(message))

    async def receive(self, *, timeout=100) -> AsyncGenerator[Message, Any]:
        while True:
            try:
                events = await self.poller.poll(timeout=timeout)

                if events:
                    yield pickle.loads(await self.sub_socket.recv())
            except asyncio.CancelledError:
                break
