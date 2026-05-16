from app.models import CourseClass, Enrollment, EnrollmentStatus, CompletedCourse, CompletedCourseStatus


def get_all_classes():
    return CourseClass.query.all()


def get_class_by_id(course_class_id):
    return CourseClass.query.get(course_class_id)


def get_registered_enrollments(student_id, semester_id):
    return Enrollment.query.filter_by(
        student_id=student_id,
        semester_id=semester_id,
        status=EnrollmentStatus.REGISTERED
    ).all()


def get_enrollment_by_student_and_class(student_id, course_class_id):
    return Enrollment.query.filter_by(
        student_id=student_id,
        course_class_id=course_class_id,
        status=EnrollmentStatus.REGISTERED
    ).first()


def has_completed_course(student_id, course_id):
    completed = CompletedCourse.query.filter_by(
        student_id=student_id,
        course_id=course_id,
        status=CompletedCourseStatus.PASSED
    ).first()

    return completed is not None