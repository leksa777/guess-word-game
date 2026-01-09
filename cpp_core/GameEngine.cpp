#include "GameEngine.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <random>
#include <map>

namespace guess_game {

bool GameEngine::loadWordsFromFile(const std::string& path, std::string& error) {
    std::ifstream file(path);
    if (!file.is_open()) {
        error = "File not found: " + path;
        return false;
    }

    words_.clear();
    std::string line;
    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string w, c;
        if (ss >> w >> c) {
            words_.push_back({w, c}); 
        }
    }
    return true;
}

bool GameEngine::startNewGame(int attempts, const std::string& category, std::string& error) {
    std::vector<WordEntry> candidates;
    for (const auto& entry : words_) {
        if (category == "Any" || entry.category == category) {
            candidates.push_back(entry);
        }
    }

    if (candidates.empty()) {
        error = "No words in category";
        return false;
    }

    currentWord_ = pickRandomWord(candidates);
    currentCategory_ = category;
    maskedWord_ = std::string(currentWord_.size(), '?');
    attemptsLeft_ = attempts;
    won_ = false;
    lost_ = false;
    usedLetters_.clear();
    return true;
}

bool GameEngine::checkWord(const std::string& guess, std::vector<LetterStatus>& feedback, std::string& error) {
    if (guess.size() != currentWord_.size()) {
        error = "Invalid length";
        return false;
    }

    feedback.assign(currentWord_.size(), LetterStatus::Absent);
    
    std::map<char, int> counts;
    for (char c : currentWord_) counts[c]++;

    //перший прохід: CORRECT (Зелений)
    for (size_t i = 0; i < currentWord_.size(); ++i) {
        if (guess[i] == currentWord_[i]) {
            feedback[i] = LetterStatus::Correct;
            counts[guess[i]]--;
        }
    }

    //другий прохід: PRESENT (Жовтий)
    for (size_t i = 0; i < currentWord_.size(); ++i) {
        if (feedback[i] == LetterStatus::Correct) continue;
        if (counts[guess[i]] > 0) {
            feedback[i] = LetterStatus::Present;
            counts[guess[i]]--;
        }
    }

    attemptsLeft_--;
    if (guess == currentWord_) won_ = true;
    else if (attemptsLeft_ <= 0) lost_ = true;

    return true;
}

std::string GameEngine::getAvailableCategories() const {
    std::unordered_set<std::string> unique_cats;
    for (const auto& e : words_) unique_cats.insert(e.category);
    
    std::string res = "Any";
    for (const auto& c : unique_cats) res += "," + c;
    return res;
}

std::string GameEngine::pickRandomWord(const std::vector<WordEntry>& candidates) const {
    static std::mt19937 gen(std::random_device{}());
    std::uniform_int_distribution<> dis(0, candidates.size() - 1);
    return candidates[dis(gen)].word;
}

GameSnapshot GameEngine::getSnapshot() const {
    return { currentWord_, maskedWord_, attemptsLeft_, score_, won_, lost_ };
}

GuessResult GameEngine::checkLetter(char letter, std::string& error) {
    if (usedLetters_.count(letter)) return GuessResult::Repeat;
    usedLetters_.insert(letter);
    bool hit = false;
    for (size_t i = 0; i < currentWord_.size(); ++i) {
        if (currentWord_[i] == letter) {
            maskedWord_[i] = letter;
            hit = true;
        }
    }
    if (hit) return GuessResult::Hit;
    attemptsLeft_--;
    return GuessResult::Miss;
}

} 