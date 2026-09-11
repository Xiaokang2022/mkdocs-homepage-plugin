/*!
 * mkdocs-homepage-plugin -- behaviour for the homepage blocks.
 *
 * No dependencies, no globals, and every feature is progressive: with scripting
 * off the stylesheet already hides what cannot work (the carousel buttons, the
 * reveal animation) and the markup is complete on its own.  Every binding is
 * idempotent so Material's instant navigation can re-run `init()` safely.
 */
(function () {
  "use strict";

  var REVEALED = "is-home-revealed";
  var BOUND = "homeBound";

  var observers = [];
  var listeners = [];
  var tilters = [];

  var prefersReducedMotion = function () {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  };

  var canTilt = function () {
    return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  };

  function teardown() {
    observers.forEach(function (observer) {
      try {
        observer.disconnect();
      } catch (error) {
        /* already gone */
      }
    });
    observers = [];
    listeners.forEach(function (entry) {
      entry[0].removeEventListener(entry[1], entry[2]);
    });
    listeners = [];
    tilters = [];
    // Binding markers have to go with the listeners. Material's instant
    // navigation runs `init()` again on a page it has already initialised, and
    // a marker left behind makes that second pass skip an element it has just
    // unbound -- so tilt, the typewriter and the lightbox all went silently
    // dead. The marker means "bound by the current pass", nothing more.
    Array.prototype.forEach.call(document.querySelectorAll("[data-home-bound]"), function (element) {
      delete element.dataset[BOUND];
    });
  }

  function on(target, type, handler, options) {
    target.addEventListener(type, handler, options);
    listeners.push([target, type, handler]);
  }

  function observe(elements, callback, options) {
    if (!("IntersectionObserver" in window)) {
      elements.forEach(callback);
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          observer.unobserve(entry.target);
          callback(entry.target);
        }
      });
    }, options || { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    elements.forEach(function (element) {
      observer.observe(element);
    });
    observers.push(observer);
  }

  function raf(handler) {
    var pending = false;
    var last = null;
    return function (event) {
      last = event;
      if (pending) {
        return;
      }
      pending = true;
      window.requestAnimationFrame(function () {
        pending = false;
        handler(last);
      });
    };
  }

  /* ---------------------------------------------------------------- reveal */

  function initReveal(root) {
    var targets = Array.prototype.filter.call(
      root.querySelectorAll("[data-home-reveal]"),
      function (element) {
        return !element.classList.contains(REVEALED);
      }
    );
    if (!targets.length) {
      return;
    }
    if (prefersReducedMotion()) {
      targets.forEach(function (element) {
        element.classList.add(REVEALED);
      });
      return;
    }
    observe(targets, function (element) {
      element.classList.add(REVEALED);
    });
  }

  /* ------------------------------------------------------------------ tilt */

  function applyTilt(card, strength, point) {
    var rect = card.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      return;
    }
    var px = (point.x - rect.left) / rect.width;
    var py = (point.y - rect.top) / rect.height;
    var nx = Math.min(1, Math.max(0, px)) * 2 - 1;
    var ny = Math.min(1, Math.max(0, py)) * 2 - 1;
    card.style.setProperty("--md-home-ry", (nx * strength).toFixed(2) + "deg");
    card.style.setProperty("--md-home-rx", (-ny * strength).toFixed(2) + "deg");
    card.style.setProperty("--md-home-mx", (px * 100).toFixed(1) + "%");
    card.style.setProperty("--md-home-my", (py * 100).toFixed(1) + "%");
  }

  function clearTilt(card) {
    card.style.setProperty("--md-home-ry", "0deg");
    card.style.setProperty("--md-home-rx", "0deg");
  }

  function covers(card, point) {
    var rect = card.getBoundingClientRect();
    return (
      point.x >= rect.left &&
      point.x <= rect.right &&
      point.y >= rect.top &&
      point.y <= rect.bottom
    );
  }

  function initTilt(root) {
    if (!canTilt() || prefersReducedMotion()) {
      return;
    }
    Array.prototype.forEach.call(root.querySelectorAll("[data-home-tilt]"), function (card) {
      if (card.dataset[BOUND]) {
        return;
      }
      var strength = parseFloat(card.getAttribute("data-home-tilt"));
      if (!strength || Number.isNaN(strength)) {
        return;
      }
      card.dataset[BOUND] = "1";

      // A `pointermove` only *schedules* the write, so a `pointerout` arriving
      // in the same frame used to be applied first and then overwritten by the
      // stale move -- leaving the card tilted with the pointer long gone. That
      // is the intermittent "does not spring back" bug. Ending the interaction
      // therefore cancels the pending frame instead of racing it, and a frame
      // whose stored point has been cleared does nothing when it does run.
      var point = null;
      var frame = null;
      var tilted = false;

      var write = function () {
        frame = null;
        if (point === null) {
          return;
        }
        applyTilt(card, strength, point);
        tilted = true;
      };

      var reset = function () {
        point = null;
        if (frame !== null) {
          window.cancelAnimationFrame(frame);
          frame = null;
        }
        if (tilted) {
          tilted = false;
          clearTilt(card);
        }
      };

      // The page moved under a stationary pointer. Viewport coordinates do not
      // change when the document scrolls, so the tilt is simply recomputed
      // against the card's new box -- which is better than resetting: the
      // pointer very often *is* still over the card, and a hard reset would make
      // ordinary scrolling kill the effect and drop the highlight. Only when the
      // card has genuinely moved out from under the pointer is it cleared.
      var refresh = function () {
        if (!tilted || point === null || frame !== null) {
          // A pending frame computes from the box as it will be, so leave it be.
          return;
        }
        if (covers(card, point)) {
          applyTilt(card, strength, point);
        } else {
          reset();
        }
      };

      on(card, "pointermove", function (event) {
        if (event.pointerType === "touch") {
          return;
        }
        point = { x: event.clientX, y: event.clientY };
        if (frame === null) {
          frame = window.requestAnimationFrame(write);
        }
      });

      // `pointerout` bubbles and fires in more cases than `pointerleave` (which
      // does not bubble and is skipped by some engines when the element is
      // scrolled out from under a stationary pointer). The containment check
      // keeps a move onto a child of the card -- icon, title -- from resetting.
      on(card, "pointerout", function (event) {
        if (!event.relatedTarget || !card.contains(event.relatedTarget)) {
          reset();
        }
      });
      on(card, "pointercancel", reset);
      on(card, "blur", reset);

      tilters.push({
        reset: reset,
        refresh: refresh,
        isTilted: function () {
          return tilted;
        },
      });
    });
  }

  function resetTilters() {
    for (var index = 0; index < tilters.length; index += 1) {
      if (tilters[index].isTilted()) {
        tilters[index].reset();
      }
    }
  }

  function refreshTilters() {
    for (var index = 0; index < tilters.length; index += 1) {
      tilters[index].refresh();
    }
  }

  function initTiltSafety() {
    if (!tilters.length) {
      return;
    }

    // Ways a card is left tilted that involve nothing happening *to the card*:
    // the pointer can leave the window (alt-tab, or straight off the edge)
    // without a boundary event ever arriving. There the pointer position stops
    // meaning anything, so those are a hard reset.
    on(document.documentElement, "mouseleave", resetTilters);
    on(document, "pointerleave", resetTilters);
    on(window, "blur", resetTilters);
    on(document, "visibilitychange", function () {
      if (document.hidden) {
        resetTilters();
      }
    });

    // Scrolling is different: the pointer has not moved, the *page* has.
    var scheduled = false;
    on(
      window,
      "scroll",
      function () {
        if (scheduled) {
          return;
        }
        scheduled = true;
        window.requestAnimationFrame(function () {
          scheduled = false;
          refreshTilters();
        });
      },
      { passive: true }
    );
  }

  /* -------------------------------------------------------------- carousel */

  function initGalleries(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-home-gallery]"), function (gallery) {
      var viewport = gallery.querySelector("[data-home-gallery-viewport]");
      var track = viewport && viewport.querySelector(".md-home__gallery-track");
      var slides = track ? Array.prototype.slice.call(track.children) : [];
      if (!viewport || slides.length < 2) {
        return;
      }
      var paged = gallery.getAttribute("data-home-gallery") === "paged";
      var previous = gallery.querySelector("[data-home-gallery-prev]");
      var next = gallery.querySelector("[data-home-gallery-next]");
      var dots = gallery.querySelector(".md-home__gallery-dots");
      var built = false;

      function perView() {
        var size = slides[0].getBoundingClientRect().width;
        return size ? Math.max(1, Math.round(viewport.clientWidth / size)) : 1;
      }

      function pageCount() {
        return paged ? Math.max(1, Math.ceil(slides.length / perView())) : slides.length;
      }

      function currentPage() {
        var size = slides[0].getBoundingClientRect().width;
        if (!size) {
          return 0;
        }
        return paged
          ? Math.round(viewport.scrollLeft / (size * perView()))
          : Math.round(viewport.scrollLeft / size);
      }

      function buildDots() {
        if (!dots) {
          return;
        }
        var total = pageCount();
        if (built && dots.children.length === total) {
          return;
        }
        dots.textContent = "";
        for (var index = 0; index < total; index += 1) {
          var dot = document.createElement("button");
          dot.type = "button";
          dot.className = "md-home__gallery-dot";
          dot.setAttribute("role", "tab");
          dot.setAttribute("aria-label", "第 " + (index + 1) + " 页");
          dot.dataset.page = String(index);
          dot.addEventListener(
            "click",
            (function (page) {
              return function () {
                goTo(page);
              };
            })(index)
          );
          dots.appendChild(dot);
        }
        built = true;
      }

      function goTo(page) {
        var size = slides[0].getBoundingClientRect().width;
        var offset = paged ? page * size * perView() : page * size;
        viewport.scrollTo({ left: offset, behavior: prefersReducedMotion() ? "auto" : "smooth" });
      }

      function sync() {
        buildDots();
        var page = Math.min(Math.max(currentPage(), 0), pageCount() - 1);
        if (dots) {
          Array.prototype.forEach.call(dots.children, function (dot, index) {
            dot.setAttribute("aria-selected", index === page ? "true" : "false");
          });
        }
        var atStart = viewport.scrollLeft <= 1;
        var atEnd = viewport.scrollLeft + viewport.clientWidth >= viewport.scrollWidth - 1;
        if (previous) {
          previous.disabled = atStart;
        }
        if (next) {
          next.disabled = atEnd;
        }
      }

      function step(direction) {
        goTo(Math.min(Math.max(currentPage() + direction, 0), pageCount() - 1));
      }

      if (previous) {
        on(previous, "click", function () {
          step(-1);
        });
      }
      if (next) {
        on(next, "click", function () {
          step(1);
        });
      }
      on(viewport, "scroll", raf(sync), { passive: true });
      on(window, "resize", raf(sync));
      on(gallery, "keydown", function (event) {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          step(-1);
        } else if (event.key === "ArrowRight") {
          event.preventDefault();
          step(1);
        }
      });

      sync();
    });
  }

  /* ---------------------------------------------------------------- counts */

  function initCounters(root) {
    var counters = root.querySelectorAll("[data-home-count]");
    if (!counters.length) {
      return;
    }
    observe(Array.prototype.slice.call(counters), function (element) {
      var target = parseFloat(element.getAttribute("data-home-count"));
      if (Number.isNaN(target)) {
        return;
      }
      var decimals = parseInt(element.getAttribute("data-home-decimals") || "0", 10) || 0;
      var format = function (value) {
        return value.toFixed(decimals);
      };
      if (prefersReducedMotion()) {
        element.textContent = format(target);
        return;
      }
      var duration = 1100;
      var start = null;
      var tick = function (timestamp) {
        if (start === null) {
          start = timestamp;
        }
        var progress = Math.min(1, (timestamp - start) / duration);
        var eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = format(target * eased);
        if (progress < 1) {
          window.requestAnimationFrame(tick);
        } else {
          element.textContent = format(target);
        }
      };
      window.requestAnimationFrame(tick);
    });
  }

  /* ------------------------------------------------------------ typewriter */

  function initTypewriters(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-home-typewriter]"), function (node) {
      if (node.dataset[BOUND]) {
        return;
      }
      node.dataset[BOUND] = "1";
      var body = node.querySelector(".md-home__anim-body");
      var text = node.getAttribute("data-home-type-text") || "";
      if (!body || !text) {
        return;
      }
      if (prefersReducedMotion()) {
        body.textContent = text;
        return;
      }
      observe([node], function () {
        body.textContent = "";
        var index = 0;
        var timer = null;
        var step = function () {
          index += 1;
          body.textContent = text.slice(0, index);
          if (index < text.length) {
            timer = window.setTimeout(step, 40 + Math.random() * 70);
          }
        };
        on(node, "mouseenter", function () {
          if (timer) {
            window.clearTimeout(timer);
            timer = null;
          }
          body.textContent = text;
        });
        step();
      });
    });
  }

  /* -------------------------------------------------------------- lightbox */

  var lightbox = null;

  function buildLightbox() {
    var box = document.createElement("div");
    box.className = "md-home-lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    // The close glyph is drawn in CSS: a copied SVG path is a silent failure mode
    // (a wrong `d` still renders a valid, invisible shape).
    box.innerHTML =
      '<button type="button" class="md-home-lightbox__close" aria-label="关闭"></button>' +
      '<img alt="">' +
      '<p class="md-home-lightbox__caption"></p>';
    box.addEventListener("click", function (event) {
      if (event.target === box || event.target.closest(".md-home-lightbox__close")) {
        closeLightbox();
      }
    });
    document.body.appendChild(box);
    return box;
  }

  function closeLightbox() {
    if (!lightbox) {
      return;
    }
    lightbox.hidden = true;
    document.documentElement.style.removeProperty("overflow");
  }

  function openLightbox(source, alt, caption) {
    lightbox = lightbox || buildLightbox();
    var image = lightbox.querySelector("img");
    var label = lightbox.querySelector(".md-home-lightbox__caption");
    image.src = source;
    image.alt = alt || "";
    label.textContent = caption || "";
    label.hidden = !caption;
    lightbox.hidden = false;
    document.documentElement.style.overflow = "hidden";
    lightbox.querySelector(".md-home-lightbox__close").focus();
  }

  function initLightbox(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-home-zoom]"), function (link) {
      if (link.dataset[BOUND]) {
        return;
      }
      link.dataset[BOUND] = "1";
      on(link, "click", function (event) {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.button) {
          return;
        }
        var image = link.querySelector("img");
        if (!image) {
          return;
        }
        var figure = link.closest(".md-home__figure");
        var caption = figure && figure.querySelector(".md-home__caption");
        event.preventDefault();
        openLightbox(image.currentSrc || image.src, image.alt, caption ? caption.textContent : "");
      });
    });
  }

  /* ------------------------------------------------------------------ boot */

  function init() {
    teardown();
    var root = document;
    initReveal(root);
    initTilt(root);
    initTiltSafety();
    initGalleries(root);
    initCounters(root);
    initTypewriters(root);
    initLightbox(root);
    on(document, "keydown", function (event) {
      if (event.key === "Escape") {
        closeLightbox();
      }
    });
    // A stamp that says "this pass completed". A stale cached asset is the most
    // common reason this file appears not to work, and without a marker a
    // half-initialised page is indistinguishable from an old copy.
    document.documentElement.setAttribute("data-home-ready", "");
  }

  function boot() {
    if (window.document$ && typeof window.document$.subscribe === "function") {
      // Material's instant navigation replaces the content and emits here.
      window.document$.subscribe(init);
      return;
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }

  boot();
})();
