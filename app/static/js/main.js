// Main JavaScript file for University AI Batch Educational Platform

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Attendance checkboxes handling
    setupAttendanceCheckboxes();
    
    // Grade input handling
    setupGradeInputs();
    
    // Subject term dropdown
    setupSubjectTermDropdown();
    
    // Add animation to cards
    animateOnScroll();
    
    // Dark mode has been removed
    
    // Setup responsive tables
    setupResponsiveTables();
    
    // Setup search functionality
    setupSearch();
    
    // Setup chatbot auto-scroll
    setupChatAutoScroll();
    
    // Setup file upload preview
    setupFileUploadPreview();
});

// Animate elements when they come into view
function animateOnScroll() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animatedElements.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Dark mode functionality has been removed

// Make tables responsive
function setupResponsiveTables() {
    const tables = document.querySelectorAll('table:not(.no-responsive)');
    
    tables.forEach(table => {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-responsive';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    });
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const searchTarget = this.getAttribute('data-search-target');
        const items = document.querySelectorAll(searchTarget);
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
        
        // Show no results message if needed
        const noResults = document.getElementById('noSearchResults');
        if (noResults) {
            const visibleItems = document.querySelectorAll(`${searchTarget}:not([style*="display: none"])`);
            noResults.style.display = visibleItems.length === 0 ? 'block' : 'none';
        }
    });
}

// Auto-scroll chat to bottom
function setupChatAutoScroll() {
    const chatMessages = document.querySelector('.chat-messages');
    
    if (!chatMessages) return;
    
    // Scroll to bottom initially
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Observe for new messages
    const observer = new MutationObserver(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    observer.observe(chatMessages, { childList: true });
}

// File upload preview
function setupFileUploadPreview() {
    const fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    
    fileInputs.forEach(input => {
        const previewId = input.getAttribute('data-preview');
        const previewElement = document.getElementById(previewId);
        
        if (!previewElement) return;
        
        input.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    if (file.type.startsWith('image/')) {
                        // Image preview
                        previewElement.innerHTML = `<img src="${e.target.result}" class="img-fluid preview-image" alt="File preview">`;
                    } else if (file.type === 'application/pdf') {
                        // PDF icon
                        previewElement.innerHTML = `
                            <div class="file-preview-icon">
                                <i class="fas fa-file-pdf fa-3x text-danger"></i>
                                <p class="mt-2">${file.name}</p>
                            </div>
                        `;
                    } else {
                        // Generic file icon
                        previewElement.innerHTML = `
                            <div class="file-preview-icon">
                                <i class="fas fa-file fa-3x text-primary"></i>
                                <p class="mt-2">${file.name}</p>
                            </div>
                        `;
                    }
                };
                
                reader.readAsDataURL(file);
            }
        });
    });
}

// Attendance checkboxes functionality
function setupAttendanceCheckboxes() {
    var attendanceCheckboxes = document.querySelectorAll('.attendance-checkbox');
    
    attendanceCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var studentId = this.getAttribute('data-student-id');
            var subjectId = this.getAttribute('data-subject-id');
            var lectureNumber = this.getAttribute('data-lecture-number');
            var isPresent = this.checked;
            var isExcused = document.querySelector(`input[data-excused="${studentId}-${subjectId}-${lectureNumber}"]`).checked;
            
            // Show loading indicator
            const row = this.closest('tr');
            const statusCell = row.querySelector('.attendance-status');
            if (statusCell) {
                statusCell.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            }
            
            // Send AJAX request to update attendance
            fetch('/admin/attendance/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'student_id': studentId,
                    'subject_id': subjectId,
                    'lecture_number': lectureNumber,
                    'is_present': isPresent,
                    'is_excused': isExcused
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Attendance updated successfully');
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="badge bg-success">Saved</span>';
                        setTimeout(() => {
                            statusCell.innerHTML = '';
                        }, 2000);
                    }
                } else {
                    showToast('Failed to update attendance', 'danger');
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="badge bg-danger">Error</span>';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred', 'danger');
                if (statusCell) {
                    statusCell.innerHTML = '<span class="badge bg-danger">Error</span>';
                }
            });
        });
    });
    
    // Excused checkboxes
    var excusedCheckboxes = document.querySelectorAll('.excused-checkbox');
    
    excusedCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var dataId = this.getAttribute('data-excused').split('-');
            var studentId = dataId[0];
            var subjectId = dataId[1];
            var lectureNumber = dataId[2];
            var isExcused = this.checked;
            var isPresent = document.querySelector(`input[data-student-id="${studentId}"][data-subject-id="${subjectId}"][data-lecture-number="${lectureNumber}"]`).checked;
            
            // Show loading indicator
            const row = this.closest('tr');
            const statusCell = row.querySelector('.attendance-status');
            if (statusCell) {
                statusCell.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            }
            
            // Send AJAX request to update attendance
            fetch('/admin/attendance/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'student_id': studentId,
                    'subject_id': subjectId,
                    'lecture_number': lectureNumber,
                    'is_present': isPresent,
                    'is_excused': isExcused
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Excused status updated successfully');
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="badge bg-success">Saved</span>';
                        setTimeout(() => {
                            statusCell.innerHTML = '';
                        }, 2000);
                    }
                } else {
                    showToast('Failed to update excused status', 'danger');
                    if (statusCell) {
                        statusCell.innerHTML = '<span class="badge bg-danger">Error</span>';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred', 'danger');
                if (statusCell) {
                    statusCell.innerHTML = '<span class="badge bg-danger">Error</span>';
                }
            });
        });
    });
}

