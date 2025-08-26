# StepCoachLive/api/services/voice_runtime.py
import os, threading, signal
from typing import Optional, Callable, Dict, Any

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

load_dotenv()

class VoiceCounselorRuntime:
    """
    Wrapper around ElevenLabs Conversation for server-side live voice sessions.
    """
    def __init__(
        self,
        agent: str = "male",
        on_user_transcript: Optional[Callable[[str], None]] = None,
        on_agent_response: Optional[Callable[[str], None]] = None,
        on_agent_correction: Optional[Callable[[str, str], None]] = None,
        initial_context: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
    ):
        self.agent = agent
        self.on_user_transcript = on_user_transcript or (lambda t: None)
        self.on_agent_response = on_agent_response or (lambda r: None)
        self.on_agent_correction = on_agent_correction or (lambda o, c: None)

        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("AGENT_ID_FEMALE") if agent == "female" else os.getenv("AGENT_ID_MALE")
        if not self.api_key or not self.agent_id:
            raise RuntimeError("Missing ELEVENLABS_API_KEY or AGENT_ID_* in environment.")

        self.client = ElevenLabs(api_key=self.api_key)

        self.user_profile = user_profile or {
            "addiction_type": "Not specified",
            "progress_level": "beginner",
            "triggers": [],
            "goals": [],
            "session_count": 0,
        }

        self.initial_context = initial_context or (
            "You are an AI counselor specializing in addiction recovery and mental health support. "
            "Be empathetic, concise, and non-judgmental. Use motivational interviewing techniques."
        )

        self.conversation = Conversation(
            self.client,
            self.agent_id,
            requires_auth=bool(self.api_key),
            audio_interface=DefaultAudioInterface(),
            callback_agent_response=self._handle_agent_response,
            callback_agent_response_correction=self._handle_agent_correction,
            callback_user_transcript=self._handle_user_transcript,
        )

        self._thread: Optional[threading.Thread] = None
        self._session_done = threading.Event()
        self._conversation_id: Optional[str] = None

    # callbacks
    def _handle_user_transcript(self, transcript: str):
        self.on_user_transcript(transcript)

    def _handle_agent_response(self, response: str):
        self.on_agent_response(response)

    def _handle_agent_correction(self, original: str, corrected: str):
        self.on_agent_correction(original, corrected)

    # control
    def start(self):
        # Add system prompt once
        try:
            self.conversation.add_system_message(self.initial_context)
        except Exception:
            pass

        def _run():
            # ❌ DO NOT set signal handlers here (we're in a worker thread)
            try:
                # Start the session (captures audio or does nothing if audio_interface=None)
                self.conversation.start_session()
                # Block until the SDK signals end of session
                self._conversation_id = self.conversation.wait_for_session_end()
            except Exception as e:
                # (Optional) log this somewhere
                # print(f"Voice session thread error: {e}")
                pass
            finally:
                self._session_done.set()

        # Avoid double-start
        if self._thread and self._thread.is_alive():
            return

        self._session_done.clear()
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._session_done.is_set()

    def end(self) -> Optional[str]:
        try:
            # Ask SDK to end; it should unblock wait_for_session_end()
            self.conversation.end_session()
        except Exception:
            pass
        finally:
            self._session_done.set()
            if self._thread:
                self._thread.join(timeout=2)
        return self._conversation_id
