// ShopSphere Client Interactivity

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(function () {
        alert.remove();
      }, 500);
    }, 5000);
  });

  // 2. Alert close buttons
  document.querySelectorAll('.alert-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const alertBox = btn.closest('.alert');
      if (alertBox) {
        alertBox.remove();
      }
    });
  });

  // 3. AJAX Add to Cart button handler (enhances UX without reloading page)
  const ajaxCartForms = document.querySelectorAll('.ajax-cart-form');
  ajaxCartForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const url = form.action;
      const formData = new FormData(form);

      fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Update cart badge in navbar
          const badges = document.querySelectorAll('.cart-badge');
          badges.forEach(b => b.textContent = data.cart_count);

          // Show floating toast
          showToast(data.message, 'success');
        } else if (data.error) {
          showToast(data.error, 'danger');
        }
      })
      .catch(err => {
        // Fallback to standard form submit if fetch fails
        form.submit();
      });
    });
  });

  function showToast(message, type) {
    let container = document.querySelector('.messages-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'messages-container';
      const main = document.querySelector('main');
      if (main) {
        main.parentNode.insertBefore(container, main);
      }
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
      <span>${message}</span>
      <button class="alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(alert);

    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  }
});
