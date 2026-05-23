try:
    from locust import HttpUser, task, between
except ImportError:
    class HttpUser:
        client = None


    def task(weight=1):
        def decorator(func):
            return func

        return decorator


    def between(min_wait, max_wait):
        return (min_wait, max_wait)


class CourseRegistrationStudentUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.post(
            "/login",
            data={
                "username": "student01",
                "password": "123456"
            },
            name="POST /login"
        )

    @task(4)
    def view_class_list(self):
        self.client.get("/student/classes", name="GET /student/classes")

    @task(2)
    def view_student_dashboard(self):
        self.client.get("/student/dashboard", name="GET /student/dashboard")

    @task(1)
    def view_completed_courses(self):
        self.client.get("/student/completed", name="GET /student/completed")

    @task(1)
    def check_auth_status(self):
        self.client.get("/api/auth/status", name="GET /api/auth/status")


class CourseRegistrationAdminUser(HttpUser):
    wait_time = between(1, 3)
    weight = 1

    def on_start(self):
        self.client.post(
            "/login",
            data={
                "username": "admin01",
                "password": "123456"
            },
            name="POST /login admin"
        )

    @task(3)
    def view_admin_classes(self):
        self.client.get("/admin/classes", name="GET /admin/classes")

    @task(1)
    def view_create_class_form(self):
        self.client.get("/admin/classes/create", name="GET /admin/classes/create")