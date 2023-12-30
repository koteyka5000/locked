from cryptography.fernet import Fernet
from tkinter import *
from tkinter.messagebox import askyesno
import os, sys
from time import time
from typing import Literal
import getpass
from colorama import init, Fore

# Настройки
SKIP_FILES = ['.DS_Store']  # Файлы, которые нельзя зашифровать и расшифровать
NON_TEXT_FORMATS = ['jpeg', 'mp3', 'mov', 'mp4', 'jpg', 'png', 'JPG']  # форматы, для которых будут использоваться методы шифрования байтов
TEST_PASSWORD = 'pass'  # пароль для двойного нажатия control
CONSOLE_PASSWORD = ['Meta_L', 'Meta_L', 'x']
DEVELOPER_MODE = True
CONSOLE_SHORTCUTS = {'terminal': 'terminalModeAsk()'}

# Уже не настройки
FILE = os.path.basename(sys.argv[0])  # имя файла (locked) !НЕ МЕНЯТЬ!
refuseBlocking = False
refuseBlockingViaPassword = False
refuseBlockingReason = None
last_incorrect_password_key = None
last_time_control_keypress = 0

backup = None

backup_help_showed = False

times_name_clicked = 0
console_password_inputed = []
console_command_inputed = ''

confirmed_developer_mode = None


def general_test():
    '''
    Тестирует основные компоненты прогрыммы
    '''
    global backup
    # данные для тестирования:
    text_file = 'file.py'
    non_text_file = 'p.jpeg'
    password = 'qwerty1234'

    if text_file == FILE or non_text_file == FILE:
        print('нельзя шифровать сам locked')
        exit()

    if isLocked(text_file):
        print(f'сначала разблокируй {text_file}')
        exit()
    if isLocked(non_text_file):
        print(f'сначала разблокируй {non_text_file}')
        exit()

    passwordVar.set(password)
    filenameVar.set(text_file)

    try:
        Fernet(make_key())
    except:
        print('ошибка генерации ключа')
        exit()

    lock()

    if not isLocked(text_file):
        print(f'файл {text_file} не зашифровался')
        exit()

    unlock()

    if isLocked(text_file):
        print(f'файл {text_file} не расшифровался')
        exit()
            
    passwordVar.set(password)
    filenameVar.set(non_text_file)

    lock()

    if not isLocked(non_text_file):
        print(f'файл {non_text_file} не зашифровался')
        exit()
        
    unlock()

    if isLocked(non_text_file):
        print(f'файл {non_text_file} не расшифровался')
        exit()

    passwordVar.set('')
    filenameVar.set('')
    printuwu('test completed successfully', 'lime')
    backup = None
    print('TEST SUCCESS')


def make_key(password=None) -> str:
    '''
    Создаёт ключ для Fernet
    '''
    if password:
        key = password
    else:
        key = str(passwordVar.get())
    key = (key * 44)[:43] + '='
    return key

def encrypt_data(text:str, type:Literal['bytes']=None) -> str|None: 
    '''
    Зашифровывает переданный текст, если он в байтах то укажи это в параметре type
    '''
    if not type == 'bytes':  # Если перены не байты, то переводим в них
        text = text.encode()
    

    cipher_key = make_key()  # Генерируем ключ для шифровки
    try:  cipher = Fernet(cipher_key)
    except:
        printuwu('unable to create key with this passwrd.\nPasswrd contains prohibited char(s)')  # В норме не выводится, а перекрывается другим
        return

    encrypted_text = cipher.encrypt(text)  # Шифруем

    return encrypted_text.decode('utf-8')

def decrypt_data(text, type:Literal['bytes']=None) -> str|bytes|None:
    '''
    Расшифровывает переданный текст, если он в байтах то укажи это в параметре type

    return:\\
    str - засшифрованый текст\\
    bytes - зашифрованные байты\\
    None - ошибка ключа/пароля
    '''
    cipher_key = make_key()  # Создаём ключ
    try:  cipher = Fernet(cipher_key)
    except:
        return
        
    if type == 'bytes':
        try:
            decrypted_text = cipher.decrypt(text)  # Если нужны байты, то не переводим из них в str
        except:
            return
    else:
        try:
            decrypted_text = cipher.decrypt(text).decode('utf-8')
        except:
            return 
    
    return decrypted_text


