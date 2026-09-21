/* テーマ切替 + 全ページ共通の業界検索（assets/nav.js の NAV を使う） */
(function () {
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem('gyokai-theme');
    if (saved) root.setAttribute('data-theme', saved);
  } catch (e) {}

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-theme-toggle]');
    if (!btn) return;
    var dark = root.getAttribute('data-theme') === 'dark' ||
      (!root.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('gyokai-theme', next); } catch (e) {}
  });

  /* 用語チップの共通ツールチップ。表のスクロール領域に切られないよう body 直下へ表示する。 */
  var termTip = document.createElement('div');
  termTip.id = 'term-tooltip';
  termTip.className = 'term-tooltip';
  termTip.setAttribute('role', 'tooltip');
  termTip.setAttribute('aria-hidden', 'true');
  var termTipLabel = document.createElement('span');
  termTipLabel.className = 'term-tooltip-label';
  var termTipDescription = document.createElement('span');
  termTipDescription.className = 'term-tooltip-description';
  termTip.appendChild(termTipLabel);
  termTip.appendChild(termTipDescription);
  document.body.appendChild(termTip);
  var activeTerm = null;
  var termTipFrame = 0;

  function placeTermTip(chip) {
    var text = chip && chip.getAttribute('data-tooltip');
    if (!text) return;
    if (termTipFrame) cancelAnimationFrame(termTipFrame);
    activeTerm = chip;
    termTipLabel.textContent = chip.textContent.trim();
    termTipDescription.textContent = text;
    termTip.classList.remove('is-visible', 'is-above');
    termTip.classList.add('is-measuring');
    chip.setAttribute('aria-describedby', termTip.id);

    var rect = chip.getBoundingClientRect();
    var tipRect = termTip.getBoundingClientRect();
    var gap = 10;
    var edge = 12;
    var targetCenter = rect.left + rect.width / 2;
    var left = targetCenter - tipRect.width / 2;
    left = Math.min(Math.max(edge, left), window.innerWidth - tipRect.width - edge);
    var top = rect.bottom + gap;
    var above = false;
    if (top + tipRect.height > window.innerHeight - 12 && rect.top > tipRect.height + gap) {
      top = rect.top - tipRect.height - gap;
      above = true;
    }
    var arrowX = Math.min(Math.max(14, targetCenter - left), tipRect.width - 14);
    termTip.style.left = Math.round(left) + 'px';
    termTip.style.top = Math.round(top) + 'px';
    termTip.style.setProperty('--arrow-x', Math.round(arrowX) + 'px');
    termTip.classList.toggle('is-above', above);
    termTip.classList.remove('is-measuring');
    termTip.setAttribute('aria-hidden', 'false');
    termTipFrame = requestAnimationFrame(function () {
      if (activeTerm === chip) termTip.classList.add('is-visible');
    });
  }

  function hideTermTip(chip) {
    if (chip && activeTerm !== chip) return;
    if (activeTerm) activeTerm.removeAttribute('aria-describedby');
    activeTerm = null;
    termTip.classList.remove('is-visible', 'is-measuring', 'is-above');
    termTip.setAttribute('aria-hidden', 'true');
  }

  document.addEventListener('mouseover', function (e) {
    var chip = e.target.closest('.term-chip.has-tip');
    if (chip) placeTermTip(chip);
  });
  document.addEventListener('mouseout', function (e) {
    var chip = e.target.closest('.term-chip.has-tip');
    if (chip && !chip.contains(e.relatedTarget) && document.activeElement !== chip) hideTermTip(chip);
  });
  document.addEventListener('focusin', function (e) {
    var chip = e.target.closest('.term-chip.has-tip');
    if (chip) placeTermTip(chip);
  });
  document.addEventListener('focusout', function (e) {
    var chip = e.target.closest('.term-chip.has-tip');
    if (chip) hideTermTip(chip);
  });
  document.addEventListener('click', function (e) {
    var chip = e.target.closest('.term-chip.has-tip');
    if (!chip) { hideTermTip(); return; }
    placeTermTip(chip);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') hideTermTip();
  });
  window.addEventListener('resize', function () { if (activeTerm) placeTermTip(activeTerm); });
  document.addEventListener('scroll', function () { if (activeTerm) placeTermTip(activeTerm); }, true);

  /* 各章の背景・因果・ビジネス上の意味を、自分の言葉で説明する想起練習。 */
  function initQuiz(quiz) {
    var dataNode = quiz.querySelector('.quiz-data');
    if (!dataNode) return;
    var all;
    try { all = JSON.parse(dataNode.textContent); } catch (e) { return; }
    if (!all.length) return;

    var intro = quiz.querySelector('[data-quiz-intro]');
    var run = quiz.querySelector('[data-quiz-run]');
    var result = quiz.querySelector('[data-quiz-result]');
    var question = quiz.querySelector('[data-quiz-question]');
    var reveal = quiz.querySelector('[data-quiz-reveal]');
    var feedback = quiz.querySelector('[data-quiz-feedback]');
    var rating = quiz.querySelector('[data-quiz-rating]');
    var known = quiz.querySelector('[data-quiz-known]');
    var review = quiz.querySelector('[data-quiz-review]');
    var next = quiz.querySelector('[data-quiz-next]');
    var progressText = quiz.querySelector('[data-quiz-progress-text]');
    var progressBar = quiz.querySelector('[data-quiz-progress-bar]');
    var scoreText = quiz.querySelector('[data-quiz-score]');
    var bestText = quiz.querySelector('[data-quiz-best]');
    var resultScore = quiz.querySelector('[data-quiz-result-score]');
    var resultMessage = quiz.querySelector('[data-quiz-result-message]');
    var retryMissed = quiz.querySelector('[data-quiz-retry-missed]');
    var storageKey = 'gyokai-business-quiz-best:' + (quiz.getAttribute('data-quiz-key') || location.pathname);
    var queue = [], missed = [], index = 0, score = 0, answered = false;

    function readBest() {
      try { return parseInt(localStorage.getItem(storageKey) || '0', 10) || 0; } catch (e) { return 0; }
    }
    function showBest() {
      var best = readBest();
      bestText.textContent = best ? 'この端末での最高得点 ' + best + '%' : '';
    }
    function saveBest(percent) {
      if (percent <= readBest()) return;
      try { localStorage.setItem(storageKey, String(percent)); } catch (e) {}
    }

    function showAnswer(item) {
      if (answered) return;
      feedback.replaceChildren();
      var title = document.createElement('strong');
      title.textContent = '回答の観点';
      var list = document.createElement('ul');
      item.points.forEach(function (point) {
        var row = document.createElement('li');
        row.textContent = point;
        list.appendChild(row);
      });
      feedback.appendChild(title);
      feedback.appendChild(list);
      feedback.hidden = false;
      reveal.hidden = true;
      rating.hidden = false;
      known.focus();
    }

    function rateAnswer(remembered, item) {
      if (answered) return;
      answered = true;
      if (remembered) score += 1;
      else if (!missed.some(function (entry) { return entry.question === item.question; })) missed.push(item);
      scoreText.textContent = '説明できた ' + score + '問';
      rating.hidden = true;
      next.hidden = false;
      next.focus();
    }

    function renderQuestion() {
      var item = queue[index];
      answered = false;
      feedback.hidden = true;
      feedback.replaceChildren();
      rating.hidden = true;
      reveal.hidden = false;
      next.hidden = true;
      question.textContent = item.question;
      progressText.textContent = (index + 1) + ' / ' + queue.length;
      scoreText.textContent = '説明できた ' + score + '問';
      progressBar.style.width = Math.round(index / queue.length * 100) + '%';
    }

    function finish() {
      run.hidden = true;
      result.hidden = false;
      var percent = Math.round(score / queue.length * 100);
      progressBar.style.width = '100%';
      resultScore.textContent = score + ' / ' + queue.length + '問説明できた（' + percent + '%）';
      resultMessage.textContent = percent === 100
        ? 'このページの主要論点を、自分の言葉で説明できる状態です。'
        : percent >= 80
          ? 'よく定着しています。復習対象の論点を説明し直すと仕上がります。'
          : '本文の因果関係を確認し、結論から短く説明する練習をもう一度行いましょう。';
      retryMissed.hidden = missed.length === 0;
      saveBest(percent);
      showBest();
      result.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }

    function start(source) {
      queue = source.slice();
      missed = [];
      index = 0;
      score = 0;
      intro.hidden = true;
      result.hidden = true;
      run.hidden = false;
      renderQuestion();
      question.scrollIntoView({ block: 'nearest' });
    }

    quiz.querySelector('[data-quiz-start]').addEventListener('click', function () { start(all); });
    reveal.addEventListener('click', function () { showAnswer(queue[index]); });
    known.addEventListener('click', function () { rateAnswer(true, queue[index]); });
    review.addEventListener('click', function () { rateAnswer(false, queue[index]); });
    next.addEventListener('click', function () {
      index += 1;
      if (index >= queue.length) finish(); else renderQuestion();
    });
    retryMissed.addEventListener('click', function () {
      var retry = missed.slice();
      start(retry);
    });
    quiz.querySelector('[data-quiz-retry-all]').addEventListener('click', function () { start(all); });
    showBest();
  }

  Array.prototype.forEach.call(document.querySelectorAll('.page-quiz'), initQuiz);

  var input = document.getElementById('q');
  if (!input || typeof NAV === 'undefined') return;
  var base = root.getAttribute('data-root') || '';
  var box = document.createElement('div');
  box.className = 'results hidden';
  input.parentNode.appendChild(box);
  var idx = -1, items = [];

  function close() { box.classList.add('hidden'); idx = -1; }

  function run() {
    var v = input.value.trim().toLowerCase();
    if (!v) { close(); return; }
    var hits = NAV.filter(function (e) { return (e.n + ' ' + e.c).toLowerCase().indexOf(v) >= 0; }).slice(0, 12);
    box.innerHTML = hits.length
      ? hits.map(function (e) {
          return '<a href="' + base + e.p + '">' + e.n + '<span class="cat">' + e.c + '</span></a>';
        }).join('')
      : '<div class="empty">該当なし</div>';
    items = Array.prototype.slice.call(box.querySelectorAll('a'));
    idx = -1;
    box.classList.remove('hidden');
  }

  input.addEventListener('input', run);
  input.addEventListener('focus', run);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { close(); input.blur(); return; }
    if (!items.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      items.forEach(function (a) { a.classList.remove('on'); });
      idx = (idx + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items[idx].classList.add('on');
      items[idx].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      (items[idx] || items[0]).click();
    }
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.search')) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input) { e.preventDefault(); input.focus(); }
  });

  /* 目次の現在位置ハイライト */
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  if (!links.length || !window.IntersectionObserver) return;
  var map = {};
  links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
  var seen = new Set();
  var ob = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) seen.add(en.target.id); else seen.delete(en.target.id);
    });
    links.forEach(function (a) { a.classList.remove('on'); });
    for (var i = 0; i < links.length; i++) {
      var id = links[i].getAttribute('href').slice(1);
      if (seen.has(id)) { links[i].classList.add('on'); break; }
    }
  }, { rootMargin: '-70px 0px -70% 0px' });
  Object.keys(map).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) ob.observe(el);
  });
})();
