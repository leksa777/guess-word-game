#pragma once

#include <string>
#include <vector>
#include <unordered_set>
#include <iostream>

namespace guess_game {

enum class LetterStatus {
    Correct = 0, 
    Present = 1, 
    Absent = 2  
};

enum class GuessResult {
    Hit = 0, Miss = 1, Repeat = 2, Invalid = 3
};

struct WordEntry {
    std::string word;
    std::string category;
};

struct GameSnapshot {
    std::string currentWord;
    std::string maskedWord;
    int attemptsLeft = 0;
    int score = 0;
    bool won = false;
    bool lost = false;
};

class GameEngine {
public:
    bool loadWordsFromFile(const std::string& path, std::string& error);
    
    bool startNewGame(int attempts, const std::string& category, std::string& error);
    
    bool checkWord(const std::string& guess, std::vector<LetterStatus>& feedback, std::string& error);
    
    GuessResult checkLetter(char letter, std::string& error);

    std::string getAvailableCategories() const;
    const std::string& getCurrentCategory() const { return currentCategory_; }
    bool isWin() const { return won_; }
    bool isLose() const { return lost_; }
    GameSnapshot getSnapshot() const;

private:
    std::string pickRandomWord(const std::vector<WordEntry>& candidates) const;
    
    //інкапсуляція
    std::vector<WordEntry> words_{}; 
    std::string currentWord_{};
    std::string currentCategory_{}; 
    std::string maskedWord_{};
    std::unordered_set<char> usedLetters_{};
    
    int attemptsLeft_{0};
    int score_{0};
    bool won_{false};
    bool lost_{false};
};

}