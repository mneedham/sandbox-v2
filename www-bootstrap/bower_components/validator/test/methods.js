var assert = chai.assert;

describe('Methods', function () {
  describe('start', function () {
    var validator = new Validator(document.createElement('input'), {
      rules: {
        required: true,
      },
    });

    it('should be valid before start', function () {
      assert.isTrue(validator.valid);
    });

    it('should not be valid after start', function () {
      validator.start();
      assert.isNotTrue(validator.valid);
    });
  });

  describe('stop', function () {
    var form = document.createElement('form');
    var input = document.createElement('input');
    var input2 = document.createElement('input');
    var count = 0;

    input.setAttribute('required', '');
    input2.setAttribute('required', '');

    form.appendChild(input);
    form.appendChild(input2);

    new Validator(form, {
      autoStart: true,
      error: function () {
        if (!count) {
          this.validator.stop();
        }

        count++;

        it('should stop to validate the second input element', function () {
          assert.equal(1, count);
        });
      },
    });
  });

  describe('isValid', function () {
    var form = document.createElement('form');
    var input = document.createElement('input');
    var input2 = document.createElement('input');

    input.setAttribute('required', '');
    input2.setAttribute('required', '');

    input.value = 'foo';
    input2.value = 'bar';

    form.appendChild(input);
    form.appendChild(input2);

    var validator = new Validator(form);

    it('should be valid', function () {
      assert.isTrue(validator.isValid());
    });

    it('should be partial valid', function () {
      input.value = '';
      assert.isNotTrue(validator.isValid(input));
      assert.isTrue(validator.isValid(input2));
    });
  });

  describe('isInvalid', function () {
    var form = document.createElement('form');
    var input = document.createElement('input');
    var input2 = document.createElement('input');

    input.setAttribute('required', '');
    input2.setAttribute('required', '');

    form.appendChild(input);
    form.appendChild(input2);

    var validator = new Validator(form);

    it('should be invalid', function () {
      assert.isTrue(validator.isInvalid());
    });

    it('should be partial invalid', function () {
      input.value = 'foo';
      assert.isNotTrue(validator.isInvalid(input));
      assert.isTrue(validator.isInvalid(input2));
    });
  });

  describe('destroy', function () {
    var input = document.createElement('input');
    var validator = new Validator(input, {
      rules: {
        required: true,
      },
      trigger: 'change',
      error: function () {
        it('should not trigger this validation after destroyed', function () {
          assert.isTrue(false);
        });
      },
    });

    it('should be valid before start', function () {
      assert.isObject(input.validator);
    });

    it('should not be valid after start', function () {
      var event = document.createEvent('Event');

      validator.destroy();
      assert.isNotObject(input.validator);
      event.initEvent('change', true, true);
      input.dispatchEvent(event);
    });
  });
});
