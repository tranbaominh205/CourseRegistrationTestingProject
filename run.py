from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserRole,
    Student,
    Semester,
    Course,
    CoursePrerequisite,
    Room,
    CourseClass,
    ClassSchedule,
    CompletedCourse,
    MajorRegistrationWindow,
    CourseClassStatus,
    CompletedCourseStatus,
    Enrollment,
    EnrollmentStatus,
)

app = create_app()


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


@app.cli.command("reset-db")
def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully.")


@app.cli.command("seed-data")
def seed_data():
    with app.app_context():
        today = date.today()

        # =====================================================
        # Helper functions
        # =====================================================

        def get_or_create_user(username, password, role, active=True):
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    role=role,
                    is_active_account=active
                )
                db.session.add(user)
                db.session.flush()
            return user

        def get_or_create_student(user, student_code, full_name, major):
            student = Student.query.filter_by(student_code=student_code).first()
            if student is None:
                student = Student(
                    user_id=user.id,
                    student_code=student_code,
                    full_name=full_name,
                    major=major
                )
                db.session.add(student)
                db.session.flush()
            else:
                student.user_id = user.id
                student.full_name = full_name
                student.major = major
            return student

        def get_or_create_semester(
            name,
            academic_year,
            start_date,
            end_date,
            registration_start_date,
            registration_end_date,
            is_active,
        ):
            semester = Semester.query.filter_by(name=name, academic_year=academic_year).first()
            if semester is None:
                semester = Semester(
                    name=name,
                    academic_year=academic_year,
                    start_date=start_date,
                    end_date=end_date,
                    registration_start_date=registration_start_date,
                    registration_end_date=registration_end_date,
                    is_active=is_active
                )
                db.session.add(semester)
                db.session.flush()
            else:
                # update dates to match seed (idempotent)
                semester.start_date = start_date
                semester.end_date = end_date
                semester.registration_start_date = registration_start_date
                semester.registration_end_date = registration_end_date
                semester.is_active = is_active

            return semester

        def get_or_create_major_registration_window(
            semester,
            major,
            registration_start_date,
            registration_end_date,
        ):
            window = MajorRegistrationWindow.query.filter_by(
                semester_id=semester.id,
                major=major
            ).first()
            if window is None:
                window = MajorRegistrationWindow(
                    semester_id=semester.id,
                    major=major,
                    registration_start_date=registration_start_date,
                    registration_end_date=registration_end_date,
                )
                db.session.add(window)
                db.session.flush()
            else:
                window.registration_start_date = registration_start_date
                window.registration_end_date = registration_end_date

            return window

        def get_or_create_course(code, name, credits):
            course = Course.query.filter_by(code=code).first()
            if course is None:
                course = Course(
                    code=code,
                    name=name,
                    credits=credits
                )
                db.session.add(course)
                db.session.flush()
            return course

        def get_or_create_room(code, capacity=50):
            room = Room.query.filter_by(code=code).first()
            if room is None:
                room = Room(
                    code=code,
                    capacity=capacity
                )
                db.session.add(room)
                db.session.flush()
            return room

        def get_or_create_class(
            course,
            semester,
            class_code,
            max_students=50,
            current_students=0,
            status=CourseClassStatus.OPEN
        ):
            course_class = CourseClass.query.filter_by(class_code=class_code).first()
            if course_class is None:
                course_class = CourseClass(
                    course_id=course.id,
                    semester_id=semester.id,
                    class_code=class_code,
                    max_students=max_students,
                    current_students=current_students,
                    status=status
                )
                db.session.add(course_class)
                db.session.flush()
            return course_class

        def get_or_create_schedule(
            course_class,
            room,
            day_of_week,
            start_period,
            end_period
        ):
            schedule = ClassSchedule.query.filter_by(
                course_class_id=course_class.id,
                day_of_week=day_of_week,
                start_period=start_period,
                end_period=end_period
            ).first()

            if schedule is None:
                schedule = ClassSchedule(
                    course_class_id=course_class.id,
                    room_id=room.id,
                    day_of_week=day_of_week,
                    start_period=start_period,
                    end_period=end_period
                )
                db.session.add(schedule)
                db.session.flush()

            return schedule

        def get_or_create_completed_course(
            student,
            course,
            semester,
            final_score=8.0,
            status=CompletedCourseStatus.PASSED
        ):
            completed = CompletedCourse.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).first()

            if completed is None:
                completed = CompletedCourse(
                    student_id=student.id,
                    course_id=course.id,
                    semester_id=semester.id,
                    final_score=final_score,
                    status=status
                )
                db.session.add(completed)
                db.session.flush()

            return completed

        def get_or_create_prerequisite(course, prerequisite_course):
            pr = CoursePrerequisite.query.filter_by(
                course_id=course.id,
                prerequisite_course_id=prerequisite_course.id
            ).first()

            if pr is None:
                pr = CoursePrerequisite(
                    course_id=course.id,
                    prerequisite_course_id=prerequisite_course.id
                )
                db.session.add(pr)
                db.session.flush()

            return pr

        # =====================================================
        # 1. USERS
        # =====================================================

        admin_user = get_or_create_user(
            username="admin01",
            password="123456",
            role=UserRole.ADMIN,
            active=True
        )

        student_user = get_or_create_user(
            username="student01",
            password="123456",
            role=UserRole.STUDENT,
            active=True
        )

        student = get_or_create_student(
            user=student_user,
            student_code="SV001",
            full_name="Nguyen Van Student",
            major="Information Technology"
        )

        student2_user = get_or_create_user(
            username="student02",
            password="123456",
            role=UserRole.STUDENT,
            active=True
        )

        student2 = get_or_create_student(
            user=student2_user,
            student_code="SV002",
            full_name="Tran Thi Student",
            major="Business Administration"
        )

        student3_user = get_or_create_user(
            username="student03",
            password="123456",
            role=UserRole.STUDENT,
            active=True
        )

        student3 = get_or_create_student(
            user=student3_user,
            student_code="SV003",
            full_name="Le Van Student",
            major="Digital Design"
        )

        locked_user = get_or_create_user(
            username="locked01",
            password="123456",
            role=UserRole.STUDENT,
            active=False
        )

        # =====================================================
        # 2. SEMESTERS
        # =====================================================

        # Create two primary semesters for the application per new requirement
        # Semester 1 (previously used to store completed courses)
        hk1 = get_or_create_semester(
            name="HK I",
            academic_year="2026",
            start_date=today - timedelta(days=200),
            end_date=today - timedelta(days=60),
            registration_start_date=today - timedelta(days=250),
            registration_end_date=today - timedelta(days=200),
            is_active=False,
        )

        # Semester 2 (active, open for registration)
        hk2 = get_or_create_semester(
            name="HK II",
            academic_year="2026",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=100),
            registration_start_date=today - timedelta(days=10),
            registration_end_date=today + timedelta(days=20),
            is_active=True,
        )

        active_semester = hk2
        expired_semester = hk1
        future_semester = None

        # Registration windows by major for active semester
        get_or_create_major_registration_window(
            semester=active_semester,
            major="Information Technology",
            registration_start_date=today - timedelta(days=1),
            registration_end_date=today + timedelta(days=20),
        )
        get_or_create_major_registration_window(
            semester=active_semester,
            major="Business Administration",
            registration_start_date=today - timedelta(days=30),
            registration_end_date=today - timedelta(days=1),
        )
        get_or_create_major_registration_window(
            semester=active_semester,
            major="Digital Design",
            registration_start_date=today + timedelta(days=5),
            registration_end_date=today + timedelta(days=25),
        )

        # =====================================================
        # 3. ROOMS
        # =====================================================

        room_a101 = get_or_create_room("A101")
        room_b202 = get_or_create_room("B202")
        room_c303 = get_or_create_room("C303")
        room_d404 = get_or_create_room("D404")

        # =====================================================
        # 4. COURSES
        # =====================================================

        # 2 môn sinh viên đã học
        course_completed_1 = get_or_create_course(
            code="ITEC1401",
            name="Nhập môn lập trình",
            credits=3
        )

        course_completed_2 = get_or_create_course(
            code="ITEC2501",
            name="Kỹ thuật lập trình",
            credits=3
        )

        # 1 môn đã học khác dùng làm điều kiện tiên quyết cho môn mới
        course_prereq_new = get_or_create_course(
            code="ITEC1501",
            name="Nhập môn hệ thống máy tính",
            credits=3
        )

        # 2 môn hết hạn đăng ký học phần
        course_expired_1 = get_or_create_course(
            code="ITEC2601",
            name="Cấu trúc dữ liệu",
            credits=3
        )

        course_expired_2 = get_or_create_course(
            code="ITEC2602",
            name="Giải thuật",
            credits=3
        )

        # 2 môn lớp học phần đã đủ số lượng
        course_full_1 = get_or_create_course(
            code="ITEC4501",
            name="Kiểm thử phần mềm",
            credits=3
        )

        course_full_2 = get_or_create_course(
            code="ITEC4502",
            name="Đảm bảo chất lượng phần mềm",
            credits=3
        )

        # 10 môn còn lại đăng ký được
        course_open_1 = get_or_create_course(
            code="ITEC2504",
            name="Lập trình hướng đối tượng",
            credits=4
        )

        course_open_2 = get_or_create_course(
            code="MATH1201",
            name="Toán cao cấp",
            credits=3
        )

        course_open_3 = get_or_create_course(
            code="ITEC2201",
            name="Cơ sở dữ liệu",
            credits=3
        )

        course_open_4 = get_or_create_course(
            code="GEN1001",
            name="Kỹ năng mềm",
            credits=2
        )

        course_open_5 = get_or_create_course(
            code="ITEC3301",
            name="Mạng máy tính",
            credits=3
        )

        course_open_6 = get_or_create_course(
            code="ITEC3302",
            name="Hệ điều hành",
            credits=3
        )

        course_open_7 = get_or_create_course(
            code="ITEC4401",
            name="Trí tuệ nhân tạo",
            credits=3
        )

        course_open_8 = get_or_create_course(
            code="ITEC4402",
            name="An toàn thông tin",
            credits=3
        )

        course_open_9 = get_or_create_course(
            code="ENG2001",
            name="Tiếng Anh chuyên ngành",
            credits=2
        )

        course_open_10 = get_or_create_course(
            code="GEN0001",
            name="Sinh hoạt đầu khóa",
            credits=1
        )

        # Course used to test "before registration start" on UI
        course_future = get_or_create_course(
            code="ITECFUT1",
            name="Môn chưa mở đăng ký",
            credits=3
        )

        # Course with two classes to test "already registered in another class"
        course_dup = get_or_create_course(
            code="ITECDUP1",
            name="Môn duplicate",
            credits=3
        )

        # 2 lớp trùng lịch để test
        course_conflict_1 = get_or_create_course(
            code="ITEC5001",
            name="Phát triển ứng dụng web",
            credits=3
        )

        course_conflict_2 = get_or_create_course(
            code="ITEC5002",
            name="Bảo mật ứng dụng",
            credits=3
        )

        # Môn mới cần điều kiện tiên quyết để test đăng ký thành công
        course_prereq_target = get_or_create_course(
            code="ITEC3503",
            name="Phát triển hệ thống",
            credits=3
        )

        # =====================================================
        # 5. COURSE CLASSES
        # =====================================================

        # 2 lớp thuộc môn sinh viên đã học (assign to HK I as completed courses)
        class_completed_1 = get_or_create_class(
            course=course_completed_1,
            semester=hk1,
            class_code="ITEC1401-HK1",
            max_students=50,
            current_students=0
        )

        class_completed_2 = get_or_create_class(
            course=course_completed_2,
            semester=hk1,
            class_code="ITEC2501-HK1",
            max_students=50,
            current_students=0
        )

        class_prereq_new = get_or_create_class(
            course=course_prereq_new,
            semester=hk1,
            class_code="ITEC1501-HK1",
            max_students=50,
            current_students=0
        )

        # 2 lớp ở HK II cho đúng các môn sinh viên đã học ở HK I
        # dùng để test chức năng không cho đăng ký lại môn đã hoàn thành
        class_completed_1_hk2 = get_or_create_class(
            course=course_completed_1,
            semester=hk2,
            class_code="ITEC1401-HK2",
            max_students=50,
            current_students=0
        )

        class_completed_2_hk2 = get_or_create_class(
            course=course_completed_2,
            semester=hk2,
            class_code="ITEC2501-HK2",
            max_students=50,
            current_students=0
        )

        # 2 lớp đã hết hạn đăng ký học phần (place them in hk2 but with registration window expired by major window)
        class_expired_1 = get_or_create_class(
            course=course_expired_1,
            semester=hk2,
            class_code="ITEC2601-EXPIRED",
            max_students=50,
            current_students=0
        )

        class_expired_2 = get_or_create_class(
            course=course_expired_2,
            semester=hk2,
            class_code="ITEC2602-EXPIRED",
            max_students=50,
            current_students=0
        )

        # 2 lớp học phần đã đủ số lượng
        class_full_1 = get_or_create_class(
            course=course_full_1,
            semester=hk2,
            class_code="ITEC4501-FULL",
            max_students=50,
            current_students=50
        )

        class_full_2 = get_or_create_class(
            course=course_full_2,
            semester=hk2,
            class_code="ITEC4502-FULL",
            max_students=50,
            current_students=50
        )

        # 10 lớp còn lại đăng ký được (assign to HK II active)
        class_open_1 = get_or_create_class(
            course=course_open_1,
            semester=hk2,
            class_code="ITEC2504-01",
            max_students=50,
            current_students=0
        )

        class_open_2 = get_or_create_class(
            course=course_open_2,
            semester=hk2,
            class_code="MATH1201-01",
            max_students=50,
            current_students=0
        )

        class_open_3 = get_or_create_class(
            course=course_open_3,
            semester=hk2,
            class_code="ITEC2201-01",
            max_students=50,
            current_students=0
        )

        class_open_4 = get_or_create_class(
            course=course_open_4,
            semester=hk2,
            class_code="GEN1001-01",
            max_students=50,
            current_students=0
        )

        class_open_5 = get_or_create_class(
            course=course_open_5,
            semester=hk2,
            class_code="ITEC3301-01",
            max_students=50,
            current_students=0
        )

        class_open_6 = get_or_create_class(
            course=course_open_6,
            semester=hk2,
            class_code="ITEC3302-01",
            max_students=50,
            current_students=0
        )

        class_open_7 = get_or_create_class(
            course=course_open_7,
            semester=hk2,
            class_code="ITEC4401-01",
            max_students=50,
            current_students=0
        )

        class_open_8 = get_or_create_class(
            course=course_open_8,
            semester=hk2,
            class_code="ITEC4402-01",
            max_students=50,
            current_students=0
        )

        class_open_9 = get_or_create_class(
            course=course_open_9,
            semester=hk2,
            class_code="ENG2001-01",
            max_students=50,
            current_students=0
        )

        class_open_10 = get_or_create_class(
            course=course_open_10,
            semester=hk2,
            class_code="GEN0001-01",
            max_students=50,
            current_students=0
        )

        # Optionally create a future class in none (skip if future_semester is None)
        if future_semester is not None:
            class_future = get_or_create_class(
                course=course_future,
                semester=future_semester,
                class_code="ITECFUT1-01",
                max_students=50,
                current_students=0
            )

        # Two classes for the same course in active semester to test duplicate-course registration
        class_dup_1 = get_or_create_class(
            course=course_dup,
            semester=hk2,
            class_code="ITECDUP1-01",
            max_students=50,
            current_students=0
        )

        class_dup_2 = get_or_create_class(
            course=course_dup,
            semester=hk2,
            class_code="ITECDUP1-02",
            max_students=50,
            current_students=0
        )

        # 2 lớp trùng lịch
        class_conflict_1 = get_or_create_class(
            course=course_conflict_1,
            semester=hk2,
            class_code="ITEC5001-CONFLICT",
            max_students=50,
            current_students=0
        )

        class_conflict_2 = get_or_create_class(
            course=course_conflict_2,
            semester=hk2,
            class_code="ITEC5002-CONFLICT",
            max_students=50,
            current_students=0
        )

        class_prereq_target = get_or_create_class(
            course=course_prereq_target,
            semester=hk2,
            class_code="ITEC3503-01",
            max_students=50,
            current_students=0
        )

        # =====================================================
        # 6. SCHEDULES
        # =====================================================
        # Các lớp đăng ký được được xếp lịch không trùng nhau
        # để sinh viên có thể đăng ký đủ 12, 25 tín chỉ.

        # 2 lớp thuộc môn đã học
        get_or_create_schedule(class_completed_1, room_a101, 2, 1, 3)
        get_or_create_schedule(class_completed_2, room_b202, 2, 4, 6)

        # Lớp điều kiện tiên quyết đã học (HK I)
        get_or_create_schedule(class_prereq_new, room_a101, 1, 1, 3)

        # 2 lớp HK II cho các môn đã học (không trùng lịch với các lớp còn lại)
        get_or_create_schedule(class_completed_1_hk2, room_c303, 1, 1, 3)
        get_or_create_schedule(class_completed_2_hk2, room_d404, 1, 4, 6)

        # 2 lớp hết hạn đăng ký
        get_or_create_schedule(class_expired_1, room_c303, 3, 1, 3)
        get_or_create_schedule(class_expired_2, room_d404, 3, 4, 6)

        # 2 lớp đầy
        get_or_create_schedule(class_full_1, room_a101, 4, 1, 3)
        get_or_create_schedule(class_full_2, room_b202, 4, 4, 6)

        # 10 lớp đăng ký được
        get_or_create_schedule(class_open_1, room_a101, 2, 7, 10)
        get_or_create_schedule(class_open_2, room_b202, 3, 7, 9)
        get_or_create_schedule(class_open_3, room_c303, 4, 7, 9)
        get_or_create_schedule(class_open_4, room_d404, 5, 1, 2)
        get_or_create_schedule(class_open_5, room_a101, 5, 3, 5)
        get_or_create_schedule(class_open_6, room_b202, 5, 6, 8)
        get_or_create_schedule(class_open_7, room_c303, 6, 1, 3)
        get_or_create_schedule(class_open_8, room_d404, 6, 4, 6)
        get_or_create_schedule(class_open_9, room_a101, 7, 1, 2)
        get_or_create_schedule(class_open_10, room_b202, 7, 4, 4)

        # 2 lớp trùng lịch (overlapping với class_open_5: Thứ 5, tiết 3-5)
        # không trùng với nhau nhưng cả 2 đều trùng với class_open_5
        get_or_create_schedule(class_conflict_1, room_c303, 5, 1, 3)  # Thứ 5, tiết 1-3 (trùng tiết 3)
        get_or_create_schedule(class_conflict_2, room_d404, 5, 4, 6)  # Thứ 5, tiết 4-6 (trùng tiết 4-5)

        # Lớp môn mới cần tiên quyết, chọn lịch riêng để student01 có thể đăng ký
        get_or_create_schedule(class_prereq_target, room_b202, 1, 7, 9)

        # schedule for future class (any slot)
        try:
            get_or_create_schedule(class_future, room_a101, 2, 1, 3)
        except Exception:
            pass

        # schedules for duplicate-course classes (non-conflicting)
        try:
            get_or_create_schedule(class_dup_1, room_b202, 3, 1, 3)
            get_or_create_schedule(class_dup_2, room_c303, 4, 1, 3)
        except Exception:
            pass

        # =====================================================
        # 7. COMPLETED COURSES
        # =====================================================
        # student01 đã học đúng 2 môn:
        # - ITEC1401
        # - ITEC2501

        get_or_create_completed_course(
            student=student,
            course=course_completed_1,
            semester=hk1,
            final_score=8.0,
            status=CompletedCourseStatus.PASSED
        )

        get_or_create_completed_course(
            student=student,
            course=course_completed_2,
            semester=hk1,
            final_score=8.5,
            status=CompletedCourseStatus.PASSED
        )

        get_or_create_completed_course(
            student=student,
            course=course_prereq_new,
            semester=hk1,
            final_score=8.2,
            status=CompletedCourseStatus.PASSED
        )

        # =====================================================
        # 8. PREREQUISITES (seed some prerequisites for testing)
        # =====================================================
        # Make ITEC2504 (Lập trình hướng đối tượng) require ITEC1401
        try:
            get_or_create_prerequisite(course_open_1, course_completed_1)
        except Exception:
            pass

        # Make ITEC2201 (Cơ sở dữ liệu) require ITEC2501
        try:
            get_or_create_prerequisite(course_open_3, course_completed_2)
        except Exception:
            pass

        # Môn mới ITEC3503 cần ITEC1501, và student01 đã học ITEC1501
        try:
            get_or_create_prerequisite(course_prereq_target, course_prereq_new)
        except Exception:
            pass

        # Add an extra prerequisite for testing: make ITEC4401 (Trí tuệ nhân tạo)
        # require ITEC3301 (Mạng máy tính) which student01 has NOT completed.
        # This allows testing missing prerequisites for student01 without using student02.
        try:
            get_or_create_prerequisite(course_open_7, course_open_5)
        except Exception:
            pass

        # =====================================================
        # 9. SOME INITIAL ENROLLMENTS (to test registered list / cancel flow)
        # =====================================================
        def get_or_create_enrollment(student, course_class, semester):
            en = Enrollment.query.filter_by(
                student_id=student.id,
                course_class_id=course_class.id,
                semester_id=semester.id
            ).first()

            if en is None:
                en = Enrollment(
                    student_id=student.id,
                    course_class_id=course_class.id,
                    semester_id=semester.id,
                    status=EnrollmentStatus.REGISTERED
                )
                db.session.add(en)
                # increment current_students
                try:
                    course_class.current_students = (course_class.current_students or 0) + 1
                except Exception:
                    pass
                db.session.flush()

            return en

        # Enroll student01 into a few classes for baseline testing
        try:
            # Create some initial enrollments for student in HK II
            get_or_create_enrollment(student, class_open_1, hk2)
            get_or_create_enrollment(student, class_open_2, hk2)
            # Enroll into one duplicate section to test duplicate-course behavior
            try:
                get_or_create_enrollment(student, class_dup_1, hk2)
            except Exception:
                pass
        except Exception:
            pass

        # Make one enrollment have a midterm score so it's not cancellable via UI
        try:
            en_mid = Enrollment.query.filter_by(
                student_id=student.id,
                course_class_id=class_open_1.id,
                semester_id=hk2.id,
                status=EnrollmentStatus.REGISTERED
            ).first()
            if en_mid is not None:
                en_mid.midterm_score = 8.0
                en_mid.final_score = None
                db.session.add(en_mid)
        except Exception:
            pass

        # student02 belongs to major with expired registration window
        # and has exactly 12 credits already registered (4 + 3 + 3 + 2).
        try:
            get_or_create_enrollment(student2, class_open_1, active_semester)
            get_or_create_enrollment(student2, class_open_2, active_semester)
            get_or_create_enrollment(student2, class_open_3, active_semester)
            get_or_create_enrollment(student2, class_open_4, active_semester)
        except Exception:
            pass

        # student03 is in a major that has not reached registration window yet
        # and intentionally has no initial enrollments.

        db.session.commit()

        print("Seed data created successfully.")


if __name__ == "__main__":
    app.run(debug=True)
