import time
import flask
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import multiprocessing
import os
import webbrowser

# If you want you can replace this with your own key
# This key is in development mode, so you might need to add your own
SPOTIPY_CLIENT_ID = '67027e84d73c49aca8f3f03fe3c8c441'
SPOTIPY_CLIENT_SECRET = '133be535ea0b468db46122056dd23ba4'
REDIRECT_URI = 'http://localhost:9099/getToken'
OAUTH2_SCOPES = (
    'user-modify-playback-state', 
    'user-read-currently-playing', 
    'user-read-playback-state'
)

APP = flask.Flask(__name__)

SPOTIPY_OAUTH = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=" ".join(OAUTH2_SCOPES)
)

def run_flask_app(queue):
    @APP.route('/getToken')
    def spotify_callback():
        try:
            code = flask.request.args.get('code')
            if not code:
                return flask.redirect('/failed')
            
            token_info = SPOTIPY_OAUTH.get_access_token(code)
            OUTPUT_API = spotipy.Spotify(auth=token_info['access_token'])
            
            # Put the OUTPUT_API in the queue
            queue.put(OUTPUT_API)
            
            return "You can now safely close this tab"
        
        except Exception as e:
            print(f"Error during Spotify authentication: {e}")
            return flask.redirect('/failed')

    @APP.route('/failed')
    def spotify_failed():
        return 'Failed to authenticate with Spotify.'

    @APP.route('/')
    @APP.route('/index')
    def index():
        auth_url = SPOTIPY_OAUTH.get_authorize_url()
        return flask.redirect(auth_url)
    browserProc = multiprocessing.Process(target=webbrowser.open_new_tab, args=("http://localhost:9099/",))
    browserProc.start()
    APP.run('127.0.0.1', port=9099, debug=False)

def HandleAuth() -> spotipy.Spotify:
    queue = multiprocessing.Queue()
    serverProc = multiprocessing.Process(target=run_flask_app, args=(queue,))
    serverProc.start()
    
    # Wait for the OUTPUT_API to be put in the queue
    OUTPUT_API = queue.get()
    time.sleep(1) # Give some time so the browser can get the success page
    # Forcefully kill the server process
    serverProc.kill()
    serverProc.join()
    os.system("cls")
    print("Returning back with the api :)")
    return OUTPUT_API
