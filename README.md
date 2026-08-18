# Resume Keyword Ranking Tool

A desktop GUI tool that parses multiple resumes (plain text files) and ranks them by how well they match a given job description — combining keyword frequency analysis with a proper string-searching algorithm (KMP) for exact phrase matching.

## What It Does

- Paste in a job description
- Optionally list required phrases (e.g. `machine learning, project management`) that must appear as exact phrases, not just individual words
- Load any number of resume `.txt` files at once
- Rank all resumes by a combined match score, highest first
- View, per resume, exactly which keywords matched, which were missing, and how many times each required phrase occurred
- Export the ranked results to a CSV file

## Design (Automation + String/DSA Search)

- **`tokenize()`** — breaks text into clean, lowercase words, filtering out common English stopwords and short/noise words
- **`extract_job_keywords()`** — uses a hash-map based frequency counter (`collections.Counter`) to pull out the most significant, most frequently mentioned words from the job description
- **`build_lps_array()` / `kmp_search_count()`** — a full implementation of the **Knuth-Morris-Pratt (KMP) string searching algorithm**, used to accurately count exact occurrences of multi-word required phrases inside each resume's raw text (something plain word-splitting cannot detect, since "machine learning" is two words that need to appear together)
- **`rank_resumes()`** — combines a keyword-coverage score (70% weight, or 100% if no phrases are given) with a required-phrase score (30% weight) into a single ranking score per resume
- **`ResumeRankerWindow`** — the PyQt6 GUI: job description input, resume loading, the ranked results table, and a detail panel breaking down each score

## Scoring Explained

- **Keyword Match %** — the percentage of the job description's significant keywords that appear anywhere in the resume
- **Phrase Match %** — the percentage of your listed required phrases that were found as exact phrases (via KMP search) in the resume
- **Total Score** — `keyword_score * 0.7 + phrase_score * 0.3` when required phrases are given, otherwise just the keyword score

## Requirements

- Python 3.8+
- PyQt6

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python resume_ranker.py
```

## Usage

1. Paste a job description into the top box (or copy the contents of `sample_job_description.txt` to try it out).
2. Optionally enter required phrases, comma-separated.
3. Click **Load Resume Files (.txt)** and select one or more resumes — try the three files in `sample_resumes/` to see it in action.
4. Click **Rank Resumes**. The table fills in, sorted by Total Score, best match first.
5. Click any row to see the full breakdown — matched keywords, missing keywords, and phrase occurrence counts.
6. Click **Export Results to CSV** to save the ranked results to a file.

## Sample Data

This repository includes `sample_job_description.txt` and three sample resumes in `sample_resumes/` — one strong match, one weak match, and one partial match — so you can immediately test the ranking without needing your own resume files.

## Screenshots

*(Add 2–3 screenshots here after running the app, e.g.:)*

`![Job Description Input](screenshots/job-input.png)`

`![Ranked Results](screenshots/ranked-results.png)`

`![Score Breakdown](screenshots/score-detail.png)`

## Note on AI Usage

AI (Claude) was used to help design and generate the initial version of the code, including the keyword extraction logic, the KMP string-searching algorithm implementation, the scoring formula, and the PyQt6 GUI layout. The ranking logic was tested independently with sample resumes and a sample job description to confirm the scores and rankings were correct before building the GUI around it.

## Author

Malak Hasnain Khan
