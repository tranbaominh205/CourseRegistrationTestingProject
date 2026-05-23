import os
import time
from pathlib import Path
from shutil import which

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://127.0.0.1:5000")


def resolve_chromedriver_path():
    env_path = os.getenv("CHROMEDRIVER_PATH")
    project_root = Path(__file__).resolve().parents[2]

    candidates = []
    if env_path:
        candidates.append(Path(env_path))

    candidates.extend(
        [
            project_root / "chromedriver.exe",
            project_root / ".venv" / "chromedriver.exe",
            project_root / ".venv" / "Scripts" / "chromedriver.exe",
            project_root / "venv" / "chromedriver.exe",
            project_root / "venv" / "Scripts" / "chromedriver.exe",
        ]
    )

    system_path = which("chromedriver")
    if system_path:
        return system_path

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


@pytest.fixture
def driver():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1366,768")


    chromedriver_path = resolve_chromedriver_path()
    if chromedriver_path:
        browser = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
    else:
        browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )

    yield browser
    browser.quit()


def wait_text(driver, text, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(normalize-space(), '{text}')]")
        )
    )


def login(driver, username, password):
    driver.get(f"{BASE_URL}/login")

    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_input = driver.find_element(By.NAME, "password")

    username_input.clear()
    username_input.send_keys(username)

    password_input.clear()
    password_input.send_keys(password)

    driver.find_element(By.XPATH, "//button[contains(., 'ĐĂNG NHẬP') or contains(., 'Đăng nhập')]").click()


def test_login_page_displayed(driver):
    driver.get(f"{BASE_URL}/login")

    wait_text(driver, "Đăng nhập")
    wait_text(driver, "Mã sinh viên / Tên đăng nhập")
    wait_text(driver, "Mật khẩu")

    assert "login" in driver.current_url.lower()


def test_student_login_success_and_open_class_list(driver):
    login(driver, "student01", "123456")

    wait_text(driver, "Dashboard sinh viên")
    wait_text(driver, "Thông tin cá nhân sinh viên")

    driver.find_element(By.XPATH, "//a[contains(., 'Vào trang đăng ký')]").click()

    wait_text(driver, "Đăng ký học phần")
    wait_text(driver, "Danh sách lớp học phần")
    wait_text(driver, "Danh sách môn học đã đăng ký")

    assert "/student/classes" in driver.current_url


def test_login_fail_wrong_password(driver):
    login(driver, "student01", "sai_password")

    wait_text(driver, "Invalid username or password")

    assert "/login" in driver.current_url


def test_logged_in_student_back_to_login_redirects_dashboard(driver):
    login(driver, "student01", "123456")

    wait_text(driver, "Dashboard sinh viên")

    driver.get(f"{BASE_URL}/login")

    wait_text(driver, "Dashboard sinh viên")
    assert "/student/dashboard" in driver.current_url


def test_admin_login_success_open_admin_classes(driver):
    login(driver, "admin01", "123456")

    wait_text(driver, "QUẢN LÝ LỚP HỌC PHẦN")
    wait_text(driver, "Tạo lớp học phần")

    assert "/admin/classes" in driver.current_url


def test_student_cannot_access_admin_page(driver):
    login(driver, "student01", "123456")

    wait_text(driver, "Dashboard sinh viên")

    driver.get(f"{BASE_URL}/admin/classes")

    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert "Dashboard admin" not in page_text
    assert (
        "Không có quyền" in page_text
        or "Forbidden" in page_text
        or "Dashboard sinh viên" in page_text
        or "Đăng nhập" in page_text
        or driver.current_url != f"{BASE_URL}/admin/classes"
    )


def test_student_class_list_has_no_server_error(driver):
    login(driver, "student01", "123456")

    driver.get(f"{BASE_URL}/student/classes")

    wait_text(driver, "Đăng ký học phần")

    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert "Internal Server Error" not in page_text
    assert "Traceback" not in page_text
    assert "500 Internal Server Error" not in page_text


def test_logout_then_back_does_not_show_protected_dashboard(driver):
    login(driver, "student01", "123456")

    wait_text(driver, "Dashboard sinh viên")

    driver.get(f"{BASE_URL}/logout")
    wait_text(driver, "Đăng nhập")

    driver.back()
    time.sleep(1)

    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert "Dashboard sinh viên" not in page_text or "Đăng nhập" in page_text