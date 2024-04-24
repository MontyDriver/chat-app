# Required Dependencies
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Flask app initialisation with instance_relative_config set to True
app = Flask(__name__, instance_relative_config=True)

# Load the configuration from the instance folder
app.config.from_pyfile('config.py')
socketio = SocketIO(app)

# rooms stored in dictionary
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

#Home page
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Input validation
        if not username:
            return render_template("home.html", error="please enter a username", code=code, username=username)
        
        if join != False and not code:
            return render_template("home.html", error="please enter a room code", code=code, username=username)
        
        room = code

        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist", code=code, username=username)
        
        session["room"] = room
        session["username"] = username
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    #Validation so you have to go to home page first
    if room is None or session.get("username") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "username": session.get("username"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('username')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    username = session.get("username")
    if not room or not username:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"username": username, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{username} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    username = session.get("username")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"username": username, "message": "has left the room"}, to=room)
    print(f"{username} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)