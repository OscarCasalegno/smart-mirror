# -*- coding: UTF-8 -*-
import io

from FacesClass import path_getter
import api
from dateutil.parser import parse
from datetime import date


def widget_html_handler(widget, user, mirror):
    if widget == "NONE":
        return ""
    elif widget == "CLOCK":
        return clock_html_handler()
    elif widget == "CLOCK & DATE":
        return clock_date_html_handler()
    elif widget == "WEATHER":
        return weather_html_handler(mirror)
    elif widget == "CALENDAR":
        return calendar_html_handler()
    elif widget == "AGENDA":
        return agenda_html_handler(user, mirror)
    elif widget == "FINANCE":
        return finance_html_handler()
    else:
        return ""


def clock_html_handler():
    path_widget = path_getter("\\mirror\\templates\\widget\\clock.html")
    try:
        f = open(path_widget, "r")
        html = f.read()
        f.close()
        # print html
        return html
    except:
        return "Clock unavailable"


def weather_html_handler(mirror):
    if not mirror.location:
        return "To see the weather, set the location of the mirror!"

    try:
        location = api.get_geocode(address=mirror.location)
        lat = location[0]["geometry"]["location"]["lat"]
        lng = location[0]["geometry"]["location"]["lng"]
        city = ""
        for detail in location[0]["address_components"]:
            if city:
                break
            for type in detail["types"]:
                if city:
                    break
                if type == "administrative_area_level_3":
                    city = detail["short_name"]
        #city = location[0]["address_components"][3]["short_name"]
    except:
        return "Weather unavailable"

    path_widget = path_getter("\\mirror\\templates\\widget\\weather.html")
    try:
        f = open(path_widget, "r")
        html = f.read()
        f.close()
        html = html.replace("XXX_LABEL_XXX/XXX_LAT_XXX_XXX_LONG_XXX", "{city}/{lat}_{lng}".format(city=city, lat=lat, lng=lng))
        return html
    except:
        return "Weather unavailable"


def agenda_html_handler(user, mirror):
    path_widget = path_getter("\\mirror\\templates\\widget\\agenda.html")
    try:
        f = io.open(path_widget, mode="r", encoding="utf-8")
        html = f.read()
        f.close()

        today = date.today()
        text_today = today.strftime("%A %d %B, %Y")
        html = html.replace("XXX_TODAY_XXX", text_today)

        event_structure = u'<li ><div class="event"><div class="hour">{start_m}-{end_m}</div><div class="description">{name}</div><div class="travel">🚗{duration}</div></div></li>'

        events = api.get_google_events(user)
        if events is None:
            html = html.replace("XXX_EVENTS_XXX", "To use the Agenda widget, link your account to Google")
            return html

        html_events = ""
        for event in events["items"]:
            name = event["summary"]
            try:
                location = event["location"]
            except:
                location = ""
            start = parse(event["start"]["dateTime"])
            end = parse(event["end"]["dateTime"])

            if location != "" and mirror.location:
                by = "driving"
                path = api.get_distance(mirror.location, location, by)
                duration = path["rows"][0]["elements"][0]["duration"]["value"]
                duration = api.format_duration(seconds=duration)
                distance = path["rows"][0]["elements"][0]["distance"]["text"]
            else:
                duration = "-"

            start_m = str(start.time())[0:5]
            end_m = str(end.time())[0:5]

            html_events += event_structure.format(start_m=start_m, end_m=end_m, name=name, duration=duration)

        html = html.replace("XXX_EVENTS_XXX", html_events)
        return html

    except:
        return "Agenda unavailable"


def calendar_html_handler():
    path_widget = path_getter("\\mirror\\templates\\widget\\calendar.html")
    try:
        f = open(path_widget, "r")
        html = f.read()
        f.close()
        # print html
        return html
    except:
        return "Calendar unavailable"


def clock_date_html_handler():
    path_widget = path_getter("\\mirror\\templates\\widget\\clock_date.html")
    try:
        f = open(path_widget, "r")
        html = f.read()
        f.close()
        # print html
        return html
    except:
        return "Clock and date unavailable"


def finance_html_handler():
    path_widget = path_getter("\\mirror\\templates\\widget\\finance.html")
    try:
        f = open(path_widget, "r")
        html = f.read()
        f.close()
        # print html
        return html
    except:
        return "Finance information unavailable"
