# coding=utf-8
import sys

from flask import Flask, render_template, request, redirect, Response
import random, json

app = Flask(__name__)

@app.route('/logindata', methods = ['POST'])
def worker():
    data = request.get_json()
    result = ''

    for item in data:
        # loop over every row
        result += str(item['make']) + '\n'

    return result

if __name__ == '__main__':
    app.run()
