from bson.json_util import dumps
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO
from flask.logging import create_logger
from db import save_post, save_like , check_likes, get_likes, update_post, save_comment, get_posts, get_comments, save_user, get_user
from pymongo.errors import DuplicateKeyError
from utils.constants import PORT_NO
import datetime as dt
import json 


app = Flask(__name__)
app.secret_key = "iuefsdbfjksdhf"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


app.config['EXPLAIN_TEMPLATE_LOADING'] = True
LOG = create_logger(app)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/loginPage')
def loginPage():
    return render_template('login.html')

@app.route('/signupPage')
def signupPage():
    return render_template('signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = "User already exists!"
    return render_template('signup.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)
        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            message = 'Failed to login!'
    return render_template('login.html', message=message)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    username = current_user.username
    if username:
        posts = get_posts()
        return render_template('profile.html',  posts = posts, username = username)
    else:
        return redirect(url_for('home'))

@socketio.on('send_post')
def handle_send_post_event(data):
    created_at = dt.datetime.now()
    formatted_time = created_at.strftime("at %I:%M %p, %d %B'%Y ")
    data.update({"formatted_time": formatted_time})
    LOG.info("{} has posted : {} at {}".format(data["username"],data["post"], formatted_time))
    try:
        id = save_post(data["username"], data["post"], formatted_time, data["likes"])
        data.update({'id': id})
        socketio.emit('receive_post', data)
    except Exception as e:
        LOG.error(e)

@socketio.on('edit_post')
def handle_comment_post_event(data):
    created_at = dt.datetime.now()
    formatted_time = created_at.strftime("%d %b %Y at %I:%M %p")
    data.update({"formatted_time": formatted_time})
    if(data['type'] == 'like') and check_likes(data['post_id'], data['username']) == None:
        save_like(data['post_id'], data['username'])
        likes = get_likes(data['post_id']) + 1
        update_post(data['post_id'], likes)
        socketio.emit('like_post', {'likes': likes, 'id': data['post_id']})
    elif data['type'] == 'comment':
        save_comment(data['post_id'], data['username'], data['data'], data['formatted_time'])
        LOG.info("{} has posted : {} at {}".format(data["username"],data["data"], formatted_time))

@socketio.on('get_comments')
def fetch_comments(data):
    post_id = data['post_id']
    comments = get_comments(post_id)
    parse_comments = []
    for comment in comments:
        parse_comments.append({'username':comment['username'], 'comment': comment['comment'],'time': comment['time']})
    data = [{'post_id': post_id}]
    data.append(parse_comments)
    socketio.emit('send_comments', data = data)

@login_manager.user_loader
def load_user(username):
    return get_user(username)
    
if __name__ == '__main__':
    socketio.run(app,port=PORT_NO, debug=True)