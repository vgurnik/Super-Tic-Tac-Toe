import numpy as np

piece = {0:' ', 1: 'X', 2: 'O'}

class Game():
    
    def __init__(self, id, player1_id=None, player2_id=None):
        self.id = id
        self.field = np.zeros((9, 9), dtype=np.uint8)
        self.main_field = np.zeros(9, dtype=np.uint8)
        self.turn = 1
        self.game_over = True
        self.active_field = -1
        self.winner = 0
        self.awaiting = True
        if player1_id != None:
            self.player_1 = player1_id
            if player2_id != None:
                self.player_2 = player2_id
                self.awaiting = False
            else:
                self.player_2 = -1
        else:
            self.player_1 = -1
            self.player_2 = -1

    def check(self, field):
        ar = [field[i*3]==field[i*3+1]==field[i*3+2]>0 for i in range(3)]
        if np.any(ar):
            return field[::3][ar][0]
        ar = [field[i]==field[i+3]==field[i+6]>0 for i in range(3)]
        if np.any(ar):
            return field[:3][ar][0]
        if field[0]==field[4]==field[8]>0 or field[2]==field[4]==field[6]>0:
            return field[4]
        if np.all(field):
            return -1
        return 0

    def check_validity(self, field_num, cell_num):
        if field_num < 0 or field_num > 8:
            return False
        if cell_num < 0 or cell_num > 8:
            return False
        if not self.game_over and self.main_field[field_num] == 0 and (self.active_field == -1 or self.active_field == field_num) and self.field[field_num, cell_num] == 0:
            return True
        return False
    
    def play(self, field_num, cell_num):
        if field_num < 0 or field_num > 8:
            return False
        if cell_num < 0 or cell_num > 8:
            return False
        if not self.game_over and self.main_field[field_num] == 0 and (self.active_field == -1 or self.active_field == field_num) and self.field[field_num, cell_num] == 0:
            self.field[field_num, cell_num] = self.turn
            c = self.check(self.field[field_num])
            if c > 0:
                self.main_field[field_num] = c
            self.active_field = cell_num if self.check(self.field[cell_num]) == 0 else -1
            over = True
            for i in range(9):
                if np.any(self.field[i]==0) and self.main_field[i]==0:
                    over = False
            check = self.check(self.main_field)
            if check or over:
                self.game_over = True
                self.winner = 0 if (over or (check == -1)) else check
                return True
            self.turn = 3-self.turn
            return True
        return False

    def clone(self):
        clone = Game(self.id, self.player_1, self.player_2)
        clone.field = self.field.copy()
        clone.main_field = self.main_field.copy()
        clone.turn = self.turn
        clone.game_over = self.game_over
        clone.active_field = self.active_field
        return clone
    
    def reset(self):
        self.field = np.zeros((9, 9), dtype=np.uint8)
        self.main_field = np.zeros(9, dtype=np.uint8)
        self.turn = 1
        self.game_over = True
        self.active_field = -1
        self.winner = 0

    def start(self):
        if not self.awaiting:
            self.game_over = False
    
    def over(self):
        return self.game_over

    def __str__(self):
        fields = [
            [" ".join([piece[self.field[i, j*3 + k]] for k in range(3)]) for j in range(3)] if self.main_field[i] == 0 else
            ["X   X", "  X  ", "X   X"] if piece[self.main_field[i]] == 'X' else ["  O  ", "O   O", "  O  "]
        for i in range(9)]
        for i in range(9):
            if fields[i][1][2] == ' ':
                fields[i][1] = fields[i][1][:2] + str(i) + fields[i][1][3:]
        return "\n-----------------\n".join(["\n".join(["|".join([fields[i * 3 + k][j] for k in range(3)]) for j in range(3)]) for i in range(3)])

    def estimate(self, turn):
        c = self.check(self.main_field)
        if c < 0:
            return True, 0
        elif c > 0:
            if c == turn:
                return True, 1000
            else:
                return True, -1000
        else:
            m_field = self.main_field.copy()
            field = self.field.copy()
            if turn==2:
                m_field[self.main_field==2] = 1
                m_field[self.main_field==1] = 2
                field[self.field==2] = 1
                field[self.field==1] = 2
            n = (m_field==1).sum()*9 - (m_field==2).sum()*9 + lookup[(m_field * f2tri).sum()] * 18
            for i in range(9):
                if m_field[i] == 0:
                    n += lookup[(field[i] * f2tri).sum()]
            # empty = np.nonzero(self.main_field == 0)[0]
            # for i in empty:
            #     self.main_field[i] = turn
            #     c = self.check(self.main_field)
            #     if c == turn:
            #         n += 18
            #     self.main_field[i] = 3-turn
            #     c = self.check(self.main_field)
            #     if c > 0:
            #         n -= 18
            #     self.main_field[i] = 0
            # for j in range(9):
            #     if self.main_field[j] == 0:
            #         empty = np.nonzero(self.field[j] == 0)[0]
            #         for i in empty:
            #             self.field[j][i] = turn
            #             c = self.check(self.field[j])
            #             if c == turn:
            #                 n += 1
            #             self.field[j][i] = 3-turn
            #             c = self.check(self.field[j])
            #             if c > 0:
            #                 n -= 1
            #             self.field[j][i] = 0
            #     elif self.main_field[j] == turn:
            #         n += 9
            #     else:
            #         n -= 9
        
            # field_here = self.field.copy()
            # field_here[self.main_field > 0] = 0
            # n += (field_here == turn).sum()
            # n -= (field_here == 3-turn).sum()
            return False, n

