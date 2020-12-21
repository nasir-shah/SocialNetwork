from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from pymongo import MongoClient, DESCENDING, ASCENDING
import datetime as dt
from bson.json_util import dumps
from bson import ObjectId
from user import User

client = MongoClient('mongodb+srv://test:test@socialnetwork.fdzic.mongodb.net/<dbname>?retryWrites=true&w=majority')

social_db = client.get_database('SocialNetworkDB')

users_collections = social_db.get_collection('users')
posts_collections = social_db.get_collection('posts')
comments_collections = social_db.get_collection('comments')
likes_collections = social_db.get_collection('likes')

def save_user(username, email, password):
    pasword_hash = generate_password_hash(password)
    users_collections.insert_one({'_id': username, 'email': email, 'password': pasword_hash})

def get_user(username):
    user_data = users_collections.find_one({'_id': username})
    return User(user_data['_id'], user_data['email'], user_data['password']) if user_data else None

def save_post(username, post, time, likes):
    id = posts_collections.insert_one({'username': username, 'post': post, 'time': time, 'created_at': dt.datetime.now(),'likes': likes}).inserted_id
    return str(id)

def update_post(post_id, likes):
    filter = { '_id': ObjectId(post_id)}
    newvalues = { "$set": { 'likes': likes} } 
    posts_collections.update_one(filter, newvalues) 

def get_posts():
    posts = posts_collections.find().sort('_id', DESCENDING)
    return posts

def save_comment(id, username, comment, time):
    comments_collections.insert_one({'post_id': id, 'username': username, 'comment': comment, 'time': time, 'created_at': dt.datetime.now()})

def get_comments(post_id, records = 0):
    comments = list(
        comments_collections.find({'post_id': post_id}).sort('_id', DESCENDING))
    return comments

def save_like(post_id , username):
    likes_collections.insert_one({'_id': {'post_id': post_id, 'username': username}, 'liked_at': dt.datetime.now()})

def check_likes(post_id , username):
    return likes_collections.find_one({'_id': {'post_id': post_id, 'username': username}})

def get_likes(post_id):
    return posts_collections.find_one({'_id': ObjectId(post_id)},{"likes" : 1})['likes']
