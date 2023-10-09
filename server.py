from flask import Flask, request, Response, jsonify, send_from_directory, send_file, make_response
from DatabaseHandler import DatabaseHandler
from werkzeug.utils import secure_filename
from urllib.parse import unquote
import logging

import os
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    response = DatabaseHandler.read_login_html()

    return response


@app.route('/index.html', methods=['GET'])
def get_home():
    logging.info("Received cookies: %s", request.cookies)  # Log received cookies
    cookie_value = request.cookies.get('myCookie12345')

    if cookie_value is None:
        return DatabaseHandler.read_login_html()

    return DatabaseHandler.read_html()

@app.route('/favicon.ico', methods=['GET'])
def serve_favicon():
    return send_from_directory('Images', "ConnectiVerse-icon.jpeg")

@app.route('/logo-B0cgv4t6l-transformed.png', methods=['GET'])
def serve_logo():
    return send_from_directory('Images', "logo-B0cgv4t6l-transformed.png")


@app.route('/insert_sound.mp3', methods=['GET'])
def serve_sound():
    return send_from_directory('Sounds', "insert_sound.mp3")

@app.route('/like_sound.mp3', methods=['GET'])
def serve_like_sound():
    return send_from_directory('Sounds', "like_sound.mp3")


@app.route('/message-recieved.mp3', methods=['GET'])
def serve_message_sound():
    return send_from_directory('Sounds', "message-recieved.mp3")


@app.route('/uploads/<filename>', methods=['GET'])
def serve_media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/profiles/<filename>', methods=['GET'])
def serve_profile(filename):
    return send_from_directory('profiles', filename)


@app.route('/api/tweet', methods=['GET'])
def get_tweets():
    username = request.args.get('username', None)
    shared = request.args.get('shared', None)

    if username is not None:
        decoded_username = unquote(username)
    else:
        decoded_username = None

    conn = DatabaseHandler.connect_db()

    if shared:
        data = DatabaseHandler.read_shared_tweets(conn, username=decoded_username)
    else:
        data = DatabaseHandler.read_tweets(conn)

    # Fetch likes, comments for each tweet
    enriched_data = []
    for tweet in data:
        tweetID = tweet[0]

        # Fetch likes for the tweet
        likes = DatabaseHandler.get_likes(conn, tweetID)

        # Fetch comments for the tweet
        comments = DatabaseHandler.read_comments(conn, tweetID)

        # Include likes and comments in the tweet data
        enriched_data.append({
            "tweetID": tweetID,
            "tweet": tweet[1],
            "username": tweet[2],
            "media_url": tweet[3],
            "timestamp": tweet[4],
            "likes": likes,
            "comments": comments
        })

    conn.close()

    return jsonify(enriched_data)


@app.route('/api/likes/<tweetID>', methods=['GET'])
def get_likes(tweetID):
    conn = DatabaseHandler.connect_db()
    likes = DatabaseHandler.get_likes(conn, tweetID)
    conn.close()
    return jsonify(likes)

@app.route('/api/comments/<tweetID>', methods=['GET'])
def get_comments(tweetID):
    conn = DatabaseHandler.connect_db()
    comments = DatabaseHandler.read_comments(conn, tweetID)
    conn.close()
    return jsonify(comments)



@app.route('/api/search', methods=['GET'])
def search_users():
    search_term = request.args.get('q', None)
    if search_term:
        conn = DatabaseHandler.connect_db()
        cursor = conn.cursor()
        query = f"SELECT username FROM Users WHERE username LIKE '%{search_term}%'"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"username": row[0]} for row in rows])
    else:
        return jsonify({"error": "Search term is required"}), 400





@app.route('/api/login', methods=['POST'])
def login():
    conn = DatabaseHandler.connect_db()
    data = request.json
    username = data['username']
    password = data['password']

    if not DatabaseHandler.authenticate_user(conn, username, password):
        conn.close()
        return Response('Not authorized!', 401, {'Content-Type': 'text/html'})

    print(f"Welcome Again {username}!")
    conn.close()
    max_age = 180 * 60  # 180 minutes in seconds

    response = make_response('OK', 200)
    response.set_cookie('myCookie12345', 'cookie_value', max_age=max_age)
    response.headers['Content-Type'] = 'application/json'
    return response






