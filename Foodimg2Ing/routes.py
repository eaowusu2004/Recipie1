from flask import render_template, url_for, flash, redirect, request, send_from_directory
from flask_login import login_required, current_user
from Foodimg2Ing import app
from Foodimg2Ing.output import output
import os


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'favicon.ico')


@app.route('/', methods=['GET'])
@login_required
def home():
    return render_template('home.html')


@app.route('/about', methods=['GET'])
@login_required
def about():
    return render_template('about.html')


@app.route('/', methods=['POST'])
@login_required
def predict():
    if 'imagefile' not in request.files or not request.files['imagefile'].filename:
        return redirect(url_for('home'))
    imagefile = request.files['imagefile']
    demo_dir = os.path.join(app.root_path, 'static', 'demo_imgs')
    os.makedirs(demo_dir, exist_ok=True)
    image_path = os.path.join(demo_dir, imagefile.filename)
    imagefile.save(image_path)
    img = "demo_imgs/" + imagefile.filename
    title, ingredients, recipe = output(image_path)
    return render_template('predict.html', title=title, ingredients=ingredients, recipe=recipe, img=img)


@app.route('/<samplefoodname>')
@login_required
def predictsample(samplefoodname):
    if samplefoodname in ['favicon.ico', 'robots.txt']:
        return redirect(url_for('static', filename=f'images/{samplefoodname}'))
    imagefile = os.path.join(app.root_path, 'static', 'images', str(samplefoodname) + ".jpg")
    if not os.path.exists(imagefile):
        return redirect(url_for('home'))
    img = "images/" + str(samplefoodname) + ".jpg"
    title, ingredients, recipe = output(imagefile)
    return render_template('predict.html', title=title, ingredients=ingredients, recipe=recipe, img=img)