var connection = null;
var isopen = false;
var session = undefined;
var audioContext = undefined;
var BSON = null;
var musicBuffer = null;
var isPlaying = false;
var processNode = null;
var source = null;
var audioPlayer = null;
var chunks = 0;

AudioPlayer = function (context) {
    var that = this;
    this.context = context;
    this.source = audioContext.createBufferSource();
    this.leftAudio = new Float32Array(0);
    this.rightAudio = new Float32Array(0);
    this.audioBuffer = null;
    this.isPlaying = false;
    this.audioLength = 0;
    this.alreadyPlayedTime = 0;
    this.currentStopTime = 0;
    this.currentlyFillingBuffer = false;
    this.framesToSkip = 0;
}

AudioPlayer.prototype.process = function (event) {
    var data = event.outputBuffer.getChannelData(0);
    for (var i=0; i<data.length; ++i) {
        data[i] = this.data[i] * 2.0 - 1.0;
    }
};

AudioPlayer.prototype.addData = function(data) {

    var audio = new Int16Array(data);

    var leftAudio = new Float32Array(audio.length / 2)
    var rightAudio = new Float32Array(audio.length / 2);

    for (var i=0; i<audio.length; ++i) {
        normalizedData = audio[i] / 32768;
        if (i % 2 == 0) {
            leftAudio[i / 2] =  normalizedData;
        } else {
            rightAudio[Math.floor(i / 2)] = normalizedData;
        }
    }

    this.currentlyFillingBuffer = true;
    this.appendData(leftAudio, rightAudio);
    this.currentlyFillingBuffer = false;
};

AudioPlayer.prototype.appendData = function(leftAudio, rightAudio) {
    var concatLeft = new Float32Array(this.leftAudio.length + leftAudio.length);
    concatLeft.set(this.leftAudio);
    concatLeft.set(leftAudio, this.leftAudio.length);
    this.leftAudio = concatLeft;

    var concatRight = new Float32Array(this.rightAudio.length + rightAudio.length);
    concatRight.set(this.rightAudio);
    concatRight.set(rightAudio, this.rightAudio.length);
    this.rightAudio = concatRight;
};


AudioPlayer.prototype.play = function () {

    var that = this;
    this.isPlaying = true;
    this.currentStopTime = this.context.currentTime;
    setTimeout(function (timeStamp){ that.playingWatchdog(timeStamp); }, 10);
};

AudioPlayer.prototype.playingWatchdog = function (timeStamp) {
    var currentTime = this.context.currentTime;
    var timeToGo = this.currentStopTime - currentTime;
    if (timeToGo < 2) {
  
        // set the new audiobuffer
        var byteLength = this.leftAudio.length + this.rightAudio.length;
        if (byteLength == 0) {
            // we have no more data to play...
            this.isPlaying = false;
            return;
        }
        this.audioBuffer = this.context.createBuffer(2, byteLength, 44100);
        this.audioBuffer.getChannelData(0).set(this.leftAudio);
        this.audioBuffer.getChannelData(1).set(this.rightAudio);

        // if we don't need to wait in order to synchronise
        if (this.framesToSkip == 0) {

            // create new  audio source
            var source = this.context.createBufferSource();
            source.buffer = this.audioBuffer;
            source.connect(this.context.destination);
            source.start(this.currentStopTime);
        } else {
            // decrease the times we need to wait
            this.framesToSkip--;
            console.log("skipping a frame");
        }

        // say when to stop and update variables
        this.currentStopTime = this.currentStopTime + this.audioBuffer.duration / this.audioBuffer.numberOfChannels;
        console.log("playing until:" + this.currentStopTime);

        // delete the buffers
        if (!this.currentlyFillingBuffer) {
            this.leftAudio = new Float32Array();
            this.rightAudio = new Float32Array();
        }
    }

    var that = this;
    setTimeout(function (timeStamp){ that.playingWatchdog(timeStamp); }, 10);
};


$(document).ready(function(){

    var host = window.location.hostname;
    connection = new WebSocket('ws://' + host + ':8080/ws');
    connection.binaryType = 'arraybuffer';

    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContext();
    audioPlayer = new AudioPlayer(audioContext);




    connection.onopen = function () {
        console.log("connection is open");
        var data = JSON.stringify({"message": "playlist"});
        connection.send(data);

    };

    connection.onmessage = function(message) {
        
        if (typeof message.data === "string") {
            data = JSON.parse(message.data)
            handleMessage(data);            
        } else {
            audioPlayer.addData(message.data);
        }
    }

    $('.send').on('click', function (event) {
        if (!connection) {
            console.log("No Connection!");
            return;
        }
        audioPlayer.play();
        console.log("starting to play");
    });

    $('.play').on('click', function (event) {
        if (!connection) {
            console.log("No Session!");
            return;
        }
        var songURI = $('#song').val();
        var data = {
            "message": "play",
            "song": songURI
        }
        connection.send(JSON.stringify(data));
    });
});

function handleMessage(data) {
    switch (data.message) {
        case "play":
            if (!audioPlayer.isPlaying) {
                audioPlayer.play();
            }
            break;
        case "skip":
            frames = data.frames;
            audioPlayer.framesToSkip = frames + 1;
            break;
        default:
            $('.placeholder').append(data.message);
            break;
    }
}

function processAudio(event) {
    console.log('bla');

}