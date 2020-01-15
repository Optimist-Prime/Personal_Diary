from datetime import datetime
from addeventform import EventForm
from db import DB, UsersModel, EventModel
from flask import Flask, session, redirect, flash, render_template, url_for, request
from loginform import LoginForm
from registerform import RegisterForm
from PIL import Image
import webbrowser
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
edit = None
db = DB()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    login_error = ''
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        user = users.exists(form.username.data, form.password.data)
        if user[0]:
            session['userid'] = users.get(user[1])[0]
            session['username'] = users.get(user[1])[1]
            session['admin'] = users.get(user[1])[3]
            session['sort'] = 0
            return redirect('/')
        else:
            login_error = 'Incorrect login or password!'
    return render_template('login.html', title='Login Form', brand="Diary", form=form, login_error=login_error)


@app.route('/')
def index():
    if "username" not in session:
        return redirect('/login')
    Event = EventModel(db.get_connection())
    all_Event = []
    for i in Event.get_all(session['userid'], session['sort']):
        all_Event.append({'pic': Image.open("static/img/" + i[5]) if i[5] != "0" else i[5], 'pub_date': datetime.fromtimestamp(i[4]).strftime('%d.%m.%Y %H:%M'),
                        'content': i[2], 'title': i[1], 'nid': i[0]})
    return render_template('index.html', title='Personal Diary', Event=all_Event, Image=Image, os=os)


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if "username" not in session:
        return redirect('/login')
    Event = EventModel(db.get_connection())

    global edit
    if not edit:
        form = EventForm()
    else:
        form = EventForm(Event.get(edit))

    if form.validate_on_submit():
        Event.insert(form.title.data if form.title.data != '' else Event.get(edit)[1] if edit else "",
                    form.content.data if form.content.data != '' else Event.get(edit)[2] if edit else "",
                    session['userid'],
                    form.picture.data.filename if form.picture.has_file() else "0" if not edit else Event.get(edit)[5],
                    edit)

        print(form.picture.data.filename) if form.picture.has_file() else print("0")

        if form.picture.has_file():
            with open('static/img/' + form.picture.data.filename, "wb") as image:
                image.write(form.picture.data.read())

        if edit:
            delete(edit)
            edit = None

        return redirect('/')
    return render_template('addEvent.html', title='Personal Diary', form=form)


@app.route('/delete_Event/<nid>')
def delete(nid):
    if "username" not in session:
        return redirect('/login')
    Event = EventModel(db.get_connection())
    Event.delete(nid)
    return redirect('/')


@app.route('/edit_Event/<nid>')
def editEvent(nid):
    if "username" not in session:
        return redirect('/login')
    Event = EventModel(db.get_connection())
    global edit
    edit = nid
    return redirect("/add_event")


@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        users.insert(form.username.data, form.password.data)
        flash('You have successfully registered', 'success')
        return redirect('/login')
    return render_template('register.html', title='Registration', form=form)


@app.route('/admin')
def admin():
    if "username" not in session or session['admin'] != 1:
        flash('Access denied!', 'danger')
        return redirect('/')
    Event, users = EventModel(db.get_connection()), UsersModel(db.get_connection())
    names, amount = {}, {}
    for n in Event.get_all():
        if n[3] in amount:
            amount[n[3]] += 1
        else:
            names[n[3]] = users.get(n[3])[1]
            amount[n[3]] = 1
    return render_template('admin.html', title='User statistics',
                           amount=amount, names=names)


@app.route('/sort/<sort>')
def sortedEvent(sort):
    if not "username" in session:
        return redirect('/login')
    session['sort'] = int(sort)
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('admin', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')