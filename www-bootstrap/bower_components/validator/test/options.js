var assert = chai.assert;

describe('Options', function () {
  describe('autoStart', function () {
    var input = document.createElement('input');
    var validator = new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
    });

    it('should start validation automatically after initialized', function () {
      assert.isNotTrue(validator.valid);
    });
  });

  describe('cache', function () {
    var input = document.createElement('input');
    var validator = new Validator(input, {
      cache: false,
    });

    validator.start();

    it('should cache the parsed attribute rules after the first validation', function () {
      assert.isNotObject(input.parsedRules);
    });
  });

  describe('filter', function () {
    var input = document.createElement('input');
    var validator = new Validator(input, {
      rules: {
        pattern: /^\w+$/,
      },
      filter: function (value) {
        return value.replace('@', '');
      },
    });

    it('should be valid with the given value after applied filter', function () {
      input.value = '@foo';
      assert.isTrue(validator.isValid());
    });
  });

  describe('messages', function () {
    var message = 'Please enter something...';
    var input = document.createElement('input');

    new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
      messages: {
        required: message,
      },
      error: function (e) {
        it('should match the given error message', function () {
          assert.deepEqual(message, e.detail.message);
        });
      },
    });
  });

  describe('namespace', function () {
    var input = document.createElement('input');

    input.setAttribute('x-required', '');

    new Validator(input, {
      autoStart: true,
      namespace: 'x',
      error: function (e) {
        it('should match the attribute rule with the given namespace', function () {
          assert.deepEqual('required', e.detail.rule);
        });
      },
    });
  });

  describe('rules', function () {
    var input = document.createElement('input');

    new Validator(input, {
      autoStart: true,
      rules: {
        minlength: 1,
      },
      error: function (e) {
        it('should match the given rule', function () {
          assert.deepEqual('minlength', e.detail.rule);
        });
      },
    });
  });

  describe('stopOnError', function () {
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
      stopOnError: false,
      error: function () {
        count++;

        it('should validate twice (' + count + '/2)', function () {
          assert.isTrue(true);
        });
      },
    });
  });

  describe('success', function () {
    var input = document.createElement('input');

    input.value = 'foo';

    new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
      success: function (e) {
        it('should trigger the "success" event', function () {
          assert.equal('success', e.type);
        });

        it('should have a rule in the "event.detail" object', function () {
          assert.isString(e.detail.rule);
        });

        it('should match the given rule', function () {
          assert.equal('required', e.detail.rule);
        });

        it('should have a message in the "event.detail" object', function () {
          assert.isString(e.detail.message);
        });
      },
    });
  });

  describe('error', function () {
    var input = document.createElement('input');

    new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
      error: function (e) {
        it('should trigger the "error" event', function () {
          assert.equal('error', e.type);
        });

        it('should have a rule in the "event.detail" object', function () {
          assert.isString(e.detail.rule);
        });

        it('should match the given rule', function () {
          assert.equal('required', e.detail.rule);
        });

        it('should have a message in the "event.detail" object', function () {
          assert.isString(e.detail.message);
        });
      },
    });
  });

  describe('trigger', function () {
    var input = document.createElement('input');
    var event = document.createEvent('Event');

    new Validator(input, {
      rules: {
        required: true,
      },
      trigger: 'change',
      success: function (e) {
        it('should validate automatically when change', function () {
          assert.isTrue(true);
        });
      },
    });

    input.value = 'foo';
    event.initEvent('change', true, true);
    input.dispatchEvent(event);
  });

  describe('validators', function () {
    var message = 'Please enter a valid number (only digits).';
    var input = document.createElement('input');

    input.setAttribute('digit-only', '');

    new Validator(input, {
      autoStart: true,
      messages: {
        digitOnly: message,
      },
      validators: {
        digitOnly: function (value) {
          return /^\d+$/.test(value);
        },
      },
      error: function (e) {
        it('should match the custom attribute rule', function () {
          assert.deepEqual('digitOnly', e.detail.rule);
        });

        it('should match the given error message', function () {
          assert.deepEqual(message, e.detail.message);
        });
      },
    });
  });
});
