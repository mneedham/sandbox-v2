var assert = chai.assert;

describe('Events', function () {
  describe('success', function () {
    var input = document.createElement('input');

    input.addEventListener('success', function (e) {
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
    }, false);

    input.value = 'foo';

    new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
    });
  });

  describe('error', function () {
    var input = document.createElement('input');

    input.addEventListener('error', function (e) {
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
    }, false);

    new Validator(input, {
      autoStart: true,
      rules: {
        required: true,
      },
    });
  });
});
