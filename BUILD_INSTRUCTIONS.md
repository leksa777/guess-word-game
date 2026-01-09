# Інструкції по збірці C++ DLL

## Проблема
Якщо категорії не відображаються в меню, це означає, що DLL не був перекомпільований з новим кодом, який підтримує категорії.

## Як перекомпілювати DLL

### Варіант 1: Через CMake (рекомендовано)

```bash
cd cpp_core
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

Після збірки скопіюйте `game_core.dll` з папки `build/Release/` до `python_ui/`:

```bash
copy build\Release\game_core.dll ..\..\python_ui\
```

### Варіант 2: Через Visual Studio

1. Відкрийте Visual Studio
2. File → Open → CMake... → виберіть `cpp_core/CMakeLists.txt`
3. Build → Build All
4. Скопіюйте `game_core.dll` з папки `build/Release/` до `python_ui/`

### Варіант 3: Через MinGW (якщо використовуєте MinGW)

```bash
cd cpp_core
g++ -shared -fPIC -std=c++17 -o game_core.dll GameEngine.cpp bridge.cpp -D_WIN32
```

## Перевірка

Після перекомпіляції запустіть:

```bash
python python_ui/app.py
```

У консолі мають з'явитися повідомлення:
- `[DEBUG] Available DLL functions: [...]` - має містити список функцій включаючи `get_categories`
- `[DEBUG] Categories string from DLL: Any|Programming|Technology|...` - має показати всі категорії

Якщо категорії все ще не відображаються, перевірте:
1. Чи файл `words.txt` містить формат `WORD;Category`
2. Чи DLL скопійовано в правильну папку (`python_ui/`)
3. Чи немає помилок компіляції

