import pyodbc

class DatabaseHandler:

    @staticmethod
    def connect_db():
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=DESKTOP-BJCTUTC;'
                              'Database=TweetDB;'
                              'Trusted_Connection=yes;'
                              'Pooling=True;'           # Enables pooling
                              'Max Pool Size=100;')

        return conn

    @staticmethod
    def add_notification(conn, username, type, tweetID, sender):
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Notifications (username, type, tweetID, sender) VALUES (?, ?, ?, ?)',
                       (username, type, tweetID, sender))
        conn.commit()

    @staticmethod
    def read_notifications(conn, username):
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Notifications WHERE username = ? ORDER BY timestamp DESC', (username,))
        rows = cursor.fetchall()
        return [{"notificationID": row[0], "username": row[1], "type": row[2], "tweetID": row[3], "sender": row[4],
                 "timestamp": row[5]} for row in rows]


    @staticmethod
    def read_profile(conn, username):
        cursor = conn.cursor()
        cursor.execute('SELECT username, bio FROM Users WHERE username = ?', (username,))
        row = cursor.fetchone()
        return {"username": row[0], "bio": row[1]}



    @staticmethod
    def read_tweets(conn, username=None):
        cursor = conn.cursor()
        query = 'SELECT * FROM Tweets'

        if username:
            query += f" WHERE username = '{username}'"

        # ORDER BY clause to sort by tweetID in descending order
        query += ' ORDER BY tweetID DESC'

        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def get_likes(conn, tweetID):
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM Likes WHERE tweetID = ?', (tweetID,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def read_comments(conn, tweetID):
        cursor = conn.cursor()
        cursor.execute('SELECT username, comment FROM Comments WHERE tweetID = ?', (tweetID,))
        rows = cursor.fetchall()
        return [{"username": row[0], "comment": row[1]} for row in rows]

    @staticmethod
    def read_shared_tweets(conn, username=None):
        cursor = conn.cursor()
        query = 'SELECT Tweets.* FROM Tweets INNER JOIN Shares ON Tweets.tweetID = Shares.tweetID'

        if username:
            query += f" WHERE Shares.username = '{username}'"

            # Add ORDER BY clause to sort by tweetID in descending order
            query += ' ORDER BY Tweets.tweetID DESC'

        cursor.execute(query)
        rows = cursor.fetchall()
        return rows




    @staticmethod
    def write_comment(conn, tweetID, username, comment):
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Comments (tweetID, username, comment) VALUES (?, ?, ?)',
                       (tweetID, username, comment))
        conn.commit()

        # Fetch the tweet owner's username
        cursor.execute('SELECT username FROM Tweets WHERE tweetID = ?', (tweetID,))
        row = cursor.fetchone()
        if row:
            tweet_owner_username = row[0]
            # Add notification
            DatabaseHandler.add_notification(conn, tweet_owner_username, 'comment', tweetID, username)



    @staticmethod
    def share_tweet(conn, tweet_id, username):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Shares (tweetID, username) VALUES (?, ?)", (tweet_id, username))
        conn.commit()

        # Fetch the tweet owner's username
        cursor.execute('SELECT username FROM Tweets WHERE tweetID = ?', (tweet_id,))
        row = cursor.fetchone()
        if row:
            tweet_owner_username = row[0]
            DatabaseHandler.add_notification(conn, tweet_owner_username, 'share', tweet_id, username)

    @staticmethod
    def remove_notification(conn, notificationID):
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM Notifications WHERE notificationID = ?', (notificationID,))
            conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error removing notification: {e}")
            return False

    @staticmethod
    def delete_user(conn, username):
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM Users WHERE username = ?', (username,))
            conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error deleting user account: {e}")
            return False

    @staticmethod
    def write_tweet(conn, tweet, username, media_url=None):
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO Tweets (tweet, username, media_url) VALUES (?, ?, ?)',
                           (tweet, username, media_url))
            conn.commit()

            # Fetching the last tweetID
            cursor.execute('SELECT TOP 1 tweetID FROM Tweets WHERE username=? ORDER BY tweetID DESC', (username,))
            row = cursor.fetchone()

            if row:
                tweet_id = row[0]
                return {'tweetID': tweet_id, 'username': username, 'tweet': tweet, 'media_url': media_url}
            else:
                return None
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    @staticmethod
    def post_like(conn, tweetID, username):
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Likes (tweetID, username) VALUES (?, ?)', (tweetID, username))
        conn.commit()
        # Fetch the tweet owner's username
        cursor.execute('SELECT username FROM Tweets WHERE tweetID = ?', (tweetID,))
        row = cursor.fetchone()
        if row:
            tweet_owner_username = row[0]
            # Add notification
            DatabaseHandler.add_notification(conn, tweet_owner_username, 'like', tweetID, username)

    @staticmethod
    def post_disliked(conn, tweetID, username):
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Likes WHERE tweetID = ? AND username = ?', (tweetID, username))
        conn.commit()



    @staticmethod
    def delete_tweet(conn, tweetID):
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Tweets WHERE tweetID = ?', (tweetID))
        conn.commit()


    @staticmethod
    def authenticate_user(conn, username, password):
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        return user is not None

    @staticmethod
    def create_user(conn, username, password):
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error creating user: {e}")
            return False

    @staticmethod
    def get_media_url_by_tweetID(conn, tweetID):
        cursor = conn.cursor()
        cursor.execute('SELECT media_url FROM Tweets WHERE tweetID = ?', (tweetID,))
        result = cursor.fetchone()
        return result[0] if result else None


    @staticmethod
    def get_profile_picture_url(conn, username):
        cursor = conn.cursor()
        cursor.execute('SELECT profile_picture_url FROM Users WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else None

    @staticmethod
    def fetch_chats_for_user(conn, username):
        cursor = conn.cursor()
        query = '''
            SELECT * FROM Messages 
            WHERE sender = ? OR receiver = ? 
            ORDER BY timestamp ASC
            '''
        cursor.execute(query, (username, username))
        rows = cursor.fetchall()
        return [{"messageID": row[0], "sender": row[1], "receiver": row[2], "content": row[3], "timestamp": row[4], "mark_as_read": row[5]} for
                row in rows]

    @staticmethod
    def fetch_last_chat_for_user(conn, username):
        cursor = conn.cursor()
        query = '''
            SELECT TOP (1) * FROM Messages 
            WHERE sender = ? OR receiver = ? 
            ORDER BY timestamp DESC
            '''
        cursor.execute(query, (username, username))
        row = cursor.fetchone()
        return {
            "messageID": row[0],
            "sender": row[1],
            "receiver": row[2],
            "content": row[3],
            "timestamp": row[4],
            "mark_as_read": row[5]
        } if row else None

    @staticmethod
    def send_chat(conn, sender, receiver, content):
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO Messages (sender, receiver, content, mark_as_read, timestamp) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)',
                (sender, receiver, content, False))
            conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error sending chat message: {e}")
            return False

    @staticmethod
    def mark_read(conn, username, otherUser):
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE Messages SET mark_as_read = ? WHERE sender = ? AND receiver = ?', (True, otherUser,username))
            conn.commit()
            return True
        except pyodbc.Error as e:
            print(f"Error marking message as read: {e}")

        return False

    @staticmethod
    def update_profile(conn, username, update_type, new_value):
        cursor = conn.cursor()
        try:
            cursor.execute(f'UPDATE Users SET {update_type} = ? WHERE username = ?', (new_value, username))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    @staticmethod
    def username_exists(conn, username):
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM Users WHERE username = ?', (username,))
        return cursor.fetchone() is not None

    @staticmethod
    def create_user(conn, username, password, bio, profile_pic):
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO Users (username, password, bio, profile_picture_url) VALUES (?, ?, ?, ?)',
                           (username, password, bio, profile_pic))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    @staticmethod
    def read_login_html():
        with open('LoginPage.html', 'rb') as f:
            return f.read()

    @staticmethod
    def read_html():
        with open('index.html', 'rb') as f:
            return f.read()








