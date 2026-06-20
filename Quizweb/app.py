from flask import Flask, render_template, request, redirect, session
import sqlite3
import pandas as pd
import os
import random
import re

app = Flask(__name__)
app.secret_key = "quizweb_2026_secret_key"

DATABASE = "quiz.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    conn = get_db()
    questions = conn.execute("SELECT * FROM questions").fetchall()
    conn.close()

    return render_template(
        "index.html",
        questions=questions
    )


# ==========================
# SUBMIT EXAM
# ==========================
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    unit = request.form.get("unit", "LUYỆN TẬP")

    answer_key = session.get("answer_key", {})
    score = 0

    for question_id, correct_answer in answer_key.items():
        user_answers = request.form.getlist(f"question_{question_id}")
        user_answers = ",".join(sorted(user_answers))

        if user_answers == correct_answer:
            score += 1

    total = len(answer_key)

    # chỉ lưu nếu không phải luyện tập
    if unit != "LUYỆN TẬP": 
        conn = get_db()
        conn.execute("""
            INSERT INTO results (name, unit, score, total)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            unit,
            score,
            total
        ))
        conn.commit()
        conn.close()

    session.pop("answer_key", None)

    return render_template(
        "result.html",
        name=name,
        score=score,
        total=total
    )


# ==========================
# START EXAM
# ==========================
@app.route("/start_exam", methods=["POST"])
def start_exam():
    name = request.form["name"]
    unit_b = request.form["unit_b"]
    unit_c = request.form["unit_c"]
    unit_d = request.form["unit_d"]

    unit = f"B{unit_b}C{unit_c}D{unit_d}"

    conn = get_db()
    all_questions = conn.execute(
        "SELECT * FROM questions"
    ).fetchall()
    conn.close()

    selected_questions = random.sample(
        list(all_questions),
        len(all_questions)
    )

    processed_questions = []
    answer_key = {}

    for q in selected_questions:
        options = [
            ("A", q["option_a"]),
            ("B", q["option_b"]),
            ("C", q["option_c"]),
            ("D", q["option_d"])
        ]

        random.shuffle(options)

        labels = ["A", "B", "C", "D"]
        shuffled_options = []
        correct_answers = q["correct_answer"].split(",")
        new_correct = []

        for i, opt in enumerate(options):
            old_letter = opt[0]
            text = opt[1]
            new_letter = labels[i]

            shuffled_options.append((new_letter, text))

            if old_letter in correct_answers:
                new_correct.append(new_letter)

        answer_key[str(q["id"])] = ",".join(sorted(new_correct))

        processed_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": shuffled_options
        })

    session["answer_key"] = answer_key

    return render_template(
        "quiz.html",
        name=name,
        unit=unit,
        questions=processed_questions
    )


# ==========================
# PRACTICE MODE
# ==========================
@app.route("/practice", methods=["GET"])
def practice():
    conn = get_db()
    all_questions = conn.execute(
        "SELECT * FROM questions"
    ).fetchall()
    conn.close()

    processed_questions = []
    answer_key = {}

    for q in all_questions:
        options = [
            ("A", q["option_a"]),
            ("B", q["option_b"]),
            ("C", q["option_c"]),
            ("D", q["option_d"])
        ]

        random.shuffle(options)

        labels = ["A", "B", "C", "D"]
        shuffled_options = []
        new_correct = None

        for i, opt in enumerate(options):
            old_letter = opt[0]
            text = opt[1]
            new_letter = labels[i]

            shuffled_options.append((new_letter, text))

            if old_letter == q["correct_answer"]:
                new_correct = new_letter

        answer_key[str(q["id"])] = new_correct

        processed_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": shuffled_options
        })

    session["answer_key"] = answer_key

    return render_template(
        "practice.html",
        name="Luyện tập",
        unit="LUYỆN TẬP",
        questions=processed_questions
    )


# ==========================
# LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "123456":
            session["admin"] = True
            return redirect("/admin")

        return render_template(
            "login.html",
            error="Sai tên đăng nhập hoặc mật khẩu!"
        )

    return render_template(
        "login.html",
        error=None
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==========================
# ADMIN
# ==========================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()

    results = conn.execute(
        "SELECT * FROM results ORDER BY id DESC"
    ).fetchall()

    questions = conn.execute(
        "SELECT * FROM questions ORDER BY id"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        results=results,
        questions=questions
    )


@app.route("/add_question", methods=["GET", "POST"])
def add_question():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        conn = get_db()

        conn.execute("""
            INSERT INTO questions
            (question, option_a, option_b, option_c, option_d, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form["question"],
            request.form["option_a"],
            request.form["option_b"],
            request.form["option_c"],
            request.form["option_d"],
            request.form["correct_answer"]
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_question.html")


@app.route("/edit_question/<int:id>", methods=["GET", "POST"])
def edit_question(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":
        conn.execute("""
            UPDATE questions
            SET question=?,
                option_a=?,
                option_b=?,
                option_c=?,
                option_d=?,
                correct_answer=?
            WHERE id=?
        """, (
            request.form["question"],
            request.form["option_a"],
            request.form["option_b"],
            request.form["option_c"],
            request.form["option_d"],
            request.form["correct_answer"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    question = conn.execute(
        "SELECT * FROM questions WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_question.html",
        question=question
    )


@app.route("/delete_question/<int:id>")
def delete_question(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/import_excel", methods=["GET", "POST"])
def import_excel():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["excel_file"]

        if file:
            filepath = "temp.xlsx"
            file.save(filepath)

            df = pd.read_excel(filepath)

            conn = get_db()

            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO questions
                    (question, option_a, option_b, option_c, option_d, correct_answer)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row["question"],
                    row["option_a"],
                    row["option_b"],
                    row["option_c"],
                    row["option_d"],
                    str(row["correct"]).replace(" ", "").upper()
                ))

            conn.commit()
            conn.close()

            os.remove(filepath)

            return redirect("/admin")

    return render_template("import_excel.html")


@app.route("/delete_result/<int:id>")
def delete_result(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM results WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/clear_results")
def clear_results():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    conn.execute("DELETE FROM results")
    conn.commit()
    conn.close()

    return redirect("/admin")


# ==========================
# LEADERBOARD
# ==========================
@app.route("/leaderboard")
def leaderboard():
    conn = get_db()
    results = conn.execute("SELECT * FROM results").fetchall()
    conn.close()

    def parse_unit(unit):
        try:
            match = re.match(r'B(\d+)C(\d+)D(\d+)', unit)
            if match:
                b = int(match.group(1))
                c = int(match.group(2))
                d = int(match.group(3))
                return (d, c, b)
        except:
            pass

        return (999, 999, 999)

    sorted_results = sorted(
        results,
        key=lambda r: (
            parse_unit(r["unit"])[0],
            parse_unit(r["unit"])[1],
            parse_unit(r["unit"])[2],
            -r["score"]
        )
    )

    return render_template(
        "leaderboard.html",
        results=sorted_results
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )