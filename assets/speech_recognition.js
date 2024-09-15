document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded and parsed");

    // Get the microphone button and input field
    var micButton = document.getElementById('mic-button');
    var inputMessage = document.getElementById('input-message');

    // Check if elements exist
    if (!micButton) {
        console.error("Microphone button not found.");
    } else {
        console.log("Microphone button found.");
    }

    if (!inputMessage) {
        console.error("Input field not found.");
    } else {
        console.log("Input field found.");
    }

    // Initialize variables
    var recognizing = false;
    var recognition;

    // Check if speech recognition is supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        console.log("Speech recognition supported.");

        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        recognition.onstart = function () {
            recognizing = true;
            micButton.classList.add('listening');
            console.log("Speech recognition started.");
        };

        recognition.onend = function () {
            recognizing = false;
            micButton.classList.remove('listening');
            console.log("Speech recognition stopped.");
        };

        recognition.onresult = function (event) {
            var transcript = event.results[0][0].transcript;
            console.log("Speech recognized: " + transcript);
            inputMessage.value = transcript;
            // Trigger the send button click programmatically
            document.getElementById('send-button').click();
        };

        micButton.addEventListener('click', function () {
            if (recognizing) {
                recognition.stop();
                recognizing = false;
                micButton.classList.remove('listening');
                console.log("Speech recognition manually stopped.");
            } else {
                recognition.start();
                console.log("Speech recognition manually started.");
            }
        });
    } else {
        console.error("Speech recognition not supported.");
        micButton.style.display = 'none';
        alert('Speech recognition is not supported in this browser.');
    }
});
