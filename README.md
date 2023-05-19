# strava-visualizer

Retrieve activity data from Strava!

## Installation

```shell
pip install -e .
```

## Authentication to Strava API

1. A `credentials.toml` file that contains your Strava API client ID/secret as well as authorization code if running for the first time:

```toml
[strava]
client_id = "{YOUR_CLIENT_ID}"
client_secret = "{YOUR_CLIENT_SECRET}"
code = "{YOUR_AUTH_CODE}"
```

2. A `tokens.json` file with the following:

```json
{
    "access_token": "{YOUR_ACCESS_TOKEN}",
    "expires_at": "EXPIRES_AT",
    "expires_in": "EXPIRES_IN",
    "refresh_token": "{YOUR_REFRESH_TOKEN}",
    "token_type": "Bearer"
}
```

The script will use the tokens in `tokens.json` to auth or re-authenticate itself if the access token has expired.

## Shell Args

```shell
❯ python3 main.py -h
usage: strava-visualizer [-h] [-c CREDS] [-t {Walk,Run,All}] [-m {0,1}] [-o OUTPUT] [-f {json,image}] [-ma MAX_ACTIVITIES]

Get last activities from strava and make a cool image!

options:
  -h, --help            show this help message and exit
  -c CREDS, --creds CREDS
  -t {Walk,Run,All}, --type {Walk,Run,All}
                        type of activity to filter for
  -m {0,1}, --map {0,1}
                        include map key in output JSON
  -o OUTPUT, --output OUTPUT
                        handle to output file to write JSON to
  -f {json,image}, --file_type {json,image}
  -ma MAX_ACTIVITIES, --max_activities MAX_ACTIVITIES
```