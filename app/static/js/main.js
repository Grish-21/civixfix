/**
 * CivicFix – Municipal Complaint Management System
 * Main JavaScript (main.js)
 *
 * Fully vanilla JavaScript (ES6+) for interactive UI behaviors:
 * 1. DOMContentLoaded initialization
 * 2. Flash message auto-dismiss
 * 3. Form validation & client-side file upload verification
 * 4. Confirmation dialogs for sensitive actions
 * 5. Interactive star rating widget
 * 6. Live image preview for uploads
 * 7. Real-time character counter for textareas
 * 8. Search & filter reset functionality
 * 9. Bootstrap tooltip & popover initialization
 * 10. Complaint detail page print handler
 * 11. Smooth scroll for anchor links
 * 12. Floating back-to-top button
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  initFlashAutoDismiss();
  initFormValidation();
  initConfirmationDialogs();
  initStarRatingWidget();
  initImagePreviews();
  initCharacterCounters();
  initFilterReset();
  initBootstrapTooltips();
  initPrintButtons();
  initSmoothScroll();
  initBackToTop();
});

/* ==========================================================================
   2. FLASH MESSAGE AUTO-DISMISS
   Fades out and removes temporary alert messages after 5 seconds.
   ========================================================================== */
function initFlashAutoDismiss() {
  const AUTO_DISMISS_DELAY_MS = 5000;
  const FADE_DURATION_MS = 400;

  const alerts = document.querySelectorAll('.alert:not(.alert-permanent):not([data-bs-autohide="false"])');

  alerts.forEach((alertEl) => {
    setTimeout(() => {
      // If Bootstrap alert instance exists, use its dismiss method
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        try {
          const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
          bsAlert.close();
          return;
        } catch (e) {
          // Fallback to manual fadeout if bootstrap Alert fails
        }
      }

      // Manual smooth fade out
      alertEl.style.transition = `opacity ${FADE_DURATION_MS}ms ease, transform ${FADE_DURATION_MS}ms ease`;
      alertEl.style.opacity = '0';
      alertEl.style.transform = 'translateY(-10px)';

      setTimeout(() => {
        if (alertEl.parentNode) {
          alertEl.parentNode.removeChild(alertEl);
        }
      }, FADE_DURATION_MS);
    }, AUTO_DISMISS_DELAY_MS);
  });
}

/* ==========================================================================
   3. FORM VALIDATION & FILE UPLOAD VERIFICATION
   - Applies Bootstrap 'was-validated' class on submit
   - Enforces max 5MB file size and image/jpeg, image/png allowed mime types
   ========================================================================== */
function initFormValidation() {
  const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
  const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png'];
  const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/pjpeg'];

  // Intercept standard forms marked for validation
  const forms = document.querySelectorAll('form.needs-validation');

  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      let isCustomValid = true;

      // Validate any file inputs inside this form
      const fileInputs = form.querySelectorAll('input[type="file"]');
      fileInputs.forEach((fileInput) => {
        if (!validateFileInput(fileInput, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES)) {
          isCustomValid = false;
        }
      });

      // Check native HTML5 form constraints
      if (!form.checkValidity() || !isCustomValid) {
        event.preventDefault();
        event.stopPropagation();
      }

      form.classList.add('was-validated');
    }, false);
  });

  // Attach live change listeners on all file inputs
  const allFileInputs = document.querySelectorAll('input[type="file"]');
  allFileInputs.forEach((fileInput) => {
    fileInput.addEventListener('change', () => {
      validateFileInput(fileInput, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES);
    });
  });
}

/**
 * Validates an individual file input against size and extension constraints.
 */
function validateFileInput(inputEl, maxBytes, allowedExts, allowedMimes) {
  const file = inputEl.files && inputEl.files[0];
  let errorMessage = '';

  // Remove existing custom error container if any
  clearFileFeedback(inputEl);

  if (file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const isExtensionValid = allowedExts.includes(ext);
    const isMimeValid = !file.type || allowedMimes.includes(file.type.toLowerCase());

    if (!isExtensionValid || !isMimeValid) {
      errorMessage = `Invalid format (${ext.toUpperCase()}). Please upload JPG, JPEG, or PNG images only.`;
    } else if (file.size > maxBytes) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      errorMessage = `File too large (${sizeMb} MB). Maximum allowed size is 5.0 MB.`;
    }
  }

  if (errorMessage) {
    inputEl.setCustomValidity(errorMessage);
    inputEl.classList.add('is-invalid');
    showFileFeedback(inputEl, errorMessage);
    return false;
  } else {
    inputEl.setCustomValidity('');
    inputEl.classList.remove('is-invalid');
    return true;
  }
}

