import socket
import tkinter as tk
from PIL import Image, ImageTk
from _thread import start_new_thread
import numpy as np
import matplotlib.pyplot as plt
import time
import ctypes
from game import Game, piece, calculate

#server = "93.175.0.37"
server = "127.0.0.1"
port = 7777
my_id = -1
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

piece = {0:' ', 1: 'X', 2: 'O'}

def send(conn, *args):
    conn.sendall(bytes(args))
    
def print_pos(field, main_field):
    fields = [
        [" ".join([piece[field[i][j*3 + k]] for k in range(3)]) for j in range(3)] if main_field[i] == 0 else
        ["X   X", "  X  ", "X   X"] if piece[main_field[i]] == 'X' else ["  O  ", "O   O", "  O  "]
    for i in range(9)]
    for i in range(9):
        if fields[i][1][2] == ' ':
            fields[i][1] = fields[i][1][:2] + str(i) + fields[i][1][3:]
    return "\n-----------------\n".join(["\n".join(["|".join([fields[i * 3 + k][j] for k in range(3)]) for j in range(3)]) for i in range(3)])
    
awaiting = False

app = tk.Tk()
win_w = 256
win_h = 256
rate = 256 // 3
srate = rate // 3
field = np.zeros((9,9), dtype=np.uint8)
main_field = np.zeros(9, dtype=np.uint8)
AI_diffs = [1000, 5000, 10000, 30000, 60000]
AI_diff_names = ["childplay", "easy", "normal", "hard", "insane"]
settings = {
    "my_id": -1,
    "active_field": -1,
    "game_state": 0,
    "winner": -1,
    "closed": False,
    "game_id": -1,
    "my_turn": 0,
    "other": -1,
    "player_num": 0,
    "players": [],
    "AI_turn": 2,
    "AI_diff": 2,
    "hint_mode": False,
    "hinted": -1,
    "timefine": 0
}
field_texture = plt.imread("textures/field.png")
x = plt.imread("textures/x.png")
o = plt.imread("textures/o.png")
chosen = plt.imread("textures/chosen.png")
hint = plt.imread("textures/-.png")
Field_img = ImageTk.PhotoImage(image=Image.fromarray((field_texture * 255).astype(np.uint8)))
X_imgs = [ImageTk.PhotoImage(image=Image.fromarray((x * 255).astype(np.uint8)).rotate(90*i).resize((rate, rate), Image.LANCZOS)) for i in range(4)]
O_imgs = [ImageTk.PhotoImage(image=Image.fromarray((o * 255).astype(np.uint8)).rotate(45*i).resize((rate, rate), Image.LANCZOS)) for i in range(8)]
field_img = ImageTk.PhotoImage(image=Image.fromarray((field_texture * 255).astype(np.uint8)).resize((rate, rate), Image.LANCZOS))
x_imgs = [ImageTk.PhotoImage(image=Image.fromarray((x * 255).astype(np.uint8)).rotate(90*i).resize((srate, srate), Image.LANCZOS)) for i in range(4)]
o_imgs = [ImageTk.PhotoImage(image=Image.fromarray((o * 255).astype(np.uint8)).rotate(45*i).resize((srate, srate), Image.LANCZOS)) for i in range(8)]
Chosen_img = ImageTk.PhotoImage(image=Image.fromarray((chosen * 255).astype(np.uint8)))
chosen_img = ImageTk.PhotoImage(image=Image.fromarray((chosen * 255).astype(np.uint8)).resize((rate, rate), Image.LANCZOS))
hint_img = ImageTk.PhotoImage(image=Image.fromarray((hint * 255).astype(np.uint8)).resize((srate, srate), Image.LANCZOS))

