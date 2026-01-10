#include "GameEngine.h"
#include <vector>
#include <string>
#include <cstring>

static guess_game::GameEngine engine;

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

extern "C" {

    EXPORT void init_db() {
        std::string error;
        engine.loadWordsFromFile("words.txt", error);
    }

    EXPORT void start_game(const char* category) {
        std::string error;
        engine.startNewGame(5, category, error);
    }

    EXPORT const char* get_secret() {
        static std::string secret;
        secret = engine.getSnapshot().currentWord;
        return secret.c_str();
    }

    EXPORT int get_lives() {
        return engine.getSnapshot().attemptsLeft;
    }

    //0-ABSENT, 1-PRESENT, 2-CORRECT
    EXPORT void check_word_guess(const char* guess, int* results) {
        std::vector<guess_game::LetterStatus> feedback;
        std::string error;
        
        if (engine.checkWord(guess, feedback, error)) {
            for (size_t i = 0; i < feedback.size(); ++i) {
                results[i] = static_cast<int>(feedback[i]);
            }
        }
    }

    //1 - перемога, -1 - поразка, 0 - гра триває
    EXPORT int get_game_status() {
        auto snapshot = engine.getSnapshot();
        if (snapshot.won) return 1;
        if (snapshot.lost) return -1;
        return 0;
    }

    EXPORT const char* get_categories() {
        static std::string cats;
        cats = engine.getAvailableCategories();
        for (char &c : cats) if (c == ',') c = '|';
        return cats.c_str();
    }
}