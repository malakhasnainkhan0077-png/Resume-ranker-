import sys
import os
import re
import csv
from collections import Counter
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QGroupBox,
    QMessageBox, QHeaderView, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "of", "in", "on",
    "at", "to", "for", "with", "by", "from", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its", "we",
    "you", "your", "our", "their", "they", "he", "she", "his", "her", "will",
    "shall", "can", "could", "would", "should", "may", "might", "must", "have",
    "has", "had", "do", "does", "did", "not", "no", "yes", "all", "any", "each",
    "which", "who", "whom", "what", "when", "where", "why", "how", "about",
    "into", "over", "after", "before", "between", "such", "than", "also",
    "job", "role", "work", "years", "year", "candidate", "candidates",
    "applicant", "position", "team", "company", "us", "including"
}


def tokenize(text):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [word for word in words if len(word) >= 3 and word not in STOPWORDS]


def extract_job_keywords(job_text, max_keywords=40):
    word_counts = Counter(tokenize(job_text))
    most_common = word_counts.most_common(max_keywords)
    return [word for word, count in most_common]


def build_lps_array(pattern):
    lps = [0] * len(pattern)
    length = 0
    i = 1

    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1

    return lps


def kmp_search_count(text, pattern):
    text = text.lower()
    pattern = pattern.lower().strip()

    if not pattern:
        return 0

    lps = build_lps_array(pattern)
    matches = 0
    i = 0
    j = 0

    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == len(pattern):
                matches += 1
                j = lps[j - 1]
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1

    return matches


class ResumeResult:
    def __init__(self, filename, keyword_score, phrase_score, total_score,
                 matched_keywords, missing_keywords, phrase_hits):
        self.filename = filename
        self.keyword_score = keyword_score
        self.phrase_score = phrase_score
        self.total_score = total_score
        self.matched_keywords = matched_keywords
        self.missing_keywords = missing_keywords
        self.phrase_hits = phrase_hits


def rank_resumes(job_text, phrases, resume_paths):
    job_keywords = extract_job_keywords(job_text)
    results = []

    for path in resume_paths:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                resume_text = f.read()
        except OSError:
            continue

        resume_word_counts = Counter(tokenize(resume_text))

        matched_keywords = [kw for kw in job_keywords if resume_word_counts[kw] > 0]
        missing_keywords = [kw for kw in job_keywords if resume_word_counts[kw] == 0]

        keyword_score = (len(matched_keywords) / len(job_keywords) * 100) if job_keywords else 0.0

        phrase_hits = {}
        if phrases:
            for phrase in phrases:
                phrase_hits[phrase] = kmp_search_count(resume_text, phrase)
            phrases_found = sum(1 for count in phrase_hits.values() if count > 0)
            phrase_score = (phrases_found / len(phrases)) * 100
        else:
            phrase_score = 0.0

        if phrases:
            total_score = (keyword_score * 0.7) + (phrase_score * 0.3)
        else:
            total_score = keyword_score

        results.append(ResumeResult(
            os.path.basename(path),
            round(keyword_score, 2),
            round(phrase_score, 2),
            round(total_score, 2),
            matched_keywords,
            missing_keywords,
            phrase_hits
        ))

    results.sort(key=lambda r: r.total_score, reverse=True)
    return results


class ResumeRankerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.resume_paths = []
        self.results = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Resume Keyword Ranking Tool")
        self.resize(1100, 750)

        main_layout = QVBoxLayout()

        job_group = QGroupBox("Job Description")
        job_layout = QVBoxLayout()
        self.job_text_edit = QTextEdit()
        self.job_text_edit.setPlaceholderText("Paste the job description here...")
        job_layout.addWidget(self.job_text_edit)

        phrase_layout = QHBoxLayout()
        phrase_layout.addWidget(QLabel("Required Phrases (comma-separated, optional):"))
        self.phrases_input = QLineEdit()
        self.phrases_input.setPlaceholderText("e.g. machine learning, project management")
        phrase_layout.addWidget(self.phrases_input)
        job_layout.addLayout(phrase_layout)

        job_group.setLayout(job_layout)
        main_layout.addWidget(job_group)

        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Resume Files (.txt)")
        load_button.clicked.connect(self.load_resumes)

        self.loaded_label = QLabel("No resumes loaded")

        rank_button = QPushButton("Rank Resumes")
        rank_button.clicked.connect(self.perform_ranking)

        export_button = QPushButton("Export Results to CSV")
        export_button.clicked.connect(self.export_results)

        button_layout.addWidget(load_button)
        button_layout.addWidget(self.loaded_label)
        button_layout.addStretch()
        button_layout.addWidget(rank_button)
        button_layout.addWidget(export_button)
        main_layout.addLayout(button_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Resume File", "Keyword Match %", "Phrase Match %", "Total Score"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.show_details)
        splitter.addWidget(self.results_table)

        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        splitter.addWidget(self.detail_view)

        splitter.setSizes([600, 500])
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def load_resumes(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Resume Text Files", "", "Text Files (*.txt)")
        if files:
            self.resume_paths = files
            self.loaded_label.setText(f"{len(files)} resume(s) loaded")

    def perform_ranking(self):
        job_text = self.job_text_edit.toPlainText().strip()

        if not job_text:
            QMessageBox.warning(self, "Input Error", "Paste a job description first.")
            return

        if not self.resume_paths:
            QMessageBox.warning(self, "Input Error", "Load at least one resume file first.")
            return

        phrases = [p.strip() for p in self.phrases_input.text().split(",") if p.strip()]

        self.results = rank_resumes(job_text, phrases, self.resume_paths)
        self.populate_table()

    def populate_table(self):
        self.results_table.setRowCount(len(self.results))
        for row, result in enumerate(self.results):
            self.results_table.setItem(row, 0, QTableWidgetItem(result.filename))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{result.keyword_score}%"))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{result.phrase_score}%"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{result.total_score}"))

        if self.results:
            self.results_table.selectRow(0)

    def show_details(self):
        selected_rows = self.results_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        result = self.results[row]

        content = f"Resume: {result.filename}\n"
        content += f"Total Score: {result.total_score}\n"
        content += f"Keyword Match: {result.keyword_score}%\n"
        content += f"Phrase Match: {result.phrase_score}%\n\n"

        content += f"Matched Keywords ({len(result.matched_keywords)}):\n"
        content += ", ".join(result.matched_keywords) if result.matched_keywords else "None"
        content += "\n\n"

        content += f"Missing Keywords ({len(result.missing_keywords)}):\n"
        content += ", ".join(result.missing_keywords) if result.missing_keywords else "None"

        if result.phrase_hits:
            content += "\n\nRequired Phrase Occurrences:\n"
            for phrase, count in result.phrase_hits.items():
                content += f"  {phrase}: {count} occurrence(s)\n"

        self.detail_view.setText(content)

    def export_results(self):
        if not self.results:
            QMessageBox.warning(self, "Nothing to Export", "Rank resumes before exporting.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Results CSV", "resume_ranking_results.csv", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Resume File", "Keyword Match %", "Phrase Match %", "Total Score"])
                for result in self.results:
                    writer.writerow([result.filename, result.keyword_score, result.phrase_score, result.total_score])

            QMessageBox.information(self, "Export Complete", f"Results saved to {file_path}")
        except OSError as error:
            QMessageBox.critical(self, "Export Error", f"Failed to save CSV: {error}")


def main():
    app = QApplication(sys.argv)
    window = ResumeRankerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
