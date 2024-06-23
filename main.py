import argparse
import json
import sys
from datetime import datetime, timedelta

import matplotlib
from humanize import precisedelta

import matplotlib.pyplot as plt
import requests
from PIL import Image, ImageDraw, ImageFont, ImageColor

from src.auth import get_strava_token

matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = ["Futura"]

ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


def get_activities(token_data: dict) -> list[dict]:
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res = requests.get(ACTIVITIES_URL, headers=headers)
    res.raise_for_status()
    return res.json()


def heart_rate_chart(
    activity_data: list[dict], chart_shape: tuple[int, int], colors: tuple[str, str]
):
    partition = 5500
    dates_small, rates_small = [], []
    dates_large, rates_large = [], []
    for a in activity_data:
        act_date = datetime.fromisoformat(a["start_date"])
        act_value = a["average_heartrate"]
        if a["distance"] > partition:
            dates_large.append(act_date)
            rates_large.append(act_value)
        else:
            dates_small.append(act_date)
            rates_small.append(act_value)
    w, h = chart_shape
    fig = plt.figure(figsize=(w / 100.0, h / 100.0), dpi=100.0)
    ax = fig.subplots(1, 1)
    ax.set_title("Average Heart Rate", fontdict={"color": colors[1]})
    plot_chart_data(dates_small, rates_small, fig, ax, colors, f"HR<={partition}m")
    ax.plot(
        dates_large,
        rates_large,
        color=colors[1],
        linestyle="dashed",
        label=f"HR>{partition}m",
    )
    return _figure_to_image(fig, colors[1])


def _figure_to_image(fig, text_color):
    with plt.rc_context({"text.color": text_color}):
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.canvas.draw()
    return Image.frombytes(
        "RGBA", fig.canvas.get_width_height(), fig.canvas.renderer.buffer_rgba()
    )


def plot_chart_data(x, y, fig, ax, colors, label):
    primary, secondary = colors
    fig.set_facecolor(primary)
    ax.set_facecolor(primary)
    ax.xaxis.label.set_color(secondary)
    ax.yaxis.label.set_color(secondary)
    ax.tick_params(colors=secondary, which="both")
    ax.plot(x, y, color=secondary, label=label)


def pace_chart(
    activity_data: list[dict], chart_shape: tuple[int, int], colors: tuple[str, str]
):
    partition = 5500
    dates_small, paces_small = [], []
    dates_large, paces_large = [], []
    for a in activity_data:
        act_date = datetime.fromisoformat(a["start_date"])
        act_value = a["average_speed"] * 3.6
        if a["distance"] > partition:
            dates_large.append(act_date)
            paces_large.append(act_value)
        else:
            dates_small.append(act_date)
            paces_small.append(act_value)
    w, h = chart_shape
    fig = plt.figure(figsize=(w / 100.0, h / 100.0), dpi=100.0)
    ax = fig.subplots(1, 1)
    plot_chart_data(
        dates_small, paces_small, fig, ax, colors, f"pace under {partition}m"
    )
    ax.set_title("Running Pace", fontdict={"color": colors[1]})
    ax.plot(
        dates_large,
        paces_large,
        color=colors[1],
        linestyle="dashed",
        label=f"pace over {partition}m",
    )
    return _figure_to_image(fig, colors[1])


def metres_per_beat_chart(
    activity_data: list[dict], chart_shape: tuple[int, int], colors: tuple[str, str]
):
    dates, pace_ratios = [], []
    for a in activity_data:
        act_date = datetime.fromisoformat(a["start_date"])
        act_value = (a["average_speed"] * 60) / a["average_heartrate"]
        dates.append(act_date)
        pace_ratios.append(act_value)
    w, h = chart_shape
    fig = plt.figure(figsize=(w / 100.0, h / 100.0), dpi=100.0)
    ax = fig.subplots(1, 1)
    plot_chart_data(dates, pace_ratios, fig, ax, colors, f"pace ratio")
    ax.set_title("Metres per heartbeat", fontdict={"color": colors[1]})
    return _figure_to_image(fig, colors[1])


def _elapsed_str(num_seconds: int):
    return precisedelta(timedelta(seconds=num_seconds))


