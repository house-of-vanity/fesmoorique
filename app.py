#
# Copyright (c) 2019, UltraDesu <ultradesu@hexor.ru>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY UltraDesu <ultradesu@hexor.ru> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL UltraDesu <ultradesu@hexor.ru> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""API for hexound v2
.. moduleauthor:: AB <github.com/house-of-vanity>
"""

import json
import logging
import os
from functools import wraps
from flask import Response, render_template, request, Flask, send_file, jsonify, redirect, url_for, make_response
from flask_cors import CORS
from tools.database import DataBase
from tools.passwd import hash_password, verify_password, rand_hash
from sqlite3 import IntegrityError

HOME_DIR = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, static_folder=os.path.realpath("{}/mods".format(HOME_DIR)))

auth_cookies = dict()


def is_authorized(name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'auth' not in request.cookies:
                return redirect(url_for('login'))
            try:
                cookie = request.cookies['auth']
                user = auth_cookies[cookie]
            except:
                return redirect(url_for('login'))
            ret = f(*args, **kwargs)
            return ret
        return wrapped
    return decorator

@app.route("/", methods = ['POST', 'GET'])
@is_authorized('index')
def index():
    cookie = request.cookies['auth']
    user = auth_cookies[cookie]
    return render_template('index.html', user=user)

@app.route("/details_group/<group_id>")
@is_authorized('details_group')
def details_group(group_id):
    try:
        details = db.get_group(group_id)
    except:
        return Response('Ошибка')
    if len(details) == 0:
        return Response('Такой группы нет.')
    print(details)
    return render_template("details_group.html", details=details)

@app.route("/add_group", methods = ['POST', 'GET'])
@is_authorized('add_group')
def add_group():
    if request.method == 'POST':
        try:
            data = request.form
            group_id = data['group_id'].upper()
            members = data["members"].upper()
            members = members.split('\n')
            members = list(map(lambda z: z.rstrip(), members))
            print('Going to add %s' % len(members))
            print(members)
            db.add_group(group_id, members)
            resp = make_response(redirect(url_for('index')))
            return resp
        except:
            return Response('Все сломалось.')
    else:
        return render_template("add_group.html")

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.form
        try:
            name = data['username'].lower()
            pass_ = data['password']
            pass_hash = hash_password(pass_)
            stored_hash = db.login(name=name)
            if stored_hash:
                if verify_password(stored_hash, pass_):
                    cookie = rand_hash()
                    resp = make_response(redirect(url_for('index')))
                    resp.set_cookie('auth', cookie)
                    auth_cookies[cookie] = name
                    return resp
            else:
                return Response('Неверный пароль или имя пользователя. Try again baby.<br><a href="/login">Назад</a>')
        except IntegrityError as e:
            return jsonify(message="Username isn't available.", exception=e)
        except KeyError as e:
            return jsonify(message="Lack of parameters.", exception=e)
        return jsonify(message="User %s created." % name)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    if 'auth' in request.cookies:
        try:
            del(auth_cookies[request.cookies['auth']])
        except:
            pass
        return redirect(url_for('login'))

if __name__ == "__main__":
    db = DataBase(scheme=os.path.realpath("{}/data.sql".format(HOME_DIR)))
    CORS(app)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger('fesmoorique')
    app.run(host='0.0.0.0')