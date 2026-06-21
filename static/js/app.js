// Tip forms – AJAX save
document.addEventListener('DOMContentLoaded', () => {
  // Prevent card navigation when clicking inside tip forms or buttons
  document.querySelectorAll('.match-card input, .match-card button, .match-card select').forEach(el => {
    el.addEventListener('click', e => e.stopPropagation());
  });

  // Round filter
  const tabs = document.querySelectorAll('#roundTabs .nav-link');
  const cards = document.querySelectorAll('.match-card');

  const groupTables = document.querySelectorAll('.group-table-section');

  tabs.forEach(tab => {
    tab.addEventListener('click', e => {
      e.preventDefault();
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const round = tab.dataset.round;

      // Match cards
      cards.forEach(card => {
        card.style.display = (round === 'all' || card.dataset.round === round) ? '' : 'none';
      });

      // Gruppentabellen
      groupTables.forEach(tbl => {
        tbl.classList.toggle('d-none', tbl.dataset.tableRound !== round);
      });
    });
  });

  // Tip save via AJAX
  document.querySelectorAll('.tip-form').forEach(form => {
    const matchId = form.dataset.matchId;
    const statusEl = form.querySelector('.save-status');

    const save = () => {
      const s1 = form.querySelector('[name=tip_score1]').value;
      const s2 = form.querySelector('[name=tip_score2]').value;
      if (s1 === '' || s2 === '') return;

      const fd = new FormData();
      fd.append('tip_score1', s1);
      fd.append('tip_score2', s2);

      fetch(`/tip/${matchId}`, { method: 'POST', body: fd })
        .then(r => {
          if (r.ok) {
            statusEl.classList.remove('d-none');
            setTimeout(() => statusEl.classList.add('d-none'), 2000);
          }
        });
    };

    form.addEventListener('submit', e => {
      e.preventDefault();
      save();
    });

    // Auto-save on blur when both fields filled
    form.querySelectorAll('.score-input').forEach(inp => {
      inp.addEventListener('change', () => {
        const s1 = form.querySelector('[name=tip_score1]').value;
        const s2 = form.querySelector('[name=tip_score2]').value;
        if (s1 !== '' && s2 !== '') save();
      });
    });
  });
});
