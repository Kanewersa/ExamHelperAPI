import asyncio
import json
import time

import websockets
from websockets import ConnectionClosed

from channel import Channel
from database import Statement
from exam_channel import ExamChannel
from user import User


async def consume(message):
    if message == "get_all_data":
        pass
    elif message.startswith("get_exam"):
        pass


class WebsocketServer:
    def __init__(self):
        self.server = None
        self.address = "localhost"
        self.port = 8765
        self.users = set()
        self.channels = list()
        self.db = None

    def start_server(self, db):
        self.db = db
        self.db.create_tables()
        exams = Statement().get_all("exams").execute()
        self.channels.append(Channel(0))
        for _ in exams:
            self.channels.append(ExamChannel(len(self.channels)))

        self.server = websockets.serve(self.handler, self.address, self.port)
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    async def register_user(self, websocket):
        user = User(len(self.users), websocket)
        self.users.add(user)
        self.channels[0].add_user(user)
        print("New user connected. Assigned id: " + str(user.identifier))
        return user

    async def unregister_user(self, websocket):
        user = next(u for u in self.users if u.websocket == websocket)
        self.users.remove(user)
        for channel in self.channels:
            channel.remove_user(user)

    async def handler(self, websocket, path):
        user = await self.register_user(websocket)

        try:
            await self.login_user(user)
            await user.wait_for_message(self.handle_messages)
        except ConnectionClosed:
            pass
        finally:
            await self.unregister_user(websocket)

    async def login_user(self, user):
        users = Statement().get_all('users').where('ip_address').equals(user.ip_address).execute()
        if len(users) > 0:
            print('User (' + users[0][1] + ') has logged in.')
            await self.send_static_info(user)
        else:
            await user.send('login')
            msg = await user.recv()
            name = msg.split('/')[1]
            print('New user (' + name + ') created')
            Statement().insert('users (name, ip_address)', name, user.ip_address).execute()
            await self.send_static_info(user)

    async def send_static_info(self, user):
        data = {"terms": Statement().get_all("terms").execute(),
                "courses": Statement().get_all("courses").execute(),
                "exams": Statement().get_all("exams").execute()}
        await user.send(json.dumps(data))

    async def handle_messages(self, user, msg):
        # TODO: Remove delay (was added to simulate network connection)
        time.sleep(0.3)
        if msg.startswith("leave_channel"):
            if user.channel is not None:
                print("Leaving channel: " + str(user.channel))
                self.channels[user.channel].remove_user(user)
                user.channel = None
        elif msg.startswith("join_channel"):
            channel_id = int(msg.split('/')[1])
            print("Joining channel: " + str(channel_id))
            self.channels[channel_id].add_user(user)
        elif user.channel is None:
            print("Unknown command: " + msg + ". Sent by: " + user.identifier + ". User does not belong to any channel.")
        else:
            await self.channels[user.channel].process_message(user, msg)
