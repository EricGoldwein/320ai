import os
import logging
from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, session, redirect, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
from datetime import datetime
import sqlite3
import json
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv
import time
import httpx
from functools import wraps
from flask import Response

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize environment variables first
logger.info("Loading environment variables...")
load_dotenv()

# Add this near the top of the file with other constants
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscribers.db')

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers
        (email TEXT PRIMARY KEY,
         signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Initialize the database
init_db()

# Set proxy configuration for PythonAnywhere
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    logger.info("Running on PythonAnywhere - setting proxy configuration")
else:
    logger.info("Running locally - no proxy configuration needed")

# Get environment variables with defaults
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
logger.info(f"API Key present: {bool(OPENAI_API_KEY)}")
if not OPENAI_API_KEY:
    logger.error("No OpenAI API key found in environment variables!")

ASSISTANT_ID = os.environ.get('ASSISTANT_ID', 'asst_6xnlbT9tnP62VLss0ondKtIw')
logger.info(f"Using Assistant ID: {ASSISTANT_ID}")

MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '5'))
TIMEOUT = int(os.environ.get('TIMEOUT', '120'))

# Initialize OpenAI client as a global variable
client = None

def init_openai_client():
    """Initialize the OpenAI client with optional proxy support for PythonAnywhere"""
    global client

    try:
        logger.info("Initializing OpenAI client...")
        if 'PYTHONANYWHERE_DOMAIN' in os.environ:
            logger.info("Detected PythonAnywhere — setting up client...")
            # Use a simpler configuration without proxy
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=30.0, read=60.0, write=30.0, pool=60.0),
                verify=True  # Enable SSL verification
            )
        else:
            logger.info("Local environment — no proxy needed.")
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=30.0, read=60.0, write=30.0, pool=60.0)
            )

        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client,
            max_retries=5,  # Increase max retries
            timeout=60.0  # Set timeout at client level
        )
        logger.info("✅ OpenAI client initialized")
        return client

    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
        return None

# Initialize the client
logger.info("About to initialize OpenAI client...")
client = init_openai_client()
if client is None:
    logger.error("Failed to initialize OpenAI client after all attempts")

# Add error handler for OpenAI API errors
def handle_openai_error(error):
    logger.error(f"OpenAI API error: {str(error)}")
    if "rate limit" in str(error).lower():
        return "I'm a bit overwhelmed right now. Please try again in a minute."
    elif "timeout" in str(error).lower():
        return "The response took too long. Please try again."
    else:
        return f"I encountered an error: {str(error)}"

# Get the template directory
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, 
    static_folder='static', 
    static_url_path='/static',
    template_folder=template_dir
)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Global error handlers
@app.errorhandler(400)
def bad_request_error(error):
    logger.error(f"Bad Request: {error}")
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not Found: {error}")
    return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {str(e)}")
    return jsonify({'error': 'Server Error', 'message': 'An unexpected error occurred'}), 500

# Request validation middleware
@app.before_request
def validate_incoming_request():
    # Validate content length
    if request.content_length and request.content_length > 16 * 1024 * 1024:  # 16MB limit
        return jsonify({'error': 'Request too large'}), 413
        
    # Validate content type for API endpoints
    if request.path.startswith('/api/') and request.method == 'POST':
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415
            
    # Rate limiting check (in addition to existing limiter)
    if getattr(request, 'limit_exempt', False):
        return
        
    # Add request logging
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

# Initialize rate limiter with simpler configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://"  # Use in-memory storage for Windows compatibility
)

# Make sure chat memory is using file system
conversation_history = {}  # Clear this if it exists

# Add file-based storage for chat history
CHAT_HISTORY_DIR = "/tmp/chat_histories"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

def save_chat_history(user_id, history):
    filename = f"{CHAT_HISTORY_DIR}/{user_id}.json"
    with open(filename, 'w') as f:
        json.dump(history, f)

def load_chat_history(user_id):
    filename = f"{CHAT_HISTORY_DIR}/{user_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

