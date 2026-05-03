(function () {
  const lessonsById = loadLessons();

  document.querySelectorAll(".feed-card").forEach((card) => {
    if (card.dataset.questionType === "swipe_verdict") {
      initSwipeVerdict(card);
    }
  });

  function loadLessons() {
    const node = document.getElementById("lessons-data");
    if (!node) return {};
    try {
      return JSON.parse(node.textContent);
    } catch (e) {
      return {};
    }
  }

  function initSwipeVerdict(card) {
    card.querySelectorAll(".verdict-btn").forEach((btn) => {
      btn.addEventListener("click", () => handleVerdict(card, btn.dataset.verdict));
    });
    attachSwipe(card);
  }

  function attachSwipe(card) {
    let startX = 0;
    let currentX = 0;
    let isDragging = false;
    let pointerId = null;

    const SWIPE_THRESHOLD = 100; // px past which the swipe commits
    const ROTATION_DIVISOR = 25; // larger = gentler tilt
    const OVERLAY_FULL = 120; // px at which overlay is fully opaque

    card.addEventListener("pointerdown", onPointerDown);
    card.addEventListener("pointermove", onPointerMove);
    card.addEventListener("pointerup", onPointerEnd);
    card.addEventListener("pointercancel", onPointerEnd);

    function onPointerDown(e) {
      if (card.classList.contains("submitted")) return;
      // Let buttons handle their own clicks
      if (e.target.closest(".verdict-btn")) return;
      isDragging = true;
      pointerId = e.pointerId;
      startX = e.clientX;
      currentX = 0;
      card.classList.add("dragging");
      card.style.transition = "none";
      try { card.setPointerCapture(pointerId); } catch (_) {}
    }

    function onPointerMove(e) {
      if (!isDragging || e.pointerId !== pointerId) return;
      currentX = e.clientX - startX;
      const rotation = currentX / ROTATION_DIVISOR;
      card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;
      const progress = Math.min(1, Math.abs(currentX) / OVERLAY_FULL);
      card.style.setProperty("--swipe-progress", progress);
      card.dataset.swipeDirection = currentX > 0 ? "real" : currentX < 0 ? "fake" : "";
    }

    function onPointerEnd(e) {
      if (!isDragging || e.pointerId !== pointerId) return;
      isDragging = false;
      card.classList.remove("dragging");
      try { card.releasePointerCapture(pointerId); } catch (_) {}

      if (Math.abs(currentX) > SWIPE_THRESHOLD) {
        const verdict = currentX > 0 ? "real" : "fake";
        flyOff(card, currentX > 0 ? 1 : -1).then(() => {
          card.style.transition = "none";
          card.style.transform = "";
          card.style.setProperty("--swipe-progress", 0);
          card.dataset.swipeDirection = "";
          requestAnimationFrame(() => { card.style.transition = ""; });
          handleVerdict(card, verdict);
        });
      } else {
        card.style.transition = "transform 0.2s ease-out";
        card.style.transform = "";
        card.style.setProperty("--swipe-progress", 0);
        card.dataset.swipeDirection = "";
        setTimeout(() => { card.style.transition = ""; }, 220);
      }
      currentX = 0;
      pointerId = null;
    }
  }

  function flyOff(card, direction) {
    return new Promise((resolve) => {
      const flyX = direction * (window.innerWidth || 600);
      card.style.transition = "transform 0.25s ease-out, opacity 0.25s ease-out";
      card.style.transform = `translateX(${flyX}px) rotate(${direction * 22}deg)`;
      card.style.opacity = "0";
      setTimeout(() => {
        card.style.opacity = "";
        resolve();
      }, 260);
    });
  }

  async function handleVerdict(card, verdict) {
    const buttons = card.querySelectorAll(".verdict-btn");
    buttons.forEach((b) => (b.disabled = true));

    const qid = parseInt(card.dataset.questionId, 10);
    const mode = card.dataset.mode || "feed";

    try {
      const res = await fetch("/api/quiz/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: qid,
          answer: { verdict: verdict },
          mode: mode,
        }),
      });
      if (!res.ok) throw new Error("save failed");
      renderResult(card, verdict);
    } catch (err) {
      buttons.forEach((b) => (b.disabled = false));
      alert("Could not save your answer. Please try again.");
    }
  }

  function renderResult(card, userVerdict) {
    const correctVerdict = card.dataset.correctVerdict;
    const why = card.dataset.why;
    const signals = (card.dataset.signals || "").split(",").filter(Boolean);
    const lessonId = card.dataset.lessonId;

    const isCorrect = userVerdict === correctVerdict;
    card.classList.add("submitted", isCorrect ? "user-correct" : "user-wrong");

    const result = card.querySelector(".card-result");
    result.classList.remove("d-none");
    result.classList.add(isCorrect ? "correct" : "wrong");

    const verdictLabel = (v) => (v === "real" ? "Real" : "Fake");
    const youSaid = isCorrect
      ? `<span class="verdict-tag user-pick">You said ${verdictLabel(userVerdict)} ✓</span>`
      : `<span class="verdict-tag user-pick was-wrong">You said ${verdictLabel(userVerdict)} ✗</span>`;
    const actual = `<span class="verdict-tag actual">Actually: ${verdictLabel(correctVerdict)}</span>`;

    const signalChips = signals
      .map((s) => `<span class="signal-chip">${escapeHtml(s)}</span>`)
      .join("");

    const lesson = !isCorrect && lessonId ? lessonsById[lessonId] : null;
    const lessonHtml = lesson ? renderLesson(lesson) : "";

    result.innerHTML = `
      <div class="result-row">${youSaid}${actual}</div>
      <p class="why-text">${escapeHtml(why || "")}</p>
      ${signals.length ? `<div class="signals-row">${signalChips}</div>` : ""}
      ${lessonHtml}
    `;
  }

  function renderLesson(lesson) {
    let body = "";
    if (lesson.type === "three_signals" || lesson.type === "recap") {
      body = renderThreeSignals(lesson);
    } else if (lesson.type === "signal_detail") {
      body = renderSignalDetail(lesson);
    } else if (lesson.type === "comparison") {
      body = renderComparison(lesson);
    } else {
      body = `<div class="lesson-fallback">Open the full lesson to learn more.</div>`;
    }
    return `
      <section class="lesson-block">
        <header class="lesson-block-header">
          <span class="lesson-tag">Lesson</span>
          <span class="lesson-block-title">${escapeHtml(lesson.title || "")}</span>
        </header>
        ${body}
      </section>
    `;
  }

  function renderThreeSignals(lesson) {
    const signals = lesson.signals || [];
    const items = signals
      .map(
        (s) => `
          <li class="lesson-signal lesson-signal-${escapeHtml(s.color || "teal")}">
            <span class="lesson-signal-num">${escapeHtml(String(s.number ?? ""))}</span>
            <div>
              <div class="lesson-signal-name">${escapeHtml(s.name || "")}</div>
              <div class="lesson-signal-body">${escapeHtml(s.body || "")}</div>
            </div>
          </li>`
      )
      .join("");
    return `<ul class="lesson-signal-list">${items}</ul>`;
  }

  function renderSignalDetail(lesson) {
    const annotations = lesson.annotations || [];
    const items = annotations
      .map(
        (a) => `
          <li class="lesson-annotation lesson-annotation-${escapeHtml(a.color || "teal")}">
            <div class="lesson-annotation-title">${escapeHtml(a.title || "")}</div>
            <div class="lesson-annotation-body">${escapeHtml(a.body || "")}</div>
          </li>`
      )
      .join("");
    return `<ul class="lesson-annotation-list">${items}</ul>`;
  }

  function renderComparison(lesson) {
    const subtitle = lesson.subtitle ? `<p class="lesson-subtitle">${escapeHtml(lesson.subtitle)}</p>` : "";
    const sideHtml = (label, side, cls) => {
      if (!side) return "";
      const checks = (side.checks || [])
        .map((c) => `<li>${escapeHtml(c)}</li>`)
        .join("");
      return `
        <div class="lesson-compare-side ${cls}">
          <div class="lesson-compare-label">${label} · ${escapeHtml(side.username || "")}</div>
          <ul>${checks}</ul>
        </div>`;
    };
    return `
      ${subtitle}
      <div class="lesson-compare">
        ${sideHtml("✓ Real", lesson.good, "is-good")}
        ${sideHtml("✗ Fake", lesson.bad, "is-bad")}
      </div>
    `;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
