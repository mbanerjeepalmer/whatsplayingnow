import os
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import UserProfile
import traceback
from oauthlib.oauth2 import TokenExpiredError
from .utils import * # TODO be less stupid

# TODO move all of this
scopes = 'user-read-currently-playing user-read-recently-played'
authorization_base_url = 'https://accounts.spotify.com/authorize'
auth_url = 'https://accounts.spotify.com/api/token'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if 'HEROKU' in os.environ:
    client_secret, client_id = os.environ['SPOTIFY_CLIENT_SECRET'], os.environ['SPOTIFY_CLIENT_ID']
    redirect_uri = 'https://whatsplayingnow.herokuapp.com/callback/'
else:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    redirect_uri = 'http://127.0.0.1:8000/callback/'
    with open(os.path.join(BASE_DIR, 'secrets.json'), 'r') as infile:
        secrets = json.loads(infile.read())
        client_secret, client_id = secrets['client_secret'], secrets['client_id']


def auth(request):
    """show a spotify auth url"""
    client = OAuth2Session(client_id=client_id, scope=scopes, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(url=authorization_base_url)
    context_dict = {'authorization_url': authorization_url}
    # TODO work out how pickling works so that I don't have to recreate the client each time, presumably
    return render(request, 'registration/login.html', context=context_dict)

@login_required
def callback(request):
    """
    Take a URL and use that to get tokens through OAuth.
    Then update those add or update those tokens in the database.
    """
    try:
        user = request.user
        authorization_response = request.build_absolute_uri()
        client = OAuth2Session(client_id=client_id, scope=scopes, redirect_uri=redirect_uri)
        token = client.fetch_token(token_url=auth_url, authorization_response=authorization_response, client_secret=client_secret)
        user_details = client.get('https://api.spotify.com/v1/me')
        user_details.raise_for_status()
        if client.authorized:
            spotify_id = user_details.json()['id']
            token['user'] = user
            token['spotify_name'] = user_details.json()['display_name']
            UserProfile.objects.update_or_create(defaults=token, spotify_id=spotify_id)
            # TODO move this whole bit elsewhere and make more general purpose
            # The update_or_create also needs to know what to use, presumably? Otherwise it will always create rather than update now?
        return HttpResponse(user_details.json()['display_name'] + " what you play will now show on https://whatsplayingnow.herokuapp.com")
    except Exception as e:
        error_message = "Argh! \n" + str(e) + traceback.format_exc()
        return HttpResponse(error_message)

@login_required
def tracks(request, spotify_id=None):
    """
    See who's playing what:
    This checks who you're requesting for by grabbing from the URL
    Asks Spotify for data on that person
    Returns the data
    """
    try:
        # TODO less bad than before
        # But still seems like odd copy paste
        tracks_details = {}
        spotify_user = get_spotify_user(spotify_id)
        client = authorise_spotify_user(client_id, spotify_user)
        tracks_details['now_playing'] = get_now_playing(client)
        tracks_details['recently_played'] = get_recently_played(client)
        tracks_details['available_spotify_accounts'] = available_spotify_accounts(request.user)
        return render (request, 'jukebox/tracks.html', context=tracks_details)
    except TokenExpiredError:
        refresh_spotify_user(client, client_id, client_secret, spotify_user, auth_url)
        return tracks(request)
    except Exception as general_error:
        error_message = "Damn. \n"+ str(general_error) + traceback.format_exc()
        return HttpResponse(error_message)
    else:
        return HttpResponse(r"No idea what's happened here  ¯\_(ツ)_/¯")
