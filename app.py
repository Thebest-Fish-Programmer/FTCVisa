from flask import Flask, send_from_directory, jsonify, request, session, redirect
from flask_socketio import SocketIO
from functools import wraps
import uuid, time
import os

app = Flask(__name__, static_folder='static')
app.secret_key = "supersecretkey"
socketio = SocketIO(app, cors_allowed_origins="*")

sessions_data = {}

# User accounts with credentials and roles
USERS = {
    "avery": {"password": "avery123", "name": "Avery", "role": "user"},
    "havish": {"password": "havish123", "name": "Havish", "role": "user"},
    "ethan": {"password": "ethan123123123", "name": "Ethan", "role": "admin"},
    "ashvath": {"password": "ashvath123123123", "name": "Ashvath", "role": "owner"},
    "kavya": {"password": "kavya123", "name": "Kavya", "role": "user"},
    "teju": {"password": "teju123", "name": "Teju", "role": "user"},
    "lebudda": {"password": "lebudda123", "name": "Lebudda", "role": "user"},
    "goonvik": {"password": "goonvik123", "name": "Goonvik", "role": "user"},
    "user9": {"password": "user9123", "name": "...", "role": "user"},
    "user10": {"password": "user10123", "name": "...", "role": "user"},
    "user11": {"password": "user11123", "name": "...", "role": "user"},
    "user12": {"password": "user12123", "name": "...", "role": "user"},
    "user13": {"password": "user13123", "name": "...", "role": "user"},
    "user14": {"password": "user14123", "name": "...", "role": "user"},
    "user15": {"password": "user15123", "name": "...", "role": "user"},
    "user16": {"password": "user16123", "name": "...", "role": "user"},
    "user17": {"password": "user17123", "name": "...", "role": "user"},
    "user18": {"password": "user18123", "name": "...", "role": "user"},
    "user19": {"password": "user19123", "name": "...", "role": "user"},
    "user20": {"password": "user20123", "name": "...", "role": "user"}
}

# Create a session for each user
for username, user_info in USERS.items():
    sid = str(uuid.uuid4())
    sessions_data[sid] = {
        "unlocked": False, 
        "expires_at": None,
        "name": user_info["name"],
        "username": username
    }
    user_info["session_id"] = sid

# --- Helpers ---
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"DEBUG: session = {dict(session)}")
        print(f"DEBUG: logged_in = {session.get('logged_in')}")
        print(f"DEBUG: username = {session.get('username')}")
        
        if not session.get("logged_in"):
            print("DEBUG: Not logged in, redirecting")
            return redirect("/")
        
        username = session.get("username")
        print(f"DEBUG: Checking role for {username}")
        
        if username not in USERS:
            print(f"DEBUG: {username} not in USERS")
            return redirect("/")
            
        user_role = USERS[username].get("role")
        print(f"DEBUG: user_role = {user_role}")
        
        if user_role not in ["admin", "owner"]:
            print(f"DEBUG: Role {user_role} not admin/owner")
            return redirect("/")
        
        print(f"DEBUG: Access granted for {username}")
        return func(*args, **kwargs)
    return wrapper

# --- Routes ---
@app.route('/', methods=["GET"])
def index():
    return send_from_directory('static', 'login.html')

@app.route('/login', methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").lower()
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400
    
    if username not in USERS or USERS[username]["password"] != password:
        return jsonify({"error": "Invalid username or password"}), 401
    
    user = USERS[username]
    session["logged_in"] = True
    session["username"] = username
    session["role"] = user.get("role", "user")
    
    role = user.get("role", "user")
    if role in ["owner", "admin"]:
        redirect_path = "/dashboard"
    else:
        redirect_path = "/status"
    
    return jsonify({
        "message": "Login successful",
        "redirect": redirect_path
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/dashboard')
@admin_required
def dashboard():
    return send_from_directory('static', 'index.html')

@app.route('/scanner')
@admin_required
def scanner():
    return send_from_directory('static', 'scanner.html')

@app.route('/status')
@login_required
def user_status():
    return send_from_directory('static', 'user_status.html')

# API Routes
@app.route('/qrs', methods=['GET'])
def get_qrs():
    qrs = []
    for sid in sessions_data:
        qrs.append({
            "session_id": sid,
            "name": sessions_data[sid]["name"],
            "url": f"{request.host_url}scanner?session_id={sid}"
        })
    return jsonify(qrs)

@app.route('/my_status', methods=['GET'])
@login_required
def my_status():
    username = session.get("username")
    if username in USERS:
        user = USERS[username]
        sid = user["session_id"]
        sess = sessions_data[sid]
        
        status = "locked"
        expires_at = None
        if sess['unlocked'] and sess['expires_at'] and time.time() < sess['expires_at']:
            status = "unlocked"
            expires_at = sess['expires_at']
        
        return jsonify({
            "name": user["name"],
            "session_id": sid,
            "url": f"{request.host_url}scanner?session_id={sid}",
            "status": status,
            "expires_at": expires_at
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/approve', methods=['POST'])
@admin_required
def approve():
    data = request.get_json()
    session_id = data.get("session_id")
    duration = data.get("duration") or 10
    if session_id in sessions_data:
        sessions_data[session_id]['unlocked'] = True
        sessions_data[session_id]['expires_at'] = time.time() + duration
        socketio.emit('unlocked', {
            'session_id': session_id, 
            'expires_at': sessions_data[session_id]['expires_at'],
            'name': sessions_data[session_id]['name']
        })
        return jsonify({"status": "approved"})
    return jsonify({"error": "invalid session"}), 400

@app.route('/session_status/<session_id>', methods=['GET'])
def session_status(session_id):
    sess = sessions_data.get(session_id)
    if not sess:
        return jsonify({"status": "invalid"})
    if sess['unlocked'] and sess['expires_at'] and time.time() < sess['expires_at']:
        return jsonify({
            "status": "unlocked", 
            "expires_at": sess['expires_at'],
            "name": sess['name']
        })
    return jsonify({"status": "locked", "name": sess['name']})

@socketio.on('connect')
def handle_connect():
    print("Client connected")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
