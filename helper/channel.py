class Channel:
    def __init__(self, identifier):
        self.identifier = identifier
        self.users = set()

    async def process_message(self, user, message):
        if self.users:
            for user in self.users:
                await user.send(message)

    def add_user(self, user):
        self.users.add(user)
        user.channel = self.identifier

    def remove_user(self, user):
        self.users.discard(user)
        user.channel = None
