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
    # show welcome page with admin and staff login options
    return render_template('welcome.html')


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
            create_user(username, password, 'staff')
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
    from App.controllers import admin
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
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'error')
        return render_template('admin/index.html',
                             total_staff=0,
                             shifts_this_week=0,
                             pending_requests_count=0,
                             pending_requests=[],
                             attendance=[])


@index_views.route('/admin/users', methods=['GET'])
@admin_required
def admin_user_list():
    from App.models import User
    users = User.query.all()
    return render_template('user_list.html', users=users)


@index_views.route('/admin/roster', methods=['GET'])
@admin_required
def admin_roster():
    from App.models import Shift, Staff, Schedule
    from datetime import datetime, timedelta
    import calendar
    
    # Get schedule filter and week_start from query parameters
    schedule_type = request.args.get('schedule_type', 'auto')  # Default to 'auto'
    selected_schedule_id = request.args.get('schedule_id')
    week_start_str = request.args.get('week_start')
    
    # Get all schedules and organize by type
    all_schedules = Schedule.query.all()
    auto_schedules = [s for s in all_schedules if s.generation_method == 'auto']
    manual_schedules = [s for s in all_schedules if s.generation_method == 'manual']
    
    # Determine which schedule to display
    schedule_to_use = None
    
    if selected_schedule_id:
        schedule_to_use = Schedule.query.get(selected_schedule_id)
    elif schedule_type == 'auto' and auto_schedules:
        schedule_to_use = auto_schedules[0]  # Default to first auto schedule
    elif schedule_type == 'manual' and manual_schedules:
        schedule_to_use = manual_schedules[0]  # Default to first manual schedule
    elif auto_schedules:
        schedule_to_use = auto_schedules[0]  # Fallback to auto if only auto exists
    elif manual_schedules:
        schedule_to_use = manual_schedules[0]  # Fallback to manual if only manual exists
    
    # Get week_start or use current week
    if week_start_str:
        try:
            week_start = datetime.fromisoformat(week_start_str).date()
        except (ValueError, TypeError):
            week_start = datetime.now().date()
    else:
        week_start = datetime.now().date()
    
    # Get the Monday of the week
    days_since_monday = week_start.weekday()
    week_start = week_start - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    # Get shifts for this week (from selected schedule if available)
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.max.time())
    
    if schedule_to_use:
        shifts = Shift.query.filter(
            Shift.start_time >= week_start_dt,
            Shift.start_time <= week_end_dt,
            Shift.schedule_id == schedule_to_use.id
        ).order_by(Shift.start_time.asc()).all()
    else:
        shifts = []
    
    # Organize shifts by day of week
    schedule_by_day = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        schedule_by_day[day.strftime('%Y-%m-%d')] = {
            'day_name': day.strftime('%A'),
            'date': day.strftime('%B %d, %Y'),
            'short_date': day.strftime('%m/%d'),
            'shifts': []
        }
    
    # Add shifts to their respective days
    for shift in shifts:
        day_key = shift.start_time.date().isoformat()
        if day_key in schedule_by_day:
            staff = Staff.query.get(shift.staff_id)
            schedule_by_day[day_key]['shifts'].append({
                'id': shift.id,
                'staff_id': shift.staff_id,
                'staff_name': staff.username if staff else f'Staff {shift.staff_id}',
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'duration': str((shift.end_time - shift.start_time).total_seconds() / 3600).rstrip('0').rstrip('.')
            })
    
    # Calculate navigation dates
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    
    context = {
        'week_start': week_start.isoformat(),
        'week_start_display': week_start.strftime('%B %d, %Y'),
        'week_end_display': week_end.strftime('%B %d, %Y'),
        'schedule_by_day': schedule_by_day,
        'prev_week': prev_week.isoformat(),
        'next_week': next_week.isoformat(),
        'total_shifts': len(shifts),
        'auto_schedules': auto_schedules,
        'manual_schedules': manual_schedules,
        'selected_schedule': schedule_to_use,
        'current_schedule_type': 'auto' if schedule_to_use and schedule_to_use.generation_method == 'auto' else 'manual'
    }
    
    return render_template('weekly_roster.html', **context)

