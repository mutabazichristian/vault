from flask import Flask, jsonify, render_template


app = Flask(__name__)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = 'this is a message from the backend'
    
    return render_template('login.html', msg = msg)


app.run()
