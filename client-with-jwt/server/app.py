from flask import request, session, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from config import app, db, api, jwt
from models import User, Note, UserSchema, NoteSchema
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request

@app.before_request
def check_if_logged_in():
    open_access_list = ['signup', 'login']
    if request.endpoint in open_access_list:
        return
    try:
        verify_jwt_in_request()
    except Exception:
        return make_response(jsonify({'error': 'Missing or invalid token'}), 401)

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
            access_token = create_access_token(identity=str(user.id))
            return make_response(jsonify(token=access_token, user=UserSchema().dump(user)), 201)
        except IntegrityError:
            return {'error': '422 Unprocessable Entity'}, 422

class WhoAmI(Resource):
    def get(self):
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return UserSchema().dump(user), 200
        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):

        username = request.get_json()['username']
        password = request.get_json()['password']

        user = User.query.filter(User.username == username).first()

        if user and user.authenticate(password):
            token = create_access_token(identity=str(user.id))
            return make_response(jsonify(token=token, user=UserSchema().dump(user)), 200)

        return {'error': '401 Unauthorized'}, 401

class NoteIndex(Resource):
    def get(self):
        user_id = get_jwt_identity()
        if user_id:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            pagination = Note.query.filter_by(user_id=user_id).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            return {
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "next_page": pagination.next_num,
                "prev_page": pagination.prev_num,
                "notes": NoteSchema(many=True).dump(pagination.items)
            }, 200
        return {'error': '401 Unauthorized'}, 401

    def post(self):
        request_json = request.get_json()
        user_id = get_jwt_identity()
        if user_id:
            try:
                note = Note(
                    title=request_json.get('title'),
                    content=request_json.get('content'),
                    user_id=get_jwt_identity()
                )
                db.session.add(note)
                db.session.commit()
                return NoteSchema().dump(note), 201

            except (IntegrityError, ValueError) as e:
                db.session.rollback()
                return {"error": str(e)}, 422
        return {'error': '401 Unauthorized'}, 401

class NoteByID(Resource):
    def patch(self, id):
        user_id = get_jwt_identity()
        note = Note.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            return {"error": "Note not found"}, 404

        request_json = request.get_json()
        try:
            for attr in request_json:
                setattr(note, attr, request_json[attr])
            db.session.commit()
            return NoteSchema().dump(note), 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 422

    def delete(self, id):
        user_id = get_jwt_identity()
        note = Note.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            return {"error": "Note not found"}, 404

        db.session.delete(note)
        db.session.commit()
        return {}, 204

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(WhoAmI, '/me', endpoint='me')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(NoteIndex, '/notes', endpoint='notes')
api.add_resource(NoteByID, '/notes/<int:id>', endpoint='note_by_id')


if __name__ == '__main__':
    app.run(port=5555, debug=True)