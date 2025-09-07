import subprocess
import sys
import os
import platform
import requests
import time
from pathlib import Path
from datetime import timedelta

def log_time(step_name, start_time):
    """Логирует время выполнения этапа"""
    elapsed = time.time() - start_time
    print(f"⏱️  {step_name} заняло: {timedelta(seconds=int(elapsed))}")

def run_command(command, check=True, shell_override=None):
    """
    Универсальная функция для выполнения команд в оболочке с обработкой ошибок.
    """
    # Определяем, нужно ли использовать shell=True (по умолчанию для Windows, False для Unix)
    if shell_override is None:
        shell_override = (platform.system() == "Windows")
    
    try:
        print(f"🛠️ Выполняется команда: {command}")
        result = subprocess.run(command, shell=shell_override, check=check, capture_output=True, text=True, timeout=300)
        print(f"✅ Успех: {result.stdout}")
        return result.stdout, True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении команды '{command}': {e.stderr}")
        return e.stderr, False
    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут при выполнении команды: {command}")
        return "Timeout", False

def install_ffmpeg():
    """Устанавливает FFmpeg в зависимости от операционной системы."""
    step_start = time.time()
    system = platform.system()
    print(f"🔍 Обнаружена система: {system}")
    
    if system == "Linux":
        # Попытка определить дистрибутив Linux
        try:
            with open('/etc/os-release') as f:
                content = f.read()
                if 'Ubuntu' in content or 'Debian' in content:
                    print("🟦 Обнаружен дистрибутив на основе Debian (Ubuntu, Debian).")
                    # Обновление индексов пакетов и установка ffmpeg
                    run_command("sudo apt update", shell_override=False)
                    run_command("sudo apt install -y ffmpeg", shell_override=False)
                elif 'Fedora' in content or 'CentOS' in content:
                    print("🟥 Обнаружен дистрибутив на основе RedHat (Fedora, CentOS).")
                    # Добавление репозитория RPM Fusion и установка ffmpeg (может потребовать согласия)
                    run_command("sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm", shell_override=False)
                    run_command("sudo dnf install -y https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm", shell_override=False)
                    run_command("sudo dnf install -y ffmpeg", shell_override=False)
                elif 'Arch' in content or 'Manjaro' in content:
                    print("🟪 Обнаружен дистрибутив на основе Arch (Arch Linux, Manjaro).")
                    run_command("sudo pacman -Sy --noconfirm ffmpeg", shell_override=False)
                else:
                    print("❓ Не удалось определить дистрибутив Linux. Установите FFmpeg вручную.")
                    return False
        except FileNotFoundError:
            print("❓ Не удалось прочитать /etc/os-release. Установите FFmpeg вручную.")
            return False

    elif system == "Darwin":  # macOS
        print("🍎 Обнаружена macOS.")
        # Проверяем, установлен ли Homebrew
        brew_check = subprocess.run("command -v brew", shell=True, capture_output=True, text=True)
        if brew_check.returncode != 0:
            print("📦 Установка Homebrew...")
            install_script = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            run_command(install_script, shell_override=True)
        # Устанавливаем или обновляем FFmpeg через Homebrew
        run_command("brew install ffmpeg", shell_override=True)

    elif system == "Windows":
        print("🪟 Обнаружена Windows.")
        # Рекомендуется установить через Chocolatey или Scoop, либо вручную
        print("👈 Рекомендуется установить FFmpeg вручную или с помощью менеджера пакетов (Chocolatey: 'choco install ffmpeg').")
        print("   См. инструкцию: https://www.ffmpeg.org/download.html#build-windows")
        # Можно реализовать автоматическую установку через Chocolatey, если он есть
        choco_check = subprocess.run("choco --version", shell=True, capture_output=True, text=True)
        if choco_check.returncode == 0:
            print("🍫 Обнаружен Chocolatey, пытаемся установить FFmpeg...")
            run_command("choco install -y ffmpeg", shell_override=True)
        else:
            print("❌ Chocolatey не найден. Установите FFmpeg вручную.")
            return False
    else:
        print(f"❓ Неподдерживаемая операционная система: {system}")
        return False

    # Проверяем, установился ли FFmpeg
    ffmpeg_check = subprocess.run("ffmpeg -version", shell=True, capture_output=True, text=True)
    if ffmpeg_check.returncode == 0:
        print(f"✅ FFmpeg успешно установлен. Версия:\n{ffmpeg_check.stdout.splitlines()[0]}")
    else:
        print("❌ Проверка версии FFmpeg не удалась. Возможно, потребуется перезапустить терминал или добавить его в PATH.")
        return False
    
    log_time("Установка FFmpeg", step_start)
    return True

