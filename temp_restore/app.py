from flask import Flask, request, jsonify, render_template, url_for
import random
from datetime import datetime
import sqlite3
import os

app = Flask(__name__, static_folder='static')

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

class WorkoutOptimizer:
    """Advanced Track Workout Generation System™"""

    NEURAL_RESPONSES = {
        "workout_intros": [
            "Based on track conditions and your metrics...",
            "After analyzing your training parameters...",
            "Our AI has processed your track-specific data...",
            "Using historical 320m segment data...",
            "Through advanced track performance modeling..."
        ],

        "workouts": [
            {
                "intensity": "SPEED_CHAOS",
                "workout": "8 x (320m sprint + 20 jumping jacks + 30-second plank) with 90s rest\nFinish with 640m cooldown",
                "science": "Optimized for multidimensional fitness adaptation"
            },
            {
                "intensity": "ENDURANCE_PLUS",
                "workout": "4 sets of (320m at 5K pace + 50 crunches + 160m fast + 25 mountain climbers), jog 320m between sets\nFinish with 800m cooldown",
                "science": "Perfect for building comprehensive track strength"
            },
            {
                "intensity": "PROGRESSIVE_MADNESS",
                "workout": "2 rounds of:\n- 800m at tempo pace, 30 jumping jacks\n- 640m at 5K pace, 40-second plank\n- 320m at 3K pace, 50 high knees\n- 320m all out, collapse gracefully",
                "science": "Calculated to maximize both entertainment and gains"
            },
            {
                "intensity": "RANDOM_GLORY",
                "workout": f"6 x ({random.choice([300, 400, 500])}m sprint + {random.randint(20, 40)} burpees)\nFinish with 800m victory lap",
                "science": "AI-generated chaos for maximum adaptation"
            },
            {
                "intensity": "THRESHOLD_PLUS",
                "workout": "8 x (320m at threshold + 15 squat jumps)\n2 x 400m float\nFinish with 1 minute plank for good luck",
                "science": "Designed by our most chaotic algorithm"
            },
            {
                "intensity": "TRACK_PARTY",
                "workout": "Warmup: 800m easy\nMain Set:\n- 320m backwards\n- 320m sideways (switch halfway)\n- 320m normal but make race car noises\nRepeat 3 times with 20 jumping jacks between rounds\nCooldown: 800m victory lap",
                "science": "Because training should be fun sometimes"
            },
            {
                "intensity": "SPEED_ROULETTE",
                "workout": f"Warmup: 800m easy\n6 x ({random.choice([200, 300, 400])}m sprint + {random.randint(10, 30)} jumping jacks)\n2 x 400m float\nCooldown: 320m victory lap",
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
            "Track analysis indicates a {probability}% chance of optimal conditions today.",
            "Your training patterns suggest {animal}-like efficiency on the track.",
            "Based on your metrics, lane {lane} might be your power lane today.",
            "Our models suggest you're ready for {pace}-level track intervals.",
            "Based on your last date's race and your last race date, we suggest lane {lane}.",
            "Your training data suggests you're {probability}% more likely to PR while making race car noises.",
        ],

        "ai_catchphrases": [
            "Quantum-calibrating your stride length...",
            "Neural networks analyzing your running aura...",
            "Calculating optimal track position using string theory...",
            "Engaging 320-dimensional hyperspace analysis...",
            "Converting caffeine levels to quantum states..."
        ]
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


@app.route("/", methods=["GET"])
def home():
    """Serve the main page with the workout form"""
    return render_template('index.html')


@app.route("/workouts", methods=["GET"])
def workouts():
    """Display the workouts page"""
    return render_template('workouts.html')


@app.route("/community", methods=["GET"])
def community():
    """Display the community page"""
    return render_template('community.html')


@app.route("/about", methods=["GET"])
def about():
    """Display the about page"""
    return render_template('about.html')


@app.route("/merch", methods=["GET"])
def merch():
    """Display the merchandise page"""
    return render_template('merch.html')


@app.route("/320split", methods=["GET"])
def crypto():
    """Display the 320SPLIT cryptocurrency page"""
    current_price = round(random.uniform(3.15, 3.25), 8)
    market_cap = current_price * 320000000
    return render_template('320split.html', 
                         price=current_price,
                         market_cap=market_cap,
                         volume=random.randint(320000, 3200000))


@app.route("/whitepaper", methods=["GET"])
def whitepaper():
    """Display the 320SPLIT whitepaper"""
    return render_template('whitepaper.html')


@app.route("/320AI", methods=["GET"])
def ai_data():
    """Display the 320AI data page"""
    return render_template('320ai.html')


@app.route("/generate_workout", methods=["POST"])
def generate_workout():
    """Generate a hyper-optimized workout using cutting-edge AI technology"""
    user_data = request.json
    
    # Easter egg for name "X"
    if user_data.get('name', '').lower() == 'x':
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
    
    # Regular workout generation continues...
    fitness_coefficient = WorkoutOptimizer.calculate_fitness_coefficient(user_data)
    workout_package = random.choice(WorkoutOptimizer.NEURAL_RESPONSES["workouts"])
    intro = random.choice(WorkoutOptimizer.NEURAL_RESPONSES["workout_intros"])
    
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


@app.route("/analyze_potential", methods=["POST"])
def analyze_potential():
    """Analyze user's running potential using advanced AI metrics"""
    user_data = request.json

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


@app.route("/subscribe", methods=["POST"])
def subscribe():
    """Handle email list subscription"""
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        db_path = os.path.join(app.root_path, 'subscribers.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if email already exists
        c.execute('SELECT email FROM subscribers WHERE email = ?', (email,))
        if c.fetchone():
            return jsonify({
                "success": False, 
                "message": "You're already on the list and your legs are getting stronger by the minute!"
            }), 400

        # Add new subscriber
        c.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Welcome to the 320 revolution! Your inbox will never be the same."
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Something went wrong. Maybe try running 320 meters and try again?"
        }), 500


if __name__ == "__main__":
    app.run(port=5009, debug=True)
