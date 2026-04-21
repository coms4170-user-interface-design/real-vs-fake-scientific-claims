function selectOption(el, type) {
  if (type === 'single') {
    document.querySelectorAll('.option-card').forEach(c => {
      c.classList.remove('selected');
      c.querySelector('.opt-input').checked = false;
    });
  }
  el.classList.toggle('selected');
  const input = el.querySelector('.opt-input');
  input.checked = !input.checked;

  const anySelected = 
document.querySelectorAll('.option-card.selected').length > 0;
  document.getElementById('submit-btn').disabled = !anySelected;
}

document.getElementById('quiz-form').addEventListener('submit', 
function(e) {
  const selected = [...document.querySelectorAll('.option-card.selected')]
    .map(c => c.dataset.value).sort().join(',');
  document.querySelectorAll('.opt-input').forEach(i => i.disabled = true);
  const hidden = document.createElement('input');
  hidden.type = 'hidden';
  hidden.name = 'answer';
  hidden.value = selected;
  this.appendChild(hidden);
  document.querySelectorAll('[name="answer"]').forEach(i => {
    if (i !== hidden) i.name = '_disabled';
  });
});
