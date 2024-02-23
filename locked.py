from cryptography.fernet import Fernet
from tkinter import *
from tkinter.messagebox import askyesno, showinfo, showwarning
import os, sys
from time import time
from typing import Literal
import getpass
from colorama import init, Fore
import json
import hashlib
import keyring
import ctypes

# Настройки
SKIP_FILES = ['.DS_Store', 'auth']  # Файлы, которые нельзя зашифровать и расшифровать
NON_TEXT_FORMATS = ['jpeg', 'mp3', 'mov', 'mp4', 'jpg', 'png', 'JPG']  # форматы, для которых будут использоваться методы шифрования байтов
TEST_PASSWORD = 'pass'  # пароль для двойного нажатия control
CONSOLE_PASSWORD = ['Meta_L', 'Meta_L', 'x']
DEVELOPER_MODE = True
CONSOLE_SHORTCUTS = {'terminal': 'terminalModeAsk()'}
DELETE_SAVED_PASSWORD_AFTER_UNLOCK = True

# kali, normal
ADMIN_TERMINAL_SKIN = 'kali'

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

keychain_password_inputed = ''
keychain_password = None
keychain_autofill = [] # при включнной дополнительной защите используется дял показа файлов к которым соханён пароль

krndata = keyring.get_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS')
if not krndata:
    keyring.set_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS', '0')


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
    fileVar.set(text_file)

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
    fileVar.set(non_text_file)

    lock()

    if not isLocked(non_text_file):
        print(f'файл {non_text_file} не зашифровался')
        exit()
        
    unlock()

    if isLocked(non_text_file):
        print(f'файл {non_text_file} не расшифровался')
        exit()

    passwordVar.set('')
    fileVar.set('')
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

def encrypt_data(text:str, type:Literal['bytes']=None, key=None) -> str|None: 
    '''
    Зашифровывает переданный текст, если он в байтах то укажи это в параметре type
    '''
    if not type == 'bytes':  # Если перены не байты, то переводим в них
        text = text.encode()
    
    if key:
        cipher_key = key
    else:
        cipher_key = make_key()  # Генерируем ключ для шифровки

    try:
        cipher = Fernet(cipher_key)
    except:
        printuwu('unable to create key with this passwrd.\nPasswrd contains prohibited char(s)')  # В норме не выводится, а перекрывается другим
        return

    encrypted_text = cipher.encrypt(text)  # Шифруем

    return encrypted_text.decode('utf-8')

def decrypt_data(text, type:Literal['bytes']=None, key=None) -> str|bytes|None:
    '''
    Расшифровывает переданный текст, если он в байтах то укажи это в параметре type

    return:\\
    str - засшифрованый текст\\
    bytes - зашифрованные байты\\
    None - ошибка ключа/пароля
    '''
    if key:
        cipher_key = key
    else:
        cipher_key = make_key()  # Создаём ключ
    try:  cipher = Fernet(cipher_key)
    except:
        return
    
    try:
        decrypted_text = cipher.decrypt(text)  # Если нужны байты, то не переводим из них в str
    except:
        return
        
    if not type == 'bytes':
        decrypted_text = decrypted_text.decode('utf-8')
    
    return decrypted_text


def isLocked(file:str) -> bool:
    '''
    Возвращает True, если файл заблокирован, или False, если он разблокирован
    '''
    if getFileFormat(file) in NON_TEXT_FORMATS:  # Если файл не текстовый
        with open(file, 'rb') as f:
            data = f.read()
            try:  # Если получается преобразовать в utf8, то значит зашифровано
                data = data.decode('utf-8')
                return True
            except:  # Если нет, то расшифровано
                return False
            
    else:
        with open(file, 'r') as f:
            data = f.read()
            if data[:4] == 'gAAA':  # Если начинается с этих символов, то он зашифрован
                return True
            return False
        
def isUnlocked(file:str) -> bool:
    '''
    Разблокирован ли файл
    '''
    return not isLocked(file)

def getFileFormat(file:str) -> str:
    '''
    Получить расширение файла (без точки)
    Пример: jpeg\\
    Для папки вернёт folder
    '''
    if '.' in file:
        dotindex = file.index('.')
        return file[dotindex+1:]
    else:
        return 'folder'
    
def getFileName(file) -> str|None:
    if '.' in file:
        dotindex = file.index('.')
        return file[:dotindex]

def lockNonText(file:str) -> None:
    '''
    Блокирует файл, не являющийся текстовым
    '''
    global backup
    with open(file, 'rb') as f:
        data = f.read()  # Получаем данные из файла
        encrypted_data = encrypt_data(data, 'bytes')  # Зашифровываем их

        backup = data

    if file == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        print('аварийный выход: попытка принудительной блокировки самого locked в lockNonText')
        exit()

    with open(file, 'w') as f:
        f.write(encrypted_data)  # Перезаписываем файл зашифроваными данными
        printuwu('successful', '#00ff7f')

def unlockNonText(file:str) -> None:
    '''
    Разблокирует файл, не являющийся текстовым
    '''
    global backup
    with open(file, 'r') as f:
        data = f.read()  # Получаем данные из файла
        decrypted_data = decrypt_data(data, type='bytes')  # Расшифровывем полученные данные
        if decrypted_data is None:  # Если decrypt_data вернула 0, значит произошла ошибка пароля
            printuwu('incorrect passwrd')
            return
        
        backup = data

    with open(file, 'wb') as f:
        f.write(decrypted_data)
        printuwu('successful', '#00ff00')

def lockText(file:str) -> None:
    '''
    Блокирует текстовый файл
    '''
    global backup
    with open(file, 'r') as f:
        data = f.read()  # Получаем данные из файла
        encrypted_data = encrypt_data(data)  # Зашифровываем эти данные
        
        if encrypted_data is None:
            return
        
        backup = data
    if file == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        print('аварийный выход: попытка принудительной блокировки самого locked в lockText')
        exit()

    with open(file, 'w') as f:
        f.write(encrypted_data)  # Перезаписываем файл с зашифроваными данными
        printuwu('successful', '#00ff7f')

def unlockText(file:str) -> None:
    '''
    Разблокирует текстовый файл
    '''
    global backup
    with open(file, 'r') as f:
        data = f.read()  # Получаем данные из файла
        decrypted_data = decrypt_data(data)  # Зашифровываем поулченные данные
        if decrypted_data is None:  # Если вернула None, значит ошибка пароля
            printuwu('incorrect passwrd')
            return
        
        backup = data

    with open(file, 'w') as f:  # Открываем файл для перезаписи
        f.write(decrypted_data)  # Перезаписываем зашифрованными данными
        printuwu('successful', '#00ff00')

