# Super-Tic-Tac-Toe
Python implementation of a new variation on tic-tac-toe, inspired by Vsauce

# Setup
To start a singleplayer game vs AI bot with minimax algorithm, run client.py without starting server  
To start a local multiplayer game, edit server IP string in both server.py and client.py to your server host's IP, then run server.py and as many instances of client.py as you wish in the same local network.

# Settings
There are commands available in singleplayer mode to switch modes of the AI. To turn them on, type them in the in-game chat text field and press 'Change diff' button; to turn off, type it again.  
List of the commands:  
*/killmeplease* command imposes penalty on AI's amount of moves; as a result, AI will try to finish a game as soon as possible.  
*/dontkillmeplease* command imposes negative penalty on AI's amount of moves; as a result, AI will try to continue a game for as long as possible while still maintaining the same score.  
*/hint* command turns on training mode, in which you will get information on AI's estimation of a current situation and your best move in its opinion, derived from minimax algorithm
