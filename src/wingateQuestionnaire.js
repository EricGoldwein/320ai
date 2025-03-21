/**
 * Wingate Protocol™ Workout Questionnaire System
 * A quantum-inspired workout generation system
 */

function wingateQuestionnaire() {
    // Question definitions
    const questions = [
        { text: "Welcome to the Wingate Protocol™! First, what's your name?", type: "text", field: "name" },
        { text: "Miles run in past 320 days?", type: "number", field: "miles_past_320_days" },
        { text: "Kilometers planned for 2025?", type: "number", field: "kilometers_2025" },
        { text: "Average heart rate while walking?", type: "number", field: "avg_hr_walking" },
        { text: "Days since last haircut?", type: "number", field: "recent_haircut" },
        { text: "Iron levels?", type: "number", field: "iron_levels" },
        { text: "Date of your last race?", type: "date", field: "last_race_date" },
        { text: "Race of your last date?", type: "text", field: "last_date_race" },
        { text: "Sum of last four digits of your SSN divided by 2?", type: "number", field: "ssn_digit_sum" }
    ];

    // Name variations for easter eggs
    const nameVariations = {
        samuel: ['sam', 'samuel', 'sammy'],
        mel: ['mel', 'melissa', 'melanie', 'melvin'],
        maddy: ['maddy', 'madeline', 'madison', 'maddie'],
        nina: ['nina', 'nena', 'ninah']
    };

    // Easter egg workouts
    const easterEggs = {
        x: (name) => `LEGENDARY X WORKOUT DETECTED! ${name}, you've unlocked something special:

1. Run 320 laps.

That's it.
That's the workout.

Good luck.

Science: Some say this workout was crafted by the George Wingate himself 🏃‍♂️`,

        samuel: (name) => `THE SACRED PUSHUP PROTOCOL HAS BEEN ACTIVATED! ${name}, your destiny awaits:

32 pushups.
3 x 32 second plank
2* 32 jump lunges
32 squats
32 second wall sit

This is the way.

Our algorithms have determined this is the optimal number. Trust the process. 💪`,

        mel: (name) => `INITIATING THE TRIPLE PLANK PROTOCOL! ${name}, prepare yourself:

3 sets of:
320 second plank

Rest? What's that?

Science: Time dilates during planks. These will feel like eternities.
Pro tip: Our AI suggests counting backwards from 320 to maintain sanity. 🧘‍♂️`,

        maddy: (name) => `THE QUANTUM DISTANCE LADDER HAS BEEN SUMMONED! ${name}, behold:

Progressive Distance Sequence Ladder (2x):
40m
80m
150m
160m
230m
420m

The numbers, what do they mean?

Science: This sequence was discovered during Mr. Wingate's 1885 Yellowstone expedition. 🏃‍♀️`,

        nina: (name) => `THE SACRED STRETCH PROTOCOL HAS BEEN ACTIVATED! ${name}, time to get flexible:

The Ultimate Stretch Sequence:
1. 10-minute yoga/stretch routine
2. Follow along with video
3. Perfect for post-workout recovery

Watch Video: https://www.youtube.com/watch?v=nlitqDM40BE

Science: Our quantum algorithms have determined this is the optimal recovery protocol. 🧘‍♀️`
    };

    // Type-specific responses
    const typeResponses = {
        number: [
            "Your numerical patterns are creating fascinating Wingatian ripples...",
            "The system is calculating optimal trajectories based on your metrics...",
            "Your data points are forming a beautiful chaos pattern...",
            "The numbers are aligning in ways that would make Daisy proud...",
            "Your metrics are generating interesting quantum fluctuations..."
        ],
        date: [
            "Time is relative in the Wingate realm...",
            "Your temporal coordinates are being processed...",
            "The space-time continuum is analyzing your schedule...",
            "Your timeline is creating interesting electric echoes...",
            "The temporal field is calculating optimal race windows..."
        ],
        text: [
            "Your words are resonating with the quantum field...",
            "The linguistic patterns are forming quantum harmonies...",
            "Your response is generating interesting semantic waves...",
            "The quantum realm is processing your narrative...",
            "Your text is creating beautiful quantum patterns..."
        ]
    };

    // Default workouts
    const defaultWorkouts = [
        (name) => `Here's your quantum-optimized training plan, ${name}:
            
1. Warmup: 15 minutes of dimensional shifting (easy jogging)
2. Main Set: 6-8 x 800m at 5K pace with 2-minute recovery
3. Cooldown: 10 minutes of temporal realignment (light jog)

Remember: Time is relative, but proper form is constant! 🌌`,
        
        (name) => `I've analyzed your quantum state, ${name}. Here's your workout:
            
1. Dynamic warmup: 20 minutes progressive
2. Speed work: 12-15 x 400m at mile race pace
3. Recovery: 2 minutes between reps
4. Cooldown: 15 minutes easy

Pro tip: Visualize yourself as a horse in the Kentucky Derby! 🐎`,
        
        (name) => `Based on your mitochondrial resonance, ${name}, try this:
            
1. Warmup: 2 mile easy pace
2. Main set: 3 x (1600m @ 5K pace, 3 min rest)
3. Bonus: 4 x 200m at max effort
4. Cooldown: 1 mile + stretching

Remember: Pain is temporary, quantum gains are forever! ⚛️`
    ];

    let state = {
        currentQuestion: 0,
        answers: {},
        specialWorkout: null
    };

    function getRandomResponse(type) {
        const responses = typeResponses[type] || typeResponses.text;
        return responses[Math.floor(Math.random() * responses.length)];
    }

    function checkEasterEggs() {
        const name = state.answers.name?.toLowerCase();
        if (!name) return null;

        // Check for 'x' first
        if (name.includes('x')) {
            return easterEggs.x(state.answers.name);
        }

        // Check other name variations
        for (const [key, variations] of Object.entries(nameVariations)) {
            if (variations.some(v => name.includes(v))) {
                return easterEggs[key](state.answers.name);
            }
        }

        return null;
    }

    function getDefaultWorkout() {
        return defaultWorkouts[Math.floor(Math.random() * defaultWorkouts.length)](state.answers.name);
    }

    function askNextQuestion() {
        if (state.currentQuestion < questions.length) {
            return questions[state.currentQuestion].text;
        } else {
            state.specialWorkout = checkEasterEggs() || getDefaultWorkout();
            return state.specialWorkout;
        }
    }

    function answerQuestion(response) {
        if (state.currentQuestion < questions.length) {
            const question = questions[state.currentQuestion];
            state.answers[question.field] = response;
            
            // Get type-specific response
            const typeResponse = getRandomResponse(question.type);
            
            state.currentQuestion++;
            
            if (state.currentQuestion < questions.length) {
                return `${typeResponse}\n\n${askNextQuestion()}`;
            } else {
                state.specialWorkout = checkEasterEggs() || getDefaultWorkout();
                return `${typeResponse}\n\nQuestionnaire complete! Generating your personalized workout plan...\n\n${state.specialWorkout}`;
            }
        }
        
        return state.specialWorkout || "Questionnaire already completed!";
    }

    return { askNextQuestion, answerQuestion, state };
}

module.exports = { wingateQuestionnaire }; 