def install_whisper():
    """
    Устанавливает OpenAI Whisper и загружает модель large-v3.
    """
    step_start = time.time()
    
    print("📻 Установка OpenAI Whisper...")
    # Устанавливаем пакет
    output, success = run_command([sys.executable, "-m", "pip", "install", "-U", "openai-whisper"])
    if not success:
        print("❌ Не удалось установить openai-whisper.")
        return False
    
    # Попытка проверить установку, импортировав whisper и загрузив модель base (для экономии времени на проверку)
    print("🔍 Проверка установки Whisper...")
    try:
        import whisper
        # Пробуем загрузить маленькую модель для проверки
        model = whisper.load_model("base")
        print("✅ Whisper установлен и работает корректно.")
        # Сообщаем, что large-v3 будет загружена при первом использовании
        print("ℹ️  Модель 'large-v3' будет автоматически загружена при первом вызове транскрибации.")
    except Exception as e:
        print(f"❌ Проверка Whisper не удалась: {e}")
        return False

    log_time("Установка Whisper", step_start)
    return True

def install_nemo():
    """
    Устанавливает NVIDIA NeMo Toolkit.
    Установка через pip может быть проблематичной, особенно на macOS и Windows.
    """
    step_start = time.time()
    
    print("🎙️ Установка NVIDIA NeMo Toolkit...")
    # Рекомендуется устанавливать в виртуальном окружении и предварительно установить torch и torchaudio
    # Сначала попробуем установить зависимости
    pip_commands = [
        [sys.executable, "-m", "pip", "install", "torch", "torchaudio", "torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"],
        [sys.executable, "-m", "pip", "install", "Cython"],
        [sys.executable, "-m", "pip", "install", "'nemo_toolkit[all]'"] # Пробуем установить все зависимости
    ]

    for cmd in pip_commands:
        output, success = run_command(cmd)
        if not success and "nemo_toolkit" in cmd[-1]:
            print("⚠️  Возникли проблемы при установке nemo_toolkit[all]. Пробуем установить базовую версию...")
            # Пробуем установить без [all]
            output, success = run_command([sys.executable, "-m", "pip", "install", "nemo_toolkit"])
            if success:
                print("✅ Nemo Toolkit (базовая версия) установлен.")
                print("ℹ️  Для полноценной работы с диаризацией могут потребоваться дополнительные зависимости.")
            else:
                print("❌ Не удалось установить даже базовую версию Nemo.")
                print("💡 Рекомендуется использовать Docker-образ NVIDIA NeMo для гарантированной работы.")
                return False
    
    log_time("Установка NeMo", step_start)
    return True

