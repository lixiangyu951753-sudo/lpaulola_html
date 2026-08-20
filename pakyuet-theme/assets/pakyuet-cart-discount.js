/**
 * PAKYUET: Cart discount code apply/remove (ported from the Tinker theme).
 *
 * Applies discount codes through the Cart Ajax API (`cart/update.js` with the
 * `discount` field), then re-renders the cart page / cart drawer sections the
 * same way Dawn's own cart.js does. Uses event delegation so it keeps working
 * after sections are re-rendered.
 */
(function () {
  const SECTIONS = ['main-cart-items', 'main-cart-footer', 'cart-drawer', 'cart-icon-bubble'];
  const DISCOUNT_ROOT_SELECTOR = '[data-cart-discount-root]';

  const strings = {
    invalid: 'Invalid discount code',
    failed: 'Could not apply discount code. Please try again.',
  };

  function parseHtml(html) {
    return new DOMParser().parseFromString(html, 'text/html');
  }

  function existingCodes(root) {
    return Array.from(root.querySelectorAll('[data-discount-code]'))
      .map((element) => element.dataset.discountCode)
      .filter(Boolean);
  }

  function showError(root, message) {
    const error = root.querySelector('[data-cart-discount-error]');
    if (!error) return;
    error.textContent = message;
    error.hidden = false;
  }

  function hideError(root) {
    const error = root.querySelector('[data-cart-discount-error]');
    if (error) error.hidden = true;
  }

  async function updateCart(discount) {
    const response = await fetch('/cart/update.js', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        discount,
        sections: SECTIONS,
        sections_url: window.location.pathname,
      }),
    });
    if (!response.ok) throw new Error('Cart update request failed');
    return response.json();
  }

  function refreshSections(data) {
    const sections = data.sections || {};

    // Cart page: cart items list
    if (sections['main-cart-items'] && document.getElementById('main-cart-items')) {
      const target = document.querySelector('#main-cart-items .js-contents');
      const source = parseHtml(sections['main-cart-items']).querySelector('.js-contents');
      if (target && source) target.innerHTML = source.innerHTML;
    }

    // Cart page: footer (subtotal / totals)
    if (sections['main-cart-footer'] && document.getElementById('main-cart-footer')) {
      const target = document.querySelector('#main-cart-footer .js-contents');
      const source = parseHtml(sections['main-cart-footer']).querySelector('.js-contents');
      if (target && source) target.innerHTML = source.innerHTML;
    }

    // Cart drawer: items + footer (mirrors Dawn's cart.js onCartUpdate)
    if (sections['cart-drawer']) {
      const doc = parseHtml(sections['cart-drawer']);
      ['cart-drawer-items', '.cart-drawer__footer'].forEach((selector) => {
        const target = document.querySelector(selector);
        const source = doc.querySelector(selector);
        if (target && source) target.replaceWith(source);
      });
    }

    // Header cart icon bubble (count badge)
    if (sections['cart-icon-bubble'] && document.getElementById('cart-icon-bubble')) {
      const target = document.getElementById('cart-icon-bubble');
      const source = parseHtml(sections['cart-icon-bubble']).querySelector('.shopify-section');
      if (target && source) target.innerHTML = source.innerHTML;
    }

    // Discount components (applied pills / error state) — re-sync from server HTML
    document.querySelectorAll(DISCOUNT_ROOT_SELECTOR).forEach((root) => {
      const sectionId = root.dataset.cartDiscountContext === 'drawer' ? 'cart-drawer' : 'main-cart-footer';
      if (!sections[sectionId]) return;
      const source = parseHtml(sections[sectionId]).querySelector(DISCOUNT_ROOT_SELECTOR);
      if (source) root.replaceWith(source);
    });
  }

  async function applyDiscount(form) {
    const root = form.closest(DISCOUNT_ROOT_SELECTOR);
    if (!root) return;
    hideError(root);

    const input = form.querySelector('input[name="discount"]');
    if (!input) return;
    const code = input.value.trim();
    if (!code) return;

    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;

    try {
      const data = await updateCart(code);
      const entry = (data.discount_codes || []).find(
        (discount) =>
          discount &&
          typeof discount.code === 'string' &&
          discount.code.toLowerCase() === code.toLowerCase()
      );
      if (entry && entry.applicable === false) {
        showError(root, strings.invalid);
        input.value = '';
        input.focus();
        return;
      }
      refreshSections(data);
      input.value = '';
    } catch (error) {
      console.error('pakyuet-cart-discount apply failed:', error);
      showError(root, strings.failed);
    } finally {
      if (button) button.disabled = false;
    }
  }

  async function removeDiscount(root, code) {
    hideError(root);
    const remaining = existingCodes(root).filter((existing) => existing !== code);
    try {
      const data = await updateCart(remaining.join(','));
      refreshSections(data);
    } catch (error) {
      console.error('pakyuet-cart-discount remove failed:', error);
      showError(root, strings.failed);
    }
  }

  document.addEventListener('submit', (event) => {
    const form = event.target.closest('[data-cart-discount-form]');
    if (!form) return;
    event.preventDefault();
    applyDiscount(form);
  });

  document.addEventListener('click', (event) => {
    const removeButton = event.target.closest('[data-discount-remove]');
    if (!removeButton) return;
    event.preventDefault();
    const root = removeButton.closest(DISCOUNT_ROOT_SELECTOR);
    const pill = removeButton.closest('[data-discount-code]');
    if (root && pill && pill.dataset.discountCode) {
      removeDiscount(root, pill.dataset.discountCode);
    }
  });
})();
