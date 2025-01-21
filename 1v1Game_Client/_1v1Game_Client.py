import socket
import threading
import pygame
import sys
import logging
from logging.handlers import RotatingFileHandler

# Logger Settings
logger = logging.getLogger("RotatingLogger")

logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler("app.log", maxBytes = 1000000, backupCount = 3)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# Server Settings
HOST = '127.0.0.1'  
PORT = 21002     

# Game settings
window_width, window_height = 500, 500
bg_color = (30, 30, 30)
circle_radius = 15     
food_radius = 10        

# Create Game
pygame.init()
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Client Game")
clock = pygame.time.Clock()

player1_pos = (100, 50)
player2_pos = (400, 300)
food_pos = (250, 250)
player1_score = 0
player2_score = 0

def send_message(s):
    while True:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            s.sendall(b"UP\n")
            logger.debug("Key pressed: UP")
        if keys[pygame.K_DOWN]:
            s.sendall(b"DOWN\n")
            logger.debug("Key pressed: DOWN")
        if keys[pygame.K_LEFT]:
            s.sendall(b"LEFT\n")
            logger.debug("Key pressed: LEFT")
        if keys[pygame.K_RIGHT]:
            s.sendall(b"RIGHT\n")
            logger.debug("Key pressed: RIGHT")
        pygame.time.delay(50)  # Prevent spamming messages 

def receive_updates(s):
    global player1_pos, player2_pos, food_pos, player1_score, player2_score

    while True:
        try:
            data = s.recv(1024).decode()
            if data:
                # Format: "x1,y1;x2,y2;fx,fy;score1,score2\n"
                parts = data.strip().split(";")
                player1_pos = tuple(map(int, parts[0].split(",")))
                player2_pos = tuple(map(int, parts[1].split(",")))
                food_pos = tuple(map(int, parts[2].split(",")))
                scores = list(map(int, parts[3].split(",")))

                player1_score, player2_score = scores
        except:
            print("Disconnected from server!")
            pygame.quit()
            sys.exit()

def render_game():
    screen.fill(bg_color)
    pygame.draw.circle(screen, (255, 0, 0), player1_pos, circle_radius)  # Player 1
    pygame.draw.circle(screen, (0, 255, 0), player2_pos, circle_radius)  # Player 2
    pygame.draw.circle(screen, (255, 255, 0), food_pos, food_radius)    # Food

    # Display scores
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Player 1: {player1_score} | Player 2: {player2_score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    pygame.display.flip()

def main():
    # Connect to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Connected to server")

        # Start threads for sending and receiving data
        sending_thread = threading.Thread(target = send_message, args = (s,), daemon = True)
        receiving_thread = threading.Thread(target = receive_updates, args = (s,), daemon = True)

        sending_thread.start()
        receiving_thread.start()


        # Pygame event loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            render_game()
            clock.tick(30)  # Limit: 30 FPS

        pygame.quit()

if __name__ == "__main__":
    main()
