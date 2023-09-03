import socket
from _thread import start_new_thread
import numpy as np
from game import Game

#server = "93.175.0.37"
#server = "127.0.0.1"
server = "192.168.0.12"
port = 7777
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen()
print(f"Server started at {server}:{port}, awaiting connection...")

def n2xy(n):
    return n%3, n//3

piece = {0:' ', 1: 'X', 2: 'O'}

class Player():

    def __init__(self, id, conn, addr):
        self.id = id
        self.conn = conn
        self.addr = addr
        self.game = None
        self.turn = 0
        self.ready = True

    def address(self):
        return ':'.join(str(a) for a in self.addr)

def send(conn, *args):
    conn.sendall(bytes(args))
    print("Sent", args, "to", conn.getpeername())

def threaded_client(player):
    conn = player.conn
    playing = [other.id for other in players]
    send(conn, player.id, len(playing), *playing)
    reply = ""
    while True:
        try:
            data = conn.recv(2048)
            if not data:
                break
            print(f"{player.address()}: received {data}")
            action = int(data[0])
            if action == 0: # connect to game
                print(f"{player.address()}: Attempting to connect to game")
                if player.game:
                    print(f"{player.address()}: Failed to connect, already connected to a game")
                    send(conn, 0, 4)
                    continue
                for game in active_games:
                    if game.awaiting:
                        if game.player_1 > -1:
                            player.game = game
                            player.turn = 2
                            game.player_2 = player.id
                            game.awaiting = False
                            game.game_over = False
                            print(f"{player.address()}: Connected to game {game.id} as O, game started")
                            send(conn, 1, game.id % 256, player.turn, game.player_1 % 256)
                            for other_player in players:
                                if other_player.id == game.player_1:
                                    send(other_player.conn, 5, player.id)
                        elif game.player_2 > -1:
                            player.game = game
                            player.turn = 1
                            game.player_1 = player.id
                            game.awaiting = False
                            game.game_over = False
                            print(f"{player.address()}: Connected to game {game.id} as X, game started")
                            send(conn, 1, game.id % 256, player.turn, game.player_2 % 256)
                            for other_player in players:
                                if other_player.id == game.player_2:
                                    send(other_player.conn, 5, player.id % 256)
                        else:
                            player.game = game
                            game.player_1 = player.id
                            player.turn = 1
                            print(f"{player.address()}: Connected to game {game.id} as X, awaiting second player...")
                            playing = [other.id for other in players]
                            send(conn, 2, game.id % 256, player.turn, min(len(playing), 255), *playing[-255:])
                if not player.game:
                    game = Game(ids["game_id"], player.id)
                    ids["game_id"] += 1
                    active_games.append(game)
                    player.game = game
                    player.turn = 1
                    print(f"{player.address()}: Started game {game.id} as X, awaiting second player...")
                    playing = [other.id for other in players]
                    send(conn, 2, game.id % 256, player.turn, min(len(playing), 255), *playing[-255:])
            elif action == 1: # play f*c
                field = data[1]
                cell = data[2]
                game = player.game
                if not player.game:
                    print(f"{player.address()}: Failed to play, not connected to a game")
                    send(conn, 0, 0)
                    continue
                print(f"{player.address()}: Attempting to play in game {game.id}: {field}x{cell}")
                if game.over():
                    print(f"{player.address()}: Failed to play, game {game.id} is over / has not started yet")
                    send(conn, 0, 1)
                    continue
                if game.turn != player.turn:
                    print(f"{player.address()}: Failed to play in game {game.id}: turn is {piece[game.turn]}, player is {piece[player.turn]}")
                    send(conn, 0, 2)
                    continue
                valid = game.play(field, cell)
                if not valid:
                    print(f"{player.address()}: Failed to play in game {game.id}: invalid cell or field num")
                    send(conn, 0, 3)
                    continue
                print(f"Server: game {game.id}:\n{game}")
                send(conn, 3, *game.field.flatten(), *game.main_field, game.active_field % 256)
                if game.over():
                    print(f"Game over, {piece[game.winner]+' won' if game.winner else 'draw'}")
                    send(conn, 4, game.winner)
                    player.ready = False
                other = game.player_1
                if player.turn == 1:
                    other = game.player_2
                for other_player in players:
                    if other_player.id == other:
                        send(other_player.conn, 3, *game.field.flatten(), *game.main_field, game.active_field % 256)
                        if game.over():
                            send(other_player.conn, 4, game.winner)
                            other_player.ready = False
            elif action == 2: # request restart game
                if not player.game:
                    print(f"{player.address()}: Failed to restart, not connected to a game")
                    send(conn, 0, 0)
                    continue
                if game.awaiting:
                    print(f"{player.address()}: Failed to restart, other player had disconnected")
                    send(conn, 0, 5)
                    continue
                player.ready = True
                other_ready = False
                other = game.player_1
                if player.turn == 1:
                    other = game.player_2
                for other_player in players:
                    if other_player.id == other:
                        if other_player.ready:
                            other_ready = True
                            game.player_1, game.player_2 = game.player_2, game.player_1
                            player.turn, other_player.turn = other_player.turn, player.turn
                            game.reset()
                            game.awaiting = False
                            game.game_over = False
                            send(conn, 1, game.id % 256, player.turn, other % 256)
                            send(other_player.conn, 1, game.id % 256, other_player.turn, player.id % 256)
                        else:
                            send(other_player.conn, 7)
                if not other_ready:
                    send(conn, 7)
            elif action == 3: # bail game
                if not player.game:
                    print(f"{player.address()}: Failed to leave, not connected to a game")
                    send(conn, 0, 0)
                    continue
                game = player.game
                print(f"{player.address()}: Left the game {game.id}")
                playing = [other.id for other in players]
                send(conn, 2, 255, 0, min(len(playing), 255), *playing[-255:])
                if player.turn == 1:
                    game.player_1 = -1
                    if game.player_2 == -1:
                        print(f"Server: Closed empty game {game.id}")
                        active_games.remove(game)
                    else:
                        game.reset()
                        game.awaiting = True
                        for other_player in players:
                            if other_player.id == game.player_2:
                                send(other_player.conn, 2, game.id % 256, 2, min(len(playing), 255), *playing[-255:])
                elif player.turn == 2:
                    game.player_2 = -1
                    if game.player_1 == -1:
                        print(f"Server: Closed empty game {game.id}")
                        active_games.remove(game)
                    else:
                        game.reset()
                        game.awaiting = True
                        for other_player in players:
                            if other_player.id == game.player_1:
                                send(other_player.conn, 2, game.id % 256, 1, min(len(playing), 255), *playing[-255:])
                player.turn = 0
                player.game = None
            elif action == 4: # message to opponent
                game = player.game
                if not game:
                    print(f"{player.address()}: Failed to send, not connected to a game")
                    send(conn, 0, 0)
                    continue
                other = game.player_2
                if player.turn == 2:
                    other = game.player_1
                if other == -1:
                    print(f"{player.address()}: Failed to send, other player has not connected yet")
                    send(conn, 0, 1)
                    continue
                valid = False
                for other_player in players:
                    if other_player.id == other:
                        other_player.conn.sendall(bytes([6])+bytes([player.id % 256])+bytes([1])+data[1:])
                        print(f"{player.id} to {other}: {data[1:].decode()}")
                        send(conn, 255)
                        valid = True
                if not valid:
                    print(f"{player.id} to {other}, which is nobody: {data[1:].decode()}")
            elif action == 5: # message to everyone
                for other_player in players:
                    other_player.conn.sendall(bytes([6])+bytes([player.id % 256])+bytes([0])+data[1:])
                print(f"{player.id} to everyone: {data[1:].decode()}")
            else:
                print(f"{player.address()}: Invalid action {action}")
                send(conn, 0, 255)
                continue
        except Exception as e:
            print(f"Error with {player.address()}: {e}")
            break

    if player.game:
        game = player.game
        if player.turn == 1:
            game.player_1 = -1
            game.reset()
            for other_player in players:
                if other_player.id == game.player_2:
                    send(other_player.conn, 2, game.id % 256, 2)
        else:
            game.player_2 = -1
            game.reset()
            for other_player in players:
                if other_player.id == game.player_1:
                    send(other_player.conn, 2, game.id % 256, 1)
    players.remove(player)
    print(f"{player.address()}: Disconnected")
    conn.close()

ids = {
    "game_id": 0,
    "player_id": 0
}
active_games = []
players = []
while True:
    try:
        conn, addr = s.accept()
        player = Player(ids["player_id"], conn, addr)
        ids["player_id"] += 1
        players.append(player)
        print("Connected to:", player.address())
        start_new_thread(threaded_client, (player,))
    except Exception as e:
        print("Error: " + str(e) + ", exiting server...")
        s.close()
        break
input()