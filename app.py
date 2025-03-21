from flask import Flask, request, jsonify, render_template, url_for, send_from_directory, session, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
from datetime import datetime
import sqlite3
import os
import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from functools import wraps
import time
from config import OPENAI_API_KEY, ASSISTANT_ID, MAX_RETRIES, TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the templates directory
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
logger.info(f"Template directory: {template_dir}")
logger.info(f"Template directory exists: {os.path.exists(template_dir)}")
logger.info(f"Template directory contents: {os.listdir(template_dir)}")

# Configure chat history storage
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

app = Flask(__name__, 
    static_folder='static', 
    static_url_path='/static',
    template_folder=template_dir
)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')  # Get from environment variable

# Initialize rate limiter with simpler configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://"  # Use in-memory storage for Windows compatibility
)

# Initialize environment variables
logger.info("Loading environment variables...")
load_dotenv()

# Initialize OpenAI client
try:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("No API key found in environment")
        client = None
    else:
        client = OpenAI(
            api_key=api_key,
            timeout=30  # Use a default timeout
        )
        logger.info(f"OpenAI client initialized successfully with API key starting with: {api_key[:8]}...")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")
    client = None

# Add error handler for OpenAI API errors
def handle_openai_error(error):
    logger.error(f"OpenAI API error: {str(error)}")
    if "rate limit" in str(error).lower():
        return "I'm a bit overwhelmed right now. Please try again in a minute."
    elif "timeout" in str(error).lower():
        return "The response took too long. Please try again."
    else:
        return "I encountered an error. Please try again."

