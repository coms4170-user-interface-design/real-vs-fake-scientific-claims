(function () {
  const spans = document.querySelectorAll(".flaggable");
  spans.forEach((span) => {
    span.addEventListener("click", function () {
      span.classList.toggle("selected");
    });
  });

  const submitBtn = document.getElementById("submit-answer");
  if (!submitBtn) return;

  submitBtn.addEventListener("click", async function () {
    const selected = Array.from(document.querySelectorAll(".flaggable.selected"))
      .map((el) => el.dataset.flagId);
    const questionId = parseInt(submitBtn.dataset.questionId, 10);
    const nextUrl = submitBtn.dataset.nextUrl;

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/quiz/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: questionId,
          answer: { selected_ids: selected },
        }),
      });
      if (!res.ok) throw new Error("save failed");
      window.location.href = nextUrl;
    } catch (err) {
      submitBtn.disabled = false;
      alert("Could not save answer. Please try again.");
    }
  });
})();
