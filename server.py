from socket import *
import threading as td


class TTT:

    def __init__(self):
        self.player1 = None
        self.player2 = None
        self.x = -1
        self.y = -1
        self.turn = 0
        self.end = False
        self.gameBoard = [[0 for i in range(3)] for i in range(3)] # 0 빈 칸 1 O, 2 X

    def start(self, p1, p2):
        self.__init__()
        self.setPlayer(p1, p2)
        self.player1.conn.send('your turn'.encode())
        self.player2.conn.send('opponent\'s turn'.encode())
        self.turn = 0

    def setPlayer(self, p1, p2):
        self.player1 = p1
        self.player2 = p2

    def setPos(self, x, y, player):
        if player == self.player1 and self.turn == 0:
            if self.isValidPos(x, y):
                self.gameBoard[y][x] = 1
                self.turn = 1
                print(f'player1 set {y},{x}')
                self.player1.conn.send('opponent\'s turn'.encode())
                self.player2.conn.send('your turn'.encode())
                self.player1.conn.send(' '.join([''.join(map(str, row)) for row in self.gameBoard]).encode())
                self.player2.conn.send(' '.join([''.join(map(str, row)) for row in self.gameBoard]).encode())
            else:
                self.player1.conn.send('invalid pos'.encode())
        elif player == self.player2 and self.turn == 1:
            if self.isValidPos(x, y):
                self.gameBoard[y][x] = 2
                self.turn = 0
                print(f'player2 set {y},{x}')
                self.player1.conn.send('your turn'.encode())
                self.player2.conn.send('opponent\'s turn'.encode())
                self.player1.conn.send(' '.join([''.join(map(str, row)) for row in self.gameBoard]).encode())
                self.player2.conn.send(' '.join([''.join(map(str, row)) for row in self.gameBoard]).encode())
            else:
                self.player2.conn.send('invalid pos'.encode())
        end = self.isEnd()
        if end == 'player1':
            self.player1.conn.send('you win'.encode())
            self.player2.conn.send('you lose'.encode())
            self.stop()
        elif end == 'player2':
            self.player1.conn.send('you lose'.encode())
            self.player2.conn.send('you win'.encode())
            self.stop()
        elif end == 'unknown':
            pass
        elif end == 'draw':
            self.player1.conn.send('draw'.encode())
            self.player2.conn.send('draw'.encode())
            self.stop()

    def stop(self):
        self.end = True

    def isEnd(self):
        winner = 'unknown'

        # player1 win state
        if [1, 1, 1] in [row for row in self.gameBoard]:
            winner = 'player1'
        if [1, 1, 1] in [[self.gameBoard[j][i] for j in range(3)] for i in range(3)]:
            winner = 'player1'
        if [1, 1, 1] == [self.gameBoard[i][i] for i in range(3)]:
            winner = 'player1'
        if [1, 1, 1] == [self.gameBoard[2-i][i] for i in range(3)]:
            winner = 'player1'

        # player2 win state
        if [2, 2, 2] in [row for row in self.gameBoard]:
            winner = 'player2'
        if [2, 2, 2] in [[self.gameBoard[j][i] for j in range(3)] for i in range(3)]:
            winner = 'player2'
        if [2, 2, 2] == [self.gameBoard[i][i] for i in range(3)]:
            winner = 'player2'
        if [2, 2, 2] == [self.gameBoard[2-i][i] for i in range(3)]:
            winner = 'player2'

        # draw state
        print()
        if sum([row.count(0) for row in self.gameBoard]) == 0 and winner == 'unknown':
            winner = 'draw'

        return winner

    def isValidPos(self, x, y):
        if self.gameBoard[y][x] == 0:
            return True
        return False


class Chat:

    def __init__(self):
        pass

    def echo(self, msg, p, p1, p2):
        if p == p1:
            p1.conn.send(f'chat:me:{msg}'.encode())
            if p2 is not None:
                p2.conn.send(f'chat:opponent:{msg}'.encode())
        else:
            if p1 is not None:
                p1.conn.send(f'chat:opponent:{msg}'.encode())
            p2.conn.send(f'chat:me:{msg}'.encode())




class Client(td.Thread):

    def __init__(self, conn, addr):
        super().__init__()
        self.conn = conn
        self.addr = addr

    def run(self):
        global server
        try:
            while True:
                msg = self.conn.recv(2048).decode()
                if 'chat' in msg:
                    if server.game.player1 is not None and server.game.player2 is not None:
                        server.chat.echo(msg.split(':')[1], self, server.game.player1, server.game.player2)
                else:
                    x, y = map(int, msg.split(','))
                    server.game.setPos(x, y, self)
                if server.game.end:
                    break
        finally:
            server.clientList.remove(self)
            self.conn.close()


class Server:

    def __init__(self):

        self.clientList = []
        self.game = TTT()
        self.chat = Chat()
        self.serverPort = 12000

        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind(('', self.serverPort))
        self.socket.listen(2)

        print('server init')
        self.isRun = True
        print('server run')

    def run(self):
        conn, addr = self.socket.accept()
        print(f'accept from conn:{conn}, addr:{addr}')
        client = Client(conn, addr)
        client.start()
        self.clientList.append(client)

        if len(self.clientList) == 2:
            self.game.start(self.clientList[0], self.clientList[1])
            self.clientList = []


if __name__ == '__main__':
    server = Server()
    while server.isRun:
        server.run()