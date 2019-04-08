import traceback
from copy import deepcopy
from .models import UserProfile
from requests_oauthlib import OAuth2Session, TokenUpdated

def get_now_playing(client):
    """Accepts an authorised OAuth client and returns a now playing dict."""
    now_playing = {}
    now_playing_request = client.get('https://api.spotify.com/v1/me/player/currently-playing') #TODO tidy up and remove copy/paste
    if now_playing_request.status_code == 200:
        now_playing_dict = now_playing_request.json()
        now_playing_details = now_playing_track(now_playing_dict) # TODO this breaks if the user has never listened to anything on Spotify before
        now_playing = now_playing_details
    else:
        now_playing = {'now_playing_dict': {'track':'Spotify says nothing is playing right now.'}}
    return now_playing

def now_playing_track(response_dict):
    """
    Same as recently_played_tracks pretty much. Potentially need to remove copy/paste.
    Uses https://developer.spotify.com/documentation/web-api/reference/player/get-the-users-currently-playing-track/
    """
    track = response_dict['item']
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    external_url = track['external_urls']['spotify']
    track_dict = dict(track_name=track_name,
                        artist_name=artist_name,
                        external_url=external_url,
                    )
    now_playing_dict = {'now_playing_dict': track_dict}
    return now_playing_dict

def get_recently_played(client):
    """
    Same as get_now_playing pretty much. Potentially need to remove copy/paste.
    """
    recents_request = client.get('https://api.spotify.com/v1/me/player/recently-played')
    recents_request.raise_for_status()
    recents_dict = recents_request.json()
    recently_played_details = recently_played_tracks(recents_dict) # This is completely wrong.
    return recently_played_details

def recently_played_tracks(response_dict):
    """
    Accepts a dictionary of the Spotify response and returns a dictionary of tracks.
    Recently played is here: https://developer.spotify.com/documentation/web-api/reference/player/get-recently-played/
    """
    recent_items = response_dict['items']
    tracks_dict = {}
    for item in recent_items:
        # TODO there will be a simpler way to do this, maybe using a comprehension
        track = item['track']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        external_url = track['external_urls']['spotify']
        played_at = item['played_at'] #TODO use dateutil.parser to convert this
        track_dict = dict(track_name=track_name,
                            artist_name=artist_name,
                            external_url=external_url,
                            played_at=played_at)
        tracks_dict[track_name] = track_dict
    recently_played_dict = {'recently_played_dict': tracks_dict}
    return recently_played_dict

def available_spotify_accounts(user):
    """
    Accepts a User object and returns all the spotify accounts they can access
    """
    acct_queryset = UserProfile.objects.filter(user=user).exclude(spotify_id__isnull=True)
    acct_dict = {acct.spotify_id: acct.spotify_name for acct in acct_queryset}
    return acct_dict

def get_spotify_user(spotify_id):
    """
    Accepts a Spotify User ID and returns a UserProfile object.
    """
    if spotify_id == None:
        spotify_user = UserProfile.objects.order_by('expires_at').last() # TODO This breaks if there are no user Profiles, obviously
    try:
        spotify_user = UserProfile.objects.get(spotify_id=spotify_id)
    except UserProfile.DoesNotExist:
        spotify_user = UserProfile.objects.order_by('expires_at').last() # TODO This breaks if there are no user Profiles, obviously
    return spotify_user

def authorise_spotify_user(client_id, spotify_user):
    """
    Accepts a UserProfile object and returns an authorised OAuth client.
    """
    token = deepcopy(spotify_user.__dict__) # TODO clearly this is ridiculous because I have to overwrite it later for an expired token
    del token['_state'], token['id'], token['user_id']
    client = OAuth2Session(client_id, token=token)
    return client

def refresh_spotify_user(client, client_id, client_secret, spotify_user, auth_url):
    # TODO fewer arguments...
    # TODO Option 3 https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
    extra = dict(client_id=client_id, client_secret=client_secret)
    token = client.refresh_token(auth_url, **extra)
    for key, value in token.items():
        setattr(spotify_user, key, value)
    spotify_user.save()
