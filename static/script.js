const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
	container.classList.remove("right-panel-active");
});
window.addEventListener("scroll", function() {
    if (window.scrollY > 1000) {
        $('.navbar').css('background-color','#060913');
    }
    else {
        $('.navbar').css('background-color','transparent')
    }
},false);