def lockFolder(folder):
    '''
    Блокирует все файлы в папке
    '''
    for file in os.listdir(f'{os.getcwd()}/{folder}'):
        lock(f'{folder}/{file}', folderMode=True)

def unlockFolder(folder):
    '''
    Разблокирует все файлы в папке
    '''
    for file in os.listdir(f'{os.getcwd()}/{folder}'):
        unlock(f'{folder}/{file}', folderMode=True)

def isFileAbleToCryptography(file:str, folderMode:bool, terminalMode:bool, mode:Literal['lock', 'unlock']):
    '''
    Можно ли разблокировать/блокировать файл прямо сейчас
    '''

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
    
    if not file:
        if terminalMode:
            return 'name..?'
        printuwu('name..?')
        return False
    
    if not isFileExist(file):
        if terminalMode:
            return 'file not found'
        printuwu('file not found')
        return False
    
    for skip_file in SKIP_FILES:
        if skip_file in file:
            if folderMode:
                return False
            
            if terminalMode:
                if mode == 'lock':
                    return 'you cant lock it'
                elif mode == 'unlock':
                    return 'you cant unlock it'
                
            if mode == 'lock':
                printuwu('you cant lock it')
            elif mode == 'unlock':
                printuwu('you cant unlock it')
            return

    if not passwordVar.get():  # Если не введён пароль
        if terminalMode:
            return 'passwrd..?'
        printuwu('passwrd..?')
        return False

    if not getFileFormat(file) == 'folder':
        if mode == 'lock':
            if isLocked(file):  # Если файл уже заблокирован
                if terminalMode:
                        return 'locked already'
                printuwu(f'locked already')
                return False
        elif mode == 'unlock':
            if isUnlocked(file):  # Если файл уже заблокирован
                if terminalMode:
                    return 'unlocked already'
                printuwu('unlocked already')
                return False
        else:
            printuwu('unknown mode. check isFileAbleToCryptography')
            return False
    
    if file == FILE: # Если каким-то чудом проскочило имя самого locked, то аварийно выходим 
        if terminalMode:
            return 'locked~ cant block itself!'
        printuwu('locked~ cant block itself!')
        return False

    return True


def lock(file=None, folderMode=False, terminalMode=False) -> None:
    '''
    Блокирует файл, перенаправляя в нужную функцию
    '''
    if file is None:
        file = fileVar.get()  # Получаем имя файла
    
    able = isFileAbleToCryptography(file, folderMode, terminalMode, 'lock')
    if able != True:
        return able
    
    if keychain_password: # если аутенфицировались в keychain, то будет сохранён пароль
        if isExtraSecurityEnabled():
            printuwu('synchronization with KeyChain...', 'pink', extra=True)
            root.update()
        _keychainAddFileAndPassword(file, passwordVar.get())
    if isExtraSecurityEnabled():
        printuwu('', extra='clearextra')

    autofillLabel.configure(text='')

    try:
        if getFileFormat(file) == 'folder':
            lockFolder(file)
            return
        
        if folderMode:
            printuwu(f'{getFileName(file)}...')
            root.update()
        
        if getFileFormat(file) in NON_TEXT_FORMATS:  # Если файл не текстовый, то перенаправляем в функцию, которая шифрует нетекстовые файлы
            lockNonText(file)
            return
        else:
            lockText(file)
    except:
        if backup:
            show_backup_help()
    
def unlock(file=None, folderMode=False, terminalMode=False):
    '''
    Разблокирует файл, перенаправляя в нужную функцию
    '''
    if file is None:
        file = fileVar.get()  # Получаем имя файла

    able = isFileAbleToCryptography(file, folderMode, terminalMode, 'unlock')
    if able != True:
        return able
    
    if keychain_password:
        if DELETE_SAVED_PASSWORD_AFTER_UNLOCK:
            if isExtraSecurityEnabled():
                printuwu('synchronization with KeyChain...', 'pink', extra=True)
                root.update()
            _keychainRemoveFileAndPassword(file, keychain_password)
    if isExtraSecurityEnabled():
        printuwu('', extra='clearextra')

    autofillLabel.configure(text='')

    try:
        if getFileFormat(file) == 'folder':
            unlockFolder(file)
            return
        
        if folderMode:
            printuwu(f'{getFileName(file)}...')
            root.update()
        if getFileFormat(file) in NON_TEXT_FORMATS:  # Если файл не текстовый
            unlockNonText(file)
        else:
            unlockText(file)
    except:
        if backup:
            show_backup_help()


def printuwu(text, color:str=None, extra:Literal[True, 'clear', 'clearextra']=False) -> None:
    '''
    Выводит текст в специальное место программы слева снизу
    extra: True чтобы вывести в дополнительное место; clear чтобы очистить все поля вывода \\
    // Мне кажется это вообще тут самая главная функция 💀💀💀💀💀💀💀💀💀💀
    '''
    if extra == 'clear':
        OutputLabel.configure(text='')
        ExtraOutputLabel.configure(text='')
        return
    elif extra == 'clearextra':
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
==БЛОКИРОВКА ФАЙЛОВ==
Введи имя файла/относительный путь к нему и пароль, нажми lock / unlock
          

==ЦВЕТА==
          
name:
    лайм - всё хорошо
    красный - неверное имя файла
    фиолетовый - нельзя блокировать сам locked~
          

==БЭКАПЫ==
Если при блокироваке/разблокировке файла произошла какая-либо ошибка и он очистился, то его всё ещё можно восстановить (не закрывай locked~ в таком случае). Для этого введи имя этого файла в name если оно не введено, пароль вводить не надо. После этого следует нажать на вопросительный знак справа снизу ПКМ, после чего откроется меню бэкапа, и нужно будет выбрать действие нажатием клавиши:

[0] Отмена, выход из меню бэкапа (однако бэкап сохранится в оперативной памяти)
[1] Восстановить файл из текущего бэкапа
[2] Записать данные бэкапа в новый файл, на случай если по каким-либо причинам не удаётся восстановить сам файл
[Command] + [D] Безвозвратно далить бэкап, после этого восстановление файла станет невозможным.

          
==КОНСОЛЬ==
          
Чтобы открыть мини-консоль прямо в окне locked~ необходимо три раза нажать на текст "name". После этого нужно выбрать действие:
[0] Отмена, закрыть консоль
[1] Ввести пароль и открыть консоль
          
При нажатии [1] необходимо будет ввести пароль от консоли, который был задан в "CONSOLE_PASSWORD"
После этого откроется консоль. Для того, чтобы убрать фокусоровку с полей ввода нажми [option]
Для того, чтобы выполнить exec введёной команды нажми правый Shift
Чтобы выполнить eval команды нажми [Enter]
Консоль работает примерно как консоль питона
Для выхода нажми [esc]

