#!/usr/bin/python
# -*- coding: UTF-8 -*-

import curses
from random import choice, randrange
from collections import defaultdict

actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']

letters_codes = [ord(i) for i in 'WASDRQwasdrq']

actions_dict = dict(zip(letters_codes, actions * 2))



def get_user_action(keyboard):
    '''接受用户输入， 阻塞 + 循环'''
    char = 'N'
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]

def invert(field):
    '''将棋盘矩阵逆转'''
    return [row[::-1] for row in field]

def transpose(field):
    '''将棋盘矩阵转置'''
    return [list(row) for row in zip(*field)]


class GameField(object):
    '''棋盘'''
    def __init__(self, width=4, height=4, win=2048):
        self.width = width           #宽
        self.height = height         #高
        self.score = 0               #当前分数
        self.highscore = 0           #最高分
        self.win_value = win         #胜利分散
        self.reset()                 #重置棋盘

    def reset(self):
        '''重启棋盘'''
        if self.highscore < self.score:
            self.highscore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]          #生成4X4棋盘
        self.spawn()                                                                       #随机生成2个数
        self.spawn()



    def spawn(self):
        '''在4X4棋盘的随机生成2或4'''
        new_element = 4 if randrange(100) > 80 else 2
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])

        self.field[i][j] = new_element

    def is_win(self):
        '''判断胜利'''
        flag = False
        for row in self.field:
            for i in row:
                if i >= self.win_value:
                    flag = True
        return flag


    def is_gameover(self):
        '''判断失败'''
        list = []
        for move in actions:
            if self.move_is_possible(move):
                list.append(1)
            else:
                list.append(0)
        if 1 in list:
            return False
        else:
            return True



    def move_is_possible(self,direction):
        '''判断是否可以移动'''
        def row_is_left_movable(row):
            '''某一行是否可以移动'''
            def change(i):
                '''判断是否有元素可以移动或者合并'''
                if row[i] != 0 and row[i] == row[i + 1]:
                    return True
                if row[i] == 0 and row[i + 1] != 0:
                    return True
                return False
            return any(change(i) for i in range(len(row)-1))

        #四个方向合并
        check = {}
        check['Left'] = lambda field: any(row_is_left_movable(row) for row in field)
        check['Right'] = lambda field: check['Left'](invert(field))
        check['Up'] = lambda field: check['Left'](transpose(field))
        check['Down'] = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False



    def move(self, direction):
        '''移动一步'''
        def move_row_left(row):
            '''某行向左移动'''
            def tighten(row):
                '''将零散的元素向左移动'''
                new_row = [num for num in row if num != 0]
                for i in range(len(row) - len(new_row)):
                    new_row.append(0)
                return new_row

            def merge(row):
                '''合并元素'''
                new_row = []
                flag = False
                for i in range(len(row)):
                    if flag:
                        self.score += 2 * row[i]
                        new_row.append(2 * row[i])
                    else:
                        if (i + 1) < len(row) and row[i] == row[i + 1]:
                            new_row.append(0)
                            flag = True
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)

                return new_row


            return tighten(merge(tighten(row)))

        #四个方向移动
        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False




    def draw(self,screen):
        '''绘制棋盘'''
        help_string1 = '(W)Up (A)Left (S)down (D)down'
        help_string2 = '     (R)Restart (Q)Exit'
        win_string   = '            YOU WIN'
        gameover_string = '   GAMEOVER!'

        def cast(string):
            '''屏幕输出'''
            return screen.addstr(string + '\n')

        def draw_hor_separator():
            '''绘制水平分割线'''
            line = ('+------' * self.width + '+')
            cast(line)


        def draw_row(row):
            '''绘制行'''
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if self.highscore != 0:
            cast('HIGHSCORE: ' + str(self.highscore))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


def main(stdscr):
    '''主逻辑'''

    curses.use_default_colors()
    game_field = GameField(win=2048)


    def init():
        game_field.reset()
        return 'Game'

    def game():
        #画出当前棋盘状态
        game_field.draw(stdscr)
        #读取用户输入action
        action = get_user_action(stdscr)
        if action == 'Restart':
            return 'Init'

        if action == 'Exit':
            return 'Exit'

        if game_field.move(action):
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    def not_game(state):
        #画出 gameover和 win的界面
        game_field.draw(stdscr)
        #读取用户输入action，判断是重启还是结束游戏
        action = get_user_action(stdscr)
        res = defaultdict(lambda: state)
        res['Restart'], res['Exit'] = 'Init', 'Exit'
        return res[action]


    actions_state={
        'Init': init,
        'Win': lambda: not_game('Win'),
        'Gameover': lambda: not_game('Gameover'),
        'Game': game
    }

    state = 'Init'
    #状态机开始循环
    while state != 'Exit':
        state = actions_state[state]()

curses.wrapper(main)





















