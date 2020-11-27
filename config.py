import pygame
import os
import socket

pygame.mixer.init()

# Set up screen and screen title --------------------------------------------------------
SCREENWIDTH = 1920
SCREENHEIGHT = 1080

# Miscellaneous variables -------------
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
select = False
# Network -------------------------------------------------
serverIP = socket.gethostname()
host = False

# sprites locations-------------------------------------------------
PLAYER = os.path.join('sprites', 'tank', 'tank0.png')
ALLY = os.path.join('sprites', 'tank', 'tankAlly0.png')
ENEMY = os.path.join('sprites', 'tank', 'enemy.png')
ENEMY2 = os.path.join('sprites', 'tank', 'enemy2.png')
ENEMY3 = os.path.join('sprites', 'tank', 'enemy3.png')
TURRET = os.path.join('sprites', 'tank', 'turret.png')
SHIELD = os.path.join('sprites', 'other', 'shield.png')
WALL = os.path.join('sprites', 'level', 'wall.png')
SMALLWALL_UP = os.path.join('sprites', 'level', 'wallc.png')
SMALLWALL_SIDE = os.path.join('sprites', 'level', 'walld.png')
WALLBREAK = os.path.join('sprites', 'level', 'wallb.png')
BULLET = os.path.join('sprites', 'other', 'bullet.png')
CURSOR = os.path.join('sprites', 'other', 'cursor.png')
BACKGROUND = os.path.join('sprites', 'level', 'background.png')
SHIELD_ITEM = os.path.join('sprites', 'level', 'shield_item.png')

# Usable colors ------------------------------------------------
white = (255, 255, 255)
blue = (0, 0, 255)
green = (0, 255, 0)
red = (255, 0, 0)
black = (0, 0, 0)
orange = (255, 100, 10)
yellow = (255, 255, 0)
blue_green = (0, 255, 170)
marroon = (115, 0, 0)
lime = (180, 255, 100)
pink = (255, 100, 180)
purple = (240, 0, 255)
gray = (127, 127, 127)
magenta = (255, 0, 230)
brown = (100, 40, 0)
forest_green = (0, 50, 0)
navy_blue = (0, 0, 100)
rust = (210, 150, 75)
dandilion_yellow = (255, 200, 0)
highlighter = (255, 255, 100)
sky_blue = (0, 255, 255)
light_gray = (200, 200, 200)
dark_gray = (50, 50, 50)
tan = (230, 220, 170)
coffee_brown = (200, 190, 140)
moon_glow = (235, 245, 255)

# SOUNDS -----------------------------------------------
pygame.mixer.fadeout(1)
explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")
explosion_sound2 = pygame.mixer.Sound("sounds/bigexplosion.wav")
shoot_sound = pygame.mixer.Sound("sounds/shoot.wav")
