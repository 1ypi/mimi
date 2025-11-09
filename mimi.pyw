import google.generativeai as genai
import subprocess
import platform
import sys
import os
import pyautogui
import time
import psutil
import json
from pathlib import Path
import speech_recognition as sr
import threading
from PIL import Image
import io
import base64
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from datetime import datetime
import random
from gtts import gTTS
import pygame
import tempfile

CONFIG_DIR = Path.home() / '.mimi'
CONFIG_FILE = CONFIG_DIR / 'config.json'
GEMINI_API_KEY = None
model = None

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

current_language = "en"  

listening_active = False
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.2
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5
microphone = None

tts_lock = threading.Lock()
tts_queue = []
tts_thread_active = False

system_info_cache = None
system_info_lock = threading.Lock()

selected_microphone_index = None
selected_speaker_index = None

root = None
input_field = None
console_output = None
status_label = None
voice_button = None
cpu_label = None
mem_label = None
process_indicator = None
language_button = None
settings_window = None

WORKING_PHRASES = {
    "en": [
        "Working on it",
        "Right away, sir",
        "Processing your request",
        "On it",
        "Understood",
        "Right away",
        "I'll handle that",
        "Consider it done"
    ],
    "es": [
        "En eso estoy",
        "Enseguida, señor",
        "Procesando su solicitud",
        "En ello",
        "Entendido",
        "De inmediato",
        "Lo haré",
        "Considérelo hecho"
    ]
}

SUCCESS_PHRASES = {
    "en": [
        "Done, sir",
        "Task completed",
        "All set",
        "Finished",
        "Complete",
        "Done, master",
        "Task successful"
    ],
    "es": [
        "Hecho, señor",
        "Tarea completada",
        "Todo listo",
        "Terminado",
        "Completo",
        "Hecho, amo",
        "Tarea exitosa"
    ]
}

UI_TEXTS = {
    "en": {
        "title": "MIMI",
        "initializing": "Initializing...",
        "ready": "Ready",
        "listening": "Listening for 'MIMI'...",
        "voice_activated": "Voice mode activated",
        "voice_deactivated": "Voice mode deactivated",
        "start_voice": "Start Voice Mode",
        "stop_voice": "Stop Voice Mode",
        "screenshot": "Screenshot",
        "clear": "Clear",
        "send": "Send",
        "language": "ES",
        "mic_unavailable": "Microphone not available",
        "console_cleared": "Console cleared",
        "screenshot_mode": "Screenshot mode enabled. Press Enter to capture and send.",
        "processing": "Processing...",
        "voice_tip": "Tip: In voice mode, start commands with 'MIMI'",
        "screenshot_tip": "Tip: Add '/screen' to include a screenshot",
        "ready_msg": "Ready. How may I assist you?",
        "api_key_prompt": "Please enter your Gemini API Key:",
        "api_key_error": "API Key is required to use MIMI",
        "api_key_saved": "API Key saved successfully"
    },
    "es": {
        "title": "MIMI",
        "initializing": "Inicializando...",
        "ready": "Listo",
        "listening": "Escuchando 'MIMI'...",
        "voice_activated": "Modo de voz activado",
        "voice_deactivated": "Modo de voz desactivado",
        "start_voice": "Iniciar Modo de Voz",
        "stop_voice": "Detener Modo de Voz",
        "screenshot": "Captura",
        "clear": "Limpiar",
        "send": "Enviar",
        "language": "EN",
        "settings": "Configuración",
        "mic_unavailable": "Micrófono no disponible",
        "console_cleared": "Consola limpiada",
        "screenshot_mode": "Modo captura activado. Presiona Enter para capturar y enviar.",
        "processing": "Procesando...",
        "voice_tip": "Consejo: En modo de voz, inicia comandos con 'MIMI'",
        "screenshot_tip": "Consejo: Añade '/screen' para incluir una captura",
        "ready_msg": "Listo. ¿En qué puedo ayudarte?",
        "api_key_prompt": "Por favor ingresa tu Clave API de Gemini:",
        "api_key_error": "La Clave API es necesaria para usar MIMI",
        "api_key_saved": "Clave API guardada exitosamente"
    }
}