function showFileFeedback(inputEl, message) {
  let feedback = inputEl.parentElement.querySelector('.file-validation-feedback');
  if (!feedback) {
    feedback = document.createElement('div');
    feedback.className = 'file-validation-feedback text-danger mt-1 small font-weight-bold';
    inputEl.parentElement.appendChild(feedback);
  }
  feedback.textContent = message;
}

function clearFileFeedback(inputEl) {
  const feedback = inputEl.parentElement.querySelector('.file-validation-feedback');
  if (feedback) {
    feedback.remove();
  }
}

/* ==========================================================================
   4. CONFIRMATION DIALOGS
   Prompts user verification before triggering critical/destructive actions.
   ========================================================================== */
function initConfirmationDialogs() {
  const confirmElements = document.querySelectorAll('.confirm-action, [data-confirm]');

  confirmElements.forEach((element) => {
    element.addEventListener('click', (event) => {
      const promptMessage = element.getAttribute('data-confirm') ||
        'Are you sure you want to proceed with this action? This cannot be undone.';

      if (!window.confirm(promptMessage)) {
        event.preventDefault();
        event.stopPropagation();
        return false;
      }
    });
  });
}

/* ==========================================================================
   5. STAR RATING WIDGET
   Handles 5-star clickable feedback with preview highlight & hidden input sync.
   ========================================================================== */
function initStarRatingWidget() {
  const starContainers = document.querySelectorAll('.star-rating-widget, .star-rating-interactive');

  starContainers.forEach((container) => {
    const inputTargetSelector = container.getAttribute('data-input-target') || 'input[name="rating"]';
    const targetInput = container.querySelector(inputTargetSelector) ||
      document.querySelector(inputTargetSelector);

    // Create 5 stars if not already present
    let stars = container.querySelectorAll('.star-item');
    if (stars.length === 0) {
      container.innerHTML = '';
      for (let i = 1; i <= 5; i++) {
        const star = document.createElement('span');
        star.className = 'star-item';
        star.dataset.value = i;
        star.innerHTML = '&#9733;'; // Unicode Star
        star.style.fontSize = '2.2rem';
        star.style.cursor = 'pointer';
        star.style.color = '#dee2e6';
        star.style.transition = 'color 0.15s ease, transform 0.15s ease';
        star.style.display = 'inline-block';
        star.style.marginRight = '0.25rem';
        container.appendChild(star);
      }
      stars = container.querySelectorAll('.star-item');
    }

    let selectedRating = targetInput ? parseInt(targetInput.value, 10) || 0 : 0;
    updateStarVisuals(stars, selectedRating);

    // Hover interactions
    stars.forEach((star) => {
      star.addEventListener('mouseenter', () => {
        const hoverVal = parseInt(star.dataset.value, 10);
        highlightStars(stars, hoverVal);
      });

      star.addEventListener('mouseleave', () => {
        updateStarVisuals(stars, selectedRating);
      });

      star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.value, 10);
        if (targetInput) {
          targetInput.value = selectedRating;
          // Trigger change event on target input for any attached listeners
          targetInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        updateStarVisuals(stars, selectedRating);
      });
    });
  });

  // Also support radio-button based star rating (.star-rating-input)
  const radioStarGroups = document.querySelectorAll('.star-rating-input');
  radioStarGroups.forEach((group) => {
    const radios = group.querySelectorAll('input[type="radio"]');
    radios.forEach((radio) => {
      radio.addEventListener('change', () => {
        const valueDisplay = group.parentElement.querySelector('.rating-value-display');
        if (valueDisplay) {
          valueDisplay.textContent = `${radio.value} of 5 Stars`;
        }
      });
    });
  });
}

