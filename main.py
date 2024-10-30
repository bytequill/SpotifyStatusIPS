try:
    from library.lcd.lcd_comm_rev_a import LcdCommRevA
    from library.lcd.lcd_comm_rev_b import LcdCommRevB
    from library.lcd.lcd_comm_rev_c import LcdCommRevC
    from library.lcd.lcd_comm_rev_d import LcdCommRevD
    from library.lcd.lcd_simulated import LcdSimulated
    from library.lcd.lcd_comm import LcdComm, Orientation
    from PIL import Image
    from time import sleep
    import spotipy
    from spotipy.oauth2 import SpotifyPKCE
    import datetime
    import threading
    import signal
    import io, os, os.path
    import urllib.request as urllib
    import dotenv
except ImportError as e:
    print(f"[error] Could not find one of the requested imports\nCheck the installation steps in README.md if you haven't already\n{e}")
    exit(1)

if os.path.exists(".env"):
    dotenv.load_dotenv()
elif os.path.exists(".env.example"):
    dotenv.load_dotenv(dotenv_path=".env.example")
else:
    print("[warn] No .env or .env.example file found. Make sure to pass in correct configuration in your environment")

try:
    try: # > If not set at all, defaults to AUTO
        COM_PORT = os.getenv("COM_PORT")
    except Exception:
        COM_PORT = "AUTO"
    revint = os.getenv("COM_REV")
    if revint.upper() == "A":
        COM_REV = LcdCommRevA
    elif revint.upper() == "B":
        COM_REV = LcdCommRevB
    elif revint.upper() == "C":
        COM_REV = LcdCommRevC
    elif revint.upper() == "D":
        COM_REV = LcdCommRevD
    elif revint.upper() == "S":
        COM_REV = LcdSimulated
    else:
        print("[error] Please specify a valid revision")
        exit(1)

    WIDTH, HEIGHT = int(os.getenv("DISPLAY_WIDTH")), int(os.getenv("DISPLAY_HEIGHT"))
    BRIGHTNESS = int(os.getenv("DISPLAY_BRIGHTNESS"))
    if BRIGHTNESS < 0 or BRIGHTNESS > 100:
        print("[error] Brightness is a percentage value (i.e 0-100)")
        exit(1)
    BGCOL = (int(os.getenv("BGCOL_R")), int(os.getenv("BGCOL_G")), int(os.getenv("BGCOL_B")))
    for col in BGCOL:
        if col < 0 or col > 255:
            print("[error] BGCOL values must be in range 0-255")
            exit(1)
    CHECK_EVERY = int(os.getenv("CHECK_EVERY"))
    if os.getenv("SPOTIPY_CLIENT_ID") == "ENTER_OWN_HERE":
        print("[error] You must create and specify a spotify client id. If not sure follow install steps in README.md")
        exit(1)
except KeyError or TypeError as e:
    print(f"[error] An error occured during setting of configuration\n{e}")
    exit(1)

## DO NOT TOUCH, NOT CONFIGURATION ##
GLOBAL_LOCK = threading.Lock()
OAUTH2_SCOPES = (
    'user-modify-playback-state', 
    'user-read-currently-playing', 
    'user-read-playback-state'
)
RUN = True
SP: spotipy.Spotify

