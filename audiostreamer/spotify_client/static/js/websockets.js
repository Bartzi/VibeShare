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
    this.currentStopTime = this.context.currentTime;
    requestAnimationFrame(function (timeStamp) { that.playingWatchdog(timeStamp); });
};

AudioPlayer.prototype.playingWatchdog = function (timeStamp) {
    var currentTime = this.context.currentTime;
    var timeToGo = this.currentStopTime - currentTime;
    if (timeToGo < 2) {

        // set the new audiobuffer
        var byteLength = this.leftAudio.length + this.rightAudio.length;
        if (byteLength == 0) {
            // we have no more data to play...
            return;
        }
        this.audioBuffer = this.context.createBuffer(2, byteLength, 44100);
        this.audioBuffer.getChannelData(0).set(this.leftAudio);
        this.audioBuffer.getChannelData(1).set(this.rightAudio);
        if (!this.currentlyFillingBuffer) {
            this.leftAudio = new Float32Array();
            this.rightAudio = new Float32Array();
        }

        // create new  audio source
        var source = this.context.createBufferSource();
        source.buffer = this.audioBuffer;
        source.connect(this.context.destination);
        source.start(this.currentStopTime);

        // say when to stop and update variables
        this.currentStopTime = this.currentStopTime + this.audioBuffer.duration / this.audioBuffer.numberOfChannels;
        console.log("playing until:" + this.currentStopTime);
    }

    var that = this;
    requestAnimationFrame(function (timeStamp){ that.playingWatchdog(timeStamp); });
};


$(document).ready(function(){

    connection = new WebSocket('ws://127.0.0.1:8080/');
    connection.binaryType = 'arraybuffer';
    BSON = bson().BSON;

    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContext();
    audioPlayer = new AudioPlayer(audioContext);




    connection.onopen = function () {

        console.log("connection is open");
        var data = BSON.serialize({"message": "playlist"}, false, true, false);
        connection.send(data);

    };

    connection.onmessage = function(message) {
        var a;
        try {
            a = BSON.deserialize(new Int8Array(message.data));
            $('.placeholder').append(a.message);
        } catch (e) {
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
        var data = BSON.serialize({"message": "play"}, false, true, false);
        connection.send(data);
    });
});

function playMusic(args) {
    var data = args.data;
    musicbuffer = data;
    if (!isPlaying) {
        processNode.connect(audioContext.destination);
        isPlaying = true;
    } else {
    }
}

function processAudio(event) {
    console.log('bla');

}