Если вышла надпись access denied, значит либо не включен режим разработчика, либо было нажато "нет" в всплывающем окне с подтверждением намерения.

          
==ТЕРМИНАЛ==

В locked~ есть режим работы в терминале. Для его включения нужно нажать на текст "term" слева сверху.
После этого будет предложен выбор:
[0] Отменить и остаться в Tkinter
[1] Запустить режим терминала

Если включен режим разработчика, то будет предложено выбрать терминал: админский с полным доступом к питону или пользовательский, в котором есть только заготовленные команды. 

В режиме админа можно вводить любые команды, поддерживаемые питоном
Для выполнения eval команды достаточно просто ввести её и нажать [Enter]
Для выполнения exec команды нужно добавить перед ней "do". Пример: do a = 5. 
          
В режиме пользователя можно вводить только заранее заготовленные команды, например для блокировки и разблокировки файла
Для получения списка команд и метода их использования введи "help".
          
Для выхода из режима терминала введи "exit"
          
==СВЯЗКА КЛЮЧЕЙ==

keychain! Система, которая может запомнить и безопасно, зашифровано хранить введёные пароли к файлам для их дальнейшего просмотра или быстрого автозаполнения. Для всего этого необходимо сначала создать связку ключей.

Чтобы сделать это достаточно нажать на open keychain слева сверху, после чего создать главный пароль, с помощью которого будет шифроваться вся связка ключей. Если его забыть, то восстановить сохранёные пароли будет невозможно. Данный пароль никогда не сохраняется на диске, поэтому при закрытии программы его точно нигде не останется. Однако он может быть временно сохранён в переменной для доступа к автозаполнению и сохранению новых паролей. 

Для этого нужно нажать на auth keychain слева сверху. После этого нужно будет ввести свой главный пароль от связки ключей и нажать [Enter]. При вводе неверного пароля он подсветится красным. При вводе правильного пароля надпись "auth keychain" станет зелёной, что означает успешный вход в связку ключей и доступа к автозаполнению старых паролей, сохранению новых и беспарольному доступу к просмотру сохранёных паролей, ведь главный пароль сохранён в переменной
          
Чтобы выйти из связки ключей достаточно нажать на зелёную надпись auth keychain и подтвердить действие нажатием [1]. После выхода главный пароль удаляется из переменной, и автозаполнение с сохранением паролей становится недоступным. Выход не повлияет на сохранёные пароли и данные.
          
(При нажатии на "open keychain" открываются пароли, но авторизация не сохраняется, Чтобы авторизоваться нужно нажать на auth keychain)

''')

def updFileEntryColor(*args) -> None:
    '''
    Изменяет цвет вводимого имени файла в зависимости от условий
    '''
    global refuseBlocking
    file = fileVar.get()

    if file == FILE:  # Если ввели этот файл (сам locked)
        fileEntry.configure(fg='#9933CC')
        printuwu('locked cant lock itself', color='#9933CC')
        refuseBlocking = True  # Останавливаем блокировку файлов, чтобы не заблокировать себя
        return

    autofill('check')

    if isFileExist(file):
        fileEntry.configure(fg='lime')
    else:
        fileEntry.configure(fg='red')

    refuseBlocking = False  # В итоге возообновляем блокировку файлов

def updPasswordEntryColor(*args) -> None:
    '''
    Изменяет цвет вводимого пароля в зависимости от условий, проверяет его на действительность и возможность использования как пароль
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
    global autofillLabel
    currentFile = fileVar.get().replace('.', '')
    dir_mode = False
    if '/' in currentFile:
        dir_mode = True
        dirr = f'{os.getcwd()}/{currentFile[:currentFile.index('/')]}'
    else:
        dirr = os.getcwd()
    try:
        if currentFile[-1] == '/':
            autofillLabel.configure(text='')
            return
    except:
        pass

    autofill_found = False

    files = os.listdir(dirr)
    for file in files:
        if file == FILE:
            continue
        # print(file)
        # print(currentFile)
        file_found = file.startswith(currentFile)
        if not file_found:
            try:
                file_found = file.startswith(currentFile[currentFile.index('/')+1:])
            except : ...
        if file_found:
            autofill_found = True
            if action == 'replace':
                if dir_mode:
                    fileVar.set(f'{currentFile[:currentFile.index('/')]}/{file}')
                else:
                    fileVar.set(f'{file}')
                if getFileFormat(file) == 'folder':
                    autofillLabel.configure(text='')
            elif action == 'check':
                if not currentFile == '':
                    if getFileFormat(file) == 'folder':
                        autofillLabel.configure(text=f'{file}', fg='#ffc0cb')
                    else:
                        autofillLabel.configure(text=f'{getFileName(file)}\n.{getFileFormat(file)}', fg='#ffc0cb')
                else:
                    autofillLabel.configure(text='')
            else:
                print(f'incorrect action: {action}')
            break
        
    if autofill_found:
        if keychain_password: # if logged in keychain
            if isExtraSecurityEnabled():
                keychainFiles = keychain_autofill
            else:
                if keychainCheckKyPassword(keychain_password):
                    keychainFiles = _keychainDecrypt(keychain_password)
                else:
                    return
            if dir_mode:
                filedir = f'{currentFile[:currentFile.index('/')]}/{file}'
            else:
                filedir = file
                
            if isExtraSecurityEnabled():
                if not filedir in keychain_autofill:
                    return 
            else:
                if not filedir in keychainFiles.keys():
                    return
                
            if not currentFile == '':
                if getFileFormat(file) == 'folder':
                    autofillLabel.configure(text=f'{file}', fg='magenta')
                else:
                    autofillLabel.configure(text=f'{getFileName(file)}\n.{getFileFormat(file)}', fg='magenta')

            if action == 'replace':
                if isExtraSecurityEnabled():
                    printuwu('authing through KeyChain...', 'pink', extra=True)
                    root.update()
                    keychainFiles = _keychainDecrypt(keychain_password)
                    printuwu('', extra='clearextra')

                    if not type(keychainFiles) == dict:
                        return
                passwordVar.set(keychainFiles[filedir])
                removeFocus()
                    
    
    if not autofill_found or not currentFile:
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
    Убирает фокусировку ввода со всех Entry
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
    file = fileVar.get()
    if type(backup) == str:
        with open(file, 'w') as f:
            f.write(backup)
    
    elif type(backup) == bytes:
        with open(file, 'wb') as f:
            f.write(backup)

    _backup_cancel()
    if backup_help_showed:
        remove_backup_help()

    printuwu(f'successfully backuped {file}\nfrom [{backup[:5]} ...]', 'lime')
    return f'successfully backuped {file}\nfrom [{backup[:5]} ...]'

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

    printuwu('[0] CANCEL and keep backup\n[1] DELETE backup', 'red')

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
    file = fileVar.get()
    removeFocus()

    if backup is None:
        printuwu('there is no backup...')
        return

    if not file:
        printuwu(f'enter file, then press\nagain to backup file')
        return
    
    try:
        open(file)
    except:
        printuwu(f'enter file, then press\nagain to backup file')
        return
    
    printuwu(f'[0] Cancel | [command+D] Delete backup', 'orange', True)
    printuwu(f'[1] RECOVERY {file}\n[2] Dump backup [{backup[:5]}...]', 'lime')

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
    printuwu('U are trying to open developer console. It is dangerous!', 'orange', True)
    printuwu('[0] Cancel and quit console\n[1] Enter password and run console')
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
        fileVar.set(file)
        
        if mode == 'lock':
            result = lock(terminalMode=True)
        elif mode == 'unlock':
            result = unlock(terminalMode=True)

        passwordVar.set('')
        fileVar.set('')
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
        fileVar.set(file)
        match mode:
            case 'recovery':
                return _backup_run()
            case 'dump':
                return _backup_dump()
            case 'delete':
                if input('this will delete backup. Are you sure? (y/n)') == 'y':
                    return _backup_delete_confirm()

