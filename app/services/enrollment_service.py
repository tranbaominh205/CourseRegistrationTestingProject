from datetime import date

from app.extensions import db
from app.models import Enrollment, EnrollmentStatus
from app.repositories.course_class_repository import (
    get_class_by_id,
    get_registered_enrollments,
    get_enrollment_by_student_and_class,
    has_completed_course,
    get_prerequisites,
)


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


def register_course(student_id, course_class_id, current_date=None):
    if current_date is None:
        current_date = date.today()

    course_class = get_class_by_id(course_class_id)

    if course_class is None:
        return None, "Không tìm thấy lớp học phần"

    semester = course_class.semester

    if current_date > semester.registration_end_date:
        return None, "Đã hết hạn đăng ký học phần"

    if course_class.current_students >= course_class.max_students:
        return None, "Lớp học phần đã đủ số lượng"

    existed_enrollment = get_enrollment_by_student_and_class(
        student_id,
        course_class_id
    )

    if existed_enrollment is not None:
        return None, "Sinh viên đã đăng ký lớp học phần này"

    if has_completed_course(student_id, course_class.course_id):
        return None, "Sinh viên đã học môn này rồi"

    # Check prerequisites
    prerequisites = get_prerequisites(course_class.course_id)
    missing = []
    for p in prerequisites:
        # p.prerequisite_course_id available; use has_completed_course to check
        if not has_completed_course(student_id, p.prerequisite_course_id):
            # try to get course name/code from relationship if available
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

    if current_credits + new_course_credits > 25:
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


def can_confirm_registration(student_id, semester_id):
    total_credits = calculate_registered_credits(student_id, semester_id)

    if total_credits < 12:
        return False, f"Bạn chưa đủ số tín chỉ tối thiểu. Cần đăng ký thêm {12 - total_credits} tín chỉ"

    if total_credits > 25:
        return False, "Tổng số tín chỉ vượt quá giới hạn cho phép"

    return True, "Bạn đã đủ điều kiện xác nhận đăng ký học kỳ"