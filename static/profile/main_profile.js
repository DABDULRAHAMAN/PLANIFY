document.addEventListener('DOMContentLoaded', () => {
    const profilePhotoInput = document.getElementById('profile-photo-input');
    const profilePhotoPreview = document.querySelector('.profile-photo');

    // Update profile photo preview when a new image is selected
    profilePhotoInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                profilePhotoPreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
});