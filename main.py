from random import randint


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"({self.x}, {self.y})"


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"


class BoardWrongShipException(BoardException):
    pass


class Game:
    def __init__(self, size=6):
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = False

        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def random_board(self):
        board = None
        while board is None:
            board = self.random_place()
        return board

    def random_place(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        attempts = 0
        for l in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def greet(self):
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def loop(self):
        num = 0
        st = []
        st2 = []
        repeat_ai = False  # Показывает повторно ли ходит AI
        while True:
            print("-" * 20)
            print("Доска пользователя:           Доска компьютера:")
            st = str(self.us.board).split("!")
            st2 = str(self.ai.board).split("!")
            for i in range(len(st)):
                print(f"{st[i]}   {st2[i]}")
            if num % 2 == 0:
                print("Ходит пользователь!")
                repeat = self.us.move(False)

            else:
                print("-" * 20)
                print("Ходит компьютер!")
                repeat = self.ai.move(repeat_ai)
                repeat_ai = repeat
            if repeat:
                num -= 1

            if self.ai.board.count == 7:
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.count == 7:
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()


class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow
        self.l = l
        self.o = o
        self.lives = l  # кол-во жизней корабля

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):
        return shot in self.dots


class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid
        self.count = 0
        self.field = [["O"] * size for _ in range(size)]
        self.busy = []
        self.ships = []

    def add_ship(self, ship):
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)
        self.ships.append(ship)
        self.contour(ship)

    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def __str__(self):
        res = ""
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"!{i + 1} | " + " | ".join(row) + " |"
        if self.hid:
            res = res.replace("■", "O")
        return res

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def shot(self, d):
        if self.out(d):
            raise BoardOutException()
        if d in self.busy:
            raise BoardUsedException()
        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print("Корабль уничтожен!")
                    return False
                else:
                    print(f"Корабль ранен!")
                    return True

        self.field[d.x][d.y] = "T"
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy
        self.x_old = 0
        self.y_old = 0

    def ask(self):
        raise NotImplementedError()

    def move(self, repeat_ai):
        while True:
            try:
                target = self.ask(repeat_ai)
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    def ask(self, repeat_ai):
        if repeat_ai:  # Если повторный ход АИ
            while True:  # Тогда повторяем цикл покачто не сделаем ход в пределах ближайшей точки к подбитому кораблю
                near_ai = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                x, y = near_ai[randint(0, 3)]
                x, y = self.x_old + x, self.y_old + y
                if (0 <= x < 6) and (0 <= y < 6):
                    check_simbol = self.enemy.field[x][y]
                    if check_simbol != '.' and check_simbol != 'X' and check_simbol != 'T':
                        d = Dot(x, y)
                        break
        else:
            while True: # Иначе делаем ход в любую клетку где нет знаков "." "X" "T"
                self.x_old, self.y_old = randint(0, 5), randint(0, 5)
                check_simbol = self.enemy.field[self.x_old][self.y_old]
                if check_simbol != '.' and check_simbol != 'X' and check_simbol != 'T':
                    d = Dot(self.x_old, self.y_old)
                    break

        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d


class User(Player):
    def ask(self, repeat_ai):
        while True:
            cords = input("Ваш ход: ").split()
            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue
            x, y = cords
            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue
            x, y = int(x), int(y)
            return Dot(x - 1, y - 1)


g = Game()
g.start()
