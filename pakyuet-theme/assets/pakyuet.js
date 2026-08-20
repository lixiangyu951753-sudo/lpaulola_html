/* ============================================
   PAKYUET interactions v2 - shop-style homepage
   - Navbar scroll shadow (add .scrolled past 10px)
   - Hero carousel (auto-play + dot navigation)
   - Sort dropdown + AJAX 排序/翻页（不跳转页面，跨页全局排序）
   - Shopify theme editor: re-init on section load
   Wrapped in an IIFE; safe to call multiple times.
   ============================================ */
(function () {
  'use strict';

  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DEFAULT_COLLECTION_HANDLE = 'all-color-sorted';

  // 当前商品集合 handle：collection 模板取当前分类，首页取 pakyuet-market 的 source_collection（all-color-sorted）
  function getCollectionHandle() {
    var section = document.querySelector('[data-product-section]');
    if (section && section.getAttribute('data-collection')) {
      return section.getAttribute('data-collection');
    }
    return DEFAULT_COLLECTION_HANDLE;
  }

  // AJAX 后的 history 路径：collection 模板用 /collections/<handle>，首页（featured market）用根路径 /
  function getBasePath(handle) {
    var section = document.querySelector('[data-product-section]');
    if (section && section.getAttribute('data-collection-page') === '1') {
      return '/collections/' + handle;
    }
    return '/';
  }

  /* ---- Navbar scroll shadow (global, once) ---- */
  function initNavScroll() {
    var header = document.querySelector('.pakyuet-header');
    if (!header || header.dataset.navBound === '1') return;
    header.dataset.navBound = '1';
    function onScroll() {
      if (window.scrollY > 10) header.classList.add('scrolled');
      else header.classList.remove('scrolled');
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---- Hero carousel ---- */
  function initHeroCarousel(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-hero-carousel]').forEach(function (carousel) {
      if (carousel.dataset.bound === '1') return;
      carousel.dataset.bound = '1';
      var slides = carousel.querySelectorAll('[data-hero-slide]');
      var dots = carousel.querySelectorAll('[data-hero-dot]');
      if (slides.length <= 1) return;
      var current = 0;
      var timer = null;

      function show(idx) {
        slides.forEach(function (s, i) { s.classList.toggle('active', i === idx); });
        dots.forEach(function (d, i) { d.classList.toggle('active', i === idx); });
        current = idx;
      }
      function next() { show((current + 1) % slides.length); }
      function prev() { show((current - 1 + slides.length) % slides.length); }
      function start() { if (!reducedMotion) { stop(); timer = setInterval(next, 5000); } }
      function stop() { if (timer) { clearInterval(timer); timer = null; } }

      dots.forEach(function (dot) {
        dot.addEventListener('click', function () {
          show(parseInt(dot.getAttribute('data-hero-dot'), 10));
          start();
        });
      });
      var prevBtn = carousel.querySelector('[data-hero-prev]');
      var nextBtn = carousel.querySelector('[data-hero-next]');
      if (prevBtn) prevBtn.addEventListener('click', function () { prev(); start(); });
      if (nextBtn) nextBtn.addEventListener('click', function () { next(); start(); });
      carousel.addEventListener('mouseenter', stop);
      carousel.addEventListener('mouseleave', start);
      start();
    });
  }

  /* ============================================
     筛选下拉：组合筛选（多维度 AND 交集）
     URL 方案：/collections/{base}/{tag1}+{tag2}+...
       base = 依類別 所选分类 handle（rings/necklaces/earrings/bracelets），未选则 all
       tag  = 其余维度所选 tag（stone/material/color/shape/style/plating）
     Shopify 原生支持 collection 路径内以 + 分隔多 tag 的 AND 交集过滤，
     故选莫桑石 + 再选颜色，两个条件会同时保留。
     ============================================ */
  var FILTER_CATEGORY_HANDLES = ['rings', 'necklaces', 'earrings', 'bracelets', 'pendants'];
  var FILTER_STONE_TAGS = { moissanite: '莫桑石', zircon: '鋯石', 'high-carbon-diamond': '高碳鑽', 'colored-gemstone': '彩寶', pearl: '珍珠' };

  // collection handle → tag（石材有中文 tag，其余是 handle 的 - 换成 _）
  function filterHandleToTag(handle) {
    if (FILTER_STONE_TAGS[handle]) return FILTER_STONE_TAGS[handle];
    return handle.replace(/-/g, '_');
  }

  // handle 属于哪一类：all / category（依類別）/ tag（可作路径 tag）/ base（其它自定义合集，保持为 base）
  function filterHandleKind(handle) {
    if (handle === 'all') return 'all';
    if (FILTER_CATEGORY_HANDLES.indexOf(handle) !== -1) return 'category';
    if (FILTER_STONE_TAGS[handle] || /^(material|color|shape|style|plating|theme)-/.test(handle)) return 'tag';
    return 'base';
  }

  // 解析当前 URL /collections/{base}/{t1+t2}；tag 型 collection 作为 base 时归一化为 tag + all
  function parseFilterState() {
    var path = decodeURIComponent(window.location.pathname);
    var seg = path.split('/').filter(Boolean);
    // 剥离 Shopify 多语言 locale 前缀（/zh-hans|zh-hant|en/collections/... → /collections/...）
    if (seg.length > 1 && seg[0] !== 'collections' && seg[1] === 'collections') seg.shift();
    var state = { base: 'all', tags: [] };
    if (seg[0] === 'collections' && seg[1]) {
      var base = seg[1];
      var kind = filterHandleKind(base);
      if (kind === 'category' || kind === 'all' || kind === 'base') {
        state.base = base;
      } else {
        state.tags.push(filterHandleToTag(base));
      }
      if (seg[2]) {
        seg[2].split('+').forEach(function (t) { if (t) state.tags.push(t); });
      }
    }
    return state;
  }

  // 逐个 encode tag（不能整体 encode，否则 + 会变成 %2B）
  function encodeTagPath(tagPath) {
    return tagPath.split('+').map(function (t) { return encodeURIComponent(t); }).join('+');
  }

  // 当前 URL 的原始 tag 段（供 AJAX 排序/翻页复用，保持与页面 base 一致）
  function getCurrentTagPath() {
    var seg = decodeURIComponent(window.location.pathname).split('/').filter(Boolean);
    if (seg.length > 1 && seg[0] !== 'collections' && seg[1] === 'collections') seg.shift();
    if (seg[0] === 'collections' && seg[2]) return seg[2];
    return '';
  }

  // 由筛选状态重建规范 URL，保留当前排序
  function buildFilterUrl(state) {
    var url = '/collections/' + (state.base || 'all');
    if (state.tags.length) url += '/' + encodeTagPath(state.tags.join('+'));
    var params = new URLSearchParams(window.location.search);
    var sortBy = params.get('sort_by');
    if (sortBy) url += '?sort_by=' + encodeURIComponent(sortBy);
    return url;
  }

  // 收集某个下拉框自己的维度信息：是否依類別 + 可选的 tag 值集合
  function collectSelectOptions(select) {
    var info = { isCategory: false, isBase: false, tags: [] };
    select.querySelectorAll('option').forEach(function (o) {
      var h = (o.value || '').replace(/\/collections\//, '').split('?')[0].split('/')[0];
      if (!h || h === 'all') return;
      var k = filterHandleKind(h);
      if (k === 'category') info.isCategory = true;
      else if (k === 'base') info.isBase = true;
      else if (k === 'tag') info.tags.push(filterHandleToTag(h));
    });
    return info;
  }

  // 选择变化：先移除本下拉框旧值，再应用新值，其余维度保留
  function applyFilterChange(select) {
    var val = select.value;
    var handle = (val || '').replace(/\/collections\//, '').split('?')[0].split('/')[0] || 'all';
    var kind = filterHandleKind(handle);
    var state = parseFilterState();
    var own = collectSelectOptions(select);
    state.tags = state.tags.filter(function (t) { return own.tags.indexOf(t) === -1; });
    if (kind === 'category' || kind === 'base') state.base = handle;
    else if (kind === 'tag') state.tags.push(filterHandleToTag(handle));
    else if (kind === 'all' && (own.isCategory || own.isBase)) state.base = 'all';
    window.location.href = buildFilterUrl(state);
  }

  // 页面加载时按当前 URL 回填各下拉框选中态
  function markFilterSelects(bar) {
    var state = parseFilterState();
    bar.querySelectorAll('select.ir-filter-select').forEach(function (select) {
      var target = null;
      select.querySelectorAll('option').forEach(function (o) {
        var h = (o.value || '').replace(/\/collections\//, '').split('?')[0].split('/')[0] || '';
        if (!h || h === 'all') return;
        var k = filterHandleKind(h);
        if (k === 'category' && state.base === h) target = o;
        else if (k === 'base' && state.base === h) target = o;
        else if (k === 'tag' && state.tags.indexOf(filterHandleToTag(h)) !== -1) target = o;
      });
      // 未命中当前筛选时回到下拉标题占位（如「依石材」），不强制选中「全部」
      select.value = target ? target.value : '';
    });
  }

  function initFilterSelects(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-filter-selects]').forEach(function (bar) {
      if (bar.dataset.bound === '1') return;
      bar.dataset.bound = '1';
      bar.querySelectorAll('select.ir-filter-select').forEach(function (select) {
        select.addEventListener('change', function () {
          var val = select.value;
          if (!val || val === '#' || val === '') return;
          applyFilterChange(select);
        });
      });
      markFilterSelects(bar);

      // 清空篩選：仅当 URL 处于筛选态（base≠all 或带 tag）时才显示；点击回 /collections/all 并保留排序
      root.querySelectorAll('[data-filter-clear]').forEach(function (btn) {
        if (btn.dataset.bound === '1') return;
        btn.dataset.bound = '1';
        var st = parseFilterState();
        btn.hidden = st.base === 'all' && st.tags.length === 0;
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          window.location.href = buildFilterUrl({ base: 'all', tags: [] });
        });
      });
    });
  }

  /* ---- 渲染单个商品卡片 HTML ---- */
  function renderCard(p) {
    var html = '<a href="' + p.url + '" class="pakyuet-product-card" data-type="' + (p.type || '') + '" data-series="' + (p.series || '') + '" data-price="' + p.price + '" data-date="' + p.created_at + '">';
    html += '<div class="product-card__image-wrap media media--hover-effect">';
    if (p.image) {
      html += '<img src="' + p.image + '" alt="' + escapeAttr(p.title) + '" class="product-card__img product-card__img--primary" loading="lazy" />';
    }
    if (p.secondary_image) {
      html += '<img src="' + p.secondary_image + '" alt="' + escapeAttr(p.title) + '" class="product-card__img product-card__img--secondary" loading="lazy" />';
    }
    if (p.series === 'moissanite') {
      html += '<span class="product-card__tag product-card__tag--moissanite">莫桑石</span>';
    } else if (p.series === 'daily') {
      html += '<span class="product-card__tag product-card__tag--daily">日常</span>';
    }
    if (!p.available) {
      html += '<span class="product-card__badge product-card__badge--soldout">售罄</span>';
    } else if (p.compare_at_price > p.price) {
      html += '<span class="product-card__badge product-card__badge--sale">SALE</span>';
    }
    html += '</div>';
    html += '<div class="product-card__info">';
    html += '<div class="product-card__name">' + escapeHtml(p.title) + '</div>';
    html += '<div class="product-card__price-wrap">';
    if (p.compare_at_price > p.price) {
      var discount = Math.round((p.compare_at_price - p.price) * 100 / p.compare_at_price);
      html += '<span class="product-card__price product-card__price--sale">' + p.price_formatted + '</span>';
      html += '<span class="product-card__price product-card__price--compare">' + p.compare_at_price_formatted + '</span>';
      html += '<span class="product-card__discount">-' + discount + '%</span>';
    } else {
      html += '<span class="product-card__price">' + p.price_formatted + '</span>';
    }
    html += '</div>';
    if (!p.available) {
      html += '<div class="product-card__soldout">售罄</div>';
    }
    html += '</div></a>';
    return html;
  }

  function escapeHtml(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function escapeAttr(s) { return escapeHtml(s).replace(/"/g, '&quot;'); }

  /* ---- AJAX 加载商品（排序 + 翻页） ---- */
  var currentState = { sortBy: 'manual', page: 1 };

  function getPageSize() {
    var section = document.querySelector('[data-product-section]');
    if (section) {
      var ps = parseInt(section.getAttribute('data-page-size'), 10);
      if (ps > 0) return ps;
    }
    return 15;
  }

  function loadProducts(sortBy, page) {
    var pageSize = getPageSize();
    var handle = getCollectionHandle();
    var basePath = getBasePath(handle);
    var tagPath = encodeTagPath(getCurrentTagPath());
    var url = '/collections/' + handle + (tagPath ? '/' + tagPath : '') + '?view=data&page_size=' + pageSize;
    if (sortBy && sortBy !== 'manual') url += '&sort_by=' + sortBy;
    if (page && page > 1) url += '&page=' + page;

    var grid = document.querySelector('[data-product-grid]');
    if (grid) grid.style.opacity = '0.4';

    currentState = { sortBy: sortBy || 'manual', page: page || 1 };

    fetch(url)
      .then(function (r) { return r.text(); })
      .then(function (text) {
        var data;
        try { data = JSON.parse(text); }
        catch (e) { console.error('JSON parse error:', e, text.slice(0, 200)); return; }
        var html = (data.products || []).map(renderCard).join('');
        if (grid) {
          grid.innerHTML = html;
          grid.style.opacity = '1';
        }
        updatePagination(data.pagination || {}, sortBy);
        updateSortUI(sortBy);
        var tagPath = encodeTagPath(getCurrentTagPath());
        var newUrl = basePath + (tagPath ? '/' + tagPath : '') + '?sort_by=' + (sortBy || 'manual');
        if (page && page > 1) newUrl += '&page=' + page;
        history.pushState({ sortBy: sortBy, page: page }, '', newUrl);
        var section = document.getElementById('products');
        if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch(function (e) {
        console.error('PAKYUET loadProducts error:', e);
        if (grid) grid.style.opacity = '1';
      });
  }

  /* ---- 页码窗口：1 … cur-2 cur-1 cur cur+1 cur+2 … last ---- */
  function buildPages(cur, total) {
    if (total <= 7) {
      var all = [];
      for (var i = 1; i <= total; i++) all.push(i);
      return all;
    }
    var pages = [1];
    var start = Math.max(2, cur - 2);
    var end = Math.min(total - 1, cur + 2);
    if (start > 2) pages.push('...');
    for (var p = start; p <= end; p++) pages.push(p);
    if (end < total - 1) pages.push('...');
    pages.push(total);
    return pages;
  }

  function updatePagination(pagination, sortBy) {
    var nav = document.querySelector('[data-pagination]');
    if (!nav) return;
    var cur = pagination.current_page || 1;
    var total = pagination.pages || 1;
    var inner = nav.querySelector('.pakyuet-pagination__inner');
    if (!inner) return;
    var handle = getCollectionHandle();
    var basePath = getBasePath(handle);
    var tagPath = encodeTagPath(getCurrentTagPath());
    var href = function (p) {
      return basePath + (tagPath ? '/' + tagPath : '') + '?sort_by=' + (sortBy || 'manual') + '&page=' + p + '#products';
    };
    var html = '';
    if (cur <= 1) {
      html += '<span class="pakyuet-pagination__btn pakyuet-pagination__btn--arrow pakyuet-pagination__btn--disabled">&lsaquo;</span>';
    } else {
      html += '<a class="pakyuet-pagination__btn pakyuet-pagination__btn--arrow" href="' + href(cur - 1) + '" rel="prev" aria-label="上一页" data-page="' + (cur - 1) + '">&lsaquo;</a>';
    }
    html += '<div class="pakyuet-pagination__pages">';
    var pages = buildPages(cur, total);
    for (var i = 0; i < pages.length; i++) {
      var p = pages[i];
      if (p === '...') {
        html += '<span class="pakyuet-pagination__num pakyuet-pagination__num--ellipsis" aria-hidden="true">&hellip;</span>';
      } else if (p === cur) {
        html += '<span class="pakyuet-pagination__num pakyuet-pagination__num--current" aria-current="page" data-current-page="' + p + '">' + p + '</span>';
      } else {
        html += '<a class="pakyuet-pagination__num" href="' + href(p) + '" data-page="' + p + '">' + p + '</a>';
      }
    }
    html += '</div>';
    if (cur >= total) {
      html += '<span class="pakyuet-pagination__btn pakyuet-pagination__btn--arrow pakyuet-pagination__btn--disabled">&rsaquo;</span>';
    } else {
      html += '<a class="pakyuet-pagination__btn pakyuet-pagination__btn--arrow" href="' + href(cur + 1) + '" rel="next" aria-label="下一页" data-page="' + (cur + 1) + '">&rsaquo;</a>';
    }
    html += '<form class="pakyuet-pagination__jump" data-pagination-jump>';
    html += '<span class="pakyuet-pagination__jump-label">跳至</span>';
    html += '<input class="pakyuet-pagination__jump-input" type="number" min="1" max="' + total + '" placeholder="' + cur + '" aria-label="跳轉頁碼">';
    html += '<span class="pakyuet-pagination__jump-label">頁</span>';
    html += '<button type="submit" class="pakyuet-pagination__jump-btn">跳轉</button>';
    html += '</form>';

    inner.innerHTML = html;
    bindPagination(nav, sortBy);
    bindPaginationJump(nav, sortBy);
  }

  function bindPaginationJump(nav, sortBy) {
    var forms = nav.querySelectorAll('[data-pagination-jump]');
    forms.forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var input = form.querySelector('.pakyuet-pagination__jump-input');
        if (!input) return;
        var total = parseInt(input.getAttribute('max'), 10) || 1;
        var val = parseInt(input.value, 10);
        if (isNaN(val) || val < 1) val = 1;
        if (val > total) val = total;
        loadProducts(sortBy || currentState.sortBy, val);
      });
    });
  }

  function updateSortUI(sortBy) {
    var items = document.querySelectorAll('.sort-dropdown__item');
    var label = document.querySelector('[data-sort-label]');
    items.forEach(function (item) {
      var key = item.getAttribute('data-sort-key');
      item.classList.toggle('active', key === (sortBy || 'manual'));
      if (key === (sortBy || 'manual') && label) {
        label.textContent = item.textContent.trim();
      }
    });
  }

  function bindPagination(nav, sortBy) {
    var links = nav.querySelectorAll('a[data-page]');
    links.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        var page = parseInt(link.getAttribute('data-page'), 10);
        loadProducts(sortBy || currentState.sortBy, page);
      });
    });
  }

  /* ---- Sort dropdown + AJAX 排序 ---- */
  function initSortDropdown(scope) {
    var root = scope || document;
    var dropdown = root.querySelector('[data-sort-dropdown]') || document.querySelector('[data-sort-dropdown]');
    if (!dropdown || dropdown.dataset.bound === '1') return;
    dropdown.dataset.bound = '1';
    var toggle = dropdown.querySelector('[data-sort-toggle]');
    if (!toggle) return;

    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdown.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
      if (!dropdown.contains(e.target)) dropdown.classList.remove('open');
    });

    var items = dropdown.querySelectorAll('.sort-dropdown__item');
    items.forEach(function (item) {
      item.addEventListener('click', function (e) {
        e.preventDefault();
        dropdown.classList.remove('open');
        var sortBy = item.getAttribute('data-sort-key');
        loadProducts(sortBy, 1);
      });
    });

    var nav = document.querySelector('[data-pagination]');
    if (nav) {
      var initialSort = (function () {
        var params = new URLSearchParams(window.location.search);
        return params.get('sort_by') || 'manual';
      })();
      bindPagination(nav, initialSort);
      bindPaginationJump(nav, initialSort);
    }

    window.addEventListener('popstate', function (e) {
      if (e.state && e.state.sortBy) {
        loadProducts(e.state.sortBy, e.state.page || 1);
      }
    });
  }

  function initAll(scope) {
    initHeroCarousel(scope);
    initSortDropdown(scope);
    initFilterSelects(scope);
  }

  function boot() {
    initNavScroll();
    initAll(document);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  /* Shopify theme editor support */
  document.addEventListener('shopify:section:load', function (e) { initAll(e.target); });
  document.addEventListener('shopify:section:select', function (e) { initAll(e.target); });
})();
