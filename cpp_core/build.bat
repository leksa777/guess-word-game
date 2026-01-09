@echo off
echo Компілюємо з примусовим експортом функцій...
cl /EHsc /MD /LD bridge.cpp GameEngine.cpp ^
   /link ^
   /EXPORT:init_db ^
   /EXPORT:get_categories ^
   /EXPORT:get_category ^
   /EXPORT:start_game ^
   /EXPORT:check_word_guess ^
   /EXPORT:get_secret ^
   /EXPORT:get_lives ^
   /EXPORT:get_game_status ^
   /OUT:game_core.dll

if exist game_core.dll (
    echo.
    echo SUCCESS: game_core.dll створено УСПІШНО!
    copy game_core.dll "..\python_ui\" /Y
    echo DLL скопійовано в python_ui\
) else (
    echo.
    echo ERROR: Не вдалося створити DLL
)
pause