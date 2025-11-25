import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash
from App.main import create_app
from App.database import db, create_db
from datetime import datetime, timedelta
from App.models import User, Schedule, Shift
from App.controllers import (
    create_user,
    get_all_users_json,
    loginCLI,
    get_user,
    update_user,
    schedule_shift, 
    get_shift_report,
    get_combined_roster,
    clock_in,
    clock_out,
    get_shift 
)


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''



class UserUnitTests(unittest.TestCase):

# User unit tests
    def test_new_user_admin(self):
        user = create_user("bot", "bobpass","admin")
        assert user.username == "bot"

    def test_new_user_staff(self):
        user = create_user("pam", "pampass","staff")
        assert user.username == "pam"

    def test_create_user_invalid_role(self):
        user = create_user("jim", "jimpass","ceo")
        assert user == None


    def test_get_json(self):
        user = User("bob", "bobpass", "admin")
        user_json = user.get_json()
        self.assertDictEqual(user_json, {"id":None, "username":"bob", "role":"admin"})
    
    def test_hashed_password(self):
        password = "mypass"
        user = User(username="tester", password=password)
        assert user.password != password
        assert user.check_password(password) is True

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password)
        assert user.check_password(password)
# Admin unit tests
    def test_schedule_shift_valid(self):
        admin = create_user("admin1", "adminpass", "admin")
        staff = create_user("staff1", "staffpass", "staff")
        schedule = Schedule(name="Morning Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 10, 22, 8, 0, 0)
        end = datetime(2025, 10, 22, 16, 0, 0)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        assert shift.staff_id == staff.id
        assert shift.schedule_id == schedule.id
        assert shift.start_time == start
        assert shift.end_time == end
        assert isinstance(shift, Shift)

    def test_schedule_shift_invalid(self):
        admin = User("admin2", "adminpass", "admin")
        staff = User("staff2", "staffpass", "staff")
        invalid_schedule_id = 999

        start = datetime(2025, 10, 22, 8, 0, 0)
        end = datetime(2025, 10, 22, 16, 0, 0)
        try:
            shift = schedule_shift(admin.id, staff.id, invalid_schedule_id, start, end)
            assert shift is None  
        except Exception:
            assert True

    def test_get_shift_report(self):
        admin = create_user("superadmin", "superpass", "admin")
        staff = create_user("worker1", "workerpass", "staff")
        db.session.add_all([admin, staff])
        db.session.commit()

        schedule = Schedule(name="Weekend Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        shift1 = schedule_shift(admin.id, staff.id, schedule.id,
                                datetime(2025, 10, 26, 8, 0, 0),
                                datetime(2025, 10, 26, 16, 0, 0))
        shift2 = schedule_shift(admin.id, staff.id, schedule.id,
                                datetime(2025, 10, 27, 8, 0, 0),
                                datetime(2025, 10, 27, 16, 0, 0))
        
        report = get_shift_report(admin.id)
        assert len(report) >= 2
        assert report[0]["staff_id"] == staff.id
        assert report[0]["schedule_id"] == schedule.id

    def test_get_shift_report_invalid(self):
        non_admin = create_user("randomstaff", "randompass", "staff")

        try:
            get_shift_report(non_admin.id)
            assert False, "Expected PermissionError for non-admin user"
        except PermissionError as e:
            assert str(e) == "Only admin can view shift report"
# Staff unit tests
    def test_get_combined_roster_valid(self):
        staff = create_user("staff3", "pass123", "staff")
        admin = create_user("admin3", "adminpass", "admin")
        schedule = Schedule(name="Test Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        # create a shift
        shift = schedule_shift(admin.id, staff.id, schedule.id,
                               datetime(2025, 10, 23, 8, 0, 0),
                               datetime(2025, 10, 23, 16, 0, 0))

        roster = get_combined_roster(staff.id)
        assert len(roster) >= 1
        assert roster[0]["staff_id"] == staff.id
        assert roster[0]["schedule_id"] == schedule.id

    def test_get_combined_roster_invalid(self):
        non_staff = create_user("admin4", "adminpass", "admin")
        try:
            get_combined_roster(non_staff.id)
            assert False, "Expected PermissionError for non-staff"
        except PermissionError as e:
            assert str(e) == "Only staff can view roster"

    def test_clock_in_valid(self):
        admin = create_user("admin_clock", "adminpass", "admin")
        staff = create_user("staff_clock", "staffpass", "staff")

        schedule = Schedule(name="Clock Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 10, 25, 8, 0, 0)
        end = datetime(2025, 10, 25, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clocked_in_shift = clock_in(staff.id, shift.id)
        assert clocked_in_shift.clock_in is not None
        assert isinstance(clocked_in_shift.clock_in, datetime)

    def test_clock_in_invalid_user(self):
        admin = create_user("admin_clockin", "adminpass", "admin")
        schedule = Schedule(name="Invalid Clock In", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        staff = create_user("staff_invalid", "staffpass", "staff")
        start = datetime(2025, 10, 26, 8, 0, 0)
        end = datetime(2025, 10, 26, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        with pytest.raises(PermissionError) as e:
            clock_in(admin.id, shift.id)
        assert str(e.value) == "Only the assigned staff can clock in to this shift."

    def test_clock_in_invalid_shift(self):
        staff = create_user("clockstaff_invalid", "clockpass", "staff")
        with pytest.raises(ValueError) as e:
            clock_in(staff.id, 999)
        assert str(e.value) == "Invalid shift for staff"

    def test_clock_out_valid(self):
        admin = create_user("admin_clockout", "adminpass", "admin")
        staff = create_user("staff_clockout", "staffpass", "staff")

        schedule = Schedule(name="ClockOut Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 10, 27, 8, 0, 0)
        end = datetime(2025, 10, 27, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clocked_out_shift = clock_out(staff.id, shift.id)
        assert clocked_out_shift.clock_out is not None
        assert isinstance(clocked_out_shift.clock_out, datetime)

    def test_clock_out_invalid_user(self):
        admin = create_user("admin_invalid_out", "adminpass", "admin")
        schedule = Schedule(name="Invalid ClockOut Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        staff = create_user("staff_invalid_out", "staffpass", "staff")
        start = datetime(2025, 10, 28, 8, 0, 0)
        end = datetime(2025, 10, 28, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        with pytest.raises(PermissionError) as e:
            clock_out(admin.id, shift.id)
        assert str(e.value) == "Only the assigned staff can clock out of this shift."

    def test_clock_out_invalid_shift(self):
        staff = create_user("staff_invalid_shift_out", "staffpass", "staff")
        with pytest.raises(ValueError) as e:
            clock_out(staff.id, 999)  
        assert str(e.value) == "Invalid shift for staff"

    def test_schedule_shift_non_staff_user(self):
        """Test that only staff role can be assigned to shifts"""
        admin = create_user("admin_scheduler", "adminpass", "admin")
        regular_user = User("regular_user", "userpass", "user")
        db.session.add(regular_user)
        db.session.commit()
        
        schedule = Schedule(name="Test Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 11, 25, 8, 0, 0)
        end = datetime(2025, 11, 25, 16, 0, 0)

        with pytest.raises(PermissionError) as e:
            schedule_shift(admin.id, regular_user.id, schedule.id, start, end)
        assert str(e.value) == "Only staff can be assigned to a shift."

    def test_get_shift_valid(self):
        """Test retrieving a valid shift"""
        admin = create_user("admin_getshift", "adminpass", "admin")
        staff = create_user("staff_getshift", "staffpass", "staff")
        schedule = Schedule(name="Get Shift Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 11, 25, 9, 0, 0)
        end = datetime(2025, 11, 25, 17, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        retrieved_shift = get_shift(shift.id)
        assert retrieved_shift is not None
        assert retrieved_shift.id == shift.id
        assert retrieved_shift.staff_id == staff.id

    def test_get_shift_invalid(self):
        """Test retrieving an invalid shift returns None"""
        shift = get_shift(99999)
        assert shift is None

    def test_clock_in_already_clocked(self):
        """Test that clocking in twice raises an error"""
        admin = create_user("admin_double_clock", "adminpass", "admin")
        staff = create_user("staff_double_clock", "staffpass", "staff")
        schedule = Schedule(name="Double Clock Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 11, 25, 8, 0, 0)
        end = datetime(2025, 11, 25, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clock_in(staff.id, shift.id)

        with pytest.raises(ValueError) as e:
            clock_in(staff.id, shift.id)
        assert "already been clocked in" in str(e.value)

    def test_clock_out_already_clocked(self):
        """Test that clocking out twice raises an error"""
        admin = create_user("admin_double_out", "adminpass", "admin")
        staff = create_user("staff_double_out", "staffpass", "staff")
        schedule = Schedule(name="Double Out Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime(2025, 11, 25, 8, 0, 0)
        end = datetime(2025, 11, 25, 16, 0, 0)
        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clock_out(staff.id, shift.id)

        with pytest.raises(ValueError) as e:
            clock_out(staff.id, shift.id)
        assert "already been clocked out" in str(e.value)

    def test_create_schedule(self):
        """Test creating a schedule"""
        from App.controllers.admin import create_schedule
        admin = create_user("admin_schedule", "adminpass", "admin")
        
        schedule = create_schedule(admin.id, "Weekly Schedule")
        
        assert schedule is not None
        assert schedule.name == "Weekly Schedule"
        assert schedule.created_by == admin.id
        assert schedule.created_at is not None

    def test_schedule_shift_invalid_schedule(self):
        """Test scheduling shift with invalid schedule ID"""
        admin = create_user("admin_invalid_sched", "adminpass", "admin")
        staff = create_user("staff_invalid_sched", "staffpass", "staff")

        start = datetime(2025, 11, 25, 8, 0, 0)
        end = datetime(2025, 11, 25, 16, 0, 0)

        with pytest.raises(ValueError) as e:
            schedule_shift(admin.id, staff.id, 99999, start, end)
        assert str(e.value) == "Invalid schedule ID"

    def test_get_user_by_username(self):
        """Test retrieving user by username"""
        from App.controllers.user import get_user_by_username
        user = create_user("findme", "findpass", "staff")
        
        found = get_user_by_username("findme")
        assert found is not None
        assert found.username == "findme"
        assert found.role == "staff"

    def test_get_user_by_username_not_found(self):
        """Test retrieving non-existent user by username"""
        from App.controllers.user import get_user_by_username
        found = get_user_by_username("nonexistent")
        assert found is None

'''
    Integration Tests
'''
@pytest.fixture(autouse=True)
def clean_db():
    db.drop_all()
    create_db()
    db.session.remove()
    yield
# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    create_db()
    db.session.remove()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = User("bob", "bobpass","user")
    assert loginCLI("bob", "bobpass") != None

class UsersIntegrationTests(unittest.TestCase):

    def test_get_all_users_json(self):
        user = create_user("bot", "bobpass","admin")
        user = create_user("pam", "pampass","staff")
        users_json = get_all_users_json()
        self.assertListEqual([{"id":1, "username":"bot", "role":"admin"}, {"id":2, "username":"pam","role":"staff"}], users_json)

    def test_update_user(self):
        user = create_user("bot", "bobpass","admin")
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"

    def test_create_and_get_user(self):
        user = create_user("alex", "alexpass", "staff")
        retrieved = get_user(user.id)
        self.assertEqual(retrieved.username, "alex")
        self.assertEqual(retrieved.role, "staff")
    
    def test_get_all_users_json_integration(self):
        create_user("bot", "bobpass", "admin")
        create_user("pam", "pampass", "staff")
        users_json = get_all_users_json()
        expected = [
            {"id": 1, "username": "bot", "role": "admin"},
            {"id": 2, "username": "pam", "role": "staff"},
        ]
        self.assertEqual(users_json, expected)
        
    def test_admin_schedule_shift_for_staff(self):
        admin = create_user("admin1", "adminpass", "admin")
        staff = create_user("staff1", "staffpass", "staff")

        schedule = Schedule(name="Week 1 Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)
        retrieved = get_user(staff.id)

        self.assertIn(shift.id, [s.id for s in retrieved.shifts])
        self.assertEqual(shift.staff_id, staff.id)
        self.assertEqual(shift.schedule_id, schedule.id)

    def test_staff_view_combined_roster(self):
        admin = create_user("admin", "adminpass", "admin")
        staff = create_user("jane", "janepass", "staff")
        other_staff = create_user("mark", "markpass", "staff")

        schedule = Schedule(name="Shared Roster", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        schedule_shift(admin.id, staff.id, schedule.id, start, end)
        schedule_shift(admin.id, other_staff.id, schedule.id, start, end)

        roster = get_combined_roster(staff.id)
        self.assertTrue(any(s["staff_id"] == staff.id for s in roster))
        self.assertTrue(any(s["staff_id"] == other_staff.id for s in roster))

    def test_staff_clock_in_and_out(self):
        admin = create_user("admin", "adminpass", "admin")
        staff = create_user("lee", "leepass", "staff")

        schedule = Schedule(name="Daily Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        shift = schedule_shift(admin.id, staff.id, schedule.id, start, end)

        clock_in(staff.id, shift.id)
        clock_out(staff.id, shift.id)


        updated_shift = get_shift(shift.id)
        self.assertIsNotNone(updated_shift.clock_in)
        self.assertIsNotNone(updated_shift.clock_out)
        self.assertLess(updated_shift.clock_in, updated_shift.clock_out)
    
    def test_admin_generate_shift_report(self):
        admin = create_user("boss", "boss123", "admin")
        staff = create_user("sam", "sampass", "staff")

        schedule = Schedule(name="Weekly Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        schedule_shift(admin.id, staff.id, schedule.id, start, end)
        report = get_shift_report(admin.id)

        self.assertTrue(any("sam" in r["staff_name"] for r in report))
        self.assertTrue(all("start_time" in r and "end_time" in r for r in report))

    def test_permission_restrictions(self):
        """Test permission restrictions for different roles"""
        admin = create_user("perm_admin", "adminpass", "admin")
        staff = create_user("perm_worker", "workpass", "staff")
        regular_user = User("perm_regular", "regularpass", "user")
        db.session.add(regular_user)
        db.session.commit()

        # Create schedule
        schedule = Schedule(name="Restricted Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        start = datetime.now()
        end = start + timedelta(hours=8)

        # Test: Regular users (non-staff) cannot be assigned to shifts
        with self.assertRaises(PermissionError):
            schedule_shift(admin.id, regular_user.id, schedule.id, start, end)

        # Test: Admins cannot view roster (staff-only function)
        with self.assertRaises(PermissionError):
            get_combined_roster(admin.id)

        # Test: Staff cannot view shift reports (admin-only function)
        with self.assertRaises(PermissionError):
            get_shift_report(staff.id)

    def test_multiple_shifts_same_schedule(self):
        """Test creating multiple shifts for the same schedule"""
        admin = create_user("multi_admin", "adminpass", "admin")
        staff1 = create_user("staff_a", "staffpass", "staff")
        staff2 = create_user("staff_b", "staffpass", "staff")

        schedule = Schedule(name="Multi-Shift Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        shift1 = schedule_shift(admin.id, staff1.id, schedule.id,
                               datetime(2025, 11, 25, 8, 0, 0),
                               datetime(2025, 11, 25, 16, 0, 0))
        shift2 = schedule_shift(admin.id, staff2.id, schedule.id,
                               datetime(2025, 11, 25, 16, 0, 0),
                               datetime(2025, 11, 26, 0, 0, 0))

        self.assertEqual(shift1.schedule_id, schedule.id)
        self.assertEqual(shift2.schedule_id, schedule.id)
        self.assertNotEqual(shift1.staff_id, shift2.staff_id)

    def test_staff_multiple_shifts(self):
        """Test staff member assigned to multiple shifts"""
        admin = create_user("scheduler_admin", "adminpass", "admin")
        staff = create_user("busy_staff", "staffpass", "staff")

        schedule1 = Schedule(name="Morning Shifts", created_by=admin.id)
        schedule2 = Schedule(name="Evening Shifts", created_by=admin.id)
        db.session.add_all([schedule1, schedule2])
        db.session.commit()

        shift1 = schedule_shift(admin.id, staff.id, schedule1.id,
                               datetime(2025, 11, 25, 8, 0, 0),
                               datetime(2025, 11, 25, 12, 0, 0))
        shift2 = schedule_shift(admin.id, staff.id, schedule2.id,
                               datetime(2025, 11, 25, 18, 0, 0),
                               datetime(2025, 11, 25, 22, 0, 0))

        roster = get_combined_roster(staff.id)
        staff_shifts = [s for s in roster if s["staff_id"] == staff.id]
        self.assertGreaterEqual(len(staff_shifts), 2)

    def test_complete_shift_lifecycle(self):
        """Test complete shift lifecycle: create, clock in, clock out, verify"""
        admin = create_user("lifecycle_admin", "adminpass", "admin")
        staff = create_user("lifecycle_staff", "staffpass", "staff")

        # Create schedule
        schedule = Schedule(name="Lifecycle Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        # Schedule shift
        shift = schedule_shift(admin.id, staff.id, schedule.id,
                              datetime(2025, 11, 25, 9, 0, 0),
                              datetime(2025, 11, 25, 17, 0, 0))
        
        self.assertIsNone(shift.clock_in)
        self.assertIsNone(shift.clock_out)

        # Clock in
        clocked_in = clock_in(staff.id, shift.id)
        self.assertIsNotNone(clocked_in.clock_in)
        self.assertIsNone(clocked_in.clock_out)

        # Clock out
        clocked_out = clock_out(staff.id, shift.id)
        self.assertIsNotNone(clocked_out.clock_in)
        self.assertIsNotNone(clocked_out.clock_out)

        # Verify in report
        report = get_shift_report(admin.id)
        shift_in_report = next((s for s in report if s["id"] == shift.id), None)
        self.assertIsNotNone(shift_in_report)
        self.assertIsNotNone(shift_in_report["clock_in"])
        self.assertIsNotNone(shift_in_report["clock_out"])

    def test_admin_create_schedule_and_view_shifts(self):
        """Test admin creating schedule and viewing all shifts"""
        admin = create_user("view_admin", "adminpass", "admin")
        staff1 = create_user("view_staff1", "staffpass", "staff")
        staff2 = create_user("view_staff2", "staffpass", "staff")

        schedule = Schedule(name="View Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        schedule_shift(admin.id, staff1.id, schedule.id,
                      datetime(2025, 11, 25, 8, 0, 0),
                      datetime(2025, 11, 25, 16, 0, 0))
        schedule_shift(admin.id, staff2.id, schedule.id,
                      datetime(2025, 11, 26, 8, 0, 0),
                      datetime(2025, 11, 26, 16, 0, 0))

        report = get_shift_report(admin.id)
        self.assertGreaterEqual(len(report), 2)

    def test_login_and_roster_workflow(self):
        """Test user login and viewing their roster"""
        from App.controllers.auth import login
        admin = create_user("login_admin", "adminpass", "admin")
        staff = create_user("login_staff", "staffpass", "staff")

        # Test login
        logged_in_user = login("login_staff", "staffpass")
        self.assertIsNotNone(logged_in_user)
        self.assertEqual(logged_in_user.username, "login_staff")

        # Create shift for staff
        schedule = Schedule(name="Login Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        schedule_shift(admin.id, staff.id, schedule.id,
                      datetime(2025, 11, 25, 8, 0, 0),
                      datetime(2025, 11, 25, 16, 0, 0))

        # View roster
        roster = get_combined_roster(staff.id)
        self.assertGreater(len(roster), 0)

    def test_schedule_json_serialization(self):
        """Test schedule JSON serialization includes all required fields"""
        admin = create_user("json_admin", "adminpass", "admin")
        staff = create_user("json_staff", "staffpass", "staff")

        schedule = Schedule(name="JSON Schedule", created_by=admin.id)
        db.session.add(schedule)
        db.session.commit()

        schedule_shift(admin.id, staff.id, schedule.id,
                      datetime(2025, 11, 25, 8, 0, 0),
                      datetime(2025, 11, 25, 16, 0, 0))

        schedule_json = schedule.get_json()
        
        self.assertIn("id", schedule_json)
        self.assertIn("name", schedule_json)
        self.assertIn("created_at", schedule_json)
        self.assertIn("created_by", schedule_json)
        self.assertIn("shift_count", schedule_json)
        self.assertIn("shifts", schedule_json)
        self.assertEqual(schedule_json["shift_count"], 1)