def isLocked(filename:str) -> bool:
    '''
    Возвращает True, если файл заблокирован, или False, если он разблокирован
    '''
    if getFileFormat(filename) in NON_TEXT_FORMATS:  # Если файл не текстовый
        with open(filename, 'rb') as f:
            data = f.read()
            try:  # Если получается преобразовать в utf8, то значит зашифровано
                data = data.decode('utf-8')
                return True
            except:  # Если нет, то расшифровано
                return False
            
    else:
        with open(filename, 'r') as f:
            data = f.read()
            if data[:4] == 'gAAA':  # Если начинается с этих символов, то он зашифрован
                return True
            return False
        
def isUnlocked(filename:str) -> bool:
    '''
    Разблокирован ли файл
    '''
    return not isLocked(filename)

def getFileFormat(filename:str) -> str:
    '''
    Получить расширение файла (без точки)
    Пример: jpeg\\
    Для папки вернёт folder
    '''
    if '.' in filename:
        dotindex = filename.index('.')
        return filename[dotindex+1:]
    else:
        return 'folder'
    
def getFileName(filenamewithext) -> str|None:
    if '.' in filenamewithext:
        dotindex = filenamewithext.index('.')
        return filenamewithext[:dotindex]

def lockNonText(filename:str) -> None:
    '''
    Блокирует файл, не являющийся текстовым
    '''
    global backup
    with open(filename, 'rb') as f:
        data = f.read()  # Получаем данные из файла
        encrypted_data = encrypt_data(data, 'bytes')  # Зашифровываем их

        backup = data

    if filename == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        print('аварийный выход: попытка принудительной блокировки самого locked в lockNonText')
        exit()

    with open(filename, 'w') as f:
        f.write(encrypted_data)  # Перезаписываем файл зашифроваными данными
        printuwu('successful', '#00ff7f')

def unlockNonText(filename:str) -> None:
    '''
    Разблокирует файл, не являющийся текстовым
    '''
    global backup
    with open(filename, 'r') as f:
        data = f.read()  # Получаем данные из файла
        decrypted_data = decrypt_data(data, type='bytes')  # Расшифровывем полученные данные
        if decrypted_data is None:  # Если decrypt_data вернула 0, значит произошла ошибка пароля
            printuwu('incorrect passwrd')
            return
        
        backup = data

    with open(filename, 'wb') as f:
        f.write(decrypted_data)
        printuwu('successful', '#00ff00')

def lockText(filename:str) -> None:
    '''
    Блокирует текстовый файл
    '''
    global backup
    with open(filename, 'r') as f:
        data = f.read()  # Получаем данные из файла
        encrypted_data = encrypt_data(data)  # Зашифровываем эти данные
        
        if encrypted_data is None:
            return
        
        backup = data
    if filename == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        print('аварийный выход: попытка принудительной блокировки самого locked в lockText')
        exit()

    with open(filename, 'w') as f:
        f.write(encrypted_data)  # Перезаписываем файл с зашифроваными данными
        printuwu('successful', '#00ff7f')

def unlockText(filename:str) -> None:
    '''
    Разблокирует текстовый файл
    '''
    global backup
    with open(filename, 'r') as f:
        data = f.read()  # Получаем данные из файла
        decrypted_data = decrypt_data(data)  # Зашифровываем поулченные данные
        if decrypted_data is None:  # Если вернула None, значит ошибка пароля
            printuwu('incorrect passwrd')
            return
        
        backup = data

    with open(filename, 'w') as f:  # Открываем файл для перезаписи
        f.write(decrypted_data)  # Перезаписываем зашифрованными данными
        printuwu('successful', '#00ff00')

def lockFolder(foldername):
    '''
    Блокирует все файлы в папке
    '''
    for filename in os.listdir(f'{os.getcwd()}/{foldername}'):
        lock(f'{foldername}/{filename}', folderMode=True)

def unlockFolder(foldername):
    '''
    Разблокирует все файлы в папке
    '''
    for filename in os.listdir(f'{os.getcwd()}/{foldername}'):
        unlock(f'{foldername}/{filename}', folderMode=True)

