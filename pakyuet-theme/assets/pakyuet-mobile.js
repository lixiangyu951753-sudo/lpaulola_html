/* ============================================
   PAKYUET 移動端 IR 布局復刻 interactions (2026-08-04)
   - 篩選摺疊：展開篩選 按鈕 → .ir-filter-collapse.active
   - 漢堡抽屜：開/關 .ir-drawer.open + body.ir-menu-open
   獨立新文件避免 CDN 快取；IIFE，可多次初始化。
   ============================================ */
(function () {
  'use strict';

  /* ---- 篩選摺疊 ---- */
  function initFilterToggle(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-filter-collapse]').forEach(function (wrap) {
      if (wrap.dataset.bound === '1') return;
      wrap.dataset.bound = '1';
      var btn = wrap.querySelector('[data-filter-toggle]');
      if (!btn) return;
      btn.addEventListener('click', function () {
        var open = wrap.classList.toggle('active');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
  }

  /* ---- 滾動收起公告欄（只留白色導航條） ---- */
  function initHeaderScroll() {
    var header = document.querySelector('[data-pakyuet-header]');
    if (!header || header.dataset.scrollBound === '1') return;
    header.dataset.scrollBound = '1';
    var ticking = false;
    function update() {
      header.classList.toggle('ir-header--scrolled', window.scrollY > 8);
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  /* ---- 漢堡抽屜 ---- */
  function initDrawer(scope) {
    var root = scope || document;
    var toggle = root.querySelector('[data-menu-toggle]');
    if (!toggle || toggle.dataset.bound === '1') return;
    toggle.dataset.bound = '1';
    var drawer = document.getElementById('ir-menu-drawer');
    var backdrop = document.querySelector('[data-menu-backdrop]');

    function open() {
      if (drawer) drawer.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      document.body.classList.add('ir-menu-open');
      toggle.setAttribute('aria-expanded', 'true');
    }
    function close() {
      if (drawer) drawer.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      document.body.classList.remove('ir-menu-open');
      toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', open);
    if (backdrop) backdrop.addEventListener('click', close);
    var closeBtn = root.querySelector('[data-menu-close]');
    if (closeBtn) closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* ---- 抽屜分組：父級=直達分類連結，右側按鈕=展開子連結 ---- */
  function initDrawerGroups(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-drawer-group]').forEach(function (group) {
      if (group.dataset.bound === '1') return;
      group.dataset.bound = '1';
      var toggle = group.querySelector('[data-drawer-toggle]');
      var children = group.querySelector('[data-drawer-children]');
      if (!toggle || !children) return;
      toggle.addEventListener('click', function () {
        var open = children.hidden;
        children.hidden = !open;
        group.classList.toggle('open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
  }

  function initAll(scope) {
    initFilterToggle(scope);
    initDrawer(scope);
    initDrawerGroups(scope);
    initHeaderScroll();
  }

  function boot() { initAll(document); }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  /* Shopify theme editor support */
  document.addEventListener('shopify:section:load', function (e) { initAll(e.target); });
  document.addEventListener('shopify:section:select', function (e) { initAll(e.target); });
})();
