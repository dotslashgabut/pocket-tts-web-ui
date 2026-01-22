const API_BASE = window.location.origin + "/api";

document.addEventListener('DOMContentLoaded', async () => {
    const statusBadge = document.getElementById('status-badge');
    const generateBtn = document.getElementById('generate-btn');
    const voiceGrid = document.getElementById('voice-grid');
    const audioPlayer = document.getElementById('audio-player');
    const downloadBtn = document.getElementById('download-btn');
    const resultSection = document.getElementById('result-section');
    const textInput = document.getElementById('text-input');
    const voiceInput = document.getElementById('voice-file');
    const fileLabel = document.getElementById('file-label');
    const dropZone = document.getElementById('drop-zone');
    const speedInput = document.getElementById('speed-input');
    const speedValue = document.getElementById('speed-value');
    const voiceUrlInput = document.getElementById('voice-url');
    const seedInput = document.getElementById('seed-input');
    const randomSeedBtn = document.getElementById('random-seed-btn');
    const tempInput = document.getElementById('temp-input');
    const tempValue = document.getElementById('temp-value');
    const lsdInput = document.getElementById('lsd-input');
    const lsdValue = document.getElementById('lsd-value');

    let selectedVoice = 'alba'; // Default
    let selectedFile = null;

    // Check Status
    async function checkStatus() {
        try {
            const res = await fetch(`${API_BASE}/status`);
            const data = await res.json();
            if (data.status === 'ready') {
                statusBadge.textContent = "Model Ready";
                statusBadge.className = "badge ready";
                generateBtn.disabled = false;

                // Check Voice Cloning Support
                if (!data.has_voice_cloning) {
                    voiceInput.disabled = true;
                    voiceUrlInput.style.display = 'none';
                    dropZone.style.opacity = "0.5";
                    dropZone.style.cursor = "not-allowed";
                    dropZone.title = "Voice cloning model not found. Using standard model.";
                    fileLabel.textContent = "Voice Cloning Unavailable";
                    // If a file was selected, clear it
                    if (selectedFile) {
                        selectVoice(selectedVoice || 'alba', document.querySelector('.voice-card.selected') || document.querySelector('.voice-card'));
                    }
                } else {
                    voiceInput.disabled = false;
                    voiceUrlInput.style.display = 'block';
                    dropZone.style.opacity = "1";
                    dropZone.style.cursor = "pointer";
                    if (!selectedFile) fileLabel.textContent = "Drop audio file or click to upload";
                }

                loadVoices();
            } else {
                statusBadge.textContent = "Loading Model...";
                statusBadge.className = "badge loading";
                generateBtn.disabled = true;
                setTimeout(checkStatus, 2000);
            }
        } catch (e) {
            statusBadge.textContent = "Connection Error";
            statusBadge.className = "badge error";
            setTimeout(checkStatus, 5000);
        }
    }

    // Load Voices
    async function loadVoices() {
        try {
            const res = await fetch(`${API_BASE}/voices`);
            const data = await res.json();
            voiceGrid.innerHTML = '';

            data.voices.forEach(voice => {
                const card = document.createElement('div');
                card.className = 'voice-card';
                if (voice === selectedVoice) card.classList.add('selected');
                card.textContent = voice.charAt(0).toUpperCase() + voice.slice(1);
                card.onclick = () => selectVoice(voice, card);
                voiceGrid.appendChild(card);
            });
        } catch (e) {
            console.error(e);
        }
    }

    function selectVoice(voice, card) {
        selectedVoice = voice;
        selectedFile = null;
        fileLabel.textContent = "Drop audio file or click to upload";
        voiceInput.value = ""; // Clear file input
        voiceUrlInput.value = ""; // Clear URL input

        document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        // Remove style from file upload zone
        dropZone.style.borderColor = "var(--border)";
    }

    // File Upload handling
    voiceInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    function handleFile(file) {
        selectedFile = file;
        selectedVoice = null;
        voiceUrlInput.value = ""; // Clear URL input
        fileLabel.textContent = file.name;
        document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
        dropZone.style.borderColor = "var(--primary)";
    }

    // URL Input handling
    voiceUrlInput.addEventListener('input', (e) => {
        if (voiceUrlInput.value.trim().length > 0) {
            selectedVoice = null;
            selectedFile = null;
            voiceInput.value = "";
            fileLabel.textContent = "Drop audio file or click to upload";
            document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
            dropZone.style.borderColor = "var(--border)";
        }
    });

    // Speed Control
    function updateSpeed() {
        const speed = parseFloat(speedInput.value);
        speedValue.textContent = speed.toFixed(1) + 'x';
        audioPlayer.playbackRate = speed;
    }

    speedInput.addEventListener('input', updateSpeed);

    // Advanced Options Control
    tempInput.addEventListener('input', () => {
        tempValue.textContent = parseFloat(tempInput.value).toFixed(2);
    });

    lsdInput.addEventListener('input', () => {
        lsdValue.textContent = lsdInput.value;
    });

    // Random Seed Button
    randomSeedBtn.addEventListener('click', () => {
        // Generate random 32-bit integer (approx)
        const randomSeed = Math.floor(Math.random() * 4294967295);
        seedInput.value = randomSeed;
    });

    // Generate
    generateBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) return;

        generateBtn.classList.add('loading');
        generateBtn.disabled = true;

        resultSection.classList.remove('show');
        audioPlayer.pause();
        audioPlayer.src = "";
        downloadBtn.style.display = 'none';

        const formData = new FormData();
        formData.append('text', text);

        if (selectedFile) {
            formData.append('file', selectedFile);
        } else if (voiceUrlInput.value.trim()) {
            formData.append('url', voiceUrlInput.value.trim());
        } else if (selectedVoice) {
            formData.append('voice', selectedVoice);
        }

        if (seedInput.value) {
            formData.append('seed', seedInput.value);
        }
        formData.append('temperature', tempInput.value);
        formData.append('lsd_steps', lsdInput.value);

        try {
            const res = await fetch(`${API_BASE}/generate`, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error(await res.text());

            // It's a streaming response, but we can consume it as a blob for <audio> src
            // Ideally we'd feed into MediaSource API for true streaming, 
            // but for simplicity fetch blob is fine for < 1 min audio.
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            audioPlayer.src = url;

            // Setup download button
            downloadBtn.href = url;
            downloadBtn.download = `pocket-tts-${Date.now()}.wav`;
            downloadBtn.style.display = 'inline-block';

            resultSection.classList.add('show');
            audioPlayer.playbackRate = parseFloat(speedInput.value); // Apply current speed
            audioPlayer.play();

        } catch (e) {
            alert("Error generating speech: " + e.message);
        } finally {
            generateBtn.classList.remove('loading');
            generateBtn.disabled = false;
        }
    });

    checkStatus();
});
