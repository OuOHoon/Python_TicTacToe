import pygame
import socket as sc
import threading as td


pygame.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 255)
BACKGROUND_COLOR = (20, 189, 172)
LINE_COLOR = (13, 161, 146)
X_COLOR = (84, 84, 84)
O_COLOR = (242, 235, 211)
STATE_IDLE, STATE_PLAY, STATE_END = 0, 1, 2

COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
FONT = pygame.font.Font(None, 32)


def translateClickPos(x, y):
    result = [0, 0]
    for i in range(3):
        if 160*i < x <= 160*(i + 1):
            result[0] = i
        if 160*i < y <= 160*(i + 1):
            result[1] = i
    return result


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_ACTIVE
        self.text = text
        self.font = FONT
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event, socket):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    socket.send(f'chat:{self.text}'.encode())
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)


class ChatBox:

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 18)
        self.chatList = []

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_ACTIVE, self.rect, 2)
        for i in range(len(self.chatList)):
            txtSurface = self.font.render(self.chatList[i], True, X_COLOR)
            screen.blit(txtSurface, (self.rect.x+5, self.rect.y+5+(self.rect.height//9)*i))

    def appendChat(self, chat):
        c = ':'.join(chat)
        if len(self.chatList) < 10:
            self.chatList.append(c)
        else:
            self.chatList = self.chatList[1:]
            self.chatList.append(c)


class Client:

    def __init__(self):


        self.screen = pygame.display.set_mode((720, 480))
        pygame.display.set_caption('TTT Client')

        self.screen.fill(BACKGROUND_COLOR)
        pygame.display.flip()

        self.state = STATE_IDLE
        self.turn = False
        self.winState = 0
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.font = pygame.font.Font('freesansbold.ttf', 24)
        self.isRun = True
        self.inputBox = InputBox(500, 400, 140, 32)
        self.chatBox = ChatBox(500, 100, 200, 290)

        self.gameBoard = [[0 for i in range(3)] for i in range(3)] # 0 빈 칸 1 O, 2 X

        self.serverName = '1.228.10.3' # '192.168.1.2'
        self.serverPort = 12000
        self.socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
        self.socket.connect((self.serverName, self.serverPort))
        t = td.Thread(target=self.recvMessage)
        t.setDaemon(True)
        t.start()
        print('connect server')

        print('client init')

    def update(self):
        self.clock.tick(self.FPS)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.isRun = False
            elif self.state == STATE_PLAY and self.turn:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # left button click
                        x, y = event.pos
                        if self.isValidClick(x, y):
                            tx, ty = translateClickPos(x, y)
                            print(f'click{ty},{tx}')
                            self.socket.send(f'{tx},{ty}'.encode())
            self.inputBox.handle_event(event, self.socket)
        self.inputBox.update()

    def render(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.drawBoard()
        self.drawState()
        self.inputBox.draw(self.screen)
        self.chatBox.draw(self.screen)
        pygame.display.update()

    def release(self):
        self.socket.close()

    def run(self):
        self.update()
        self.render()

    def drawBoard(self):
        for i in range(4):
            pygame.draw.line(self.screen, LINE_COLOR, (160 * i, 0), (160 * i, 480), 10)
            pygame.draw.line(self.screen, LINE_COLOR, (0, 160 * i), (480, 160 * i), 10)
        for i in range(3):
            for j in range(3):
                if self.gameBoard[i][j] == 1:
                    pygame.draw.ellipse(self.screen, O_COLOR, (160 * j + 50, 160 * i + 50, 160 - 100, 160 - 100), 10)
                elif self.gameBoard[i][j] == 2:
                    pygame.draw.line(self.screen, X_COLOR, (160 * j + 50, 160 * i + 50), (160 * (j + 1) - 50, 160 * (i + 1) - 50), 15)
                    pygame.draw.line(self.screen, X_COLOR, (160 * j + 50, 160 * (i + 1) - 50), (160 * (j + 1) - 50, 160 * i + 50), 15)

    def drawState(self):
        if self.state == STATE_IDLE:
            text = self.font.render('Wait opponent', True, X_COLOR, BACKGROUND_COLOR)
        elif self.state == STATE_PLAY:
            text = self.font.render('My turn' if self.turn else 'Opponent\'s turn', True, X_COLOR, BACKGROUND_COLOR)
        elif self.state == STATE_END:
            text = self.font.render('You Win' if self.winState == 1 else 'You Lose' if self.winState == 2 else 'Draw', True, X_COLOR, BACKGROUND_COLOR)
        self.screen.blit(text, (500, 70))

    def isValidClick(self, x, y):
        if 0 < x < 480 and 0 < y < 480:
            tx, ty = translateClickPos(x, y)
            if self.gameBoard[ty][tx] == 0:
                return True
        return False

    def recvMessage(self):
        while True:
            msg = self.socket.recv(2048).decode()
            if msg == 'your turn':
                self.state = STATE_PLAY
                self.turn = True
            elif msg == 'opponent\'s turn':
                self.state = STATE_PLAY
                self.turn = False
            elif msg == 'invalid pos':
                print('invalid pos')
            elif 'you win' in msg:
                self.state = STATE_END
                self.winState = 1
                board = msg[:msg.index('you win')].split()
                for i in range(3):
                    for j in range(3):
                        self.gameBoard[i][j] = int(board[i][j])
                print(self.gameBoard)
                # self.isRun = False
            elif 'you lose' in msg:
                self.state = STATE_END
                self.winState = 2
                board = msg[:msg.index('you lose')].split()
                for i in range(3):
                    for j in range(3):
                        self.gameBoard[i][j] = int(board[i][j])
                print(self.gameBoard)
                # self.isRun = False
            elif 'draw' in msg:
                self.state = STATE_END
                self.winState = 0
                board = msg[:msg.index('draw')].split()
                for i in range(3):
                    for j in range(3):
                        self.gameBoard[i][j] = int(board[i][j])
                print(self.gameBoard)
                # self.isRun = False
            elif 'chat' in msg:
                chat = msg.split(':')[1:]
                self.chatBox.appendChat(chat)
            else:
                board = msg.split()
                for i in range(3):
                    for j in range(3):
                        self.gameBoard[i][j] = int(board[i][j])
                print(self.gameBoard)
            print(msg)


if __name__ == '__main__':
    client = Client()
    while client.isRun:
        client.run()
    client.release()