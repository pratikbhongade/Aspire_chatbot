document.addEventListener('DOMContentLoaded', function () {
    var micButton = document.getElementById('mic-button');
    var inputMessage = document.getElementById('input-message');

    // Check if the microphone button and input field exist
    if (!micButton || !inputMessage) {
        console.error("Microphone button or input field not found.");
        return;
    }

    var recognizing = false;
    var recognition;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        recognition.onstart = function () {
            recognizing = true;
            micButton.classList.add('listening');
        };

        recognition.onend = function () {
            recognizing = false;
            micButton.classList.remove('listening');
        };

        recognition.onresult = function (event) {
            var transcript = event.results[0][0].transcript;
            inputMessage.value = transcript;
            // Trigger the send button click programmatically
            document.getElementById('send-button').click();
        };

        micButton.addEventListener('click', function () {
            if (recognizing) {
                recognition.stop();
                recognizing = false;
                micButton.classList.remove('listening');
            } else {
                recognition.start();
            }
        });
    } else {
        // Speech Recognition not supported
        micButton.style.display = 'none';
        alert('Speech recognition is not supported in this browser.');
    }
});
