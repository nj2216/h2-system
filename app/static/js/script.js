// H2 System Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const a = document.getElementById('this_year');
    a.innerText = new Date().getFullYear();
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('form[action*="/delete"] button');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Table row selection
    const checkAllCheckbox = document.getElementById('checkAll');
    if (checkAllCheckbox) {
        checkAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="selected-items"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = checkAllCheckbox.checked;
            });
        });
    }

    // Format currency
    const currencyElements = document.querySelectorAll('[data-currency]');
    currencyElements.forEach(function(element) {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            element.textContent = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR'
            }).format(value);
        }
    });

    // Format dates
    const dateElements = document.querySelectorAll('[data-date]');
    dateElements.forEach(function(element) {
        const date = new Date(element.textContent);
        if (!isNaN(date.getTime())) {
            element.textContent = new Intl.DateTimeFormat('en-IN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }).format(date);
        }
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('searchForm').submit();
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Prevent double form submission
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        // Save original button text
        button.setAttribute('data-original-text', button.innerHTML);
        
        button.addEventListener('click', function(e) {
            // Check if form is valid before disabling
            const form = button.closest('form');
            if (form && !form.checkValidity()) {
                return; // Don't disable if form is invalid
            }
            
            // Only disable after form submission has started
            setTimeout(() => {
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }, 0);
        });
    });

    // Status badge colors
    const statusBadges = document.querySelectorAll('[data-status]');
    statusBadges.forEach(function(badge) {
        const status = badge.getAttribute('data-status').toLowerCase();
        badge.classList.remove('bg-secondary');
        
        switch(status) {
            case 'approved':
            case 'approved by h2':
            case 'good':
                badge.classList.add('bg-success');
                break;
            case 'rejected':
            case 'poor':
            case 'damaged':
                badge.classList.add('bg-danger');
                break;
            case 'pending':
                badge.classList.add('bg-warning', 'text-dark');
                break;
            case 'in progress':
                badge.classList.add('bg-info');
                break;
            default:
                badge.classList.add('bg-secondary');
        }
    });
});

// Utility Functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('Copied to clipboard!');
    });
}

function printDiv(divId) {
    const printContents = document.getElementById(divId).innerHTML;
    const originalContents = document.body.innerHTML;
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(value);
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    
    for (let i = 0; i < table.rows.length; i++) {
        let row = [];
        for (let j = 0; j < table.rows[i].cells.length; j++) {
            row.push(table.rows[i].cells[j].innerText);
        }
        csv.push(row.join(','));
    }
    
    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], {type: 'text/csv'});
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.download = filename;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
