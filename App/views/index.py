from flask import Blueprint, redirect, render_template, jsonify, request, url_for, flash, session
from App.controllers import create_user, initialize, login
from functools import wraps

index_views = Blueprint('index_views', __name__, template_folder='../templates')

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index_views.staff_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Home / Utility ----------

@index_views.route('/', methods=['GET'])
def index_page():
    # send people straight to the staff login page
    return redirect(url_for('index_views.staff_login'))


@index_views.route('/init', methods=['GET'])
def init():
    initialize()
    return jsonify(message='db initialized!')


@index_views.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


# ---------- Staff UI Pages ----------

@index_views.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('staff_login.html', username=username)

        user = login(username, password)
        if not user:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('staff_login.html', username=username)
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        # Redirect admins to admin dashboard
        if user.role == 'admin':
            flash('Welcome, Administrator!', 'success')
            return redirect(url_for('index_views.admin_dashboard'))
        
        return redirect(url_for('index_views.staff_dashboard'))

    # GET
    return render_template('staff_login.html')


@index_views.route('/staff/signup', methods=['GET', 'POST'])
def staff_signup():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not fullname or not email or not phone or not role or not username or not password:
            flash('All fields are required.', 'error')
            return render_template('staff_signup.html', fullname=fullname, email=email, phone=phone, username=username)

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('staff_signup.html', fullname=fullname, email=email, phone=phone, username=username)

        try:
            # TODO: Adjust this call to match your real create_user signature
            # e.g. create_user(username, password, fullname, email, phone, role)
            create_user(username, password)
        except Exception as e:
            flash(f'Could not create account: {e}', 'error')
            return render_template('staff_signup.html', fullname=fullname, email=email, phone=phone, username=username)

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('index_views.staff_login'))

    # GET
    return render_template('staff_signup.html')


@index_views.route('/staff/dashboard', methods=['GET'])
def staff_dashboard():
    staff_id = session.get('user_id')
    today_shift = None
    shifts_week = []
    total_hours = 0.0
    
    if staff_id:
        from App.models import Shift
        from datetime import datetime, timedelta
        
        # Get today's shift
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today + timedelta(days=1)
        today_shift = Shift.query.filter(
            Shift.staff_id == staff_id,
            Shift.start_time >= today,
            Shift.start_time < today_end
        ).first()
        
        # Get this week's shifts (next 7 days)
        week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        shifts_week = Shift.query.filter(
            Shift.staff_id == staff_id,
            Shift.start_time >= week_start,
            Shift.start_time < week_end
        ).all()
        
        # Calculate total hours
        for shift in shifts_week:
            if shift.clock_in and shift.clock_out:
                hours = (shift.clock_out - shift.clock_in).total_seconds() / 3600
                total_hours += hours
    
    return render_template('staff_dashboard.html', 
                         today_shift=today_shift,
                         shifts_count=len(shifts_week),
                         total_hours=f"{total_hours:.1f}")


@index_views.route('/staff/shift-details', methods=['GET'])
def staff_shift_details():
    return render_template('shift_details.html')


@index_views.route('/staff/clock', methods=['GET', 'POST'])
def staff_clock():
    if request.method == 'POST':
        action = request.form.get('action', '').strip()
        shift_id = request.form.get('shift_id', '1').strip()
        
        # Get staff_id from session
        staff_id = session.get('user_id')
        if not staff_id:
            flash('You must be logged in.', 'error')
            return redirect(url_for('index_views.staff_login'))
        
        if action == 'clock_in':
            from App.controllers.shift_controller import ShiftController
            result, status_code = ShiftController.clock_in(staff_id, int(shift_id))
            if status_code == 200:
                flash('Successfully clocked in!', 'success')
            else:
                flash(f"Clock in failed: {result.get('error', 'Unknown error')}", 'error')
        elif action == 'clock_out':
            from App.controllers.shift_controller import ShiftController
            result, status_code = ShiftController.clock_out(staff_id, int(shift_id))
            if status_code == 200:
                flash('Successfully clocked out!', 'success')
            else:
                flash(f"Clock out failed: {result.get('error', 'Unknown error')}", 'error')
        
        return render_template('staff_clock.html')
    
    # GET - fetch current shift info
    staff_id = session.get('user_id')
    shift_data = None
    if staff_id:
        from App.controllers.shift_controller import ShiftController
        from App.models import Shift
        # Get the first upcoming shift for this staff member (ordered by start_time ascending)
        shifts = Shift.query.filter_by(staff_id=staff_id).order_by(Shift.start_time.asc()).first()
        shift_data = shifts.get_json() if shifts else None
    
    return render_template('staff_clock.html', shift=shift_data)


