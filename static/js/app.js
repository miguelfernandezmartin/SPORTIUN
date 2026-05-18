document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('routineSearch');
    const routineCards = document.querySelectorAll('.routine-item');

    searchInput.addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase();

        routineCards.forEach(card => {
            // Buscamos dentro del título y la descripción
            const title = card.querySelector('.routine-name').textContent.toLowerCase();
            const description = card.querySelector('.card-text').textContent.toLowerCase();

            if (title.includes(term) || description.includes(term)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});