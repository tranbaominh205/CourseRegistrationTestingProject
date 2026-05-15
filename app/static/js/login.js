/**
 * Login Page JavaScript
 * Handles password visibility toggle
 */

document.addEventListener('DOMContentLoaded', function() {
    setupPasswordToggle();
    setupTopNavigation();
});

/**
 * Setup password visibility toggle
 */
function setupPasswordToggle() {
    const toggleBtn = document.getElementById('togglePasswordBtn');
    const passwordInput = document.getElementById('password');
    const iconEye = toggleBtn.querySelector('.icon-eye');
    const iconEyeOff = toggleBtn.querySelector('.icon-eye-off');

    if (!toggleBtn || !passwordInput) return;

    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();

        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';

        // Toggle icon visibility
        if (isPassword) {
            iconEye.style.display = 'none';
            iconEyeOff.style.display = 'block';
        } else {
            iconEye.style.display = 'block';
            iconEyeOff.style.display = 'none';
        }
    });
}

/**
 * Setup top navigation button actions
 */
function setupTopNavigation() {
    const registerBtn = document.getElementById('registerBtn');
    const backToHomeBtn = document.getElementById('backToHomeBtn');

    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            window.location.href = '/register';
        });
    }

    if (backToHomeBtn) {
        backToHomeBtn.addEventListener('click', function() {
            window.location.href = '/';
        });
    }
}