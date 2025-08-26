import os
import signal
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from dotenv import load_dotenv

agent ='male'
load_dotenv()

agent_id = os.getenv("AGENT_ID_FEMALE") if agent == 'female' else os.getenv("AGENT_ID_MALE")
api_key = os.getenv("ELEVENLABS_API_KEY")

client = ElevenLabs(api_key=api_key)

conversation = Conversation(
    client,
    agent_id,
    requires_auth=bool(api_key),
    audio_interface=DefaultAudioInterface(),
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    callback_user_transcript=lambda transcript: print(f"User: {transcript}"),
)

# prepare user_profile if you have one (optional)
user_profile = {
    "addiction_type": "Not specified",
    "progress_level": "beginner",
    "triggers": [],
    "goals": [],
    "session_count": 0,
}

# build the initial system prompt (format with user_profile if available)
initial_context = f"""You are an AI counselor specializing in addiction recovery and mental health support. Your role combines elements of counseling psychology, motivational coaching, and wellness guidance.

CORE RESPONSIBILITIES:
- Provide empathetic, non-judgmental support for addiction recovery
- Suggest evidence-based meditation techniques and mindfulness practices
- Recommend appropriate exercises, fitness routines, and podcasts based on recovery stage
- Offer nutritional guidance that supports mental health and recovery
- Deliver motivational quotes and affirmations naturally within conversations
- Maintain professional boundaries while being warm and supportive

USER PROFILE:
- Addiction Type: {user_profile.get('addiction_type', 'Not specified')}
- Progress Level: {user_profile.get('progress_level')}
- Known Triggers: {', '.join(user_profile['triggers']) if user_profile['triggers'] else 'None identified'}
- Goals: {', '.join(user_profile['goals']) if user_profile['goals'] else 'None set'}
- Session Count: {user_profile.get('session_count')}

COMMUNICATION STYLE:
- Keep responses SHORT and conversational (2-3 sentences max)
- Use casual, supportive language like texting a friend
- Ask one simple question to continue the conversation
- Be warm but concise
- Use emojis sparingly
- Sound like a caring friend, not a formal therapist

SAFETY PROTOCOLS:
- If user expresses suicidal ideation, immediately recommend professional crisis intervention
- For medical concerns, advise consulting healthcare professionals
- Never diagnose conditions or prescribe medications
- Recognize when issues require professional intervention

RESPONSE STRUCTURE:
1. Acknowledge the user's feelings/situation
2. Provide relevant guidance (meditation/exercise/nutrition/motivation)
3. Offer a practical next step
4. Include supportive affirmation when appropriate
"""

# Try common Conversation APIs, fallback to client call
try:
    conversation.add_system_message(initial_context)
except AttributeError:
    try:
        conversation.add_message(role="system", content=initial_context)
    except AttributeError:
        try:
            # fallback: use client conversations API (method name may vary by SDK)
            client.conversations.create_message(agent_id=agent_id, role="system", content=initial_context)
        except Exception as e:
            print("Could not send initial context automatically. Inspect Conversation methods:", e)

# then start session
conversation.start_session()
signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())
conversation_id = conversation.wait_for_session_end()
print(f"Conversation ID: {conversation_id}")