def isFileAbleToCryptography(file:str, folderMode:bool, terminalMode:bool, mode:Literal['lock', 'unlock']):
    '''
    Можно ли разблокировать/блокировать файл прямо сейчас
    '''
    if file:
        filename = file
    else:
        filename = filenameVar.get()  # Получаем имя файла

    if refuseBlocking or refuseBlockingViaPassword:  # Если остановлена блокировка файлов (например когда попытка блокировки этого файла)
        if refuseBlockingReason:
            if terminalMode:
                return f'cryptography is currently unavailable.\n{refuseBlockingReason}'
            printuwu(f'cryptography is currently unavailable.\n{refuseBlockingReason}', color='#9933CC')
        else:
            if terminalMode:
                return 'cryptography is currently unavailable'
            printuwu('cryptography is currently unavailable', color='#9933CC')
        return False
    
    if not filename:
        if terminalMode:
            return 'name..?'
        printuwu('name..?')
        return False
    
    if not isFileExist(filename):
        if terminalMode:
            return 'file not found'
        printuwu('file not found')
        return False
    
    for skip_file in SKIP_FILES:
        if skip_file in filename:
            if not folderMode:
                if terminalMode:
                    return 'this file is skipped'
                printuwu('this file is skipped')
            return False

    if not passwordVar.get():  # Если не введён пароль
        if terminalMode:
            return 'passwrd..?'
        printuwu('passwrd..?')
        return False

    if not getFileFormat(filename) == 'folder':
        if mode == 'lock':
            if isLocked(filename):  # Если файл уже заблокирован
                if terminalMode:
                        return 'locked already'
                printuwu(f'locked already')
                return False
        elif mode == 'unlock':
            if isUnlocked(filename):  # Если файл уже заблокирован
                if terminalMode:
                    return 'unlocked already'
                printuwu('unlocked already')
                return False
        else:
            printuwu('unknown mode. check isFileAbleToCryptography')
            return False
    
    if filename == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        if terminalMode:
            return 'locked~ cant block itself!'
        printuwu('locked~ cant block itself!')
        return False

    return True


def lock(file=None, folderMode=False, terminalMode=False) -> None:
    '''
    Блокирует файл, перенаправляя в нужную функцию
    '''
    if file:
        filename = file
    else:
        filename = filenameVar.get()  # Получаем имя файла
    
    able = isFileAbleToCryptography(filename, folderMode, terminalMode, 'lock')
    if able != True:
        return able
    
    try:
        if getFileFormat(filename) == 'folder':
            lockFolder(filename)
            return
        
        if folderMode:
            printuwu(f'{getFileName(filename)}...')
            root.update()
        
        if getFileFormat(filename) in NON_TEXT_FORMATS:  # Если файл не текстовый, то перенаправляем в функцию, которая шифрует нетекстовые файлы
            lockNonText(filename)
            return
        else:
            lockText(filename)
    except:
        if backup:
            show_backup_help()
    
def unlock(file=None, folderMode=False, terminalMode=False):
    '''
    Разблокирует файл, перенаправляя в нужную функцию
    '''
    if file:
        filename = file
    else:
        filename = filenameVar.get()  # Получаем имя файла

    able = isFileAbleToCryptography(filename, folderMode, terminalMode, 'unlock')
    if able != True:
        return able
    
    try:
        if getFileFormat(filename) == 'folder':
            unlockFolder(filename)
            return
        
        if folderMode:
            printuwu(f'{getFileName(filename)}...')
            root.update()
        if getFileFormat(filename) in NON_TEXT_FORMATS:  # Если файл не текстовый
            unlockNonText(filename)
        else:
            unlockText(filename)
    except:
        if backup:
            show_backup_help()


def printuwu(text, color:str=None, extra:Literal[True, 'clear']=False) -> None:
    '''
    Выводит текст в специальное место программы слева снизу
    extra: True чтобы вывести в дополнительное место; clear чтобы очистить все поля вывода
    '''
    if extra == 'clear':
        OutputLabel.configure(text='')
        ExtraOutputLabel.configure(text='')
        return
    
    if not extra:
        OutputLabel.configure(text=text)
        if color:
            OutputLabel.configure(fg=color)
        else:
            OutputLabel.configure(fg='systemTextColor')  # Цвет темы в мак ос
    elif extra:
        ExtraOutputLabel.configure(text=text)
        if color:
            ExtraOutputLabel.configure(fg=color)
        else:
            ExtraOutputLabel.configure(fg='systemTextColor')  # Цвет темы в мак ос

