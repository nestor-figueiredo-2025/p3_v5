import pyautogui
import pyperclip
import time

from pynput.keyboard import Key, Controller
import time

keyboard = Controller()

# Limpeza área de transferência
# Abrir o prompt de comando
pyautogui.hotkey('win', 'v')
time.sleep(1)

pyautogui.press('tab')
time.sleep(0.5)
pyautogui.press('enter')
time.sleep(0.5)
keyboard.press(Key.up)
keyboard.release(Key.up)
pyautogui.press('enter')


