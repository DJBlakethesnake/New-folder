from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from .models import CalendarEvent, Link
from . import db

import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SCORES_FILE = os.path.join(BASE_DIR, "quiz_scores.csv")
CHART_FILE = os.path.join(BASE_DIR, "website", "static", "score_chart.png")

DEVELOPER_PASSWORD = "12345678"


def save_score(score, total):
    file_exists = os.path.exists(SCORES_FILE)

    with open(SCORES_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["score", "total"])

        writer.writerow([score, total])


def create_score_chart():
    scores = []

    if not os.path.exists(SCORES_FILE):
        return

    with open(SCORES_FILE, "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            scores.append(int(row["score"]))

    score_counts = Counter(scores)

    x_values = sorted(score_counts.keys())
    y_values = [score_counts[x] for x in x_values]

    plt.figure(figsize=(8, 5))
    plt.bar(x_values, y_values)
    plt.xlabel("Score")
    plt.ylabel("Number of Students")
    plt.title("Quiz Score Distribution")
    plt.xticks(range(0, max(x_values) + 1))
    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

views = Blueprint("views", __name__)


@views.route("/")
@login_required
def home():
    return render_template("home.html", user=current_user)


@views.route("/events", methods=["GET"])
@login_required
def get_events():
    events = CalendarEvent.query.filter_by(user_id=current_user.id).all()

    return jsonify([
    {
        "id": event.id,
        "title": event.title,
        "start": str(event.start),
        "end": str(event.end) if event.end else None
    }
    for event in events
])


@views.route("/events", methods=["POST"])
@login_required
def add_event():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    title = data.get("title")
    start = data.get("start")
    end = data.get("end")

    if not title or not start:
        return jsonify({"error": "Title and start are required"}), 400

    new_event = CalendarEvent(
        title=title,
        start=start,
        end=end,
        user_id=current_user.id
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": new_event.id,
        "title": new_event.title,
        "start": new_event.start,
        "end": new_event.end
    }), 201


@views.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = CalendarEvent.query.get(event_id)

    if event and event.user_id == current_user.id:
        db.session.delete(event)
        db.session.commit()

    return jsonify({"success": True})


@views.route("/links")
@login_required
def links():
    user_links = Link.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "links.html",
        user=current_user,
        links=user_links
    )


@views.route("/add-link", methods=["POST"])
@login_required
def add_link():
    title = request.form.get("title")
    url = request.form.get("url")
    image_url = request.form.get("image_url")

    if not title or not url:
        flash("Title and URL are required.", category="error")
        return redirect(url_for("views.links"))

    if not image_url:
        image_url = "https://via.placeholder.com/300x180?text=No+Image"

    new_link = Link(
        title=title,
        url=url,
        image_url=image_url,
        user_id=current_user.id
    )

    db.session.add(new_link)
    db.session.commit()

    return redirect(url_for("views.links"))


@views.route("/delete-link/<int:link_id>", methods=["POST"])
@login_required
def delete_link(link_id):
    link = Link.query.get(link_id)

    if link and link.user_id == current_user.id:
        db.session.delete(link)
        db.session.commit()

    return redirect(url_for("views.links"))

@views.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    questions = [
        {
            "question": "When confronted with day-to-day tasks, we tend to overthink the repetitiveness of our actions and dwell on negativity. Practicing the Shift in Mindset principle encourages a positive mindset and fosters motivation. One example of this principle is:",
            "options": [
                "Scrutinizing yourself about your mistakes",
                "Ignoring the negativity and choosing a more constructive perspective",
                "Doing nothing until motivation appears",
                "Giving up when tasks feel repetitive"
            ],
            "answer": "Ignoring the negativity and choosing a more constructive perspective"
        },
        {
            "question": "What is an effective method of motivating oneself to complete tasks?",
            "options": [
                "Gamification",
                "Depriving oneself of enjoyable activities until a task is completed",
                "Doing nothing until motivation appears",
                "Nothing, motivation sucks"
            ],
            "answer": "Gamification"
        },
        {
            "question": "When completing tasks, we often confuse efficiency with rapid completion, not thoughtful completion. What is one strategy used to overcome this?",
            "options": [
                "Sacrificing speed for quality, even if you are limited on time",
                "Working solo and spend an extreme amount of time on each tasks",
                "Accepting the poorer quality and continuing on practicing the same level of 'efficiency'",
                "Bringing others on board"
            ],
            "answer": "Bringing others on board"
        }
    ]

    results = None
    score = 0
    total = len(questions)

    if request.method == 'POST':
        results = []

        for index, question in enumerate(questions):
            user_answer = request.form.get(f'question_{index}')
            correct = user_answer == question["answer"]

            if correct:
                score += 1

            results.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": question["answer"],
                "correct": correct
            })
        save_score(score, total)
        create_score_chart()
    return render_template(
        "quiz.html",
        user=current_user,
        questions=questions,
        results=results,
        score=score,
        total=total
    )

@views.route("/developer", methods=["GET", "POST"])
def developer():
    if current_user.is_authenticated:
        return redirect(url_for("views.home"))
    if request.method == "POST":
        entered_password = request.form.get("password")
        if entered_password == DEVELOPER_PASSWORD:
            if os.path.exists(USER_DATA_FILE):
                with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
                    data = file.read()
            else:
                data = "No user data has been recorded yet."
            return render_template(
                "developer_view.html",
                user=current_user,
                data=data
            )
        return redirect(url_for("views.developer"))
    return render_template(
        "developer_login.html",
        user=current_user
    )