def install_ollama_and_gemma():
    """
    Устанавливает Ollama и загружает модель gemma3:27b.
    """
    step_start = time.time()
    
    system = platform.system()
    print(f"🤖 Установка Ollama для {system}...")

    if system == "Linux":
        # Установка через официальный скрипт
        output, success = run_command("curl -fsSL https://ollama.com/install.sh | sh", shell_override=True)
    elif system == "Darwin":  # macOS
        # Проверяем, установлен ли Homebrew
        brew_check = subprocess.run("command -v brew", shell=True, capture_output=True, text=True)
        if brew_check.returncode == 0:
            output, success = run_command("brew install ollama", shell_override=True)
        else:
            # Установка через скрипт
            output, success = run_command("curl -fsSL https://ollama.com/install.sh | sh", shell_override=True)
    elif system == "Windows":
        print("👈 Для Windows загрузите и установите Ollama вручную с https://ollama.com/download")
        print("   После установки убедитесь, что сервис Ollama запущен, и вернитесь в скрипт.")
        # Даем пользователю время на установку
        input("Нажмите Enter после установки и запуска Ollama...")
        success = True
    else:
        print(f"❌ Неподдерживаемая система для автоматической установки Ollama: {system}")
        success = False

    if not success:
        print("❌ Не удалось установить Ollama.")
        return False

    # Запускаем сервер Ollama (на Linux/macOS он часто запускается автоматически как служба)
    if system != "Windows":
        # Пытаемся запустить сервер, если он не запущен
        run_command("ollama serve > /dev/null 2>&1 &", shell_override=True, check=False)
        time.sleep(3) # Даем серверу время на запуск

    # Проверяем, работает ли сервер Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Сервер Ollama запущен и отвечает.")
        else:
            print("⚠️ Сервер Ollama не ответил кодом 200. Возможно, потребуется его перезапуск.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Не удалось подключиться к серверу Ollama. Попробуйте запустить его вручную командой 'ollama serve'.")
        success = False

    # Загружаем модель gemma3:27b
    if success:
        print("📥 Загрузка модели gemma3:27b (это может занять время и потребовать ~12 ГБ места)...")
        output, success = run_command("ollama pull gemma3:27b", shell_override=True)
        if success:
            print("✅ Модель gemma3:27b успешно загружена.")
        else:
            print("❌ Не удалось загрузить модель gemma3:27b.")
    
    log_time("Установка Ollama и загрузка модели", step_start)
    return success

