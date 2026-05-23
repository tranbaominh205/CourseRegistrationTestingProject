from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models import CourseClass, Enrollment, EnrollmentStatus, Student, MajorRegistrationWindow
from app.repositories.course_class_repository import (
    get_class_by_id,
    get_registered_enrollments,
    get_enrollment_by_student_and_class,
    has_completed_course,
    get_prerequisites,
)

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


MIN_CREDITS = 12
MAX_CREDITS = 25


def _normalize_enrollment_ids(enrollment_ids):
    normalized = []
    seen = set()

    if not enrollment_ids:
        return normalized

    for enrollment_id in enrollment_ids:
        try:
            normalized_id = int(enrollment_id)
        except (TypeError, ValueError):
            continue

        if normalized_id in seen:
            continue

        seen.add(normalized_id)
        normalized.append(normalized_id)

    return normalized


def is_period_overlap(start_1, end_1, start_2, end_2):
    return start_1 <= end_2 and start_2 <= end_1


def is_schedule_conflict(existing_class, new_class):
    for existing_schedule in existing_class.schedules:
        for new_schedule in new_class.schedules:
            same_day = existing_schedule.day_of_week == new_schedule.day_of_week
            overlap = is_period_overlap(
                existing_schedule.start_period,
                existing_schedule.end_period,
                new_schedule.start_period,
                new_schedule.end_period
            )

            if same_day and overlap:
                return True

    return False


def calculate_registered_credits(student_id, semester_id):
    enrollments = get_registered_enrollments(student_id, semester_id)

    total = 0
    for enrollment in enrollments:
        total += enrollment.course_class.course.credits

    return total


def calculate_credits_after_pending_cancel(student_id, semester_id, pending_cancel_ids):
    registered_enrollments = get_registered_enrollments(student_id, semester_id)
    pending_ids = set(_normalize_enrollment_ids(pending_cancel_ids))

    total = 0
    for enrollment in registered_enrollments:
        if enrollment.id in pending_ids:
            continue
        total += enrollment.course_class.course.credits

    return total


def get_registration_window_dates(student, semester):
    if student is not None and student.major:
        major_window = MajorRegistrationWindow.query.filter_by(
            semester_id=semester.id,
            major=student.major
        ).first()
        if major_window is not None:
            return major_window.registration_start_date, major_window.registration_end_date

    return semester.registration_start_date, semester.registration_end_date


def validate_registration_window(student, semester, current_date):
    registration_start_date, registration_end_date = get_registration_window_dates(student, semester)

    if current_date < registration_start_date:
        return "Chưa đến thời gian đăng ký học phần"

    if current_date > registration_end_date:
        return "Đã hết hạn đăng ký học phần"

    return None


def validate_cancel_draft(student_id, enrollment_id):
    try:
        enrollment_id = int(enrollment_id)
    except (TypeError, ValueError):
        return None, "Không tìm thấy đăng ký học phần."

    enrollment = db.session.get(Enrollment, enrollment_id)
    if enrollment is None:
        return None, "Không tìm thấy đăng ký học phần."

    if enrollment.student_id != student_id:
        return None, "Bạn không có quyền hủy đăng ký này."

    if enrollment.status == EnrollmentStatus.CANCELLED:
        return None, "Học phần này đã bị hủy trước đó."

    if enrollment.status != EnrollmentStatus.REGISTERED:
        return None, "Không tìm thấy đăng ký học phần."

    return enrollment, None


def cancel_enrollment(student_id, enrollment_id, current_date=None):
    if current_date is None:
        current_date = date.today()

    enrollment, error = validate_cancel_draft(student_id, enrollment_id)
    if error is not None:
        return None, error
    rule_error = _validate_cancel_rules(enrollment, current_date=current_date)
    if rule_error is not None:
        return None, rule_error

    enrollment.status = EnrollmentStatus.CANCELLED
    enrollment.cancelled_at = datetime.now(VIETNAM_TZ)

    course_class = enrollment.course_class
    if course_class is not None:
        current_students = course_class.current_students or 0
        course_class.current_students = max(0, current_students - 1)

    return enrollment, None


def _validate_cancel_rules(enrollment, current_date=None):
    if current_date is None:
        current_date = date.today()

    semester = enrollment.semester
    if semester is None:
        return "Không tìm thấy đăng ký học phần."

    try:
        calculated_deadline = semester.start_date + timedelta(days=14)
    except Exception:
        return "Đã quá hạn hủy đăng ký học phần."

    if current_date > calculated_deadline:
        return "Đã quá hạn hủy đăng ký học phần."

    if getattr(enrollment, 'midterm_score', None) is not None or enrollment.midterm_exam_done:
        return "Không thể hủy vì học phần đã có điểm giữa kỳ."

    return None


