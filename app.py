# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import os
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *

from models import db, Artist, Venue, Show, Genre

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """Get a list of all venues"""
    venues = Venue.query.all()

    venue_data = {}

    for venue in venues:
        # For each venue, calculate the number of upcoming shows
        upcoming_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).count()

        key = (venue.city, venue.state)
        if key not in venue_data:
            venue_data[key] = {
                "city": venue.city,
                "state": venue.state,
                "venues": []
            }

        venue_data[key]["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": upcoming_shows
        })

    # Convert the dictionary to a list for the template
    data = [value for key, value in venue_data.items()]

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # Get the search term from the form
    search_term = request.form.get('search_term', '')

    # Perform a case-insensitive search using ilike
    matching_venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

    # Prepare the data for the response
    data = []
    for venue in matching_venues:
        num_upcoming_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).count()
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # Fetch the venue data using venue_id
    venue = Venue.query.get(venue_id)
    if not venue:
        # Render a 404 page if the venue is not found
        abort(404)

    # Fetch past shows and upcoming shows for the venue
    past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).all()
    upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).all()

    past_shows = [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
    } for show in past_shows_query]

    upcoming_shows = [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
    } for show in upcoming_shows_query]

    # Construct the data dictionary for the venue
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [genre.name for genre in venue.genres],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Get form data from request
    form_data = request.form

    try:
        # Create a new Venue instance using form data
        new_venue = Venue(
            name=form_data['name'],
            city=form_data.get('city'),
            state=form_data.get('state'),
            address=form_data.get('address'),
            phone=form_data.get('phone'),
            genres=form_data.getlist('genres'),
            facebook_link=form_data.get('facebook_link'),
            # Add other fields as necessary
        )

        # Add the new venue to the database session and commit
        db.session.add(new_venue)
        db.session.commit()

        # Flash a success message
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
        # Roll back the session in case of an error
        db.session.rollback()

        # Flash an error message
        flash('An error occurred. Venue ' + form_data['name'] + ' could not be listed.')

    finally:
        # Close the session
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        # Find the venue with the given id
        venue_to_delete = Venue.query.get(venue_id)

        # If no venue found, return an error
        if not venue_to_delete:
            flash(f'No venue found with id {venue_id}')
            return jsonify({'success': False}), 404

        # Delete the venue
        db.session.delete(venue_to_delete)

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash('Venue was successfully deleted!')

    except:
        # Roll back the session in case of an error
        db.session.rollback()

        # Flash an error message
        flash('An error occurred. Venue could not be deleted.')

    finally:
        # Close the session
        db.session.close()

        # Redirect the user to the homepage (for the bonus challenge)
    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = [{
        "id": artist.id,
        "name": artist.name
    }
        for artist in artists
    ]
    return render_template('pages/artists.html', artists=sorted(data, key=lambda artist: artist['name']))


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')

    # Using ilike for case-insensitive search
    matching_artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

    response = {
        "count": len(matching_artists),
        "data": [{
            "id": artist.id,
            "name": artist.name,
            # Assuming you have a method or property to get the number of upcoming shows for an artist
            "num_upcoming_shows": artist.num_upcoming_shows,
        } for artist in matching_artists]
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # Fetch the artist data using artist_id
    artist = Artist.query.get(artist_id)
    if not artist:
        # Render a 404 page if the artist is not found
        abort(404)

    # Fetch past shows and upcoming shows for the artist
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()

    past_shows = [{
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
    } for show in past_shows_query]

    upcoming_shows = [{
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
    } for show in upcoming_shows_query]

    # Construct the data dictionary for the artist
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [genre.name for genre in artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    # Query the artist with the given artist_id from the database
    artist_query = Artist.query.get(artist_id)

    # Check if the artist exists in the database
    if artist_query:
        # Populate the form with values from the artist
        form.name.data = artist_query.name
        form.genres.data = artist_query.genres
        form.city.data = artist_query.city
        form.state.data = artist_query.state
        form.phone.data = artist_query.phone
        form.website_link.data = artist_query.website_link
        form.facebook_link.data = artist_query.facebook_link
        form.seeking_venue.data = artist_query.seeking_venue
        form.seeking_description.data = artist_query.seeking_description
        form.image_link.data = artist_query.image_link

        # Create a dictionary from the artist object to be used in the template
        artist = {
            "id": artist_query.id,
            "name": artist_query.name,
            "genres": artist_query.genres,
            "city": artist_query.city,
            "state": artist_query.state,
            "phone": artist_query.phone,
            "website_link": artist_query.website_link,
            "facebook_link": artist_query.facebook_link,
            "seeking_venue": artist_query.seeking_venue,
            "seeking_description": artist_query.seeking_description,
            "image_link": artist_query.image_link
        }
    else:
        flash('Artist with ID {} not found.'.format(artist_id))
        return redirect(url_for('index'))

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # Query the artist with the given artist_id from the database
    artist = Artist.query.get(artist_id)

    if not artist:
        flash('Artist with ID {} not found.'.format(artist_id))
        return redirect(url_for('index'))

    try:
        # Update the artist's attributes with values from the form
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.website_link = request.form['website_link']

        # Additional fields can be updated here as needed

        # Commit the changes to the database
        db.session.commit()
        flash('Artist {} was successfully updated!'.format(artist.name))

    except:
        db.session.rollback()
        flash('An error occurred. Artist {} could not be updated.'.format(artist.name))
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    # Query the venue with the given venue_id from the database
    venue_query = Venue.query.get(venue_id)

    # Check if the venue exists in the database
    if venue_query:
        # Populate the form with values from the venue
        form.name.data = venue_query.name
        form.genres.data = venue_query.genres
        form.address.data = venue_query.address
        form.city.data = venue_query.city
        form.state.data = venue_query.state
        form.phone.data = venue_query.phone
        form.website_link.data = venue_query.website_link
        form.facebook_link.data = venue_query.facebook_link
        form.seeking_talent.data = venue_query.seeking_talent
        form.seeking_description.data = venue_query.seeking_description
        form.image_link.data = venue_query.image_link

        # Create a dictionary from the venue object to be used in the template
        venue = {
            "id": venue_query.id,
            "name": venue_query.name,
            "genres": venue_query.genres,
            "address": venue_query.address,
            "city": venue_query.city,
            "state": venue_query.state,
            "phone": venue_query.phone,
            "website_link": venue_query.website_link,
            "facebook_link": venue_query.facebook_link,
            "seeking_talent": venue_query.seeking_talent,
            "seeking_description": venue_query.seeking_description,
            "image_link": venue_query.image_link
        }
    else:
        flash('Venue with ID {} not found.'.format(venue_id))
        return redirect(url_for('index'))

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # Fetch the venue with the given venue_id
    venue_to_update = Venue.query.get(venue_id)

    if not venue_to_update:
        flash(f'Error: Venue with ID {venue_id} not found.')
        return redirect(url_for('index'))

    try:
        # Update the venue's attributes with the form data
        venue_to_update.name = request.form['name']
        venue_to_update.genres = request.form.getlist('genres')
        venue_to_update.address = request.form['address']
        venue_to_update.city = request.form['city']
        venue_to_update.state = request.form['state']
        venue_to_update.phone = request.form['phone']
        venue_to_update.website_link = request.form['website_link']
        venue_to_update.facebook_link = request.form['facebook_link']
        venue_to_update.seeking_talent = 'seeking_talent' in request.form
        venue_to_update.seeking_description = request.form['seeking_description']
        venue_to_update.image_link = request.form['image_link']

        # Commit the changes to the database
        db.session.commit()

        flash(f'Venue {venue_to_update.name} was successfully updated!')

    except:
        # Rollback the session in case of an error
        db.session.rollback()
        flash(f'An error occurred. Venue {venue_to_update.name} could not be updated.')

    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Create a new Artist object using the form data
    # Create a new Artist object using the form data
    genre_names = request.form.getlist('genres')
    genre_objects = Genre.query.filter(Genre.name.in_(genre_names)).all()
    new_artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=genre_objects,
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website_link=request.form['website_link'],
        seeking_venue='seeking_venue' in request.form,
        seeking_description=request.form['seeking_description']
    )

    try:
        # Add the new artist to the database and commit
        db.session.add(new_artist)
        db.session.commit()

        # Flash a success message
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        # Rollback the session in case of an error and flash an error message
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # Query all shows from the database
    shows_query = Show.query.all()

    # Construct the data for each show
    data = [{
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
    } for show in shows_query]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # Create a new Show object using the form data
    new_show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time']
    )

    try:
        # Add the new show to the database and commit
        db.session.add(new_show)
        db.session.commit()

        # Flash a success message
        flash('Show was successfully listed!')
    except:
        # Rollback the session in case of an error and flash an error message
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:

if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
'''