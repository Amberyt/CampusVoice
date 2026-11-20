/* CampusVoice mobile speech-output compatibility patch.
 * Load after the main inline script in python/static/index.html.
 * Keeps the existing backend response format and Hindi/English detection.
 */
(() => {
  'use strict';

  const synth = window.speechSynthesis;
  const Utterance = window.SpeechSynthesisUtterance;
  const supported = !!(synth && Utterance);
  const interim = document.getElementById('interim');
  let unlockedByGesture = false;
  let voiceCache = [];
  let runId = 0;
  let activeWatchdog = null;
  let nextChunkTimer = null;

  const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  function showSpeechMessage(message, isError = false) {
    if (!interim) return;
    interim.textContent = message;
    interim.className = isError ? 'err' : '';
  }

  function refreshVoices() {
    try { voiceCache = synth.getVoices() || []; }
    catch (_) { voiceCache = []; }
    return voiceCache;
  }

  if (supported) {
    refreshVoices();
    synth.addEventListener?.('voiceschanged', refreshVoices);
    synth.onvoiceschanged = refreshVoices;
  } else {
    showSpeechMessage('Voice output is not available in this browser. Open CampusVoice in Safari or Chrome.', true);
  }

  // iOS Safari requires speechSynthesis.speak() to be called during a real
  // user gesture. The original app called speak() only after an async fetch,
  // outside that gesture. A zero-volume utterance primes the engine on the
  // first microphone, send, mute, or suggested-question tap.
  function unlockFromUserGesture() {
    if (!supported || unlockedByGesture) return;
    try {
      const primer = new Utterance(' ');
      primer.lang = 'en-IN';
      primer.volume = 0;
      primer.rate = 1;
      primer.onend = () => { unlockedByGesture = true; };
      primer.onerror = () => { unlockedByGesture = true; };
      synth.speak(primer);
      synth.resume();
      // WebKit removes its user-gesture restriction synchronously at speak().
      unlockedByGesture = true;
    } catch (_) {
      // The real response will report an error if this browser blocks speech.
    }
  }

  document.addEventListener('click', (event) => {
    const target = event.target;
    if (target && target.closest && target.closest('#orb, #mic, #send, #mute, [data-q]')) {
      unlockFromUserGesture();
    }
  }, true);

  document.addEventListener('submit', (event) => {
    if (event.target && event.target.id === 'composer') unlockFromUserGesture();
  }, true);

  // A short polling window is needed because some mobile browsers return an
  // empty getVoices() list initially and populate it after voiceschanged.
  async function waitForVoices() {
    let voices = refreshVoices();
    for (let attempt = 0; attempt < 12 && !voices.length; attempt += 1) {
      await new Promise(resolve => setTimeout(resolve, 125));
      voices = refreshVoices();
    }
    return voices;
  }

  function chooseVoice(language, voices) {
    const prefix = language === 'hi' ? 'hi' : 'en';
    const normalized = value => String(value || '').toLowerCase().replace('_', '-');
    const candidates = voices.filter(voice => normalized(voice.lang).startsWith(prefix));
    if (!candidates.length) return null;

    if (language === 'hi') {
      return candidates.find(v => /google|natural|neerja|aditi|raveena|hindi|हिन्दी|हिंदी/i.test(v.name))
        || candidates.find(v => normalized(v.lang) === 'hi-in')
        || candidates[0];
    }
    return candidates.find(v => normalized(v.lang) === 'en-in')
      || candidates.find(v => /google|samantha|aria|jenny|zira|natural/i.test(v.name))
      || candidates[0];
  }

  function splitForMobile(text, maxLength = 150) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    if (!clean) return [];
    const sentences = clean.match(/[^.!?।]+[.!?।]*/g) || [clean];
    const result = [];
    let current = '';
    for (const sentence of sentences) {
      const piece = sentence.trim();
      if (!piece) continue;
      if (current && (current + ' ' + piece).length > maxLength) {
        result.push(current);
        current = piece;
      } else {
        current = current ? current + ' ' + piece : piece;
      }
      while (current.length > maxLength) {
        let cut = current.lastIndexOf(' ', maxLength);
        if (cut < Math.floor(maxLength * 0.55)) cut = maxLength;
        result.push(current.slice(0, cut).trim());
        current = current.slice(cut).trim();
      }
    }
    if (current) result.push(current);
    return result;
  }

  function clearSpeechTimers() {
    if (activeWatchdog) clearTimeout(activeWatchdog);
    if (nextChunkTimer) clearTimeout(nextChunkTimer);
    activeWatchdog = null;
    nextChunkTimer = null;
  }

  // Replace the original chunk-queuing implementation. Mobile Safari is more
  // reliable when only one utterance is queued at a time and the next starts
  // after onend, rather than queueing every chunk simultaneously.
  window.stopSpeaking = function stopSpeakingMobileSafe() {
    runId += 1;
    clearSpeechTimers();
    if (supported) {
      try { synth.cancel(); } catch (_) {}
    }
    try { if (typeof setPhase === 'function') setPhase('idle'); } catch (_) {}
    try { if (typeof decay === 'function') decay(); } catch (_) {}
  };

  window.speak = async function speakMobileSafe(text, spokenLang) {
    if (!supported) {
      showSpeechMessage('Voice output is not supported here. Open CampusVoice in Safari or Chrome.', true);
      return;
    }
    if (typeof voiceOn !== 'undefined' && !voiceOn) return;

    // Every answer is still spoken in the language returned by the backend.
    const language = spokenLang === 'hi' ? 'hi' : 'en';
    const utteranceLang = language === 'hi' ? 'hi-IN' : 'en-IN';
    const parts = splitForMobile(text);
    if (!parts.length) return;

    const thisRun = ++runId;
    clearSpeechTimers();
    try { synth.cancel(); } catch (_) {}
    try { synth.resume(); } catch (_) {}
    try { if (typeof setPhase === 'function') setPhase('speaking'); } catch (_) {}

    const voices = await waitForVoices();
    if (thisRun !== runId) return;
    const voice = chooseVoice(language, voices);
    let index = 0;
    let failures = 0;

    const finish = () => {
      if (thisRun !== runId) return;
      clearSpeechTimers();
      try { if (typeof setPhase === 'function') setPhase('idle'); } catch (_) {}
      try { if (typeof decay === 'function') decay(); } catch (_) {}
    };

    const playNext = () => {
      if (thisRun !== runId) return;
      if (index >= parts.length) { finish(); return; }

      const utterance = new Utterance(parts[index]);
      utterance.lang = voice?.lang || utteranceLang;
      if (voice) utterance.voice = voice;
      utterance.rate = language === 'hi' ? 0.96 : 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1;

      let settled = false;
      const advance = (failed = false) => {
        if (settled || thisRun !== runId) return;
        settled = true;
        if (activeWatchdog) clearTimeout(activeWatchdog);
        activeWatchdog = null;
        if (failed) failures += 1;
        else failures = 0;
        index += 1;
        if (failures >= 2) {
          showSpeechMessage('Could not play voice on this device. Check media volume and open CampusVoice in Safari or Chrome.', true);
          finish();
          return;
        }
        nextChunkTimer = setTimeout(playNext, isMobile ? 120 : 60);
      };

      utterance.onstart = () => {
        if (interim && interim.classList.contains('err')) {
          interim.textContent = '';
          interim.className = '';
        }
      };
      utterance.onboundary = () => {
        try { if (typeof level !== 'undefined') level = Math.min(1, level + 0.18); } catch (_) {}
      };
      utterance.onend = () => advance(false);
      utterance.onerror = (event) => {
        const error = event?.error || 'unknown';
        if (error === 'canceled' || error === 'interrupted') return;
        if (error === 'not-allowed') {
          unlockedByGesture = false;
          showSpeechMessage('Tap the microphone or send button once to enable voice playback on this phone.', true);
          finish();
          return;
        }
        advance(true);
      };

      // Fallback in case a mobile browser drops onend and leaves the speech
      // queue stuck. The timeout scales with the chunk length and rate.
      const watchdogMs = Math.max(9000, parts[index].length * 150);
      activeWatchdog = setTimeout(() => {
        if (settled || thisRun !== runId) return;
        try { synth.cancel(); } catch (_) {}
        advance(true);
      }, watchdogMs);

      try {
        synth.resume();
        synth.speak(utterance);
        // Some iOS versions remain paused after a tab/app switch.
        setTimeout(() => { if (thisRun === runId && synth.paused) synth.resume(); }, 250);
      } catch (_) {
        advance(true);
      }
    };

    // On mobile, playback is unlocked by the user's mic/send tap before the
    // asynchronous API response returns. Keep language-specific speech intact.
    if (isMobile && !unlockedByGesture) {
      showSpeechMessage('Tap the microphone or send button once to enable voice playback on this phone.', true);
      finish();
      return;
    }
    playNext();
  };

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && supported && synth.paused) {
      try { synth.resume(); } catch (_) {}
    }
  });
})();
