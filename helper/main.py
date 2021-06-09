from database import DatabaseManager
from websockets_server import WebsocketServer


if __name__ == '__main__':
    database_manager = DatabaseManager()
    database_manager.connect()

    server = WebsocketServer()
    server.start_server(database_manager)
    print("Server started.")
