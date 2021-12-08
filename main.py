# coding:utf-8
from types import TracebackType
import numpy as np
import cv2
import time
import configparser
import play_sound
import threading
import copy
import random
from cvzone.HandTrackingModule import HandDetector
import queue
import sys

detector = HandDetector(detectionCon=0.8)

#カメラ設定
CAMERA_FPS = 12
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

#石の数
width = 6
height = 5
max_type = 6

#石の大きさ
stone_height = 55
stone_width = 55

#石の間隔
bet_stone_y = 65
bet_stone_x = 65

#ホールド時間制限
hold_time_limit = 10

#ホールドの指の間隔
hold_finger_bet = 80

timerbar_length = bet_stone_x
hpbar_length = bet_stone_x*width

#ステージの左上
stage_x = 200
stage_y = 50

#映像設定
img_up = stage_y-30
img_left = stage_x-30
IMAGE_WIDTH = bet_stone_x*width+60
IMAGE_HEIGHT = bet_stone_y*(height+1)+30
ENEMY_WIDTH = IMAGE_WIDTH
ENEMY_HEIGHT = IMAGE_HEIGHT
IMAGE_QUALITY = 100

WINDOW_WIDTH = int((IMAGE_WIDTH+ENEMY_WIDTH)*1.5)
WINDOW_HEIGHT = int(IMAGE_HEIGHT*1.5)

#各種フラグ
initial_flag = True
waiting_flag = False
holding_flag = False
moving_flag = False
turn_change_flag = False
check_delete_flag = False
check_fall_flag = False
wait_delete_flag = False
wait_fall_flag = False
wait_yourattack_flag = False
wait_enemyattack_flag = False
finished_flag = False
finish_flag = True
finish_sound_flag = True

#各種待ち時間
delete_wait_time = 0.4
fall_wait_time = 0.1
yourattack_wait_time = 1.5
enemyattack_wait_time = 1.5
init_wait_time = 2

cells = [[0 for _ in range(width)] for _ in range(height)]
turn = 1
combo = 0
yourattack = 0
enemyattack = 0
heal = 0
your_max_hp = 1000
enemy_max_hp = 1000
your_hp = your_max_hp
enemy_hp = enemy_max_hp
enemy = cv2.imread('enemy/punpkin.jpg')
enemy = cv2.resize(enemy, (ENEMY_WIDTH, ENEMY_HEIGHT))

holding_stone = [-1, -1]
print_x = -1
print_y = -1
deleted_attack_stone_num = 0
deleted_heal_stone_num = 0

checked_x = [[False for _ in range(width)] for _ in range(height)]
checked_y = [[False for _ in range(width)] for _ in range(height)]
delete_list = queue.Queue()
check_list = queue.Queue()
checked_delete = [[False for _ in range(width)] for _ in range(height)]


def calc_yourattack(deleted_attack_stone_num, combo):
    return int(10*deleted_attack_stone_num*1.1**combo)

def calc_heal(deleted_heal_stone_num, combo):
    return int(20*deleted_heal_stone_num*1.1**combo)

def calc_enemyattack():
    return int(200 + 50*np.random.randn())


def swap_cells(holding_stone):
    swapped = False
    if lmList[8][0] > stage_x + bet_stone_x*(holding_stone[1]+1) and holding_stone[1] < width-1:
        cells[holding_stone[0]][holding_stone[1]], cells[holding_stone[0]][holding_stone[1]+1] = cells[holding_stone[0]][holding_stone[1]+1], cells[holding_stone[0]][holding_stone[1]]
        holding_stone[1] += 1
        swapped = True
        thread = threading.Thread(target=play_sound.play_swap_sound)
        thread.start()
                    
    if lmList[8][0] < stage_x + bet_stone_x*holding_stone[1] and holding_stone[1] > 0:
        cells[holding_stone[0]][holding_stone[1]], cells[holding_stone[0]][holding_stone[1]-1] = cells[holding_stone[0]][holding_stone[1]-1], cells[holding_stone[0]][holding_stone[1]]
        holding_stone[1] -= 1
        swapped = True
        thread = threading.Thread(target=play_sound.play_swap_sound)
        thread.start()

    if lmList[8][1] > stage_y + bet_stone_y*(holding_stone[0]+1) and holding_stone[0] < height-1:
        cells[holding_stone[0]][holding_stone[1]], cells[holding_stone[0]+1][holding_stone[1]] = cells[holding_stone[0]+1][holding_stone[1]], cells[holding_stone[0]][holding_stone[1]]
        holding_stone[0] += 1
        swapped = True
        thread = threading.Thread(target=play_sound.play_swap_sound)
        thread.start()
        
    if lmList[8][1] < stage_y + bet_stone_y*holding_stone[0] and holding_stone[0] > 0:
        cells[holding_stone[0]][holding_stone[1]], cells[holding_stone[0]-1][holding_stone[1]] = cells[holding_stone[0]-1][holding_stone[1]], cells[holding_stone[0]][holding_stone[1]]
        holding_stone[0] -= 1
        swapped = True
        thread = threading.Thread(target=play_sound.play_swap_sound)
        thread.start()
    return (holding_stone, swapped)


