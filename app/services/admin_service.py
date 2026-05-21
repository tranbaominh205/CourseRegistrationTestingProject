from app.extensions import db
from app.models import (
    Course,
    CourseClass,
    CourseClassStatus,
    ClassSchedule,
    Enrollment,
    Room,
    Semester,
)

MAX_CLASS_STUDENTS = 50


class AdminServiceError(ValueError):
    pass


def _to_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise AdminServiceError(f"{field_name} không hợp lệ")


def is_period_overlap(start_1, end_1, start_2, end_2):
    return start_1 <= end_2 and start_2 <= end_1


def is_room_schedule_conflict(
    room_id,
    day_of_week,
    start_period,
    end_period,
    exclude_course_class_id=None,
):
    query = ClassSchedule.query.filter_by(
        room_id=room_id,
        day_of_week=day_of_week,
    )

    if exclude_course_class_id is not None:
        query = query.filter(ClassSchedule.course_class_id != exclude_course_class_id)

    schedules = query.all()

    for schedule in schedules:
        if is_period_overlap(
            start_period,
            end_period,
            schedule.start_period,
            schedule.end_period,
        ):
            return True

    return False


def _validate_course_class_data(data, course_class_id=None):
    course_id = _to_int(data.get("course_id"), "Môn học")
    semester_id = _to_int(data.get("semester_id"), "Học kỳ")
    room_id = _to_int(data.get("room_id"), "Phòng học")
    day_of_week = _to_int(data.get("day_of_week"), "Thứ học")
    start_period = _to_int(data.get("start_period"), "Tiết bắt đầu")
    end_period = _to_int(data.get("end_period"), "Tiết kết thúc")

    class_code = (data.get("class_code") or "").strip().upper()
    status = data.get("status") or CourseClassStatus.OPEN
    max_students = _to_int(data.get("max_students") or 50, "Số sinh viên tối đa")

    if not class_code:
        raise AdminServiceError("Mã lớp học phần không được để trống")

    if status not in [CourseClassStatus.OPEN, CourseClassStatus.CLOSED]:
        raise AdminServiceError("Trạng thái lớp học phần không hợp lệ")

    if max_students < 1 or max_students > MAX_CLASS_STUDENTS:
        raise AdminServiceError("Số sinh viên tối đa mỗi lớp không được vượt quá 50")

    if day_of_week < 2 or day_of_week > 8:
        raise AdminServiceError("Thứ học phải từ 2 đến 8")

    if start_period < 1 or end_period < 1 or start_period > 15 or end_period > 15:
        raise AdminServiceError("Tiết học phải từ 1 đến 15")

    if start_period > end_period:
        raise AdminServiceError("Tiết bắt đầu không được lớn hơn tiết kết thúc")

    course = db.session.get(Course, course_id)
    if course is None:
        raise AdminServiceError("Môn học không tồn tại")

    semester = db.session.get(Semester, semester_id)
    if semester is None:
        raise AdminServiceError("Học kỳ không tồn tại")

    room = db.session.get(Room, room_id)
    if room is None:
        raise AdminServiceError("Phòng học không tồn tại")

    existed_class = CourseClass.query.filter_by(class_code=class_code).first()
    if existed_class is not None and existed_class.id != course_class_id:
        raise AdminServiceError("Mã lớp học phần đã tồn tại")

    if max_students > room.capacity:
        raise AdminServiceError("Số sinh viên tối đa không được vượt quá sức chứa phòng")

    if is_room_schedule_conflict(
        room_id=room_id,
        day_of_week=day_of_week,
        start_period=start_period,
        end_period=end_period,
        exclude_course_class_id=course_class_id,
    ):
        raise AdminServiceError("Lịch học bị trùng phòng")

    return {
        "course_id": course_id,
        "semester_id": semester_id,
        "room_id": room_id,
        "day_of_week": day_of_week,
        "start_period": start_period,
        "end_period": end_period,
        "class_code": class_code,
        "max_students": max_students,
        "status": status,
    }


def get_all_course_classes():
    return CourseClass.query.order_by(CourseClass.id.desc()).all()


def get_course_class_or_404(course_class_id):
    return db.session.get(CourseClass, course_class_id)


def get_admin_form_options():
    return {
        "courses": Course.query.order_by(Course.code.asc()).all(),
        "semesters": Semester.query.order_by(Semester.start_date.desc()).all(),
        "rooms": Room.query.order_by(Room.code.asc()).all(),
        "statuses": [CourseClassStatus.OPEN, CourseClassStatus.CLOSED],
    }


def create_course_class(data):
    validated = _validate_course_class_data(data)

    course_class = CourseClass(
        course_id=validated["course_id"],
        semester_id=validated["semester_id"],
        class_code=validated["class_code"],
        max_students=validated["max_students"],
        current_students=0,
        status=validated["status"],
    )

    db.session.add(course_class)
    db.session.flush()

    schedule = ClassSchedule(
        course_class_id=course_class.id,
        room_id=validated["room_id"],
        day_of_week=validated["day_of_week"],
        start_period=validated["start_period"],
        end_period=validated["end_period"],
    )

    db.session.add(schedule)
    db.session.commit()

    return course_class


def update_course_class(course_class_id, data):
    course_class = db.session.get(CourseClass, course_class_id)

    if course_class is None:
        raise AdminServiceError("Không tìm thấy lớp học phần")

    validated = _validate_course_class_data(data, course_class_id=course_class.id)

    if validated["max_students"] < course_class.current_students:
        raise AdminServiceError(
            "Số sinh viên tối đa không được nhỏ hơn số sinh viên hiện tại"
        )

    course_class.course_id = validated["course_id"]
    course_class.semester_id = validated["semester_id"]
    course_class.class_code = validated["class_code"]
    course_class.max_students = validated["max_students"]
    course_class.status = validated["status"]

    schedule = ClassSchedule.query.filter_by(course_class_id=course_class.id).first()

    if schedule is None:
        schedule = ClassSchedule(course_class_id=course_class.id)
        db.session.add(schedule)

    schedule.room_id = validated["room_id"]
    schedule.day_of_week = validated["day_of_week"]
    schedule.start_period = validated["start_period"]
    schedule.end_period = validated["end_period"]

    db.session.commit()

    return course_class


def has_any_enrollment(course_class_id):
    return Enrollment.query.filter_by(course_class_id=course_class_id).count() > 0


def delete_course_class(course_class_id):
    course_class = db.session.get(CourseClass, course_class_id)

    if course_class is None:
        raise AdminServiceError("Không tìm thấy lớp học phần")

    if has_any_enrollment(course_class.id):
        raise AdminServiceError("Không được xoá lớp nếu đã có sinh viên đăng ký")

    ClassSchedule.query.filter_by(course_class_id=course_class.id).delete()
    db.session.delete(course_class)
    db.session.commit()

    return True