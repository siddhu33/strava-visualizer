import argparse
import json
import sys
import time

import requests
import tomllib
from PIL import Image, ImageDraw, ImageFont

STRAVA_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
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


def get_activities(token_data: dict) -> list[dict]:
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res = requests.get(ACTIVITIES_URL, headers=headers)
    res.raise_for_status()
    return res.json()


def check_refresh_token(creds_data: dict, token_data: dict) -> dict:
    if time.time() > token_data["expires_at"]:
        print("Token expired! Using refresh token to get new one!", file=sys.stderr)
        return refresh_access_token(creds_data, token_data["refresh_token"])
    else:
        print("Token is still valid, so using this one!", file=sys.stderr)
        return token_data


def image_from_activity_data(
    activity_data: list[dict], max_activities: int, result_file
) -> None:
    """create an image from the activity data and then write it out to an image"""
    shape = (800, 480)
    w, h = shape
    image = Image.new("RGB", shape, color=(45, 27, 89))
    activities = activity_data[:max_activities]
    box_shape = w, (h / len(activities))
    context = ImageDraw.Draw(image)
    font = ImageFont.truetype("MesloLGS NF Regular.ttf", size=18)
    for idx, act in enumerate(activities):
        context.rectangle((0, idx * box_shape[1], w, idx * box_shape[1]))
        context.text(
            (10, idx * box_shape[1]),
            f"{idx+1}: {act['name']}: {act['start_date_local']} -> {act['elapsed_time']} seconds",
            font=font,
            fill=(255, 255, 0, 255),
        )
        context.text(
            (10, 20 + idx * box_shape[1]),
            f"Distance: {act['distance']}m, Heart Rate: {act['average_heartrate']}",
            font=font,
        )

    image.save(result_file, format="jpeg")


def main():
    parser = argparse.ArgumentParser(
        "strava-visualizer",
        description="Get last activities from strava and make a cool image!",
    )
    parser.add_argument("-c", "--creds", required=False, default="credentials.toml")
    parser.add_argument(
        "-t",
        "--type",
        required=False,
        default="All",
        help="type of activity to filter for",
        choices=["Walk", "Run", "All"],
    )
    parser.add_argument(
        "-m",
        "--map",
        required=False,
        default=1,
        type=int,
        help="include map key in output JSON",
        choices=[0, 1],
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        default="",
        help="handle to output file to write JSON to",
    )
    parser.add_argument(
        "-f", "--file_type", required=False, default="json", choices=["json", "image"]
    )
    parser.add_argument("-ma", "--max_activities", required=False, default=5, type=int)

    args = parser.parse_args()
    creds_data = load_credentials(args.creds)
    try:
        with open(TOKENS_PATH, "r") as token_file:
            token_data = json.load(token_file)
    except OSError:
        token_data = get_access_token(creds_data=creds_data)
        with open(TOKENS_PATH, "w") as out_file:
            json.dump(token_data, out_file, sort_keys=True)

    token_data = check_refresh_token(creds_data, token_data)

    activity_data = get_activities(token_data)

    if args.type != "All":
        activity_data = (a for a in activity_data if a["type"] == args.type)

    if args.map == 0:
        activity_data = (
            {k: v for k, v in a.items() if k != "map"} for a in activity_data
        )

    if args.output:
        result_file = open(args.output, "w")
    else:
        result_file = sys.stdout

    activity_data = list(activity_data)

    match args.file_type:
        case "json":
            print(json.dumps(activity_data, sort_keys=True), file=result_file)
        case "image":
            image_from_activity_data(activity_data, args.max_activities, result_file)


if __name__ == "__main__":
    main()
