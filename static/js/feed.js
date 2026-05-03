(function () {
  const cards = document.querySelectorAll(".feed-card");
  cards.forEach((card) => {
    const type = card.dataset.questionType;
    if (type === "swipe_verdict") {
      initSwipeVerdict(card);
    }
  });

  function initSwipeVerdict(card) {
    const buttons = card.querySelectorAll(".verdict-btn");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => handleVerdict(card, btn.dataset.verdict));
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

    result.innerHTML = `
      <div class="result-row">${youSaid}${actual}</div>
      <p class="why-text">${escapeHtml(why || "")}</p>
      ${signals.length ? `<div class="signals-row">${signalChips}</div>` : ""}
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
