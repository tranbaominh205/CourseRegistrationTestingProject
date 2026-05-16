from datetime import date

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
    CourseClassStatus,
    CompletedCourseStatus,
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
        # =====================================================
        # 1. USERS
        # =====================================================

        admin = User.query.filter_by(username="admin01").first()
        if admin is None:
            admin = User(
                username="admin01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.ADMIN,
                is_active_account=True
            )
            db.session.add(admin)

        student_user = User.query.filter_by(username="student01").first()
        if student_user is None:
            student_user = User(
                username="student01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=True
            )
            db.session.add(student_user)
            db.session.flush()

        student = Student.query.filter_by(student_code="SV001").first()
        if student is None:
            student = Student(
                user_id=student_user.id,
                student_code="SV001",
                full_name="Nguyen Van Student",
                major="Information Technology"
            )
            db.session.add(student)

        student2_user = User.query.filter_by(username="student02").first()
        if student2_user is None:
            student2_user = User(
                username="student02",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=True
            )
            db.session.add(student2_user)
            db.session.flush()

        student2 = Student.query.filter_by(student_code="SV002").first()
        if student2 is None:
            student2 = Student(
                user_id=student2_user.id,
                student_code="SV002",
                full_name="Tran Thi Student",
                major="Information Technology"
            )
            db.session.add(student2)

        locked_user = User.query.filter_by(username="locked01").first()
        if locked_user is None:
            locked_user = User(
                username="locked01",
                password_hash=generate_password_hash("123456"),
                role=UserRole.STUDENT,
                is_active_account=False
            )
            db.session.add(locked_user)

        db.session.commit()

        # =====================================================
        # 2. SEMESTERS
        # =====================================================

        active_semester = Semester.query.filter_by(name="HK1 2026").first()
        if active_semester is None:
            active_semester = Semester(
                name="HK1 2026",
                start_date=date(2026, 9, 1),
                registration_start_date=date(2026, 8, 1),
                registration_end_date=date(2026, 8, 25),
                cancel_deadline=date(2026, 9, 15),
                is_active=True
            )
            db.session.add(active_semester)

        expired_semester = Semester.query.filter_by(name="HK Expired").first()
        if expired_semester is None:
            expired_semester = Semester(
                name="HK Expired",
                start_date=date(2026, 1, 1),
                registration_start_date=date(2025, 12, 1),
                registration_end_date=date(2025, 12, 15),
                cancel_deadline=date(2026, 1, 15),
                is_active=False
            )
            db.session.add(expired_semester)

        db.session.commit()

        # =====================================================
        # 3. COURSES
        # =====================================================

        course_python = Course.query.filter_by(code="ITEC1401").first()
        if course_python is None:
            course_python = Course(
                code="ITEC1401",
                name="Nhập môn lập trình",
                credits=3
            )
            db.session.add(course_python)

        course_oop = Course.query.filter_by(code="ITEC2504").first()
        if course_oop is None:
            course_oop = Course(
                code="ITEC2504",
                name="Lập trình hướng đối tượng",
                credits=4
            )
            db.session.add(course_oop)

        course_web = Course.query.filter_by(code="ITEC3401").first()
        if course_web is None:
            course_web = Course(
                code="ITEC3401",
                name="Lập trình Web",
                credits=3
            )
            db.session.add(course_web)

        course_testing = Course.query.filter_by(code="ITEC4501").first()
        if course_testing is None:
            course_testing = Course(
                code="ITEC4501",
                name="Kiểm thử phần mềm",
                credits=3
            )
            db.session.add(course_testing)

        course_database = Course.query.filter_by(code="ITEC3301").first()
        if course_database is None:
            course_database = Course(
                code="ITEC3301",
                name="Cơ sở dữ liệu",
                credits=3
            )
            db.session.add(course_database)

        db.session.commit()

        # =====================================================
        # 4. PREREQUISITES
        #    Lập trình Web cần Lập trình hướng đối tượng
        # =====================================================

        prerequisite = CoursePrerequisite.query.filter_by(
            course_id=course_web.id,
            prerequisite_course_id=course_oop.id
        ).first()

        if prerequisite is None:
            prerequisite = CoursePrerequisite(
                course_id=course_web.id,
                prerequisite_course_id=course_oop.id
            )
            db.session.add(prerequisite)

        db.session.commit()

        # =====================================================
        # 5. ROOMS
        # =====================================================

        room_a101 = Room.query.filter_by(code="A101").first()
        if room_a101 is None:
            room_a101 = Room(
                code="A101",
                capacity=50
            )
            db.session.add(room_a101)

        room_b202 = Room.query.filter_by(code="B202").first()
        if room_b202 is None:
            room_b202 = Room(
                code="B202",
                capacity=50
            )
            db.session.add(room_b202)

        room_c303 = Room.query.filter_by(code="C303").first()
        if room_c303 is None:
            room_c303 = Room(
                code="C303",
                capacity=50
            )
            db.session.add(room_c303)

        db.session.commit()

        # =====================================================
        # 6. COURSE CLASSES - ACTIVE SEMESTER
        # =====================================================

        class_python = CourseClass.query.filter_by(class_code="ITEC1401-01").first()
        if class_python is None:
            class_python = CourseClass(
                course_id=course_python.id,
                semester_id=active_semester.id,
                class_code="ITEC1401-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_python)

        class_oop = CourseClass.query.filter_by(class_code="ITEC2504-01").first()
        if class_oop is None:
            class_oop = CourseClass(
                course_id=course_oop.id,
                semester_id=active_semester.id,
                class_code="ITEC2504-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_oop)

        class_web = CourseClass.query.filter_by(class_code="ITEC3401-01").first()
        if class_web is None:
            class_web = CourseClass(
                course_id=course_web.id,
                semester_id=active_semester.id,
                class_code="ITEC3401-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_web)

        class_testing_full = CourseClass.query.filter_by(class_code="ITEC4501-FULL").first()
        if class_testing_full is None:
            class_testing_full = CourseClass(
                course_id=course_testing.id,
                semester_id=active_semester.id,
                class_code="ITEC4501-FULL",
                max_students=50,
                current_students=50,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_testing_full)

        class_database_no_conflict = CourseClass.query.filter_by(class_code="ITEC3301-01").first()
        if class_database_no_conflict is None:
            class_database_no_conflict = CourseClass(
                course_id=course_database.id,
                semester_id=active_semester.id,
                class_code="ITEC3301-01",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_database_no_conflict)

        db.session.commit()

        # =====================================================
        # 7. COURSE CLASSES - EXPIRED SEMESTER
        # =====================================================

        class_expired = CourseClass.query.filter_by(class_code="ITEC3301-EXPIRED").first()
        if class_expired is None:
            class_expired = CourseClass(
                course_id=course_database.id,
                semester_id=expired_semester.id,
                class_code="ITEC3301-EXPIRED",
                max_students=50,
                current_students=0,
                status=CourseClassStatus.OPEN
            )
            db.session.add(class_expired)

        db.session.commit()

        # =====================================================
        # 8. SCHEDULES
        # =====================================================
        # ITEC1401-01: dùng để test "môn đã học rồi"
        # Thứ 2, tiết 1-3, phòng A101

        if ClassSchedule.query.filter_by(course_class_id=class_python.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_python.id,
                room_id=room_a101.id,
                day_of_week=2,
                start_period=1,
                end_period=3
            ))

        # ITEC2504-01: lớp hợp lệ, không trùng lịch với ITEC1401-01
        # Thứ 3, tiết 1-3, phòng B202

        if ClassSchedule.query.filter_by(course_class_id=class_oop.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_oop.id,
                room_id=room_b202.id,
                day_of_week=3,
                start_period=1,
                end_period=3
            ))

        # ITEC3401-01: trùng lịch với ITEC1401-01
        # Thứ 2, tiết 2-4, phòng B202
        # Cố ý khác phòng để chứng minh ràng buộc "trùng lịch sinh viên"
        # không phụ thuộc vào phòng học.

        if ClassSchedule.query.filter_by(course_class_id=class_web.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_web.id,
                room_id=room_b202.id,
                day_of_week=2,
                start_period=2,
                end_period=4
            ))

        # ITEC4501-FULL: lớp đầy
        # Thứ 4, tiết 1-3, phòng A101

        if ClassSchedule.query.filter_by(course_class_id=class_testing_full.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_testing_full.id,
                room_id=room_a101.id,
                day_of_week=4,
                start_period=1,
                end_period=3
            ))

        # ITEC3301-01: lớp không trùng lịch, dùng để test đăng ký thêm lớp hợp lệ
        # Thứ 5, tiết 1-3, phòng C303

        if ClassSchedule.query.filter_by(course_class_id=class_database_no_conflict.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_database_no_conflict.id,
                room_id=room_c303.id,
                day_of_week=5,
                start_period=1,
                end_period=3
            ))

        # ITEC3301-EXPIRED: lớp thuộc học kỳ đã hết hạn đăng ký
        # Dùng để manual test deadline.

        if ClassSchedule.query.filter_by(course_class_id=class_expired.id).first() is None:
            db.session.add(ClassSchedule(
                course_class_id=class_expired.id,
                room_id=room_c303.id,
                day_of_week=6,
                start_period=1,
                end_period=3
            ))

        db.session.commit()

        # =====================================================
        # 9. COMPLETED COURSES
        #    student01 đã học Nhập môn lập trình
        # =====================================================

        student = Student.query.filter_by(student_code="SV001").first()

        if student is not None:
            completed_python = CompletedCourse.query.filter_by(
                student_id=student.id,
                course_id=course_python.id
            ).first()

            if completed_python is None:
                completed_python = CompletedCourse(
                    student_id=student.id,
                    course_id=course_python.id,
                    semester_id=active_semester.id,
                    final_score=8.0,
                    status=CompletedCourseStatus.PASSED
                )
                db.session.add(completed_python)

            # student01 đã học OOP để tuần 4 có thể test môn tiên quyết:
            # Nếu đã học OOP thì được đăng ký Lập trình Web,
            # nhưng tuần 3 vẫn có thể dùng class_web để test trùng lịch nếu đã đăng ký class_python trước.
            completed_oop = CompletedCourse.query.filter_by(
                student_id=student.id,
                course_id=course_oop.id
            ).first()

            if completed_oop is None:
                completed_oop = CompletedCourse(
                    student_id=student.id,
                    course_id=course_oop.id,
                    semester_id=active_semester.id,
                    final_score=8.5,
                    status=CompletedCourseStatus.PASSED
                )
                db.session.add(completed_oop)

        db.session.commit()

        print("Seed data created successfully.")
        print("Accounts:")
        print("- admin01 / 123456")
        print("- student01 / 123456")
        print("- student02 / 123456")
        print("- locked01 / 123456")
        print("Main test classes:")
        print("- ITEC2504-01: valid class")
        print("- ITEC1401-01: completed course class")
        print("- ITEC3401-01: schedule conflict class")
        print("- ITEC4501-FULL: full class")
        print("- ITEC3301-01: non-conflict class")
        print("- ITEC3301-EXPIRED: expired registration class")


if __name__ == "__main__":
    app.run(debug=True)