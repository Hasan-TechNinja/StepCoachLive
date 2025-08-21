import json
import random
import pytesseract
from PIL import Image
import PyPDF2
import io
import openai
from dotenv import load_dotenv
import os
import sys
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables from .env file
load_dotenv()

class AICounselor:
    def __init__(self):
        """
        Initializes the AI counselor with the API key from the .env file and prepares the environment.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] =  api_key
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables.")

        # Set up LangChain LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.7,
        )

        # Set up memory for conversation
        self.memory = ConversationBufferWindowMemory(
            k=10,  # remembers last 10 exchanges
            return_messages=True,
            memory_key="chat_history"
        )

        # Prompt template for the conversation
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=(
                "You are a supportive friend helping with addiction recovery.\n\n"
                "Recent conversation:\n{chat_history}\n\n"
                "Current message: {input}\n\n"
                "Respond in 2-3 short sentences like you're texting a close friend. "
                "Be supportive but keep it brief. Ask one simple follow-up question."
            )
        )

        # Set up the conversation chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt, memory=self.memory)

        self.conversation_history = []
        self.user_profile = {
            "addiction_type": None,
            "progress_level": "beginner",
            "triggers": [],
            "goals": [],
            "session_count": 0
        }

        # Motivational quotes database
        self.motivational_quotes = [
            "Recovery is not a race. You don't have to feel guilty if it takes you longer than you thought it would.",
            "The greatest revolution of our generation is the discovery that human beings, by changing the inner attitudes of their minds, can change the outer aspects of their lives.",
            "You are stronger than your addiction and your addiction is not stronger than your God.",
            "Don't quit too easily. Your life is precious.",
            "Recovery is about progression, not perfection.",
            "If you are tired take rest and start again. Believe that you can do it.",
            "One day at a time, one moment at a time, one breath at a time.",
            "Life doesn't always go with the flow. Life is like a wave sometimes you need to stay calm sometimes you need to rise.",
            "The only person you are destined to become is the person you decide to be.",
            "Don't let the past take over your today.",
            "Healing takes time, and asking for help is a courageous step.",
            "Progress, not perfection, is what we should strive for."
        ]

    def create_system_prompt(self) -> str:
        return f"""
        You are an AI counselor specializing in addiction recovery and mental health support. Your role combines elements of counseling psychology, motivational coaching, and wellness guidance.

        CORE RESPONSIBILITIES:
        - Provide empathetic, non-judgmental support for addiction recovery
        - Suggest evidence-based meditation techniques and mindfulness practices
        - Recommend appropriate exercises, fitness routines, and podcasts based on recovery stage
        - Offer nutritional guidance that supports mental health and recovery
        - Deliver motivational quotes and affirmations naturally within conversations
        - Maintain professional boundaries while being warm and supportive

        USER PROFILE:
        - Addiction Type: {self.user_profile.get('addiction_type', 'Not specified')}
        - Progress Level: {self.user_profile['progress_level']}
        - Known Triggers: {', '.join(self.user_profile['triggers']) if self.user_profile['triggers'] else 'None identified'}
        - Goals: {', '.join(self.user_profile['goals']) if self.user_profile['goals'] else 'None set'}
        - Session Count: {self.user_profile['session_count']}

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

    def extract_text_from_image(self, image_data: bytes) -> str:
        """
        Extracts text from an image using OCR (Optical Character Recognition).
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            return f"Error processing image: {str(e)}"

    def extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """
        Extracts text from a PDF file.
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    def analyze_user_message(self, message: str) -> dict:
        """
        Analyzes the user's message to determine emotional state, triggers, and support needed.
        """
        # Simple keyword-based analysis to avoid API parsing issues
        message_lower = message.lower()
        
        # Detect emotional state
        emotional_state = "neutral"
        if any(word in message_lower for word in ["anxious", "anxiety", "nervous", "worried", "panic"]):
            emotional_state = "anxious"
        elif any(word in message_lower for word in ["sad", "depressed", "down", "hopeless", "worthless"]):
            emotional_state = "depressed"
        elif any(word in message_lower for word in ["angry", "mad", "frustrated", "pissed", "furious"]):
            emotional_state = "angry"
        elif any(word in message_lower for word in ["craving", "want to", "need to", "urge", "tempted"]):
            emotional_state = "craving"
        elif any(word in message_lower for word in ["drunk", "high", "using", "relapsed", "drank"]):
            emotional_state = "using"
        
        # Detect support needed
        support_needed = ["general_support"]
        if emotional_state == "anxious":
            support_needed.append("meditation")
        elif emotional_state == "depressed":
            support_needed.extend(["exercise", "motivation"])
        elif emotional_state == "craving":
            support_needed.extend(["meditation", "motivation"])
        elif emotional_state == "using":
            support_needed.extend(["crisis", "motivation"])
        
        # Detect urgency
        urgency = "medium"
        if any(word in message_lower for word in ["suicide", "kill myself", "end it", "can't go on"]):
            urgency = "crisis"
        elif any(word in message_lower for word in ["drunk", "high", "relapsed", "used"]):
            urgency = "high"
        elif any(word in message_lower for word in ["craving", "urge", "tempted"]):
            urgency = "high"
        
        return {
            "emotional_state": emotional_state,
            "triggers": [],
            "support_needed": support_needed,
            "urgency": urgency,
            "key_concerns": []
        }

    def generate_meditation_suggestion(self, emotional_state: str) -> str:
        """
        Suggests a meditation based on the user's emotional state.
        """
        meditation_prompts = {
            "anxious": "Try a 5-minute breathing meditation: Inhale for 4 counts, hold for 4, exhale for 6. This activates your parasympathetic nervous system and reduces anxiety.",
            "depressed": "Consider a loving-kindness meditation: Start by sending love to yourself, then extend it to others. This can help counter negative self-talk and isolation.",
            "angry": "Practice a body scan meditation: Notice where you feel tension, breathe into those areas, and consciously relax each muscle group.",
            "craving": "Use the RAIN technique: Recognize the craving, Allow it to be present, Investigate with kindness, and Natural awareness - don't identify with it.",
            "default": "Try a simple mindfulness meditation: Focus on your breath for 10 minutes, noticing when your mind wanders and gently returning to the breath."
        }

        return meditation_prompts.get(emotional_state.lower(), meditation_prompts["default"])

    def generate_exercise_suggestion(self, progress_level: str, emotional_state: str) -> str:
        """
        Suggests an exercise routine based on the user's progress level and emotional state.
        """
        if emotional_state.lower() in ["anxious", "stressed"]:
            return "Try gentle yoga or a 15-minute walk in nature. Physical movement helps metabolize stress hormones like cortisol."
        elif emotional_state.lower() in ["depressed", "low"]:
            return "Light cardio can boost endorphins. Start with 10 minutes of dancing to your favorite music or climbing stairs."
        elif progress_level == "beginner":
            return "Begin with 10-15 minutes of daily movement: stretching, walking, or bodyweight exercises like wall push-ups."
        else:
            return "Try a 20-30 minute workout combining cardio and strength training. Exercise is proven to reduce cravings and improve mood."

    def generate_nutrition_advice(self, addiction_type: str = None) -> str:
        """
        Suggests nutritional advice based on addiction type.
        """
        general_advice = "Focus on stable blood sugar with protein + complex carbs + healthy fats at each meal. Stay hydrated and consider a B-complex vitamin."

        specific_advice = {
            "alcohol": "Alcohol depletes B vitamins and magnesium. Include leafy greens, nuts, and consider milk thistle for liver support.",
            "drugs": "Prioritize brain-healing nutrients: omega-3s (fish, walnuts), antioxidants (berries), and amino acids (lean proteins).",
            "smoking": "Vitamin C is depleted by smoking. Include citrus fruits, bell peppers, and consider NAC supplement for lung support."
        }

        if addiction_type and addiction_type.lower() in specific_advice:
            return f"{general_advice} {specific_advice[addiction_type.lower()]}"
        return general_advice

    def get_motivational_quote(self) -> str:
        """
        Returns a random motivational quote.
        """
        return random.choice(self.motivational_quotes)

    def update_user_profile(self, analysis: dict):
        """
        Updates the user's profile with analysis results.
        """
        for trigger in analysis.get("triggers", []):
            if trigger not in self.user_profile["triggers"]:
                self.user_profile["triggers"].append(trigger)

        self.user_profile["session_count"] += 1

    def process_message(self, message: str, image_data: bytes = None, pdf_data: bytes = None) -> str:
        extracted_text = ""
        if image_data:
            extracted_text += "Image content: " + self.extract_text_from_image(image_data) + "\n"
        if pdf_data:
            extracted_text += "PDF content: " + self.extract_text_from_pdf(pdf_data) + "\n"

        full_message = message
        if extracted_text.strip():
            full_message += f"\n\nAdditional context from attachments:\n{extracted_text}"

        # Analyze the message
        analysis = self.analyze_user_message(full_message)
        self.update_user_profile(analysis)

        try:
            response = self.chain.invoke({"input": full_message})
            # If response is a dict (as with PromptTemplate), use response["text"]
            if isinstance(response, dict) and "text" in response:
                return response["text"].strip()
            return response.strip()
        except Exception as e:
            return f"I'm here for you, but having some tech issues. Can you tell me more about how you're feeling? 💙"


    def save_conversation_history(self, filename: str):
        """
        Saves conversation history to a file.
        """
        data = {
            "conversation_history": self.conversation_history,
            "user_profile": self.user_profile,
            "timestamp": datetime.now().isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_conversation_history(self, filename: str):
        """
        Loads conversation history from a file.
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.conversation_history = data.get("conversation_history", [])
                self.user_profile = data.get("user_profile", self.user_profile)
                print(f"✅ Loaded previous session from {data.get('timestamp', 'unknown time')}")
        except FileNotFoundError:
            print("Starting a fresh conversation session.")

    def display_welcome(self):
        """
        Displays welcome message and instructions.
        """
        print("\n" + "="*60)
        print("🌟 WELCOME TO YOUR AI COUNSELOR 🌟")
        print("="*60)
        print("I'm here to support you on your recovery journey.")
        print("I can help with:")
        print("  • Meditation and mindfulness techniques")
        print("  • Exercise and fitness guidance")
        print("  • Nutritional advice")
        print("  • Emotional support and motivation")
        print("  • Coping strategies for triggers")
        print("\nCommands:")
        print("  • Type 'quit', 'exit', or 'bye' to end the session")
        print("  • Type 'save' to save your conversation")
        print("  • Type 'profile' to view your current profile")
        print("  • Type 'clear' to clear the screen")
        print("="*60)

    def display_profile(self):
        """
        Displays the current user profile.
        """
        print("\n" + "="*40)
        print("📋 YOUR PROFILE")
        print("="*40)
        print(f"Addiction Type: {self.user_profile.get('addiction_type', 'Not specified')}")
        print(f"Progress Level: {self.user_profile['progress_level']}")
        print(f"Session Count: {self.user_profile['session_count']}")
        print(f"Known Triggers: {', '.join(self.user_profile['triggers']) if self.user_profile['triggers'] else 'None identified'}")
        print(f"Goals: {', '.join(self.user_profile['goals']) if self.user_profile['goals'] else 'None set'}")
        print("="*40 + "\n")

    def clear_screen(self):
        """
        Clears the terminal screen.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def start_chat(self):
        """
        Starts the interactive chat session in the terminal.
        """
        # Load previous session if exists
        session_file = "counselor_session.json"
        self.load_conversation_history(session_file)
        
        self.display_welcome()
        
        print("\n💬 How are you feeling today? What's on your mind?")
        print("-" * 60)
        
        while True:
            try:
                # Get user input
                user_input = input("\n🗣️  You: ").strip()
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n🤗 Take care of yourself. Remember, I'm here whenever you need support.")
                    print("Your progress matters, and you're doing great by reaching out.")
                    self.save_conversation_history(session_file)
                    break
                
                elif user_input.lower() == 'save':
                    self.save_conversation_history(session_file)
                    print("💾 Conversation saved successfully!")
                    continue
                
                elif user_input.lower() == 'profile':
                    self.display_profile()
                    continue
                
                elif user_input.lower() == 'clear':
                    self.clear_screen()
                    self.display_welcome()
                    continue
                
                elif not user_input:
                    print("❓ I'm here to listen. Please share what's on your mind.")
                    continue
                
                # Process the message and get response
                print("\n🤔 Let me think about that...")
                response = self.process_message(user_input)
                
                # Display the response
                print(f"\n🧠 Counselor: {response}")
                print("-" * 60)
                
                # Auto-save periodically
                if self.user_profile['session_count'] % 5 == 0:
                    self.save_conversation_history(session_file)
                    print("💾 (Auto-saved)")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Your progress is saved.")
                self.save_conversation_history(session_file)
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again, or type 'quit' to exit.")

# Main execution
if __name__ == "__main__":
    try:
        counselor = AICounselor()
        counselor.start_chat()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please make sure you have a .env file with your GOOGLE_API_KEY.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        print("Please check your setup and try again.")