function highlightStars(stars, count) {
  stars.forEach((star) => {
    const val = parseInt(star.dataset.value, 10);
    if (val <= count) {
      star.style.color = '#ffc107';
      star.style.transform = 'scale(1.15)';
    } else {
      star.style.color = '#dee2e6';
      star.style.transform = 'scale(1)';
    }
  });
}

function updateStarVisuals(stars, activeCount) {
  stars.forEach((star) => {
    const val = parseInt(star.dataset.value, 10);
    star.style.transform = 'scale(1)';
    if (val <= activeCount) {
      star.style.color = '#ffc107';
    } else {
      star.style.color = '#dee2e6';
    }
  });
}

/* ==========================================================================
   6. LIVE IMAGE PREVIEW
   Renders image thumbnail preview below file input upon user file selection.
   ========================================================================== */
function initImagePreviews() {
  const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"], input[type="file"].preview-enabled, #image, #resolution_image');

  fileInputs.forEach((input) => {
    input.addEventListener('change', function () {
      const file = this.files && this.files[0];
      const previewContainerId = this.getAttribute('data-preview-container');
      let previewWrapper = previewContainerId ? document.getElementById(previewContainerId) : null;

      // Create fallback preview container if none specified
      if (!previewWrapper) {
        let parent = this.closest('.file-upload-wrapper') || this.parentElement;
        previewWrapper = parent.querySelector('.image-preview-box');

        if (!previewWrapper) {
          previewWrapper = document.createElement('div');
          previewWrapper.className = 'image-preview-box mt-3';
          parent.appendChild(previewWrapper);
        }
      }

      previewWrapper.innerHTML = '';

      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();

        reader.onload = (e) => {
          const previewCard = document.createElement('div');
          previewCard.className = 'card border-1 shadow-sm p-2 d-inline-block position-relative fade-in';
          previewCard.style.maxWidth = '260px';

          const img = document.createElement('img');
          img.src = e.target.result;
          img.alt = 'Uploaded Image Preview';
          img.className = 'img-fluid rounded';
          img.style.maxHeight = '180px';
          img.style.objectFit = 'cover';

          const caption = document.createElement('div');
          caption.className = 'small text-muted mt-1 text-truncate';
          caption.textContent = `${file.name} (${(file.size / 1024).toFixed(0)} KB)`;

          const removeBtn = document.createElement('button');
          removeBtn.type = 'button';
          removeBtn.className = 'btn btn-sm btn-danger position-absolute top-0 end-0 m-1 rounded-circle p-0';
          removeBtn.style.width = '24px';
          removeBtn.style.height = '24px';
          removeBtn.innerHTML = '&times;';
          removeBtn.title = 'Remove image';

          removeBtn.addEventListener('click', () => {
            input.value = '';
            previewWrapper.innerHTML = '';
            input.dispatchEvent(new Event('change', { bubbles: true }));
          });

          previewCard.appendChild(img);
          previewCard.appendChild(caption);
          previewCard.appendChild(removeBtn);
          previewWrapper.appendChild(previewCard);
        };

        reader.readAsDataURL(file);
      }
    });
  });
}

/* ==========================================================================
   7. REAL-TIME CHARACTER COUNTER
   Displays current character length and alerts when approaching threshold.
   ========================================================================== */
function initCharacterCounters() {
  const textareas = document.querySelectorAll('textarea[data-maxlength], textarea[maxlength]');

  textareas.forEach((textarea) => {
    const maxLen = parseInt(textarea.getAttribute('data-maxlength') || textarea.getAttribute('maxlength'), 10);
    if (!maxLen || isNaN(maxLen)) return;

    // Create or select counter container
    let counter = textarea.parentElement.querySelector('.char-counter');
    if (!counter) {
      counter = document.createElement('div');
      counter.className = 'char-counter';
      textarea.parentElement.appendChild(counter);
    }

    const updateCount = () => {
      const currentLen = textarea.value.length;
      counter.textContent = `${currentLen} / ${maxLen} characters`;

      counter.classList.remove('limit-near', 'limit-reached');
      if (currentLen >= maxLen) {
        counter.classList.add('limit-reached');
      } else if (currentLen >= maxLen * 0.85) {
        counter.classList.add('limit-near');
      }
    };

    textarea.addEventListener('input', updateCount);
    updateCount();
  });
}

