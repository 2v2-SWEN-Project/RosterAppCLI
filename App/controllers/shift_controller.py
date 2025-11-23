"""
Shift Controller

Handles individual shift operations (clock in/out, view, update, delete).
This controller layer manages all database interactions and business logic for shifts.
"""

from datetime import datetime
from typing import Dict, Any, Tuple

from App.database import db
from App.models import Staff, Shift


class ShiftController:
    """
    Controller for shift-specific operations.
    Responsible for clock in/out, shift viewing, and modifications.
    """

    # ============================================================================
    # CONTROLLER MARKER: clock_in()
    # ============================================================================
    # Purpose: Staff member clocks in to a shift
    #
    # Signature:
    #   @staticmethod
    #   def clock_in(staff_id: int, shift_id: int) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Validation:
    #      a. Query Shift by shift_id; return error if not found
    #      b. Verify shift.staff_id == staff_id (belongs to requesting staff)
    #      c. Check if already clocked in (shift.clock_in is not None)
    #   2. Update shift:
    #      a. Set shift.clock_in = datetime.utcnow()
    #      b. db.session.add(shift)
    #      c. db.session.commit()
    #   3. Return:
    #      - Success: (shift.get_json(), 200)
    #      - Already clocked in: ({"error": "Already clocked in"}, 400)
    #      - Not found/unauthorized: ({"error": "Shift not found or unauthorized"}, 404)
    #
    # Usage:
    #   result, status = ShiftController.clock_in(staff_id=2, shift_id=10)
    #
    # Example output (200):
    #   {
    #       "id": 10,
    #       "staff_id": 2,
    #       "start_time": "2024-11-22T09:00:00",
    #       "end_time": "2024-11-22T17:00:00",
    #       "clock_in": "2024-11-22T09:05:30",
    #       "clock_out": null
    #   }
    pass

    # ============================================================================
    # CONTROLLER MARKER: clock_out()
    # ============================================================================
    # Purpose: Staff member clocks out of a shift
    #
    # Signature:
    #   @staticmethod
    #   def clock_out(staff_id: int, shift_id: int) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Validation:
    #      a. Query Shift by shift_id; return error if not found
    #      b. Verify shift.staff_id == staff_id (belongs to requesting staff)
    #      c. Check if clocked in (shift.clock_in is not None)
    #      d. Check if not already clocked out (shift.clock_out is None)
    #   2. Update shift:
    #      a. Set shift.clock_out = datetime.utcnow()
    #      b. db.session.add(shift)
    #      c. db.session.commit()
    #   3. Return:
    #      - Success: (shift.get_json(), 200)
    #      - Not clocked in: ({"error": "Not clocked in"}, 400)
    #      - Already clocked out: ({"error": "Already clocked out"}, 400)
    #      - Not found/unauthorized: ({"error": "Shift not found or unauthorized"}, 404)
    #
    # Usage:
    #   result, status = ShiftController.clock_out(staff_id=2, shift_id=10)
    #
    # Example output (200):
    #   {
    #       "id": 10,
    #       "staff_id": 2,
    #       "start_time": "2024-11-22T09:00:00",
    #       "end_time": "2024-11-22T17:00:00",
    #       "clock_in": "2024-11-22T09:05:30",
    #       "clock_out": "2024-11-22T17:02:45"
    #   }
    pass

    # ============================================================================
    # CONTROLLER MARKER: get_staff_shifts()
    # ============================================================================
    # Purpose: Retrieve all shifts for a staff member
    #
    # Signature:
    #   @staticmethod
    #   def get_staff_shifts(staff_id: int) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Validation:
    #      a. Query Staff by staff_id; return error if not found
    #   2. Query shifts:
    #      a. Query all Shift records where staff_id matches
    #      b. Order by start_time DESC (most recent first)
    #   3. Return:
    #      - Success: ({"shifts": [shift.get_json(), ...], "count": N}, 200)
    #      - Error: ({"error": "Staff not found"}, 404)
    #
    # Usage:
    #   result, status = ShiftController.get_staff_shifts(staff_id=2)
    #
    # Example output (200):
    #   {
    #       "shifts": [
    #           {"id": 10, "staff_id": 2, "start_time": "2024-11-22T09:00:00", ...},
    #           {"id": 9, "staff_id": 2, "start_time": "2024-11-21T09:00:00", ...},
    #       ],
    #       "count": 2
    #   }
    pass

    # ============================================================================
    # CONTROLLER MARKER: update_shift()
    # ============================================================================
    # Purpose: Admin updates shift times (for corrections)
    #
    # Signature:
    #   @staticmethod
    #   def update_shift(
    #       shift_id: int,
    #       start_time: datetime = None,
    #       end_time: datetime = None
    #   ) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Validation:
    #      a. Query Shift by shift_id; return error if not found
    #      b. If both start_time and end_time provided, verify start_time < end_time
    #      c. Don't allow updates if clock_in/out times already set (hard constraint)
    #   2. Update shift:
    #      a. If start_time provided: shift.start_time = start_time
    #      b. If end_time provided: shift.end_time = end_time
    #      c. db.session.add(shift)
    #      d. db.session.commit()
    #   3. Return:
    #      - Success: (shift.get_json(), 200)
    #      - Error: ({"error": "message"}, 400/404)
    #
    # Usage:
    #   result, status = ShiftController.update_shift(
    #       shift_id=10,
    #       start_time=datetime(2024, 11, 22, 10, 0)
    #   )
    pass

    # ============================================================================
    # CONTROLLER MARKER: delete_shift()
    # ============================================================================
    # Purpose: Admin deletes a shift
    #
    # Signature:
    #   @staticmethod
    #   def delete_shift(shift_id: int) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Validation:
    #      a. Query Shift by shift_id; return error if not found
    #      b. Don't allow deletion if clock_in/out times are set (hard constraint)
    #   2. Delete shift:
    #      a. db.session.delete(shift)
    #      b. db.session.commit()
    #   3. Return:
    #      - Success: ({"id": shift_id, "deleted": true}, 200)
    #      - Error: ({"error": "message"}, 400/404)
    #
    # Usage:
    #   result, status = ShiftController.delete_shift(shift_id=10)
    pass

    # ============================================================================
    # CONTROLLER MARKER: get_shift_report()
    # ============================================================================
    # Purpose: Generate a shift report (for admin/analytics)
    #
    # Signature:
    #   @staticmethod
    #   def get_shift_report(
    #       start_date: datetime,
    #       end_date: datetime,
    #       staff_id: int = None
    #   ) -> Tuple[Dict[str, Any], int]:
    #
    # Responsibilities:
    #   1. Query shifts between start_date and end_date
    #   2. If staff_id provided, filter to that staff member only
    #   3. Calculate statistics:
    #      - Total shifts, total hours, average hours per shift
    #      - Clock in/out stats (on time, late, etc. — if tracking)
    #      - Per-staff breakdown
    #   4. Return:
    #      - Success: (report_dict, 200)
    #      - Error: ({"error": "message"}, 400/404)
    #
    # Usage:
    #   result, status = ShiftController.get_shift_report(
    #       start_date=datetime(2024, 11, 1),
    #       end_date=datetime(2024, 11, 30),
    #       staff_id=2
    #   )
    pass
