# Guess The Word (Python + C++)

Гібридний проєкт курсової роботи: ядро гри реалізовано на C++ з експортом у вигляді `game_core.dll`, інтерфейс та інтеграція — на Python (CustomTkinter + ctypes).

## Структура

- `cpp_core/` — C++ проєкт (CMake) з класом `GameEngine` та C API.
- `python_ui/` — графічний застосунок, що звертається до DLL.
- `words.txt` — словник, з якого ядро випадково обирає слова (формат: `WORD;Category`).

## Швидкий старт

### 1. Перекомпіляція DLL (якщо категорії не відображаються)

**Windows (PowerShell):**
```powershell
.\rebuild_dll.ps1
```

**Або вручну:**
```bash
cd cpp_core
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
# Скопіюйте game_core.dll з build/Release/ до python_ui/
```

### 2. Запуск Python UI

```bash
cd python_ui
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

## Особливості

- **Швидке ядро на C++** (`GameEngine`) з читанням словника, підтримкою категорій, підрахунком спроб та очок.
- **Python-інтерфейс** із сучасним виглядом (CustomTkinter), Wordle-стилем, віртуальною клавіатурою та статистикою.
- **Категорії слів**: обирайте категорію перед грою (Programming, Technology, Food, тощо)
- **Двомовність**: перемикання між англійською та українською мовами
- **Зв'язок між мовами** через `ctypes` та просту структуру `GameStateDTO`.

## Формат words.txt

Кожен рядок має формат: `WORD;Category`

Приклад:
```
PYTHON;Programming
APPLE;Fruit
LONDON;City
```

## Якщо категорії не відображаються

1. Переконайтеся, що DLL перекомпільовано: `.\rebuild_dll.ps1`
2. Перевірте, чи файл `words.txt` містить формат `WORD;Category`
3. Перевірте консоль на наявність помилок при запуску

Див. `BUILD_INSTRUCTIONS.md` для детальніших інструкцій.
