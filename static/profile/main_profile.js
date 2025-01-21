document.addEventListener('DOMContentLoaded', () => {
    const changePasswordBtn = document.getElementById('change-password-btn');
    const passwordFields = document.getElementById('password-fields');

    // Initially hide the password fields
    passwordFields.style.display = 'none';

    // Toggle password fields visibility
    changePasswordBtn.addEventListener('click', () => {
        if (passwordFields.style.display === 'none') {
            passwordFields.style.display = 'block';
            changePasswordBtn.textContent = 'Cancel Password Change';
        } else {
            passwordFields.style.display = 'none';
            changePasswordBtn.textContent = 'Change Password';
        }
    });
});
