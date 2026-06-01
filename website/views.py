from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from .models import CalendarEvent, Link
from . import db

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



