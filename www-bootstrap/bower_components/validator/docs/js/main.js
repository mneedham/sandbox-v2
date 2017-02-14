window.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('form');
  var validator = new window.Validator(form, {
    namespace: 'x',
    trigger: 'input',
    success: function(e) {
      var input = e.target;

      input.classList.remove('form-control-warning');
      input.classList.add('form-control-success');
      input.parentNode.classList.remove('has-warning');
      input.parentNode.classList.add('has-success');
      input.nextElementSibling.textContent = '';
    },
    error: function(e) {
      var input = e.target;

      input.focus();
      input.classList.remove('form-control-success');
      input.classList.add('form-control-warning');
      input.parentNode.classList.remove('has-success');
      input.parentNode.classList.add('has-warning');
      input.nextElementSibling.textContent = e.detail.message;
    },
  });

  form.querySelector('button[type="submit"]').addEventListener('click', function (e) {
    if (validator.isInvalid()) {
      e.preventDefault();
    }
  }, false);
}, false);
