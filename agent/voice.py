"""Voice input — mic capture via arecord + faster-whisper transcription.

Uses arecord (ALSA) for mic capture because sounddevice has compatibility
issues with PipeWire on this system. arecord captures reliably.

Usage:
    recorder = VoiceRecorder()
    recorder.start()          # begin recording from mic
    # ... user speaks ...
    text = recorder.stop()    # stop, transcribe, return text

Auto-stop: monitors audio level, stops after SILENCE_DURATION of quiet.
"""

import os
import signal
import struct
import subprocess
import tempfile
import threading
import time
import wave

import numpy as np
from faster_whisper import WhisperModel

# Recording settings
SAMPLE_RATE = 44100
CHANNELS = 1
RECORD_FORMAT = "S16_LE"  # arecord format

# Silence detection
SILENCE_THRESHOLD = 200  # int16 RMS below this = silence
SILENCE_DURATION = 1.5  # seconds of silence before auto-stop
MIN_RECORDING_DURATION = 0.5  # ignore recordings shorter than this
MAX_RECORDING_DURATION = 30  # safety cap

# Whisper settings — CPU to avoid VRAM competition with coding model
WHISPER_MODEL = "base.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

_whisper = None
_whisper_lock = threading.Lock()


def _get_whisper():
    """Lazy-load whisper model."""
    global _whisper
    if _whisper is None:
        with _whisper_lock:
            if _whisper is None:
                _whisper = WhisperModel(
                    WHISPER_MODEL,
                    device=WHISPER_DEVICE,
                    compute_type=WHISPER_COMPUTE,
                )
    return _whisper


def _wav_to_float(wav_path: str) -> np.ndarray:
    """Read a wav file and return float32 audio array."""
    with wave.open(wav_path, "r") as w:
        frames = w.readframes(w.getnframes())
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return data


def _resample_to_16k(audio: np.ndarray, source_rate: int) -> np.ndarray:
    """Resample to 16kHz for Whisper."""
    if source_rate == 16000:
        return audio
    ratio = source_rate / 16000
    indices = np.round(np.arange(0, len(audio), ratio)).astype(int)
    indices = indices[indices < len(audio)]
    return audio[indices]


def transcribe(audio: np.ndarray) -> str:
    """Transcribe float32 audio array to text using faster-whisper."""
    model = _get_whisper()
    audio_16k = _resample_to_16k(audio, SAMPLE_RATE)
    segments, _info = model.transcribe(
        audio_16k,
        beam_size=5,
        language="en",
        vad_filter=True,
    )
    return " ".join(seg.text.strip() for seg in segments).strip()


class VoiceRecorder:
    """Records audio from the mic using arecord with silence detection."""

    def __init__(self, on_auto_stop=None):
        """
        Args:
            on_auto_stop: callback(text) called when silence auto-stops recording.
                          Called from a background thread.
        """
        self.on_auto_stop = on_auto_stop
        self._recording = False
        self._process = None
        self._wav_path = None
        self._monitor_thread = None

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        """Start recording from the default microphone via arecord."""
        if self._recording:
            return

        self._wav_path = tempfile.mktemp(suffix=".wav")
        self._recording = True

        # Start arecord as subprocess
        self._process = subprocess.Popen(
            [
                "arecord",
                "-f", RECORD_FORMAT,
                "-r", str(SAMPLE_RATE),
                "-c", str(CHANNELS),
                "-d", str(MAX_RECORDING_DURATION),
                self._wav_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Start silence monitoring thread
        if self.on_auto_stop:
            self._monitor_thread = threading.Thread(
                target=self._monitor_silence, daemon=True
            )
            self._monitor_thread.start()

    def stop(self) -> str | None:
        """Stop recording and transcribe. Returns text or None."""
        if not self._recording:
            return None

        self._recording = False
        self._kill_arecord()

        if not self._wav_path or not os.path.exists(self._wav_path):
            return None

        try:
            audio = _wav_to_float(self._wav_path)
        except Exception:
            return None
        finally:
            self._cleanup_wav()

        duration = len(audio) / SAMPLE_RATE
        if duration < MIN_RECORDING_DURATION:
            return None

        # Check if there's actual audio (not just silence)
        rms_int = np.sqrt(np.mean((audio * 32768) ** 2))
        if rms_int < SILENCE_THRESHOLD:
            return None

        return transcribe(audio)

    def cancel(self):
        """Cancel recording without transcribing."""
        self._recording = False
        self._kill_arecord()
        self._cleanup_wav()

    def _kill_arecord(self):
        """Terminate the arecord process."""
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGINT)
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def _cleanup_wav(self):
        """Remove temp wav file."""
        if self._wav_path and os.path.exists(self._wav_path):
            try:
                os.unlink(self._wav_path)
            except OSError:
                pass
        self._wav_path = None

    def _monitor_silence(self):
        """Monitor recording for silence to auto-stop."""
        silence_start = None
        check_interval = 0.3  # check every 300ms
        min_time = MIN_RECORDING_DURATION

        time.sleep(min_time)  # let at least min_time pass

        while self._recording:
            time.sleep(check_interval)

            if not self._recording or not self._wav_path:
                return

            # Read the tail of the wav file to check current audio level
            try:
                if not os.path.exists(self._wav_path):
                    continue
                size = os.path.getsize(self._wav_path)
                if size < 8000:  # need at least some data
                    continue

                # Read last 0.5s of audio from the file
                tail_bytes = int(SAMPLE_RATE * 0.5 * 2)  # 16-bit = 2 bytes/sample
                with open(self._wav_path, "rb") as f:
                    f.seek(max(44, size - tail_bytes))  # skip wav header
                    raw = f.read()

                if len(raw) < 100:
                    continue

                # Parse as int16
                n_samples = len(raw) // 2
                samples = struct.unpack(f"<{n_samples}h", raw[:n_samples * 2])
                rms = (sum(s * s for s in samples) / n_samples) ** 0.5

                if rms < SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= SILENCE_DURATION:
                        # Auto-stop
                        self._recording = False
                        self._kill_arecord()
                        self._handle_auto_stop()
                        return
                else:
                    silence_start = None

            except Exception:
                continue

    def _handle_auto_stop(self):
        """Process auto-stopped recording."""
        if not self._wav_path or not os.path.exists(self._wav_path):
            return

        try:
            audio = _wav_to_float(self._wav_path)
        except Exception:
            self._cleanup_wav()
            return

        self._cleanup_wav()

        duration = len(audio) / SAMPLE_RATE
        if duration < MIN_RECORDING_DURATION:
            return

        rms_int = np.sqrt(np.mean((audio * 32768) ** 2))
        if rms_int < SILENCE_THRESHOLD:
            return

        text = transcribe(audio)
        if text and self.on_auto_stop:
            self.on_auto_stop(text)