def create_processing_script():
    """
    Создает финальный Python-скрипт для обработки аудиофайлов.
    """
    step_start = time.time()
    
    script_content = '''import subprocess
import requests
import json
import time
import os
import sys
from pathlib import Path
from datetime import timedelta
import threading
import itertools

class Spinner:
    """Класс для отображения индикатора загрузки"""
    def __init__(self, message="Загрузка..."):
        self.spinner = itertools.cycle(['-', '/', '|', '\\\\'])
        self.message = message
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(next(self.spinner) + ' ' + self.message + '\\r')
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\\r' + ' ' * (len(self.message) + 2) + '\\r')
            sys.stdout.flush()

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        self.thread.join()
        sys.stdout.write('\\r' + ' ' * (len(self.message) + 2) + '\\r')
        sys.stdout.flush()

def log_step_time(func):
    """Декоратор для логирования времени выполнения функций"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"⏱️ Время выполнения '{func.__name__}': {timedelta(seconds=int(elapsed))}")
        return result
    return wrapper

@log_step_time
def check_ollama_server():
    """Проверяет, запущен ли сервер Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

@log_step_time
def start_ollama_server():
    """Запускает сервер Ollama в фоновом режиме"""
    try:
        with Spinner("🔄 Запускаем сервер Ollama..."):
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(5)
            
            for _ in range(10):
                if check_ollama_server():
                    print("✅ Сервер Ollama успешно запущен")
                    return process
                time.sleep(2)
        
        print("❌ Не удалось запустить сервер Ollama")
        return None
    except Exception as e:
        print(f"❌ Ошибка при запуске сервера Ollama: {e}")
        return None

@log_step_time
def ensure_gemma_model():
    """Убеждается, что модель Gemma 3 27B доступна"""
    try:
        with Spinner("🔍 Проверяем наличие модели Gemma 3 27B..."):
            response = requests.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            
            gemma_models = [m for m in models if "gemma3" in m.get("name", "").lower() and "27b" in m.get("name", "")]
            
            if not gemma_models:
                print("📥 Модель Gemma 3 27B не найдена, начинаем загрузку...")
                subprocess.run(["ollama", "pull", "gemma3:27b"], check=True)
                print("✅ Модель Gemma 3 27B успешно загружена")
            else:
                print("✅ Модель Gemma 3 27B уже доступна")
                
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке/загрузке модели: {e}")
        return False

@log_step_time
def transcribe_audio(audio_path):
    """Транскрибирует аудио с помощью Whisper large-v3"""
    try:
        with Spinner("🎙️ Транскрибируем аудио с помощью Whisper large-v3..."):
            # Используем Whisper для транскрибации
            result = subprocess.run([
                "whisper", audio_path, 
                "--model", "large-v3",
                "--language", "ru",
                "--output_format", "txt"
            ], capture_output=True, text=True, check=True)
            
            # Читаем результат из файла
            base_name = Path(audio_path).stem
            txt_path = f"{base_name}.txt"
            with open(txt_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
        
        print("✅ Транскрибация завершена")
        return transcript, txt_path
    except Exception as e:
        print(f"❌ Неожиданная ошибка при транскрибации: {e}")
        return None, None

@log_step_time
def summarize_text(text):
    """Создает краткое содержание текста с помощью Ollama и Gemma 3 27B"""
    try:
        with Spinner("🧠 Создаем краткое содержание с помощью Gemma 3 27B..."):
            prompt = f"""
            Создай подробное краткое содержание следующего текста встречи в формате Markdown.
            Включи следующие разделы:
            - Основные темы обсуждения
            - Ключевые решения
            - Действия и ответственные
            - Следующие шаги
            - Общая тональность встречи
            
            Текст встречи:
            {text[:12000]}
            """
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:27b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_ctx": 8192  # Размер контекста
                    }
                },
                timeout=60*60*3  # Увеличиваем таймаут для больших текстов
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("response", "")
                print("✅ Саммаризация завершена")
                return summary
            else:
                print(f"❌ Ошибка саммаризации: {response.text}")
                return None

    except Exception as e:
        print(f"❌ Неожиданная ошибка при саммаризации: {e}")
        return None

@log_step_time
def save_markdown(summary, output_path):
    """Сохраняет результат в Markdown файл"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ Результат сохранен в файл: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        return False

def main():
    script_start_time = time.time()
    print("🚀 Начало процесса обработки аудио\\n")

    if len(sys.argv) < 2:
        print("❌ Укажите путь к аудиофайлу в качестве аргумента.")
        print("   Пример: python summarize.py audio.m4a")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print(f"❌ Аудиофайл {audio_path} не найден")
        sys.exit(1)
    
    # Проверяем и запускаем сервер Ollama
    ollama_process = None
    if not check_ollama_server():
        ollama_process = start_ollama_server()
        if not ollama_process:
            print("❌ Не удалось запустить Ollama. Убедитесь, что Ollama установлен.")
            sys.exit(1)
    
    # Убеждаемся, что модель Gemma доступна
    if not ensure_gemma_model():
        print("❌ Не удалось загрузить модель Gemma 3 27B")
        if ollama_process:
            ollama_process.terminate()
        sys.exit(1)
    
    # Транскрибируем аудио
    transcript, transcript_path = transcribe_audio(audio_path)
    if not transcript:
        print("❌ Не удалось транскрибировать аудио")
        if ollama_process:
            ollama_process.terminate()
        sys.exit(1)
    
    # Создаем краткое содержание
    summary = summarize_text(transcript)
    if not summary:
        print("❌ Не удалось создать краткое содержание")
        if ollama_process:
            ollama_process.terminate()
        sys.exit(1)
    
    # Сохраняем результат
    base_name = Path(audio_path).stem
    output_path = f"{base_name}_summary.md"
    if save_markdown(summary, output_path):
        print("🎉 Процесс завершен успешно!")
    else:
        print("⚠️ Процесс завершен с ошибками при сохранении")
    
    # Останавливаем сервер Ollama, если мы его запускали
    if ollama_process:
        with Spinner("🛑 Останавливаем сервер Ollama..."):
            ollama_process.terminate()
            try:
                ollama_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                ollama_process.kill()
    
    print(f"📝 Полный транскрипт сохранен в {transcript_path}")

    total_time = time.time() - script_start_time
    print(f"\\n🕐 ОБЩЕЕ ВРЕМЯ ВЫПОЛНЕНИЯ: {timedelta(seconds=int(total_time))}")

if __name__ == "__main__":
    main()
'''
    script_filename = "summarize.py"
    try:
        with open(script_filename, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"✅ Финальный скрипт сохранен как {script_filename}")
        # Делаем скрипт исполняемым (для Unix-систем)
        if platform.system() != "Windows":
            os.chmod(script_filename, 0o755)
    except Exception as e:
        print(f"❌ Не удалось создать скрипт {script_filename}: {e}")
        return False
    
    log_time("Создание скрипта обработки", step_start)
    return True

