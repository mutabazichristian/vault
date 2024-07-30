import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, session
from mysql.connector import Error
from dotenv import load_dotenv
auth = Blueprint('auth', __name__)

# LOGIN ROUTE


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            cursor = g.db.cursor(dictionary=True, buffered=True)

            try:
                cursor.execute(
                    "SELECT * FROM users WHERE email=%s AND password=%s",
                    (email, password)
                )
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user['user_id']
                    session['username'] = user['name']
                    return jsonify({"success": True, "message": "Login successful"}), 200
                else:
                    return jsonify({"success": False, "message": "Invalid email or password"}), 400
            except Error as e:
                print(f"The error '{e}' occurred")
                return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500
            finally:
                cursor.close()
        return jsonify({"success": False, "message": "Invalid request format"}), 400

    if request.method == 'GET':
        return render_template('login.html', api_url=os.getenv('API_URL'))


# LOGOUT ROUTE


@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('main.dashboard'))

# REGISTRATION ROUTE

    
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            if password != confirm_password:
                return jsonify({"success": False, "message": "Passwords do not match"}), 400

            # Check if user already exists
            cursor = g.db.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                cursor.close()
                return jsonify({"success": False, "message": "User already exists"}), 400

            # Insert new user into the database
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            g.db.commit()
            cursor.close()

            return jsonify({"success": True, "message": "Signup successful"}), 200

        return jsonify({"success": False, "message": "Invalid request format"}), 400

    if request.method == 'GET':
        return render_template('signup.html')