lookup = np.zeros(3**9, dtype=np.int32)
lookup = np.zeros(3**9, dtype=np.int32)
f2tri = 3**np.arange(9)
field = np.zeros(9)
game = Game(0)
for i in range(3**9):
    k = i
    n = 0
    for j in range(9):
        field[j] = k%3
        k //= 3
    c = game.check(field)
    if c != 0:
        lookup[i] = c
    else:
        empty = np.nonzero(field == 0)[0]
        for e in empty:
            field[e] = 1
            c = game.check(field)
            if c == 1:
                n += 1
            field[e] = 2
            c = game.check(field)
            if c > 0:
                n -= 1
            field[e] = 0
        lookup[i] = n

def calculate(game, turn, cost, minmax, addret=False, timefine=0):
    est, amount = game.estimate(turn)
    if est or cost < 1:
        #print(game, amount, turn)
        return amount, [-2+est], 1
    if np.sum(game.field) == 0:
        positions = np.array([0,1,2,4,5,8,9,10,12,13,15,16,27,28,29,30,31,32,36,37,40])
    else:
        positions = (game.field == 0)*1
        positions[game.main_field>0] = 0
        f,c = np.nonzero(positions)
        if game.active_field > -1:
            c = c[f==game.active_field]
            f = f[f==game.active_field]
        positions = f*9+c
    costs = np.zeros_like(positions)
    rets = [[]] * len(positions)
    if cost < len(positions) or len(positions) == 0:
        # print(game, amount)
        return amount, [-2], 1
    cost = cost / len(positions)
    spent = 0
    index = -1
    for i,p in enumerate(positions):
        game1 = game.clone()
        res = [-1]
        if game1.play(p//9, p%9):
            costs[i], res, s = calculate(game1, turn, cost, not minmax, True, timefine)
            spent += s
            cost += (cost-s) / (len(positions)-i)
        rets[i] = res
        if (minmax and costs[i] > 900) or (not minmax and costs[i] < -900):
            index = i
            break
    if index < 0:
        if minmax:
            index = np.argmax(costs)
        else:
            index = np.argmin(costs)
        if (costs==costs[index]).sum() > 1:
            index = np.random.choice(np.nonzero(costs==costs[index])[0])
    if addret:
        return costs[index]+timefine, [positions[index]] + rets[index], spent
    else:
        return costs[index]+timefine