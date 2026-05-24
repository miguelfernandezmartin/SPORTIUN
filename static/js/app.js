document.addEventListener('DOMContentLoaded', function () {

    // ── Búsqueda en lista de rutinas ──────────────────────────────────────
    const searchInput = document.getElementById('routineSearch');
    if (searchInput) {
        const routineCards = document.querySelectorAll('.routine-item');
        searchInput.addEventListener('input', function (e) {
            const term = e.target.value.toLowerCase();
            routineCards.forEach(card => {
                const title = card.querySelector('.routine-name')?.textContent.toLowerCase() || '';
                const desc  = card.querySelector('.card-text')?.textContent.toLowerCase()  || '';
                card.style.display = (title.includes(term) || desc.includes(term)) ? '' : 'none';
            });
        });
    }

    // ── Auto-dismiss alerts después de 4 s ───────────────────────────────
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 4000);
    });

    // ── Confirmación simple al hacer delete por link (clase js-confirm) ──
    document.querySelectorAll('.js-confirm').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.dataset.msg || '¿Seguro que quieres continuar?')) {
                e.preventDefault();
            }
        });
    });

});