def showHelp() -> None:
    '''
    Показывает справку в терминале
    '''
    lockedLabel.configure(text='check terminal')
    print('''\nlocked~
==Блокировка файлов==
Заблокировать: введи имя файла и пароль, нажми lock
Разблокировать: введи имя файла и пароль, нажми unlock
          
==Цвета==
          
name:
    лайм - всё хорошо
    красный - неверное имя файла
    фиолетовый - нельзя блокировать сам locked~

passwrd:
    лайм - отличный пароль
    оранжевый - хороший пароль
    зелёный - не очень надёжно, но ограничений на длинну пароля нет
          
          
!Если забыть пароль, то разблокировать будет невозможно (наверное)''')

def updFilenameEntryColor(*args) -> None:
    '''
    Изменяет цвет вводимого имени файла в зависимости от условий
    '''
    global refuseBlocking
    filename = filenameVar.get()

    if filename == FILE:  # Если ввели этот файл (сам locked)
        filenameEntry.configure(fg='#9933CC')
        printuwu('locked cant lock itself', color='#9933CC')
        refuseBlocking = True  # Останавливаем блокировку файлов, чтобы не заблокировать себя
        return

    autofill('check')

    if isFileExist(filename):
        filenameEntry.configure(fg='lime')
    else:
        filenameEntry.configure(fg='red')

    refuseBlocking = False  # В итоге возообновляем блокировку файлов

def updPasswordEntryColor(*args) -> None:
    '''
    Изменяет цвет вводимого пароля в зависимости от условий
    '''
    global last_incorrect_password_key, refuseBlockingViaPassword, refuseBlockingReason
    password = passwordVar.get()
    
    lenght = len(password)  # Получаем длинну пароля

    try:  # Пробуем создать ключ с паролем на момент ввода
        Fernet(make_key('a'+password))
    except:  # Если не получилось, то
        try:  # пробуем создать ключ с последним символом пароля (только что введённым)
            password_with_space = 'abc' + password # Если поле для ввода пустое, то будет ошибка. поэтому добаляем a в начало, чтобы ошибки не было
            Fernet(make_key(password_with_space[-1]))
        except:  # Если не получилось, то
            last_incorrect_password_key = password_with_space[-1]  # Запоминаем этот символ
        printuwu(f'incorrect symbol in the passwrd: {last_incorrect_password_key}', 'red')  # Выводим его
        passwordEntry.configure(fg='red')  # Делаем пароль красным
        refuseBlockingViaPassword = True
        refuseBlockingReason = f'incorrect symbol in the passwrd: {last_incorrect_password_key}'
        return
    else:
        if last_incorrect_password_key:
            printuwu('')  # Если всё хорошо, то убираем надпись
            last_incorrect_password_key = None
    
    if lenght >= 40:
        passwordEntry.configure(fg='red')
        printuwu('passwrd cant be longer than 40 symbols')
        refuseBlockingViaPassword = True
        refuseBlockingReason = 'the passwrd is too long'
        return

    if lenght <= 3:
        passwordEntry.configure(fg='green')  # Не очень надежный
    elif lenght <= 7:
        passwordEntry.configure(fg='orange')  # Хороший
    else:
        passwordEntry.configure(fg='lime')  # Отличный
    refuseBlockingViaPassword = False
    refuseBlockingReason = None

def isFileExist(file:str) -> bool:
    '''
    Возвращает True если файл/папка/файл по определённому пути существует, иначе Falase
    '''
    if file == '' or file == '/':
        return False
    if getFileFormat(file) == 'folder':
        if file in os.listdir(os.getcwd()):
            return True
        return False
    try:
        open(file, 'r')
    except:  # Если не найден файл
        return False
    else:
        return True

def autofill(action:Literal['replace', 'check']) -> None:
    '''
    При action=replace автоматически дополняет введённое имя файла\\
    При action=check проверяет, если ли доступные автозамены 
    '''
    filename = filenameVar.get().replace('.', '')
    autofill_found = False

    files = os.listdir(os.getcwd())
    for file in files:
        if file == FILE:
            continue
        
        if file.startswith(filename):
            autofill_found = True
            if action == 'replace':
                filenameVar.set(f'{file}')
                if getFileFormat(file) == 'folder':
                    autofillLabel.configure(text='')
            elif action == 'check':
                if getFileFormat(file) == 'folder':
                    autofillLabel.configure(text=f'{file}')
                else:
                    autofillLabel.configure(text=f'{getFileName(file)}\n.{getFileFormat(file)}')
            else:
                print(f'incorrect action: {action}')

    if not autofill_found or not filename:
        autofillLabel.configure(text='')