@index_views.route('/admin/weekly-roster', methods=['GET'])
@admin_required
def weekly_roster():
    return render_template('weekly_roster.html')


@index_views.route('/admin/reports', methods=['GET', 'POST'])
@admin_required
def shift_report():
    from App.models import Staff
    from App.controllers import ScheduleController
    from datetime import datetime
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from flask import make_response
    
    staff_members = Staff.query.all()
    report_data = None
    
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        week_start_str = request.form.get('week_start')
        generate_pdf = request.form.get('generate_pdf')
        
        if staff_id and week_start_str:
            try:
                week_start = datetime.fromisoformat(week_start_str)
                report_data, status_code = ScheduleController.get_staff_weekly_report(int(staff_id), week_start)
                
                if generate_pdf:
                    # Generate PDF
                    pdf_buffer = BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                    elements = []
                    
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=18,
                        textColor=colors.HexColor('#1a2332'),
                        spaceAfter=6,
                    )
                    
                    # Title
                    title = Paragraph(f"Weekly Shift Report - {report_data['staff_name']}", title_style)
                    elements.append(title)
                    
                    # Summary info
                    summary_style = ParagraphStyle(
                        'CustomBody',
                        parent=styles['BodyText'],
                        fontSize=10,
                        textColor=colors.HexColor('#333333'),
                    )
                    
                    summary_text = f"""
                    <br/><b>Period:</b> {report_data['week_start']} to {report_data['week_end']}<br/>
                    <b>Total Shifts:</b> {report_data['total_shifts']}<br/>
                    <b>Attended Shifts:</b> {report_data['attended_shifts']}<br/>
                    <b>Attendance Rate:</b> {report_data['attendance_percentage']}%<br/>
                    <b>Scheduled Hours:</b> {report_data['total_scheduled_hours']}<br/>
                    <b>Actual Hours:</b> {report_data['total_actual_hours']}<br/>
                    <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
                    """
                    elements.append(Paragraph(summary_text, summary_style))
                    elements.append(Spacer(1, 0.3*inch))
                    
                    # Shifts table
                    table_data = [['Date', 'Start', 'End', 'Scheduled Hrs', 'Clock In', 'Clock Out', 'Actual Hrs', 'Attended']]
                    for shift in report_data['shifts']:
                        table_data.append([
                            shift['date'],
                            shift['start_time'],
                            shift['end_time'],
                            str(shift['scheduled_hours']),
                            shift['clock_in'],
                            shift['clock_out'],
                            str(shift['actual_hours']),
                            shift['attended']
                        ])
                    
                    table = Table(table_data, colWidths=[0.9*inch, 0.75*inch, 0.75*inch, 0.85*inch, 0.75*inch, 0.75*inch, 0.75*inch, 0.7*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2332')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ]))
                    elements.append(table)
                    
                    # Build PDF
                    doc.build(elements)
                    pdf_buffer.seek(0)
                    
                    response = make_response(pdf_buffer.read())
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = f'attachment; filename="shift_report_{report_data["staff_name"]}_{report_data["week_start"]}.pdf"'
                    return response
                
            except ValueError as e:
                flash(f'Invalid date format: {str(e)}', 'error')
            except Exception as e:
                flash(f'Error generating report: {str(e)}', 'error')
    
    return render_template('shift_report.html', staff_members=staff_members, report_data=report_data)

@index_views.route('/admin/requests', methods=['GET', 'POST'])
@admin_required
def admin_requests():
    from App.models import ShiftSwapRequest
    
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')  # approve or deny
        
        if request_id and action:
            try:
                swap_request = ShiftSwapRequest.query.get(int(request_id))
                if not swap_request:
                    flash('Request not found', 'error')
                else:
                    if action == 'approve':
                        swap_request.status = 'approved'
                        flash(f'Request from {swap_request.requesting_staff.username} has been approved', 'success')
                    elif action == 'deny':
                        swap_request.status = 'denied'
                        flash(f'Request from {swap_request.requesting_staff.username} has been denied', 'error')
                    
                    db.session.commit()
            except Exception as e:
                flash(f'Error processing request: {str(e)}', 'error')
        
        return redirect(url_for('index_views.admin_requests'))
    
    # GET - Show all pending requests
    pending_requests = ShiftSwapRequest.query.filter_by(status='pending').order_by(ShiftSwapRequest.created_at.desc()).all()
    approved_requests = ShiftSwapRequest.query.filter_by(status='approved').order_by(ShiftSwapRequest.created_at.desc()).all()
    denied_requests = ShiftSwapRequest.query.filter_by(status='denied').order_by(ShiftSwapRequest.created_at.desc()).all()
    
    return render_template('admin_requests.html', 
                         pending_requests=pending_requests,
                         approved_requests=approved_requests,
                         denied_requests=denied_requests)

@index_views.route('/logout', methods=['GET'])
def logout():
    # later you can call your real auth logout function here
    return redirect(url_for('index_views.staff_login'))

@index_views.route('/admin/create-shift', methods=['GET', 'POST'])
@admin_required
def create_shift():
    if request.method == 'POST':
        try:
            from datetime import datetime
            from App.models import Shift
            
            staff_id = request.form.get('staff_id')
            shift_date = request.form.get('shift_date')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            
            if not all([staff_id, shift_date, start_time_str, end_time_str]):
                flash('All fields are required.', 'error')
                from App.models import Staff
                staff_members = Staff.query.all()
                return render_template('create_shift.html', staff_members=staff_members)
            
            # Combine date and time
            start_datetime = datetime.fromisoformat(f"{shift_date}T{start_time_str}")
            end_datetime = datetime.fromisoformat(f"{shift_date}T{end_time_str}")
            
            if end_datetime <= start_datetime:
                flash('End time must be after start time.', 'error')
                from App.models import Staff
                staff_members = Staff.query.all()
                return render_template('create_shift.html', staff_members=staff_members)
            
            # Create the shift
            new_shift = Shift(
                staff_id=int(staff_id),
                start_time=start_datetime,
                end_time=end_datetime
            )
            from App.database import db
            db.session.add(new_shift)
            db.session.commit()
            
            flash(f'Shift created successfully for staff member {staff_id}!', 'success')
            from App.models import Staff
            staff_members = Staff.query.all()
            return render_template('create_shift.html', staff_members=staff_members)
        
        except Exception as e:
            flash(f'Error creating shift: {str(e)}', 'error')
            from App.models import Staff
            staff_members = Staff.query.all()
            return render_template('create_shift.html', staff_members=staff_members)
    
    # GET request - show form
    from App.models import Staff
    staff_members = Staff.query.all()
    return render_template('create_shift.html', staff_members=staff_members)

@index_views.route('/admin/create-schedule', methods=['GET', 'POST'])
@admin_required
def create_schedule():
    from App.models import Schedule, Shift
    from App.database import db
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            schedule_name = request.form.get('schedule_name', '').strip()
            week_start = request.form.get('week_start')
            week_end = request.form.get('week_end')
            admin_id = session.get('user_id')
            shift_ids = request.form.getlist('shifts')
            
            if not all([schedule_name, week_start, week_end, admin_id]):
                flash('All fields are required.', 'error')
                available_shifts = Shift.query.filter_by(schedule_id=None).all()
                return render_template('create_schedule.html', available_shifts=available_shifts)
            
            # Parse dates
            start_date = datetime.fromisoformat(week_start)
            end_date = datetime.fromisoformat(week_end)
            
            if end_date <= start_date:
                flash('End date must be after start date.', 'error')
                available_shifts = Shift.query.filter_by(schedule_id=None).all()
                return render_template('create_schedule.html', available_shifts=available_shifts)
            
            # Create schedule
            new_schedule = Schedule(
                name=schedule_name,
                created_by=admin_id,
                admin_id=admin_id,
                created_at=datetime.utcnow(),
                generation_method='manual'
            )
            db.session.add(new_schedule)
            db.session.flush()  # Get the schedule ID without committing
            
            # Assign selected shifts to schedule
            if shift_ids:
                for shift_id in shift_ids:
                    try:
                        shift = Shift.query.get(int(shift_id))
                        if shift and shift.schedule_id is None:
                            shift.schedule_id = new_schedule.id
                    except (ValueError, TypeError):
                        continue
            
            db.session.commit()
            
            flash(f'Schedule "{schedule_name}" created successfully with {len(shift_ids)} shifts!', 'success')
            return redirect(url_for('index_views.admin_dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating schedule: {str(e)}', 'error')
            available_shifts = Shift.query.filter_by(schedule_id=None).all()
            return render_template('create_schedule.html', available_shifts=available_shifts)
    
    # GET request - show form with available shifts
    available_shifts = Shift.query.filter_by(schedule_id=None).all()
    return render_template('create_schedule.html', available_shifts=available_shifts)

@index_views.route('/admin/select-schedule', methods=['GET', 'POST'])
@admin_required
def select_schedule():
    from App.models import Staff, Schedule
    from App.controllers.schedule_controller import ScheduleController
    from datetime import datetime, timedelta
    
    if request.method == 'POST':
        try:
            schedule_name = request.form.get('schedule_name', '').strip()
            week_start_str = request.form.get('week_start')
            week_end_str = request.form.get('week_end')
            strategy = request.form.get('strategy', '').strip()
            admin_id = session.get('user_id')
            
            if not all([schedule_name, week_start_str, week_end_str, strategy, admin_id]):
                flash('All fields are required.', 'error')
                staff_members = Staff.query.all()
                return render_template('select_strategy.html', staff_members=staff_members)
            
            # Parse dates
            week_start = datetime.fromisoformat(week_start_str)
            week_end = datetime.fromisoformat(week_end_str)
            
            if week_end <= week_start:
                flash('End date must be after start date.', 'error')
                staff_members = Staff.query.all()
                return render_template('select_strategy.html', staff_members=staff_members)
            
            # Get all staff members
            staff_members = Staff.query.all()
            if not staff_members:
                flash('No staff members available for scheduling.', 'error')
                return render_template('select_strategy.html', staff_members=staff_members)
            
            eligible_staff_ids = [s.id for s in staff_members]
            
            # Create schedule
            from App.database import db
            new_schedule = Schedule(
                name=schedule_name,
                created_by=admin_id,
                admin_id=admin_id,
                created_at=datetime.utcnow(),
                generation_method='auto',
                strategy_used=strategy
            )
            db.session.add(new_schedule)
            db.session.flush()
            
            # Calculate number of days
            num_days = (week_end.date() - week_start.date()).days + 1
            
            # Default shift hours: use start hour from week_start, default 8-hour shift
            shift_start_hour = week_start.hour if week_start.hour else 9
            shift_end_hour = shift_start_hour + 8  # 8-hour shift by default
            
            # Auto-populate schedule using the selected strategy
            result, status_code = ScheduleController.auto_populate_schedule(
                schedule_id=new_schedule.id,
                strategy_type=strategy,
                eligible_staff_ids=eligible_staff_ids,
                num_days=num_days,
                shift_start_hour=shift_start_hour,
                shift_end_hour=shift_end_hour,
                base_date=week_start
            )
            
            if status_code != 201:
                db.session.rollback()
                flash(f'Error generating schedule: {result.get("error", "Unknown error")}', 'error')
                staff_members = Staff.query.all()
                return render_template('select_strategy.html', staff_members=staff_members)
            
            db.session.commit()
            
            shifts_count = result.get('count', 0)
            flash(f'Schedule "{schedule_name}" created successfully with {shifts_count} auto-generated shifts using {strategy} strategy!', 'success')
            staff_members = Staff.query.all()
            return render_template('select_strategy.html', staff_members=staff_members)
        
        except Exception as e:
            flash(f'Error creating schedule: {str(e)}', 'error')
            staff_members = Staff.query.all()
            return render_template('select_strategy.html', staff_members=staff_members)
    
    # GET request - show form
    staff_members = Staff.query.all()
    return render_template('select_strategy.html', staff_members=staff_members)

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