class App:
    def __init__(self, comm: LcdComm) -> None:
        self.comm = comm
        self.sp: spotipy.Spotify = None
        self.lock = GLOBAL_LOCK
        
        self.isScreen = True
        self.isSong = False

        # Default values so the threading doesnt freak out
        self.time_total: datetime.time = seconds_to_time(1) # Using a 0 value results in a divide by zero error
        self.time_done: datetime.time = seconds_to_time(0)
        self.current_id = ""

    def ClearWithBG(self):
        bg = Image.new("RGB", (WIDTH, HEIGHT), BGCOL)
        self.lock.acquire()
        self.comm.DisplayPILImage(bg)
        self.lock.release()

    def _drawThumbnail(self, url: str):
        fd = urllib.urlopen(url)
        image_file = io.BytesIO(fd.read())
        a = Image.open(image_file)
        a.thumbnail((219,219))
        self.lock.acquire()
        self.comm.DisplayPILImage(a)
        self.lock.release()

    def _checkForNewSong(self):
        playback = SP.current_playback()
        #print(f"PLAYBACK IS: {playback}\n===============")
        try: 
            if playback["currently_playing_type"] != "track": 
                print(f"[WARN] This playback type has not been implemented: {playback['currently_playing_type']}");return
        except TypeError: pass
        def screenOFFProcedure(self: App):
            if self.isSong: self.isSong = False
            if self.isScreen:
                self.isScreen = False
            else:
                self.sp.me() # Tries to keep the auth working if idle for too long - Not tested yet
                return
            self.current_id = ""
            self.lock.acquire()
            self.comm.ScreenOff()
            self.lock.release()
            print("Turning screen OFF")
            self.ClearWithBG()
        try:
            if not playback["is_playing"] and self.isScreen:
                screenOFFProcedure(self)
        except TypeError: # Happens when it initialises without a song playing and after a while without playback
            screenOFFProcedure(self)
            return
        if playback["is_playing"]:
            if not self.isScreen: 
                self.lock.acquire()
                self.comm.ScreenOn()
                self.lock.release()
                self.isScreen = True
                print("Turning screen ON")
            if not self.isSong: self.isSong = True
            id = playback["item"]["id"]
            self.time_done = seconds_to_time(int(playback["progress_ms"]/1000))
            if id != self.current_id:
                self.current_id = id
                self.time_total = seconds_to_time(int(playback["item"]["duration_ms"]/1000))
                artists = ""
                for artist in playback["item"]["artists"]:
                    if len(artists) > 0: artists += ", "
                    artists += artist["name"]
                song_info = {
                    "name": playback["item"]["name"],
                    "artists": artists,
                    "cover": playback["item"]["album"]["images"][1]["url"]
                }
                self.drawNewSong(songinfo=song_info)

    def _secondIncrease(self):
        while RUN:
            sleep(1)
            self.time_done = (datetime.datetime.combine(datetime.date.today(), self.time_done) + datetime.timedelta(seconds=1)).time()

    def _updateSongBar(self):
        i = 0
        while RUN:
            if i % CHECK_EVERY == 0:
                threading.Thread(target=self._checkForNewSong).start() # Runs asynchronously to not disrupt the play bar with internet requests
            i += 1
            if self.isSong:
                self.lock.acquire()
                time = self.time_done.strftime("%M:%S")
                self.comm.DisplayText(time, x=2, y=248 + 20 + 20,
                                font="Roboto-Italic.ttf",
                                font_size=20,
                                font_color=(255, 255, 255),
                                background_color=BGCOL,
                                align='left')
                self.comm.DisplayProgressBar(x = 58, y = 248 + 20 + 20 + 3, height = 19, width = 360, max_value=time_to_seconds(self.time_total), value=time_to_seconds(self.time_done))
                #print(f"Max: {time_to_seconds(self.time_total)}; Val: {time_to_seconds(self.time_done)}")
                self.lock.release()
                sleep(0.25)
            else:
                sleep(0.5) # We dont want to take up too much resources

    def drawNewSong(self, songinfo: dict):
        clearBitmap = Image.new("RGB", (WIDTH, 50), BGCOL) # used to clear the area behind the text
        time = self.time_total.strftime("%M:%S")
        print(
f'''New song detected:
    TITLE = {songinfo["name"]}
    ARTISTS = {songinfo["artists"]}
    LENGHT = {time}
    COVER_URL = {songinfo["cover"]}''')
        self.lock.acquire()
        self.comm.DisplayPILImage(clearBitmap, y=222)
        self.comm.DisplayText(songinfo["name"], x=2, y=222,
                         font="Roboto-Italic.ttf",
                         font_size=24,
                         font_color=(255, 255, 255),
                         background_color=BGCOL,
                         align='left')
        self.comm.DisplayText(f"By {songinfo['artists']}", x=2, y=222 + 24 + 3,
                         font="Roboto-Italic.ttf",
                         font_size=20,
                         font_color=(255, 255, 255),
                         background_color=BGCOL,
                         align='left')
        self.comm.DisplayText(time, x=WIDTH-58, y=248 + 20 + 20,
                        font="Roboto-Italic.ttf",
                        font_size=20,
                        font_color=(255, 255, 255),
                        background_color=BGCOL,
                        align='right')
        self.lock.release()
        self._drawThumbnail(songinfo["cover"])

    def drawLoginPage(self):
        self.ClearWithBG()
        logo = Image.open("res/imgs/spoti-logo.png")
        logo.thumbnail((219,219))
        self.lock.acquire()
        self.comm.DisplayText("Please authorize this application to access your spotify data\nThere should be a new tab in your default browser", x=2, y=219+5,
                                font="Roboto-Italic.ttf",
                                font_size=18,
                                font_color=(255, 255, 255),
                                background_color=BGCOL,
                                align='left')
        self.comm.DisplayPILImage(logo)
        self.lock.release()

def seconds_to_time(seconds):
    # Use timedelta to handle the conversion from seconds
    td = datetime.timedelta(seconds=seconds)
    
    # Extract hours, minutes, and seconds from the timedelta object
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600) % 24  # Mod 24 to handle overflows
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    # Return a time object
    return datetime.time(hours, minutes, seconds)

def time_to_seconds(time_obj: datetime.time) -> int:
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

def HandleAuth() -> spotipy.Spotify:
    # BRUH, I implemented a whole flask web server and it just had this builtin
    sp = spotipy.Spotify(oauth_manager=SpotifyPKCE(scope=OAUTH2_SCOPES))
    oauth: SpotifyPKCE = sp.oauth_manager
    oauth.get_access_token()
    return sp

if __name__ == "__main__":
    def stopall(signum, frame):
        global RUN
        RUN = False
    signal.signal(signal.SIGTERM, stopall)
    signal.signal(signal.SIGINT, stopall)
    
    if type(COM_REV) == LcdCommRevA:
        lcd_comm = COM_REV(com_port=COM_PORT, display_width=WIDTH, display_height=HEIGHT)
    else:
        lcd_comm = COM_REV(com_port=COM_PORT, display_width=HEIGHT, display_height=WIDTH)
    lcd_comm.Reset()
    lcd_comm.InitializeComm()
    lcd_comm.SetBrightness(level=BRIGHTNESS)

    #lcd_comm.Clear() # This is not actually needed since we restart and use ClearWithBG. Just takes up time on init
    lcd_comm.SetOrientation(orientation=Orientation.LANDSCAPE)

    app = App(lcd_comm)

    app.ClearWithBG()
    lcd_comm.ScreenOn()
    app.drawLoginPage()
    SP = HandleAuth()
    app.sp = SP
    app.ClearWithBG()
    threading.Thread(target=app._updateSongBar, daemon=True).start()
    threading.Thread(target=app._secondIncrease).start() # keeping up with progress between API updates
    while RUN:
        pass

    lcd_comm.closeSerial()