def insertTestPassword():
    """
    Вводит тестовый пароль в строку ввода пароля (быстро нажми control 2 раза)
    """
    global last_time_control_keypress
    current_time = time()
    if current_time - last_time_control_keypress >= 1:
        last_time_control_keypress = time()
    else:
        passwordVar.set(TEST_PASSWORD)
        last_time_control_keypress = 0

def preventClosing() -> None:
    """
    Функция, перехватывающая попытку закрыть окно (но не cmd+q) при поломке файла, чтобы случайно не потерять бэкап сломаного файла
    """
    print('\n\n\n\nIf you will exit now you will lose your backup so you wont be able to restore it.\nTo stay in locked and continue recovering file press Enter in the terminal.\nTo close window and LOSE YOUR FILE enter "lose" and press Enter.')
    action = input('so: ')
    if action == 'lose':
        root.destroy()
        root.protocol("WM_DELETE_WINDOW", lambda x=None: exit())
        exit()

def removeFocus():
    """
    Убирает фокусировку ввода с Entry
    """
    root.focus()

def show_backup_help():
    """
    Запустить предупреждение о поломке файла и необходимости его восстановить, открыть меню бэкапа, добавить подтверждение для выхода
    """
    global backup_help_showed
    lockedLabel.configure(text='ВНИМАНИЕ! Похоже, что файл сломался,\nсейчас необходимо следовать инструкциям\nснизу приложения, чтобы восстановить файл', bg='red')

    helpLabel.unbind("<Enter>")
    helpLabel.unbind("<Leave>")
    helpLabel.unbind("<Button-1>")
    backup_help_showed = True
    root.protocol("WM_DELETE_WINDOW", preventClosing)
    backupFile()

def remove_backup_help():
    """
    Убрать предупреждение о поломке файла
    """
    global backup_help_showed
    lockedLabel.configure(text='locked~', bg='systemWindowBackgroundColor')

    helpLabel.bind("<Button-1>", lambda e: showHelp())
    helpLabel.bind("<Enter>", lambda e: lockedLabel.configure(text='click to show help\nright click to backup'))
    helpLabel.bind("<Leave>", lambda e: lockedLabel.configure(text='locked~'))
    backup_help_showed = False
    root.protocol("WM_DELETE_WINDOW", exit)

def _backup_run(e=None):
    """
    Пробует восстановить файл из бэкапа
    """
    filename = filenameVar.get()
    if type(backup) == str:
        with open(filename, 'w') as f:
            f.write(backup)
    
    elif type(backup) == bytes:
        with open(filename, 'wb') as f:
            f.write(backup)

    _backup_cancel()
    if backup_help_showed:
        remove_backup_help()

    printuwu(f'successfully backuped {filename}\nfrom [{backup[:5]} ...]', 'lime')
    return f'successfully backuped {filename}\nfrom [{backup[:5]} ...]'

def _backup_dump(e=None):
    """
    Создать файл и записать в него бэкап, на случай если по какой-либо причине не получилось восстановить файл.
    """
    try:
        with open('backup_dump_bytes', 'xb') as f:
            f.write(backup)
    except:
        with open('backup_dump_text', 'x') as f:
            f.write(backup)
    _backup_cancel()
    if backup_help_showed:
        remove_backup_help()

    printuwu(f'successfully dumped\n[{backup.replace("\n", " ")[:10]} ...]', 'lime')
    return f'successfully dumped\nfrom {backup.replace("\n", " ")[:10]} ..', 'lime'

def _backup_delete_confirm(e=None):
    """
    Удаляет текущий бэкап без подтверждения
    """
    global backup
    backup = None
    printuwu('backup successfully deleted', 'red')
    _backup_cancel()

    if backup_help_showed:
        remove_backup_help()
    return 'backup successfully deleted'

def _backup_delete_aks(e=None):
    """
    Запрашивает подтверждение, точно ли удалить бэкап
    """
    _backup_cancel()

    printuwu('press 0 to CANCEL and keep backup\npress 1 to CONFIRM and DELETE backup', 'red')

    root.bind('0', _backup_cancel)
    root.bind('1', _backup_delete_confirm)

