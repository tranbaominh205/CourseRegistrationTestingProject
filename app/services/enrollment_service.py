from datetime import date
from app.extensions import db
from app.models import Enrollment, EnrollmentStatus
from app.repositories.course_class_repository import (
    get_class_by_id,
    get_registered_enrollments,
    get_enrollment_by_student_and_class,
    has_completed_course
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


def register_course(student_id, course_class_id, current_date=None):
    if current_date is None:
        current_date = date.today()

    course_class = get_class_by_id(course_class_id)

    if course_class is None:
        return None, "Course class not found"

    semester = course_class.semester

    if current_date > semester.registration_end_date:
        return None, "Registration deadline has passed"

    if course_class.current_students >= course_class.max_students:
        return None, "Course class is full"

    existed_enrollment = get_enrollment_by_student_and_class(
        student_id,
        course_class_id
    )

    if existed_enrollment is not None:
        return None, "Student already registered this class"

    if has_completed_course(student_id, course_class.course_id):
        return None, "Student has already completed this course"

    existing_enrollments = get_registered_enrollments(
        student_id,
        semester.id
    )

    for enrollment in existing_enrollments:
        if is_schedule_conflict(enrollment.course_class, course_class):
            return None, "Schedule conflict"

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