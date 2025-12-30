#!/usr/bin/env python3

from random import randint, choice as rc

from faker import Faker

from app import app
from models import db, Note, User

fake = Faker()

with app.app_context():

    print("Deleting all records...")
    Note.query.delete()
    User.query.delete()

    fake = Faker()

    print("Creating users...")

    # make sure users have unique usernames
    users = []
    usernames = []

    for i in range(20):
        username = fake.first_name()
        while username in usernames:
            username = fake.first_name()
        usernames.append(username)

        user = User(
            username=username,
            bio=fake.paragraph(nb_sentences=3),
        )

        user.password_hash = user.username + 'password'

        users.append(user)

    db.session.add_all(users)

    print("Creating notes...")
    notes = []
    for i in range(100):
        content = fake.paragraph(nb_sentences=8)
        note = Note(
            title=fake.sentence(),
            content=content,
            user=rc(users)
        )

        note.user = rc(users)

        notes.append(note)

    db.session.add_all(notes)
    db.session.commit()
    print("Complete.")
