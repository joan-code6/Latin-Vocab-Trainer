let selectedLessons = [];
let lastShownWordId = null;
let currentWord = null;
let showingTranslation = false;
let isActive = false;

const fullscreenBtn = document.getElementById('mobileFullscreenBtn');

let sessionStats = { 
    total: 0, 
    correct: 0, 
    wrong: 0,
    learned: 0,
    demoted: 0,
    startTime: null 
};

function isFullscreenSupported() {
    return !!(
        document.fullscreenEnabled ||
        document.webkitFullscreenEnabled ||
        document.msFullscreenEnabled
    );
}

function getFullscreenElement() {
    return (
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.msFullscreenElement ||
        null
    );
}

function updateFullscreenButtonLabel() {
    if (!fullscreenBtn) return;
    fullscreenBtn.textContent = getFullscreenElement() ? 'Normal' : 'Vollbild';
}

function syncFullscreenModeClass() {
    document.body.classList.toggle('fullscreen-mode', !!getFullscreenElement());
}

function enterFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) return el.requestFullscreen();
    if (el.webkitRequestFullscreen) return el.webkitRequestFullscreen();
    if (el.msRequestFullscreen) return el.msRequestFullscreen();
    return Promise.resolve();
}

function exitFullscreen() {
    if (document.exitFullscreen) return document.exitFullscreen();
    if (document.webkitExitFullscreen) return document.webkitExitFullscreen();
    if (document.msExitFullscreen) return document.msExitFullscreen();
    return Promise.resolve();
}

function toggleFullscreen() {
    if (getFullscreenElement()) {
        exitFullscreen().catch(() => {});
    } else {
        enterFullscreen().catch(() => {});
    }
}

if (fullscreenBtn) {
    if (!isFullscreenSupported()) {
        fullscreenBtn.classList.add('hidden');
    } else {
        fullscreenBtn.addEventListener('click', () => {
            toggleFullscreen();
        });

        updateFullscreenButtonLabel();
        syncFullscreenModeClass();

        const handleFullscreenChange = () => {
            updateFullscreenButtonLabel();
            syncFullscreenModeClass();
        };

        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    }
}

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

    refreshOverallProgress();
    
    fetchNextWord();
}

function refreshOverallProgress() {
    if (!selectedLessons || selectedLessons.length === 0) {
        updateProgressBar(0);
        return;
    }

    fetch('/api/get_progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lessons: selectedLessons }),
    })
    .then(response => response.json())
    .then(data => {
        const progress = typeof data.progress === 'number' ? data.progress : 0;
        updateProgressBar(Math.round(progress * 100));
    })
    .catch((error) => {
        console.error('Error:', error);
    });
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
        refreshOverallProgress();
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