def _terminalHideWindow():
    """
    Скрывает окно locked, чтобы открыть терминал
    """
    try:
        root.withdraw()
    except:
        pass

def _terminalStartAdmin():
    """
    Запускает админский терминал
    """
    init(autoreset=True)
    _terminalReset()
    _terminalHideWindow()

    USERNAME = getpass.getuser()
    print(f'Admin terminal mode started.\nType {Fore.CYAN}exit{Fore.RESET} to exit terminal and return to window mode\n\
type "{Fore.CYAN}do ...{Fore.RESET}" to execute command, or "{Fore.CYAN}eval ...{Fore.RESET}" to evaluate it. you can also just enter command to evaluate it')
    while True:
        print()
        if ADMIN_TERMINAL_SKIN == 'normal':
            inp = input(f'{Fore.LIGHTRED_EX}{USERNAME}@locked~ $ {Fore.RESET}')
        else:
            inp = input(f'{Fore.BLUE}┌──({Fore.LIGHTRED_EX}root㉿locked~{Fore.BLUE})-[{Fore.LIGHTWHITE_EX}/users/{USERNAME}{Fore.BLUE}]\n└─{Fore.LIGHTRED_EX}# {Fore.RESET}')
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
            e = str(e)
            e = e.replace('(<string>, line 1)', '')
            e = e.replace('(detected at line 1)', '')
            e = e.replace('(<string>, line 0)', '')
            print(f'{Fore.RED}{e}')
    print(f'{Fore.LIGHTMAGENTA_EX}closing...')
    _terminalReset()
    root.wm_deiconify()

def _terminalStartUser():
    """
    Запускает пользовательский терминал
    """
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
    """
    Открывает выбор терминала для открытия
    """
    _terminalReset()
    if not DEVELOPER_MODE:
        _terminalStartUser()
        return
    
    printuwu('Which terminal do u want to use?', extra=True)
    printuwu('[1] Start administrator console\n[2] Start default user console')

    root.bind('1', lambda e: _terminalStartAdmin())
    root.bind('2', lambda e: _terminalStartUser())

def _terminalReset():
    """
    Сбрасывает все бинды терминала
    """
    root.unbind('0')
    root.unbind('1')
    root.unbind('2')
    printuwu('', extra='clear')

def terminalModeAsk():
    """
    Запрашивает подтверждение намерения открыть терминал
    """
    removeFocus()
    printuwu('Open locked~ in the terminal? ', 'orange', True)
    printuwu('[0] Cancel and stay in Tkinter\n[1] Start Terminal mode')

    root.bind('0', lambda e: _terminalReset())
    root.bind('1', lambda e: _terminalChoose())


def _keychainAddFileAndPassword(file, filePassword):
    """
    Добавляет файл и пароль к нему в связку ключей, после чего сохраняет это в файл и шифрует его
    """
    keychain_autofill.append(file)
    data = _keychainDecrypt(keychain_password)
    if data == 403:
        printuwu('too many attempts. KeyChain is unavailable')
        return
    data[file] = filePassword

    with open('auth/keychain.txt', 'w') as f:
        f.write(str(data).replace("'", '"')) # Замена одинарных кавычек на двойные 💀💀💀💀💀💀💀💀
         
    _keychainEncryptKeychain(keychain_password)

# def _keychainGet(file, keychainPassword):
#     """
#     Получить данные из keychain? //всем пофиг на эту функцию))
#     """
#     data = _keychainDecrypt(keychainPassword)
#     return data[file]

def _keychainRemoveFileAndPassword(file, keychainPassword):
    """
    Удаляет сохранёный пароль к файлу из связки ключей, и записывает обновленную связку ключей, шифруя её
    """
    try:
        keychain_autofill.remove(file)
    except:
        pass
    data = _keychainDecrypt(keychainPassword)
    if data == False:
        return 'incorrect password'
    elif data == 403:
        printuwu('too many attempts. Keychain is unavailable')
    if file in data.keys():
        data.pop(file)
    else:
        return

    with open('auth/keychain.txt', 'w') as f:
        f.write(str(data).replace("'", '"'))
    _keychainEncryptKeychain(keychainPassword)

def _keychainReset():
    """
    Сбрасывает все бинды у связки ключей
    """
    global keychain_password_inputed
    try:
        root.unbind('0')
        root.unbind('1')
        root.unbind('2')
    except:
        ...

    printuwu('', extra='clear')

    try:
        root.unbind('<KeyPress>', keychain_enter_password_ID)
    except:
        ...

    keychain_password_inputed = ''

def _keychainAddCharToPassword(e):
    """
    Добавляет нажатую клавишу в поле ввода пароля от связки ключей в locked, а так же обрабатывает нажатия на esc, enter, delete
    """
    global keychain_password_inputed, keychain_password

    char = e.char
    keysym = e.keysym
    if keysym == 'Escape':
        _keychainReset()
        keychain_password_inputed = ''
        return
    elif keysym == 'BackSpace':
        if keychain_password_inputed:
            keychain_password_inputed = keychain_password_inputed[:-1]
        printuwu(f'{keychain_password_inputed}', 'orange')
        return
    elif keysym == 'Return':
        isPasswordExists = _keychainIsPasswordExists()
        if not isPasswordExists:
            _keychainReset()
            printuwu('create a keychain first')
        touchRequired = _touchIsEnabled()
        if touchRequired:
            touch = _touchAuth('\n\nuse Touch ID to auth KeyChain')
            if touch == -1:
                printuwu('Touch ID is Disabled\nLock & Unlock your Mac', 'red')
                return
            elif touch == False:
                printuwu('Touch ID Failed', 'red')
                return
        
        decrypted_ky = _keychainDecrypt(keychain_password_inputed)
        if (decrypted_ky or decrypted_ky == {}) and decrypted_ky != 403:
            keychain_password = keychain_password_inputed
            for key in decrypted_ky.keys():
                keychain_autofill.append(key)
            _keychainReset()
            printuwu('successfully logined into keychain')
            keychainAuthLabel.configure(fg='green')
            keyring.set_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS', '0')
        elif decrypted_ky == 403:
            printuwu('too many attempts.\nKeychain is unavailable now', 'red')
            keychain_password_inputed = ''
        else:
            printuwu(None, 'red')
            keychain_password_inputed = ''
        return
    
    keychain_password_inputed += char

    printuwu(f'{keychain_password_inputed}', 'orange')