class WorkoutOptimizer:
    """Advanced Track Workout Generation System™"""

    NEURAL_RESPONSES = {
        "predefined_workouts": [
            {
                "intensity": "AGILITY",
                "workout": "Mind the Divot:\nWarm-up: 1-2 easy Wingos\nMain Set: 6 Wingos at tempo pace\nAt the divot: 10 two-legged hops",
                "science": "Embrace your natural variation."
            },
            {
                "intensity": "CLASSIC",
                "workout": "ERock's 160:\n2 sets: 5 Half-Wingo repeats\nTwo workouts in between\nSelect 2 from: pushups, planks, wall sit, lunges, bicycle crunches, burpees, situps...\nFive minute rest, then repeat",
                "science": "Hyper-individualized efficiency is where it's at."
            },
            {
                "intensity": "STRENGTH",
                "workout": "The G.W. Wingate Challenge:\nHang on field goal post\nTotal time: 320 seconds\nAdd 10 seconds for every 30 seconds of rest",
                "science": "A perfect balance of strength and strength."
            },
            {
                "intensity": "CLASSIC",
                "workout": "The Yellowstone:\n32 Wingos\nThat's it. That's the workout.\nKeep the pace consistently inconsistent",
                "science": "This sequence was discovered during Mr. Wingate's 1885 Yellowstone Expedition."
            },
            {
                "intensity": "STRENGTH",
                "workout": "Stairmaster:\nSet 1: 3:20 up/down stairs\nWingo loop\nSet 2: 3:20 up/down stairs\nWingo loop\nSet 3: 3:20 up/down stairs",
                "science": "Building power and endurance through vertical movement."
            },
            {
                "intensity": "PRECISION",
                "workout": "The Naked Wrist Challenge\nTempo for exactly 320 seconds\nMust finish within 5s of 320s\nOutside range? Start over!",
                "science": "Developing internal clock and harmonic efficiency."
            },
            {
                "intensity": "GLORY DAYS",
                "workout": "The Comeback:\nStart with old PR pace\nGradually increase speed\nEnd with a new PR attempt",
                "science": "Reconnecting with past performance levels."
            },
            {
                "intensity": "PRECISION",
                "workout": "The Garmin-free Gallop:\nTake off watch\nRun 1 m*le at mareathon pace\nIf off by 6+ seconds, repeat",
                "science": "Timing is everything."
            },
            {
                "intensity": "ROCKY",
                "workout": "The Pain Train:\n10 Wingos at max effort\nRest: walk backwards\nRepeat until you can't walk forwards",
                "science": "Make it Hurts."
            },
            {
                "intensity": "HUSTLE",
                "workout": "The Filly Special:\n10 Wingos at half mare-athon pace...then stop!\nEnjoy the city's energy\nRun the Wingate stairs",
                "science": "Trust the DAISY™ process."
            },
            {
                "intensity": "PARTNER",
                "workout": "Three-Legged Daisy:\nGrap a partner for 3 x three-legged Wingos\nFirst Wingo: Moderate pace\nSecond Wingo: Modereter pace, focus on efficiency\nThird Wingo, sprint on your own\nSwitch inside/outside leg positions each round\nFinish with victory Wingo (regular two legs)",
                "science": "Three legs are better than two."
            },
            {
                "intensity": "BUFFALO",
                "workout": "The TRIMBLE:\n10 x Wingos total\nFirst 160m: Very Fast\nSecond 160m: Very Slow",
                "science": "Maximize the contrast between fast and slow"
            },
            {
                "intensity": "PAIN",
                "workout": "Goran Dragic:\n320 seconds of plank\nVictory Wingo trot",
                "science": "Take care of your core and your core will take care of you."
            },
            {
                "intensity": "GENIE",
                "workout": "Shuffle Roulette:\n5 x km repeats: \nEach km paced to random Christina\nGenie in a bottle? 3:36 KM. Come On Over? 3:09 KM\nOne minute rest between songs",
                "science": "Tip: 1 KM equals 3.125 Wingos"
            },
            {
                "intensity": "REVERSE",
                "workout": "Look Back in Anger:\nMaster the art of backwards running:\n8 x 80m backwards buildup\n4 x Furlongs alternating (front-back)\n3 x Wingos (front-back-front)",
                "science": "Sally can no longer wait"
            },
            {
                "intensity": "MYSTERIOUS",
                "workout": "Double Lost Ladder:\nSprints: 40m-80m-150m-160m-230m-420m\n60s rest between each sprint\nBack down the ladder\nDo it again",
                "science": "We have to go back"
            },
            {
                "intensity": "PRECISION",
                "workout": "The Naked Wrist Challenge:\nTake off the Garmin:\nTempo for exactly 320 seconds\nMust finish within 5s of 320s\nOutside range? Start over!",
                "science": "Because the only device you need is DAISY™."
            },
            {
                "intensity": "STRENGTH",
                "workout": "The G.W. Wingate Challenge:\nHang on field goal post\nTotal time: 320 seconds\nAdd 10s for every 30s of rest",
                "science": "Can you hang?"
            },
            {
                "intensity": "ENDURANCE",
                "workout": "The Yellowstone:\n32 Wingos\nThat's it. That's the workout.\nKeep the pace consistently inconsistent",
                "science": "32 Wingos is equal to 50.9 furlongs, according to DAISY™."
            },

            {
                "intensity": "CHAOTIC",
                "workout": "The Porcupine Prance:\nRun random paces, switching every 30s, for seven minutes\nrepeat 3x\nLook out for bikers and lane 1 walkers",
                "science": "Designed by DAISY™ for optimized natural variation."
            },
            
            {
                "intensity": "EXAM",
                "workout": "The Uncle George:\nRun 32 Wingos\nAt your best pace\nNo stopping",
                "science": "10.24 km: The ultimate Wingate test."
            },
            {
                "intensity": "HARMONY",
                "workout": "The Shuffle:\nGallop (tempo) pace to your favorite album\nTempo song 1, trot song 2, tempo song 3, trot song 4...\nRepeat until album is complete",
                "science": "Music-synchronized training increases harmonic efficiency by 32%."
            }
        ],
        "workout_intros": [
            "Based on your metrics, DAISY™ has crafted a specialized training protocol.",
            "Your personalized workout has been calculated using advanced algorithms.",
            "DAISY™ designed a workout that matches your unique profile.",
            "Here's your DAISY™-optimized training sequence."
        ],
        "insights": [
            "DAISY™ analysis indicates a {probability}% chance of optimal conditions today.",
            "Your training patterns suggest {animal}-like efficiency on the track.",
            "Based on your metrics, lane {lane} might be your power lane today.",
            "Our models suggest you're ready for {pace}-level Wingos.",
            "DAISY™ suggests you're {probability}% more likely to PR while making race car noises."
        ],
        "ai_catchphrases": [
            "Quantum-calibrating your gallop length...",
            "Neural networks analyzing your running aura...",
            "Calculating optimal Wingatian position using string theory...",
            "Engaging 320-dimensional hyperspace analysis...",
            "Converting caffeine levels to quantum states..."
        ],
        "easter_eggs": {
            "x": {
                "title": "LEGENDARY",
                "workout": "Run 320 Wingos",
                "science": "Sometimes the simplest solution is the most effective.",
                "ai_insight": "DAISY™ suggests you're ready for something... special.",
                "meta": {
                    "models_consulted": 999,
                    "processing_time_ms": 0.1,
                    "quantum_states_analyzed": "320M+"
                }
            },
            "sam": {
                "title": "STRENGTH",
                "workout": "Blink Time:\n3 sets of: \n32 pushups\n32 squats\n32s plank\n32 burpees\n32 jumping jacks\n32 high knees\n32 butt kicks",
                "science": "A perfect balance of strength and strength.",
                "ai_insight": "DAISY™ suggests you need something... muscular.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.2,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "mel": {
                "title": "ENDURANCE",
                "workout": "Goran Dragic:\nPlank for 320 seconds\nVictory Wngo\nStretch",
                "science": "Take care of your core and your core will take care of you.",
                "ai_insight": "DAISY™ suggests you need something... enduring.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.3,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "maddy": {
                "title": "GET LOST",
                "workout": "Ladder:\n40m sprint\nRest: 60s\n80m sprint\nRest: 60s\n150m sprint\nRest: 60s\n160m sprint\nRest: 60s\n230m sprint\nRest: 60s\n420m sprint",
                "science": "Progressive overload at its finest.",
                "ai_insight": "DAISY™ suggests you need something... mysterious.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.4,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "nina": {
                "title": "FLEXIBILITY",
                "workout": "The Sacred Stretch Protocol:\n10-minute yoga/stretch routine\nFollow video but at your own pace\nPerfect for post-workout",
                "science": "Recovery is just as important as the workout.",
                "ai_insight": "DAISY™ suggests you need something... flexible.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.5,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "katherine": {
                "title": "STAIRMASTER",
                "workout": "The Stairmaster Protocol:\nSet 1: 3:20 up/down stairs\nWingo loop\nSet 2: 3:20 up/down stairs\nWingo loop\nSet 3: 3:20 up/down stairs",
                "science": "Building power and endurance through vertical movement.",
                "ai_insight": "DAISY™ suggests you need something... elevated.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.6,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "will": {
                "title": "TIMING",
                "workout": "The No-Watch Challenge:\nRun 1 m*le in exactly 6:50\nNo watch allowed\nIf off by 6+ seconds, repeat\nFocus on internal pacing",
                "science": "Developing internal clock and pace awareness.",
                "ai_insight": "DAISY™ suggests you need something... precise.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.7,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "lorena": {
                "title": "The Filly Special",
                "workout": "Philadelphia Freedom:\n10 Wingos at half mare-athon pace\nAbruptly stop and run the Wingate stairs",
                "science": "Channel your inner Rocky.",
                "ai_insight": "DAISY™ suggests you need something... legendary.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "job": {
                "title": "Fly Like an Eagle",
                "workout": "Infield sprints\n20 x field goal posts to wall\nAll-out effort",
                "science": "Make it Hurts.",
                "ai_insight": "DAISY™ suggests you need something... painful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
                        },
            "Eric": {
                "title": "Hustle",
                "workout": "Run a 5K in 17:37",
                "science": "Be like Bo Cruz.",
                "ai_insight": "DAISY™ suggests you need ...therapy.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "matt": {
                "title": "Song Roulette",
                "workout": "Christina-powered chaos:\n5 x km, each paced to random Christina song\nGenie in a bottle? 3:36. Come On Over? 3:09\nOne minute rest",
                "science": "Consult Wingo Pace Concverter for assistance.",
                "ai_insight": "DAISY™ suggests you need something... musical.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "scarlett": {
                "title": "The Naked Wrist Challenge",
                "workout": "Take off the Garmin:\nTempo for exactly 320 seconds\nMust finish within 5 seconds of 320s\nOutside range? Start over!",
                "science": "Timing is everything.",
                "ai_insight": "DAISY™ suggests you need something... punctual.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "meghan": {
                "title": "PARTNER",
                "workout": "Three-Legged Daisy:\n3 x three-legged Wingos\nFirst Wingo: Trot\nSecond Wingo: Canter \nThird Wingo: Gallop on your own\nRest 2-3 minutes between sets\nSwitch inside/outside leg positions each round\nFinish with victory lap",
                "science": "Building coordination and teamwork.",
                "ai_insight": "DAISY™ suggests you need something... connected.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.9,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "eli": {
                "title": "PARTNER",
                "workout": "Three-Legged Daisy:\n3 x three-legged Wingos\nFirst Wingo: Trot\nSecond Wingo: Canter\nThird Wingo: Gallop on your own\nRest 2-3 minutes between sets\nSwitch inside/outside leg positions each round\nFinish with victory lap",
                "science": "Building coordination and teamwork.",
                "ai_insight": "DAISY™ suggests you need something... connected.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.9,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "chris": {
                "title": "TIME MACHINE",
                "workout": "The Glory Days Protocol:\nDouble Wingo in 1:57\nThen 7 victory Wingos\nRelive your high school glory\nChannel your inner champion",
                "science": "Reconnecting with past performance levels.",
                "ai_insight": "DAISY™ suggests you need something... nostalgic.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.0,
                    "quantum_states_analyzed": "32M+"
                }
            },
            "ben": {
                "title": "STRENGTH",
                "workout": "Pullups and Wingos:\n10 pullups, Wingo (sub-70s)\n8 pullups, Wingo (sub-70s)\n6 pullups, Wingo (sub-70s)\n4 pullups, Wingo (sub-70s)\n2 pullups, Wingo (sub-70s)",
                "science": "Combining upper body strength with speed work.",
                "ai_insight": "DAISY™ suggests you need something... powerful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.1,
                    "quantum_states_analyzed": "32M+"
                }
            },
            }
        }

    @staticmethod
    def calculate_fitness_coefficient(user_data):
        """Totally scientific calculation of user's fitness potential"""
        return random.uniform(0.8, 1.2)

    @staticmethod
    def generate_insight(user_data):
        template = random.choice(WorkoutOptimizer.NEURAL_RESPONSES["insights"])
        return template.format(
            probability=random.randint(87, 99),
            animal=random.choice(["cheetah", "gazelle", "quantum horse", "winged unicorn", "time-traveling ostrich"])
        )