def _backup_cancel(e=None):
    '''
    Сбросить все бинды для бэкапа и очистить поля вывода
    '''
    root.unbind('<Meta_L><0>')        
    root.unbind('0')
    root.unbind('1')
    root.unbind('2')
    printuwu('', extra='clear')
    
def backupFile():
    """
    Выводит информацию о бэкапе
    """
    filename = filenameVar.get()
    removeFocus()

    if backup is None:
        printuwu('there is no backup...')
        return

    if not filename:
        printuwu(f'enter filename, then press\nagain to backup file')
        return
    
    try:
        open(filename)
    except:
        printuwu(f'enter filename, then press\nagain to backup file')
        return
    
    printuwu(f'press 0 to cancel | press command+D to delete backup', 'orange', True)
    printuwu(f'НАЖМИ 1 ЧТОБЫ ВОССТАНОВИТЬ [{filename}]\npress 2 to dump backup [{backup[:5]}...]', 'lime')

    root.bind('<Meta_L><d>', _backup_delete_aks)        
    root.bind('0', _backup_cancel)
    root.bind('1', _backup_run)
    root.bind('2', _backup_dump)

def _consoleClearInputedCommand(e=None):
    """
    Очистить введёную в консоль команду, но не обновлять поле для ввода
    """
    global console_command_inputed

    console_command_inputed = ''

def _consoleExecuteCommand(mode:Literal['exec', 'eval']):
    """
    Выполнить введёную команду при определённых условиях
    """
    global confirmed_developer_mode
    if not DEVELOPER_MODE:
        printuwu('access denied', 'red')
        return
    
    if confirmed_developer_mode is None:
        answer = askyesno('warning', f'Неправильное использование команд может сломать программу и/или ваши файлы, или даже больше. Продолжай на свой страх и риск. Запустить [{console_command_inputed}] и все последующие команды в этом сеансе?')
        confirmed_developer_mode = answer

    if confirmed_developer_mode == False:
        printuwu('access denied', 'red')
        _consoleClearInputedCommand()
        return
    
    if not console_command_inputed:
        return
    
    try:
        if mode == 'eval':
            result = eval(console_command_inputed)
        elif mode == 'exec':
            result = exec(console_command_inputed)
        else:
            printuwu(f'incorrect mode: {mode}', 'red')
            return
    except Exception as e:
        printuwu(f'{e}', 'red')
    else:
        printuwu(result, 'lime')
    finally:
        _consoleClearInputedCommand()

def _consoleAddCharToCommand(e):
    """
    Добавляет нажатую клавишу в консоль
    """
    global console_command_inputed

    char = e.char
    keysym = e.keysym
    if keysym == 'Escape':
        _consoleReset()
        console_command_inputed = ''
        return
    elif keysym == 'BackSpace':
        if console_command_inputed:
            console_command_inputed = console_command_inputed[:-1]
        printuwu(f'{console_command_inputed}', 'orange')
        return
    elif keysym == 'Return':
        _consoleExecuteCommand('eval')
        return
    elif keysym == 'Shift_R':
        _consoleExecuteCommand('exec')
        return
    
    console_command_inputed += char

    if console_command_inputed in CONSOLE_SHORTCUTS:
        console_command_inputed = CONSOLE_SHORTCUTS[console_command_inputed]

    printuwu(f'{console_command_inputed}', 'orange')

add_char_to_command_ID = None  # To unbind in the future
def _consoleRun(e=None):
    """
    Запустить консоль
    """
    global add_char_to_command_ID
    _consoleReset()
    printuwu('enter command | esc to exit', 'orange', True)
    
    add_char_to_command_ID = root.bind('<KeyPress>', _consoleAddCharToCommand)

def _consoleAddCharToPassword(e=None):
    """
    Добавить нажатую клавишу к полю ввода пароля
    """
    global console_password_inputed

    char = e.keysym
    if char == 'Escape':
        _consoleReset()
        return
    elif char == 'BackSpace':
        if console_password_inputed:
            console_password_inputed.pop()
        printuwu(f'{' '.join(console_password_inputed)}', 'orange')
        return
    
    console_password_inputed.append(char)

    printuwu(f'{' '.join(console_password_inputed)}', 'orange')

    if console_password_inputed == CONSOLE_PASSWORD:
        console_password_inputed.clear()
        _consoleRun()


    