def _keychainLogout():
    """
    Выходит из аккаунта связки ключей
    """
    global keychain_password
    keychain_password = None
    keychainAuthLabel.configure(fg='systemTextColor')
    _keychainReset()

keychain_enter_password_ID = None  # To unbind in the future
def _keychainEnterPassword():
    """
    Запускает меню ввода пароля в locked либо предлогает разлогиниться если залогинены
    """
    global keychain_enter_password_ID
    _keychainReset()
    try:
        with open('auth/keychain.txt'): ...
    except:
        printuwu('Create keychain first')
        return 
    if keychain_password:
        printuwu("Logout? It won't affect on your saved passwords", extra=True)
        printuwu('[0] Cancel and stay logged in\n[1] Logout and dont save new passwords')
        root.bind('0', lambda e:  _keychainReset())
        root.bind('1', lambda e: _keychainLogout())
        return 
    removeFocus()
    printuwu("Enter keychain password", extra=True)
    keychain_enter_password_ID = root.bind('<KeyPress>', _keychainAddCharToPassword)

def _keychainEncryptKeychain(password):
    """
    Шифрует файл связки ключей
    """
    with open('auth/keychain.txt', 'r') as f:
        data = f.read()
        key = make_key(password)

        encr = encrypt_data(data, key=key)

    if isExtraSecurityEnabled():
        encr = lockExtraSecurityData(encr, password)
    with open('auth/keychain.txt', 'w') as f:
        f.write(encr)

def _keychainIsPasswordExists() -> bool:
    with open('auth/keychain.txt', 'r') as f:
        data = f.read()
        if not data[:4] == 'gAAA':  # Если начинается с этих символов, то он зашифрован
            return False
        return True
    