def draw_stone(img, x, y, w, h, i, j):
    if cells[i][j] == 0:
        cv2.circle(img, (x+w//2,y+h//2), h//2 ,(255, 200, 0), thickness=-1)
    elif cells[i][j] == 1:
        cv2.circle(img, (x+w//2,y+h//2), h//2 ,(0, 230, 0), thickness=-1)
    elif cells[i][j] == 2:
        cv2.circle(img, (x+w//2,y+h//2), h//2 ,(0, 0, 255), thickness=-1)
    elif cells[i][j] == 3:
        cv2.circle(img, (x+w//2,y+h//2), h//2 ,(175, 0, 175), thickness=-1)
    elif cells[i][j] == 4:
        cv2.rectangle(img, (x,y), (x+w, y+h),(255, 225, 255),cv2.FILLED)
    elif cells[i][j] == 5:
        cv2.circle(img, (x+w//2,y+h//2), h//2 ,(0, 255, 255), thickness=-1)
    return img

def draw_all_stone(img):
    for i in range(height):
        for j in range(width):
            x = bet_stone_x*j + stage_x
            y = bet_stone_y*i + stage_y
            if i == holding_stone[0] and j == holding_stone[1]:
                img = draw_stone(img, lmList[8][0]-30, lmList[8][-1]-30, stone_width+15, stone_height+15, i, j)
            else:
                img = draw_stone(img, x, y, stone_width, stone_height, i, j)
    return img


def count_stone_x(_x, _y, _celltype, count):
    if _celltype == -1:
        return 0
    if _x<0 or _x>=width or _y<0 or _y >= height or checked_x[_y][_x] or cells[_y][_x]!=_celltype:
        return count
    count += 1
    checked_x[_y][_x] = True
    if not checked_delete[_y][_x]:
        check_list.put([_y, _x])
        checked_delete[_y][_x] = True
    count = count_stone_x(_x+1, _y, _celltype, count)
    count = count_stone_x(_x-1, _y, _celltype, count)
    return count

def count_stone_y(_x, _y, _celltype, count):
    if _celltype == -1:
        return 0
    if _x<0 or _x>=width or _y<0 or _y>=height or checked_y[_y][_x] or cells[_y][_x]!=_celltype:
        return count
    count += 1
    checked_y[_y][_x] = True
    if not checked_delete[_y][_x]:
        check_list.put([_y, _x])
        checked_delete[_y][_x] = True
    count = count_stone_y(_x, _y+1, _celltype, count)
    count = count_stone_y(_x, _y-1, _celltype, count)
    return count

def check_delete(_x, _y, _celltype):
    for i in range(height):
        for j in range(width):
            checked_x[i][j] = False
            checked_y[i][j] = False
    n_x = count_stone_x(_x, _y, _celltype, 0)
    n_y = count_stone_y(_x, _y, _celltype, 0)
    if n_x >=3 or n_y >= 3:
        delete_list.put([_y, _x])


def adjust(img, alpha=1.0, beta=0.0):
    dst = alpha * img + beta
    return np.clip(dst, 0, 255).astype(np.uint8)


def init_cells(cells):
    for y in range(height):
        for x in range(width):
            cells[y][x] = random.randrange(max_type)
    not_ready = True
    while not_ready:
        not_ready = False
        for i in range(height):
            for j in range(width):
                checked_delete[i][j] = False
        for y in range(height):
            for x in range(width):
                if not checked_delete[y][x]:
                    check_list.put([y, x])
                    checked_delete[y][x] = True
                    while not check_list.empty():
                        pos = check_list.get()
                        check_delete(pos[1], pos[0], cells[pos[0]][pos[1]])
                        while not delete_list.empty():
                            not_ready = True
                            pos = delete_list.get()
                            cells[pos[0]][pos[1]] = random.randrange(max_type)
    return cells


def draw_game(img):
    img = draw_all_stone(img)
    if lmList:
        cv2.putText(img, str(int(l1)), (stage_x,bet_stone_y*(height+1)+stage_y-30), cv2.FONT_HERSHEY_PLAIN,1,(255,255,255),2)
        if moving_flag:
            cv2.rectangle(img, (lmList[8][0], lmList[8][1]-10), (lmList[8][0]+timerbar_length, lmList[8][1]-5),(0,0,0),cv2.FILLED)
            cv2.rectangle(img, (lmList[8][0], lmList[8][1]-10), (lmList[8][0]+int(timerbar_length*hold_left//hold_time_limit), lmList[8][1]-5),(255,255,255),cv2.FILLED)
        else:
            cv2.circle(img, (lmList[8][0], lmList[8][1]), 7,(255,255,255),cv2.FILLED)
    text_hp_1 = 'YOUR HP:'+str(your_hp)
    cv2.rectangle(img, (stage_x, stage_y-10), (stage_x+hpbar_length, stage_y-5),(0,0,255),cv2.FILLED)
    cv2.rectangle(img, (stage_x, stage_y-10), (stage_x+hpbar_length*your_hp//your_max_hp, stage_y-5),(0,255,0),cv2.FILLED)
    cv2.putText(img, text_hp_1, (stage_x-15, stage_y-15), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)
    if initial_flag:
        cv2.rectangle(img, (stage_x-50, bet_stone_y+bet_stone_y*2), (stage_x+bet_stone_x*width+50, bet_stone_y+bet_stone_y*3),(255,0,255),cv2.FILLED)
        cv2.putText(img, 'BOSS BATTLE!', (stage_x, bet_stone_y+bet_stone_y*2+50), cv2.FONT_HERSHEY_PLAIN,3.5,(0,0,255),5)
    elif not waiting_flag and not lmList:
        text = 'NO HAND DETECTED'
        cv2.putText(img, text, (stage_x, bet_stone_y+bet_stone_y*2+30), cv2.FONT_HERSHEY_PLAIN,2.5,(255,255,255),3)
        
    elif wait_yourattack_flag:
        text = 'YOUR ATTACK:' + str(yourattack)
        cv2.rectangle(img, (stage_x-50, bet_stone_y+bet_stone_y*2), (stage_x+bet_stone_x*width+50, bet_stone_y+bet_stone_y*3),(255,255,255),cv2.FILLED)
        cv2.putText(img, text, (stage_x, bet_stone_y+bet_stone_y*3-20), cv2.FONT_HERSHEY_PLAIN,2.5,(0,150,255),3)
    elif wait_enemyattack_flag:
        text = 'ENEMY\'S ATTACK:' + str(enemyattack)
        cv2.rectangle(img, (stage_x-50, bet_stone_y+bet_stone_y*2), (stage_x+bet_stone_x*width+50, bet_stone_y+bet_stone_y*3),(255,255,255),cv2.FILLED)
        cv2.putText(img, text, (stage_x-20, bet_stone_y+bet_stone_y*3-20), cv2.FONT_HERSHEY_PLAIN,2.5,(0,0,255),3)
    elif finished_flag:
        if winner == 0:
            cv2.rectangle(img, (stage_x-50, bet_stone_y+bet_stone_y*2), (stage_x+bet_stone_x*width+50, bet_stone_y+bet_stone_y*3),(0,255,255),cv2.FILLED)
            cv2.putText(img, 'YOU WIN!', (stage_x+30, bet_stone_y+bet_stone_y*2+50), cv2.FONT_HERSHEY_PLAIN,4.5,(0,0,255),5)
        else:
            cv2.rectangle(img, (stage_x-50, bet_stone_y+bet_stone_y*2), (stage_x+bet_stone_x*width+50, bet_stone_y+bet_stone_y*3),(255,255,0),cv2.FILLED)
            cv2.putText(img, 'YOU LOSE!', (stage_x, bet_stone_y+bet_stone_y*2+50), cv2.FONT_HERSHEY_PLAIN,4.5,(255,0,0),5)
    if waiting_flag and not finished_flag and not wait_enemyattack_flag and not wait_yourattack_flag:
        text = str(yourattack)+'DAMAGE!'+' '+str(heal)+'HEAL!'
        cv2.rectangle(img, (stage_x, bet_stone_y+bet_stone_y*height-10), (stage_x+bet_stone_x*5, bet_stone_y+bet_stone_y*height+30),(255,255,255),cv2.FILLED)
        cv2.putText(img, 'DAMAGE', (stage_x,bet_stone_y*(height+1)+stage_y-30), cv2.FONT_HERSHEY_PLAIN,1,(0,0,255),2)
        cv2.putText(img, str(yourattack), (stage_x+80,bet_stone_y*(height+1)+stage_y-30), cv2.FONT_HERSHEY_PLAIN,2,(0,0,255),3)
        cv2.putText(img, 'HEAL', (stage_x+150,bet_stone_y*(height+1)+stage_y-30), cv2.FONT_HERSHEY_PLAIN,1,(0,255,0),2)
        cv2.putText(img, str(heal), (stage_x+220,bet_stone_y*(height+1)+stage_y-30), cv2.FONT_HERSHEY_PLAIN,2,(0,255,0),3)
        if print_x != -1 and print_y != -1:
            cv2.putText(img, str(combo)+'COMBO!', (bet_stone_x*print_x + stage_x,bet_stone_y*(print_y+1) + stage_y), cv2.FONT_HERSHEY_PLAIN,3,(255,255,255),3)
    return img

def draw_enemy(enemy):
    enemy = copy.copy(enemy)
    text_hp_2 = 'ENEMY HP:'+str(enemy_hp)
    cv2.rectangle(enemy, (80, 250), (80+250, 250+5),(0,0,255),cv2.FILLED)
    cv2.rectangle(enemy, (80, 250), (80+int(250*enemy_hp//enemy_max_hp), 250+5),(0,255,0),cv2.FILLED)
    cv2.putText(enemy, text_hp_2, (80-10, 250-10), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 2)
    return enemy





cells = init_cells(cells)
back_bgm = True
start_time = time.perf_counter()
while True:
    now_time = time.perf_counter()
    flag, img = cam.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList, bboxInfo = detector.findPosition(img)
    if lmList:
        l1, _, _ = detector.findDistance(8, 12, img)
    img = adjust(img, alpha=0.4, beta=20.0)

    if initial_flag:
        if now_time - start_time > init_wait_time:
            initial_flag = False
#待ち状態でない=操作可能なとき
    elif not waiting_flag:       
        if lmList:
        #ホールド中
            if holding_flag and l1 < hold_finger_bet:
                if moving_flag:
                    hold_time = now_time - hold_start_time
                    hold_left = hold_time_limit - hold_time
                    if hold_left < 0:
                        holding_flag = False
                        moving_flag = False
                        holding_stone = [-1, -1]
                        check_delete_flag = True
                        waiting_flag = True
        #ホールドする
            elif not holding_flag and l1 < hold_finger_bet and lmList[8][1]>stage_y and lmList[8][0]>stage_x and lmList[8][1]<stage_y+bet_stone_y*height and lmList[8][0]<stage_x+bet_stone_x*width:
                holding_flag = True
                holding_stone = [(lmList[8][1]-stage_y)//bet_stone_y, (lmList[8][0]-stage_x)//bet_stone_x]
        #離す
            else:
                holding_flag = False
                holding_stone = [-1, -1]
                if moving_flag:
                    moving_flag = False
                    check_delete_flag = True
                    waiting_flag = True
        #スワップ処理
            if holding_flag and holding_stone[0]!=-1 and holding_stone[1]!=-1:
                holding_stone, swapped_flag = swap_cells(holding_stone)
            #ターマーの開始
                if not moving_flag and swapped_flag:
                    hold_start_time = now_time
                    moving_flag = True
                    hold_left = hold_time_limit
    #手が認識されない
        else:
            holding_flag = False
            moving_flag = False

#待ち状態のとき
    else:
        if finished_flag:
            if now_time - finished_time > 3:
                break
        if wait_delete_flag:
            if now_time - wait_start_time > delete_wait_time:
                wait_delete_flag = False

        elif wait_fall_flag:
            if now_time - wait_start_time > fall_wait_time:
                wait_fall_flag = False

        elif wait_yourattack_flag:
            if now_time - wait_start_time > yourattack_wait_time:
                wait_yourattack_flag = False
                yourattack = 0
            #敵を倒していたら終わり
                if enemy_hp == 0:
                    finished_flag = True
                    finished_time = now_time
                    winner = 0
                    threading.Thread(target=play_sound.play_win_sound).start()
                    continue
                wait_enemyattack_flag = True
                start_wait = now_time
                threading.Thread(target=play_sound.play_enemyattack_sound).start()
                enemyattack = calc_enemyattack()
                your_hp -= enemyattack
                if your_hp <= 0:
                    your_hp = 0
                      
        elif wait_enemyattack_flag:
            if now_time - start_wait > enemyattack_wait_time:
                wait_enemyattack_flag = False
            #倒されていたら終わり
                if your_hp == 0:
                    finished_flag = True
                    finished_time = now_time
                    winner = 1
                    threading.Thread(target=play_sound.play_lose_sound).start()
                    continue
                waiting_flag = False
                
        elif check_delete_flag:
            check_delete_flag = False
            for i in range(height):
                for j in range(width):
                    checked_delete[i][j] = False
            for y in range(height):
                for x in range(width):
                    if not check_delete_flag and not checked_delete[y][x]:
                        tmp = cells[y][x]
                        check_list.put([y, x])
                        checked_delete[y][x] = True
                        while not check_list.empty():
                            pos = check_list.get()
                            check_delete(pos[1], pos[0], cells[pos[0]][pos[1]])
                        if not delete_list.empty():
                            n = 0
                            while not delete_list.empty():
                                n += 1
                                pos = delete_list.get()
                                cells[pos[0]][pos[1]] = -1
                            check_delete_flag = True
                            combo += 1
                            threading.Thread(target=play_sound.play_delete_sound).start()
                            if tmp == 4:
                                deleted_heal_stone_num += n
                            else:
                                deleted_attack_stone_num += n
                            heal = calc_heal(deleted_heal_stone_num, combo)
                            yourattack = calc_yourattack(deleted_attack_stone_num, combo)
                            wait_delete_flag = True
                            check_fall_flag = True
                            wait_start_time = now_time
                            print_x = x
                            print_y = y

            if not check_delete_flag and not check_fall_flag:
                enemy_hp -= yourattack
                your_hp += heal
                if enemy_hp <= 0:
                    enemy_hp = 0
                if your_hp > your_max_hp:
                    your_hp = your_max_hp
                deleted_attack_stone_num = 0
                deleted_heal_stone_num = 0
                combo = 0
                heal = 0
                wait_yourattack_flag = True
                threading.Thread(target=play_sound.play_yourattack_sound).start()
                wait_start_time = now_time

        elif check_fall_flag:
            check_fall_flag = False
            for y in range(height-2, -1, -1):
                for x in range(width):
                    if cells[y][x] != -1 and cells[y+1][x] == -1:
                        cells[y+1][x], cells[y][x] = cells[y][x], -1
                        check_fall_flag = True
                        wait_fall_flag = True
                        wait_start_time = now_time
            for x in range(width):
                if cells[0][x] == -1:
                    cells[0][x] = random.randrange(max_type)
                    check_fall_flag = True
                    wait_fall_flag = True
                    wait_start_time = now_time
            
            if not check_fall_flag:
                check_delete_flag = True
                        
    img = draw_game(img)
    print_x = -1
    print_y = -1
    img = img[img_up:img_up+IMAGE_HEIGHT, img_left:img_left+IMAGE_WIDTH]
    enemy_tmp = draw_enemy(enemy)
    img = cv2.hconcat([img, enemy_tmp])
    img = cv2.resize(img, (WINDOW_WIDTH, WINDOW_HEIGHT))

    cv2.imshow("Image", img)
    if back_bgm:
        back_bgm = False
        thread_bgm = threading.Thread(target=play_sound.play_bgm)
        thread_bgm.start()
    cv2.waitKey(10)

cv2.destroyAllWindows()
sys.exit()