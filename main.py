import sys
import time
import pygame
from pygame import mixer
from pygame.locals import *
import os
import random
pygame.font.init()
pygame.mixer.init()


WIDTH, HEIGHT = 1000, 1000
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invasion")

# Load images
RED_SPACE_SHIP = pygame.image.load("assets/S_red.png")
PURPLE_SPACE_SHIP = pygame.image.load("assets/S_purple.png")
BLUE_SPACE_SHIP = pygame.image.load("assets/S_blue.png")
# Player player
PLAYER_SPACE_SHIP = pygame.image.load("assets/S_player.png")
#scaling images
DEFAULT_IMAGE_SIZE = (80, 80)
RED_SPACE_SHIP = pygame.transform.scale(RED_SPACE_SHIP, DEFAULT_IMAGE_SIZE)
PURPLE_SPACE_SHIP = pygame.transform.scale(PURPLE_SPACE_SHIP, DEFAULT_IMAGE_SIZE)
BLUE_SPACE_SHIP = pygame.transform.scale(BLUE_SPACE_SHIP, DEFAULT_IMAGE_SIZE)
PLAYER_SPACE_SHIP = pygame.transform.scale(PLAYER_SPACE_SHIP, DEFAULT_IMAGE_SIZE)


# Lasers
RED_LASER = pygame.transform.scale(pygame.image.load('assets/L_red.png'),(10,50))
PURPLE_LASER = pygame.transform.scale(pygame.image.load('assets/L_purple.png'),(10,50))
BLUE_LASER = pygame.transform.scale(pygame.image.load('assets/L_blue.png'),(10,50))
PLAYER_LASER = pygame.transform.scale(pygame.image.load('assets/L_green.png'),(10,70))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "invaders.png")), (WIDTH, HEIGHT))

#level Background music
mixer.music.load('assets/theme.wav')
mixer.music.play(-1)


#joystick support
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                enemyl_sound = mixer.Sound('assets/pew.wav')
                enemyl_sound.play()
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser_sound = mixer.Sound('assets/shoot.wav')
            laser_sound.play()
            laser = Laser(self.x + 36, self.y - 35, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SPACE_SHIP
        self.laser_img = PLAYER_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        collision_sound = mixer.Sound('assets/invaderkilled.wav')
                        collision_sound.play()
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 5))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 5))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (PURPLE_SPACE_SHIP, PURPLE_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 36, self.y + 45, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def main():

    run = True
    FPS = 60
    level = 0
    lives = 10
    main_font = pygame.font.SysFont("comicsans", 50)
    lost_font = pygame.font.SysFont("comicsans", 60)

    enemies = []
    wave_length = 4
    enemy_vel = 1

    player_vel = 5
    laser_vel = 5

    player = Player(300, 630)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BG, (0,0))
        # draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))

        WIN.blit(level_label, (10, 10))
        WIN.blit(lives_label, (WIDTH - level_label.get_width() - 20, 10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        pygame.display.update()

    motion = [0,0]
    while run:
        clock.tick(FPS)
        redraw_window()
        if player.health <= 0:
            dead_sound = mixer.Sound('assets/explode.wav')
            dead_sound.play()
            lives -= 2
            player.health = 100

        if lives <= 0 :
            lost = True
            lost_count += 1

        if lost:
            lost_sound = mixer.Sound('assets/explosion.wav')
            lost_sound.play()
            if lost_count > FPS * 2:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        #JOYSTICK CONTROL
        #if player.x > 0 and player.x + player.get_width() < WIDTH and player.y - player_vel > 0 and player.y + player.get_height() + 15 < HEIGHT:
        if abs(motion[0]) < 0.1:
            motion[0] = 0
        if abs(motion[1]) < 0.1:
            motion[1] = 0
        player.x += int(motion[0]) * 10
        player.y += int(motion[1]) * 10
        for event in pygame.event.get():
            if event.type == QUIT:
                quit()
            if event.type == JOYBUTTONDOWN:
                if event.button == 0 or event.button == 5:
                    player.shoot()
                if event.button == 6:
                    run = False
            if event.type == JOYAXISMOTION:
                motion[event.axis] = event.value


        # KEYBOARD CONTROL
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            quit()
            sys.exit()
        if keys[pygame.K_LEFT] and player.x - player_vel > 0: # left
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH: # right
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0: # up
            player.y -= player_vel
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() + 15 < HEIGHT: # down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 2*60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies)
    # mixer.music.stop()
def main_menu():
    title_font = pygame.font.SysFont("comicsans", 70)
    run = True

    while run:

        WIN.blit(BG, (0,0))
        game_label = title_font.render("SPACE INVASION",1, (random.randint(1,255),random.randint(1,255),random.randint(1,255)))
        WIN.blit(game_label,(WIDTH/2 - game_label.get_width()/2, 100))
        line1_label = title_font.render("Press ENTER to start", 1, (255,255,255))
        WIN.blit(line1_label, (WIDTH/2 - line1_label.get_width()/2, 350))
        line2_label = title_font.render("Press ESCAPE to exit", 1, (255, 255, 255))
        WIN.blit(line2_label, (WIDTH / 2 - line2_label.get_width() / 2, 400))
        line3_label = title_font.render("CONTROLS", 1, (255,255,255))
        WIN.blit(line3_label, (WIDTH/2 - line3_label.get_width()/2, 500))
        line4_label = title_font.render("ARROW KEYS -- MOVEMENT", 1, (255, 255, 255))
        WIN.blit(line4_label, (WIDTH / 2 - line4_label.get_width() / 2, 550))
        line5_label = title_font.render("SPACE BAR -- SHOOT", 1, (255, 255, 255))
        WIN.blit(line5_label, (WIDTH / 2 - line5_label.get_width() / 2, 600))
        pygame.display.update()
        time.sleep(.1)
        for event in pygame.event.get():
            k1 = pygame.key.get_pressed()
            if k1[pygame.K_ESCAPE]:
                quit()
                sys.exit()
            if event.type == QUIT:
                run = False
            if k1[pygame.K_RETURN]:
                main()
            if event.type == JOYBUTTONDOWN:
                if event.button == 7:
                    main()
    pygame.quit()


main_menu()