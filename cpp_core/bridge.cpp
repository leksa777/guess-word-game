#include "GameEngine.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <fstream>
#include <random>
#include <stdexcept>
#include <vector>
#include <string>

namespace guess_game {

namespace {

char normalizeLetter(char letter) {
    return static_cast<char>(std::toupper(static_cast<unsigned char>(letter)));
}

void trim(std::string& text) {
    const auto start = text.find_first_not_of(" \t\r\n");
    const auto end = text.find_last_not_of(" \t\r\n");
    if (start == std::string::npos || end == std::string::npos) {
        text.clear();
        return;
    }
    text = text.substr(start, end - start + 1);
}

std::string maskWord(const std::string& word) {
    std::string masked(word);
    std::transform(masked.begin(), masked.end(), masked.begin(), [](unsigned char ch) {
        return std::isalpha(ch) ? '*' : ch;
    });
    return masked;
}

} // namespace

bool GameEngine::loadWordsFromFile(const std::string& path, std::string& error) {
    std::ifstream input(path);
    if (!input) {
        error = "Cannot open words file: " + path;
        return false;
    }

    std::vector<std::string> result;
    std::string line;
    while (std::getline(input, line)) {
        trim(line);
        if (line.empty()) {
            continue;
        }
        std::transform(line.begin(), line.end(), line.begin(), [](unsigned char ch) {
            return static_cast<char>(std::toupper(ch));
        });
        result.push_back(line);
    }

    if (result.empty()) {
        error = "Words file is empty: " + path;
        return false;
    }

    words_ = std::move(result);
    return true;
}

bool GameEngine::startNewGame(int attempts, std::string& error) {
    if (attempts <= 0) {
        error = "Attempts must be positive";
        return false;
    }

    if (!ensureWordsLoaded(error)) {
        return false;
    }

    currentWord_ = pickRandomWord();
    maskedWord_ = std::string(currentWord_.size(), '?');
    usedLetters_.clear();
    attemptsLeft_ = attempts;
    won_ = false;
    lost_ = false;
    score_ = 0;

    return true;
}

GuessResult GameEngine::checkLetter(char letter, std::string& error) {
    if (won_ || lost_) {
        error = "Game already concluded";
        return GuessResult::Invalid;
    }

    if (!std::isalpha(static_cast<unsigned char>(letter))) {
        error = "Letter must be alphabetical";
        return GuessResult::Invalid;
    }

    char normalized = normalizeLetter(letter);
    if (usedLetters_.count(normalized)) {
        return GuessResult::Repeat;
    }
    usedLetters_.insert(normalized);

    if (currentWord_.find(normalized) != std::string::npos) {
        revealLetter(normalized);
        score_ += 10;
        if (maskedWord_ == currentWord_) {
            won_ = true;
        }
        return GuessResult::Hit;
    }

    --attemptsLeft_;
    score_ = std::max(0, score_ - 5);
    if (attemptsLeft_ <= 0) {
        lost_ = true;
    }
    return GuessResult::Miss;
}

const GameSnapshot GameEngine::getSnapshot() const {
    GameSnapshot snapshot;
    snapshot.currentWord = currentWord_;
    snapshot.maskedWord = maskedWord_;
    snapshot.attemptsLeft = attemptsLeft_;
    snapshot.score = score_;
    snapshot.won = won_;
    snapshot.lost = lost_;
    return snapshot;
}

std::string GameEngine::pickRandomWord() const {
    if (words_.empty()) {
        throw std::runtime_error("No words loaded");
    }
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<std::size_t> dist(0, words_.size() - 1);
    return words_[dist(rng)];
}

void GameEngine::revealLetter(char letter) {
    for (std::size_t i = 0; i < currentWord_.size(); ++i) {
        if (currentWord_[i] == letter) {
            maskedWord_[i] = letter;
        }
    }
}

bool GameEngine::ensureWordsLoaded(std::string& error) const {
    if (words_.empty()) {
        error = "No words loaded";
        return false;
    }
    return true;
}

bool GameEngine::checkWord(const std::string& guess, std::vector<LetterStatus>& feedback, std::string& error) {
    if (won_ || lost_) {
        error = "Game already concluded";
        return false;
    }

    if (guess.size() != currentWord_.size()) {
        error = "Guess length mismatch";
        return false;
    }

    std::string normalized = guess;
    std::transform(normalized.begin(), normalized.end(), normalized.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });

    for (unsigned char ch : normalized) {
        if (!std::isalpha(ch)) {
            error = "Guess must contain only letters";
            return false;
        }
    }

    feedback.assign(currentWord_.size(), LetterStatus::Absent);

    std::array<int, 26> counts{};
    for (char ch : currentWord_) {
        if (std::isalpha(static_cast<unsigned char>(ch))) {
            counts[ch - 'A']++;
        }
    }

    for (std::size_t i = 0; i < currentWord_.size(); ++i) {
        if (normalized[i] == currentWord_[i]) {
            feedback[i] = LetterStatus::Correct;
            counts[normalized[i] - 'A']--;
        }
    }

    for (std::size_t i = 0; i < currentWord_.size(); ++i) {
        if (feedback[i] == LetterStatus::Correct) {
            continue;
        }
        char ch = normalized[i];
        if (counts[ch - 'A'] > 0) {
            feedback[i] = LetterStatus::Present;
            counts[ch - 'A']--;
        }
    }

    if (normalized == currentWord_) {
        won_ = true;
        maskedWord_ = currentWord_;
        score_ += 50;
    } else {
        --attemptsLeft_;
        score_ = std::max(0, score_ - 5);
        if (attemptsLeft_ <= 0) {
            lost_ = true;
        }
    }
    return true;
}
