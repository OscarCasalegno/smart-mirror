import googlemaps


def get_g_key():

    path = __file__ + ""
    temp = path.split("\\")
    uri_file = ""
    for direct in temp:
        uri_file = uri_file + direct + "\\"
        if direct == "website":
            break
    uri_file = uri_file + "static\\secret\\google_key.txt"

    f = open(uri_file, "r")
    my_key = f.read()
    f.close()
    print my_key
    return my_key


def get_client():
    my_key = get_g_key()
    gmaps = googlemaps.Client(key=my_key)
    return gmaps


def get_address(raw_address):
    gmaps = get_client()
    response = gmaps.places_autocomplete_query(raw_address, language="en")
    try:
        address = response[0]["description"]+""
    except:
        address = ""
    return address

