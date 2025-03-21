const { wingateQuestionnaire } = require('./wingateQuestionnaire');

// Create an instance of the questionnaire
const questionnaire = wingateQuestionnaire();

// Example usage in a command-line interface
console.log("Starting the Wingate Protocol™ Questionnaire...\n");

// Get the first question
console.log(questionnaire.askNextQuestion());

// Example of how to handle responses
// In a real application, you would get these from user input
const exampleResponses = [
    "John",
    "100",
    "1000",
    "70",
    "30",
    "12",
    "2024-03-14",
    "Marathon",
    "42"
];

// Process each response
exampleResponses.forEach(response => {
    console.log("\nYour answer:", response);
    console.log("\n" + questionnaire.answerQuestion(response));
}); 