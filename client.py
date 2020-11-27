######################################
# Author: Tyler Gassan
######################################
import os
import random
import socket
import subprocess
import threading
import time
import math
from store import *
import pygame
from pygame.math import Vector2
from pygame.rect import *

from config import *
from levels import *
from network import Network

# initialize pygame ##############################################################################################
pygame.init()

# SET WINDOW ##############################################################################################
window = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('Flank Tank')

# Sprite groups ##############################################################################################
all_sprites_list = pygame.sprite.Group()
bullet_list = pygame.sprite.Group()
enemy_bullet_list = pygame.sprite.Group()
players_list = pygame.sprite.Group()
walls = pygame.sprite.Group()
lasers = pygame.sprite.Group()
shields = pygame.sprite.Group()
pickups = pygame.sprite.Group()
enemies = pygame.sprite.Group()
BACKGROUND = pygame.image.load(BACKGROUND).convert()

players = []  # play object list
particles = []
# Explosion Image Initializing ##############################################################################################
explosion_anim = {'lg': [], 'sm': []}
for i in range(9):
    filename = 'sprites/explosions/regularExplosion0{}.png'.format(i)
    img = pygame.image.load(filename).convert()
    img.set_colorkey(black)
    img_lg = pygame.transform.scale(img, (200, 200))
    explosion_anim['lg'].append(img_lg)
    img_sm = pygame.transform.scale(img, (75, 75))
    explosion_anim['sm'].append(img_sm)

# Bounce image initializing ##############################################################################################
bounce_anim = {'lg': [], 'sm': []}
for i in range(2):
    filename = 'sprites/bounce/bounce0{}.png'.format(i)
    img = pygame.image.load(filename).convert()
    img.set_colorkey(black)
    img_lg = pygame.transform.scale(img, (150, 150))
    bounce_anim['lg'].append(img_lg)
    img_sm = pygame.transform.scale(img, (50, 50))
    bounce_anim['sm'].append(img_sm)

# Shield item initializing ##############################################################################################
shield_anim = {'lg': [], 'sm': []}
for i in range(14):
    filename = 'sprites/shield/shield_item{}.png'.format(i)
    img = pygame.image.load(filename).convert()
    img.set_colorkey(black)
    img_lg = pygame.transform.scale(img, (150, 150))
    shield_anim['lg'].append(img_lg)
    img_sm = pygame.transform.scale(img, (75, 75))
    shield_anim['sm'].append(img_sm)


