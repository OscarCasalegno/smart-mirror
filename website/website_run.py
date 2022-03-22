from website import app

#Checks if the website_run.py file has executed directly and not imported
if __name__ == '__main__':
    app.run(ssl_context='adhoc', debug=True) #debug=True
    # https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