def start_game():
    if settings["my_id"] < 0:
        single.reset()
        single.start()
        settings["my_turn"] = 3-settings["AI_turn"]
        if settings["game_state"] == 0:
            if settings["AI_turn"] == 1:
                settings["game_state"] = 3
                update_screen(False)
                cost, pos, spent = calculate(single, settings["AI_turn"], AI_diffs[settings["AI_diff"]], True, True, settings["timefine"])
                if settings["hint_mode"]:
                    add_text(to_hint(cost, pos, spent), "AI")
                single.play(pos[0]//9, pos[0]%9)
            settings["game_state"] = 2
        else:
            settings["game_state"] = 0
    else:
        if settings["game_state"] == 0:
            send(client, 0)
        else:
            send(client, 3)

def reset():
    field[:] = np.zeros((9,9), dtype=np.uint8)
    main_field[:] = np.zeros(9, dtype=np.uint8)
    settings['active_field'] = -1

def add_text(text, source='Server'):
    text_field.config(state='normal')
    time_s = time.asctime()[4:-5]
    text_field.insert(1.0, f'{time_s} {source}: {text}\n\n')
    text_field.tag_add('time', 1.0, '1.'+str(len(time_s)+1))
    text_field.tag_add('sender', '1.'+str(len(time_s)+1), '1.'+str(len(source)+len(time_s)+1))
    text_field.config(state='disabled')

def click(event):
    if settings["my_id"] < 0:
        if settings["game_state"] == 2:
            fi, ce = int(event.y // rate * 3 + event.x // rate), int((event.y % rate) // srate * 3 + (event.x % rate) // srate)
            t = single.play(fi, ce)
            if not single.over() and t:
                settings["game_state"] = 3
                update_screen(False)
                cost, pos, spent = calculate(single, settings["AI_turn"], AI_diffs[settings["AI_diff"]], True, True, settings["timefine"])
                if settings["hint_mode"]:
                    add_text(to_hint(cost, pos, spent), "AI")
                single.play(pos[0]//9, pos[0]%9)
            settings["game_state"] = 2
            if single.over():
                settings["game_state"] = 4
        elif settings["game_state"] == 4:
            single.reset()
            single.start()
            settings["my_turn"] = 3-settings["AI_turn"]
            if settings["AI_turn"] == 1:
                settings["game_state"] = 3
                update_screen(False)
                cost, pos, spent = calculate(single, settings["AI_turn"], AI_diffs[settings["AI_diff"]], True, True, settings["timefine"])
                if settings["hint_mode"]:
                    add_text(to_hint(cost, pos, spent), "AI")
                single.play(pos[0]//9, pos[0]%9)
            settings["game_state"] = 2
    else:
        if settings["game_state"] == 2:
            field_n = int(event.y // rate * 3 + event.x // rate)
            cell_n = int((event.y % rate) // srate * 3 + (event.x % rate) // srate)
            if field_n < 0 or field_n > 8 or cell_n < 0 or cell_n > 8:
                return
            send(client, 1, field_n, cell_n)
        if settings["game_state"] == 4:
            send(client, 2)
            settings["game_state"] = 5

def listen(server):
    while True:
        try:
            res = server.recv(1)
        except:
            print("Connection error")
            break
        res_key = int(res[0])
        if res_key == 0:
            res = server.recv(1)
            err_key = int(res[0])
            if err_key == 0:
                status = "not connected to a game"
            elif err_key == 1:
                status = "game is over / has not started yet"
            elif err_key == 2:
                status = "not your turn yet"
            elif err_key == 3:
                status = "invalid cell or field num"
            elif err_key == 4:
                status = "failed to connect, already connected to a game"
            elif err_key == 5:
                status = "failed to restart, other player had disconnected"
            elif err_key == 255:
                status = "invalid action"
            else:
                status = "unknown error"
            print(status)
            add_text(status, 'Error')
        elif res_key == 1:
            res = server.recv(3)
            settings["game_id"], settings["my_turn"], settings["other"] = int(res[0]), int(res[1]), int(res[2])
            status = f"Connected to game {settings['game_id']} as {piece[settings['my_turn']]}, you are playing with {settings['other']}"
            print(status)
            add_text(status)
            if settings["my_turn"] == 1:
                settings["game_state"] = 2
                status_text.config(text='Your turn')
            else:
                settings["game_state"] = 3
                status_text.config(text='Started')
            reset()
        elif res_key == 2:
            res = server.recv(2)
            settings["game_id"], settings["my_turn"] = int(res[0]), int(res[1])
            if settings["game_id"] == 255:
                status = f"Bailed the game"
                settings["game_state"] = 0
            elif settings["game_state"] == 0:
                status = f"Connected to game {settings['game_id']} as {piece[settings['my_turn']]}, awaiting other player..."
                settings["game_state"] = 1
            else:
                status = f"Player {settings['other']} left, awaiting other player..."
                settings["game_state"] = 1
                settings['other'] = -1
            settings["player_num"] = int(client.recv(1)[0])
            settings["players"] = []
            for i in range(settings['player_num']):
                settings["players"].append(int(client.recv(1)[0]))
            status += f"\nCurrently online {settings['player_num']} players: {settings['players']}"
            print(status)
            add_text(status)
            status_text.config(text='Connected')
            reset()
        elif res_key == 3:
            res = server.recv(91)
            field[:] = np.array([[int(res[j*9+i]) for i in range(9)] for j in range(9)])
            main_field[:] = np.array([int(f) for f in res[81:90]])
            settings["active_field"] = int(res[90])
            if settings["active_field"] == 255:
                settings["active_field"] = -1
            # print(print_pos(field, main_field))
            # print("active field is", settings["active_field"])
            if settings["game_state"] == 3:
                status = "It is your turn now"
                settings["game_state"] = 2
                status_text.config(text='Your turn')
            elif settings["game_state"] == 2:
                status = f"Successfully played, awaiting other player..."
                settings["game_state"] = 3
                status_text.config(text='Waiting...')
            print(status)
            add_text(status)
        elif res_key == 4:
            res = server.recv(1)
            settings["winner"] = int(res[0])
            if settings["winner"] == settings["my_turn"]:
                status = "You win!"
            elif settings["winner"] == 0:
                status = "Draw!"
            else:
                status = "You lose!"
            print(status)
            add_text(status)
            add_text("Click anywhere to restart", "Hint")
            status_text.config(text=status)
            settings["game_state"] = 4
        elif res_key == 5:
            res = server.recv(1)
            settings["other"] = int(res[0])
            status = f"Game started! You are playing with {settings['other']}"
            print(status)
            add_text(status)
            if settings["my_turn"] == 1:
                print("It is your turn now")
                settings["game_state"] = 2
                status_text.config(text='Your turn')
            else:
                print("Awaiting other player's move...")
                settings["game_state"] = 3
                status_text.config(text='Waiting...')
        elif res_key == 6:
            res = server.recv(2048)
            author = int(res[0])
            dest = int(res[1])
            mess = res[2:].decode()
            if dest == 0:
                dest = 'everyone'
            else:
                dest = 'you'
            print(f"{author} to {dest}:", mess)
            add_text(mess, f"{author} to {dest}")
        elif res_key == 7:
            if settings["game_state"] == 4:
                status = f"wants to restart! Click anywhere to confirm."
                add_text(status, str(settings["other"]))
            elif settings["game_state"] == 5:
                status = f"Restarting, waiting for other player to confirm..."
                add_text(status)
            print(status)
            status_text.config(text='Waiting...')
        elif res_key == 255:
            print("Ok")
            add_text("Ok")
        else:
            status = f"Unknown response from server: {res_key}"
            print(status)
            add_text(status, "Error")
    # TODO: enter offline mode

def update_screen(after=True):
    if settings["my_id"] < 0:
        label_id.config(text='Offline mode')
        settings["active_field"] = single.active_field
        field[:] = single.field
        main_field[:] = single.main_field
        if settings["game_state"] == 0:
            c.config(state='disabled')
            c.delete("all")
            start_butt.config(text='Connect vs AI')
            send_butt.config(state='disabled')
            send_all_butt.config(state='disabled')
            turn_text.config(text='-')
            label_opponent.config(text='Not in game...')
        else:
            c.config(state='normal')
            start_butt.config(text='Bail')
            send_butt.config(state='normal', text='Change diff')
            send_all_butt.config(state='normal', text='Change X/O')
            label_opponent.config(text=f"Opponent: {piece[settings['AI_turn']]}, difficulty: {AI_diff_names[settings['AI_diff']]}")
    else:
        label_id.config(text=f'Id: {settings["my_id"]}')
        send_all_butt.config(state='normal')
        if settings["game_state"] == 0:
            c.config(state='disabled')
            c.delete("all")
            start_butt.config(text='Connect')
            turn_text.config(text='-')
            send_butt.config(state='disabled')
            label_opponent.config(text='Not in game...')
        elif settings["game_state"] == 1:
            c.config(state='disabled')
            c.delete("all")
            start_butt.config(text='Bail')
            turn_text.config(text='-')
            send_butt.config(state='disabled')
            label_opponent.config(text='No opponent...')
        else:
            c.config(state='normal')
            start_butt.config(text='Bail')
            send_butt.config(state='normal')
            label_opponent.config(text=f"Opponent: {settings['other']}")
    if settings["game_state"] > 1:
        if settings["game_state"] == 2:
            turn_text.config(text=piece[settings["my_turn"]])
        if settings["game_state"] == 3:
            turn_text.config(text=piece[3-settings["my_turn"]])
        c.delete("all")
        c.create_image(0, 0, image=Field_img, anchor='nw')
        np.random.seed(seed)
        for i in range(9):
            c.create_image(i % 3 * rate, i // 3 * rate, image=field_img, anchor='nw')
            for j in range(9):
                num = np.random.randint(8)
                if field[i, j] == 1:
                    c.create_image((i % 3 * rate) + (j % 3 * srate), (i // 3 * rate) + (j // 3 * srate), image=x_imgs[num%4], anchor='nw')
                elif field[i, j] == 2:
                    c.create_image((i % 3 * rate) + (j % 3 * srate), (i // 3 * rate) + (j // 3 * srate), image=o_imgs[num], anchor='nw')
                elif settings["hinted"] // 9 == i and settings["hinted"] % 9 == j:
                    c.create_image((i % 3 * rate) + (j % 3 * srate), (i // 3 * rate) + (j // 3 * srate), image=hint_img, anchor='nw')
            num = np.random.randint(8)
            if main_field[i] == 1:
                c.create_image(i % 3 * rate, i // 3 * rate, image=X_imgs[num%4], anchor='nw')
            elif main_field[i] == 2:
                c.create_image(i % 3 * rate, i // 3 * rate, image=O_imgs[num], anchor='nw')
            if settings["game_state"] in [2, 3] and settings["active_field"] == i:
                c.create_image(i % 3 * rate, i // 3 * rate, image=chosen_img, anchor='nw')
        if settings["game_state"] in [2, 3] and settings["active_field"] == -1:
            c.create_image(0, 0, image=Chosen_img, anchor='nw')
        if settings["game_state"] == 2:
            c.config(cursor=('X_cursor' if settings["my_turn"] == 1 else 'circle'))
        elif settings["game_state"] == 3:
            c.config(cursor='watch')
        elif settings["game_state"] == 4:
            c.config(cursor=('pirate' if settings["winner"] == 0 else 'iron_cross' if settings["winner"] == 1 else 'target'))
    app.update()
    if not settings["closed"] and after:
        app.after(100, update_screen)

def to_hint(cost, pos, spent):
    phrase = 'AI estimates '
    cost -= (len(pos)-1) * settings["timefine"]
    settings["hinted"] = pos[1]
    if cost == 0:
        phrase += 'you draw'
    elif cost<0:
        phrase += f'you lead {-cost} points' if cost > -900 else 'you basically won'
    else:
        phrase += f'you are losing {cost} points' if cost < 900 else 'you basically lost'
    phrase += f"\nAI thinks your best next move to be field {pos[1]//9}: cell {pos[1]%9}\n"
    if abs(cost) > 900:
        phrase += f"AI is estimating the game to be finished in {len(pos)-1} moves"
    else:
        phrase += f"AI has calculated {len(pos)-1} moves"
    return phrase

def send_opponent():
    if settings["my_id"] < 0:
        mess = entry.get()
        if mess.strip() == '/hint':
            if settings["hint_mode"]:
                settings["hint_mode"] = False
                add_text("Entering pro mode", "cheatengine")
                settings["hinted"] = -1
            else:
                settings["hint_mode"] = True
                add_text("Entering training mode, AI will tell its estimate on situation and suggest your best move in its opinion\nBest played in insane diff", "cheatengine")
            entry.delete(0, tk.END)
        elif mess.strip() == '/killmeplease':
            if settings["timefine"] == 1:
                settings["timefine"] = 0
                add_text("Sudden death reverted, play as usual", "cheatengine")
            else:
                settings["timefine"] = 1
                add_text("Sudden death activated, AI will try to kill you painlessly and quickly", "cheatengine")
            entry.delete(0, tk.END)
        elif mess.strip() == '/dontkillmeplease':
            if settings["timefine"] == -1:
                settings["timefine"] = 0
                add_text("Postponed death reverted, play as usual", "cheatengine")
            else:
                settings["timefine"] = -1
                add_text("Postponed death activated, AI will try to kill you as slow as possible, enjoy your suffering", "cheatengine")
            entry.delete(0, tk.END)
        else:
            settings["AI_diff"] = (settings["AI_diff"]+1) % 5
            single.reset()
            single.start()
            if settings["game_state"] > 0:
                if settings["AI_turn"] == 1:
                    settings["game_state"] = 3
                    update_screen(False)
                    cost, pos, spent = calculate(single, settings["AI_turn"], AI_diffs[settings["AI_diff"]], True, True, settings["timefine"])
                    if settings["hint_mode"]:
                        add_text(to_hint(cost, pos, spent), "AI")
                    single.play(pos[0]//9, pos[0]%9)
                settings["game_state"] = 2
    else:
        mess = entry.get()
        if mess.strip():
            mess = mess.strip().encode()
            client.sendall(bytes([4])+mess[:2046])
            entry.delete(0, tk.END)

def send_all():
    if settings["my_id"] < 0:
        settings["my_turn"] = settings["AI_turn"]
        settings["AI_turn"] = 3-settings["AI_turn"]
        single.reset()
        single.start()
        if settings["game_state"] > 0:
            if settings["AI_turn"] == 1:
                settings["game_state"] = 3
                update_screen(False)
                cost, pos, spent = calculate(single, settings["AI_turn"], AI_diffs[settings["AI_diff"]], True, True, settings["timefine"])
                if settings["hint_mode"]:
                    add_text(to_hint(cost, pos, spent), "AI")
                single.play(pos[0]//9, pos[0]%9)
            settings["game_state"] = 2
    else:
        mess = entry.get()
        if mess.strip():
            mess = mess.strip().encode()
            client.sendall(bytes([5])+mess[:2046])
            entry.delete(0, tk.END)

label_id = tk.Label(text='Not connected...')
label_id.grid(row=1, column=1, columnspan=3)
label_opponent = tk.Label(text='Not in game...')
label_opponent.grid(row=1, column=4, columnspan=3)
text_field = tk.Text(width=30, height=16, wrap='word', state='disabled')
text_field.grid(row=2, column=4, columnspan=3)
text_field.tag_config('sender', foreground='red')
text_field.tag_config('time', foreground='blue')
entry = tk.Entry(width=25)
entry.grid(row=3, column=4)
send_butt = tk.Button(text="Send", command=send_opponent)
send_butt.grid(row=3, column=5)
send_all_butt = tk.Button(text="Send all", command=send_all)
send_all_butt.grid(row=3, column=6)
c = tk.Canvas(bg='#E0CDA8', width=256, height=256, cursor='watch', state='disabled')
c.grid(row=2, column=1, columnspan=3)
start_butt = tk.Button(text="Connect", command=start_game)
start_butt.grid(row=3, column=1, padx=10, pady=5)
turn_text = tk.Label(text='-')
turn_text.grid(row=3, column=3, padx=10, pady=5)
status_text = tk.Label(text='Idle')
status_text.grid(row=3, column=2, padx=10, pady=5)
seed = np.random.randint(np.iinfo(np.int32).max)
single = Game(0, 0, 0)
single.start()

print("Awaiting connection to the server...")
trys = 0
while settings["my_id"] == -1:
    try:
        client.connect((server, port))
        settings["my_id"] = int(client.recv(1)[0])
        print("Connected! Your id is:", my_id)
        settings["player_num"] = int(client.recv(1)[0])
        settings["players"] = []
        for i in range(settings['player_num']):
            settings["players"].append(int(client.recv(1)[0]))
        add_text(f"Your id: {settings['my_id']}\nCurrently online {settings['player_num']} players: {settings['players']}")
        label_id.config(text=f"Id: {settings['my_id']}")
        receiver = start_new_thread(listen, (client,))
    except socket.error as e:
        if trys < 1:
            print("Connection error:", str(e))
            print("Trying to reconnect...")
            trys += 1
        else:
            print("Couldn't establish connection, entering single play mode...")
            break
c.bind("<Button>", click)
app.after(1, update_screen)
ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 6 )
try:
    app.mainloop()
except:
    pass
settings["closed"] = True