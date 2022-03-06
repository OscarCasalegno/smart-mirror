from flask_mail import Message
from website import mail, path_getter


def get_content():

    uri_html = path_getter("templates\\mail.html")
    uri_logo = path_getter("static\\logo.png")

    fc = open(uri_html, "r")
    cont = fc.read()
    fc.close()

    fl = open(uri_logo, 'rb')
    img = fl.read()
    fl.close()

    return cont, img


def send_registration_mail(recipient, title, name):
    cont, img = get_content()

    recipients = ["debeluca98@gmail.com"]
    recipients.append(recipient)
    msg = Message(title, sender='cleveror.it@gmail.com', recipients=recipients)
    msg.body = title    #"Welcome in Cleveror"

    msg.attach(filename='logo.png', content_type='image/png', data=img, disposition='inline',
           headers=[("Content-ID", "<inline_logo>")])

    cont = cont.replace("XXX_LINK_XXX", "https://127.0.0.1:5000/")
    msg.html = cont.replace("XXX_NAME_XXX", name)
    mail.send(msg)

