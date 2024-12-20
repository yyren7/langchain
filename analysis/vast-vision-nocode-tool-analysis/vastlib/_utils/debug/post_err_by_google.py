# ===============================================================================
# Name      : post_err_by_google.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2021-12-23 15:09
# Copyirght 2021 Hiroya Aoyama [aoyama.hiroya@nidec.com]
# ===============================================================================

import requests
import time
import json


class Request2GoogleChat():
    def __init__(self):
        # self.url = "https://chat.googleapis.com/v1/spaces/AAAA5hMEFpA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=QGpiMZaRnB1q0r4ijclX5ckihn1m_baHN6jx0k52Ijs%3D"
        self.url = 'https://chat.googleapis.com/v1/spaces/AAAA5hMEFpA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=QGpiMZaRnB1q0r4ijclX5ckihn1m_baHN6jx0k52Ijs%3D'

        self.headers = {"Content-Type": "application/json"}

    def post_data(self, obj: dict = None, text: str = ''):
        if obj is None:
            obj = {'text': text}
        response = requests.post(self.url, data=json.dumps(obj), headers=self.headers)
        return response.text


class Request2GoogleForm():
    def __init__(self):
        self.url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSfH8qtSLRtbKQ6vGW5U3amFkAXxGjI393-5yC_LNWAuRLj13A/formResponse"

    def post_form(self):
        params = {
            'entry.815011211': 3,
            'entry.1750047047': 5,
        }
        r = requests.get(self.url, params=params)
        print(r.url)
        print(r.status_code)


class Request2GoogleSpreadSheet():
    def get_item(self):
        obj = {'key': 'header'}
        response = requests.get(self.url, params=obj, headers=self.headers)
        item_lst = response.json()[0]
        return item_lst

    def __init__(self, url=None, header=None):
        if url is not None:
            self.url = url
        else:
            self.url = "https://script.google.com/macros/s/AKfycbzUEe8lU-Mr6-y0MZD83fCHIGs9ufUG5NJI4R8XZIgZWerzex_yinmD7wXbO7SgasIGxw/exec"

        if header is not None:
            self.header = header
        else:
            self.headers = {"Content-Type": "application/json"}

        self.items = self.get_item()
        print("items:{}".format(self.items))

    def post_data(self, obj={}):
        response = requests.post(self.url, data=json.dumps(obj), headers=self.headers)
        return response.text

    def get_data(self, obj={}):
        response = requests.get(self.url, params=obj, headers=self.headers)
        return response.json()


if __name__ == '__main__':

    req_gc = Request2GoogleChat()
    req_gc.post_data(text='5mi')
