import os
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session, TokenUpdated
from .models import UserProfile
import traceback
from oauthlib.oauth2 import TokenExpiredError
from .utils import recently_played_tracks, now_playing_track, available_spotify_accounts

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
    """See who's playing what"""
    try:
        # TODO this is all a crock of shit
        # Split apart into different elements
        # Allow choice between different users
        tracks_details = {}
        try:
            spotify_user = UserProfile.objects.get(spotify_id=spotify_id)
        except UserProfile.DoesNotExist:
            spotify_user = UserProfile.objects.order_by('expires_at').last() # TODO This breaks if there are no user Profiles, obviously
        token = spotify_user.__dict__ # TODO clearly this is ridiculous because I have to overwrite it later for an expired token
        del token['_state'], token['id'], token['user_id']
        client = OAuth2Session(client_id, token=token)
        now_playing_request = client.get('https://api.spotify.com/v1/me/player/currently-playing') #TODO tidy up and remove copy/paste
        if now_playing_request.status_code == 200:
            now_playing_dict = now_playing_request.json()
            now_playing_details = now_playing_track(now_playing_dict) # TODO this breaks if the user has never listened to anything on Spotify before
            tracks_details['now_playing'] = now_playing_details
        else:
            tracks_details['now_playing'] = {'now_playing_dict': {'track':'Spotify says nothing is playing right now.'}}
        recents_request = client.get('https://api.spotify.com/v1/me/player/recently-played')
        recents_request.raise_for_status()
        recents_dict = recents_request.json()
        recently_played_details = recently_played_tracks(recents_dict) # This is completely wrong.
        tracks_details['recently_played'] = recently_played_details
        tracks_details['available_spotify_accounts'] = available_spotify_accounts(request.user)
        return render (request, 'jukebox/tracks.html', context=tracks_details)
    except TokenExpiredError:
        # TODO Option 3 https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
        extra = dict(client_id=client_id, client_secret=client_secret)
        token = client.refresh_token(auth_url, **extra)
        spotify_user = UserProfile.objects.order_by('expires_at').last()
        for key, value in token.items():
            setattr(spotify_user, key, value)
        spotify_user.save()
        return tracks(request)
    except Exception as general_error:
        error_message = "Damn. \n"+ str(general_error) + traceback.format_exc()
        return HttpResponse(error_message)
    else:
        return HttpResponse(r"No idea what's happened here  ¯\_(ツ)_/¯")
