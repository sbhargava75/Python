# CLAUDE.md

## Project Overview

Educational Python repository demonstrating basic data structures and text processing. Contains a word-frequency histogram generator that reads a text file and reports the most common words.

## Repository Structure

```
Python/
├── CLAUDE.md                # This file
└── DataStructures/
    └── histogram.py         # Word frequency histogram script
```

## Code Details

### DataStructures/histogram.py

Reads `data.txt` from the current working directory, counts word frequencies using a dictionary, and prints the top 5 most frequent words sorted in descending order.

- **Dependencies:** Python 3 standard library only (`re` is imported but unused)
- **Input:** Expects a file named `data.txt` in the working directory
- **Output:** Prints top 5 words by frequency to stdout

### Running

```bash
cd DataStructures
python3 histogram.py
```

A `data.txt` file must exist in the working directory or the script exits with an error message.

## Code Conventions

- **Style:** Procedural (no classes or functions), inline comments explaining each section
- **Variable naming:** camelCase for compound names (e.g., `newTuple`)
- **File I/O:** Manual open/close with try/except for `FileNotFoundError`
- **Python version:** Python 3 (uses f-string-compatible syntax, modern exception handling)

## Development

- **No build system** — no setup.py, pyproject.toml, or Makefile
- **No dependency management** — no requirements.txt or lock files
- **No test framework** — no tests directory, no pytest/unittest configuration
- **No CI/CD** — no GitHub Actions, no linting or formatting configuration

## Git

- **Primary branch:** `master`
- **Single initial commit** from September 2018
