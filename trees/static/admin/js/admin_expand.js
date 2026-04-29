/**
 * admin_expand.js
 * Automatically toggles admin view collapsable fields open.
 */

(function() {
    function openFieldsets() {
        const targets = document.querySelectorAll('fieldset.start-open details');
        
        targets.forEach(details => {
            details.open = true;
            
            details.classList.remove('collapsed');
            
            const summary = details.querySelector('summary');
            if (summary) {
                summary.setAttribute('aria-expanded', 'true');
            }
        });
    }

    // Run after the page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(openFieldsets, 200);
    });
})();