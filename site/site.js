/* Small enhancements only: switch fictional runs, run the rubric scorer, and give honest clipboard feedback. */
'use strict';

const select = document.querySelector('#example-select');
const stamp = document.querySelector('#trace-stamp');

function showExample(id) {
  for (const node of document.querySelectorAll('[data-example]')) node.hidden = node.dataset.example !== id;
  const panel = document.querySelector(`.example-content[data-example="${id}"]`);
  if (panel && stamp) stamp.textContent = panel.dataset.outcome;
}

if (select) {
  select.addEventListener('change', () => showExample(select.value));
  showExample(select.value);
}

function openSkillSource() {
  if (location.hash === '#skill-source') document.querySelector('#skill-source').open = true;
}
window.addEventListener('hashchange', openSkillSource);
openSkillSource();

async function copyFrom(target, status, done) {
    const content = target instanceof HTMLTextAreaElement ? target.value : target.textContent;
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(content);
      status.textContent = done;
    } catch {
      // Keep a manual path when a browser denies clipboard access. Do not claim success.
      if (target instanceof HTMLTextAreaElement) {
        target.focus();
        target.select();
      } else {
        const range = document.createRange();
        range.selectNodeContents(target);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
      status.textContent = 'Clipboard unavailable. The text is selected; use your browser’s Copy command.';
    }
}

document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', () => {
    const skill = button.dataset.copy === 'skill-text';
    copyFrom(document.getElementById(button.dataset.copy), document.getElementById(skill ? 'skill-copy-status' : 'copy-status'), skill ? 'SKILL.md copied.' : 'Starting prompt copied.');
  });
});

// The scorer applies the same zone rule as the skill. Nothing is stored or sent.
const CORE = ['Job', 'First value', 'Fit', 'Outcome', 'Trust'];
const scorer = document.querySelector('.scorer');

function readScores() {
  const scores = {};
  for (const select of scorer.querySelectorAll('select')) {
    scores[select.dataset.criterion] = scores[select.dataset.criterion] || {};
    scores[select.dataset.criterion][select.dataset.kind] = select.value;
  }
  return scores;
}

function judge(scores) {
  const holding = [];
  for (const name of CORE) {
    const { rating, grade } = scores[name];
    if (rating !== 'Solid') holding.push(`${name} is ${rating}`);
    else if (grade === 'Claimed') holding.push(`${name} is only claimed`);
  }
  const ready = holding.length === 0;
  const r = scores.Return;
  const worth = ready && r.rating === 'Solid' && r.grade === 'Repeated';
  return { ready, worth, holding, returnNote: r.rating === 'Solid' && r.grade !== 'Repeated' ? 'Return needs people coming back, shown more than once.' : '' };
}

function cardText(scores, result) {
  const tool = document.getElementById('tool-name').value.trim() || '<tool>';
  const user = document.getElementById('tool-user').value.trim() || '<named person> · <recurring job>';
  const pad = s => (s + ' '.repeat(14)).slice(0, 14);
  const rows = Object.entries(scores).map(([name, s]) => `${pad(name)}${s.rating} · ${s.grade} · <one line>`);
  const zone = result.worth ? 'Stranger-ready met · Worth using met' : result.ready ? 'Stranger-ready met · Worth using not yet' : `Stranger-ready not yet (${result.holding.join('; ')}) · Worth using not yet`;
  return [`USEFULNESS CARD · ${tool} · score only`, `${pad('User + job')}${user}`, ...rows, `${pad('Zone')}${zone}`, `${pad('Return check')}<who> · <when> · <what counts as coming back>`, `${pad('Cut')}<what was removed, or "nothing">`].join('\n');
}

function updateScorer() {
  const scores = readScores();
  const result = judge(scores);
  const box = scorer.querySelector('.scorer-result');
  box.classList.toggle('is-ready', result.ready && !result.worth);
  box.classList.toggle('is-worth', result.worth);
  document.getElementById('verdict').textContent = result.worth ? 'Worth using.' : result.ready ? 'Stranger-ready. Worth using not shown yet.' : 'No zone yet.';
  document.getElementById('holding').textContent = result.worth
    ? 'Every criterion is Solid with evidence, and people come back. Keep watching; zones can be lost.'
    : result.ready
      ? `Set a return check: who, when, and what counts as coming back. ${result.returnNote}`.trim()
      : `Holding it back: ${result.holding.join('; ')}.`;
  document.getElementById('card-text').textContent = cardText(scores, result);
}

if (scorer) {
  scorer.addEventListener('change', updateScorer);
  scorer.addEventListener('input', updateScorer);
  document.getElementById('copy-card').addEventListener('click', () => {
    const pre = document.getElementById('card-text');
    pre.hidden = false;
    copyFrom(pre, document.getElementById('card-status'), 'Usefulness card copied. Fill in the one-line reasons.');
  });
  document.getElementById('reset-card').addEventListener('click', () => {
    for (const select of scorer.querySelectorAll('select')) select.selectedIndex = 0;
    for (const input of scorer.querySelectorAll('input')) input.value = '';
    document.getElementById('card-text').hidden = true;
    document.getElementById('card-status').textContent = '';
    updateScorer();
  });
  updateScorer();
}