/* ==========================================================================
   8. SEARCH & FILTER RESET
   Clears all filters in search bar and re-executes search or reloads base view.
   ========================================================================== */
function initFilterReset() {
  const clearButtons = document.querySelectorAll('.btn-clear-filters, #clearFilters, [data-action="clear-filters"]');

  clearButtons.forEach((button) => {
    button.addEventListener('click', (event) => {
      const form = button.closest('form');
      if (form) {
        event.preventDefault();

        // Reset all text and search inputs
        const inputs = form.querySelectorAll('input[type="text"], input[type="search"]');
        inputs.forEach((inp) => (inp.value = ''));

        // Reset all select elements to first option
        const selects = form.querySelectorAll('select');
        selects.forEach((sel) => (sel.selectedIndex = 0));

        // Uncheck radio / checkboxes
        const checkables = form.querySelectorAll('input[type="checkbox"], input[type="radio"]');
        checkables.forEach((chk) => (chk.checked = false));

        // Submit cleaned form or redirect to action URL without query parameters
        if (form.getAttribute('action')) {
          window.location.href = form.getAttribute('action');
        } else {
          form.submit();
        }
      }
    });
  });
}

/* ==========================================================================
   9. BOOTSTRAP TOOLTIPS & POPOVERS INITIALIZATION
   Enables native Bootstrap 5 interactive tooltips and popovers across DOM.
   ========================================================================== */
function initBootstrapTooltips() {
  if (typeof bootstrap === 'undefined') return;

  // Initialize Tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"], .has-tooltip')
  );
  tooltipTriggerList.forEach((tooltipTriggerEl) => {
    try {
      bootstrap.Tooltip.getOrCreateInstance(tooltipTriggerEl, {
        boundary: 'window',
      });
    } catch (e) {
      // Ignore if element is not rendered
    }
  });

  // Initialize Popovers
  const popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  popoverTriggerList.forEach((popoverTriggerEl) => {
    try {
      bootstrap.Popover.getOrCreateInstance(popoverTriggerEl);
    } catch (e) {
      // Ignore
    }
  });
}

/* ==========================================================================
   10. PRINT COMPLAINT HANDLER
   Triggers browser print preview for complaint details or resolution summary.
   ========================================================================== */
function initPrintButtons() {
  const printButtons = document.querySelectorAll('.btn-print, [data-action="print"]');

  printButtons.forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      window.print();
    });
  });
}

/* ==========================================================================
   11. SMOOTH SCROLL FOR ANCHOR LINKS
   Smoothly scrolls page when clicking hash anchors (#section).
   ========================================================================== */
function initSmoothScroll() {
  const anchorLinks = document.querySelectorAll('a[href^="#"]:not([href="#"]):not([data-bs-toggle])');

  anchorLinks.forEach((anchor) => {
    anchor.addEventListener('click', function (event) {
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        event.preventDefault();
        const navOffset = 70; // Offset for sticky navbar
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - navOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth',
        });
      }
    });
  });
}

/* ==========================================================================
   12. BACK TO TOP BUTTON
   Appears after scrolling down 300px; clicking scrolls user smoothly to top.
   ========================================================================== */
function initBackToTop() {
  let backBtn = document.getElementById('backToTop') || document.querySelector('.btn-back-to-top');

  // Auto-generate back to top button if it doesn't already exist in template
  if (!backBtn) {
    backBtn = document.createElement('button');
    backBtn.id = 'backToTop';
    backBtn.className = 'btn-back-to-top';
    backBtn.setAttribute('aria-label', 'Scroll to top');
    backBtn.innerHTML = '&#8593;'; // Up arrow
    document.body.appendChild(backBtn);
  }

  const toggleBackToTop = () => {
    if (window.scrollY > 300) {
      backBtn.classList.add('show');
    } else {
      backBtn.classList.remove('show');
    }
  };

  window.addEventListener('scroll', toggleBackToTop, { passive: true });
  toggleBackToTop();

  backBtn.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  });
}