@app.route("/", methods=["GET"])
def home():
    return render_template("intro-daisy.html")

@app.route("/320AI", methods=["GET"])
def ai_system():
    return render_template("320AI.html")

@app.route("/workouts", methods=["GET"])
def three_twenty_day():
    # Simple predefined workouts
    workouts = [
        {
            "title": "The Wingate Protocol",
            "intensity": "HIGH",
            "workout": "3 sets of:\n320m sprint\n3:20 rest\n\nFocus on maximum power output",
            "science": "Based on the Wingate test protocol for anaerobic power"
        },
        {
            "title": "The 320 Ladder",
            "intensity": "MEDIUM",
            "workout": "320m\n640m\n960m\n\nRest: 3:20 between each",
            "science": "Progressive distance ladder for building endurance"
        }
    ]
    return render_template("workouts.html", workouts=workouts)

@app.route("/community", methods=["GET"])
def community():
    return render_template("community.html")

@app.route('/daisy')
def daisy():
    return render_template("about.html")

@app.route('/about')
def about():
    return redirect(url_for('daisy'))

@app.route("/merch", methods=["GET"])
def merch():
    return render_template("merch.html")

@app.route("/daisy-score", methods=["GET"])
def daisy_score():
    return render_template("daisy-score.html")

@app.route("/daisy3", methods=["GET"])
def daisy3():
    return render_template("daisy3.html")