# Add a route to serve static files directly
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Database setup
def init_db():
    db_path = os.path.join(app.root_path, 'subscribers.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers
        (email TEXT PRIMARY KEY, signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
with app.app_context():
    init_db()

# Make sure chat memory is using file system
conversation_history = {}  # Clear this if it exists
# Add file-based storage for chat history

class WorkoutOptimizer:
    """Advanced Track Workout Generation System™"""

    NEURAL_RESPONSES = {
        "workout_intros": [
            "DAISY™ has analyzed your data and generated a precision-optimized workout...",
            "Based on your unique biomechanical waveform, DAISY™ prescribes this session...",
            "Your quantum fitness signature suggests this DAISY™-approved workout..."
        ],

        "predefined_workouts": [
            {
                "intensity": "AGILITY",
                "workout": "Mind the Divot:\n\nWarm-up: 1-2 easy Wingos\nMain Set: 6 x Wingo at tempo pace\nAt the divot: 15 two-legged hops",
                "science": "A test of agility, awareness, and your ability to laugh through pain"
            },
            {
                "intensity": "LEGEND",
                "workout": "ERock's 160:\n\n5 x Half-Wingos at threshold\nBetween HWs, select 2 from:\n- Pushups, Planks, Wall sits, Lunges, Bicycle crunches, Burpees, Situps, Jump lunges, Squat lunges, Squats\n 5 minute break\n Repeat",
                "science": "Choose wisely, suffer greatly"
            },
            {
                "intensity": "GRAB YOUR PARTNER",
                "workout": "Three-Legged Daisy:\n\nPartner Workout: 3 x Wingo three-legged runs:\n- First Wingo: Moderate pace, focus on coordination\n- Second Wingo: Moderate pace, focus on efficiency\n- Third Wingo: On your own\nRest 2-3 minutes and switch leg positions between sets",
                "science": "Three legs are better than two - a true test of coordination"
            },
            {
                "intensity": "CLASSIC",
                "workout": "The TRIMBLE:\n\n10 x Wingo total\n- First 160m: Very Fast\n- Second 160m: Very Slow",
                "science": "The key is maximizing the contrast between fast and slow"
            },
            {
                "intensity": "CORE",
                "workout": "320 Seconds of Pain:\n\n- 60s standard plank\n- 60s left side\n- 60s right side\n- 60s reverse plank\n- 80s finale (standard)",
                "science": "The ultimate core stability test"
            },
            {
                "intensity": "MUSICAL",
                "workout": "Song Roulette:\n\n3km of Christina chaos:\n- Each km paced to random Christina\n- Hit 'Fighter'? Time to sprint!\n- 'Beautiful'? Recovery pace",
                "science": "Music-synchronized training for optimal performance"
            },
            {
                "intensity": "BACKWARDS",
                "workout": "Do Look Back in Anger:\n\n- 8 x 80m backwards buildup\n- 6 x alternating half-Wingo (front-back)\n- 4 x alternating Wingo (front-back)\n- Stay out of lane 1",
                "science": "Sally can no longer wait"
            },
            {
                "intensity": "LADDER",
                "workout": "Get Lost:\n\n- 40m sprint\n- 80m, 150m, 160m progression\n- 230m, 420m buildup\n- Down the ladder\n- Do it again",
                "science": "We have to go back"
            },
            {
                "intensity": "ENDURANCE",
                "workout": "The Yellowstone:\n\n- 32 x Wingo\n- That's it. That's the workout.\n- Keep the pace consistently inconsistent",
                "science": "Simple but brutal - sometimes less is more"
            },
            {
                "intensity": "PRECISION",
                "workout": "The Clock:\n\n- Run for exactly 320 seconds\n- Must finish within 5s window\n- Outside range? Start over!",
                "science": "Time is of the essence - precision is key"
            },
            {
                "intensity": "STRENGTH",
                "workout": "The G.W. Wingate Challenge:\n\n- Hang on field goal post\n- Total time: 320 seconds\n- Add 10 seconds for every 30 seconds of rest",
                "science": "Grip it and trip it"
            },
            {
                "intensity": "RECOVERY",
                "workout": "Caroline in My Mind:\n\n- 10-minute yoga/stretch routine\n- Follow video but at your own pace\n- Perfect for post-workout\n\nWatch Video: https://www.youtube.com/watch?v=nlitqDM40BE",
                "science": "Essential recovery for optimal performance"
            }
        ],

        "workouts": [
            {
                "intensity": "MODERATE",
                "workout": "Warm-up: 1-2 easy laps\nMain Set: 6 x Wingo at tempo pace\nCool-down: 1-2 easy laps",
                "science": "This workout targets your aerobic threshold while maintaining form integrity."
            },
            {
                "intensity": "HIGH",
                "workout": "Warm-up: 1-2 easy laps\nMain Set: 8 x Wingo at 5k pace\nRecovery: 90s between repeats\nCool-down: 1-2 easy laps",
                "science": "High-intensity intervals improve your VO2 max and running economy."
            },
            {
                "intensity": "VERY HIGH",
                "workout": "Warm-up: 1-2 easy laps\nMain Set: 12 x Wingo at m*le pace\nRecovery: 60s between repeats\nCool-down: 1-2 easy laps",
                "science": "Short, fast intervals enhance your anaerobic capacity and speed."
            },
            {
                "intensity": "THE_DAISY",
                "workout": "Partner Workout: The Three-Legged Daisy\n\n3 x three-legged Wingos:\n- First Wingo: Moderate pace, focus on coordination\n- Second Wingo: Pick up the pace, channel your inner mutant\n- Third Wingo: All out (if you dare)\n\nRest 2-3 minutes between sets\nSwitch inside/outside leg positions each round\n\nFinish with a victory trot (regular two legs)",
                "science": "Because two legs are boring and four legs would be cheating"
            },
            {
                "intensity": "TRIMBLE_SPECIAL",
                "workout": "The TRIMBLE Split:\n\n10 x Wingo total\n- First 160m: Very Fast\n- Second 160m: Very Slow\n- Maximize the contrast",
                "science": "Scientifically designed to confuse your legs and entertain spectators"
            },
            {
                "intensity": "ENDURANCE_PLUS",
                "workout": "4 sets of (Wingo at 5K pace + 50 crunches + 160m fast + 25 mountain climbers), Wingo trot between sets\nFinish with Double Wingo cooldown",
                "science": "Perfect for building comprehensive track strength"
            },
            {
                "intensity": "PROGRESSIVE_MADNESS",
                "workout": "2 rounds of:\n- Double Wingo at tempo pace, 30 jumping jacks\n- Wingo at 5K pace, 40-second plank\n- Furlong at 3K pace, 50 high knees\n- half-Wingo all out, collapse gracefully",
                "science": "Calculated to maximize both entertainment and gains"
            },
            {
                "intensity": "RANDOM_GLORY",
                "workout": f"6 x ({random.choice([80, 160])}m sprint + {random.randint(5, 15)} burpees)\nFinish with victory Wingo",
                "science": "DAISY™-designed chaos for maximum adaptation"
            },
            {
                "intensity": "THRESHOLD_PLUS",
                "workout": "8 x (half-Wingo at threshold + 15 squat jumps)\n2 x Wingo float\nFinish with 1 minute plank for good luck",
                "science": "Designed by our most chaotic algorithm"
            },
            {
                "intensity": "TRACK_PARTY",
                "workout": "Warmup: 2 Wingo easy\nMain Set:\n- backwards Wingo\n- Sideways Wingo (switch halfway)\n- Normal Wingo\nRepeat 3 times with 20 jumping jacks between rounds\nCooldown: victory WIngo",
                "science": "Because training should be fun sometimes"
            },
            {
                "intensity": "SPEED_ROULETTE",
                "workout": f"Warmup: 2 Wingos\n6 x ({random.choice([80, 160])}m sprint + {random.randint(10, 30)} jumping jacks)\n2 x Wingo float\nCooldown: victory Wingo",
                "science": "Randomized for optimal unpredictability"
            },
            {
                "intensity": "PLANK_CHALLENGE",
                "workout": "The 320-Second Plank Challenge:\n\n1. 60s standard plank\n2. 60s left side plank\n3. 60s right side plank\n4. 60s reverse plank\n5. 80s standard plank finale\n\nTotal: 320 seconds of core stability mastery",
                "science": "Perfectly calibrated to strengthen your core in exactly 320 seconds"
            },
            {
                "intensity": "EROCK_160",
                "workout": "ERock's 160 - The Ultimate Track + Strength Combo:\n\n5 x 160m repeats (at threshold) - Round 1:\n- After #1: 32s forearm plank + 32 jumping jacks\n- After #2: 32 situps + 32s wall sit\n- After #3: 32 bicycles + 32 squats\n- After #4: 16 pushups + 16 jump squats\n- After #5: 32s straight arm plank + 16 burpees\n\nRest 2-3 minutes, then...\n\nRepeat entire sequence once more!\n\nCooldown: 320m easy jog",
                "science": "A legendary workout crafted by the track master himself"
            },
            {
                "intensity": "SONG_ROULETTE",
                "workout": "Song Roulette Challenge:\n\n3 rounds of:\n- 1km at the pace of whatever song plays\n- Recovery: Walk until next song starts\n\nRules:\n1. No skipping songs\n2. Must adjust pace to match song tempo\n3. If 'Fighter' comes on, sprint the remainder\n\nTotal: 3km of musical mayhem",
                "science": "Music-synchronized training proven to be 320% more entertaining"
            }
        ],

        "insights": [
            "DAISY™ analysis indicates a {probability}% chance of optimal conditions today.",
            "Your training patterns suggest {animal}-like efficiency on the track.",
            "Based on your metrics, lane {lane} might be your power lane today.",
            "Our models suggest you're ready for {pace}-level Wingos.",
            "DAISY™ suggests you're {probability}% more likely to PR while making race car noises.",
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
                "workout": "Blink Time:\n32 pushups\n32 squats\n32 plank rotations\n32 mountain climbers\n32 burpees\n32 jumping jacks\n32 high knees\n32 butt kicks\n32 arm circles\n32 leg swings",
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
                "workout": "Triple Plank Protocol:\nSet 1: 320 second plank\nRest: 60 seconds\nSet 2: 320 second plank\nRest: 60 seconds\nSet 3: 320 second plank",
                "science": "Building core stability and mental fortitude.",
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
                "title": "Watch Out",
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
            "arielle": {
                "title": "PROMISE",
                "workout": "The Promise Protocol:\n1. Swear to sign up for Al Goldstein 5k\n2. Complete 8 Wingos\n3. Keep your word",
                "science": "Building commitment and follow-through.",
                "ai_insight": "DAISY™ suggests you need something... meaningful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.2,
                    "quantum_states_analyzed": "32M+"
                }
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
            animal=random.choice(["gazelle", "cheetah", "falcon", "antelope"]),
            lane=random.choice(["3", "4", "5", "6"]),
            pace=random.choice(["threshold", "interval", "repetition", "race"])
        )


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only check login for coach page and admin routes
        if request.endpoint in ['coach_daisy', 'chat', 'view_subscribers']:
            if 'logged_in' not in session:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'Old-Ril$y':  # Simple password
            session['logged_in'] = True
            next_page = request.args.get('next', 'home')
            return redirect(url_for(next_page))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/320AI", methods=["GET"])
def ai_system():
    return render_template("320AI.html")

@app.route("/320Day", methods=["GET"])
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

@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@app.route("/merch", methods=["GET"])
def merch():
    return render_template("merch.html")

@app.route("/320split", methods=["GET"])
def crypto():
    try:
        # Mock data for $WINGO stats with default values
        price = "3.20"  # String to avoid floating point issues
        market_cap = "320,000,000.0"  # Pre-formatted string
        volume = "32,000,000.0"  # Pre-formatted string
        return render_template("320split.html", price=price, market_cap=market_cap, volume=volume)
    except Exception as e:
        # Fallback values if formatting fails
        return render_template("320split.html", price="3.20", market_cap="320,000,000.0", volume="32,000,000.0")

@app.route("/whitepaper", methods=["GET"])
def whitepaper():
    return render_template("whitepaper.html")

@app.route('/DAISY')
@app.route('/daisy')
def daisy():
    return render_template("daisy.html")

@app.route("/daisy-score", methods=["GET"])
def daisy_score():
    return render_template("daisy-score.html")

@app.route("/daisy3", methods=["GET"])
def daisy3():
    return render_template("daisy3.html")

@app.route("/game", methods=["GET"])
def game():
    return render_template("game.html")

@app.route("/game2", methods=["GET"])
def game2():
    return render_template("game2.html")

@app.route("/coach-daisy", methods=["GET"])
@login_required
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
            
        name = user_data.get('name', '').lower().strip()
        if not name:
            return jsonify({"error": "Name is required"}), 400
            
        # Easter egg for name containing "x"
        if 'x' in name:
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "You have unlocked the legendary X workout...",
                "workout_details": {
                    "intensity": "LEGENDARY",
                    "workout": "Run 320 laps.\n\nThat's it.\nThat's the workout.\n\nGood luck.",
                    "science": "Some say this workout was crafted by the ancient track gods themselves"
                },
                "ai_insight": "Our models are both impressed and concerned.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.320,
                    "quantum_states_analyzed": "320^320"
                }
            }
            return jsonify(response)

        # Easter egg for Samuel variations
        samuel_variations = ['sam', 'samuel', 'sammy']
        if any(variation in name for variation in samuel_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Shin Splint Prevention Protocol has been activated...",
                "workout_details": {
                    "intensity": "STRENGTH",
                    "workout": "32 pushups. 32 squats. 32s plank (3x). 32 jump lunges. 32 calf raises. \n\nYou'll be a regular at the gym starting... now",
                    "science": "Our wingatian algorithms have determined this is the optimal number. Trust the process."
                },
                "ai_insight": "DAISY™ suggests you need something ... stronger.",
                "meta": {
                    "models_consulted": 32,
                    "processing_time_ms": 3.20,
                    "quantum_states_analyzed": "32^2"
                }
            }
            return jsonify(response)

        # Easter egg for Mel variations
        mel_variations = ['mel', 'melissa', 'melanie', 'melvin']
        if any(variation in name for variation in mel_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "Initiating the Triple Plank Protocol...",
                "workout_details": {
                    "intensity": "ENDURANCE",
                    "workout": "Triple Plank:\n3 x 320-second planks (2 minute breaks)\n1 victory Wingo\n\nRunning is overrated",
                    "science": "Take care of your core and your core will take care of you."
                },
                "ai_insight": "DAISY™ suggests counting backwards from 320 to maintain sanity.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 320.0,
                    "quantum_states_analyzed": "plank^3"
                }
            }
            return jsonify(response)

        # Easter egg for Maddy variations
        maddy_variations = ['maddy', 'madeline', 'madison', 'maddie']
        if any(variation in name for variation in maddy_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Smoke Monster has been summoned...",
                "workout_details": {
                    "intensity": "MYSTERIOUS",
                    "workout": "A Double Lost Ladder:\n40m-80m-150m-160m-230m-420m\nClimb down the ladder\nDo it again",
                    "science": "This sequence was discovered during Mr. Wingate's 1885 Yellowstone Expedition."
                },
                "ai_insight": "Don't tell DAISY™ what you can't do.",
                "meta": {
                    "models_consulted": 1080,
                    "processing_time_ms": 3.20,
                    "quantum_states_analyzed": "40+80+150+160+230+420"
                }
            }
            return jsonify(response)

        # Easter egg for Nina variations
        nina_variations = ['nina', 'nena', 'ninah']
        if any(variation in name for variation in nina_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Sacred Stretch Protocol has been activated...",
                "workout_details": {
                    "intensity": "FLEXIBILITY",
                    "workout": "The Ultimate Stretch Sequence:\n\n1. 10-minute yoga/stretch routine\n2. Follow along with video\n3. Perfect for post-workout recovery\n\nWatch Video: https://www.youtube.com/watch?v=nlitqDM40BE",
                    "science": "Our quantum algorithms have determined this is the optimal recovery protocol."
                },
                "ai_insight": "The ancient scrolls speak of the power of proper stretching.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 3.20,
                    "quantum_states_analyzed": "stretch^3"
                }
            }
            return jsonify(response)

        # Easter egg for Katherine variations
        katherine_variations = ['katherine', 'katie', 'kat', 'kate']
        if any(variation in name for variation in katherine_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Stairmaster Protocol has been activated...",
                "workout_details": {
                    "intensity": "FLIGHT MODE",
                    "workout": "Step it up:\nSet 1: 3:20 up/down stairs\nWingo trot\nSet 2: 3:20 up/down stairs\nWingo trot\nSet 3: 3:20 up/down stairs\nWingo trot",
                    "science": "Building power and endurance through vertical movement."
                },
                "ai_insight": "DAISY™ suggests you need something... elevated.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.6,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Lorena
        if 'lorena' in name:
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Filly Special has been activated...",
                "workout_details": {    
                    "intensity": "HUSTLE",
                    "workout": "The Filly Special:\n10 Wingos at half mare-athon pace...then stop!\nEnjoy the city's energy\nRun the Wingate stairs",
                    "science": "Train like Rocky"
                },
                "ai_insight": "DAISY™ suggests you need something... legendary.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Will variations
        will_variations = ['will', 'william', 'willy', 'wil']
        if any(variation in name for variation in will_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Naked Wrist Challenge has been activated...",
                "workout_details": {
                    "intensity": "TIMING",
                    "workout": "The Naked Wrist Challenge:\nRun 1 m*le in exactly 6:50\nNo watch allowed\nIf off by 6+ seconds, repeat\nFocus on internal pacing",
                    "science": "Developing internal clock and pace awareness."
                },
                "ai_insight": "DAISY™ suggests you need something... precise.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.7,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Chris variations
        chris_variations = ['chris', 'christopher', 'christian']
        if any(variation in name for variation in chris_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Glory Days Protocol has been activated...",
                "workout_details": {
                    "intensity": "TIME MACHINE",
                    "workout": "The Glory Days Protocol:\n640m in 1:57\nThen 7 victory Wingos\nRelive your high school glory\nChannel your inner champion",
                    "science": "Reconnecting with past performance levels."
                },
                "ai_insight": "DAISY™ suggests you need something... nostalgic.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.0,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Ben variations
        ben_variations = ['ben', 'benjamin', 'bennie']
        if any(variation in name for variation in ben_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Pullup Protocol has been activated...",
                "workout_details": {
                    "intensity": "STRENGTH",
                    "workout": "Pullups and Wingos:\n10 pullups, Wingo (sub-70s)\n8 pullups, Wingo (sub-70s)\n6 pullups, Wingo (sub-70s)\n4 pullups, Wingo (sub-70s)\n2 pullups, Wingo (sub-70s)",
                    "science": "Insane gains only comes with pains."
                },
                "ai_insight": "DAISY™ suggests you need something... powerful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.1,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Arielle variations
        arielle_variations = ['arielle', 'ariel', 'ariella']
        if any(variation in name for variation in arielle_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Promise Protocol has been activated...",
                "workout_details": {
                    "intensity": "TRUST",
                    "workout": "The Promise:\n1. Swear to sign up for Al Goldstein 5k\n2. Complete 8 Wingos\n3. Keep your word",
                    "science": "Building commitment and follow-through."
                },
                "ai_insight": "DAISY™ suggests you need something... meaningful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 1.2,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Meghan variations
        meghan_variations = ['meghan', 'meg', 'megh']
        if any(variation in name for variation in meghan_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Three-Legged Protocol has been activated...",
                "workout_details": {
                    "intensity": "PARTNER",
                    "workout": "Three-Legged Daisy:\n3 x Wingo three-legged runs\nFirst Wingo: Moderate pace\nSecond Wingo: Moderate pace\nThird Wingo: On your own\nRest 2-3 minutes between sets\nSwitch inside/outside leg positions each round\nFinish with victory lap",
                    "science": "Building coordination and teamwork."
                },
                "ai_insight": "Your data suggests you need something... connected.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.9,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)

        # Easter egg for Eli variations
        eli_variations = ['eli', 'elijah', 'elias']
        if any(variation in name for variation in eli_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Three-Legged Protocol has been activated...",
                "workout_details": {
                    "intensity": "PARTNER",
                    "workout": "Three-Legged Daisy:\n3 x Wingo three-legged runs\nFirst Wingo: Moderate pace\nSecond Wingo: Moderate pace\nThird Wingo: On your own\nRest 2-3 minutes between sets\nSwitch inside/outside leg positions each round\nFinish with victory lap",
                    "science": "Building coordination and teamwork."
                },
                "ai_insight": "Your data suggests you need something... connected.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.9,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)
        
        # Easter egg for Scarlett variations
        scarlett_variations = ['scarlett', 'scarlet']
        if any(variation in name for variation in scarlett_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Watch Out Protocol has been activated...",
                "workout_details": {
                    "intensity": "PRECISION",
                    "workout": "Take off the Garmin:\nTempo for exactly 320 seconds\nMust finish within 5 seconds of 320s\nOutside range? Start over!",
                    "science": "Timing is everything."
                },
                "ai_insight": "Your data suggests you need something... punctual.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)
        
        # Easter egg for Job variations
        job_variations = ['job', 'jobby']
        if any(variation in name for variation in job_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Eagle Protocol has been activated...",
                "workout_details": {
                    "intensity": "GRITTY",
                    "workout": "Fly Like an Eagle:\nInfield sprints\n20 x field goal posts to wall\nAll-out effort",
                    "science": "Make it Hurts."
                },
                "ai_insight": "DAISY™ suggests you need something... painful.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)
 
 # Easter egg for Eric variations
        eric_variations = ['eric', 'erock', 'ericr']
        if any(variation in name for variation in eric_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Hustle Protocol has been activated...",
                "workout_details": {
                    "intensity": "PRESSURE",
                    "workout": "5K TIME:\nRun 15.625 Wingos in 17:37 (67.6s per Wingo)",
                    "science": "Be like Bo Cruz."
                },
                "ai_insight": "DAISY™ suggests you need ... Therapy.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)
        
        # Easter egg for Matt variations
        matt_variations = ['matt', 'matthew', 'matty']
        if any(variation in name for variation in matt_variations):
            response = {
                "timestamp": datetime.now().isoformat(),
                "fitness_coefficient": 3.20,
                "confidence_score": "320.00%",
                "workout_intro": "The Christina Protocol has been activated...",
                "workout_details": {
                    "intensity": "SONG ROULETTE",
                    "workout": "Christina-powered chaos:\n5 x km, each paced to random Christina song\nGenie in a bottle? 3:36. Come On Over? 3:09\nOne minute rest",
                    "science": "Consult Wingo Pace Converter for assistance."
                },
                "ai_insight": "DAISY™ suggests you need something... legendary.",
                "meta": {
                    "models_consulted": 320,
                    "processing_time_ms": 0.8,
                    "quantum_states_analyzed": "32M+"
                }
            }
            return jsonify(response)
        
        # Regular workout generation continues...
        fitness_coefficient = WorkoutOptimizer.calculate_fitness_coefficient(user_data)
        
        # Always select from predefined workouts
        workout_package = random.choice(WorkoutOptimizer.NEURAL_RESPONSES["predefined_workouts"])
        intro = "DAISY™ has selected a proven workout from our collection..."
        
        response = {
            "timestamp": datetime.now().isoformat(),
            "fitness_coefficient": round(fitness_coefficient, 4),
            "confidence_score": f"{random.randint(98, 100)}.{random.randint(10, 99)}%",
            "workout_intro": intro,
            "workout_details": workout_package,
            "ai_insight": WorkoutOptimizer.generate_insight(user_data),
            "meta": {
                "models_consulted": random.randint(320, 999),
                "processing_time_ms": random.uniform(0.1, 2.0),
                "quantum_states_analyzed": "320M+"
            }
        }
        
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in generate_workout: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

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
        db_path = os.path.join(app.root_path, 'subscribers.db')
        conn = sqlite3.connect(db_path)
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
@login_required
@limiter.limit("30 per minute")
def chat():
    """Handle chat interactions with DAISY™"""
    try:
        logger.info("\n=== DAISY Chat Debug ===")
        logger.info("1. Checking API client...")
        
        if not client:
            logger.error("OpenAI client is not initialized!")
            return jsonify({"error": "API client not configured"}), 500
        
        logger.info("2. Client initialized successfully")
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        user_id = request.remote_addr
        
        logger.info(f"3. Received message: '{message}'")
        logger.info(f"4. Conversation history length: {len(conversation_history)}")
        
        try:
            # Create a thread
            thread = client.beta.threads.create()
            
            # Add the conversation history to the thread
            for msg in conversation_history:
                client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=msg['role'],
                    content=msg['content']
                )
            
            # Add the current message to the thread
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )
            
            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )
            
            # Wait for the run to complete with timeout
            start_time = time.time()
            while True:
                if time.time() - start_time > TIMEOUT:
                    raise TimeoutError("Response took too long")
                    
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status == 'failed':
                    raise Exception("Assistant run failed")
                time.sleep(0.5)
            
            # Get the assistant's response
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_response = messages.data[0].content[0].text.value
            
            # Save the updated conversation history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
            logger.info("5. Assistant response received successfully!")
            return jsonify({
                "response": assistant_response,
                "conversation_history": conversation_history
            })
            
        except Exception as api_error:
            error_message = f"API Error: {str(api_error)}"
            logger.error(error_message)
            return jsonify({"error": error_message}), 500
            
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

@app.route('/transform2')
def transform2():
    return render_template("transform2.html")

@app.route("/admin/subscribers", methods=["GET"])
@login_required  # Keep admin routes protected
def view_subscribers():
    """Display the subscribers admin page"""
    try:
        db_path = os.path.join(app.root_path, 'subscribers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT email, signup_date FROM subscribers ORDER BY signup_date DESC')
        subscribers = c.fetchall()
        conn.close()
        return render_template('admin/subscribers.html', subscribers=subscribers)
    except Exception as e:
        logger.error(f"Error viewing subscribers: {str(e)}")
        return render_template('admin/subscribers.html', error="Error loading subscribers")

@app.route("/wingo-converter", methods=["GET"])
def wingo_converter():
    return render_template("wingo_converter.html")

if __name__ == "__main__":
    app.run(port=5009, debug=True)