add_char_to_password_ID = None  # To unbind in the future
def _consoleEnterPassword():
    """
    Запросить пароль для консоли
    """
    global add_char_to_password_ID
    _consoleReset()

    printuwu('enter console passwrd | esc to exit', 'orange', True)

    add_char_to_password_ID = root.bind('<KeyPress>', _consoleAddCharToPassword)

def _consoleReset(e=None):
    """
    Разбиндить все клавиши, используемые для консоли и очистить поле вывода
    """
    try:
        root.unbind('0')
        root.unbind('1')
    except:
        pass

    try:
        root.unbind('<KeyPress>', add_char_to_password_ID)
    except:
        pass

    try:
        root.unbind('<KeyPress>', add_char_to_command_ID)
    except:
        pass
    
    printuwu('', extra='clear')

def colsoleOpenAks():
    """
    Спросить, уверен ли пользователь что он хочет открыть консоль
    """
    global times_name_clicked
    if times_name_clicked < 2:
        times_name_clicked += 1
        return
    removeFocus()
    printuwu('u are trying to open developer console. It is dangerous!', 'orange', True)
    printuwu('Press [0] to cancel and quit console\nPress [1] to enter password and run console')
    root.bind('0', lambda e: _consoleReset())
    root.bind('1', lambda e: _consoleEnterPassword())

class CustomCommandsHandler:
    def __init__(self) -> None:
        self.COMMANDS = ['lock', 'unlock', 'backup', 'help']

    def run(self, command:str):
        command, *args = command.split()
        if command in self.COMMANDS:
            return eval(f'self._{command}({args})')
        return 'undefined command. You can type "help"'
        
    def __crypto(self, mode:Literal['lock', 'unlock'], args):
        try: 
            file = args[0]
            password = args[1]
        except:
            if mode == 'lock':
                return 'usage: lock <file> <password>'
            else:
                return 'usage: unlock <file> <password>'
        
        passwordVar.set(password)
        filenameVar.set(file)
        
        if mode == 'lock':
            result = lock(terminalMode=True)
        elif mode == 'unlock':
            result = unlock(terminalMode=True)

        passwordVar.set('')
        filenameVar.set('')
        if result is None:
            return 'success'
        return result
    def _help(self, *args):
        return """
commands:
lock <file> <password>
unlock <file> <password>
backup <recovery/dump/delete>
help"""

    def _lock(self, args):
        return self.__crypto('lock', args)
    
    def _unlock(self, args):
        return self.__crypto('unlock', args)
    
    def _backup(self, args):
        try:
            file = args[0]
            mode = args[1]
        except:
            return 'usage: backup <file> <recovery/dump/delete>'
        filenameVar.set(file)
        match mode:
            case 'recovery':
                return _backup_run()
            case 'dump':
                return _backup_dump()
            case 'delete':
                if input('this will delete backup. Are you sure? (y/n)') == 'y':
                    return _backup_delete_confirm()
        
        
def _terminalHideWindow():
    try:
        root.withdraw()
    except:
        pass

def _terminalStartAdmin():
    init(autoreset=True)
    _terminalReset()
    _terminalHideWindow()

    USERNAME = getpass.getuser()
    print(f'Admin terminal mode started.\nType {Fore.CYAN}exit{Fore.RESET} to exit terminal and return to window mode\n\
type "{Fore.CYAN}do ...{Fore.RESET}" to execute command, or "{Fore.CYAN}eval ...{Fore.RESET}" to evaluate it. you can also just enter command to evaluate it')
    while True:
        print()
        inp = input(f'{Fore.LIGHTRED_EX}{USERNAME}@locked~ $ {Fore.RESET}')
        result = None
        if inp == 'exit':
            break

        try:
            if inp[:3] == 'do ':
                exec(inp[3:])
            elif inp[:5] == 'eval ':
                result = eval(inp[5:])
            else:
                result = eval(inp)

            if result:
                    print(f'{Fore.LIGHTCYAN_EX}{result}')
        except Exception as e:
            print(f'{Fore.RED}{e}')
    print(f'{Fore.LIGHTMAGENTA_EX}closing...')
    _terminalReset()
    root.wm_deiconify()


