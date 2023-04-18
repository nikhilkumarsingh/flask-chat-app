import json
from datetime import datetime

import requests
from bson.json_util import dumps
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_socketio import SocketIO, join_room, leave_room
from pymongo.errors import DuplicateKeyError

from db import (add_room_members, get_messages, get_room, get_room_members,
                get_rooms_for_user, get_user, is_room_admin, is_room_member,
                remove_room_members, save_message, save_room, save_user,
                update_room)
from no_sql_db import DB, Table

app = Flask(__name__)
app.secret_key = "sfdjkafnk"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/post", methods=["POST"])
def post_fn():
    data = request.get_json()
    data = jsonify(data)
    print(data.json)
    return data


@app.route("/get", methods=["GET"])
def get_fn():
    message = {"greeting": "Hello from flask!"}
    return jsonify(message)


@app.route("/chats")
def chats():
    friends = ["test1", "test2", "test3", "test4", "test5"]
    # if current_user.is_authenticated:
    #     rooms = get_rooms_for_user(current_user.username)
    return render_template("chats.html", friends=friends)


@app.route("/add-friend", methods=["POST"])
def add_friend_route():
    friend_name = request.form.get("name")
    if not friend_name:
        return "Friend name is required", 400

    # added = add_friend(friend_name)
    added = True
    if added:
        return "Friend added successfully", 200
    else:
        return "Failed to add friend", 500


@app.route("/chats/<friend>/")
@login_required
def view_chat(friends: list, friend: str):
    # room = get_room(room_id)
    # if room and is_room_member(room, current_user.username):
    #     room_members = get_room_members(room_id)  # should return a list of usernames
    #     friend_username = room_members[1] if room_members[0] == current_user.username else room_members[0]
    #     messages = get_messages(room_id)
    #     return render_template('view_chat.html', username=current_user.username, room=room, friend_username=friend_username,
    #                            messages=messages)
    # else:
    #     return "Room not found", 404
    if current_user.is_authenticated and friend in friends:
        messages = ["first message", "second message", "third message"]
        return render_template(
            "view_chat.html", friend_username=friend, messages=messages
        )
    else:
        print("view_chat didn't work :(")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        print("authenticated somehow")
        return redirect(url_for("home"))

    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password_input = request.form.get("password")
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for("chats"))
        else:
            message = "Failed to login!"
    return render_template("login.html", message=message)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    #   if current_user.is_authenticated:
    #       return redirect(url_for('home'))

    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            save_user(username, email, password)
            if current_user.is_authenticated:
                return redirect(url_for("home"))
            else:
                return redirect(url_for("login"))
        except DuplicateKeyError:
            message = "User already exists!"
    return render_template("signup.html", message=message)


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/create-room/", methods=["GET", "POST"])
@login_required
def create_room():
    message = ""
    if request.method == "POST":
        room_name = request.form.get("room_name")
        usernames = [
            username.strip() for username in request.form.get("members").split(",")
        ]

        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for("view_room", room_id=room_id))
        else:
            message = "Failed to create room"
    return render_template("create_room.html", message=message)


@app.route("/rooms/<room_id>/edit", methods=["GET", "POST"])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [
            member["_id"]["username"] for member in get_room_members(room_id)
        ]
        room_members_str = ",".join(existing_room_members)
        message = ""
        if request.method == "POST":
            room_name = request.form.get("room_name")
            room["name"] = room_name
            update_room(room_id, room_name)

            new_members = [
                username.strip() for username in request.form.get("members").split(",")
            ]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            if len(members_to_add):
                add_room_members(
                    room_id, room_name, members_to_add, current_user.username
                )
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = "Room edited successfully"
            room_members_str = ",".join(new_members)
        return render_template(
            "edit_room.html",
            room=room,
            room_members_str=room_members_str,
            message=message,
        )
    else:
        return "Room not found", 404


@app.route("/rooms/<room_id>/")
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template(
            "view_room.html",
            username=current_user.username,
            room=room,
            room_members=room_members,
            messages=messages,
        )
    else:
        return "Room not found", 404


@app.route("/rooms/<room_id>/messages/")
@login_required
def get_older_messages(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        page = int(request.args.get("page", 0))
        messages = get_messages(room_id, page)
        return dumps(messages)
    else:
        return "Room not found", 404


@socketio.on("send_message")
def handle_send_message_event(data):
    app.logger.info(
        "{} has sent message to the room {}: {}".format(
            data["username"], data["room"], data["message"]
        )
    )
    data["created_at"] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data["room"], data["message"], data["username"])
    socketio.emit("receive_message", data, room=data["room"])


@socketio.on("join_room")
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data["username"], data["room"]))
    join_room(data["room"])
    socketio.emit("join_room_announcement", data, room=data["room"])


@socketio.on("leave_room")
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data["username"], data["room"]))
    leave_room(data["room"])
    socketio.emit("leave_room_announcement", data, room=data["room"])


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == "__main__":
    db = DB.get_instance()
    db.export_JSON()
    db.create_chats()
    # db.message_add_test()
    # socketio.run(app, debug=True)
    app.run(ssl_context="adhoc", debug=True)
