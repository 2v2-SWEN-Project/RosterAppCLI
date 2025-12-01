from flask import Blueprint, redirect, render_template, jsonify, request, url_for, flash
from App.controllers import create_user, initialize

index_views = Blueprint('index_views', __name__, template_folder='../templates')

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

        # TODO: hook into your real auth controller here
        # e.g. auth.login(username, password)
        # For now, just pretend it worked and go to dashboard:
        return redirect(url_for('index_views.staff_dashboard'))

    # GET
    return render_template('staff_login.html')


@index_views.route('/staff/signup', methods=['GET', 'POST'])
def staff_signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('staff_signup.html', username=username)

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('staff_signup.html', username=username)

        try:
            # Adjust this call to match your real create_user signature
            # e.g. create_user(username, password, role="staff")
            create_user(username, password)
        except Exception as e:
            flash(f'Could not create user: {e}', 'error')
            return render_template('staff_signup.html', username=username)

        flash('Account created. You can now log in.', 'success')
        return redirect(url_for('index_views.staff_login'))

    # GET
    return render_template('staff_signup.html')


@index_views.route('/staff/dashboard', methods=['GET'])
def staff_dashboard():
    return render_template('staff_dashboard.html')


@index_views.route('/staff/shift-details', methods=['GET'])
def staff_shift_details():
    return render_template('shift_details.html')


@index_views.route('/staff/clock', methods=['GET'])
def staff_clock():
    return render_template('shift_details.html')


@index_views.route('/staff/request-swap', methods=['GET', 'POST'])
def request_swap():
    return render_template('shift_details.html')

@index_views.route('/staff/schedule', methods=['GET'])
def staff_schedule():
    # For now, reuse the weekly roster page as the staff's "View Schedule"
    return render_template('weekly_roster.html')

@index_views.route('/staff/shifts', methods=['GET'])
def staff_shifts():
    # Alias for the shift details/list page
    return render_template('shift_details.html')

# ---------- Admin UI Pages ----------

@index_views.route('/admin/login', methods=['GET'])
def admin_login():
    return render_template('admin_login.html')


@index_views.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    return render_template('admin_dashboard.html')


@index_views.route('/admin/users', methods=['GET'])
def admin_user_list():
    return render_template('user_list.html')


@index_views.route('/admin/weekly-roster', methods=['GET'])
def weekly_roster():
    return render_template('weekly_roster.html')


@index_views.route('/admin/reports', methods=['GET'])
def shift_report():
    return render_template('shift_report.html')

@index_views.route('/logout', methods=['GET'])
def logout():
    # later you can call your real auth logout function here
    return redirect(url_for('index_views.staff_login'))

@index_views.route('/admin/create-schedule', methods=['GET', 'POST'])
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
def select_strategy():
    # Later you can POST the chosen strategy and call your scheduler.
    if request.method == 'POST':
        chosen = request.form.get('strategy')
        # TODO: call your scheduler with this strategy
        flash(f'Selected strategy: {chosen}', 'success')
        return redirect(url_for('index_views.admin_dashboard'))

    return render_template('select_strategy.html')
