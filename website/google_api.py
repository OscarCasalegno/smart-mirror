import googlemaps
import pandas as pd
import json
import geocoder


def run():
    print "Ciao"

    f = open("./static/secret/google_key.txt", "r")
    my_key = f.read()
    f.close()
    print my_key

    f = open("./static/secret/google_id.txt", "r")
    id = f.readline().strip()
    secret = f.readline().strip()
    f.close()

    #print "ID Client: {}\nClient Secret: {}".format(id, secret)

    #"""print "    \n\nciao amico\ncome va".strip()
    #print "\n    \nciao amico\ncome va".strip("\n")"""
    #print type(my_key)
    # gmaps.directions("Sydney Town Hall", "Parramatta, NSW", mode="transit", departure_time=now)

    gmaps = googlemaps.Client(key=my_key)
    #response = gmaps.distance_matrix(origins="albergo gli scoiattoli ceresole reale", destinations="Politecnico di Torino", mode="driving", language="it")
    #print json.dumps(response)

    response = gmaps.places_autocomplete_query("corso Vinzaglio 3 Torino", language="en")
    #print response
    #print type(json.dumps(response))
    print json.dumps(response)
    print response[0]["description"]

    #raw_response = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
    #raw_response = gmaps.geocode("corso Vinzaglio 3 Torino")
    #print json.dumps(raw_response)
    #print raw_response[0]["formatted_address"]



    """
    #print type(raw_response) #list

    #r_json = json.loads(raw_response)
    #print(r_json)
    #dataframe = pd.DataFrame.from_dict(r_json, orient="index")
    #print(dataframe)
    
    n = 0
    for elem in raw_response:
        print "{}: \n".format(n)
        print elem
        print type(elem)
        n += 1


    response = pd.DataFrame(raw_response)
    print "Final\n"
    print response.to_string()

    dataframe = pd.DataFrame.from_dict(raw_response[0], orient="index")
    print dataframe
    """

def ciao():
    g = geocoder.ip('me')
    print(g.latlng)
    print g.city
    print g.state + " "
    print g.country + " "

if __name__ == '__main__':
    #ciao()
    run()

