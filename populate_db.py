from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

from config import INITIAL_DATA_PATH
from models import Genre, Venue, Artist, Show
from sqlalchemy import inspect

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
inspector = inspect(db.engine)

# Your models go here...

# Initialize the app and database
with app.app_context():
    # Drop all tables
    db.drop_all()

    # Recreate all tables based on the models
    db.create_all()
    print("printing inspector.get_table_names() ", inspector.get_table_names())

    # Load the JSON data
    with open(INITIAL_DATA_PATH, "r") as f:
        data = json.load(f)

    # Add genres to the database
    genre_objects = []
    for genre in data["genres"]:
        genre_objects.append(Genre(id=genre["id"], name=genre["name"]))
    db.session.add_all(genre_objects)
    db.session.commit()

    # Add venues to the database
    venue_objects = []
    for venue in data["venues"]:
        venue_objects.append(Venue(
            id=venue["id"],
            name=venue["name"],
            address=venue["address"],
            city=venue["city"],
            state=venue["state"],
            phone=venue["phone"],
            website_link=venue.get("website_link", ""),
            facebook_link=venue.get("facebook_link", ""),
            seeking_talent=venue.get("seeking_talent", False),
            seeking_description=venue.get("seeking_description", ""),
            image_link=venue["image_link"],
            genres=[genre_objects[genre_id - 1] for genre_id in venue["genres"]]
        ))
    db.session.add_all(venue_objects)
    db.session.commit()

    # Add artists to the database
    artist_objects = []
    for artist in data["artists"]:
        artist_objects.append(Artist(
            id=artist["id"],
            name=artist["name"],
            city=artist["city"],
            state=artist["state"],
            phone=artist["phone"],
            website_link=artist.get("website_link", ""),
            facebook_link=artist.get("facebook_link", ""),
            seeking_venue=artist.get("seeking_venue", False),
            seeking_description=artist.get("seeking_description", ""),
            image_link=artist["image_link"],
            genres=[genre_objects[genre_id - 1] for genre_id in artist["genres"]]
        ))
    db.session.add_all(artist_objects)
    db.session.commit()

    artist = Artist.query.get(4)
    print('printing artist', artist)

    # Add shows to the database
    show_objects = []
    for show in data["shows"]:
        show_objects.append(Show(
            venue_id=show["venue_id"],
            artist_id=show["artist_id"],
            start_time=datetime.fromisoformat(show["start_time"].replace("Z", "+00:00"))
        ))
    db.session.add_all(show_objects)

    db.session.commit()