def auto_text_color(primary):
    r, g, b = ImageColor.getrgb(primary)
    a = 1 - (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if (a < 0.5) else "#ffffff"


def select_random_color_palette():
    import colorsys
    import random

    def to_8_bit(c):
        return int(255 * c)

    hue = random.randint(1, 12) / 12.0
    complementary_hue = (hue + 0.5) % 1
    p_red, p_green, p_blue = [to_8_bit(c) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
    s_red, s_green, s_blue = [
        to_8_bit(c) for c in colorsys.hsv_to_rgb(complementary_hue, 1.0, 1.0)
    ]
    primary_rgb_str = f"#{p_red:02x}{p_green:02x}{p_blue:02x}"
    secondary_rgb_str = f"#{s_red:02x}{s_green:02x}{s_blue:02x}"
    return primary_rgb_str, secondary_rgb_str


def image_from_activity_data(
    activity_data: list[dict],
    max_activities: int,
    result_file,
    shape: tuple[int, int],
    colors: tuple[str, str],
) -> None:
    """create an image from the activity data and then write it out to an image"""
    primary, secondary = colors
    w, h = shape
    image = Image.new("RGB", shape, color=primary)
    activities = activity_data[:max_activities]
    box_shape = w / 2, (h / len(activities))
    context = ImageDraw.Draw(image)
    heading = ImageFont.truetype("Futura", size=18)
    subheading = ImageFont.truetype("Futura", size=16)
    content = ImageFont.truetype("Futura", size=14)
    text_color = auto_text_color(primary=primary)
    for idx, act in enumerate(activities):
        context.rectangle(
            (0, idx * box_shape[1], w / 2, idx * box_shape[1]), outline=primary
        )
        run_date_str = datetime.fromisoformat(act["start_date_local"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        pace_str = f"{act['average_speed']*3.6:.2f}km/h"
        context.text(
            (10, idx * box_shape[1]),
            f"{act['name']}: {run_date_str}",
            font=heading,
            fill=secondary,
        )
        context.text(
            (10, 20 + idx * box_shape[1]),
            f"Elapsed Time: {_elapsed_str(act['elapsed_time'])}",
            font=subheading,
            fill=text_color,
        )
        context.text(
            (10, 40 + idx * box_shape[1]),
            f"Distance: {act['distance']}m, Heart Rate: {act['average_heartrate']}, Pace: {pace_str}",
            font=content,
            fill=text_color,
        )
    num_charts = 3
    chart_shape = (w / 2, h / num_charts)
    chart_data = []  # two charts, heart rate and distance
    chart_data.append(heart_rate_chart(activity_data, chart_shape, colors))
    chart_data.append(pace_chart(activity_data, chart_shape, colors))
    chart_data.append(metres_per_beat_chart(activity_data, chart_shape, colors))
    for idx in range(num_charts):
        context.rectangle(
            (w / 2, idx * (h / num_charts), w, idx * (h / num_charts)), outline="red"
        )
        box = (w / 2, idx * chart_shape[1])
        box = [int(i) for i in box]
        image.paste(chart_data[idx], box=box)

    image.save(result_file, format="jpeg")


def get_activity_data(args, token_data):
    activity_data = get_activities(token_data)

    if args.type != "All":
        activity_data = (a for a in activity_data if a["type"] == args.type)

    if args.map == 0:
        activity_data = (
            {k: v for k, v in a.items() if k != "map"} for a in activity_data
        )

    activity_data = list(activity_data)
    return activity_data


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
        help="handle to output file to write JSON or image to",
    )
    parser.add_argument(
        "-iw",
        "--width",
        required=False,
        type=int,
        default=800,
        help="If writing image, the width of the image being written",
    )
    parser.add_argument(
        "-ih",
        "--height",
        required=False,
        type=int,
        default=480,
        help="If writing image, the width of the image being written",
    )
    parser.add_argument(
        "-f", "--file_type", required=False, default="json", choices=["json", "image"]
    )
    parser.add_argument("-ma", "--max_activities", required=False, default=5, type=int)
    parser.add_argument("-p", "--primary-color", required=False, default=None)
    parser.add_argument("-s", "--secondary-color", required=False, default=None)
    args = parser.parse_args()
    if args.output:
        result_file = open(args.output, "w")
    else:
        result_file = sys.stdout

    if not args.primary_color and not args.secondary_color:
        colors = select_random_color_palette()
    else:
        colors = (args.primary_color, args.secondary_color)
    token_data = get_strava_token(args)
    activity_data = get_activity_data(args, token_data)
    match args.file_type:
        case "json":
            json.dump(activity_data, file=result_file, sort_keys=True)
        case "image":
            image_from_activity_data(
                activity_data,
                args.max_activities,
                result_file,
                (args.width, args.height),
                colors,
            )


if __name__ == "__main__":
    main()
