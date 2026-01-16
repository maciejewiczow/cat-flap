import asyncio
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

        xpub.bind(self.pub_address)
        xsub.bind(self.sub_address)

        try:
            zmq.proxy(xpub, xsub)
        finally:
            xpub.close()
            xsub.close()


class WorkerMessageHub(MessageHub):
    def __init__(self, socket_dir: str):
        super().__init__(socket_dir)

        self.pub_socket = self.context.socket(zmq.PUB)

        self.pub_socket.connect(self.pub_address)

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.sub_address)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

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
