import "@testing-library/jest-dom";

// Mock Web Audio API
class MockAnalyserNode {
  frequencyBinCount = 128;
  fftSize = 256;
  getByteFrequencyData(arr: Uint8Array) {
    for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
  }
  getByteTimeDomainData(arr: Uint8Array) {
    for (let i = 0; i < arr.length; i++) arr[i] = 128;
  }
  connect() {
    return this;
  }
  disconnect() {}
}

class MockGainNode {
  gain = { value: 1 };
  connect() {
    return this;
  }
  disconnect() {}
}

class MockMediaElementSourceNode {
  connect() {
    return this;
  }
  disconnect() {}
}

class MockAudioContext {
  state = "running";
  createAnalyser() {
    return new MockAnalyserNode();
  }
  createGain() {
    return new MockGainNode();
  }
  createMediaElementSource() {
    return new MockMediaElementSourceNode();
  }
  resume() {
    return Promise.resolve();
  }
  close() {
    return Promise.resolve();
  }
}

(globalThis as any).AudioContext = MockAudioContext;
(globalThis as any).webkitAudioContext = MockAudioContext;

// Mock HTMLMediaElement.play()
Object.defineProperty(HTMLMediaElement.prototype, "play", {
  configurable: true,
  value: () => Promise.resolve(),
});

Object.defineProperty(HTMLMediaElement.prototype, "pause", {
  configurable: true,
  value: () => {},
});
