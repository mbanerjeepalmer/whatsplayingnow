import traceback
from .models import UserProfile

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
    Accepts a User object and returns all the spotu
    """
    acct_dict = {}
    acct_queryset = UserProfile.objects.filter(user=user).exclude(spotify_id__isnull=True)
    for acct in acct_queryset:
        setattr(acct_dict, acct.spotify_id, acct.spotify_name)
    return acct_queryset
