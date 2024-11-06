// navbarFixed
window.onscroll = function() {
  const header = document.querySelector('header')
  const fixedNav = header.offsetTop;

  if (window.scrollY > fixedNav) {
    header.classList.add('navbar-fixed');
  } else {
    header.classList.remove('navbar-fixed');
  }
}

// hamburger
const hamburger = document.querySelector('#hamburger')
const navMenu = document.querySelector('#nav-menu')

hamburger.addEventListener('click', function() {
  hamburger.classList.toggle('hamburger-active');
  navMenu.classList.toggle('nav-hidden');
});

// close button
const closeBtns = document.querySelectorAll('.close-btn');

closeBtns.forEach(function(button) {
  button.addEventListener('click', function() {
    button.parentElement.style.display = 'none';
  });
});

// const radioButtons = document.querySelectorAll('input[type="radio"]');

// radioButtons.forEach(radioButton => {
//   radioButton.addEventListener('change', () => {
//     const questionBlock = radioButton.closest('.question-block');
//     questionBlock.classList.remove('error');
//   });
// });

// function validateForm() {
//   let isValid = true;
//   radioButtons.forEach(radioButton => {
//     const questionBlock = radioButton.closest('.question-block');
//     if (!radioButton.checked) {
//       questionBlock.classList.add('error');
//       isValid = false;
//     }
//   });
//   return isValid;
// }

// const form = document.querySelector('form')
// form.addEventListener('submit', (event) => {
//   if (!validateForm()) {
//     event.preventDefault();
//   }
// });

function selectOption(questionIndex, selectedChoiceIndex) {
  // Get all choices for the current question
  const options = document.querySelectorAll(`[name="question_${questionIndex}"]`);

  // Remove the 'selected' class from all labels for this question
  options.forEach(option => {
      const label = document.querySelector(`label[for="${option.id}"]`);
      label.classList.remove('selected');
  });

  // Add the 'selected' class to the label of the selected option
  const selectedLabel = document.querySelector(`label[for="option_${questionIndex}_${selectedChoiceIndex}"]`);
  selectedLabel.classList.add('selected');
}