def open_settings():
    global settings_window, selected_microphone_index, listening_active

    if listening_active:
        listening_active = False
        voice_button.config(text=get_text("start_voice"))
        log_to_console(get_text("voice_deactivated"))

    if settings_window is not None and settings_window.winfo_exists():
        settings_window.lift()
        return

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings" if current_language == "en" else "Configuración")
    settings_window.geometry("550x550")
    settings_window.configure(bg="#ffffff")
    settings_window.resizable(False, False)

    settings_window.transient(root)
    settings_window.grab_set()
    settings_window.attributes('-topmost', True)

    main_frame = tk.Frame(settings_window, bg="#ffffff", padx=30, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    title = tk.Label(main_frame, 
                     text="Settings" if current_language == "en" else "Configuración",
                     font=("Segoe UI", 16, "bold"),
                     bg="#ffffff", fg="#000000")
    title.pack(pady=(0, 20))

    api_frame = tk.LabelFrame(main_frame, 
                              text="API Configuration" if current_language == "en" else "Configuración de API",
                              font=("Segoe UI", 11, "bold"),
                              bg="#ffffff", fg="#000000",
                              padx=15, pady=15)
    api_frame.pack(fill=tk.X, pady=(0, 20))

    api_status_text = "Current API Key: " if current_language == "en" else "Clave API Actual: "
    api_status = tk.Label(api_frame,
                         text=api_status_text + ("*" * 32 if GEMINI_API_KEY else "Not set"),
                         font=("Segoe UI", 9),
                         bg="#ffffff", fg="#666666",
                         anchor=tk.W)
    api_status.pack(fill=tk.X, pady=(0, 10))

    def change_api_key():
        if prompt_for_api_key(settings_window):
            api_status.config(text=api_status_text + "*" * 32)
            if initialize_gemini():
                messagebox.showinfo("Success" if current_language == "en" else "Éxito",
                                  "API key updated and validated successfully!" if current_language == "en" 
                                  else "¡Clave API actualizada y validada exitosamente!")
                log_to_console("API key updated successfully")
            else:
                messagebox.showerror("Error", "Failed to initialize with new API key")

    change_api_btn = tk.Button(api_frame,
                              text="Change API Key" if current_language == "en" else "Cambiar Clave API",
                              font=("Segoe UI", 10),
                              bg="#0078d4", fg="#ffffff",
                              activebackground="#005a9e",
                              activeforeground="#ffffff",
                              relief=tk.FLAT,
                              bd=0,
                              padx=20, pady=8,
                              cursor="hand2",
                              command=change_api_key)
    change_api_btn.pack(anchor=tk.W)

    audio_label = tk.Label(main_frame,
                         text="Audio Device Settings:" if current_language == "en" else "Configuración de Dispositivos de Audio:",
                         font=("Segoe UI", 11, "bold"),
                         bg="#ffffff", fg="#000000",
                         anchor=tk.W)
    audio_label.pack(fill=tk.X, pady=(0, 10))

    mic_devices = get_audio_devices()

    mic_frame = tk.Frame(main_frame, bg="#ffffff")
    mic_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    mic_scrollbar = tk.Scrollbar(mic_frame)
    mic_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    mic_listbox = tk.Listbox(mic_frame,
                             font=("Segoe UI", 9),
                             bg="#f9f9f9",
                             fg="#000000",
                             selectbackground="#0078d4",
                             selectforeground="#ffffff",
                             yscrollcommand=mic_scrollbar.set,
                             height=8)
    mic_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    mic_scrollbar.config(command=mic_listbox.yview)

    for i, device in enumerate(mic_devices):
        mic_listbox.insert(tk.END, f"{i}: {device}")
        if selected_microphone_index == i:
            mic_listbox.select_set(i)

    button_frame = tk.Frame(main_frame, bg="#ffffff")
    button_frame.pack(fill=tk.X, pady=(10, 0))

    def apply_settings():
        global selected_microphone_index, microphone

        selection = mic_listbox.curselection()
        if selection:
            selected_microphone_index = selection[0]
            log_to_console(f"Microphone changed to: {mic_devices[selected_microphone_index]}")

            initialize_microphone()

            messagebox.showinfo("Success" if current_language == "en" else "Éxito",
                              "Settings applied successfully" if current_language == "en" else "Configuración aplicada exitosamente")

    def reset_settings():
        global selected_microphone_index
        selected_microphone_index = None
        mic_listbox.selection_clear(0, tk.END)
        log_to_console("Audio settings reset to default")

    apply_btn = tk.Button(button_frame,
                         text="Apply" if current_language == "en" else "Aplicar",
                         font=("Segoe UI", 10),
                         bg="#0078d4", fg="#ffffff",
                         activebackground="#005a9e",
                         activeforeground="#ffffff",
                         relief=tk.FLAT,
                         bd=0,
                         padx=20, pady=8,
                         cursor="hand2",
                         command=apply_settings)
    apply_btn.pack(side=tk.LEFT, padx=(0, 10))

    reset_btn = tk.Button(button_frame,
                         text="Reset" if current_language == "en" else "Reiniciar",
                         font=("Segoe UI", 10),
                         bg="#f0f0f0", fg="#000000",
                         activebackground="#e0e0e0",
                         activeforeground="#000000",
                         relief=tk.FLAT,
                         bd=0,
                         padx=20, pady=8,
                         cursor="hand2",
                         command=reset_settings)
    reset_btn.pack(side=tk.LEFT, padx=(0, 10))

    close_btn = tk.Button(button_frame,
                         text="Close" if current_language == "en" else "Cerrar",
                         font=("Segoe UI", 10),
                         bg="#f0f0f0", fg="#000000",
                         activebackground="#e0e0e0",
                         activeforeground="#000000",
                         relief=tk.FLAT,
                         bd=0,
                         padx=20, pady=8,
                         cursor="hand2",
                         command=settings_window.destroy)
    close_btn.pack(side=tk.RIGHT)

def get_text(key):
    return UI_TEXTS[current_language].get(key, key)

def load_config():
    global GEMINI_API_KEY
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                GEMINI_API_KEY = config.get('api_key')
                return True
        return False
    except Exception as e:
        print(f"Error loading config: {e}")
        return False

def save_config(api_key):
    global GEMINI_API_KEY
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {'api_key': api_key}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

        if platform.system() != "Windows":
            os.chmod(CONFIG_FILE, 0o600)
        GEMINI_API_KEY = api_key
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def prompt_for_api_key(parent_window=None):
    if parent_window is None:
        temp_root = tk.Tk()
        temp_root.withdraw()
        temp_root.attributes('-topmost', True)
        parent = temp_root
    else:
        parent = parent_window
        temp_root = None

    while True:
        api_key = simpledialog.askstring(
            "Gemini API Key",
            get_text("api_key_prompt"),
            show='*',
            parent=parent
        )

        if temp_root:
            temp_root.destroy()

        if not api_key:
            if messagebox.askyesno("Cancel", "Do you want to cancel? The application cannot run without an API key."):
                return False
            continue

        messagebox.showinfo("Validating", "Validating API key, please wait...")
        is_valid, message = validate_api_key(api_key)

        if is_valid:
            if save_config(api_key):
                messagebox.showinfo("Success", get_text("api_key_saved"))
                return True
            else:
                messagebox.showerror("Error", "Failed to save API key")
                return False
        else:
            retry = messagebox.askyesno("Invalid API Key", 
                                       f"{message}\n\nWould you like to try another key?")
            if not retry:
                return False

    return False


def validate_api_key(api_key):
    try:
        genai.configure(api_key=api_key)
        test_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = test_model.generate_content("Hi")
        return True, "API key is valid"
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
            return False, "Invalid API key"
        elif "quota" in error_msg.lower():
            return False, "API key valid but quota exceeded"
        else:
            return False, f"Validation failed: {error_msg}"

def initialize_gemini():
    global model
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        return True
    except Exception as e:
        print(f"Gemini initialization failed: {e}")
        return False

def initialize_tts():
    try:

        pygame.mixer.init()

        threading.Thread(target=tts_worker, daemon=True).start()
        return True
    except Exception as e:
        print(f"TTS initialization failed: {e}")
        return False

def tts_worker():
    global tts_thread_active
    tts_thread_active = True

    while tts_thread_active:
        if tts_queue:
            text = tts_queue.pop(0)
            with tts_lock:
                try:

                    lang_code = "es" if current_language == "es" else "en"

                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_file.close()

                    if lang_code == "en":
                        tts = gTTS(text=text, lang=lang_code, slow=False, tld='co.uk')
                    else:
                        tts = gTTS(text=text, lang=lang_code, slow=False, tld='com.mx')

                    tts.save(temp_file.name)

                    pygame.mixer.music.load(temp_file.name)

                    pygame.mixer.quit()
                    pygame.mixer.init(frequency=48000)  
                    pygame.mixer.music.load(temp_file.name)
                    pygame.mixer.music.play()

                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                    pygame.mixer.quit()
                    pygame.mixer.init(frequency=22050)

                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass

                except Exception as e:
                    print(f"TTS error: {e}")
        time.sleep(0.1)

def speak(text):
    if text:
        tts_queue.append(text)

def initialize_microphone():
    global microphone
    try:
        if selected_microphone_index is not None:
            microphone = sr.Microphone(device_index=selected_microphone_index)
        else:
            microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        return True
    except Exception as e:
        log_to_console(f"Microphone initialization failed: {e}")
        return False

def get_audio_devices():
    try:
        mic_list = sr.Microphone.list_microphone_names()
        return mic_list
    except Exception as e:
        print(f"Error getting audio devices: {e}")
        return []

def system_info_updater():
    global system_info_cache
    while True:
        try:
            new_info = get_system_info()
            with system_info_lock:
                system_info_cache = new_info
            update_system_stats()
        except:
            pass
        time.sleep(20)

def get_cached_system_info():
    with system_info_lock:
        return system_info_cache

def listen_for_speech(timeout=10):
    if not microphone:
        return None

    try:
        with microphone as source:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=15)

        lang_code = "es-ES" if current_language == "es" else "en-US"
        text = recognizer.recognize_google(audio, language=lang_code)
        return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None
    except Exception:
        return None

