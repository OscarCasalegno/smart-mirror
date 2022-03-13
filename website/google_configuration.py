
def get_maps_key():
    f = open("static/secret/google_key.txt", "r")
    my_key = f.read()
    f.close()
    print "Maps API key: {}".format(my_key)
    return my_key


def get_id_client_secret():
    f = open("static/secret/google_id.txt", "r")
    google_id_client = f.readline().strip()
    google_client_secret = f.readline().strip()
    f.close()
    print "ID Client: {}\nClient Secret: {}".format(google_id_client, google_client_secret)
    return google_id_client, google_client_secret


#get_id_client_secret()
#get_maps_key()