def _keychainDecrypt(password, checkoverattempts:bool=None) -> dict | bool:
    """
    Возвращает расшифрованую версию связки ключей (не расшифровывает сам файл)\\
    словарь если пароль верный\\
    False если пароль неверный\\
    403 если слишком много попыток ввода неправильного пароля
    """
    ok_password_time = keyring.get_password('LOCKED', 'OK_PASSWORD_TIME')
    if ok_password_time:
        if time() > int(ok_password_time):
            print(time())
            keyring.delete_password('LOCKED', 'OK_PASSWORD_TIME')
    if ok_password_time:
        if time() < int(ok_password_time):
            while time() < int(ok_password_time):
                try:
                    if int(int(keyring.get_password('LOCKED', 'OK_PASSWORD_TIME'))-time()) == 0:
                        kyIncorrectPasswordLabel.configure(text=f'', justify='center')
                    else:
                        kyIncorrectPasswordLabel.configure(text=f'too many attempts\ntry again is {int(int(keyring.get_password('LOCKED', 'OK_PASSWORD_TIME'))-time())}s', justify='center')
                except:
                    ...
                ky.update()
            try:
                keyring.delete_password('LOCKED', 'OK_PASSWORD_TIME')
            except:
                pass
            keyring.set_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS', '0')

    if checkoverattempts:
        return
    with open('auth/keychain.txt', 'r') as f:
        
        data = f.read()
        if not data[:4] == 'gAAA':  # Если начинается с этих символов, то он зашифрован
            return data

        if isExtraSecurityEnabled():
            data = unlockExtraSecurityData(data, password)
        key = make_key(password)

        decr = decrypt_data(data, key=key)
        if decr is None:
            if isExtraSecurityEnabled():
                
                
                keyring.set_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS', str(int(keyring.get_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS'))+1))
                time_after_block = 10 # sec
                if int(keyring.get_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS')) > 1:
                    if not ok_password_time:
                        keyring.set_password('LOCKED', 'OK_PASSWORD_TIME', str(int(time())+(time_after_block)))
                    return 403
            return False
        if decr == '{}':
            return {}
        decr = json.loads(decr)
        
        return decr
    
def _keychainInsertToText(s):
    """
    Добавляет s в поле вывода выролей
    """
    passwordsField.configure(state=NORMAL)
    passwordsField.insert(END, s)
    passwordsField.configure(state=DISABLED)

def _keychainOpenPasswords(passwords:dict):
    """
    Убирает все следы от ввода пароля и создаёт создаёт поле, в которое выводятся сохранёные пароли
    """
    global passwordsField, kyCreateRecoveryKeyLabel
    kyIncorrectPasswordLabel.destroy()
    kyEnterPasswordLabel.destroy()
    kyPasswordEntry.destroy()
    kyEnterLabel.destroy()
    try:
        kyForgotPasswordLabel.destroy()
        kyNewPasswordLabel.destroy()
    except:
        pass
    

    passwordsField = Text(ky, state='disabled')
    passwordsField.place(x=5, y=5, width=290, height=170)
    if passwords == {}:
        _keychainInsertToText('You dont have any saved passwords in \nlocked~ keychain')
    for key in passwords.keys():
        s = f'{key} – {passwords[key]}\n'
        _keychainInsertToText(s)

    kyExtraSecurityLabel = Label(ky, text='Extra Security')
    kyExtraSecurityLabel.place(x=2, y=173)
    kyExtraSecurityLabel.bind("<Button-1>", lambda e: _securityOpen()) 
    keyring.set_password('LOCKED', 'INCORRECT_PASSWORD_ATTEMPTS', '0')
    # kyCreateRecoveryKeyLabel = Label(ky, text='create recovery key')
    # kyCreateRecoveryKeyLabel.place(x=2, y=173)
    # kyCreateRecoveryKeyLabel.bind("<Button-1>", lambda e: _keychainStartCreatingRecoveryKey()) 

def _keychainForgotPassword():
    """
    Может сбросить файл если забыт пароль
    """
    if askyesno('', 'it is impossible to recover your password. You can delete all your keychain and create a new one, or continue trying passwords.\nDELETE KEYCHAIN AND SET UP NEW?'):
        try:
            kyNewPasswordEntry.destroy()
            kyEnterNewLabel.destroy()
            kyCurrentLabel.destroy()
            kyNewLabel.destroy()
        except:
            ...

        with open('auth/keychain.txt', 'w') as f:
            f.write("{}")
        if isExtraSecurityEnabled():
            os.remove('auth/security')

        try:  keyring.delete_password('LOCKED', 'OK_PASSWORD_TIME')
        except:  pass

        try: keyring.delete_password("LOCKED", 'TOUCH_ID')
        except: pass
        ky.unbind('<Return>')
        kyPasswordEntry.delete(0, END)
        kyEnterPasswordLabel.configure(text='Create your ky password')
        ky.bind('<Return>', lambda e: _keychainAuth(kypasswordVar.get()))
    ky.focus()
    kyPasswordEntry.focus()

def _keychainStartChangingPassword():
    """
    Создаёт обстановку для смены пароля
    """
    global kyNewPasswordEntry, kyEnterNewLabel, kyCurrentLabel, kyNewLabel
    kyNewPasswordEntry = Entry(ky, justify='center')
    kyNewPasswordEntry.place(x=53, y=105)
    kyIncorrectPasswordLabel.configure(text=' ')

    kyEnterPasswordLabel.configure(text='Create a new password')
    # kyEnterLabel.config(text='')
    kyEnterNewLabel = Label(ky, text='↩')
    kyEnterNewLabel.place(x=250, y=108)

    kyCurrentLabel = Label(ky, text='current')
    kyCurrentLabel.place(x=5, y=77)

    kyNewLabel = Label(ky, text='new')
    kyNewLabel.place(x=14, y=105)
    ky.unbind('<Return>')
    ky.bind('<Return>', lambda e: _keychainChangePassword(current=kypasswordVar.get(), new=kyNewPasswordEntry.get()))

    
def _keychainChangePassword(current, new):
    """
    Меняет пароль с current на new
    """
    try:
        Fernet(make_key(new))
    except:
        kyEnterPasswordLabel.config(text='bad new password')
        return
    decrypted_ky = _keychainDecrypt(current)
    if decrypted_ky == {} or decrypted_ky and decrypted_ky != 403:
        data = decrypted_ky
        with open('auth/keychain.txt', 'w') as f:
            f.write(str(data).replace("'", '"'))
        _keychainEncryptKeychain(new)
        _keychainAuth(new)
    elif decrypted_ky == 403:
        kyEnterPasswordLabel.config(text='    too many attempts'     )
    else:
        kyEnterPasswordLabel.config(text='incorrect current password')
    
def _keychainAuth(password):
    """
    Запускает процесс авторизации. Проверяет пароль, если он верный,  то открывает окно с паролями
    """
    touchRequired = _touchIsEnabled()
    if touchRequired:
        touch = _touchAuth('\n\nuse Touch ID to open paswords')
        if touch == -1:
            showwarning('err', 'Touch ID is Disabled\nLock & Unlock your Mac')
            ky.focus()
            kyPasswordEntry.focus()
            return
        elif touch == False:
            showwarning('err', 'Touch ID Failed')
            ky.focus()
            kyPasswordEntry.focus()
            return
        
    isPasswordExists = _keychainIsPasswordExists()
    if not isPasswordExists:
        _keychainEncryptKeychain(password)
    decrypted_ky = _keychainDecrypt(password)
    if decrypted_ky == {}:
        _keychainOpenPasswords(decrypted_ky)
    elif decrypted_ky == 403:
        kyPasswordEntry.delete(0, END)
        _keychainDecrypt('', checkoverattempts=True )
    elif decrypted_ky:
        _keychainOpenPasswords(decrypted_ky)
    
    else:
        kyPasswordEntry.delete(0, END)
        kyIncorrectPasswordLabel.configure(text='incorrect password')

def _keychainCreateFilesIfNotExist():
    '''
    Создаёт файлы для связки ключей если их нет, но не шифрует в конце
    '''
    if not os.path.exists('auth'):
        os.makedirs('auth')

    try:
        with open('auth/keychain.txt'): ...
    except:
        with open('auth/keychain.txt', 'x') as f:
            f.write('{}')

def _keychainStartWindow():
    """
    Запускает окно связки ключей поверх основного окна
    """
    global kyIncorrectPasswordLabel, kyEnterPasswordLabel, kyPasswordEntry, kyEnterLabel, ky, kyForgotPasswordLabel, kypasswordVar, kyNewPasswordLabel
    _keychainReset()
    ky = Tk()
    ky.geometry('300x200')
    ky.title(' ')
    ky.resizable(False, False)
    centerwindow(ky)
    if isExtraSecurityEnabled():
        root.update()
    _keychainCreateFilesIfNotExist()
    isPasswordExists = _keychainIsPasswordExists()
    if not isPasswordExists:
        kyEnterPasswordLabel = Label(ky, text='Create your ky password')
    else:
        kyEnterPasswordLabel = Label(ky, text='Enter your ky password')
    kyEnterPasswordLabel.place(x=76, y=50)

    kyIncorrectPasswordLabel = Label(ky, justify='center')
    kyIncorrectPasswordLabel.place(x=89, y=100)

    kypasswordVar = StringVar(ky)
    kypasswordVar.trace_add('write', lambda *args: kyIncorrectPasswordLabel.configure(text=' '))

    kyPasswordEntry = Entry(ky, textvariable=kypasswordVar, show='·', justify='center')
    kyPasswordEntry.place(x=53, y=75)

    kyEnterLabel = Label(ky, text='↩')
    kyEnterLabel.place(x=250, y=78)
    if isPasswordExists:
        kyNewPasswordLabel = Label(ky, text='New ky password')
        kyNewPasswordLabel.place(x=3, y=175)
        kyNewPasswordLabel.bind("<Button-1>", lambda e: _keychainStartChangingPassword()) 

        kyForgotPasswordLabel = Label(ky, text='forgot?')
        kyForgotPasswordLabel.place(x=247, y=175)
        kyForgotPasswordLabel.bind("<Button-1>", lambda e: _keychainForgotPassword()) 
    kyPasswordEntry.focus()
    if keychain_password:
        _keychainAuth(keychain_password)
    _keychainDecrypt('', checkoverattempts=True)
    ky.bind('<Return>', lambda e: _keychainAuth(kypasswordVar.get()))

def _keychainStartCreatingRecoveryKey():###
    if not keychain_password:
        _keychainInsertToText('\nAuth keychain first')
        return
    recovery = _keychainCreateRecoveryKey(keychain_password)
    print(f'{Fore.LIGHTMAGENTA_EX}{recovery}{Fore.RESET}')
    kyCreateRecoveryKeyLabel.destroy()
    

def _keychainCreateRecoveryKey(password):###
    password = str(password)
    key = b'Vbuh3wSREjMJNFwZB3WRtQok-Bq6Aw_CbKhjPpl9rIQ='
    enc = encrypt_data(password, key=key)
    return enc

def _keychainUseRecoveryKey(encrypted_password):###
    key = b'Vbuh3wSREjMJNFwZB3WRtQok-Bq6Aw_CbKhjPpl9rIQ='
    passw = Fernet(key).decrypt(encrypted_password).decode('utf-8')
    print(f'{Fore.LIGHTCYAN_EX}{passw}{Fore.RESET}')

def keychainCheckKyPassword(kypassword):
    decrypted_ky = _keychainDecrypt(kypassword)
    if decrypted_ky == 403:
        return 403
    if decrypted_ky == {}:
        return True
    elif decrypted_ky:
        return True
    return False

def _securityPrintInfo(s, color:str=None, clear=False):
    seInfoLabel.configure(fg='systemTextColor')

    if clear:
        seInfoLabel.configure(text='')
        return
    seInfoLabel.configure(text=str(s))
    if color is not None:
        seInfoLabel.configure(fg=color)

def _touchAuth(desc='authenticate you via Touch ID') -> bool|int:
    """
    return:
    \\-1: unable to use Touch ID
    True: successful
    False: failed
    """
    from LocalAuthentication import LAContext
    from LocalAuthentication import LAPolicyDeviceOwnerAuthenticationWithBiometrics

    kTouchIdPolicy = LAPolicyDeviceOwnerAuthenticationWithBiometrics

    c = ctypes.cdll.LoadLibrary(None)

    PY3 = sys.version_info[0] >= 3
    if PY3:
        DISPATCH_TIME_FOREVER = sys.maxsize
    else:
        DISPATCH_TIME_FOREVER = sys.maxint

    dispatch_semaphore_create = c.dispatch_semaphore_create
    dispatch_semaphore_create.restype = ctypes.c_void_p
    dispatch_semaphore_create.argtypes = [ctypes.c_int]

    dispatch_semaphore_wait = c.dispatch_semaphore_wait
    dispatch_semaphore_wait.restype = ctypes.c_long
    dispatch_semaphore_wait.argtypes = [ctypes.c_void_p, ctypes.c_uint64]

    dispatch_semaphore_signal = c.dispatch_semaphore_signal
    dispatch_semaphore_signal.restype = ctypes.c_long
    dispatch_semaphore_signal.argtypes = [ctypes.c_void_p]

    context = LAContext.new()

    can_evaluate = context.canEvaluatePolicy_error_(kTouchIdPolicy, None)[0]
    if not can_evaluate:
        return -1

    sema = dispatch_semaphore_create(0)

    # we can't reassign objects from another scope, but we can modify them
    res = {'success': False, 'error': None}

    def cb(_success, _error):
        res['success'] = _success
        if _error:
            res['error'] = _error.localizedDescription()
        dispatch_semaphore_signal(sema)

    context.evaluatePolicy_localizedReason_reply_(kTouchIdPolicy, desc, cb)
    dispatch_semaphore_wait(sema, DISPATCH_TIME_FOREVER)

    if res['error']:
        return False
    return True

def _touchEnable(se):
    if _touchIsEnabled():
        print('enabled already')
        return
    
    auth = _touchAuth('\n\nYou will need to auth via Touch ID when using ky.\nuse Touch ID to continue')
    if auth == -1:
        _securityPrintInfo('unable to use Touch ID. If your mac supports it,\nlock and unlock your mac')
    elif auth == False:
        _securityPrintInfo('Touch ID Failed', 'red')
    elif auth == True:
        keyring.set_password('LOCKED', 'TOUCH_ID', '1')
        seTouchIdEnableButton.destroy()
        seTouchIdDisableButton = Button(se, text='Disable Touch ID', fg='red', command=lambda:_touchDisable(se))
        seTouchIdDisableButton.place(x=182, y=145, width=120)
        _securityPrintInfo("")

def _touchDisable(se):
    if not _touchIsEnabled():
        print('disabled already')
        return
    
    auth = _touchAuth('\n\nYou wont need to auth via Touch ID anymore.\nuse Touch ID to continue')
    if auth == -1:
        _securityPrintInfo('unable to use Touch ID. If your mac supports it,\nlock and unlock your mac')
    elif auth == False:
        _securityPrintInfo('Touch ID Failed', 'red')
    elif auth == True:
        keyring.delete_password('LOCKED', 'TOUCH_ID')
        seTouchIdDisableButton.destroy()
        seTouchIdEnableButton = Button(se, text='Enable Touch ID', fg='magenta', command=lambda:_touchEnable(se))
        seTouchIdEnableButton.place(x=182, y=145, width=120)
        _securityPrintInfo("")

def _touchIsEnabled() -> bool:
    istouch = keyring.get_password('LOCKED', 'TOUCH_ID')
    if istouch == None:
        return False
    return True

def _securityOpen(e=None):
    global seSecurityEnabledLabel, seDisableButton, seSecurityDisabledLabel, seEnableButton, seKyPasswordEntry, seInfoLabel,\
    seTouchIdDisableButton, seTouchIdEnableButton
    se = Tk()
    se.geometry('300x200')
    se.title(' ')
    se.resizable(False, False)
    centerwindow(se)
    Label(se, text='Welcome to ExtraSecurity mode', font='Arial 20').pack()
    Button(se, text='what is it?', command=_securityShowHelp).place(x=216, y=172, width=87)

    seEnabled = isExtraSecurityEnabled()
    touchIdEnabled = _touchIsEnabled()



    seSecurityEnabledLabel = Label(se, text='ExtraSecurity is enabled', fg='lime', font='Arial 15')
    seDisableButton = Button(se, text='DISABLE', fg='red', command=lambda:_securityDisable(se=se))
    seSecurityDisabledLabel = Label(se, text='ExtraSecurity is disabled', font='Arial 15', fg='pink')
    seEnableButton = Button(se, text='ENABLE', fg='magenta', command=lambda:_securityEnable(se=se))
    seInfoLabel = Label(se, text='', justify='left')
    seInfoLabel.place(x=0, y=125)

    seTouchIdEnableButton = Button(se, text='Enable Touch ID', fg='magenta', command=lambda:_touchEnable(se))
    seTouchIdDisableButton = Button(se, text='Disable Touch ID', fg='red', command=lambda:_touchDisable(se))

    if not keychain_password:
        seNotLoginedLabel = Label(se, text='You are not authed.\nEnter ky password to make actions:', justify='left', fg='orange')
        seNotLoginedLabel.place(x=0, y=60)

        seKyPasswordEntry = Entry(se)
        seKyPasswordEntry.place(x=0, y=100)
        seKyPasswordEntry.focus()

    if touchIdEnabled:
        seTouchIdDisableButton.place(x=182, y=145, width=120)
    else:
        seTouchIdEnableButton.place(x=182, y=145, width=120)

    if seEnabled:
        seSecurityEnabledLabel.place(x=68, y=30)
        seDisableButton.place(x=0, y=172, width=220)
    else: 
        seSecurityDisabledLabel.place(x=61, y=30)
        seEnableButton.place(x=0, y=172, width=220)

def _securityShowHelp(e=None):
    showinfo('ExtraSecurity', 'Программа дополнительной защиты KeyChain позволяет существенно затруднить взлом брутфорсом, требуя больше времени на каждую попытку ввода пароля')

def _securityDisable(e=None, se=None):
    global seSecurityEnabledLabel, seDisableButton, seSecurityDisabledLabel, seEnableButton
    password = keychain_password
    if not password:
        if not seKyPasswordEntry.get():
            _securityPrintInfo('Input your ky password', 'red')
            se.focus()
            seKyPasswordEntry.focus()
            return
        else:
            password = seKyPasswordEntry.get()
    
    check =  keychainCheckKyPassword(password)
    if check == 403:
        _securityPrintInfo('too many attempts.\ntry again later', 'red')
        return
    if not check:
        _securityPrintInfo('incorrect password', 'red')
        print(2)
        seKyPasswordEntry.focus()
        return

    try:
        open('auth/security')
    except:
        showinfo('', 'ExtraSecurity dont enabled')
        return
    
    with open('auth/security', 'rb') as f:
        salt = f.read()

    with open('auth/keychain.txt', 'r') as f:
        kydata = f.read()
    
    unlockedData = unlockExtraSecurityData(kydata, password)
    if not unlockedData:
        showinfo('Error')
        return

    with open('auth/keychain.txt', 'w') as f:
        f.write(unlockedData)

    os.remove('auth/security')
    if se:
        seSecurityDisabledLabel = Label(se, text='ExtraSecurity is disabled', font='Arial 15', fg='pink')
        seEnableButton = Button(se, text='ENABLE', fg='magenta', command=lambda:_securityEnable(se=se))
        
        seSecurityEnabledLabel.destroy()
        seDisableButton.destroy()
        seSecurityDisabledLabel.place(x=61, y=30)
        seEnableButton.place(x=0, y=172, width=220)



def _securityEnable(e=None, se=None):
    global seSecurityEnabledLabel, seDisableButton, seSecurityDisabledLabel, seEnableButton

    password = keychain_password
    if not password:
        if not seKyPasswordEntry.get():
            showinfo('', 'Input your ky password')
            se.focus()
            seKyPasswordEntry.focus()
            return
        else:
            password = seKyPasswordEntry.get()
    
    if not keychainCheckKyPassword(password):
        showinfo('', 'incorrect password')
        se.focus()
        seKyPasswordEntry.focus()
        return
    
    salt = os.urandom(128)

    try:
        open('auth/security')
    except:
        pass
    else:
        showinfo('', 'ExtraSecurity file already exists')
        return
    
    with open('auth/security', 'xb') as f:
        f.write(salt)

    with open('auth/keychain.txt', 'r') as f:
        kydata = f.read()

    lockedData = lockExtraSecurityData(kydata, password)
    if not lockedData:
        showinfo('Error')
        return 
    with open('auth/keychain.txt', 'w') as f:
        f.write(lockedData)

    if se:
        seSecurityEnabledLabel = Label(se, text='ExtraSecurity is enabled', fg='lime', font='Arial 15')
        seDisableButton = Button(se, text='DISABLE', fg='red', command=lambda:_securityDisable(se=se))

        seSecurityDisabledLabel.destroy()
        seEnableButton.destroy()
        seSecurityEnabledLabel.place(x=68, y=30)
        seDisableButton.place(x=0, y=172, width=220)
        


def _securityCreateNewKey(kypassword, salt):
    newkey = hashlib.pbkdf2_hmac(
        'sha256',
        str(kypassword).encode('utf-8'),
        salt,
        7_000_000
    )
    newkey = str(newkey)
    newkey = ''.join(e for e in newkey if e.isalnum()) # убрать специальные символы типо " \ ' 
    return newkey

def unlockExtraSecurityData(data, kypassword:str):
    if not isExtraSecurityEnabled():
        return
    
    with open('auth/security', 'rb') as f:
        salt = f.read()
    
    newkey = _securityCreateNewKey(kypassword, salt)

    decr = decrypt_data(data, key=make_key(newkey))
    return decr

def lockExtraSecurityData(data, kypassword:str):
    if not isExtraSecurityEnabled():
        return
    
    with open('auth/security', 'rb') as f:
        salt = f.read()
    
    newkey = _securityCreateNewKey(kypassword, salt)

    enc = encrypt_data(data, key=make_key(newkey))
    return enc

def isExtraSecurityEnabled() -> bool:
    try:
        open('auth/security', 'rb')
    except:
        return False
    else:
        return True

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
# root.after(50)
# root.iconify()
# root.update()
centerwindow(root)


fileVar = StringVar(root)
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

fileEntry = Entry(root, textvariable=fileVar)
fileEntry.place(x=60, y=60)
fileVar.trace_add('write', updFileEntryColor)  # При записи каждой новой буквы вызываетя обновление цвета для имени файла

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
try:
    import platform
    if platform.system() == 'Windows':
        showwarning('', 'App is not designed for Windows system. You may experience problems')
except:
    pass

helpLabel = Label(root, text='?', relief='flat')
helpLabel.place(x=281, y=174)
helpLabel.bind("<Button-1>", lambda e: showHelp())  # При нажатии на вопрос
helpLabel.bind("<Button-2>", lambda e: backupFile())
helpLabel.bind("<Enter>", lambda e: lockedLabel.configure(text='click to show help\nr click to backup'))  # При наведении на вопрос
helpLabel.bind("<Leave>", lambda e: lockedLabel.configure(text='locked~'))  # При уведении курсора с вопроса

terminalLabel = Label(root, text='term', relief='flat')
terminalLabel.place(x=0, y=0)
terminalLabel.bind("<Button-1>", lambda e: terminalModeAsk()) 
_keychainForgotPassword
keychainAuthLabel = Label(root, text='auth keychain')
keychainAuthLabel.place(x=0, y=17)
keychainAuthLabel.bind("<Button-1>", lambda e: _keychainEnterPassword()) 

keychainOpenLabel = Label(root, text='open keychain')
keychainOpenLabel.place(x=0, y=35)
keychainOpenLabel.bind("<Button-1>", lambda e: _keychainStartWindow()) 
removeFocus()
# тестирование
# general_test()
root.mainloop()
