from flask import Flask, send_from_directory, jsonify, request, session, redirect
from flask_socketio import SocketIO
import uuid, time

app = Flask(__name__, static_folder='static')
app.secret_key = "supersecretkey"
socketio = SocketIO(app, cors_allowed_origins="*")

# Pre-generate sessions with user accounts
sessions_data = {}
NGROK_HOST = "3533419bef85.ngrok-free.app"

# User accounts with credentials
USERS = {
    "avery": {"password": "avery123", "name": "Avery"},
    "havish": {"password": "havish123", "name": "Havish"},
    "ethan": {"password": "ethan123", "name": "Ethan"},
    "ashvath": {"password": "ashvath123", "name": "Ashvath"},
    "kavya": {"password": "kavya123", "name": "Kavya"},
    "teju": {"password": "teju123", "name": "Teju"},
    "lebudda": {"password": "lebudda123", "name": "Lebudda"},
    "goonvik": {"password": "goonvik123", "name": "Goonvik"},
    "user9": {"password": "user9123", "name": "..."},
    "user10": {"password": "user10123", "name": "..."},
    "user11": {"password": "user11123", "name": "..."},
    "user12": {"password": "user12123", "name": "..."},
    "user13": {"password": "user13123", "name": "..."},
    "user14": {"password": "user14123", "name": "..."},
    "user15": {"password": "user15123", "name": "..."},
    "user16": {"password": "user16123", "name": "..."},
    "user17": {"password": "user17123", "name": "..."},
    "user18": {"password": "user18123", "name": "..."},
    "user19": {"password": "user19123", "name": "..."},
    "user20": {"password": "user20123", "name": "..."}
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

# --- Helper ---
def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("logged_in"):
            return func(*args, **kwargs)
        return redirect("/")
    return wrapper

# --- Routes ---
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        username = data.get("username", "").lower()
        password = data.get("password")
        
        # Check regular users
        if username in USERS and USERS[username]["password"] == password:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "error", "msg": "Invalid credentials"}), 401
    
    return send_from_directory('static', 'login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/status')
@login_required
def status():
    return send_from_directory('static', 'user_status.html')

@app.route('/dash/dashboard/dashboard/dashboard/dashboard/dashboard')
def dashboard():
    return send_from_directory('static', 'index.html')

@app.route('/scanner/scanner/scanning/scammer/scanner/scanner')
def scanner():
    return send_from_directory('static', 'scanner.html')

# Return all QR sessions for admin dashboard
@app.route('/qrs')
def get_qrs():
    qrs = []
    for sid in sessions_data:
        qrs.append({
            "session_id": sid,
            "name": sessions_data[sid]["name"],
            "url": f"https://{NGROK_HOST}/scanner?session_id={sid}"
        })
    return jsonify(qrs)

# Return user's own QR and status
@app.route('/my_status')
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
            "url": f"https://{NGROK_HOST}/scanner?session_id={sid}",
            "status": status,
            "expires_at": expires_at
        })
    return jsonify({"error": "User not found"}), 404

# --- Approve endpoint ---
@app.route('/approve', methods=['POST'])
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

@app.route('/session_status/<session_id>')
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
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)