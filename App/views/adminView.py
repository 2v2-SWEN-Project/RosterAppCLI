# app/views/admin_views.py
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from App.controllers import staff, auth, admin
# Removed flask_jwt_extended import
from sqlalchemy.exc import SQLAlchemyError
from App.models import Shift, Schedule
from App.database import db

admin_view = Blueprint('admin_view', __name__, template_folder='../templates')

# Based on the controllers in App/controllers/admin.py, admins can do the following actions:
# 1. Create Schedule
# 2. Get Schedule Report
# 3. View Dashboard with real data

@admin_view.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the admin dashboard with real data."""
    try:
        total_staff = admin.get_total_staff_count()
        shifts_this_week = admin.get_shifts_this_week()
        pending_requests = admin.get_pending_swap_requests()
        attendance = admin.get_staff_attendance()
        
        return render_template('admin/index.html',
                             total_staff=total_staff,
                             shifts_this_week=shifts_this_week,
                             pending_requests_count=len(pending_requests),
                             pending_requests=pending_requests,
                             attendance=attendance)
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/api/dashboard-overview', methods=['GET'])
def dashboard_overview():
    """API endpoint for dashboard overview metrics."""
    try:
        total_staff = admin.get_total_staff_count()
        shifts_this_week = admin.get_shifts_this_week()
        pending_requests = admin.get_pending_swap_requests()
        
        return jsonify({
            "total_staff": total_staff,
            "shifts_this_week": shifts_this_week,
            "pending_requests": len(pending_requests)
        }), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/api/staff-attendance', methods=['GET'])
def staff_attendance():
    """API endpoint for staff attendance data."""
    try:
        attendance = admin.get_staff_attendance()
        return jsonify(attendance), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/api/pending-swap-requests', methods=['GET'])
def pending_swap_requests():
    """API endpoint for pending shift swap requests."""
    try:
        requests = admin.get_pending_swap_requests()
        return jsonify(requests), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/api/swap-request/<int:request_id>/approve', methods=['POST'])
def approve_swap_request(request_id):
    """Approve a shift swap request."""
    try:
        swap_req = admin.approve_swap_request(request_id)
        return jsonify({"message": "Swap request approved", "request": swap_req.get_json()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

@admin_view.route('/api/swap-request/<int:request_id>/deny', methods=['POST'])
def deny_swap_request(request_id):
    """Deny a shift swap request."""
    try:
        swap_req = admin.deny_swap_request(request_id)
        return jsonify({"message": "Swap request denied", "request": swap_req.get_json()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

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