// Grade inputs functionality
function setupGradeInputs() {
    var gradeInputs = document.querySelectorAll('.grade-input');
    
    gradeInputs.forEach(function(input) {
        // Add debounce to avoid too many requests
        let timeout = null;
        
        input.addEventListener('input', function() {
            // Clear any existing timeout
            clearTimeout(timeout);
            
            // Show "typing" indicator
            const statusElement = this.nextElementSibling;
            if (statusElement && statusElement.classList.contains('grade-status')) {
                statusElement.innerHTML = '<small class="text-muted">Typing...</small>';
            }
            
            // Set a new timeout
            timeout = setTimeout(() => {
                updateGrade(this);
            }, 500);
        });
        
        // Also update on blur (when input loses focus)
        input.addEventListener('blur', function() {
            clearTimeout(timeout);
            updateGrade(this);
        });
    });
    
    function updateGrade(input) {
        var studentId = input.getAttribute('data-student-id');
        var subjectId = input.getAttribute('data-subject-id');
        var gradeType = input.getAttribute('data-grade-type');
        var gradeValue = input.value;
        
        // Show loading indicator
        const statusElement = input.nextElementSibling;
        if (statusElement && statusElement.classList.contains('grade-status')) {
            statusElement.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        }
        
        // Send AJAX request to update grade
        fetch('/admin/grades/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'student_id': studentId,
                'subject_id': subjectId,
                'grade_type': gradeType,
                'grade_value': gradeValue
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Grade updated successfully');
                if (statusElement) {
                    statusElement.innerHTML = '<small class="text-success">Saved</small>';
                    setTimeout(() => {
                        statusElement.innerHTML = '';
                    }, 2000);
                }
            } else {
                showToast('Failed to update grade', 'danger');
                if (statusElement) {
                    statusElement.innerHTML = '<small class="text-danger">Error</small>';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred', 'danger');
            if (statusElement) {
                statusElement.innerHTML = '<small class="text-danger">Error</small>';
            }
        });
    }
}

// Subject term dropdown functionality
function setupSubjectTermDropdown() {
    var termDropdown = document.getElementById('term-dropdown');
    
    if (termDropdown) {
        termDropdown.addEventListener('change', function() {
            var termId = this.value;
            var subjectContainers = document.querySelectorAll('.subject-term-container');
            
            // Hide all subject containers with animation
            subjectContainers.forEach(function(container) {
                container.classList.add('fade-out');
                setTimeout(() => {
                    container.style.display = 'none';
                    container.classList.remove('fade-out');
                }, 300);
            });
            
            // Show the selected term's container with animation
            setTimeout(() => {
                var selectedContainer = document.getElementById('term-' + termId);
                if (selectedContainer) {
                    selectedContainer.style.display = 'block';
                    selectedContainer.classList.add('fade-in');
                    setTimeout(() => {
                        selectedContainer.classList.remove('fade-in');
                    }, 300);
                }
            }, 300);
        });
    }
}

// Toast notification helper
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    var toastId = 'toast-' + Date.now();
    var toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast align-items-center text-white bg-' + type + ' border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Add animation class
    toast.classList.add('toast-animation');
    
    // Toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${getToastIcon(type)}
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    var bsToast = new bootstrap.Toast(toast, {
        delay: 3000
    });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Get appropriate icon for toast type
function getToastIcon(type) {
    switch (type) {
        case 'success':
            return '<i class="fas fa-check-circle me-2"></i>';
        case 'danger':
            return '<i class="fas fa-exclamation-circle me-2"></i>';
        case 'warning':
            return '<i class="fas fa-exclamation-triangle me-2"></i>';
        case 'info':
            return '<i class="fas fa-info-circle me-2"></i>';
        default:
            return '';
    }
}

// Add CSS for new animations
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .fade-out {
            opacity: 0;
            transition: opacity 0.3s ease-out;
        }
        
        .toast-animation {
            animation: slideInRight 0.3s ease-out;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
            }
            to {
                transform: translateX(0);
            }
        }
        
        .file-preview-icon {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            background-color: rgba(0,0,0,0.03);
            border-radius: 0.375rem;
        }
        
        .preview-image {
            max-height: 200px;
            border-radius: 0.375rem;
        }
        
        /* Dark mode styles */
        /* Dark mode styles have been removed */
    `;
    document.head.appendChild(style);
}); 