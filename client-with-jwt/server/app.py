from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Note, UserSchema, NoteSchema

class Signup(Resource):
    def post(self):
        request_json = request.get_json()

        username = request_json.get('username')
        password = request_json.get('password')
        bio = request_json.get('bio')

        try:
            user = User(
            username=username,
            bio=bio
        )
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return UserSchema().dump(user), 201
        except IntegrityError:
            return {'error': '422 Unprocessable Entity'}, 422

class CheckSession(Resource):
    def get(self):
        if session.get('user_id'):
            user = User.query.filter(User.id == session['user_id']).first()
            return UserSchema().dump(user), 200
        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):

        username = request.get_json()['username']
        password = request.get_json()['password']

        user = User.query.filter(User.username == username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {'error': '401 Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return {}, 204
        return {}, 401

class RecipeIndex(Resource):
    def get(self):
        if session.get('user_id'):
            schema = NoteSchema(many=True)
            return schema.dump(Note.query.all()), 200
        return {'error': '401 Unauthorized'}, 401

    def post(self):
        request_json = request.get_json()
        if session.get('user_id'):
            try:
                note = Note(
                    title=request_json.get('title'),
                    content=request_json.get('content'),
                    user_id=session.get('user_id')
                )
                db.session.add(note)
                db.session.commit()
                return NoteSchema().dump(note), 201

            except (IntegrityError, ValueError) as e:
                db.session.rollback()
                return {"error": str(e)}, 422
        return {'error': '401 Unauthorized'}, 401


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)