import cv2
import mediapipe as mp
import pygame
import sys

# Initialize MediaPipe Hand
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Initialize Pygame
pygame.init()

# Game Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BALL_RADIUS = 10
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SPEED_X, BALL_SPEED_Y = 5, 5
FPS = 60

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture-Controlled Pong")
clock = pygame.time.Clock()

# Define Ball and Paddle
class Ball:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = BALL_RADIUS
        self.speed_x = BALL_SPEED_X
        self.speed_y = BALL_SPEED_Y

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y

        # Collision with top and bottom
        if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
            self.speed_y *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (self.x, self.y), self.radius)

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed_x *= -1
        self.speed_y = BALL_SPEED_Y if self.speed_y > 0 else -BALL_SPEED_Y

class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.speed = 7

    def move(self, y):
        self.y = y
        # Ensure paddle stays on screen
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > HEIGHT:
            self.y = HEIGHT - self.height

    def auto_move(self, ball_y):
        # Simple AI to follow the ball
        if self.y + self.height / 2 < ball_y:
            self.y += self.speed
        elif self.y + self.height / 2 > ball_y:
            self.y -= self.speed
        # Ensure paddle stays on screen
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > HEIGHT:
            self.y = HEIGHT - self.height

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height))

# Initialize Game Objects
ball = Ball()
player_paddle = Paddle(WIDTH - 20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
ai_paddle = Paddle(10, HEIGHT // 2 - PADDLE_HEIGHT // 2)

# Initialize Webcam
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
) as hands:

    running = True
    player_score = 0
    ai_score = 0

    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Flip the frame horizontally for natural (mirror-like) interaction
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = hands.process(frame_rgb)

        # Default paddle position
        paddle_y = player_paddle.y

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get the y-coordinate of the wrist (landmark 0)
                wrist = hand_landmarks.landmark[0]
                # Convert normalized coordinates to Pygame coordinates
                paddle_y = int(wrist.y * HEIGHT) - PADDLE_HEIGHT // 2
                # Update player's paddle position
                player_paddle.move(paddle_y)
                # Draw hand landmarks on the frame (optional)
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Update AI paddle
        ai_paddle.auto_move(ball.y)

        # Move the ball
        ball.move()

        # Collision with paddles
        if (ball.x + ball.radius >= player_paddle.x and
            player_paddle.y < ball.y < player_paddle.y + player_paddle.height):
            ball.speed_x *= -1

        if (ball.x - ball.radius <= ai_paddle.x + ai_paddle.width and
            ai_paddle.y < ball.y < ai_paddle.y + ai_paddle.height):
            ball.speed_x *= -1

        # Check for scoring
        if ball.x < 0:
            player_score += 1
            ball.reset()
        elif ball.x > WIDTH:
            ai_score += 1
            ball.reset()

        # Draw everything
        screen.fill(BLACK)
        ball.draw(screen)
        player_paddle.draw(screen)
        ai_paddle.draw(screen)

        # Display Scores
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Player: {player_score}  AI: {ai_score}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))

        pygame.display.flip()
        clock.tick(FPS)

        # Optional: Display the webcam feed with landmarks
        cv2.imshow('Gesture-Controlled Pong - Webcam Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

# Clean up
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
