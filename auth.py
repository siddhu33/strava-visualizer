import json
import sys
import time

import requests
import tomllib

STRAVA_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
TOKENS_PATH = "tokens.json"


def load_credentials(creds: str) -> dict:
    with open(creds, "rb") as in_file:
        return tomllib.load(in_file)


def get_access_token(creds_data: dict):
    headers = {"Content-Type": "application/json"}
    body = dict(grant_type="authorization_code", **creds_data["strava"])
    res = requests.post(STRAVA_TOKEN_URL, json=body, headers=headers)
    res.raise_for_status()
    return res.json()


def refresh_access_token(creds_data: dict, refresh_token: str) -> dict:
    strava_data = creds_data["strava"]
    res = requests.post(
        STRAVA_TOKEN_URL,
        json={
            "client_id": strava_data["client_id"],
            "client_secret": strava_data["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    res.raise_for_status()
    new_token_data = res.json()
    with open(TOKENS_PATH, "w") as out_file:
        json.dump(new_token_data, out_file, sort_keys=True)
    return new_token_data


def check_refresh_token(creds_data: dict, token_data: dict) -> dict:
    if time.time() > token_data["expires_at"]:
        print("Token expired! Using refresh token to get new one!", file=sys.stderr)
        return refresh_access_token(creds_data, token_data["refresh_token"])
    else:
        print("Token is still valid, so using this one!", file=sys.stderr)
        return token_data


def get_strava_token(args):
    creds_data = load_credentials(args.creds)
    try:
        with open(TOKENS_PATH, "r") as token_file:
            token_data = json.load(token_file)
    except OSError:
        token_data = get_access_token(creds_data=creds_data)
        with open(TOKENS_PATH, "w") as out_file:
            json.dump(token_data, out_file, sort_keys=True)

    token_data = check_refresh_token(creds_data, token_data)
    return token_data
