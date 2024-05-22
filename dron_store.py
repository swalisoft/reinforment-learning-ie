import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()
font = pygame.font.Font('arial.ttf', 18)

class Direction(Enum):
  RIGHT = 1
  LEFT = 2
  UP = 3
  DOWN = 4
    
Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255)
RED = (200,0,0)
GRAY1 = (63, 63, 63)
GRAY2 = (80, 80, 80)
BROWN = (77, 61, 19)
BLACK = (0,0,0, 0)

BLOCK_SIZE = 20
SPEED = 40

background_image = pygame.image.load('./assets/floor.png')

avatar_image = pygame.image.load('./assets/dron_sm.png')
avatar_rect = avatar_image.get_rect()

product_image = pygame.image.load('./assets/barril.png')
product_rect = product_image.get_rect()

class DronStoreAI:
    
  def __init__(self, w=640, h=480, trained = False):
    self.w = w
    self.h = h

    # init display
    self.display = pygame.display.set_mode((self.w, self.h))
    pygame.display.set_caption('Dron Store')
    self.clock = pygame.time.Clock()

    self.trained = trained

    self.reset()
    
  def reset(self):
    # init game state
    self.direction = Direction.UP
    
    self.by_door = Point(0, self.h-BLOCK_SIZE)

    if self.trained:
      self.head = self.by_door
    else:
      self.head = Point(self.w/2, self.h/2)

    self.snake = [self.head]

    wall_top = Point(BLOCK_SIZE*4, BLOCK_SIZE*4)
    limit = (self.h//BLOCK_SIZE) - 8

    self.wall = [ Point(wall_top.x, wall_top.y+(i*BLOCK_SIZE)) for i in range(limit) ]

    wall_top = Point(BLOCK_SIZE*14, BLOCK_SIZE*4)
    self.wall = self.wall + [ Point(wall_top.x, wall_top.y+(i*BLOCK_SIZE)) for i in range(limit) ]

    wall_top = Point(BLOCK_SIZE*24, BLOCK_SIZE*4)
    self.wall = self.wall + [ Point(wall_top.x, wall_top.y+(i*BLOCK_SIZE)) for i in range(limit) ]

    # wall_top = Point(BLOCK_SIZE*38, BLOCK_SIZE*4)
    # self.wall = self.wall + [ Point(wall_top.x, wall_top.y+(i*BLOCK_SIZE)) for i in range(limit) ]
    
    self.score = 0
    self.food = None

    if self.trained:
      self._place_food()
    else:
      self._place_food_trainer()

    self.frame_iteration = 0

  def _place_food_trainer(self):
    x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
    y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE

    self.food = Point(x, y)

    if self.food in self.wall:
      self._place_food_trainer()

  def _place_food(self, by_door = False):
    if by_door:
      self.food = self.by_door
    else:
      idx = random.randint(0, len(self.wall) - 1)

      if random.randint(0, 1):
        position = -BLOCK_SIZE
      else:
        position = BLOCK_SIZE
        
      target = self.wall[idx]

      self.food = Point(target.x-position, target.y)
      
  def play_step(self, action):
    self.frame_iteration += 1

    # 1. collect user input
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        quit()
    
    # 2. move
    self._move(action) # update the head
    self.snake.insert(0, self.head)
    
    # 3. check if game over
    reward = 0
    game_over = False

    if self.is_collision() or self.frame_iteration > 100 * (self.score+1):
      game_over = True
      reward = -10
      return reward, game_over, self.score
        
    if self.score > 100:
      game_over = True
      reward = 10

      return reward, game_over, self.score

    # 4. place new food or just move
    if self.head == self.food:
      self.score += 1
      reward = 10

      if self.trained:
        self._place_food(self.food != self.by_door)
      else:
        self._place_food_trainer()

    self.snake.pop()

    # 5. update ui and clock
    self._update_ui()
    self.clock.tick(SPEED)
    # 6. return game over and score
    return reward, game_over, self.score

  def danger_row(self, x=None):
    for el in self.wall:
      if el.x == x:
        return True
    
    return False
  
  def is_collision(self, pt=None):
    if pt is None:
      pt = self.head

    # hits boundary
    if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
      return True

    # hits with wall
    # if self.head in self.wall:
    #   return True
    
    return False
      
  def _update_ui(self):
    self.display.blit(background_image, (0, 0))
    # self.display.fill(BLACK)
    
    for pt in self.wall:
      pygame.draw.rect(self.display, GRAY1, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
      pygame.draw.rect(self.display, GRAY2, pygame.Rect(pt.x+4, pt.y+4, 12, 12))

    if self.food == self.by_door:
      pygame.draw.rect(self.display, BROWN, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))
    else:
      product_rect.center = (self.food.x + 10, self.food.y + 10)
      self.display.blit(product_image, product_rect)

    for pt in self.snake:
      avatar_rect.center = (pt.x + 10, pt.y + 10)
      self.display.blit(avatar_image, avatar_rect)
    
    if not self.trained:
      text = font.render("Found items: " + str(self.score), True, WHITE)

      self.display.blit(text, [0, 0])

    pygame.display.flip()
      
  def _move(self, action):
    # [straight, right, left]

    clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
    idx = clock_wise.index(self.direction)

    if np.array_equal(action, [1, 0, 0]):
      new_dir = clock_wise[idx]  # no change
    elif np.array_equal(action, [0, 1, 0]):
      next_idx = (idx + 1) % 4
      new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u
    else:  # [0, 0, 1]
      next_idx = (idx - 1) % 4
      new_dir = clock_wise[next_idx]  # left turn r -> u -> l -> d

    self.direction = new_dir

    x = self.head.x
    y = self.head.y

    if self.direction == Direction.RIGHT:
      x += BLOCK_SIZE
    elif self.direction == Direction.LEFT:
      x -= BLOCK_SIZE
    elif self.direction == Direction.DOWN:
      y += BLOCK_SIZE
    elif self.direction == Direction.UP:
      y -= BLOCK_SIZE

    self.head = Point(x, y)
            