// Dark Mode Theme Toggle
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const body = document.body;
    
    // Get saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    setTheme(savedTheme);
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', function() {
        const currentTheme = htmlElement.getAttribute('data-bs-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    });
    
    function setTheme(theme) {
        // Update HTML attribute
        htmlElement.setAttribute('data-bs-theme', theme);
        body.setAttribute('data-bs-theme', theme);
        
        // Update localStorage
        localStorage.setItem('theme', theme);
        
        // Update button icon
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.classList.remove('bi-moon-stars');
            icon.classList.add('bi-sun');
            themeToggle.title = 'Switch to light mode';
        } else {
            icon.classList.remove('bi-sun');
            icon.classList.add('bi-moon-stars');
            themeToggle.title = 'Switch to dark mode';
        }
    }
    
    // Respect system preference if no saved theme
    if (!localStorage.getItem('theme')) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
});
