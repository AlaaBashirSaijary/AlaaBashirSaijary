(function () {
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Headline: wrap each word so it rises into place (the text itself is already in the HTML).
  var h1 = document.getElementById('h1');
  if (h1) {
    var tmp = document.createElement('div'); tmp.innerHTML = h1.innerHTML;
    var toks = [];
    (function walk(n, em) {
      n.childNodes.forEach(function (c) {
        if (c.nodeType === 3) {
          c.textContent.split(/\s+/).filter(Boolean).forEach(function (w) { toks.push({ w: w, em: em }); });
        } else walk(c, em || c.nodeName === 'EM');
      });
    })(tmp, false);
    // Keep neighbouring Latin words together ("Education ERP") so right-to-left pages do not reverse them.
    var units = [];
    toks.forEach(function (t) {
      var last = units[units.length - 1];
      if (last && last.em === t.em && /^[\x00-\x7F]+$/.test(t.w) && /^[\x00-\x7F ]+$/.test(last.w)) last.w += ' ' + t.w;
      else units.push({ w: t.w, em: t.em });
    });
    var out = units.map(function (u, i) {
      return '<span style="margin-inline-end:.25em"><i style="--i:' + i + '">' + (u.em ? '<em>' + u.w + '</em>' : u.w) + '</i></span>';
    }).join('');
    h1.setAttribute('aria-label', h1.textContent.replace(/\s+/g, ' ').trim());
    h1.innerHTML = out;
    requestAnimationFrame(function () { requestAnimationFrame(function () { h1.classList.add('in'); }); });
  }

  // Counters count up from 0; the final number is already in the HTML.
  function count(el) {
    var to = +el.dataset.count, suf = el.dataset.suffix || '', t0 = null, dur = 1600;
    if (reduce || !to) return;
    el.textContent = '0' + suf;
    (function step(t) {
      if (!t0) t0 = t;
      var p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 4);
      el.textContent = Math.round(to * e).toLocaleString('en') + suf;
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  }

  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target; el.classList.add('in'); io.unobserve(el);
      el.querySelectorAll('[data-count]').forEach(count);
      el.querySelectorAll('.bar i').forEach(function (b) { b.style.width = b.style.getPropertyValue('--w'); });
    });
  }, { threshold: .15 });
  document.querySelectorAll('.rv,.tl').forEach(function (el) { io.observe(el); });

  // Mobile menu
  var burger = document.getElementById('burger'), menu = document.getElementById('menu');
  function toggle(open) { burger.setAttribute('aria-expanded', open); menu.classList.toggle('open', open); }
  burger.addEventListener('click', function () { toggle(burger.getAttribute('aria-expanded') !== 'true'); });
  menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { toggle(false); }); });
  addEventListener('keydown', function (e) { if (e.key === 'Escape') toggle(false); });
  addEventListener('resize', function () { if (innerWidth > 860) toggle(false); });

  // Scroll progress + sticky shadow
  var prog = document.getElementById('progress'), nav = document.getElementById('nav');
  addEventListener('scroll', function () {
    var h = document.documentElement.scrollHeight - innerHeight;
    prog.style.transform = 'scaleX(' + (scrollY / h) + ')'; nav.classList.toggle('stuck', scrollY > 40);
  }, { passive: true });

  // Hero: glow follows the pointer, phone tilts
  var hero = document.getElementById('hero'), phone = document.getElementById('phone');
  if (hero) {
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      hero.style.setProperty('--mx', (x * 100) + '%'); hero.style.setProperty('--my', (y * 100) + '%');
      if (phone && !reduce) phone.style.transform = 'rotateY(' + (-14 + (x - .5) * 22) + 'deg) rotateX(' + (4 - (y - .5) * 14) + 'deg)';
    });
    hero.addEventListener('pointerleave', function () { if (phone) phone.style.transform = ''; });
  }

  // Visit statistics events: WhatsApp, email, downloads, outbound links, video play.
  // Does nothing until src/analytics.json names a provider (window.__ANALYTICS is then set).
  var cfg = window.__ANALYTICS;
  if (cfg && navigator.doNotTrack !== '1') {
    var pageKey = document.body.getAttribute('data-page') || 'page';
    var send = function (name, section, target) {
      var path = name + '/' + pageKey + '/' + section;
      if (cfg.provider === 'goatcounter' && window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({ path: path, title: name + (target ? ': ' + target : ''), event: true });
      } else if (cfg.provider === 'plausible' && window.plausible) {
        window.plausible(name, { props: { page: pageKey, section: section, target: target || '' } });
      } else if (cfg.provider === 'ga4' && window.gtag) {
        window.gtag('event', name, { page: pageKey, section: section, target: target || '' });
      }
    };
    var sectionOf = function (a) {
      if (a.classList.contains('wa-float')) return 'floating-button';
      var s = a.closest('section, header, footer, .topbar');
      if (!s) return 'page';
      return s.id || (s.className || '').split(' ')[0] || s.tagName.toLowerCase();
    };
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a) return;
      var href = a.getAttribute('href') || '';
      var where = sectionOf(a);
      if (/^https?:\/\/(wa\.me|api\.whatsapp\.com)\//.test(href)) send('whatsapp-click', where);
      else if (/^mailto:/.test(href)) send('email-click', where);
      else if (/\.(pdf|apk)(\?|$)/i.test(href)) send('download', where, href.split('/').pop().split('?')[0]);
      else if (a.hostname && a.hostname !== location.hostname) send('outbound-click', where, a.hostname + a.pathname.replace(/\/$/, ''));
    }, true);
    var video = document.querySelector('video');
    if (video) video.addEventListener('play', function () { send('video-play', 'video'); }, { once: true });
  }
})();
