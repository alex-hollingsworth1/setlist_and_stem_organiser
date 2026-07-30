// Reusable multiple-choice quiz widget for teaching lessons.
// Markup contract:
// <div class="quiz" data-quiz>
//   <p class="quiz-question">...</p>
//   <div class="quiz-options">
//     <button class="quiz-option" data-correct>Option text</button>
//     <button class="quiz-option">Option text</button>
//   </div>
//   <p class="quiz-feedback"></p>
// </div>
(function () {
  function initQuiz(quiz) {
    const options = quiz.querySelectorAll(".quiz-option");
    const feedback = quiz.querySelector(".quiz-feedback");

    options.forEach((opt) => {
      opt.addEventListener("click", () => {
        if (quiz.dataset.answered === "true") return;
        quiz.dataset.answered = "true";

        const correct = opt.hasAttribute("data-correct");
        options.forEach((o) => {
          o.disabled = true;
          if (o.hasAttribute("data-correct")) o.classList.add("quiz-correct");
        });
        if (!correct) opt.classList.add("quiz-wrong");

        if (feedback) {
          feedback.textContent = correct
            ? (quiz.dataset.rightMsg || "Correct.")
            : (quiz.dataset.wrongMsg || "Not quite — the right answer is highlighted above.");
          feedback.classList.add(correct ? "quiz-feedback-good" : "quiz-feedback-bad");
        }
      });
    });
  }

  document.querySelectorAll("[data-quiz]").forEach(initQuiz);
})();
