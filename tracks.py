def tracks():
    try:
        on_the_decks = UserProfile.objects.order_by('expires_at').last()
        token = on_the_decks.__dict__ # TODO clearly this is ridiculous
        del token['_state'], token['id'], token['user_id']
        client = OAuth2Session(client_id, token=token)
    except TokenExpiredError:
        # TODO Do 3 https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#refreshing-tokens
        extra = dict(client_id=client_id, client_secret=client_secret)
        token = client.refresh_token(token_url, **extra)
        print(token)
        UserProfile.objects.update_or_create(defaults=token, user=on_the_decks)
    try:
        on_the_decks = UserProfile.objects.order_by('expires_at').last()
        token = on_the_decks.__dict__
        del token['_state'], token['id'], token['user_id']
        print(token)
        client = OAuth2Session(client_id, token=token)
        resp = client.get('https://api.spotify.com/v1/me/player/recently-played')
        tracks_details = recently_played_tracks(resp)
        print(tracks_details)
    except Exception as general_error:
        error_message = str(general_error) + traceback.format_exc()
        print(error_message)
    else:
        print(r"No idea what's happened here  ¯\_(ツ)_/¯")
