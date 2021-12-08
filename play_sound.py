from playsound import playsound
import threading

def play_swap_sound():
    playsound("sound/swap.mp3")

def play_delete_sound():
    playsound("sound/delete.mp3")

def play_yourattack_sound():
    playsound("sound/yourattack.mp3")

def play_enemyattack_sound():
    playsound("sound/enemyattack.mp3")
    
def play_win_sound():
    playsound("sound/win.mp3")

def play_lose_sound():
    playsound("sound/lose.mp3")

def play_bgm():
    playsound("sound/bgm.mp3")