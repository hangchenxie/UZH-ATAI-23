from speakeasypy import Speakeasy
class Credentials:

    def __init__(self):
        self.url = "https://speakeasy.ifi.uzh.ch"
        self.username = 'torch-staccato-mushroom_bot'
        self.password = 'ofmkiY2qPQeiRg'

    def login(self):
        self.s = Speakeasy(self.url, self.username, self.password)
        self.s.login()

    def check_rooms(self):
        self.s.get_rooms(active=True)

