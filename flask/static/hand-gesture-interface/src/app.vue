<template>
  <div id="app">
    <div class="container">
      <div class="slides">
        <video ref="video" autoplay playsinline @loadedmetadata="handleLoadedmetadata" />
      </div>
      <div class="controls">
        <button @click="prevSlide" :disabled="currentSlide === 0">Previous</button>
        <button @click="nextSlide" :disabled="currentSlide === totalSlides - 1">Next</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import cv2 from 'cv2';
import HandDetector from 'cvzone/HandTrackingModule';

export default {
  name: 'App',
  setup() {
    const video = ref(null);
    const currentSlide = ref(0);
    const totalSlides = ref(0);
    const detector = new HandDetector();

    onMounted(() => {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        video.value.srcObject = stream;
        constpoll = setInterval(() => {
          detectHands();
          if (totalSlides.value > 0) {
            clearInterval(poll);
          }
        }, 100);
      });
    });

    const detectHands = () => {
      const imageData = cv2.cvtColor(video.value, cv2.COLOR_RGBA2BGR);
      const hands = detector.findHands(imageData);
      if (hands) {
        const hand = hands[0];
        const cx = hand.center[0];
        const cy = hand.center[1];

        if (cy <= detector.gestureThreshold) {
          if (hand.fingersUp[0] && !hand.fingersUp[1] && !hand.fingersUp[2] && !hand.fingersUp[3] && !hand.fingersUp[4]) {
            prevSlide();
          } else if (!hand.fingersUp[0] && !hand.fingersUp[1] && !hand.fingersUp[2] && !hand.fingersUp[3] && hand.fingersUp[4]) {
            nextSlide();
          }
        }
      }
    };

    const handleLoadedmetadata = () => {
      totalSlides.value = Math.ceil(video.value.videoWidth / video.value.videoHeight);
    };

    const nextSlide = () => {
      currentSlide.value++;
      fetch('/next');
    };

    const prevSlide = () => {
      currentSlide.value--;
      fetch('/prev');
    };

    return {
      video,
      currentSlide,
      totalSlides,
      prevSlide,
      nextSlide,
    };
  },
};
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

.container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 80%;
  max-width: 1200px;
  margin: 0 auto;
}

.slides {
  width: 70%;
  height: 70vh;
  overflow: hidden;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.controls {
  width: 30%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  border: none;
  outline: none;
}

button:hover {
  background-color: #e5e5e5;
}

button:active {
  background-color: #d5d5d5;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>