class User:
    def __init__(self, identifier, websocket):
        self.identifier = identifier
        self.websocket = websocket
        self.channel = None
        self.ip_address = websocket.remote_address[0]

    async def send(self, message):
        await self.websocket.send(message)

    async def wait_for_message(self, function):
        async for message in self.websocket:
            await function(self, message)

    async def recv(self):
        return await self.websocket.recv()
