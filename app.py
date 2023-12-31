import os

from flask import Flask, render_template, redirect, url_for, session, request
from flask_oauthlib.client import OAuth
import requests
from PIL import Image
from io import BytesIO
import base64


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
SPOTIFY_SCOPES = ['user-read-recently-played user-read-private user-library-read user-read-email playlist-read-private user-top-read']

oauth = OAuth(app)

spotify = oauth.remote_app(
    'spotify',
    request_token_params={
        'scope':SPOTIFY_SCOPES,},
    base_url='https://api.spotify.com/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.spotify.com/api/token',
    authorize_url='https://accounts.spotify.com/authorize',
    consumer_key='96626927888642e5bedd41bf75518c59',
    consumer_secret=os.getenv('consumer_secret'),
)

@app.route('/')
def home():
    # Check if the user has access token
    access_token = session.get('spotify_token')

    if access_token:
        return redirect(url_for('collage'))

    # If the user is not logged in, show the login page
    return render_template('index.html', user_data='')


@app.route('/login')
def login():
    return spotify.authorize(callback=url_for('spotify_authorized', _external=True))


@app.route('/spotify_authorized')
def spotify_authorized():
    response = spotify.authorized_response()
    if response is None or response.get('access_token') is None:
        # Handle authentication failure
        return redirect(url_for('login'))

    # Save the access token and refresh token in the session
    session['spotify_token'] = response['access_token']
    session['spotify_refresh_token'] = response.get('refresh_token')

    # Redirect to collage
    return redirect(url_for('collage'))

@app.route('/collage')
def collage():
    access_token = session.get('spotify_token')
    if not access_token:
        return redirect(url_for('login'))

    # Fetch the user's top tracks data from the Spotify API
    limit= 50
    headers = {'Authorization': f'Bearer {access_token}'}
    top_tracks_url = 'https://api.spotify.com/v1/me/top/tracks'
    timerange=request.args.get('time_range','short_term')
    response = requests.get(top_tracks_url, headers=headers, params={'limit':{limit},'time_range':{timerange}})

    if response.status_code == 200:
        top_tracks_data = response.json()
        top_tracks = top_tracks_data.get('items')

        # Extract album images from the top tracks
        album_images_set = set()
        for track in top_tracks:
            album_images_set.add(track['album']['images'][0]['url'])
            if len(album_images_set)>= 25:
                break
        album_images = list(album_images_set)
        # Render the 'collage.html' template with the album_images data
        return render_template('collage.html', album_images=album_images)

    else:
        print(f"Failed to fetch top tracks data. Status code: {response.status_code}")
        return render_template('error.html', message='Failed to fetch top tracks data')


@app.route('/logout')
def logout():
    # Clear session data
    session.pop('spotify_token', None)
    session.pop('spotify_refresh_token', None)
    session.clear()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)
