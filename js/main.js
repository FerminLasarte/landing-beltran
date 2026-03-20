/* ════════════════════════════════════════════════════
   main.js — Core interactions
   - Sophisticated smooth scroll (easeInOutQuint curve)
   - Navbar scroll state
   - Mobile menu toggle
   - Reveal animations (IntersectionObserver)
   - Counter animation (ease-out cubic)
════════════════════════════════════════════════════ */

/* ─────────────────────────────────────────────────────
   1. SMOOTH SCROLL — easeInOutQuint for premium feel
─────────────────────────────────────────────────────── */

function easeInOutQuint(t) {
  return t < 0.5
    ? 16 * t * t * t * t * t
    : 1 - Math.pow(-2 * t + 2, 5) / 2;
}

function smoothScrollTo(targetY, duration) {
  duration  = duration || 960;
  var startY    = window.pageYOffset;
  var distance  = targetY - startY;
  var startTime = null;

  function step(now) {
    if (!startTime) startTime = now;
    var elapsed  = now - startTime;
    var progress = Math.min(elapsed / duration, 1);
    window.scrollTo(0, startY + distance * easeInOutQuint(progress));
    if (elapsed < duration) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* Intercept all anchor clicks with href="#section" */
document.addEventListener('click', function (e) {
  var link = e.target.closest('a[href^="#"]');
  if (!link) return;

  var targetId = link.getAttribute('href').slice(1);
  if (!targetId) return;

  var targetEl = document.getElementById(targetId);
  if (!targetEl) return;

  e.preventDefault();

  /* Close mobile menu when a mobile nav link is tapped */
  if (link.hasAttribute('data-mobile')) closeMobileMenu();

  var navH    = document.getElementById('navbar').offsetHeight;
  var targetY = targetEl.getBoundingClientRect().top + window.pageYOffset - navH;
  smoothScrollTo(targetY, 980);
});


/* ─────────────────────────────────────────────────────
   2. NAVBAR — adds .scrolled class after 60px
─────────────────────────────────────────────────────── */

var navbar = document.getElementById('navbar');
window.addEventListener('scroll', function () {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
}, { passive: true });


/* ─────────────────────────────────────────────────────
   3. MOBILE MENU — visibility/opacity toggle (no bleed)
─────────────────────────────────────────────────────── */

var menuBtn    = document.getElementById('menu-btn');
var mobileMenu = document.getElementById('mobile-menu');
var menuOpen   = false;

menuBtn.addEventListener('click', function () {
  menuOpen = !menuOpen;
  mobileMenu.classList.toggle('open', menuOpen);
  menuBtn.querySelector('i').className = menuOpen
    ? 'fa-solid fa-xmark text-xl'
    : 'fa-solid fa-bars text-xl';
});

function closeMobileMenu() {
  menuOpen = false;
  mobileMenu.classList.remove('open');
  menuBtn.querySelector('i').className = 'fa-solid fa-bars text-xl';
}


/* ─────────────────────────────────────────────────────
   4. REVEAL ANIMATIONS — IntersectionObserver
─────────────────────────────────────────────────────── */

var revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');

var revealObserver = new IntersectionObserver(function (entries) {
  entries.forEach(function (entry) {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

revealEls.forEach(function (el) { revealObserver.observe(el); });


/* ─────────────────────────────────────────────────────
   5. COUNTER ANIMATION — ease-out cubic
─────────────────────────────────────────────────────── */

function animateCounter(el) {
  var target    = parseInt(el.getAttribute('data-target'), 10);
  var duration  = 2200;
  var startTime = performance.now();

  function tick(now) {
    var elapsed  = now - startTime;
    var progress = Math.min(elapsed / duration, 1);
    var ease     = 1 - Math.pow(1 - progress, 3); /* ease-out cubic */
    el.textContent = Math.floor(ease * target).toLocaleString('es-AR');
    if (progress < 1) requestAnimationFrame(tick);
    else el.textContent = target.toLocaleString('es-AR');
  }
  requestAnimationFrame(tick);
}

var counterObserver = new IntersectionObserver(function (entries) {
  entries.forEach(function (entry) {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.counter').forEach(function (el) {
  counterObserver.observe(el);
});
