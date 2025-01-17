// Adding click functionality to the carousel
const carousel = document.getElementById('carouselExample');

carousel.addEventListener('click', function(e) {
    const width = carousel.offsetWidth;
    const xPos = e.clientX;

    if (xPos > width / 2) {
        // Move to the next slide
        $('#carouselExample').carousel('next');
    } else {
        // Move to the previous slide
        $('#carouselExample').carousel('prev');
    }
});
