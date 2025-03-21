# Wingate Protocol™ Workout Questionnaire

A quantum-inspired workout generation system that creates personalized training plans based on user responses.

## Features

- Interactive questionnaire system
- Easter egg workouts for special names
- Quantum-themed responses
- Type-specific feedback
- Random workout generation
- Special case handling

## Installation

```bash
npm install
```

## Usage

Basic usage example:

```javascript
const { wingateQuestionnaire } = require('./src/wingateQuestionnaire');

// Create a new questionnaire instance
const questionnaire = wingateQuestionnaire();

// Get the first question
console.log(questionnaire.askNextQuestion());

// Answer questions
console.log(questionnaire.answerQuestion("John")); // First question
console.log(questionnaire.answerQuestion("100")); // Second question
// ... and so on
```

Run the example:

```bash
npm start
```

## Project Structure

```
wingate-workout/
├── src/
│   ├── index.js           # Example usage
│   └── wingateQuestionnaire.js  # Main questionnaire module
├── package.json
└── README.md
```

## Easter Eggs

The system includes special workouts for certain names:
- Names containing 'x'
- Variations of 'Samuel'
- Variations of 'Mel'
- Variations of 'Maddy'
- Variations of 'Nina'

## License

MIT 