def voice_input_loop():
    global listening_active
    log_to_console(get_text("voice_activated") + ". " + get_text("voice_tip"))
    speak(get_text("voice_activated"))

    time.sleep(2)

    while listening_active:
        set_status(get_text("listening"), "#666666")
        text = listen_for_speech()
        if text:

            if text.lower().startswith('mimi'):

                command = text[5:].strip()

                exit_words = ['exit', 'quit', 'stop listening', 'bye', 'goodbye', 
                              'salir', 'detener', 'adiós', 'hasta luego']
                if any(word in command.lower() for word in exit_words):
                    listening_active = False
                    log_to_console(get_text("voice_deactivated"))
                    speak(get_text("voice_deactivated"))
                    break

                if command:
                    log_to_console(f"You: {command}")

                    response = random.choice(WORKING_PHRASES[current_language])
                    log_to_console(f"MIMI: {response}")
                    speak(response)

                    time.sleep(1.5)

                    current_sysinfo = get_cached_system_info()
                    process_request_with_retry(command, current_sysinfo, voice_mode=True)

        time.sleep(0.1)

    root.after(0, lambda: voice_button.config(text=get_text("start_voice")))
    set_status(get_text("ready"), "#000000")

def get_all_directories(root_path, max_depth=3, current_depth=0):
    directories = []

    if current_depth >= max_depth:
        return directories

    try:
        for item in Path(root_path).iterdir():
            if item.is_dir():
                try:
                    directories.append(str(item))
                    if current_depth < max_depth - 1:
                        subdirs = get_all_directories(item, max_depth, current_depth + 1)
                        directories.extend(subdirs)
                except PermissionError:
                    pass
                except:
                    pass
    except:
        pass

    return directories

def get_system_directories():
    directories = []
    system = platform.system()

    try:
        home = Path.home()
        directories.append(str(home))

        common_dirs = ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Videos', 'Music']
        for dirname in common_dirs:
            dirpath = home / dirname
            if dirpath.exists():
                directories.append(str(dirpath))
                directories.extend(get_all_directories(dirpath, max_depth=2))

        current = Path.cwd()
        directories.append(str(current))
        directories.extend(get_all_directories(current, max_depth=2))

        if system == "Windows":
            drives = ['C:\\', 'D:\\', 'E:\\']
            for drive in drives:
                if Path(drive).exists():
                    directories.append(drive)
                    try:
                        for item in Path(drive).iterdir():
                            if item.is_dir():
                                directories.append(str(item))
                    except:
                        pass

            prog_files = [
                Path('C:\\Program Files'),
                Path('C:\\Program Files (x86)')
            ]
            for pf in prog_files:
                if pf.exists():
                    directories.append(str(pf))
                    directories.extend(get_all_directories(pf, max_depth=2))

        elif system == "Linux":
            linux_dirs = ['/home', '/usr', '/opt', '/var', '/etc']
            for d in linux_dirs:
                if Path(d).exists():
                    directories.append(d)
                    try:
                        for item in Path(d).iterdir():
                            if item.is_dir():
                                directories.append(str(item))
                    except:
                        pass

        elif system == "Darwin":
            mac_dirs = ['/Applications', '/Users', '/Library']
            for d in mac_dirs:
                if Path(d).exists():
                    directories.append(d)
                    directories.extend(get_all_directories(d, max_depth=2))

    except Exception as e:
        pass

    return list(set(directories))[:500]

def get_desktop_shortcuts():
    shortcuts = []
    system = platform.system()

    try:
        desktop = Path.home() / 'Desktop'

        if system == "Windows":
            if desktop.exists():
                for item in desktop.iterdir():
                    if item.suffix.lower() == '.lnk':
                        shortcuts.append({
                            'name': item.stem,
                            'path': str(item)
                        })

        elif system == "Darwin":
            if desktop.exists():
                for item in desktop.iterdir():
                    if item.suffix in ['.app', '.webloc']:
                        shortcuts.append({
                            'name': item.stem,
                            'path': str(item)
                        })

        else:
            if desktop.exists():
                for item in desktop.iterdir():
                    if item.suffix == '.desktop':
                        shortcuts.append({
                            'name': item.stem,
                            'path': str(item)
                        })
    except:
        pass

    return shortcuts

def get_installed_programs():
    programs = []
    system = platform.system()

    try:
        if system == "Windows":
            paths = [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs'
            ]

            for path in paths:
                if path.exists():
                    for item in path.iterdir():
                        if item.is_dir():
                            programs.append(item.name)

            try:
                result = subprocess.run(
                    'wmic product get name',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n')[1:]:
                        if line.strip():
                            programs.append(line.strip())
            except:
                pass

        elif system == "Linux":
            try:
                result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if line.startswith('ii'):
                        parts = line.split()
                        if len(parts) > 1:
                            programs.append(parts[1])
            except:
                pass
        elif system == "Darwin":
            apps_path = Path('/Applications')
            if apps_path.exists():
                for item in apps_path.iterdir():
                    if item.suffix == '.app':
                        programs.append(item.stem)
    except:
        pass

    return list(set(programs))[:50]

def get_running_processes():
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'name': proc.info['name'],
                    'pid': proc.info['pid'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent']
                })
            except:
                pass
    except:
        pass

    processes.sort(key=lambda x: x.get('memory', 0), reverse=True)
    return processes[:30]