def can_cancel_enrollment(student_id, enrollment_id, current_date=None):

    if current_date is None:
        current_date = date.today()

    enrollment, error = validate_cancel_draft(student_id, enrollment_id)
    if error is not None:
        return False, error

    rule_error = _validate_cancel_rules(enrollment, current_date=current_date)
    if rule_error is not None:
        return False, rule_error

    return True, None


def cancel_pending_enrollments(student_id, enrollment_ids, current_date=None):
    if current_date is None:
        current_date = date.today()

    cancelled_ids = []
    messages = []

    for enrollment_id in _normalize_enrollment_ids(enrollment_ids):
        enrollment, error = cancel_enrollment(student_id, enrollment_id, current_date=current_date)
        if error is not None:
            messages.append(error)
            continue

        if enrollment is not None:
            cancelled_ids.append(enrollment.id)

    if cancelled_ids:
        db.session.commit()

    return cancelled_ids, messages


def register_course(student_id, course_class_id, current_date=None):
    if current_date is None:
        current_date = date.today()

    course_class = get_class_by_id(course_class_id)

    if course_class is None:
        return None, "Không tìm thấy lớp học phần"

    semester = course_class.semester
    student = db.session.get(Student, student_id)
    window_error = validate_registration_window(student, semester, current_date)
    if window_error is not None:
        return None, window_error

    if course_class.current_students >= course_class.max_students:
        return None, "Lớp học phần đã đủ số lượng"

    existed_enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_class_id=course_class_id,
        status=EnrollmentStatus.REGISTERED
    ).first()

    if existed_enrollment is not None:
        return None, "Sinh viên đã đăng ký lớp học phần này"

    cancelled_enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_class_id=course_class_id,
        status=EnrollmentStatus.CANCELLED
    ).first()

    if cancelled_enrollment is not None:
        cancelled_enrollment.status = EnrollmentStatus.REGISTERED
        cancelled_enrollment.registered_at = datetime.now(VIETNAM_TZ)
        cancelled_enrollment.cancelled_at = None
        course_class.current_students += 1
        db.session.commit()
        return cancelled_enrollment, None

    same_course_enrollment = Enrollment.query.join(
        CourseClass
    ).filter(
        Enrollment.student_id == student_id,
        Enrollment.semester_id == semester.id,
        Enrollment.status == EnrollmentStatus.REGISTERED,
        CourseClass.course_id == course_class.course_id,
    ).first()

    if same_course_enrollment is not None:
        return None, "Sinh viên đã đăng ký môn học này ở lớp khác"

    if has_completed_course(student_id, course_class.course_id):
        return None, "Sinh viên đã học môn này rồi"

    prerequisites = get_prerequisites(course_class.course_id)
    missing = []
    for p in prerequisites:
        if not has_completed_course(student_id, p.prerequisite_course_id):
            try:
                name = p.prerequisite_course.name
                code = p.prerequisite_course.code
                missing.append(f"{code} - {name}")
            except Exception:
                missing.append(str(p.prerequisite_course_id))

    if missing:
        return None, f"Thiếu điều kiện tiên quyết: {', '.join(missing)}"

    current_credits = calculate_registered_credits(student_id, semester.id)
    new_course_credits = course_class.course.credits

    if current_credits + new_course_credits > MAX_CREDITS:
        return None, "Tổng số tín chỉ vượt quá giới hạn cho phép"

    existing_enrollments = get_registered_enrollments(
        student_id,
        semester.id
    )

    for enrollment in existing_enrollments:
        if is_schedule_conflict(enrollment.course_class, course_class):
            return None, "Lớp học phần bị trùng lịch học"

    enrollment = Enrollment(
        student_id=student_id,
        course_class_id=course_class.id,
        semester_id=semester.id,
        status=EnrollmentStatus.REGISTERED
    )

    course_class.current_students += 1

    db.session.add(enrollment)
    db.session.commit()

    return enrollment, None


def can_confirm_registration(student_id, semester_id, total_credits=None):
    if total_credits is None:
        total_credits = calculate_registered_credits(student_id, semester_id)

    if total_credits < MIN_CREDITS:
        return False, (
            f"Bạn chưa đủ số tín chỉ tối thiểu. Cần đăng ký thêm {MIN_CREDITS - total_credits} tín chỉ"
        )

    if total_credits > MAX_CREDITS:
        return False, "Tổng số tín chỉ vượt quá giới hạn cho phép"

    return True, "Bạn đã đủ điều kiện xác nhận đăng ký học kỳ"