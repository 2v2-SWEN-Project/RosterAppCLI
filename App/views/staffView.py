# app/views/staff_views.py
from flask import Blueprint, jsonify, request
from App.controllers import staff, auth
# Removed flask_jwt_extended import
from sqlalchemy.exc import SQLAlchemyError

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

#Based on the controllers in App/controllers/staff.py, staff can do the following actions:
# 1. View combined roster
# 2. Clock in 
# 3. Clock out
# 4. View specific shift details

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

# Staff view roster route
@staff_views.route('/staff/roster', methods=['GET'])
def view_roster():
    try:
        staff_id = request.args.get('staff_id', type=int)
        roster = staff.get_combined_roster(staff_id)
        return jsonify(roster), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@staff_views.route('/staff/shift', methods=['GET'])
def view_shift():
    try:
        data = request.get_json()
        shift_id = data.get("shiftID")
        shift = staff.get_shift(shift_id)
        if not shift:
            return jsonify({"error": "Shift not found"}), 404
        return jsonify(shift.get_json()), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

# Staff Clock in endpoint
@staff_views.route('/staff/clock_in', methods=['POST'])
def clockIn():
    try:
        data = request.get_json()
        staff_id = int(data.get('staff_id'))
        shift_id = data.get("shiftID")
        shiftOBJ = staff.clock_in(staff_id, shift_id)
        return jsonify(shiftOBJ.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

# Staff Clock out endpoint
@staff_views.route('/staff/clock_out/', methods=['POST'])
def clock_out():
    try:
        data = request.get_json()
        staff_id = int(data.get('staff_id'))
        shift_id = data.get("shiftID")
        shift = staff.clock_out(staff_id, shift_id)
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500