@app.route('/api/share', methods=['POST'])
def post_share():
    conn = DatabaseHandler.connect_db()
    data = request.json
    username = data['username']
    id = data['tweetID']
    DatabaseHandler.share_tweet(conn, id, username)
    conn.close()
    return Response('POST share request received!', 200, {'Content-Type': 'text/html'})



@app.route('/api/comment', methods=['POST'])
def post_comment():
    conn = DatabaseHandler.connect_db()
    data = request.json
    tweetID = data['tweetID']
    username = data['username']
    comment = data['comment']
    DatabaseHandler.write_comment(conn, tweetID, username, comment)
    conn.close()
    return Response('POST comment request received!', 200, {'Content-Type': 'text/html'})



@app.route('/api/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username', None)
    decoded_username = unquote(username)
    if decoded_username:
        conn = DatabaseHandler.connect_db()
        profile_data = DatabaseHandler.read_profile(conn, decoded_username)
        conn.close()
        return jsonify(profile_data)
    else:
        return jsonify({"error": "Username is required"}), 400



@app.route('/api/profile_pic/<username>', methods=['GET'])
def get_and_serve_profile_picture(username):
    decoded_username = unquote(username)
    conn = DatabaseHandler.connect_db()
    profile_picture_url = DatabaseHandler.get_profile_picture_url(conn, decoded_username)
    conn.close()

    if profile_picture_url:
        file_path = f"{profile_picture_url}.jpg"
        file_path_with_ext = profile_picture_url
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/jpg')
        elif os.path.exists(file_path_with_ext):
            return send_file(file_path_with_ext, mimetype='image/jpg')
        else:
            return Response('Profile picture file not found', 404, {'Content-Type': 'text/html'})
    else:
        return Response('Profile picture not found', 404, {'Content-Type': 'text/html'})



@app.route('/api/tweet', methods=['POST'])
def post_tweet():
    conn = DatabaseHandler.connect_db()
    tweet = request.form.get('tweet')
    username = request.form.get('username')
    media_url = None

    file = request.files.get('media')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(upload_path)
        media_url = f'/uploads/{filename}'

    result = DatabaseHandler.write_tweet(conn, tweet, username, media_url)
    conn.close()

    if result is not None:
        return jsonify(result)
    else:
        return Response('Failed to post tweet', 500, {'Content-Type': 'text/html'})

@app.route('/api/like', methods=['POST'])
def post_like():
    conn = DatabaseHandler.connect_db()
    data = request.json
    username = data['username']
    id = data['tweetID']
    DatabaseHandler.post_like(conn, id, username)
    conn.close()
    return Response('POST like request received!', 200, {'Content-Type': 'text/html'})



@app.route('/api/notifications/<username>', methods=['GET'])
def get_notifications(username):
    decoded_username = unquote(username)
    conn = DatabaseHandler.connect_db()
    notifications = DatabaseHandler.read_notifications(conn, decoded_username)
    return jsonify(notifications)


@app.route('/api/notification/<int:notificationID>', methods=['DELETE'])
def remove_notification(notificationID):
    conn = DatabaseHandler.connect_db()
    success = DatabaseHandler.remove_notification(conn, notificationID)
    if success:
        return jsonify({"message": "Notification removed successfully"}), 200
    else:
        return jsonify({"message": "Failed to remove notification"}), 400





@app.route('/api/like', methods=['DELETE'])
def post_dislike():
    conn = DatabaseHandler.connect_db()
    data = request.json
    username = data['username']
    id = data['tweetID']
    DatabaseHandler.post_disliked(conn, id, username)
    conn.close()
    return Response('POST disliked request received!', 200, {'Content-Type': 'text/html'})