# Player creation class ##############################################################################################
class Tank(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(PLAYER).convert_alpha()
        self.rect = self.image.get_rect()
        self.health = 100
        self.health_bar = ProgressBar(self.health, self.health, (100, 10), green, gray, [self.rect.x,
                                                                                         self.rect.y - 15])  # max_bar, progress, size, barColor, borderColor, position
        self.turret = Turret(self, pygame.mouse.get_pos(), 1)
        self.rotate = 0
        players_list.add(self)
        all_sprites_list.add(self)
        players.append(self)

    def move(self):
        key = pygame.key.get_pressed()
        wall_hit = pygame.sprite.spritecollide(self, walls, False)
        if key[pygame.K_LSHIFT]:
            move_speed = 2
        else:
            move_speed = 1
        if (key[pygame.K_a] and not (key[pygame.K_w] or key[pygame.K_s])) and self.rect.x > 0:
            if wall_hit:
                self.rect.x += 2
            self.rect.move_ip(move_speed * -1, 0)
            self.rotate = 2
        elif (key[pygame.K_d] and not (key[pygame.K_w] or key[pygame.K_s])) and self.rect.x < 1845:
            if wall_hit:
                self.rect.x -= 2
            self.rect.move_ip(move_speed, 0)
            self.rotate = 3
        if key[pygame.K_w] and self.rect.y > 0:
            if wall_hit:
                self.rect.y += 2
            self.rect.move_ip(0, move_speed * -1)
            self.rotate = 0
        elif key[pygame.K_s] and self.rect.y < 988:
            if wall_hit:
                self.rect.y -= 2
            self.rect.move_ip(0, move_speed)
            self.rotate = 1
        png = 'tank{img}.png'.format(img=str(self.rotate))
        PLAYER = os.path.join('sprites', 'tank', png)
        self.image = pygame.image.load(PLAYER).convert_alpha()

    def draw(self):
        window.blit(self.image, self.rect)

    def damage(self, x):
        if not god:
            if self.health > 0:
                self.health_bar.progress -= x
                self.health -= x

    def addHealth(self, x):
        self.health_bar.progress += x
        self.health += x

    def update(self):
        self.health_bar.update([self.rect.x, self.rect.y - 15])
        self.turret.updateTurret(pygame.mouse.get_pos())
        self.move()


# Creates an ally to play alongside player (used for coop) ##############################################################################################
class Ally(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(ALLY).convert_alpha()
        self.rect = self.image.get_rect()
        self.target = [0, 0]
        self.health = 100
        self.health_bar = ProgressBar(self.health, self.health, (100, 10), green, gray, [self.rect.x,
                                                                                         self.rect.y - 15])  # max_bar, progress, size, barColor, borderColor, position
        self.turret = Turret(self, pygame.mouse.get_pos(), 1)
        self.rotate = 0
        players_list.add(self)
        all_sprites_list.add(self)
        players.append(self)

    def move(self):
        png = 'tankAlly{img}.png'.format(img=str(self.rotate))
        ALLY = os.path.join('sprites', 'tank', png)
        self.image = pygame.image.load(ALLY).convert_alpha()

    def draw(self):
        window.blit(self.image, self.rect)

    def damage(self, x):
        if not god:
            if self.health > 0:
                self.health_bar.progress -= x
                self.health -= x

    def addHealth(self, x):
        self.health_bar.progress += x
        self.health += x

    def updateMouse(self, mousepos):
        self.target = mousepos

    def update(self):
        self.health_bar.update([self.rect.x, self.rect.y - 15])
        self.turret.updateTurret(self.target)
        self.move()


# Enemy creation class ##############################################################################################
class Enemy(pygame.sprite.Sprite):

    def __init__(self, speed, health, strength):
        super().__init__()
        self.color = red
        self.colorb = gray
        if strength == 0:
            strength = ENEMY
        elif strength == 1:
            self.color = purple
            strength = ENEMY2
        elif strength == 2:
            self.color = yellow
            strength = ENEMY3
        self.image = pygame.image.load(strength).convert_alpha()
        self.rect = self.image.get_rect()
        self.speed = speed
        self.health = health
        self.turretEnemy = Turret(self, [player.rect.centerx, player.rect.centery], 0)
        self.health_bar = ProgressBar(self.health, self.health, (100, 10), self.color, self.colorb,
                                      [self.rect.x, self.rect.y - 15])
        all_sprites_list.add(self)
        enemies.add(self)

    def shoot(self):
        self.turretEnemy.shoot()

    def draw(self):
        self.turretEnemy.draw()

    def moveRight(self, pixels):
        self.rect.x += pixels

    def moveLeft(self, pixels):
        self.rect.x -= pixels

    def moveForward(self, speed):
        self.rect.y += self.speed * speed / 20

    def moveBackward(self, speed):
        self.rect.y -= self.speed * speed / 20

    def changeSpeed(self, speed):
        self.speed = speed

    def damage(self, x):
        self.health_bar.power -= x
        self.health -= x

    def addHealth(self, x):
        self.health_bar.power += x
        self.health += x

    def update(self):
        try:
            self.health_bar.update([self.rect.x, self.rect.y - 15])
            self.turretEnemy.draw()
            targetPlayer = player
            shorter = 999999
            for p in players:
                x = abs(p.rect.centerx - self.rect.centerx)
                y = abs(p.rect.centery - self.rect.centery)
                if (x + y) < shorter:
                    shorter = x + y
                    targetPlayer = p
            self.turretEnemy.updateTurret([targetPlayer.rect.centerx, targetPlayer.rect.centery])
        except Exception as e:
            print("Enemy update error:", e)


# Turret laser class ##############################################################################################
class Laser(pygame.sprite.Sprite):

    def __init__(self, pos, target):
        super().__init__()
        self.target = target
        self.pos = pos
        self.laser = pygame.draw.line(window, red, self.pos, self.target, 0)
        lasers.add(self)

    def draw(self, pos, target):
        self.target = target
        self.pos = pos
        self.laser = pygame.draw.line(window, red, self.pos, self.target, 0)


class Turret(pygame.sprite.Sprite):

    def __init__(self, base, target, player):
        self.player = player
        self.base = base
        self.target = target
        self.original_barrel = pygame.image.load(TURRET).convert_alpha()
        self.barrel = self.original_barrel.copy()
        self.rect = self.barrel.get_rect(center=base.rect.center)
        self.angle = self.get_angle(target)
        if player != 1:
            self.enemy_laser = Laser(self.rect.center, self.target)

    def get_angle(self, mouse):
        offset = (mouse[1] - self.rect.centery, mouse[0] - self.rect.centerx)
        self.angle = 270 - math.degrees(math.atan2(*offset))
        self.barrel = pygame.transform.rotozoom(self.original_barrel, self.angle, 1)
        self.rect = self.barrel.get_rect(center=self.rect.center)

    def draw(self):
        if self.player == 1 and laser_sight:
            self.laserx, self.lasery = pygame.mouse.get_pos()
            laser = pygame.draw.line(window, red, (self.rect.centerx, self.rect.centery), (self.laserx, self.lasery), 3)
        if self.player != 1:
            self.enemy_laser.draw(self.rect.center, self.target)
        window.blit(self.barrel, self.rect)

    def addAmmo(self, x):
        self.ammo += x

    def shoot(self):
        bullet = Bullet(self.player)
        bullet.upgrade()
        bullet.rect.center = self.rect.center
        target_x, target_y = self.target
        Bullet.bulletMove(bullet, target_x, target_y, self.rect.centerx, self.rect.centery)

    def updateTurret(self, target):
        self.target = target
        self.image_center = self.rect.center
        self.rect.center = self.base.rect.center
        self.get_angle(self.target)
        self.draw()


# Tank Bullet creation class ##############################################################################################
class Bullet(pygame.sprite.Sprite):

    def __init__(self, player):
        # pygame.mixer.Sound.play(shoot_sound)
        global bulletValue
        super().__init__()
        self.player = player

        if self.player == 1:
            bullet_list.add(self)
        else:
            enemy_bullet_list.add(self)
        all_sprites_list.add(self)
        self.image = pygame.image.load(BULLET).convert_alpha()
        self.bulletSpeed = bulletValue * 5
        self.rect = self.image.get_rect()
        self.change_y = 0
        self.change_x = 0
        self.bounces = 0
        self.save_x = 0
        self.save_y = 0
        self.trail = Particle(self.rect.center, white, 3)

    def bulletMove(self, cursor_pos_x, cursor_pos_y, player_pos_x, player_pos_y):

        block_vec_x = (cursor_pos_x - player_pos_x)
        block_vec_y = (cursor_pos_y - player_pos_y)
        vec_length = 1 / 4 * math.sqrt(block_vec_x ** 2 + block_vec_y ** 2)
        block_vec_y = (block_vec_y / vec_length) * self.bulletSpeed
        block_vec_x = (block_vec_x / vec_length) * self.bulletSpeed
        self.change_y += block_vec_y
        self.change_x += block_vec_x

    def bounce(self):
        if self.bounces == bounceNum:
            expl2 = Explosion(self.rect.center, 'sm')
            bullet_list.remove(self)
            all_sprites_list.remove(self)
            enemy_bullet_list.remove(self)
            self.bounces = 0
        else:
            if self.rect.x < 0 or self.rect.x > 1920:
                self.change_x *= -1
            elif self.rect.y < 0 or self.rect.y > 1080:
                self.change_y *= -1
            self.bounces += 1

    def wallBounce(self, wall):
        if self.bounces == bounceNum:
            expl2 = Explosion(self.rect.center, 'sm')
            bullet_list.remove(self)
            enemy_bullet_list.remove(self)
            all_sprites_list.remove(self)
            self.bounces = 0
        else:
            if (self.rect.centerx - 15 < wall.rect.centerx - 50) or (self.rect.centerx + 15 > wall.rect.centerx + 50):
                self.change_x *= -1
            elif (self.rect.centery - 15 < wall.rect.centery - 50) or (self.rect.centery + 15 > wall.rect.centery + 50):
                self.change_y *= -1
            self.bounces += 1

    def update(self):
        self.trail = Particle(self.rect.center, white, 3)
        self.rect.centery += self.change_y
        self.rect.centerx += self.change_x

    def upgrade(self):
        global bulletValue, upgrade
        if upgrade:
            # bulletValue += 1
            print("Weapon Upgrade")
            upgrade = False


# Create explosions class ##############################################################################################
class Explosion(pygame.sprite.Sprite):

    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.center = center
        self.size = size
        self.image = explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 60
        all_sprites_list.add(self)
        # if size == 'lg':
        #     pygame.mixer.Sound.play(explosion_sound2)
        # else:
        #     pygame.mixer.Sound.play(explosion_sound)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = self.center


# Create Bounce class ##############################################################################################
class Bounce(pygame.sprite.Sprite):

    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.center = center
        self.size = size
        self.image = bounce_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 30
        all_sprites_list.add(self)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(bounce_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = bounce_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = self.center


# Create particle effects ##############################################################################################
class Particle:

    def __init__(self, location, color, size):
        super().__init__()
        self.start = player.rect.center
        self.xdir = location[0]
        self.ydir = location[1]
        self.size = random.randint(1, size)
        self.color = color
        particles.append(self)

    def draw(self):
        pygame.draw.circle(window, self.color, [self.xdir, self.ydir], self.size)

    def update(self):
        if self.size > 7:
            self.color = self.color
        elif 5 <= self.size < 7:
            self.color = gray
        elif 0 < self.size < 5:
            self.color = light_gray
        else:
            particles.remove(self)
        self.size -= 0.1
        self.draw()


# Creat progress bars for related object ##############################################################################################
class ProgressBar:

    def __init__(self, max_bar, progress, size, barColor, borderColor, position):
        self.max_bar = max_bar
        self.progress = progress
        self.power = self.progress / self.max_bar
        self.barColor = barColor
        self.borderColor = borderColor
        self.position = position
        self.x, self.y = self.position
        self.size = size

    def draw(self):
        pygame.draw.rect(window, self.borderColor, (*self.position, *self.size), 1)
        innerPos = (self.position[0] + 3, self.position[1] + 3)
        innerSize = ((self.size[0] - 6) * self.power, self.size[1] - 6)
        pygame.draw.rect(window, self.barColor, (*innerPos, *innerSize))

    def update(self, tankPos):
        self.power = self.progress / self.max_bar
        self.position = tankPos
        self.draw()


# Creates a shield object for tank ##############################################################################################
class Shield(pygame.sprite.Sprite):

    def __init__(self, c, x, y, r, a):
        super().__init__()
        self.radius = r
        self.color = c
        self.armor = a
        self.image = pygame.image.load(SHIELD).convert_alpha()
        self.rect = self.image.get_rect(center=[x, y])
        shields.add(self)

    def draw(self):
        if self.armor > 0:
            window.blit(self.image, self.rect)

    def damage(self, x):
        if self.armor > 0:
            self.armor -= x
            armor_bar.progress -= x

    def addArmor(self, x):
        self.armor += x
        armor_bar.progress += x
        if self.armor > 100:
            self.armor = 100
        if armor_bar.progress > 100:
            armor_bar.progress = 100

    def update(self):
        if self.armor > 0:
            self.rect.center = player.rect.center
            self.draw()
        else:
            self.rect.center = [0, 0]


class ShieldAnim(pygame.sprite.Sprite):

    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.center = center
        self.size = size
        self.image = shield_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 60
        pickups.add(self)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(shield_anim[self.size]):
                self.frame = 0
            else:
                center = self.rect.center
                self.image = shield_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = self.center
        window.blit(self.image, self.rect)


# Creates a pickup item in the level ##############################################################################################
class PickUps(pygame.sprite.Sprite):

    def __init__(self, item, x, y):
        super().__init__()
        self.image = pygame.image.load(item).convert()
        self.rect = self.image.get_rect(center=[x, y])
        pickups.add(self)

    def draw(self):
        window.blit(self.image, self.rect)

    def update(self):
        self.draw()


# Creates connection with server ##############################################################################################
class Network:

    def __init__(self):
        global allyLocation, host

        if host:
            self.server = self.startServer()
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((socket.gethostname(), 5555))
        else:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((serverIP, 5555))

        self.player2 = Ally()
        self.player2.rect.center = allyLocation
        self.waitPlayers()
        self.data = ''

    def update(self):
        in_data = self.client.recv(2048)
        out_data = self.sendPosition()
        try:
            self.client.sendall(bytes(out_data, 'UTF-8'))
        except Exception as e:
            print("COOP UPDATE ERROR:", e)
        try:
            newPos = in_data.decode()
            print("Player 2 data:", newPos)
            if newPos != '':
                x = newPos.strip('][').split(',')
            if isinstance(x, list):
                self.player2.rect.centerx = int(x[0])
                self.player2.rect.centery = int(x[1])
                self.player2.updateMouse([int(x[2]), int(x[3])])
                if int(x[4]) == 1:
                    self.player2.turret.shoot()
                self.player2.rotate = int(x[5])
                self.player2.health, self.player2.health_bar.progress = int(x[6]), int(x[6])
                if int(x[7] == 0):
                    enemies.empty()
                self.player2.update()
            else:
                print("Invalid data")
        except Exception as e:
            print("Issue updating coop player data:", e)

    def sendPosition(self):
        global shoot
        try:
            mousex, mousey = pygame.mouse.get_pos()
            player1_pos = str(
                [player.rect.centerx, player.rect.centery, mousex, mousey, shoot, player.rotate, player.health,
                 len(enemies)])
            return player1_pos
        except Exception as e:
            print("SEND POS ERROR:", e)

    def getData(self):
        try:
            in_data = self.client.recv(2048)
            out_data = self.sendPosition()
            try:
                self.client.sendall(bytes(out_data, 'UTF-8'))
            except Exception as e:
                print("COOP UPDATE ERROR:", e)
            data = in_data.decode()
            return data

        except Exception as e:
            print("Get network data error:", e)
            return

    def startServer(self):
        try:
            server = subprocess.Popen(['server.bat'])
            return server
        except Exception as e:
            print("Start server error:", e)

    def disconnect(self):
        out_data = "EXIT"
        try:
            print(out_data)
            self.client.sendall(bytes(out_data, 'UTF-8'))
        except Exception as e:
            print("DISCONNECT ERROR", e)

    # When coop is enabled, waits for player connection
    def waitPlayers(self):
        global coop
        try:
            wait = True
            while wait:
                window.blit(BACKGROUND, (0, 0))
                draw_text(window, "Waiting for another player...", 75, SCREENWIDTH / 2, SCREENHEIGHT / 2 - 100, green)
                draw_text(window, "When other player has connected, game will start.", 30, SCREENWIDTH / 2,
                          SCREENHEIGHT / 2, white)
                draw_text(window, "Press [ESC] to quit", 30, 175, 30, white)
                pygame.display.update()
                for event in pygame.event.get():
                    key = pygame.key.get_pressed()
                    if key[pygame.K_ESCAPE]:
                        coop = False
                        self.disconnect()
                        self.server.terminate()
                        main()
                    if key[pygame.K_SPACE]:
                        wait = False
                x = self.getData()
                if x is not None:
                    if x.find('[') != -1:
                        wait = False

        except Exception as e:
            print("Player waiting error:", e)


# Create level objects ##############################################################################################
class Level(pygame.sprite.Sprite):

    def __init__(self, location_x, location_y, image, breakable):
        super().__init__()
        walls.add(self)
        self.breakable = breakable
        try:
            self.wall = pygame.image.load(image).convert_alpha()
        except Exception as e:
            print(image, e)
        self.rect = self.wall.get_rect()
        self.rect.x = location_x
        self.rect.y = location_y

    def draw(self):
        window.blit(self.wall, self.rect)

    def update(self):
        self.draw()


# Create Level ##############################################################################################
def createLevel():
    global nextLevel, levelMap, levelMap2, levelMap3, levelNum, level, coop, allyLocation
    if infinite:
        levelMap = levelMap2
    # if coop:
    #     levelMap = levelMap3
    if not enemies:  # and not coop:
        nextLevel = True
    if nextLevel:
        level += 1
        if levelNum == len(levelMap):
            endGame(1)
            return
        if levelNum != 0 and not select:
            completionScreen()
        loadingScreen()
        pickups.empty()
        enemy_bullet_list.empty()
        bullet_list.empty()
        walls.empty()
        locx = 0
        locy = 0
        for row in levelMap[levelNum]:
            locx = 0
            for col in row:
                if col == 00000:
                    levels = Level(locx, locy, WALL, False)
                if col == 10101:
                    levels = Level(locx, locy, WALLBREAK, True)
                if col == 10001:
                    levels = Level(locx, locy, SMALLWALL_UP, False)
                if col == 11001:
                    levels = Level(locx, locy + 50, SMALLWALL_SIDE, False)
                if col == 11111:
                    player.rect.x = locx
                    player.rect.y = locy
                if col == 55555:
                    allyLocation = [locx, locy]
                if col == 22222:
                    createEnemy(locx, locy, 50, 0)
                if col == 33333:
                    createEnemy(locx, locy, 150, 1)
                if col == 44444:
                    createEnemy(locx, locy, 500, 2)
                if col == 21212:
                    shieldOrb = ShieldAnim([locx + 50, locy + 50], 'sm')
                    # PickUps(SHIELD_ITEM,locx,locy)
                locx += 100
            locy += 100
        nextLevel = False
        if not infinite:
            levelNum += 1


#####################################----MENUS----#########################################################
def loadingScreen():
    ending = True
    t = 500
    while t > 0:
        s = pygame.Surface((SCREENWIDTH, SCREENWIDTH))
        s.set_alpha(25)
        s.fill(black)
        window.blit(s, (0, 0))
        if t > 250:
            draw_text(window, "LEVEL " + str(levelNum + 1), 150, SCREENWIDTH / 2, SCREENHEIGHT / 3, red)
            draw_text(window, "SCORE: " + str(score), 50, SCREENWIDTH / 2, SCREENHEIGHT / 3 + 150, white)
            draw_text(window, "LOADING....", 50, SCREENWIDTH - 250, SCREENHEIGHT - 100, blue)

        else:
            draw_text(window, "LEVEL " + str(levelNum + 1), 150, SCREENWIDTH / 2, SCREENHEIGHT / 3, red)
            draw_text(window, "SCORE: " + str(score), 50, SCREENWIDTH / 2, SCREENHEIGHT / 3 + 150, white)
            draw_text(window, "LOADING..  ", 50, SCREENWIDTH - 250, SCREENHEIGHT - 100, blue)
        t -= 4
        pygame.display.update()
        clock.tick(60)

def completionScreen():
    ending = True
    t = 400
    while t > 0:
        draw_text(window, "LEVEL COMPLETE", 200, SCREENWIDTH / 2, SCREENHEIGHT / 3, green)
        t -= 4
        pygame.display.update()
        clock.tick(60)

def pauseGame():
    ending = True
    while ending:
        s = pygame.Surface((SCREENWIDTH, SCREENWIDTH))
        s.set_alpha(10)
        s.fill(black)
        window.blit(s, (0, 0))
        draw_text(window, "PAUSED", 100, SCREENWIDTH / 2, SCREENHEIGHT / 3, blue)
        draw_text(window, "Press [SPACE] to unpause", 50, SCREENWIDTH / 2, (SCREENHEIGHT / 3) + 250, white)
        draw_text(window, "Press [ESC] to go to main menu", 30, 250, 30, white)
        for event in pygame.event.get():
            key = pygame.key.get_pressed()
            if key[pygame.K_ESCAPE]:
                resetGame()
                ending = False
            if key[pygame.K_SPACE]:
                startGame()
        pygame.display.update()
        clock.tick(60)
    main()


def endGame(outcome):
    ending = True
    while ending:
        global score
        s = pygame.Surface((SCREENWIDTH, SCREENWIDTH))
        s.set_alpha(5)
        s.fill(black)
        window.blit(s, (0, 0))
        if outcome == 0:
            draw_text(window, "MISSION FAILED", 100, SCREENWIDTH / 2, SCREENHEIGHT / 3, red)
        else:
            draw_text(window, "MISSION ACCOMPLISHED", 100, SCREENWIDTH / 2, SCREENHEIGHT / 3, blue_green)

        draw_text(window, "High Score: " + str(score), 75, SCREENWIDTH / 2, (SCREENHEIGHT / 3) + 150, sky_blue)
        draw_text(window, "Press [SPACE] to replay", 25, SCREENWIDTH / 2, (SCREENHEIGHT / 3) + 250, white)
        draw_text(window, "Press [ESC] to quit", 30, 175, 30, white)
        for event in pygame.event.get():
            key = pygame.key.get_pressed()
            if key[pygame.K_ESCAPE]:
                ending = False
            if key[pygame.K_SPACE]:
                resetGame()
                startGame()
                ending = False
        pygame.display.update()
        clock.tick(60)
    resetGame()
    main()


# Draw text ------------------------------------------------------
font_name = "font/Chunq.ttf"


def draw_text(surf, text, size, x, y, color):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)


def resetGame():
    global speed, infinite, running, shooting, ability, special, timer, coop, shoot, amount, level, levelNum, score, nextLevel, player, specialAmmo, tankShield, special_ability,select

    speed = 1
    move_speed = 1
    upgrade = False
    bulletValue = 1
    god = False
    bounceNum = 2
    specialAmmo = 0
    infinite = False
    laser_sight = False
    levelNum = 0
    running = True
    shooting = False
    ability = 'NOT-READY'
    special = False
    timer = 100
    coop = False
    shoot = 0
    allyLocation = [0, 0]
    amount = 0
    addDifficulty = 1
    level = 0
    score = 0
    nextLevel = True
    select = False

    all_sprites_list.empty()
    bullet_list.empty()
    enemy_bullet_list.empty()
    enemies.empty()
    players_list.empty()
    walls.empty()
    shields.empty()
    pickups.empty()

    players = []
    player = Tank()
    player.rect.center = [200, 500]
    special_ability = ProgressBar(60, 0, (215, 25), purple, gray, [15, SCREENHEIGHT - 35])
    tankShield = Shield(sky_blue, player.rect.centerx, player.rect.centery, 90, 0)
    armor_bar = ProgressBar(100, tankShield.armor, (215, 25), sky_blue, gray, [15, SCREENHEIGHT - 65])

###############################################----Threads----###################################################################
threads = []


def run_shoot():
    global score, addDifficulty, all_sprites_list, timer, nextLevel, laser_sight, specialAmmo, infinite, running, special, shoot

    for event in pygame.event.get():
        key = pygame.key.get_pressed()
        if event.type == pygame.QUIT:
            running = False
        if key[pygame.K_ESCAPE]:
            pauseGame()
        if specialAmmo == 60:
            ability = 'READY'
            laser_sight = True
            if key[pygame.K_SPACE]:
                special = True
        else:
            ability = 'NOT-READY'
            laser_sight = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            shoot = 1
            player.turret.shoot()
            score -= 10
    if special and specialAmmo != 0:
        specialAmmo -= 1
        shoot = 1
        player.turret.shoot()
        score -= 10
        special_ability.progress = 0
    else:
        special = False


def collisions():
    global score, addDifficulty, all_sprites_list, timer, nextLevel, laser_sight, specialAmmo, infinite, running, special

    for p in pickups:
        pickup = pygame.sprite.spritecollide(p, players_list, False)
        if pickup:
            pickups.remove(p)
            tankShield.addArmor(100)

    attacked = pygame.sprite.spritecollide(player, enemies, False)
    for enemyTanker in attacked:  # Checking if enemies collided with player
        player.damage(50)
        all_sprites_list.remove(enemyTanker)
        enemies.remove(enemyTanker)

    for bullets in enemy_bullet_list:  # Checking if enemy bullet collided with player
        player_hit_list = pygame.sprite.spritecollide(bullets, players_list, False)
        shield_hit_list = pygame.sprite.pygame.sprite.spritecollide(bullets, shields, False)
        if player_hit_list:
            Explosion(bullets.rect.center, 'sm')
            all_sprites_list.remove(bullets)
            enemy_bullet_list.remove(bullets)
            player.damage(50)
        elif shield_hit_list:
            Explosion(bullets.rect.center, 'sm')
            all_sprites_list.remove(bullets)
            enemy_bullet_list.remove(bullets)
            if tankShield.armor > 0:
                tankShield.damage(25)

    for bullet in bullet_list:  # Checking if player bullet collided with enemy
        enemy_hit_list = pygame.sprite.spritecollide(bullet, enemies, False)
        if enemy_hit_list:
            for enemy in enemy_hit_list:  # ENEMY KILLED
                enemy.health_bar.progress -= 50
                expl2 = Explosion(bullet.rect.center, 'sm')
                if enemy.health_bar.progress <= 0:
                    expl = Explosion(enemy.rect.center, 'lg')
                    score += 110

                    if specialAmmo < 60 and special is False:
                        special_ability.progress += 5
                        specialAmmo += 5
                    all_sprites_list.remove(enemy)
                    enemies.remove(enemy)
                bullet_list.remove(bullet)
                all_sprites_list.remove(bullet)


def wallCollisions():
    for bullet in bullet_list:  # check if bullet collided with walls
        if (bullet.rect.y < 0 or bullet.rect.y > 1080) or (bullet.rect.x < 0 or bullet.rect.x > 1920):
            b = Bounce(bullet.rect.center, 'lg')
            bullet.bounce()

        wall_hit = pygame.sprite.spritecollide(bullet, walls, False)
        if wall_hit:
            for wall in wall_hit:
                if bullet.rect.collidepoint(bullet.rect.centerx, bullet.rect.centery):
                    if wall.breakable:
                        expl = Explosion(wall.rect.center, 'lg')
                        walls.remove(wall)
                        bullet_list.remove(bullet)
                        all_sprites_list.remove(bullet)
                    else:
                        b = Bounce(bullet.rect.center, 'lg')
                        bullet.wallBounce(wall)

    for enemyBullet in enemy_bullet_list:
        if (enemyBullet.rect.y < 0 or enemyBullet.rect.y > 1080) or (
                enemyBullet.rect.x < 0 or enemyBullet.rect.x > 1920):
            enemyBullet.bounce()
        enemy_wall_hit = pygame.sprite.spritecollide(enemyBullet, walls, False)
        if enemy_wall_hit:
            for wall in enemy_wall_hit:
                enemyBullet.wallBounce(wall)

amount = 0
addDifficulty = 1
level = 0
score = 0
nextLevel = True
def createEnemies():
    try:
        global enemies, amount, upgrade, level, addDifficulty, nextLevel
        if not enemies:
            level += 1
            amount += 5 * addDifficulty
            for x in range(amount):
                enemyTank = Enemy(random.randint(20, 50))
                enemyTank.rect.x = random.randint(SCREENWIDTH * 3 / 4, SCREENWIDTH - 100)
                enemyTank.rect.y = random.randint(100, SCREENHEIGHT - 100)
            nextLevel = True
        else:
            nextLevel = False
    except Exception as e:
        print("Create enemies error:", e)

def createEnemy(x, y, health, strength):
    enemyTank = Enemy(0, health, strength)
    enemyTank.rect.x = x
    enemyTank.rect.y = y

# Create player intance and its turret##############################################################################################
player = Tank()
player.rect.center = [200, 500]
special_ability = ProgressBar(60, 0, (215, 25), purple, gray, [15, SCREENHEIGHT - 35])
tankShield = Shield(sky_blue, player.rect.centerx, player.rect.centery, 90, 0)
armor_bar = ProgressBar(100, tankShield.armor, (215, 25), sky_blue, gray, [15, SCREENHEIGHT - 65])
#####################################################-----START------##################################################################################

clock = pygame.time.Clock()


def startGame():
    global score, addDifficulty, all_sprites_list, timer, nextLevel, laser_sight, specialAmmo, infinite, running, player, enemies, special_ability, shoot, coop, select
    if levelNum == 0 or select:
        for enemy in enemies:
            all_sprites_list.remove(enemy)
        enemies.empty()
    createLevel()
    if coop:
        try:
            coopGame = Network()  # Create new connection
        except Exception as e:
            print("Starting coop error:", e)
            coop = False
            main()

    # Running game ---------------------------
    while running:
        Particle(player.rect.center, gray, 10)
        window.blit(BACKGROUND, (0, 0))
        createLevel()

        # START THREADS ------------------------------------------------a
        run_shoot()
        collisions()
        wallCollisions()

        # logic -----------------------------------------------------------------------------
        if infinite:
            for enemy in enemies:
                enemy.moveLeft(speed)
                if (enemy.rect.x < SCREENWIDTH / 3):
                    enemy.rect.x = random.randint(SCREENWIDTH / 4 * 3, 1745)
                    enemy.changeSpeed(random.randint(20, 30))

        # UPDATES -------------------------------------------------------------
        for particle in particles:
            particle.update()
        all_sprites_list.draw(window)
        all_sprites_list.update()
        walls.update()
        shields.update()

        player.update()

        pickups.update()
        special_ability.update([15, SCREENHEIGHT - 35])
        armor_bar.update([15, SCREENHEIGHT - 100])

        if coop:
            coopGame.update()

        # Create cursor image for default cursor ----------------------------------
        cursor = pygame.image.load(CURSOR)
        pygame.mouse.set_visible(False)  # hide the cursor
        coordx, coordy = pygame.mouse.get_pos()
        window.blit(cursor, (coordx - 10, coordy - 10))

        # Enemy shooting logic -----------------------------------------------------
        for enemy in enemies:
            if timer == 0:  # When timer hits 0, enemy shoots (should be like a 3 second delay between shots)
                enemy.shoot()
            enemy.update()

        # RESET ENEMY SHOOT TIMER
        if timer == 0:
            timer = 100
        timer -= 1  # each loop shortens timer

        # Checks if player has died
        if not coop:
            if player.health <= 0:  # PLAYER DEAD
                exp = Explosion(player.rect.center, 'lg')
                print("Dead")
                running = False
        else:
            if player.health <= 0 and coopGame.player2.health <= 0:  # PLAYER DEAD
                exp = Explosion(player.rect.center, 'lg')
                exp = Explosion(coopGame.player2.rect.center, 'lg')
                print("Both players dead")
                running = False

        # Draw game text on screen --------------------------------------------------------------
        draw_text(window, str("Health: " + str(player.health)), 25, 100, 10, green)
        draw_text(window, str("Score: " + str(score)), 20, 100, 40, sky_blue)
        draw_text(window, str("Special: " + ability), 20, 125, SCREENHEIGHT - 60, purple)
        draw_text(window, str("Shield: "), 20, 125, SCREENHEIGHT - 125, sky_blue)
        draw_text(window, str("Level: " + str(level)), 30, SCREENWIDTH - 100, 10, white)
        draw_text(window, str("Enemies left: " + str(len(enemies))), 20, SCREENWIDTH - 100, 50, red)

        shoot = 0  # Reset player shoot

        # Update game window with changes --------------------
        pygame.display.update()
        clock.tick(60)

    endGame(0)  # If player dies, game over


# Creates clickable buttons ###############################################################
buttons = []

class Button:

    def __init__(self, text, x, y, w, h, color):
        self.width = w
        self.height = h
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.color = color
        self.text = text
        self.click = False
        buttons.append(self)

    def draw(self):
        mouse = pygame.mouse.get_pos()
        if self.x <= mouse[0] <= self.x + self.width and self.y <= mouse[1] <= self.y + self.height:
            pygame.draw.rect(window, gray, [self.x, self.y, self.width, self.height])

        else:
            pygame.draw.rect(window, self.color, [self.x, self.y, self.width, self.height])

        pygame.draw.rect(window, dark_gray, [self.x, self.y, self.width, self.height], 3)
        font = pygame.font.SysFont(font_name, 35)
        label = font.render(self.text, True, white)
        label_rect = label.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        window.blit(label, label_rect)

#Main menu screen ###############################################################
def main():
    global god, coop, infinite, host, levelNum, select, store
    option = False
    coop = False
    pygame.mouse.set_visible(True)  # show the cursor

    # CREATE MENU BUTTONS -------------------------------------------------------
    startButton = Button("PLAY", SCREENWIDTH / 2, SCREENHEIGHT / 2, 450, 50, blue)
    levelSelect = Button("Select Level", SCREENWIDTH / 2 + 350, SCREENHEIGHT / 2, 200, 50, navy_blue)
    coopCreate = Button("Create Coop", SCREENWIDTH / 2 - 125, SCREENHEIGHT / 2 + 100, 200, 50, dark_gray)
    coopJoin = Button("Join Coop", SCREENWIDTH / 2 + 125, SCREENHEIGHT / 2 + 100, 200, 50, dark_gray)
    optionsButton = Button("Options", SCREENWIDTH / 2, SCREENHEIGHT / 2 + 200, 450, 50, dark_gray)
    quitButton = Button("Exit Game", SCREENWIDTH / 2, SCREENHEIGHT / 2 + 400, 450, 50, dark_gray)
    # Options buttons ---
    godButton = Button("GOD MODE", SCREENWIDTH / 2 - 125, SCREENHEIGHT / 2 + 50, 200, 50, red)
    infButton = Button("INFINITE", SCREENWIDTH / 2 + 125, SCREENHEIGHT / 2 + 50, 200, 50, red)
    back = Button("Back", SCREENWIDTH / 2, SCREENHEIGHT / 2 + 150, 450, 50, dark_gray)
    #Level select buttons ---
    lb = []
    x = 75
    for i in range(len(levelMap)):
        lb.append(Button(str(i + 1),SCREENWIDTH/3 + x, SCREENHEIGHT/2,50,50,blue))
        x += 100

    #store button ----
    storeButton = Button("Skin Shop", SCREENWIDTH / 2, SCREENHEIGHT / 2 + 300, 450, 50, purple)

    # Create main menu background enemies --------
    y = 25
    for i in range(8):
        createEnemy(0, y, 100, 0)
        y += 125

    # start menu loop -----
    menu = True
    while menu:

        Particle(player.rect.center, gray, 10)

        window.blit(BACKGROUND, (0, 0))

        for enemy in enemies:
            enemy.moveLeft(4)
            if enemy.rect.x < 0:
                enemy.rect.x = random.randint(SCREENWIDTH / 2, SCREENWIDTH)
                enemy.changeSpeed(random.randint(50, 100))
        # Check if any of the buttons were clicked -------
        mouse = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.x <= mouse[0] <= button.x + button.width and button.y <= mouse[1] <= button.y + button.height:
                        button.click = True
                    else:
                        button.click = False

        # Draw other window elements ------------------------
        for particle in particles:
            particle.update()
        all_sprites_list.draw(window)
        all_sprites_list.update()

        player.update()

        draw_text(window, "FLANK TANK", 200, SCREENWIDTH / 2, 250, green)


        if option:  # options menu
            if godButton.click:
                god = True
                godButton.color = green
            if infButton.click:
                infinite = True
                infButton.color = green
            if back.click:
                option = False
            godButton.draw()
            infButton.draw()
            back.draw()

        elif select: #level select
            i = 0
            for button in lb:
                if button.click:
                    levelNum = i
                    loadingScreen()
                    startGame()
                i += 1
                button.draw()
            if back.click:
                select = False
            back.draw()
        elif store: # skin shop
            shop = Shop()
            shop.update()
            if back.click:
                store = False
            back.draw()

        # Show main buttons -------
        else:
            if startButton.click:
                loadingScreen()
                startGame()
            if levelSelect.click:
                select = True
            if coopCreate.click:
                coop = True
                host = True
                startGame()
            if coopJoin.click:
                coop = True
                startGame()
            if optionsButton.click:
                option = True
            if storeButton.click:
                store = True
            if quitButton.click:
                menu = False

            # draw buttons ---------------
            startButton.draw()
            levelSelect.draw()
            coopCreate.draw()
            coopJoin.draw()
            optionsButton.draw()
            storeButton.draw()
            quitButton.draw()

        clock.tick(60)
        pygame.display.update()
    pygame.quit()


if __name__ == "__main__":
    main()
