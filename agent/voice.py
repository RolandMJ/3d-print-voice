"""Voice input — mic capture + faster-whisper transcription.

Usage:
    recorder = VoiceRecorder()
    recorder.start()          # begin recording from mic
    # ... user speaks ...
    text = recorder.stop()    # stop, transcribe, return text

Auto-stop: if silence_callback is set, recording stops automatically
after SILENCE_DURATION seconds of silence.
"""

import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# Audio settings — capture at 48kHz (Corsair native), resample for Whisper
SAMPLE_RATE = 48000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 2048  # samples per callback

# Silence detection
SILENCE_THRESHOLD = 0.01  # RMS below this = silence
SILENCE_DURATION = 1.5  # seconds of silence before auto-stop
MIN_RECORDING_DURATION = 0.5  # ignore recordings shorter than this

# Whisper settings — CPU to avoid VRAM competition with coding model
WHISPER_MODEL = "base.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

_whisper = None
_whisper_lock = threading.Lock()


def _get_whisper():
    """Lazy-load whisper model (first call takes a few seconds)."""
    global _whisper
    if _whisper is None:
        with _whisper_lock:
            if _whisper is None:
                try:
                    _whisper = WhisperModel(
                        WHISPER_MODEL,
                        device=WHISPER_DEVICE,
                        compute_type=WHISPER_COMPUTE,
                    )
                except Exception:
                    # CUDA not available, fall back to CPU
                    _whisper = WhisperModel(
                        WHISPER_MODEL,
                        device="cpu",
                        compute_type="int8",
                    )
    return _whisper


def _resample_to_16k(audio: np.ndarray) -> np.ndarray:
    """Resample from SAMPLE_RATE to 16kHz for Whisper."""
    if SAMPLE_RATE == 16000:
        return audio
    # Simple decimation — works well for integer ratios (48000/16000 = 3)
    ratio = SAMPLE_RATE / 16000
    indices = np.round(np.arange(0, len(audio), ratio)).astype(int)
    indices = indices[indices < len(audio)]
    return audio[indices]


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio array to text using faster-whisper."""
    model = _get_whisper()
    audio_16k = _resample_to_16k(audio)
    segments, _info = model.transcribe(
        audio_16k,
        beam_size=5,
        language="en",
        vad_filter=True,
    )
    return " ".join(seg.text.strip() for seg in segments).strip()


class VoiceRecorder:
    """Records audio from the default microphone with silence detection."""

    def __init__(self, on_auto_stop=None):
        """
        Args:
            on_auto_stop: callback(text) called when silence auto-stops recording.
                          Called from a background thread — use thread-safe UI updates.
        """
        self.on_auto_stop = on_auto_stop
        self._frames = []
        self._recording = False
        self._stream = None
        self._silence_samples = 0
        self._total_samples = 0

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        """Start recording from the default microphone."""
        if self._recording:
            return
        self._frames = []
        self._silence_samples = 0
        self._total_samples = 0
        self._recording = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> str | None:
        """Stop recording and transcribe. Returns text or None if too short."""
        if not self._recording:
            return None
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return None

        audio = np.concatenate(self._frames, axis=0).flatten()
        duration = len(audio) / SAMPLE_RATE

        if duration < MIN_RECORDING_DURATION:
            return None

        return transcribe(audio)

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio block."""
        if not self._recording:
            return

        self._frames.append(indata.copy())
        self._total_samples += frames

        # Silence detection
        rms = np.sqrt(np.mean(indata ** 2))
        if rms < SILENCE_THRESHOLD:
            self._silence_samples += frames
        else:
            self._silence_samples = 0

        # Auto-stop after sustained silence (but only if we have some speech)
        min_samples = int(MIN_RECORDING_DURATION * SAMPLE_RATE)
        silence_limit = int(SILENCE_DURATION * SAMPLE_RATE)

        if (self._total_samples > min_samples
                and self._silence_samples >= silence_limit
                and self.on_auto_stop is not None):
            # Stop in a separate thread to avoid blocking the audio callback
            self._recording = False
            threading.Thread(target=self._auto_stop_handler, daemon=True).start()

    def _auto_stop_handler(self):
        """Handle auto-stop: close stream, transcribe, call callback."""
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return

        audio = np.concatenate(self._frames, axis=0).flatten()
        duration = len(audio) / SAMPLE_RATE

        if duration < MIN_RECORDING_DURATION:
            return

        text = transcribe(audio)
        if text and self.on_auto_stop:
            self.on_auto_stop(text)