@app.route('/api/tweet', methods=['DELETE'])
def delete_tweet():
    conn = DatabaseHandler.connect_db()
    data = request.json
    id = data['tweetID']
    media = data['containsMedia']

    if media == 'yes':
        # Fetch the media URL from the database before deleting the tweet
        media_url = DatabaseHandler.get_media_url_by_tweetID(conn, id)

        if media_url:
            # Extract the filename from the media URL
            filename = media_url.split('/')[-1]

            # Build the full path of the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Remove the file from the upload folder
            if os.path.exists(file_path):
                os.remove(file_path)


    DatabaseHandler.delete_tweet(conn, id)
    conn.close()
    return Response('DELETE request received!', 200, {'Content-Type': 'text/html'})



@app.route('/api/user', methods=['DELETE'])
def delete_account():
    username = request.args.get('username', None)
    decoded_username = unquote(username)
    conn = DatabaseHandler.connect_db()
    if DatabaseHandler.delete_user(conn, decoded_username):
        conn.close()
        return Response('Account Permanently Deleted!', 200, {'Content-Type': 'text/html'})
    else:
        conn.close()
        return Response('Failed to delete the account', 400, {'Content-Type': 'text/html'})

@socketio.on('send_message')
def send_message(data):
    conn = DatabaseHandler.connect_db()

    sender = data['sender']
    receiver = data['receiver']
    content = data['content']

    # Save the message to the database
    DatabaseHandler.send_chat(conn, sender, receiver, content)

    # Fetch the last message for the sender or receiver
    last_message = DatabaseHandler.fetch_last_chat_for_user(conn, receiver)



    # Emit the last message to the connected client(s)
    socketio.emit('receive_message', last_message, room=receiver)

    #emit('receive_message', last_message, broadcast=True)
    conn.close()




@app.route('/api/fetch_chats', methods=['GET'])
def fetch_chats():
    username = request.args.get('username', None)
    decoded_username = unquote(username)
    if decoded_username:
        conn = DatabaseHandler.connect_db()
        chats = DatabaseHandler.fetch_chats_for_user(conn, decoded_username)
        conn.close()
        return jsonify(chats)
    else:
        return jsonify({"error": "Username is required"}), 400




@app.route('/api/mark_as_read', methods=['POST'])
def mark_as_read():
    username = request.args.get('username', None)
    otherUser = request.args.get('otherUser', None)
    decoded_username = unquote(username)
    decoded_otheruser = unquote(otherUser)
    conn = DatabaseHandler.connect_db()
    if DatabaseHandler.mark_read(conn, decoded_username, decoded_otheruser):
        conn.close()
        return Response('Marked as read', 200, {'Content-Type': 'text/html'})
    else:
        conn.close()
        return Response('Failed to mark as read', 400, {'Content-Type': 'text/html'})


@app.route('/api/settings', methods=['PUT'])
def update_profile():
    update_type = request.args.get('type')
    username = request.args.get('username')
    new_value = request.form.get('new_value')

    conn = DatabaseHandler.connect_db()

    if update_type == 'profile_pic':
        file = request.files['new_value']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('profiles', filename)
            file_path = file_path.replace('\\', '/')
            file.save(file_path)
            success = DatabaseHandler.update_profile(conn, username, 'profile_picture_url', file_path)
    elif update_type == 'name':
        success = DatabaseHandler.update_profile(conn, username, 'username', new_value)
    elif update_type == 'bio':
        success = DatabaseHandler.update_profile(conn, username, 'bio', new_value)
    else:
        return jsonify({"status": "error", "message": "Invalid update type"}), 400

    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to update"}), 500




@app.route('/api/create_account', methods=['POST'])
def create_account():
    username = request.form.get('username')
    password = request.form.get('password')
    bio = request.form.get('bio')
    file = request.files.get('profile_pic')
    conn = DatabaseHandler.connect_db()

    # Check if username already exists
    if DatabaseHandler.username_exists(conn, username):
        return jsonify({"status": "error", "message": "Username already taken"}), 400

    # Save profile picture
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('profiles', filename)
        file_path = file_path.replace('\\', '/')
        file.save(file_path)
    else:
        file_path = None
    # Create user account
    success = DatabaseHandler.create_user(conn, username, password, bio, file_path)

    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to create account"}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)
