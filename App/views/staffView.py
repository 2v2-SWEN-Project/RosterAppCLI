# app/views/staff_views.py
from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, flash
from App.controllers import staff, auth
from App.database import db
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from datetime import datetime, timedelta

staff_views = Blueprint('staff_views', __name__, template_folder='../templates')

# Staff authentication decorator
def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('index_views.staff_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============== API ROUTES ==============

# Staff view roster route (API)
@staff_views.route('/api/staff/roster', methods=['GET'])
def view_roster():
    try:
        staff_id = request.args.get('staff_id', type=int)
        roster = staff.get_combined_roster(staff_id)
        return jsonify(roster), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error"}), 500

# Get shift details (API)
@staff_views.route('/api/staff/shift', methods=['GET'])
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

# Staff Clock in endpoint (API)
@staff_views.route('/api/staff/clock_in', methods=['POST'])
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

# Staff Clock out endpoint (API)
@staff_views.route('/api/staff/clock_out', methods=['POST'])
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

# ============== SWAP REQUEST API ROUTES ==============

@staff_views.route('/api/staff/swap-requests', methods=['GET'])
@staff_required
def get_swap_requests():
    """Get all swap requests for the logged-in staff member."""
    from App.models import ShiftSwapRequest
    
    staff_id = session.get('user_id')
    
    # Get requests made by this staff member
    made_requests = ShiftSwapRequest.query.filter_by(requesting_staff_id=staff_id).all()
    
    # Get requests received by this staff member
    received_requests = ShiftSwapRequest.query.filter_by(requested_staff_id=staff_id).all()
    
    return jsonify({
        'made_requests': [r.get_json() for r in made_requests],
        'received_requests': [r.get_json() for r in received_requests]
    }), 200

@staff_views.route('/api/staff/swap-requests', methods=['POST'])
@staff_required
def create_swap_request():
    """Create a new shift swap request."""
    from App.models import ShiftSwapRequest, Shift
    
    staff_id = session.get('user_id')
    data = request.get_json()
    
    shift_id = data.get('shift_id')
    requested_staff_id = data.get('requested_staff_id')
    reason = data.get('reason', '')
    
    if not shift_id or not requested_staff_id:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify the shift belongs to the requesting staff
    shift = Shift.query.get(shift_id)
    if not shift or shift.staff_id != staff_id:
        return jsonify({'error': 'Invalid shift or not your shift'}), 400
    
    try:
        new_request = ShiftSwapRequest(
            requesting_staff_id=staff_id,
            requested_staff_id=requested_staff_id,
            shift_id=shift_id,
            reason=reason,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({'message': 'Swap request created', 'request': new_request.get_json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@staff_views.route('/api/staff/swap-requests/<int:request_id>/respond', methods=['POST'])
@staff_required
def respond_to_swap_request(request_id):
    """Respond to a received swap request (accept/decline)."""
    from App.models import ShiftSwapRequest, Shift
    
    staff_id = session.get('user_id')
    data = request.get_json()
    action = data.get('action')  # 'accept' or 'decline'
    
    if action not in ['accept', 'decline']:
        return jsonify({'error': 'Invalid action'}), 400
    
    swap_request = ShiftSwapRequest.query.get(request_id)
    if not swap_request:
        return jsonify({'error': 'Request not found'}), 404
    
    if swap_request.requested_staff_id != staff_id:
        return jsonify({'error': 'Not authorized to respond to this request'}), 403
    
    if swap_request.status != 'pending':
        return jsonify({'error': 'Request already processed'}), 400
    
    try:
        if action == 'accept':
            # Swap the shift assignment
            shift = Shift.query.get(swap_request.shift_id)
            if shift:
                shift.staff_id = swap_request.requested_staff_id
            swap_request.status = 'approved'
        else:
            swap_request.status = 'denied'
        
        db.session.commit()
        return jsonify({'message': f'Request {action}ed', 'request': swap_request.get_json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============== WEB PAGE ROUTES ==============

@staff_views.route('/staff/swap-requests', methods=['GET', 'POST'])
@staff_required
def staff_swap_requests():
    """View and manage swap requests."""
    from App.models import ShiftSwapRequest, Shift, Staff
    
    staff_id = session.get('user_id')
    
    if request.method == 'POST':
        action = request.form.get('action')
        request_id = request.form.get('request_id')
        
        if request_id and action in ['accept', 'decline']:
            swap_request = ShiftSwapRequest.query.get(int(request_id))
            if swap_request and swap_request.requested_staff_id == staff_id:
                try:
                    if action == 'accept':
                        shift = Shift.query.get(swap_request.shift_id)
                        if shift:
                            shift.staff_id = swap_request.requested_staff_id
                        swap_request.status = 'approved'
                        flash('Swap request accepted! The shift has been assigned to you.', 'success')
                    else:
                        swap_request.status = 'denied'
                        flash('Swap request declined.', 'error')
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error processing request: {str(e)}', 'error')
        
        return redirect(url_for('staff_views.staff_swap_requests'))
    
    # GET - fetch swap requests
    made_requests = ShiftSwapRequest.query.filter_by(requesting_staff_id=staff_id).order_by(ShiftSwapRequest.created_at.desc()).all()
    received_requests = ShiftSwapRequest.query.filter_by(requested_staff_id=staff_id, status='pending').order_by(ShiftSwapRequest.created_at.desc()).all()
    
    return render_template('staff_swap_requests.html',
                         made_requests=made_requests,
                         received_requests=received_requests)

@staff_views.route('/staff/profile', methods=['GET', 'POST'])
@staff_required
def staff_profile():
    """View and update staff profile."""
    from App.models import Staff, Shift
    
    staff_id = session.get('user_id')
    staff_member = Staff.query.get(staff_id)
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if current_password and new_password:
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif not staff_member.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            else:
                try:
                    staff_member.set_password(new_password)
                    db.session.commit()
                    flash('Password updated successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error updating password: {str(e)}', 'error')
        
        return redirect(url_for('staff_views.staff_profile'))
    
    # Get statistics
    total_shifts = Shift.query.filter_by(staff_id=staff_id).count()
    completed_shifts = Shift.query.filter(Shift.staff_id == staff_id, Shift.clock_out.isnot(None)).count()
    
    return render_template('staff_profile.html', staff=staff_member, total_shifts=total_shifts, completed_shifts=completed_shifts)