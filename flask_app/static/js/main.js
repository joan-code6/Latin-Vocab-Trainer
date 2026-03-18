let selectedLessons = [];
let lastShownWordId = null;
let currentWord = null;
let showingTranslation = false;
let isActive = false;

let sessionStats = { 
    total: 0, 
    correct: 0, 
    wrong: 0,
    learned: 0,
    demoted: 0,
    startTime: null 
};

function startSession() {
    const checkboxes = document.querySelectorAll('.lektion-checkbox:checked');
    selectedLessons = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (selectedLessons.length === 0) {
        return;
    }

    isActive = true;
    sessionStats = { 
        total: 0, 
        correct: 0, 
        wrong: 0,
        learned: 0,
        demoted: 0,
        startTime: Date.now() 
    };

    document.getElementById('lektionPopup').style.display = 'none';
    document.getElementById('controls').style.display = 'flex';
    document.getElementById('sessionStats').style.display = 'flex';
    document.getElementById('counter').style.display = 'block';
    
    fetchNextWord();
}

function fetchNextWord() {
    if (!isActive) return;
    
    fetch('/api/get_next_word', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            lessons: selectedLessons, 
            last_word_id: lastShownWordId 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
            return;
        }
        currentWord = data;
        lastShownWordId = data.id;
        showWord(data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function showWord(word) {
    const vokabelEl = document.getElementById('vokabel');
    const uebersetzungEl = document.getElementById('uebersetzung');
    
    vokabelEl.innerText = word.latin;
    uebersetzungEl.innerText = "";
    uebersetzungEl.classList.remove('revealed');
    showingTranslation = false;
    
    updateStats();
}

function revealTranslation() {
    if (!currentWord || showingTranslation) return;
    
    const uebersetzungEl = document.getElementById('uebersetzung');
    uebersetzungEl.innerText = currentWord.german;
    uebersetzungEl.classList.add('revealed');
    showingTranslation = true;
}

function submitResult(isCorrect) {
    if (!currentWord || !showingTranslation) {
        revealTranslation();
        return;
    }

    sessionStats.total++;
    if (isCorrect) sessionStats.correct++;
    else sessionStats.wrong++;
    
    fetch('/api/submit_result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            word_id: currentWord.id, 
            correct: isCorrect 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.lesson_progress) {
            updateProgressBar(data.lesson_progress.percent);
        }
        updateStats();
    })
    .catch((error) => {
        console.error('Error:', error);
    });

    fetchNextWord();
}

function updateStats() {
    const correctEl = document.getElementById('statCorrect');
    const wrongEl = document.getElementById('statWrong');
    const counterEl = document.getElementById('counter');
    const accuracy = sessionStats.total > 0 
        ? Math.round((sessionStats.correct / sessionStats.total) * 100) 
        : 0;
    
    if (correctEl) correctEl.textContent = sessionStats.correct;
    if (wrongEl) wrongEl.textContent = sessionStats.wrong;
    
    const status = document.getElementById('status');
    if (status) {
        status.innerText = accuracy > 0 ? `${accuracy}%` : '';
    }
    
    if (counterEl) {
        counterEl.innerText = sessionStats.total > 0 
            ? `${sessionStats.correct}/${sessionStats.total}` 
            : '';
    }
}

function updateProgressBar(percent) {
    const fill = document.getElementById('progressFill');
    if (fill) fill.style.width = percent + '%';
}

document.addEventListener('keydown', (e) => {
    if (document.getElementById('lektionPopup').style.display !== 'none') return;
    if (!isActive) return;

    if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
        e.preventDefault();
    }

    if (e.code === 'Space' || e.code === 'ArrowRight') {
        revealTranslation();
    } else if (e.code === 'ArrowUp') {
        if (showingTranslation) submitResult(true);
    } else if (e.code === 'ArrowDown') {
        if (showingTranslation) submitResult(false);
    }
});

document.addEventListener('click', (e) => {
    if (document.getElementById('lektionPopup').style.display !== 'none') return;
    if (!isActive) return;
    if (e.target.closest('.nav') || e.target.closest('.controls') || e.target.closest('button')) return;
    
    if (!showingTranslation) {
        revealTranslation();
    }
});
