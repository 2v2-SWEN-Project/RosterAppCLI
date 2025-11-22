from flask import Blueprint, render_template, jsonify, request, flash, send_from_directory, redirect, url_for
# Removed flask_jwt_extended import

from .index import index_views

from App.controllers import (
    login,
)

auth_views = Blueprint('auth_views', __name__, template_folder='../templates')

'''
Page/Action Routes
'''

@auth_views.route('/identify', methods=['GET'])
def identify_page():
    return render_template('message.html', title="Identify", message="You are logged in (no auth)")
    

@auth_views.route('/login', methods=['POST'])
def login_action():
    data = request.form
    user = login(data['username'], data['password'])
    response = redirect(request.referrer)
    if not user:
        flash('Bad username or password given'), 401
    else:
        flash('Login Successful')
    return response

@auth_views.route('/logout', methods=['GET'])
def logout_action():
    response = redirect(request.referrer)
    flash("Logged Out!")
    return response

'''
API Routes
'''

@auth_views.route('/api/login', methods=['POST'])
def user_login_api():
    data = request.json
    user = login(data['username'], data['password'])
    if not user:
        return jsonify(message='bad username or password given'), 401
    return jsonify(user_id=user.id)

@auth_views.route('/api/identify', methods=['GET'])
def identify_user():
    return jsonify({'message': "You are logged in (no auth)"})

@auth_views.route('/api/logout', methods=['GET'])
def logout_api():
    return jsonify(message="Logged Out!")