def _terminalStartUser():
    commandsHandler = CustomCommandsHandler()
    init(autoreset=True)
    _terminalReset()
    _terminalHideWindow()

    USERNAME = getpass.getuser()
    print(f'User terminal mode started.\nType {Fore.CYAN}exit{Fore.RESET} to exit terminal and return to window mode\n\
commands: {Fore.CYAN}lock{Fore.RESET}, {Fore.CYAN}unlock{Fore.RESET}, {Fore.CYAN}backup{Fore.RESET}')
    
    while True:
        print()
        inp = input(f'{Fore.LIGHTBLUE_EX}{USERNAME}@locked~ % {Fore.RESET}')
        if inp == 'exit':
            break
        result = commandsHandler.run(inp)
        print(f'{Fore.CYAN}{result}')

    print(f'{Fore.LIGHTMAGENTA_EX}closing...')
    _terminalReset()
    root.wm_deiconify()

def _terminalChoose():
    _terminalReset()
    if not DEVELOPER_MODE:
        _terminalStartUser()
        return
    
    printuwu('Which terminal do u want to use?', extra=True)
    printuwu('Press [1] to start administrator console\nPress [2] to start default user console')

    root.bind('1', lambda e: _terminalStartAdmin())
    root.bind('2', lambda e: _terminalStartUser())


def _terminalReset():
    root.unbind('0')
    root.unbind('1')
    root.unbind('2')
    printuwu('', extra='clear')

def terminalModeAsk():
    removeFocus()
    printuwu('Open locked~ in the terminal? ', 'orange', True)
    printuwu('Press [0] to cancel and stay in tkinter\nPress [1] to start terminal mode')

    root.bind('0', lambda e: _terminalReset())
    root.bind('1', lambda e: _terminalChoose())

def centerwindow(win):
    """
    💀💀💀💀💀💀💀💀💀💀💀
    центрирует окно ткинтер
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

root = Tk()
root.geometry('300x200')
root.title(' ')
root.resizable(False, False)
root.after(50)
root.iconify()
root.update()
centerwindow(root)


filenameVar = StringVar(root)
passwordVar = StringVar(root)

autofillLabel = Label(root, fg='#ffc0cb', font='Arial 12', justify='left')
autofillLabel.place(x=250, y=56)

lockedLabel = Label(root, text='locked~')
lockedLabel.pack()

Button(root, text='lock', command=lock).place(x=5, y=120)
Button(root, text='unlock', command=unlock).place(x=220, y=120)

nameLabel = Label(root, text='name')
nameLabel.place(x=5, y=63)
nameLabel.bind("<Button-1>", lambda e: colsoleOpenAks())

Label(root, text='passwrd').place(x=5, y=93)

filenameEntry = Entry(root, textvariable=filenameVar)
filenameEntry.place(x=60, y=60)
filenameVar.trace_add('write', updFilenameEntryColor)  # При записи каждой новой буквы вызываетя обновление цвета для имени файла

passwordEntry = Entry(root, textvariable=passwordVar, fg='red')
passwordEntry.place(x=60, y=90)
passwordVar.trace_add('write', updPasswordEntryColor)  # аналогично

OutputLabel = Label(root, text='', justify='left')
OutputLabel.place(x=5, y=160)

ExtraOutputLabel = Label(root, text='', justify='left', font='Arial 12')
ExtraOutputLabel.place(x=5, y=146)

root.bind('<Tab>', lambda e: autofill('replace'))
root.bind('<Control_L>', lambda e: insertTestPassword())
root.bind('<Alt_L>', lambda e: root.focus())

helpLabel = Label(root, text='?', relief='flat')
helpLabel.place(x=281, y=174)
helpLabel.bind("<Button-1>", lambda e: showHelp())  # При нажатии на вопрос
helpLabel.bind("<Button-2>", lambda e: backupFile())
helpLabel.bind("<Enter>", lambda e: lockedLabel.configure(text='click to show help\nright click to backup'))  # При наведении на вопрос
helpLabel.bind("<Leave>", lambda e: lockedLabel.configure(text='locked~'))  # При уведении курсора с вопроса

terminalLabel = Label(root, text='term', relief='flat')
terminalLabel.place(x=0, y=0)
terminalLabel.bind("<Button-1>", lambda e: terminalModeAsk()) 
# тестирование
# general_test()

root.mainloop()