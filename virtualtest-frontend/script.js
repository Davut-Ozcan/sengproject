// --- Sayfa Geçiş Yönetimi ---
function navigateTo(viewId) {
    document.querySelectorAll('.view').forEach(v => {
        v.classList.remove('active-view');
        setTimeout(() => v.classList.add('hidden'), 10);
    });

    const target = document.getElementById(viewId);
    if(target) {
        target.classList.remove('hidden');
        setTimeout(() => target.classList.add('active-view'), 20);
        window.scrollTo(0,0);
    }
}

// --- Speaking Modülü (FR12 & FR13) ---
function startSpeakingTest() {
    document.getElementById('speaking-step-1').classList.add('hidden');
    document.getElementById('speaking-step-2').classList.remove('hidden');
}

// --- Writing Modülü (FR19 & FR22) ---
function startWritingTest() {
    document.getElementById('writing-step-1').classList.add('hidden');
    document.getElementById('writing-step-2').classList.remove('hidden');
}

// Kelime Sayacı 
const essayArea = document.getElementById('essay-area');
if(essayArea) {
    essayArea.addEventListener('input', function() {
        const count = this.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        document.getElementById('word-counter').innerText = `Words: ${count}`;
    });
}

// --- Listening Modülü (FR33 & FR34) ---
function playAudioDemo() {
    const playBtn = document.querySelector('.btn-play');
    const progressBar = document.getElementById('audio-progress');
    const phase1 = document.getElementById('listening-phase-1');
    const phase2 = document.getElementById('listening-phase-2');

    playBtn.disabled = true;
    playBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    playBtn.style.opacity = "0.7";

    let width = 0;
    const interval = setInterval(() => {
        if (width >= 100) {
            clearInterval(interval);
            playBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
            
            setTimeout(() => {
                phase1.style.display = 'none';
                phase2.classList.remove('hidden');
            }, 1000);
        } else {
            width++;
            progressBar.style.width = width + '%';
            document.querySelector('.time-txt').innerText = `00:${width < 10 ? '0'+width : width} / 01:30`;
        }
    }, 50);
}