@index_views.route('/staff/request-swap', methods=['GET', 'POST'])
def request_swap():
    if request.method == 'POST':
        shift_id = request.form.get('shift_id', '').strip()
        target_staff = request.form.get('target_staff', '').strip()
        reason = request.form.get('reason', '').strip()

        if not shift_id or not target_staff or not reason:
            flash('All fields are required.', 'error')
            return render_template('request_swap.html')

        try:
            # TODO: Call your real shift swap controller here
            # e.g. shift_controller.request_swap(shift_id, target_staff, reason)
            flash(
                f'Shift swap request submitted successfully! Staff member has been notified.',
                'success'
            )
        except Exception as e:
            flash(f'Could not submit swap request: {e}', 'error')

        return render_template('request_swap.html')

    # GET
    return render_template('request_swap.html')

@index_views.route('/staff/schedule', methods=['GET'])
def staff_schedule():
    # For now, reuse the weekly roster page as the staff's "View Schedule"
    return render_template('weekly_roster.html')

@index_views.route('/staff/shifts', methods=['GET'])
def staff_shifts():
    staff_id = session.get('user_id')
    completed_shifts = []
    total_hours = 0
    completion_rate = 0
    
    if staff_id:
        from App.models import Shift
        # Get all shifts for this staff member
        shifts = Shift.query.filter_by(staff_id=staff_id).order_by(Shift.start_time.desc()).all()
        
        # Filter for completed shifts (both clocked in and out)
        for shift in shifts:
            if shift.clock_in and shift.clock_out:
                completed_shifts.append(shift)
        
        # Calculate total hours
        if completed_shifts:
            for shift in completed_shifts:
                if shift.clock_in and shift.clock_out:
                    hours = (shift.clock_out - shift.clock_in).total_seconds() / 3600
                    total_hours += hours
        
        # Calculate completion rate
        if shifts:
            completion_rate = (len(completed_shifts) / len(shifts)) * 100
    
    return render_template('staff_shifts.html', shifts=completed_shifts, total_hours=round(total_hours, 2), completion_rate=int(completion_rate))

# ---------- Admin UI Pages ----------

@index_views.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('admin_login.html')

        user = login(username, password)
        if not user:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('admin_login.html')
        
        if user.role != 'admin':
            flash('You do not have admin privileges.', 'error')
            return render_template('admin_login.html')
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        flash('Welcome, Administrator!', 'success')
        return redirect(url_for('index_views.admin_dashboard'))

    # GET
    return render_template('admin_login.html')


@index_views.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


@index_views.route('/admin/users', methods=['GET'])
@admin_required
def admin_user_list():
    from App.models import User
    users = User.query.all()
    return render_template('user_list.html', users=users)


@index_views.route('/admin/weekly-roster', methods=['GET'])
@admin_required
def weekly_roster():
    return render_template('weekly_roster.html')


@index_views.route('/admin/reports', methods=['GET'])
@admin_required
def shift_report():
    return render_template('shift_report.html')

@index_views.route('/logout', methods=['GET'])
def logout():
    # later you can call your real auth logout function here
    return redirect(url_for('index_views.staff_login'))

@index_views.route('/admin/create-schedule', methods=['GET', 'POST'])
@admin_required
def create_schedule():
    if request.method == 'POST':
        week_start = request.form.get('week_start')
        staff_id   = request.form.get('staff_id')
        shift_date = request.form.get('shift_date')
        shift_start = request.form.get('shift_start')
        shift_end   = request.form.get('shift_end')

        # TODO: later call your real controller to save a shift:
        # scheduler.create_manual_shift(...)

        # For now just show a success message and stay on the page
        flash(
            f"Added shift for staff {staff_id} on {shift_date} "
            f"{shift_start}–{shift_end} (week starting {week_start}).",
            "success"
        )
        return render_template('create_schedule.html')

    # GET request
    return render_template('create_schedule.html')

@index_views.route('/admin/select-strategy', methods=['GET', 'POST'])
@admin_required
def select_strategy():
    # Later you can POST the chosen strategy and call your scheduler.
    if request.method == 'POST':
        chosen = request.form.get('strategy')
        # TODO: call your scheduler with this strategy
        flash(f'Selected strategy: {chosen}', 'success')
        return redirect(url_for('index_views.admin_dashboard'))

    return render_template('select_strategy.html')