def get_steam_games():
    games = []
    try:
        steam_paths = [
            Path('C:/Program Files (x86)/Steam/steamapps/common'),
            Path('C:/Program Files/Steam/steamapps/common'),
            Path.home() / '.steam/steam/steamapps/common',
            Path.home() / 'Library/Application Support/Steam/steamapps/common'
        ]

        for path in steam_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass

    return games[:30]

def get_epic_games():
    games = []
    try:
        epic_paths = [
            Path('C:/Program Files/Epic Games'),
            Path('C:/Program Files (x86)/Epic Games'),
            Path.home() / 'Epic Games',
            Path.home() / 'Program Files' / 'Epic Games'
        ]
        for path in epic_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass
    return games[:30]

def get_rockstar_games():
    games = []
    try:
        rockstar_paths = [
            Path('C:/Program Files/Rockstar Games'),
            Path('C:/Program Files (x86)/Rockstar Games'),
            Path.home() / 'Games' / 'Rockstar Games'
        ]
        for path in rockstar_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass
    return games[:30]

def get_ubisoft_games():
    games = []
    try:
        ubisoft_paths = [
            Path('C:/Program Files (x86)/Ubisoft'),
            Path('C:/Program Files/Ubisoft'),
            Path.home() / 'Ubisoft',
            Path.home() / 'Games' / 'Ubisoft'
        ]
        for path in ubisoft_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass
    return games[:30]

def get_ea_games():
    games = []
    try:
        ea_paths = [
            Path('C:/Program Files (x86)/Origin Games'),
            Path('C:/Program Files (x86)/EA Games'),
            Path('C:/Program Files/Origin Games'),
            Path.home() / 'Games' / 'EA'
        ]
        for path in ea_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass
    return games[:30]

def get_gog_games():
    games = []
    try:
        gog_paths = [
            Path('C:/Program Files (x86)/GOG Galaxy/Games'),
            Path('C:/Program Files/GOG Galaxy/Games'),
            Path('C:/GOG Games'),
            Path.home() / 'GOG Games'
        ]
        for path in gog_paths:
            if path.exists():
                for item in path.iterdir():
                    if item.is_dir():
                        games.append(item.name)
    except:
        pass
    return games[:30]

def get_network_info():
    info = {}
    try:
        info['interfaces'] = []
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:
                    info['interfaces'].append({
                        'name': iface,
                        'ip': addr.address
                    })

        net_io = psutil.net_io_counters()
        info['bytes_sent'] = net_io.bytes_sent
        info['bytes_recv'] = net_io.bytes_recv
    except:
        pass

    return info

def get_disk_info():
    disks = []
    try:
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent
                })
            except:
                pass
    except:
        pass

    return disks

