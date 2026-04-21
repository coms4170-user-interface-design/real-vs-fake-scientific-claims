(function () {
  const slider = document.getElementById("credibility-slider");
  const valueDisplay = document.getElementById("slider-value");

  slider.addEventListener("input", function () {
    valueDisplay.textContent = slider.value;
  });

  const submitBtn = document.getElementById("submit-answer");
  if (!submitBtn) return;

  submitBtn.addEventListener("click", async function () {
    const sliderValue = parseInt(slider.value, 10);
    const selected = Array.from(document.querySelectorAll(".signal-check:checked"))
      .map((el) => el.dataset.signalId);

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/quiz/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: parseInt(submitBtn.dataset.questionId, 10),
          answer: {
            slider_value: sliderValue,
            selected_signal_ids: selected,
          },
        }),
      });
      if (!res.ok) throw new Error("save failed");
      window.location.href = submitBtn.dataset.nextUrl;
    } catch (err) {
      submitBtn.disabled = false;
      alert("Could not save answer. Please try again.");
    }
  });
})();