@app.route("/game", methods=["GET"])
def game():
    return render_template("game.html")

@app.route("/coach", methods=["GET"])
def coach_daisy():
    return render_template("coach.html")

@app.route("/game/leaderboard", methods=["GET", "POST"])
def game_leaderboard():
    """Handle game leaderboard operations"""
    if request.method == "POST":
        try:
            data = request.json
            score = data.get('score', 0)
            player_name = data.get('player_name', 'Anonymous')
            
            # TODO: Implement leaderboard database operations
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"Error in leaderboard POST: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    else:
        try:
            # Return top scores
            # TODO: Implement leaderboard retrieval
            return jsonify({"scores": []})
        except Exception as e:
            logger.error(f"Error in leaderboard GET: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    """Generate a hyper-optimized workout using cutting-edge AI technology"""
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "No data provided"}), 400
            
        name = user_data.get('name', '').strip()
        if not name:
            return jsonify({"error": "Name is required"}), 400
            
        # Generate a random workout from the predefined list
        workout_optimizer = WorkoutOptimizer()
        workout = random.choice(workout_optimizer.NEURAL_RESPONSES["predefined_workouts"])
        
        response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
            "workout_intro": random.choice(workout_optimizer.NEURAL_RESPONSES["workout_intros"]),
            "workout_details": workout,
            "ai_insight": "DAISY™ has analyzed your data and generated this optimal workout.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.320,
                    "quantum_states_analyzed": "320^320"
                }
            }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analyze_potential", methods=["POST"])
def analyze_potential():
    """Analyze user's running potential using advanced AI metrics"""
    try:
        user_data = request.json
        if not user_data:
            return jsonify({"error": "No data provided"}), 400

        analysis = {
            "runner_name": user_data.get("name", "Anonymous Runner"),
            "analysis_timestamp": datetime.now().isoformat(),
            "ai_confidence": f"{random.randint(97, 100)}.{random.randint(10, 99)}%",
            "potential_metrics": {
                "quantum_speed_score": random.randint(80, 100),
                "neural_efficiency": f"{random.uniform(0.8, 1.0):.2f}",
                "genetic_potential": f"{random.randint(85, 99)}th percentile",
                "motivation_index": f"{random.uniform(8.5, 10.0):.1f}/10"
            },
            "ai_recommendations": [
                "Your running form shows remarkable similarity to a quantum-enhanced perpetual motion machine",
                f"Based on your data, you have a {random.randint(85, 98)}% chance of achieving your goals",
                "Our AI suggests visualizing yourself as a blockchain-powered rocket ship for optimal performance"
            ]
        }

        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error in analyze_potential: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """Handle email subscription"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get('email')
        if not email or not isinstance(email, str):
            return jsonify({"error": "Valid email is required"}), 400
            
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Successfully subscribed!"
            })
        except sqlite3.IntegrityError:
            return jsonify({
                "success": False,
                "message": "You're already subscribed!"
            }), 400
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in subscribe: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Server error. Please try again."
        }), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    """Handle chat interactions with DAISY™"""
    global client
    
    try:
        logger.info("\n=== DAISY Chat Debug ===")
        logger.info("1. Checking API client...")

        # Ensure client is initialized
        if not client:
            logger.info("Client not initialized, attempting to initialize...")
            client = init_openai_client()
            if not client:
                logger.error("Failed to initialize OpenAI client!")
                return jsonify({"error": "API client not configured"}), 500

        logger.info("2. Client initialized successfully")

        data = request.get_json()
        if not data or "message" not in data:
            logger.error("No message provided in request data")
            return jsonify({"error": "No message provided"}), 400

        message = data["message"]
        logger.info(f"3. Received message: '{message}'")

        # Step 1: Retrieve or create thread for this session
        try:
            thread_id = session.get("thread_id")
            logger.info(f"Current session thread_id: {thread_id}")
            logger.info(f"Session ID: {session.sid if hasattr(session, 'sid') else 'No session ID'}")
            
            if not thread_id:
                logger.info("No existing thread found, creating new one...")
                try:
                    # Create thread with retry logic and timeout
                    max_attempts = 5
                    for attempt in range(max_attempts):
                        try:
                            logger.info(f"Attempting to create thread (attempt {attempt + 1}/{max_attempts})")
                            thread = client.beta.threads.create(
                                timeout=60.0  # Increased timeout
                            )
                            thread_id = thread.id
                            session["thread_id"] = thread_id
                            session.modified = True  # Ensure session is saved
                            logger.info(f"Successfully created new thread: {thread_id}")
                            break
                        except Exception as thread_error:
                            logger.error(f"Error creating thread (attempt {attempt + 1}): {str(thread_error)}")
                            if attempt < max_attempts - 1:
                                time.sleep(min(2 ** attempt, 10))  # Exponential backoff with max 10 seconds
                            else:
                                raise
                except Exception as thread_error:
                    logger.error(f"All attempts to create thread failed: {str(thread_error)}")
                    return jsonify({"error": "Failed to create conversation thread"}), 500
            else:
                logger.info(f"Using existing thread: {thread_id}")

            # Step 2: Add user message
            logger.info("Adding user message to thread...")
            try:
                client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=message
                )
                logger.info("User message added successfully")
            except Exception as msg_error:
                logger.error(f"Error adding message: {str(msg_error)}")
                return jsonify({"error": "Failed to add message to thread"}), 500

            # Step 3: Start assistant run
            logger.info("Starting assistant run...")
            try:
                run = client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=ASSISTANT_ID
                )
                logger.info(f"Assistant run started with ID: {run.id}")
            except Exception as run_error:
                logger.error(f"Error starting assistant run: {str(run_error)}")
                return jsonify({"error": "Failed to start assistant"}), 500

            # Step 4: Poll until run completes
            start_time = time.time()
            while True:
                if time.time() - start_time > TIMEOUT:
                    logger.error("Assistant response timed out")
                    raise TimeoutError("Assistant response timed out")

                try:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    logger.info(f"Run status: {run_status.status}")
                    
                    if run_status.status == "completed":
                        logger.info("Assistant run completed successfully")
                        break
                    elif run_status.status == "failed":
                        error_msg = getattr(run_status, 'last_error', 'Unknown error')
                        logger.error(f"Assistant run failed: {error_msg}")
                        raise Exception(f"Assistant run failed: {error_msg}")
                except Exception as status_error:
                    logger.error(f"Error checking run status: {str(status_error)}")
                    raise
                time.sleep(1)

            # Step 5: Retrieve messages
            logger.info("Retrieving messages from thread...")
            try:
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                messages_sorted = sorted(messages.data, key=lambda x: x.created_at, reverse=True)
                logger.info(f"Found {len(messages_sorted)} messages")
            except Exception as list_error:
                logger.error(f"Error retrieving messages: {str(list_error)}")
                return jsonify({"error": "Failed to retrieve messages"}), 500

            # Step 6: Get latest assistant response
            logger.info("Extracting assistant response...")
            assistant_response = None
            for msg in messages_sorted:
                if msg.role == "assistant":
                    for content_part in msg.content:
                        if hasattr(content_part, "text"):
                            assistant_response = content_part.text.value
                            logger.info("Found assistant response")
                            break
                    if assistant_response:
                        break

            if not assistant_response:
                logger.error("No valid assistant response found in messages")
                raise Exception("No valid assistant response found")

            logger.info("4. Assistant response received successfully!")
            response_data = {
                "response": assistant_response,
                "thread_id": thread_id
            }
            logger.info(f"Returning response with thread_id: {thread_id}")
            return jsonify(response_data)

        except Exception as session_error:
            logger.error(f"Session/thread error: {str(session_error)}")
            return jsonify({"error": "Session error occurred"}), 500

    except TimeoutError as te:
        logger.error(f"Timeout error: {str(te)}")
        return jsonify({"error": "Request timed out"}), 504
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def generate_transition_text(question_type):
    """Generate quantum-themed transition text for Wingate protocol"""
    transitions = {
        'number': [
            "Your numerical patterns are creating fascinating Wingatian ripples...",
            "The system is calculating optimal trajectories based on your metrics...",
            "Your data points are forming a beautiful chaos pattern...",
            "The numbers are aligning in ways that would make Daisy proud...",
            "Your metrics are generating interesting quantum fluctuations..."
        ],
        'date': [
            "Time is relative in the Wingate realm...",
            "Your temporal coordinates are being processed...",
            "The space-time continuum is analyzing your schedule...",
            "Your timeline is creating interesting electric echoes...",
            "The temporal field is calculating optimal race windows..."
        ],
        'text': [
            "Your words are resonating with the quantum field...",
            "The linguistic patterns are forming quantum harmonies...",
            "Your response is generating interesting semantic waves...",
            "The quantum realm is processing your narrative...",
            "Your text is creating beautiful quantum patterns..."
        ]
    }
    
    transition_array = transitions.get(question_type, transitions['text'])
    return random.choice(transition_array)

def generate_wingate_workout(answers):
    """Generate a personalized workout based on Wingate questionnaire answers"""
    name = answers.get('name', 'Runner')
    
    workouts = [
        f"Based on your quantum state analysis, {name}, here's your optimized workout:\n\n"
        "1. Warmup: 15 minutes of dimensional shifting (easy jogging)\n"
        "2. Main Set: 6-8 x Double Wingo at 5K pace with 2-minute recovery\n"
        "3. Cooldown: 10 minutes of temporal realignment (light jog)\n\n"
        "Remember: Time is relative, but proper form is constant! 🌌",
        
        f"I've analyzed your metrics, {name}. Your workout:\n\n"
        "1. Dynamic warmup: 20 minutes progressive\n"
        "2. Speed work: 12-15 x Wingos at m*le race pace\n"
        "3. Recovery: 2 minutes between reps\n"
        "4. Cooldown: 15 minutes easy\n\n"
        "Pro tip: Channel your inner quantum horse! 🐎",
        
        f"Your data suggests this optimal sequence, {name}:\n\n"
        "1. Warmup: 2 KM easy pace\n"
        "2. Main set: 3 x (KM @ 5K pace, 3 min rest)\n"
        "3. Bonus: 4 x Furlongs at max effort\n"
        "4. Cooldown: 1 KM + stretching\n\n"
        "Remember: Pain is temporary, quantum gains are forever! ⚛️"
    ]
    
    return random.choice(workouts)

# Wingate questionnaire state
wingateState = {
    'currentQuestion': 0,
    'answers': {},
    'questions': [
        {
            'text': "Welcome to the Wingate Protocol™! First, what's your name?",
            'type': "text",
            'field': "name"
        },
        {
            'text': "Kilometers run in past 320 days?",
            'type': "number",
            'field': "miles_past_320_days"
        },
        {
            'text': "Furlongs planned for 2025?",
            'type': "number",
            'field': "kilometers_2025"
        },
        {
            'text': "Average heart rate while walking?",
            'type': "number",
            'field': "avg_hr_walking"
        },
        {
            'text': "Days since last haircut?",
            'type': "number",
            'field': "recent_haircut"
        },
        {
            'text': "Iron levels?",
            'type': "number",
            'field': "iron_levels"
        },
        {
            'text': "Date of your last race?",
            'type': "date",
            'field': "last_race_date"
        },
        {
            'text': "Race of your last date?",
            'type': "text",
            'field': "last_date_race"
        }
    ]
}

@app.route('/transformation')
def transformation():
    return render_template("transformation.html")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Handle admin login"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.environ.get('ADMIN_PASSWORD', '320admin'):  # Default password if not set
            session['admin_logged_in'] = True
            session.permanent = True  # Make session last longer
            response = redirect(url_for('view_subscribers'))
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
        return render_template('admin/login.html', error='Invalid password')
    return render_template('admin/login.html')

@app.route("/admin/subscribers", methods=["GET"])
@admin_required
def view_subscribers():
    """Display the subscribers admin page"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT email, signup_date FROM subscribers ORDER BY signup_date DESC')
        subscribers = c.fetchall()
        conn.close()
        response = make_response(render_template('admin/subscribers.html', subscribers=subscribers))
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    except Exception as e:
        logger.error(f"Error viewing subscribers: {str(e)}")
        return render_template('admin/subscribers.html', error="Error loading subscribers"), 500

@app.route("/admin/logout")
def admin_logout():
    """Handle admin logout"""
    session.pop('admin_logged_in', None)
    response = redirect(url_for('admin_login'))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route("/wingo-converter", methods=["GET"])
def wingo_converter():
    return render_template("wingo_converter.html")

@app.route("/wingo")
def wingo():
    # Mock price data for the $WINGO token
    price = "1.885"
    market_cap = "41.25M"
    volume = "112.03M"
    return render_template("wingo.html", price=price, market_cap=market_cap, volume=volume)

@app.route("/whitepaper")
def whitepaper():
    return render_template("whitepaper.html")

@app.route("/archive-320")
def archive_320():
    return render_template("archive_320.html")

@app.route("/random_workout", methods=["GET"])
def random_workout():
    """Generate a random workout without requiring user input"""
    try:
        workout_optimizer = WorkoutOptimizer()
        workout = random.choice(workout_optimizer.NEURAL_RESPONSES["predefined_workouts"])
        
        response = {
            "timestamp": datetime.now().isoformat(),
            "fitness_coefficient": 3.20,
            "confidence_score": "320.00%",
            "workout_intro": random.choice(workout_optimizer.NEURAL_RESPONSES["workout_intros"]),
            "workout_details": workout,
            "ai_insight": "DAISY™ has generated this optimal workout for you.",
            "meta": {
                "models_consulted": 320,
                "processing_time_ms": 0.320,
                "quantum_states_analyzed": "320^320"
            }
        }
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this after other imports but before any routes
@app.before_request
def redirect_to_custom_domain():
    # Only redirect in production environment
    if os.environ.get('FLASK_ENV') != 'development' and request.host != "www.daisy320.com":
        return redirect(f"https://www.daisy320.com{request.full_path}", code=301)
    return None  # Allow request to continue normally

if __name__ == "__main__":
    # Development configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    try:
        # Simple development server configuration
        app.run(
            host='0.0.0.0',
            port=5009,
            threaded=True,
            debug=False
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise