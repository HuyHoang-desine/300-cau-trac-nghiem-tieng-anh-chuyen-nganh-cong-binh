import sqlite3

conn = sqlite3.connect("quiz.db")
cur = conn.cursor()

# Tạo bảng câu hỏi
cur.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL
)
""")

# Tạo bảng kết quả
cur.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Nếu chưa có câu hỏi nào thì thêm câu hỏi mẫu
count = cur.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

if count == 0:
    sample_questions = [
        (
            "2 + 2 bằng bao nhiêu?",
            "3",
            "4",
            "5",
            "6",
            "B"
        ),
        (
            "Thủ đô của Việt Nam là gì?",
            "Huế",
            "Đà Nẵng",
            "Hà Nội",
            "Hải Phòng",
            "C"
        )
    ]

    cur.executemany("""
    INSERT INTO questions
    (question, option_a, option_b, option_c, option_d, correct_answer)
    VALUES (?, ?, ?, ?, ?, ?)
    """, sample_questions)

conn.commit()
conn.close()

print("Đã tạo cơ sở dữ liệu thành công!")