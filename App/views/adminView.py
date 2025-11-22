# app/views/staff_views.py
from flask import Blueprint, jsonify, request
from datetime import datetime
from App.controllers import staff, auth, admin
# Removed flask_jwt_extended import
from sqlalchemy.exc import SQLAlchemyError

admin_view = Blueprint('admin_view', __name__, template_folder='../templates')

# Based on the controllers in App/controllers/admin.py, admins can do the following actions:
# 1. Create Schedule
# 2. Get Schedule Report

@admin_view.route('/createSchedule', methods=['POST'])
def createSchedule():
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        scheduleName = data.get("scheduleName")
        schedule = admin.create_schedule(admin_id, scheduleName)
        return jsonify(schedule.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/createShift', methods=['POST'])
def createShift():
    try:
        data = request.get_json()
        admin_id = data.get("admin_id")
        scheduleID = data.get("scheduleID")
        staffID = data.get("staffID")
        startTime = data.get("start_time")
        endTime = data.get("end_time")
        try:
            start_time = datetime.fromisoformat(startTime)
            end_time = datetime.fromisoformat(endTime)
        except ValueError:
            start_time = datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
        shift = admin.schedule_shift(admin_id, staffID, scheduleID, start_time, end_time)
        print("Debug: Created shift in view:", shift.get_json())
        return jsonify(shift.get_json()), 200
    except (PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 403
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/shiftReport', methods=['GET'])
def shiftReport():
    try:
        admin_id = request.args.get('admin_id')
        report = admin.get_shift_report(admin_id)
        return jsonify(report), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500