![Demonstration](demonstration.png)  
Spotify display for screens compatible with https://github.com/mathoudebine/turing-smart-screen-python/

# Instalation guide
1. Setup a python virtual environment  
    - If you dont't have python installed or want an easy setup:
        1. Right click the `nopython-makeenv.ps1` and click `run with powershell`  
    - If You want to do it manually and have python installed:  
        1. Run `python -m venv {env_name}`. The name `pythonportable` lets you take advantage of `nopython-run.bat`
        2. Activate the environment:
            - Unix/macOS  
            `source {env_name}/bin/activate`
            - Windows  
            `{env_name}\Scripts\activate`
        3. Install required packages  
        `pip install -r requirements.txt`
2. Create a spotify API application
    1. Goto `https://developer.spotify.com/dashboard/create` in your browser of choice
    2. Fill in `App name` and `App description` in any way you like
    3. For `Redirect URIs` enter whatever is set as `SPOTIPY_REDIRECT_URI` in your `.env` or `.env.example` file (default is `http://localhost:9099/getToken`)
    4. You also need to mark `Web API` in the next section
    5. Click `Save` to create your app
    6. In the apps section click the `Settings` button
    7. Copy the `Client ID` to your clipboard or note it down somewhere
    8. Go into your `.env` or `.env.example` file and paste the `Client ID` into the `SPOTIPY_CLIENT_ID` field
3. Final configuration steps
    1. Ensure your screen of choice is set as the `COM_REV` in your `.env` or `.env.example`
4. Run the program
    - If you used the powershell script to set up python:
        - Run the `nopython-run.bat` file
    - If you created the environment manually:
        - Run `main.py` within the environment
- If there are any bugs or otherwhise problems with any of the displays, please create a [Issue](https://ben.balter.com/2023/03/02/github-for-non-technical-roles/#issues) or contact me with a discord dm (my username is `codebased`)
    - Due to how the code works, it is especially important to look for mis-orientation issues. Those can be resolved within seconds but I just dont have all the supported displays to try them
    - Note that due to the way the displays work they take their time to do any action and paint pretty slow. This is NOT a software issue and is just the nature of the hardware