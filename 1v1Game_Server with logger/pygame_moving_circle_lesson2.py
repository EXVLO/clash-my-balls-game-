import pygame
import sys
import math
import threading
import socket
import random
import logging
from logging.handlers import RotatingFileHandler

# Logger Settings
logger = logging.getLogger("RotatingLogger")

logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler("app.log", maxBytes = 1000000, backupCount = 6)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# Client (Player)
class Client:
    def __init__(self, connected_socket, addr):
        self.connected_socket = connected_socket
        self.addr = addr

# Player Object
class Circle:
    def __init__(self, radius, x, y, vx, vy, changeVX, changeVY, color, max_vx, max_vy, name):
        self.radius = radius
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.changeVX = changeVX
        self.changeVY = changeVY
        self.color = color
        self.max_vx = max_vx
        self.max_vy = max_vy
        self.score = 0
        self.name = name

    def move(self, window_width, window_height):
        self.x += self.vx
        self.y += self.vy

        # Bounce off walls
        if self.x - self.radius < 0 or self.x + self.radius > window_width:
            self.vx *= -1
            self.x = max(self.radius, min(self.x, window_width - self.radius))
        if self.y - self.radius < 0 or self.y + self.radius > window_height:
            self.vy *= -1
            self.y = max(self.radius, min(self.y, window_height - self.radius))

    # Keyboard Movements
    def key_up(self):
        self.vy = max(-self.max_vy, self.vy - self.changeVY)

    def key_down(self):
        self.vy = min(self.max_vy, self.vy + self.changeVY)

    def key_left(self):
        self.vx = max(-self.max_vx, self.vx - self.changeVX)

    def key_right(self):
        self.vx = min(self.max_vx, self.vx + self.changeVX)

# Food Object
class Food:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color

    def respawn(self, window_width, window_height):
        self.x = random.randint(self.radius, window_width - self.radius)
        self.y = random.randint(self.radius, window_height - self.radius)

# Collision detection
def check_collision(player1, player2):
    dx = player1.x - player2.x
    dy = player1.y - player2.y
    distance = math.sqrt(dx**2 + dy**2)

    if distance < player1.radius + player2.radius:
        # Swap velocities
        player1.vx, player2.vx = player2.vx, player1.vx
        player1.vy, player2.vy = player2.vy, player1.vy

# Check if a player eats the food
def check_food_collision(player, food):
    dx = player.x - food.x
    dy = player.y - food.y
    distance = math.sqrt(dx**2 + dy**2)
    return distance < player.radius + food.radius

# Client handler function
def client_online(curr_client, player):
    with curr_client.connected_socket as conn:
        print(f"Client connected: {curr_client.addr}")
        while True:
            try:
                message_received = conn.recv(32).decode().strip()
                if message_received == "UP":
                    player.key_up()
                    logger.debug(f"{player.name} pressed key: UP")
                elif message_received == "DOWN":
                    player.key_down()
                    logger.debug(f"{player.name} pressed key: DOWN")
                elif message_received == "LEFT":
                    player.key_left()
                    logger.debug(f"{player.name} pressed key: LEFT")
                elif message_received == "RIGHT":
                    player.key_right()
                    logger.debug(f"{player.name} pressed key: RIGHT")
            except:
                print(f"Client {curr_client.addr} disconnected")
                break

# Broadcast positions to all clients
def broadcast_positions():
    while running:
        positions = f"{player1.x},{player1.y};{player2.x},{player2.y};{food.x},{food.y};{player1.score},{player2.score}\n"
        for client in client_list:
            try:
                client.connected_socket.sendall(positions.encode())
            except:
                print(f"Client {client.addr} disconnected")
                client_list.remove(client)
        pygame.time.delay(30) 


#-----# Settings #-----#


# Game Settings (Pygame)
pygame.init()
window_width, window_height = 500, 500
bg_color = (30, 30, 30)  
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Server Game")
clock = pygame.time.Clock()

# Game objects
player1 = Circle(15, 100, 50, 0, 0, 2, 2, (255, 0, 0), 12, 12, "Player 1")
player2 = Circle(15, 400, 300, 0, 0, 2, 2, (0, 255, 0), 12, 12, "Player 2")
food = Food(random.randint(15, window_width - 15), random.randint(15, window_height - 15), 10, (255, 255, 0))

# Server settings
HOST = '0.0.0.0'
PORT = 21002
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(2)
print("Server is running... Waiting for clients.")

client_list = []
running = True

#-----# Main Thread #-----#


# Accept clients
for i in range(2):
    conn, addr = s.accept()
    client = Client(conn, addr)
    client_list.append(client)

    # Clients Thread - (Get Key information from Clients all time)
    client_thread = threading.Thread(target = client_online, args = (client, player1 if i == 0 else player2), daemon = True)
    client_thread.start()

# Position_broadcast Thread - (Send positions to Clients all time)
broadcast = threading.Thread(target = broadcast_positions, daemon = True)
broadcast.start()

# Main Thread - (update player positions and check food collisions all time)
try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update game state
        player1.move(window_width, window_height)
        player2.move(window_width, window_height)
        check_collision(player1, player2)

        # Check food collisions
        if check_food_collision(player1, food):
            player1.score += 1
            food.respawn(window_width, window_height)
        elif check_food_collision(player2, food):
            player2.score += 1
            food.respawn(window_width, window_height)

        # Render game on the server screen
        screen.fill(bg_color)
        pygame.draw.circle(screen, player1.color, (player1.x, player1.y), player1.radius)
        pygame.draw.circle(screen, player2.color, (player2.x, player2.y), player2.radius)
        pygame.draw.circle(screen, food.color, (food.x, food.y), food.radius)
        pygame.display.flip()

        clock.tick(30)  # Limit: 30 FPS

except KeyboardInterrupt:
    print("Shutting down server...")

finally:
    s.close()
    pygame.quit()
    sys.exit()


# Wait for Clients - Listen(2)
# Clients Thread - (Get Key information from Clients all time)
# Position_broadcast Thread - (Send positions to Clients all time)
# Main Thread - (update player positions and check food collisions all time)
# FPS = 30
# Shut Down Server