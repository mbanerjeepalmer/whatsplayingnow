import os
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session, TokenUpdated
from .models import UserProfile
import traceback
from oauthlib.oauth2 import TokenExpiredError
from .spotify import recently_played_tracks, now_playing_track

# TODO move all of this
scopes = 'user-read-currently-playing user-read-recently-played'
authorization_base_url = 'https://accounts.spotify.com/authorize'
auth_url = 'https://accounts.spotify.com/api/token'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if 'HEROKU' in os.environ:
    client_secret, client_id = os.environ['SPOTIFY_CLIENT_SECRET'], os.environ['SPOTIFY_CLIENT_ID']
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
    try:
        user = request.user
        authorization_response = request.build_absolute_uri()
        client = OAuth2Session(client_id=client_id, scope=scopes, redirect_uri=redirect_uri)
        token = client.fetch_token(token_url=auth_url, authorization_response=authorization_response, client_secret=client_secret)
        r = client.get('https://api.spotify.com/v1/me')
        r.raise_for_status()
        if client.authorized:
            UserProfile.objects.update_or_create(defaults=token, user=user) # TODO move this whole bit elsewhere and make more general purpose
        return HttpResponse(r.json()['display_name'])
    except Exception as e:
        error_message = str(e) + traceback.format_exc()
        return HttpResponse(error_message)

@login_required
def tracks(request):
    try:
        # TODO this is all a crock of shit
        tracks_details = {}
        usr = UserProfile.objects.order_by('expires_at').last() # TODO This breaks if there are no user Profiles, obviously
        token = usr.__dict__ # TODO clearly this is ridiculous because I have to overwrite it later for an expired token
        del token['_state'], token['id'], token['user_id']
        client = OAuth2Session(client_id, token=token)
        now_playing_request = client.get('https://api.spotify.com/v1/me/player/currently-playing') #TODO tidy up and remove copy/paste
        if now_playing_request.status_code == 200:
            now_playing_dict = now_playing_request.json()
            now_playing_details = now_playing_track(now_playing_dict)
            tracks_details['now_playing'] = now_playing_details
        else:
            tracks_details['now_playing'] = {'now_playing_dict': {'track':'Spotify says nothing is playing right now.'}}
        recents_request = client.get('https://api.spotify.com/v1/me/player/recently-played')
        recents_request.raise_for_status()
        recents_dict = recents_request.json()
        recently_played_details = recently_played_tracks(recents_dict) # This is completely wrong.
        tracks_details['recently_played'] = recently_played_details
        return render (request, 'jukebox/tracks.html', context=tracks_details)
    except TokenExpiredError:
        # TODO Option 3 https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
        extra = dict(client_id=client_id, client_secret=client_secret)
        token = client.refresh_token(auth_url, **extra)
        usr = UserProfile.objects.order_by('expires_at').last()
        for key, value in token.items():
            setattr(usr, key, value)
        usr.save()
        return tracks(request)
    except Exception as general_error:
        error_message = str(general_error) + traceback.format_exc()
        return HttpResponse(error_message)
    else:
        return HttpResponse(r"No idea what's happened here  ¯\_(ツ)_/¯")