def get_system_info():
    system = platform.system()
    shell_type = "Unknown"

    if system == "Windows":
        if 'PSMODULEPATH' in os.environ:
            shell_type = "PowerShell"
        else:
            shell_type = "CMD"
    elif system == "Linux":
        shell_type = os.environ.get('SHELL', '/bin/bash').split('/')[-1]
    elif system == "Darwin":
        shell_type = os.environ.get('SHELL', '/bin/zsh').split('/')[-1]

    cpu_info = {
        'physical_cores': psutil.cpu_count(logical=False),
        'logical_cores': psutil.cpu_count(logical=True),
        'usage_percent': psutil.cpu_percent(interval=1),
        'frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }

    memory = psutil.virtual_memory()
    memory_info = {
        'total_gb': round(memory.total / (1024**3), 2),
        'available_gb': round(memory.available / (1024**3), 2),
        'used_gb': round(memory.used / (1024**3), 2),
        'percent': memory.percent
    }

    return {
        "os": system,
        "os_version": platform.version(),
        "machine": platform.machine(),
        "shell": shell_type,
        "processor": platform.processor(),
        "hostname": platform.node(),
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": get_disk_info(),
        "network": get_network_info(),
        "directories": get_system_directories(),
        "desktop_shortcuts": get_desktop_shortcuts(),
        "installed_programs": get_installed_programs(),
        "running_processes": get_running_processes(),
        "steam_games": get_steam_games(),
        "epic_games": get_epic_games(),
        "rockstar_games": get_rockstar_games(),
        "ubisoft_games": get_ubisoft_games(),
        "ea_games": get_ea_games(),
        "gog_games": get_gog_games(),
        "user": os.getenv('USERNAME') or os.getenv('USER'),
        "home_dir": str(Path.home()),
        "current_dir": os.getcwd()
    }

def take_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return Image.open(img_buffer)
    except Exception as e:
        log_to_console(f"Screenshot failed: {e}")
        return None

def create_prompt(user_request, system_info, previous_error=None, prefer_keystrokes=False, screenshot=None):

    keystroke_preference = ""
    if prefer_keystrokes:
        keystroke_preference = """
IMPORTANT: User has requested keystroke/GUI automation for this task.
Use keystrokes and GUI interactions for tasks like:
- Opening websites in browsers
- Filling out forms
- Creating accounts
- Navigating UI elements
- Any task that benefits from GUI interaction
"""

    error_context = ""
    if previous_error:
        error_context = f"""
PREVIOUS ATTEMPT FAILED WITH ERROR:
{previous_error}

Please analyze the error and provide a corrected command or approach.
If you need updated system information, output: REFRESH_SYSINFO
Then I will provide fresh system data and you can retry.
"""

    screenshot_context = ""
    if screenshot:
        screenshot_context = """
SCREENSHOT PROVIDED:
The user has provided a screenshot of their current screen.
Analyze the screenshot to understand the current state and provide appropriate commands.
You can see what's currently on screen and tailor your response accordingly.
"""

    steam_games_formatted = '\n'.join([f'  - {game}' for game in system_info['steam_games'][:30]]) if system_info['steam_games'] else 'None detected'

    directories_formatted = '\n'.join([f'  - {d}' for d in system_info['directories'][:100]]) if system_info.get('directories') else 'None'

    shortcuts_formatted = '\n'.join([f'  - {s["name"]}: {s["path"]}' for s in system_info.get('desktop_shortcuts', [])]) if system_info.get('desktop_shortcuts') else 'None'

    prompt = f"""You are a command-line assistant. Convert natural language requests into executable terminal commands or keyboard sequences.

CRITICAL RULES:
1. Output ONLY the command or keystrokes - no explanations, no markdown, no additional text
2. {'PREFER KEYSTROKES for this request (user preference or task requires GUI automation)' if prefer_keystrokes else 'STRONGLY PREFER commands over keystrokes (use keystrokes only when absolutely necessary)'}
3. If the request is unclear or dangerous, output: ERROR: [brief reason]
4. For Windows: Prefix PowerShell commands with "PS:" and CMD commands with "CMD:"
5. If you need updated system information, output: REFRESH_SYSINFO

{keystroke_preference}

{error_context}

{screenshot_context}

SYSTEM INFORMATION:
OS: {system_info['os']}
Shell: {system_info['shell']}
Processor: {system_info['processor']}
Hostname: {system_info['hostname']}
User: {system_info['user']}
Current Directory: {system_info['current_dir']}

CPU: {system_info['cpu']['physical_cores']} physical cores, {system_info['cpu']['logical_cores']} logical cores, {system_info['cpu']['usage_percent']}% usage
Memory: {system_info['memory']['used_gb']}GB / {system_info['memory']['total_gb']}GB ({system_info['memory']['percent']}% used)

DISK DRIVES:
{json.dumps(system_info['disk'], indent=2)}

NETWORK INTERFACES:
{json.dumps(system_info['network']['interfaces'], indent=2)}

SYSTEM DIRECTORIES (sample of {len(system_info.get('directories', []))} total):
{directories_formatted}

DESKTOP SHORTCUTS:
{shortcuts_formatted}

TOP RUNNING PROCESSES:
{json.dumps(system_info['running_processes'][:10], indent=2)}

INSTALLED PROGRAMS (sample):
{', '.join(system_info['installed_programs'][:20])}

GAMES LIBRARY:

STEAM GAMES:
{steam_games_formatted}

EPIC GAMES:
{chr(10).join([f'  - {game}' for game in system_info['epic_games'][:30]]) if system_info['epic_games'] else 'None detected'}

ROCKSTAR GAMES:
{chr(10).join([f'  - {game}' for game in system_info['rockstar_games']]) if system_info['rockstar_games'] else 'None detected'}

UBISOFT GAMES:
{chr(10).join([f'  - {game}' for game in system_info['ubisoft_games']]) if system_info['ubisoft_games'] else 'None detected'}

EA/ORIGIN GAMES:
{chr(10).join([f'  - {game}' for game in system_info['ea_games']]) if system_info['ea_games'] else 'None detected'}

GOG GAMES:
{chr(10).join([f'  - {game}' for game in system_info['gog_games']]) if system_info['gog_games'] else 'None detected'}

NOTE: For Steam games, use the folder name to launch via Steam protocol.
Example: If user says "open Geometry Dash" and you see it in the list, use: PS:Start-Process "steam://rungameid/322170"
(You'll need to look up the Steam AppID separately or use the folder name with Steam's launch protocol)

COMMAND PRIORITY:
- {'USE KEYSTROKES for GUI tasks' if prefer_keystrokes else 'ALWAYS prefer terminal commands over keystrokes'}
- Use keystrokes for: GUI navigation, form filling, account creation, website interaction, screenshots, locking screen
- For everything else (listing, searching, system info), use commands unless GUI is specifically needed

TYPE 1 - TERMINAL COMMANDS:
Format for Windows: PS:command or CMD:command
Format for Linux/Mac: command

Windows PowerShell examples:
- PS:Get-Process
- PS:Get-Service
- PS:Start-Process chrome "https://example.com"
- PS:Start-Process "steam://rungameid/322170"
- PS:Test-Connection google.com

Windows CMD examples:
- CMD:dir
- CMD:ipconfig
- CMD:start chrome https://example.com

Linux/Mac examples:
- ls -la
- open https://example.com (Mac)
- xdg-open https://example.com (Linux)

TYPE 2 - KEYBOARD SHORTCUTS & GUI AUTOMATION:
Format: [KEY1] [KEY2] or TYPE:text or WAIT:seconds

Examples:
- [WIN] [S] TYPE:chrome WAIT:1 [ENTER]
- [CTRL] [T] WAIT:0.5 TYPE:https://roblox.com/signup WAIT:1 [ENTER] WAIT:3 [TAB] TYPE:username
- [WIN] [L] (lock screen)
- [WIN] [SHIFT] [S] (screenshot)

For complex tasks like creating accounts:
1. Open browser: [WIN] [S] TYPE:chrome [ENTER] WAIT:2
2. Navigate to site: [CTRL] [T] TYPE:https://site.com [ENTER] WAIT:3
3. Fill forms: [TAB] TYPE:username [TAB] TYPE:email [TAB] TYPE:password
4. Use WAIT: between actions for page loads and UI updates

USER REQUEST: {user_request}

OUTPUT:"""

    return prompt

def execute_hotkey(keys):
    key_map = {
        "WIN": "win", "CTRL": "ctrl", "ALT": "alt", "SHIFT": "shift",
        "ENTER": "enter", "ESC": "esc", "TAB": "tab", "SPACE": "space",
        "BACKSPACE": "backspace", "DELETE": "delete",
        "UP": "up", "DOWN": "down", "LEFT": "left", "RIGHT": "right",
        "HOME": "home", "END": "end", "PAGEUP": "pageup", "PAGEDOWN": "pagedown",
    }

    mapped_keys = []
    for key in keys:
        if key in key_map:
            mapped_keys.append(key_map[key])
        elif key.startswith("F") and len(key) <= 3 and key[1:].isdigit():
            mapped_keys.append(key.lower())
        elif len(key) == 1:
            mapped_keys.append(key.lower())
        else:
            mapped_keys.append(key)

    if len(mapped_keys) == 1:
        pyautogui.press(mapped_keys[0])
    else:
        pyautogui.hotkey(*mapped_keys)

def execute_keystroke_sequence(sequence):
    try:
        actions = []
        i = 0

        while i < len(sequence):
            if sequence[i:i+5] == "TYPE:":
                j = i + 5
                text = ""
                while j < len(sequence):
                    if sequence[j:j+1] == "[" or sequence[j:j+5] == "WAIT:":
                        break
                    text += sequence[j]
                    j += 1
                actions.append(("TYPE", text.strip()))
                i = j
            elif sequence[i:i+5] == "WAIT:":
                j = i + 5
                wait_time = ""
                while j < len(sequence) and (sequence[j].isdigit() or sequence[j] == '.'):
                    wait_time += sequence[j]
                    j += 1
                actions.append(("WAIT", float(wait_time)))
                i = j
            elif sequence[i] == "[":
                j = i + 1
                while j < len(sequence) and sequence[j] != "]":
                    j += 1
                if j < len(sequence):
                    key = sequence[i+1:j]
                    actions.append(("KEY", key))
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1

        current_keys = []
        for action_type, action_value in actions:
            if action_type == "KEY":
                current_keys.append(action_value)
            elif action_type == "TYPE":
                if current_keys:
                    execute_hotkey(current_keys)
                    current_keys = []
                    time.sleep(0.1)
                pyautogui.write(action_value, interval=0.05)
            elif action_type == "WAIT":
                if current_keys:
                    execute_hotkey(current_keys)
                    current_keys = []
                time.sleep(action_value)

        if current_keys:
            execute_hotkey(current_keys)

        return {"success": True, "message": "Keystrokes executed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def should_run_detached(command):
    detached_keywords = ['start', 'open', 'launch', 'chrome', 'firefox', 'browser', 'notepad', 'code', 'explorer']
    command_lower = command.lower()
    return any(keyword in command_lower for keyword in detached_keywords)

def execute_command(command):
    try:
        is_windows = platform.system() == "Windows"
        shell_cmd = command
        run_detached = should_run_detached(command)

        if is_windows:
            if command.startswith("PS:"):
                shell_cmd = command[3:].strip()
                if run_detached:
                    subprocess.Popen(
                        ["powershell", "-Command", shell_cmd],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    time.sleep(0.5)
                    return {
                        "success": True,
                        "stdout": "Command launched",
                        "stderr": "",
                        "returncode": 0
                    }
                else:
                    result = subprocess.run(
                        ["powershell", "-Command", shell_cmd],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
            elif command.startswith("CMD:"):
                shell_cmd = command[4:].strip()
                if run_detached:
                    subprocess.Popen(
                        shell_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    time.sleep(0.5)
                    return {
                        "success": True,
                        "stdout": "Command launched",
                        "stderr": "",
                        "returncode": 0
                    }
                else:
                    result = subprocess.run(
                        shell_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
            else:
                if run_detached:
                    subprocess.Popen(
                        shell_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    time.sleep(0.5)
                    return {
                        "success": True,
                        "stdout": "Command launched",
                        "stderr": "",
                        "returncode": 0
                    }
                else:
                    result = subprocess.run(
                        shell_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
        else:
            if run_detached:
                subprocess.Popen(
                    shell_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                time.sleep(0.5)
                return {
                    "success": True,
                    "stdout": "Command launched",
                    "stderr": "",
                    "returncode": 0
                }
            else:
                result = subprocess.run(
                    shell_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15
                )

        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def execute_ai_response(response):
    response = response.strip()

    if '[' in response or 'TYPE:' in response or 'WAIT:' in response:
        log_to_console(f"Executing keystrokes: {response}")
        result = execute_keystroke_sequence(response)
        if result["success"]:
            log_to_console(f"{result['message']}")
            return {"success": True, "error": None}
        else:
            log_to_console(f"Keystroke failed: {result['error']}")
            return {"success": False, "error": result['error']}
    else:
        shell_type = "Command"
        if response.startswith("PS:"):
            shell_type = "PowerShell"
        elif response.startswith("CMD:"):
            shell_type = "CMD"

        log_to_console(f"{shell_type}: {response}")

        result = execute_command(response)

        if result["success"]:
            if result["stdout"] and result["stdout"] != "Command launched":
                log_to_console(result["stdout"])
            elif result["stdout"] == "Command launched":
                log_to_console("Command launched")
            if result["stderr"]:
                log_to_console(f"Error output: {result['stderr']}")
            if result["returncode"] != 0:
                return {"success": False, "error": f"Exit code {result['returncode']}"}
            return {"success": True, "error": None}
        else:
            log_to_console(f"Failed: {result['error']}")
            return {"success": False, "error": result['error']}

def get_ai_command(user_request, system_info, previous_error=None, prefer_keystrokes=False, screenshot=None):
    try:
        prompt = create_prompt(user_request, system_info, previous_error, prefer_keystrokes, screenshot)

        if screenshot:
            response = model.generate_content([prompt, screenshot])
        else:
            response = model.generate_content(prompt)

        command = response.text.strip()

        if command.startswith("ERROR:"):
            return None, command, False

        if command == "REFRESH_SYSINFO":
            return None, None, True

        return command, None, False
    except Exception as e:
        return None, f"ERROR: AI request failed - {str(e)}", False

def process_request_with_retry(user_input, system_info, max_retries=3, voice_mode=False):
    include_screenshot = False
    screenshot = None

    if user_input.endswith('/screen'):
        include_screenshot = True
        user_input = user_input[:-7].strip()
        log_to_console("Taking screenshot...")
        screenshot = take_screenshot()
        if screenshot:
            log_to_console("Screenshot captured")
        else:
            log_to_console("Screenshot failed, continuing without it")

    keystroke_keywords = ['keystroke', 'keyboard', 'gui', 'click', 'type into', 'fill out', 'create account', 'sign up', 'register']
    prefer_keystrokes = any(keyword in user_input.lower() for keyword in keystroke_keywords)

    if prefer_keystrokes:
        log_to_console("Using keyboard automation")

    previous_error = None
    current_sysinfo = system_info

    for attempt in range(max_retries):
        if attempt > 0:
            log_to_console(f"Retry {attempt}/{max_retries-1}")

        set_status(get_text("processing"), "#666666")
        show_processing(True)
        log_to_console("Analyzing request...")
        command, error, needs_refresh = get_ai_command(user_input, current_sysinfo, previous_error, prefer_keystrokes, screenshot)
        show_processing(False)

        if needs_refresh:
            log_to_console("Refreshing system info...")
            current_sysinfo = get_system_info()
            continue

        if error:
            log_to_console(f"{error}")
            if attempt < max_retries - 1:
                previous_error = error
                continue
            else:
                log_to_console("Max retries reached")
                set_status(get_text("ready"), "#000000")
                if voice_mode:
                    time.sleep(0.5)
                    speak(f"Error: {error}")
                return False

        result = execute_ai_response(command)

        if result["success"]:
            set_status(get_text("ready"), "#000000")
            if voice_mode:
                time.sleep(0.5)
                response = random.choice(SUCCESS_PHRASES[current_language])
                log_to_console(f"MIMI: {response}")
                speak(response)
            return True
        else:
            if attempt < max_retries - 1:
                previous_error = f"Command failed: {result['error']}"
                log_to_console(f"Sending error to AI for retry...")
            else:
                log_to_console("Max retries reached")
                set_status(get_text("ready"), "#000000")
                if voice_mode:
                    time.sleep(0.5)
                    speak(f"Task failed: {result['error']}")
                return False

    return False

def log_to_console(message, msg_type="info"):
    if console_output is None:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    console_output.insert(tk.END, f"[{timestamp}] {message}\n")
    console_output.see(tk.END)

def set_status(text, color="#000000"):
    if status_label:
        status_label.config(text=text, foreground=color)

def show_processing(active):
    if process_indicator:
        if active:
            process_indicator.config(text="●")
            animate_processing()
        else:
            process_indicator.config(text="")

def animate_processing():
    if process_indicator and process_indicator.cget("text") == "●":
        current = process_indicator.cget("foreground")
        new_color = "#999999" if current == "#333333" else "#333333"
        process_indicator.config(foreground=new_color)
        root.after(500, animate_processing)

def update_system_stats():
    if system_info_cache and cpu_label and mem_label:
        cpu = system_info_cache['cpu']['usage_percent']
        mem = system_info_cache['memory']['percent']

        root.after(0, lambda: cpu_label.config(text=f"CPU {cpu:.0f}%"))
        root.after(0, lambda: mem_label.config(text=f"RAM {mem:.0f}%"))

def toggle_language():
    global current_language, listening_active

    if listening_active:
        listening_active = False
        voice_button.config(text=get_text("start_voice"))
        log_to_console(get_text("voice_deactivated"))

    current_language = "es" if current_language == "en" else "en"

    voice_button.config(text=get_text("start_voice"))
    language_button.config(text=get_text("language"))
    set_status(get_text("ready"), "#000000")

    initialize_tts()

    log_to_console(f"Language changed to: {'Spanish' if current_language == 'es' else 'English'}")

def toggle_voice():
    global listening_active

    if not microphone:
        log_to_console(get_text("mic_unavailable"))
        return

    if listening_active:
        listening_active = False
        voice_button.config(text=get_text("start_voice"))
        log_to_console(get_text("voice_deactivated"))
        set_status(get_text("ready"), "#000000")
    else:
        listening_active = True
        voice_button.config(text=get_text("stop_voice"))
        threading.Thread(target=voice_input_loop, daemon=True).start()

def process_input(event=None):
    user_input = input_field.get().strip()
    if not user_input:
        return

    input_field.delete(0, tk.END)
    log_to_console(f"You: {user_input}")

    current_sysinfo = get_cached_system_info()
    threading.Thread(target=process_request_with_retry, args=(user_input, current_sysinfo), daemon=True).start()

def take_screenshot_command():
    current_text = input_field.get().strip()
    if not current_text.endswith('/screen'):
        input_field.delete(0, tk.END)
        input_field.insert(0, current_text + ' /screen' if current_text else '/screen')
    log_to_console(get_text("screenshot_mode"))

def clear_console():
    if console_output:
        console_output.delete(1.0, tk.END)
        log_to_console(get_text("console_cleared"))

def create_gui():
    global root, input_field, console_output, status_label, voice_button, cpu_label, mem_label, process_indicator, language_button

    root = tk.Tk()
    root.title(get_text("title"))
    root.geometry("900x700")
    root.configure(bg="#ffffff")
    
    try:
        root.iconbitmap('')
    except:
        pass

    root.attributes('-alpha', 0.97)
    root.attributes('-topmost', True)

    header = tk.Frame(root, bg="#ffffff", height=70)
    header.pack(fill=tk.X, padx=0, pady=0)
    header.pack_propagate(False)

    title_frame = tk.Frame(header, bg="#ffffff")
    title_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

    title_label = tk.Label(title_frame, text=get_text("title"), font=("Segoe UI", 22, "bold"), 
                           fg="#000000", bg="#ffffff")
    title_label.pack(side=tk.LEFT)

    stats_frame = tk.Frame(title_frame, bg="#ffffff")
    stats_frame.pack(side=tk.RIGHT)

    cpu_label = tk.Label(stats_frame, text="CPU --", font=("Segoe UI", 11), 
                        fg="#666666", bg="#ffffff")
    cpu_label.pack(side=tk.LEFT, padx=10)

    mem_label = tk.Label(stats_frame, text="RAM --", font=("Segoe UI", 11), 
                        fg="#666666", bg="#ffffff")
    mem_label.pack(side=tk.LEFT, padx=10)

    separator = tk.Frame(root, bg="#e5e5e5", height=1)
    separator.pack(fill=tk.X)

    status_frame = tk.Frame(root, bg="#ffffff", height=40)
    status_frame.pack(fill=tk.X)
    status_frame.pack_propagate(False)

    status_content = tk.Frame(status_frame, bg="#ffffff")
    status_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

    status_label = tk.Label(status_content, text=get_text("initializing"), font=("Segoe UI", 10), 
                           fg="#666666", bg="#ffffff", anchor=tk.W)
    status_label.pack(side=tk.LEFT)

    process_indicator = tk.Label(status_content, text="", font=("Segoe UI", 12), 
                                 fg="#333333", bg="#ffffff")
    process_indicator.pack(side=tk.RIGHT)

    console_frame = tk.Frame(root, bg="#ffffff")
    console_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

    console_output = scrolledtext.ScrolledText(console_frame, 
                                               wrap=tk.WORD,
                                               font=("Segoe UI", 10),
                                               bg="#f9f9f9",
                                               fg="#000000",
                                               insertbackground="#000000",
                                               selectbackground="#d4d4d4",
                                               relief=tk.FLAT,
                                               padx=15,
                                               pady=15,
                                               borderwidth=1)
    console_output.pack(fill=tk.BOTH, expand=True)
    console_output.configure(highlightthickness=1, highlightbackground="#e5e5e5", highlightcolor="#e5e5e5")

    control_frame = tk.Frame(root, bg="#ffffff")
    control_frame.pack(fill=tk.X, padx=30, pady=(0, 30))

    input_frame = tk.Frame(control_frame, bg="#f0f0f0", highlightthickness=1, 
                          highlightbackground="#d4d4d4", highlightcolor="#d4d4d4")
    input_frame.pack(fill=tk.X, pady=(0, 15))

    input_field = tk.Entry(input_frame,
                          font=("Segoe UI", 12),
                          bg="#f0f0f0",
                          fg="#000000",
                          insertbackground="#000000",
                          relief=tk.FLAT,
                          bd=0)
    input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=10, padx=15)
    input_field.bind("<Return>", process_input)
    input_field.focus()

    send_btn = tk.Button(input_frame, text=get_text("send"), 
                        font=("Segoe UI", 11),
                        bg="#f0f0f0", fg="#000000",
                        activebackground="#e0e0e0",
                        activeforeground="#000000",
                        relief=tk.FLAT,
                        bd=0,
                        padx=20,
                        cursor="hand2",
                        command=process_input)
    send_btn.pack(side=tk.LEFT, ipady=8, padx=(0, 10))

    button_frame = tk.Frame(control_frame, bg="#ffffff")
    button_frame.pack(fill=tk.X)

    voice_button = tk.Button(button_frame, text=get_text("start_voice"),
                            font=("Segoe UI", 10),
                            bg="#f0f0f0", fg="#000000",
                            activebackground="#e0e0e0",
                            activeforeground="#000000",
                            relief=tk.FLAT,
                            bd=0,
                            padx=15,
                            pady=8,
                            cursor="hand2",
                            command=toggle_voice)
    voice_button.pack(side=tk.LEFT, padx=(0, 10))

    language_button = tk.Button(button_frame, text=get_text("language"),
                               font=("Segoe UI", 10, "bold"),
                               bg="#f0f0f0", fg="#000000",
                               activebackground="#e0e0e0",
                               activeforeground="#000000",
                               relief=tk.FLAT,
                               bd=0,
                               padx=15,
                               pady=8,
                               cursor="hand2",
                               command=toggle_language)
    language_button.pack(side=tk.LEFT, padx=(0, 10))

    settings_button = tk.Button(button_frame, text="⚙",
                                font=("Segoe UI", 12),
                                bg="#f0f0f0", fg="#000000",
                                activebackground="#e0e0e0",
                                activeforeground="#000000",
                                relief=tk.FLAT,
                                bd=0,
                                padx=15,
                                pady=8,
                                cursor="hand2",
                                command=open_settings)
    settings_button.pack(side=tk.LEFT, padx=(0, 10))

    screenshot_btn = tk.Button(button_frame, text=get_text("screenshot"),
                              font=("Segoe UI", 10),
                              bg="#f0f0f0", fg="#000000",
                              activebackground="#e0e0e0",
                              activeforeground="#000000",
                              relief=tk.FLAT,
                              bd=0,
                              padx=15,
                              pady=8,
                              cursor="hand2",
                              command=take_screenshot_command)
    screenshot_btn.pack(side=tk.LEFT, padx=(0, 10))

    clear_btn = tk.Button(button_frame, text=get_text("clear"),
                         font=("Segoe UI", 10),
                         bg="#f0f0f0", fg="#000000",
                         activebackground="#e0e0e0",
                         activeforeground="#000000",
                         relief=tk.FLAT,
                         bd=0,
                         padx=15,
                         pady=8,
                         cursor="hand2",
                         command=clear_console)
    clear_btn.pack(side=tk.LEFT)

    return root

def initialize_system():
    global system_info_cache

    log_to_console("=" * 60)
    log_to_console("MIMI - Your Command-Line Assistant")
    log_to_console("=" * 60)
    log_to_console("Gathering system information...")

    set_status(get_text("initializing"), "#666666")

    system_info_cache = get_system_info()

    log_to_console(f"System: {system_info_cache['os']}")
    log_to_console(f"Shell: {system_info_cache['shell']}")
    log_to_console(f"CPU: {system_info_cache['cpu']['physical_cores']} cores @ {system_info_cache['cpu']['usage_percent']}%")
    log_to_console(f"Memory: {system_info_cache['memory']['used_gb']}GB / {system_info_cache['memory']['total_gb']}GB")
    log_to_console(f"Programs: {len(system_info_cache['installed_programs'])}")
    log_to_console(f"Processes: {len(system_info_cache['running_processes'])}")
    log_to_console(f"Directories indexed: {len(system_info_cache.get('directories', []))}")
    log_to_console(f"Desktop shortcuts: {len(system_info_cache.get('desktop_shortcuts', []))}")

    steam_count = len(system_info_cache.get('steam_games', []))
    epic_count = len(system_info_cache.get('epic_games', []))
    rockstar_count = len(system_info_cache.get('rockstar_games', []))
    ubisoft_count = len(system_info_cache.get('ubisoft_games', []))
    ea_count = len(system_info_cache.get('ea_games', []))
    gog_count = len(system_info_cache.get('gog_games', []))

    total_games = steam_count + epic_count + rockstar_count + ubisoft_count + ea_count + gog_count

    if total_games > 0:
        log_to_console(f"Games detected: {total_games} total")
        if steam_count > 0:
            log_to_console(f"  Steam: {steam_count}")
        if epic_count > 0:
            log_to_console(f"  Epic: {epic_count}")
        if rockstar_count > 0:
            log_to_console(f"  Rockstar: {rockstar_count}")
        if ubisoft_count > 0:
            log_to_console(f"  Ubisoft: {ubisoft_count}")
        if ea_count > 0:
            log_to_console(f"  EA/Origin: {ea_count}")
        if gog_count > 0:
            log_to_console(f"  GOG: {gog_count}")

    sysinfo_thread = threading.Thread(target=system_info_updater, daemon=True)
    sysinfo_thread.start()
    log_to_console("Background monitoring active (20s intervals)")

    tts_available = initialize_tts()
    if tts_available:
        log_to_console("Text-to-speech Ready")
    else:
        log_to_console("Text-to-speech Not available")

    mic_available = initialize_microphone()
    if mic_available:
        log_to_console("Microphone: Ready")
        log_to_console(get_text("voice_tip"))
    else:
        log_to_console("Microphone: Not available")

    log_to_console(get_text("screenshot_tip"))
    log_to_console("=" * 60)
    log_to_console(get_text("ready_msg"))
    log_to_console("")

    update_system_stats()
    set_status(get_text("ready"), "#000000")

def main():
    global root

    try:
        import google.generativeai
    except ImportError:
        print("Error: google-generativeai not found")
        print("Install: pip install google-generativeai")
        sys.exit(1)

    try:
        import pyautogui
    except ImportError:
        print("Error: pyautogui not found")
        print("Install: pip install pyautogui")
        sys.exit(1)

    try:
        import psutil
    except ImportError:
        print("Error: psutil not found")
        print("Install: pip install psutil")
        sys.exit(1)

    try:
        import speech_recognition
    except ImportError:
        print("Error: speech_recognition not found")
        print("Install: pip install SpeechRecognition pyaudio")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow not found")
        print("Install: pip install Pillow")
        sys.exit(1)

    try:
        from gtts import gTTS
    except ImportError:
        print("Error: gTTS not found")
        print("Install: pip install gtts")
        sys.exit(1)

    try:
        import pygame
    except ImportError:
        print("Error: pygame not found")
        print("Install: pip install pygame")
        sys.exit(1)

    root = create_gui()

    if not load_config():

        if not prompt_for_api_key():
            root.destroy()
            sys.exit(0)

    if not initialize_gemini():
        messagebox.showerror("Error", "Failed to initialize Gemini AI. Please check your API key.")
        root.destroy()
        sys.exit(1)

    threading.Thread(target=initialize_system, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":

    main()
