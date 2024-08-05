import pygame
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import threading
import os
import random

cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.8, maxHands=2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


frame_with_landmarks = None
fingersUp = {'Right':[], 'Left':[]}
fingersUp_lock = threading.Lock()



def hand_detection():
    global fingersUp, frame_with_landmarks
    while True:
        ret, frame = cap.read()
        cv2.rectangle(frame, (0, 0), (250, 50), (0, 255, 0), -1)
        cv2.putText(frame, 'Right:', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (640-250, 0), (640, 50), (255, 255, 17), -1)
        cv2.putText(frame, 'Left:', (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        if not ret:
            continue
        hands, img = detector.findHands(frame)
        with fingersUp_lock:
            if hands and len(hands)==2:    
                fingersUp[hands[0]['type']] = detector.fingersUp(hands[0])
                fingersUp[hands[1]['type']] = detector.fingersUp(hands[1])
                if fingersUp["Right"]==[0,1,0,0,0]:
                    cv2.putText(frame, '-->', (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif fingersUp["Right"]==[0,1,1,0,0]:
                    cv2.putText(frame, '<--', (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                if fingersUp["Left"]==[1,1,1,1,1]:
                    cv2.putText(frame, 'JUMPING', (480, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                elif fingersUp["Left"]==[0,1,0,0,0]:
                    cv2.putText(frame, 'SHOOTING', (480, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            else:
                fingersUp = {'Right':[], 'Left':[]}

        frame_with_landmarks = cv2.flip(frame, 1)

hand_thread = threading.Thread(target=hand_detection, daemon=True)
hand_thread.start()
        

screen_width = 1200
screen_height = 720



pygame.init()

music = pygame.mixer.music.load('assets/music.ogg')
pygame.mixer.music.play(-1)
shooting_sound = pygame.mixer.Sound('assets/shooting.wav')
screaming_sound = pygame.mixer.Sound('assets/screaming.wav')


win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('GESTURE-CONTROLLED SHOOTER GAME')

bullet_img = pygame.transform.scale(pygame.image.load('assets/light_bullet.png'), (15, 15))
bg_img = pygame.image.load('assets/swamp.png')
gameover = pygame.image.load('assets/game_over.png')
game_over = pygame.transform.scale(gameover, (screen_width, screen_height))
bg = pygame.transform.scale(bg_img, (screen_width, screen_height))
blood = pygame.image.load('assets/blood2.png')
blood_player = pygame.image.load('assets/blood_player2.png')

#stationary = pygame.image.load(os.path.join("hero", "standing.png"))

left = [None]*10
for picIndex in range(1,10):
    left[picIndex-1] = pygame.image.load(os.path.join("hero", "L"+str(picIndex)+".png"))
    picIndex+=1

right = [None]*10
for picIndex in range(1,10):
    right[picIndex-1] = pygame.image.load(os.path.join("hero", "R"+str(picIndex)+".png"))
    picIndex+=1

left_enemy = [
    pygame.image.load(os.path.join("enemy", "L1E.png")),
    pygame.image.load(os.path.join("enemy", "L2E.png")),
    pygame.image.load(os.path.join("enemy", "L3E.png")),
    pygame.image.load(os.path.join("enemy", "L4E.png")),
    pygame.image.load(os.path.join("enemy", "L5E.png")),
    pygame.image.load(os.path.join("enemy", "L6E.png")),
    pygame.image.load(os.path.join("enemy", "L7E.png")),
    pygame.image.load(os.path.join("enemy", "L8E.png")),
    pygame.image.load(os.path.join("enemy", "L9P.png")),
    pygame.image.load(os.path.join("enemy", "L10P.png")),
    pygame.image.load(os.path.join("enemy", "L11P.png"))]

right_enemy = [
    pygame.image.load(os.path.join("enemy", "R1E.png")),
    pygame.image.load(os.path.join("enemy", "R2E.png")),
    pygame.image.load(os.path.join("enemy", "R3E.png")),
    pygame.image.load(os.path.join("enemy", "R4E.png")),
    pygame.image.load(os.path.join("enemy", "R5E.png")),
    pygame.image.load(os.path.join("enemy", "R6E.png")),
    pygame.image.load(os.path.join("enemy", "R7E.png")),
    pygame.image.load(os.path.join("enemy", "R8E.png")),
    pygame.image.load(os.path.join("enemy", "R9P.png")),
    pygame.image.load(os.path.join("enemy", "R10P.png")),
    pygame.image.load(os.path.join("enemy", "R11P.png"))]


class Hero:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_x = 6
        self.vel_y = 10
        self.face_right = True
        self.face_left = False
        self.stepIndex = 0
        self.jump = False
        self.bullets = []
        self.cool_down_count = 0
        #health
        self.hitbox = (self.x+40, self.y+30, 45, 95)
        self.health = 100
        self.alive = True
        self.score = 0
        self.bleeding = False
        self.bleeding_counter = 5

    def move_hero(self, userInput):
        self.bleed(win)
        if (userInput[pygame.K_RIGHT]and(self.x<screen_width-105)) or ((fingersUp["Right"]==[0,1,0,0,0]) and(self.x<screen_width-105)):
            self.x += self.vel_x
            self.face_right = True
            self.face_left = False
        elif ((userInput[pygame.K_LEFT])and(self.x>-15)) or ((fingersUp["Right"] ==[0,1,1,0,0])and(self.x>-15)):
            self.x -= self.vel_x
            self.face_right = False
            self.face_left = True

        else:
            self.stepIndex = 0

    def jump_motion(self, userInput):
        with fingersUp_lock:
            if self.jump is False and (userInput[pygame.K_SPACE] or (fingersUp["Left"]==[1,1,1,1,1])):
                self.jump = True
        if self.jump is True:
            # player.y -= player.vel_y*4
            # player.vel_y -= 1
            # if player.vel_y < -10:
            #     self.jump = False
            #     player.vel_y = 10

            player.y -= player.vel_y*2
            player.vel_y -= 0.5
            if player.vel_y < -10:
                self.jump = False
                player.vel_y = 10

    def draw(self, win):
        with fingersUp_lock:
            self.hitbox = (self.x+40, self.y+30, 45, 95)
            # pygame.draw.rect(win, (0, 0, 0), self.hitbox, 1)
            pygame.draw.rect(win, (255, 0, 0), (self.x+20, self.y+12, 100, 15))
            if self.health >= 0:
                pygame.draw.rect(win, (0, 255, 0), (self.x+20, self.y+12, self.health, 15))
                font = pygame.font.Font('freesansbold.ttf', 16)
                text = font.render(str(self.health)+" %", True, (255, 255, 255))
                win.blit(text, (self.x+22, self.y-5))
            if self.stepIndex>=27:
                self.stepIndex = 0
            if self.face_left:
                win.blit(left[self.stepIndex//3], (self.x,self.y))
                self.stepIndex+=1
            if self.face_right:
                win.blit(right [self.stepIndex//3], (self.x,self.y))
                self.stepIndex+=1
    

    def cooldown(self):
        if self.cool_down_count>=20:
            self.cool_down_count = 0
        elif self.cool_down_count > 0:
            self.cool_down_count+=1
    
    def shoot(self):
        self.cooldown()
        if (userInput[pygame.K_f] and self.cool_down_count==0) or (fingersUp["Left"]==[0,1,0,0,0] and self.cool_down_count==0):
            shooting_sound.play()
            bullet = Bullet(self.x, self.y, self.face_left)
            self.bullets.append(bullet)
            self.cool_down_count = 1
        for bullet in self.bullets:
            bullet.move()
            if bullet.off_screen():
                self.bullets.remove(bullet)

    def hit(self):
        for enemy in enemies:
            for bullet in self.bullets:
                if (enemy.hitbox[0] < bullet.x < enemy.hitbox[0]+enemy.hitbox[2]) and (enemy.hitbox[1] < bullet.y < enemy.hitbox[1]+enemy.hitbox[3]):
                    self.bullets.remove(bullet)
                    enemy.health-=4
                    enemy.bleeding = True
                    if enemy.health==0:
                        enemies.remove(enemy)
                        self.score+=1

    def bleed(self, win):
        if self.bleeding:
            win.blit(blood_player, (self.x+30, self.y))
            self.bleeding_counter -= 1
            if self.bleeding_counter==0:
                self.bleeding = False
                self.bleeding_counter = 5
class Bullet:
    def __init__(self, x, y, left):
        if left:
            self.direction = "left"
        else:
            self.direction = "right"
        if self.direction=="right":
            self.x = x+80
            self.y = y+65
        else:
            self.x = x+35
            self.y = y+65

    def draw_bullets(self):
        win.blit(bullet_img, (self.x, self.y))
    
    def move(self):
        if self.direction == "right":
            self.x+=15
        else:
            self.x-=15
    
    def off_screen(self):
        return not(self.x >= 0 and self.x <= screen_width)

class Enemy:
    def __init__(self, x, y, dir):
        self.direction = dir
        if self.direction=="left":
            self.y = y+10
        else:
            self.y = y-10
        self.x = x
        if self.direction == "left":
            self.stepIndex = 0
        else:
            self.stepIndex = 11
        #health
        self.hitbox = (self.x+40, self.y+30, 45, 95)
        self.health = 40
        self.bleeding = False
        self.bleeding_counter = 7
    
    def check_step(self):
        if self.stepIndex >=66 and self.direction=="left":
            self.stepIndex=0
        elif self.stepIndex >=66 and self.direction=="right":
            self.stepIndex=11

    def draw(self, win):
        self.hitbox = (self.x+30, self.y+6, 50, 80)

        # pygame.draw.rect(win, (0, 0, 0), self.hitbox, 1)
        pygame.draw.rect(win, (255, 0, 0), (self.x+35, self.y, 40, 10))
        if self.health >= 0:
            pygame.draw.rect(win, (0, 255, 0), (self.x+35, self.y, self.health, 10))
        self.check_step()
        if self.direction=="left":
            win.blit(left_enemy[self.stepIndex//6], (self.x, self.y))
        else:
            win.blit(right_enemy[self.stepIndex//6], (self.x, self.y))
        self.stepIndex+=1
    
    def move(self):
        self.hit()
        self.bleed(win)
        if self.direction=="left":
            self.x -= 2
        else:
            self.x += 2
    
    def bleed(self, win):
        if self.bleeding:
            win.blit(blood, (self.x+30, self.y))
            self.bleeding_counter -= 1
            if self.bleeding_counter==0:
                self.bleeding = False
                self.bleeding_counter = 7


    def hit(self):
        if (player.hitbox[0] < enemy.x+50 < player.hitbox[0]+player.hitbox[2]) and (player.hitbox[1] < enemy.y+32 < player.hitbox[1]+player.hitbox[3]):
            screaming_sound.play()
            player.health-=1
            player.bleeding = True
            if player.health==0:
                player.alive = False

    def off_screen(self):
        if self.direction == "left":
            return not(self.x >= -110 and self.x <= screen_width)
        else:
            return not(self.x <= screen_width)
    


i = 0

def draw_game():
    #draw moving background
    global i
    global enemies
    win.blit(bg, (i,0))
    win.blit(bg, (screen_width+i, 0))
    if i== -screen_width:
        win.blit(bg, (screen_width+i, 0))
        i=0
    i -= 1

    #draw player
    player.draw(win)

    #draw bullets
    for bullet in player.bullets:
        bullet.draw_bullets()
    
    #draw enemies
    for enemy in enemies:
        enemy.draw(win)

    if not player.alive:
        win.blit(game_over, (0, 0))
        enemies = []
        if fingersUp["Right"]==[1,1,1,1,1] and fingersUp["Left"]==[1,1,1,1,1]:
            player.alive = True
            player.score = 0
            player.health = 100
    
    font = pygame.font.Font('freesansbold.ttf', 32)
    text = font.render("Kills: " + str(player.score), True, (255, 0, 0))
    pygame.draw.rect(win, (255, 255, 0), (1030, 10, 150, 50))
    win.blit(text, (1035, 20))



player = Hero(screen_width/2, screen_height-200)
enemies = []

last_spawn_time = pygame.time.get_ticks()
spawn_delay = random.randint(2000, 5000)  # Initial random delay between 1 and 3 seconds

run = True
while run:
    current_time = pygame.time.get_ticks()
    userInput = None
    # win.fill((0, 0, 0))
    draw_game()
    # pygame.draw.circle(win, (255, 255, 17), (int(x), int(y)), radius)
    
    #EXIT IMPLEMENTATION----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    #----------------------------
    
    userInput = pygame.key.get_pressed()
    player.move_hero(userInput)
    player.jump_motion(userInput)
    player.shoot()
    player.hit()

    #Enemy
    if current_time - last_spawn_time > spawn_delay:
        if len(enemies)<3:
            rand_nr = random.randint(0,1)
            if rand_nr == 1:
                last_spawn_time = current_time
                enemy = Enemy(screen_width, screen_height-170, "left")
                enemies.append(enemy)
            elif rand_nr==0:
                last_spawn_time = current_time
                enemy = Enemy(-110, screen_height-170, "right")
                enemies.append(enemy)
    
    for enemy in enemies:
        enemy.move()
        if enemy.off_screen():
            enemies.remove(enemy)

    if frame_with_landmarks is not None:
        frame_with_landmarks = cv2.resize(frame_with_landmarks, (400,250))
        frame_rgb = cv2.cvtColor(frame_with_landmarks, cv2.COLOR_BGR2RGB)
        frame_rgb = np.rot90(frame_rgb)
        frame_surface = pygame.surfarray.make_surface(frame_rgb)
        win.blit(frame_surface, ((screen_width/2)-200,0))

    pygame.display.update()