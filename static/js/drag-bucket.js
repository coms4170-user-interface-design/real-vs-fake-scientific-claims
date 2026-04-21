(function () {
  const tray = document.getElementById("drag-tray");
  const bucketDrops = document.querySelectorAll(".bucket-drop");
  const draggables = document.querySelectorAll(".draggable-item");

  let draggedElement = null;

  draggables.forEach((item) => {
    item.addEventListener("dragstart", function (e) {
      draggedElement = item;
      item.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    });
    item.addEventListener("dragend", function () {
      item.classList.remove("dragging");
      draggedElement = null;
    });
  });

  const targets = [tray, ...bucketDrops];
  targets.forEach((target) => {
    target.addEventListener("dragover", function (e) {
      e.preventDefault();
      target.classList.add("drop-hover");
    });
    target.addEventListener("dragleave", function () {
      target.classList.remove("drop-hover");
    });
    target.addEventListener("drop", function (e) {
      e.preventDefault();
      target.classList.remove("drop-hover");
      if (draggedElement) {
        target.appendChild(draggedElement);
      }
    });
  });

  const submitBtn = document.getElementById("submit-answer");
  if (!submitBtn) return;

  submitBtn.addEventListener("click", async function () {
    const placements = {};
    document.querySelectorAll(".draggable-item").forEach((item) => {
      const bucketDrop = item.closest(".bucket-drop");
      if (bucketDrop) {
        const bucket = bucketDrop.closest(".bucket");
        placements[item.dataset.draggableId] = bucket.dataset.bucketId;
      } else {
        placements[item.dataset.draggableId] = null;
      }
    });

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/quiz/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: parseInt(submitBtn.dataset.questionId, 10),
          answer: { placements: placements },
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
