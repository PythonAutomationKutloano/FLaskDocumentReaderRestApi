import docx2txt
from sklearn.feature_extraction.text import CountVectorizer
from flask import Flask, request, Response, jsonify
from werkzeug.utils import secure_filename
from sklearn.metrics.pairwise import cosine_similarity
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message



app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'briliware.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'  # change this IRL


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    test_user = User(first_name='Kutloano',
                     last_name='mokgethwa',
                     email='kutloano.mokgethwa@brilliware.com',
                     password='mokgethwa')

    db.session.add(test_user)
    db.session.commit()
    print('Database seeded!')


@app.route('/not_found')
def not_found():
    return jsonify(message='That resource was not found'), 404


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='That email already exists.'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succeeded!", access_token=access_token)
    else:
        return jsonify(message="Bad email or password"), 401


@app.route('/')
def ApiStatus():
    return jsonify(meassage='BRILLIWARE HR API IS UP AND RUNNING!'), 200 #


@app.route('/Brilliware/CompareDocuments', methods=['POST'])#THIS ENDPOINT WILL ALLOW DOCUMENTS TO BE COMPARED! AND THE RESULT IS A MATCH PERCENTAGE
def CompareDocuments(): 
    resume = request.files['resume']#Gets the resume.docx from the client
    job = request.files['job']#Gets the job.docx from the client
    if(resume and job):#if both documents are popultated then lets continue with our operation
        convertedResume = docx2txt.process(resume)
        convertedJob = docx2txt.process(job)
        text = [convertedResume,convertedJob]
        cv = CountVectorizer()
        c = cv.fit_transform(text) 
        match_percentage = cosine_similarity(c)[0][1]*100#this basically where the magic happens!
        return  jsonify(matchresult=(str(match_percentage)[0:5]+"% match")), 200  #we send off the response and a status code 200 OK!
    return 'Documents were compared succesfully!', 200


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')

user_schema = UserSchema()
users_schema = UserSchema(many=True)


if __name__ == '__main__':
    app.run()