def main():
    """
    Основная функция, которая запускает весь процесс установки.
    """
    # Переменная для хранения времени начала выполнения скрипта
    script_start_time = time.time()
    print("🚀 Начинаем установку всех необходимых компонентов...")
    
    # Создаем словарь для хранения времени выполнения каждого этапа
    step_times = {}
    
    # 1. Установка FFmpeg
    print("\n" + "="*50)
    print("1. УСТАНОВКА FFMPEG")
    print("="*50)
    step_start = time.time()
    ffmpeg_ok = install_ffmpeg()
    step_times["FFmpeg"] = time.time() - step_start
    
    # 2. Установка Whisper
    print("\n" + "="*50)
    print("2. УСТАНОВКА OPENAI WHISPER")
    print("="*50)
    step_start = time.time()
    whisper_ok = install_whisper()
    step_times["Whisper"] = time.time() - step_start
    
    # 3. Установка NeMo
    print("\n" + "="*50)
    print("3. УСТАНОВКА NVIDIA NEMO")
    print("="*50)
    step_start = time.time()
    nemo_ok = install_nemo()
    step_times["NeMo"] = time.time() - step_start
    
    # 4. Установка Ollama и модели Gemma
    print("\n" + "="*50)
    print("4. УСТАНОВКА OLLAMA И МОДЕЛИ GEMMA 3 27B")
    print("="*50)
    step_start = time.time()
    ollama_ok = install_ollama_and_gemma()
    step_times["Ollama"] = time.time() - step_start
    
    # 5. Создание финального скрипта
    print("\n" + "="*50)
    print("5. СОЗДАНИЕ ФИНАЛЬНОГО СКРИПТА")
    print("="*50)
    step_start = time.time()
    script_ok = create_processing_script()
    step_times["Создание скрипта"] = time.time() - step_start
    
    # Итоговый отчет
    total_time = time.time() - script_start_time
    print("\n" + "="*50)
    print("УСТАНОВКА ЗАВЕРШЕНА")
    print("="*50)
    print("Статус установки компонентов:")
    print(f"  FFmpeg: {'✅' if ffmpeg_ok else '❌'}")
    print(f"  Whisper: {'✅' if whisper_ok else '❌'}")
    print(f"  NVIDIA NeMo: {'✅' if nemo_ok else '❌'}")
    print(f"  Ollama & Gemma3:27b: {'✅' if ollama_ok else '❌'}")
    print(f"  Финальный скрипт: {'✅' if script_ok else '❌'}")
    
    # Выводим время выполнения каждого этапа
    print("\n⏱️  ВРЕМЯ ВЫПОЛНЕНИЯ ЭТАПОВ:")
    for step, duration in step_times.items():
        print(f"  {step}: {timedelta(seconds=int(duration))}")
    
    print(f"\n🕐 ОБЩЕЕ ВРЕМЯ УСТАНОВКИ: {timedelta(seconds=int(total_time))}")
    
    if all([ffmpeg_ok, whisper_ok, nemo_ok, ollama_ok, script_ok]):
        print("\n🎉 Все компоненты успешно установлены!")
        print("\n📖 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:")
        print("   1. Поместите ваш аудиофайл (например, meeting.m4a) в ту же папку.")
        print("   2. Запустите скрипт обработки, указав путь к аудиофайлу:")
        print("      python summarize.py meeting.m4a")
        print("   3. Результат будет сохранен в файле meeting_summary.md")
    else:
        print("\n⚠️  Некоторые компоненты установлены с ошибками.")
        print("   Пожалуйста, проверьте вывод выше и установите недостающие компоненты вручную.")
    
    print("\n💡 ПРИМЕЧАНИЯ:")
    print("   - Для работы Whisper large-v3 требуется около 12 ГБ VRAM/ОЗУ.")
    print("   - Модель Gemma3:27b требует около 12 ГБ места и достаточного объема ОЗУ/VRAM.")
    print("   - Первый запуск транскрибации займет время на загрузку модели large-v3.")

if __name__ == "__main__":
    main()