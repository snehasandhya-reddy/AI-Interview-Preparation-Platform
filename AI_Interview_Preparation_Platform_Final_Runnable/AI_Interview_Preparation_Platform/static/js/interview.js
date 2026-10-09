
const questions = window.INTERVIEW_DATA || [];
let index = 0;
let results = [];
let timerSeconds = 0;
let timerHandle = null;
let recognition = null;
let listening = false;

const qText = document.getElementById("questionText");
const answer = document.getElementById("answer");
const submitBtn = document.getElementById("submitBtn");
const voiceBtn = document.getElementById("voiceBtn");
const voiceStatus = document.getElementById("voiceStatus");
const counter = document.getElementById("counter");
const progressBar = document.getElementById("progressBar");
const timer = document.getElementById("timer");
const feedbackBox = document.getElementById("feedbackBox");

function loadQuestion() {
  const q = questions[index];
  qText.textContent = q.question;
  answer.value = "";
  counter.textContent = `Question ${index + 1} of ${questions.length}`;
  progressBar.style.width = `${(index / questions.length) * 100}%`;
  feedbackBox.classList.add("hidden");
  feedbackBox.innerHTML = "";
  submitBtn.disabled = false;
  submitBtn.textContent = "Evaluate Answer →";
  timerSeconds = 0;
  clearInterval(timerHandle);
  timerHandle = setInterval(() => {
    timerSeconds++;
    const m = String(Math.floor(timerSeconds / 60)).padStart(2,"0");
    const s = String(timerSeconds % 60).padStart(2,"0");
    timer.textContent = `${m}:${s}`;
  },1000);
}
loadQuestion();

submitBtn.addEventListener("click", async () => {
  const text = answer.value.trim();
  if (text.length < 10) {
    alert("Please provide a meaningful answer before evaluating.");
    return;
  }
  submitBtn.disabled = true;
  submitBtn.textContent = "Evaluating...";
  try {
    const res = await fetch("/api/evaluate", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question_id:questions[index].id, question:questions[index].question, answer:text})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Evaluation failed");
    results.push({...data, question_id:questions[index].id, question:questions[index].question, answer:text});
    feedbackBox.innerHTML = `
      <h3>Answer evaluation: ${data.overall}/100</h3>
      <p><b>Strengths:</b> ${data.strengths}</p>
      <p><b>Needs improvement:</b> ${data.weaknesses}</p>
      <p><b>Suggestions:</b> ${data.suggestions}</p>
      <button id="nextBtn" class="btn primary">${index === questions.length-1 ? "Finish Interview" : "Next Question →"}</button>
    `;
    feedbackBox.classList.remove("hidden");
    document.getElementById("nextBtn").addEventListener("click", nextQuestion);
  } catch(e) {
    alert(e.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "Evaluate Answer →";
  }
});

async function nextQuestion() {
  if (index < questions.length - 1) {
    index++;
    loadQuestion();
  } else {
    clearInterval(timerHandle);
    const res = await fetch("/finish", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({results})
    });
    const data = await res.json();
    if (data.ok) window.location.href = `/result/${data.interview_id}`;
    else alert(data.error || "Could not save interview.");
  }
}

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-IN";
  recognition.onstart = () => {
    listening = true;
    voiceBtn.textContent = "⏹ Stop Voice";
    voiceStatus.textContent = "Listening...";
  };
  recognition.onresult = (event) => {
    let finalText = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) finalText += event.results[i][0].transcript + " ";
    }
    if (finalText) answer.value += finalText;
  };
  recognition.onerror = () => {
    listening = false;
    voiceBtn.textContent = "🎙 Start Voice";
    voiceStatus.textContent = "Voice recognition error. You can continue by typing.";
  };
  recognition.onend = () => {
    if (listening) {
      try { recognition.start(); } catch(e) {}
    } else {
      voiceBtn.textContent = "🎙 Start Voice";
      voiceStatus.textContent = "Voice input stopped.";
    }
  };
  voiceBtn.addEventListener("click", () => {
    if (listening) {
      listening = false;
      recognition.stop();
    } else {
      listening = true;
      recognition.start();
    }
  });
} else {
  voiceBtn.disabled = true;
  voiceStatus.textContent = "Speech recognition is not supported by this browser. Use Chrome/Edge or type your answer.";
}
