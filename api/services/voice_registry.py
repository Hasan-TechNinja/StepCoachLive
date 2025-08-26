# StepCoachLive/api/services/voice_registry.py
from typing import Dict, Optional
from .voice_runtime import VoiceCounselorRuntime

class VoiceSessionRegistry:
    def __init__(self):
        self._by_user: Dict[str, VoiceCounselorRuntime] = {}

    def get(self, user_key: str) -> Optional[VoiceCounselorRuntime]:
        return self._by_user.get(user_key)

    def start(self, user_key: str, **kwargs) -> VoiceCounselorRuntime:
        existing = self._by_user.get(user_key)
        if existing and existing.is_running():
            return existing
        runtime = VoiceCounselorRuntime(**kwargs)
        self._by_user[user_key] = runtime
        runtime.start()
        return runtime

    def end(self, user_key: str) -> Optional[str]:
        rt = self._by_user.pop(user_key, None)
        if not rt:
            return None
        return rt.end()

voice_registry = VoiceSessionRegistry()
