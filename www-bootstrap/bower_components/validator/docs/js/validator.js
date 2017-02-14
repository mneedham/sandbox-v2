/*!
 * Validator v0.1.0
 * https://github.com/xkeshi/validator
 *
 * Copyright (c) 2017 xkeshi
 * Released under the MIT license
 *
 * Date: 2017-02-07T03:02:09.435Z
 */

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global.Validator = factory());
}(this, (function () { 'use strict';

var DEFAULTS = {
  /**
   * Define if start validation automatically after initialized.
   *
   * - Type: Boolean
   */
  autoStart: false,

  /**
   * Define if cache the parsed attribute rules after the first validation.
   *
   * - Type: Boolean
   */
  cache: true,

  /**
   * Filter the element value before validate it.
   *
   * - Type: Function
   * - Example: function (value) { return value.trim() }
   */
  filter: null,

  /**
   * Customize error messages for rules.
   *
   * - Type: Object
   * - Example: { required: 'This field is required.' }
   */
  messages: null,

  /**
   * Specify a namespace (or prefix) for each attribute rule.
   *
   * - Type: String
   * - Example: 'data'
   */
  namespace: '',

  /**
   * Add extra built-in or custom rules rules which are not defined in the element attributes.
   *
   * - Type: Object
   * - Example: { minlength: 8, maxlength: 16 }
   */
  rules: null,

  /**
   * Define if stop to validate the other elements when the current element validate error.
   *
   * - Type: Boolean
   */
  stopOnError: true,

  /**
   * A shortcut for the "success" event.
   *
   * - Type: Function
   * - Example: function (e) { console.log(e.message) }
   */
  success: null,

  /**
   * A shortcut for the "success" event.
   *
   * - Type: Function
   * - Example: function (e) { console.log(e.message) }
   */
  error: null,

  /**
   * Specify an event for triggering validation automatically.
   *
   * - Type: String
   * - Example: 'change'
   */
  trigger: '',

  /**
   * Customize validators for rules.
   *
   * - Type: Object
   * - Example: { number(value) { return /^\d+$/.test(value) } }
   */
  validators: null
};

var MESSAGES = {
  required: 'This field is required.',
  pattern: 'Please enter a matched value.',
  min: 'Please enter a value greater than or equal to %d.',
  max: 'Please enter a value less than or equal to %d.',
  minlength: 'Please enter at least %d characters.',
  maxlength: 'Please enter no more than %d characters.'
};

var VALIDATORS = {
  /**
   * Check if the given value is not empty.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  required: function required(value) {
    return String(value) !== '';
  },


  /**
   * Check if the given value is not empty.
   *
   * @param {String} value
   * @param {RegExp} regexp
   * @return {Boolean} valid
   */

  pattern: function pattern(value) {
    var regexp = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : /.*/;

    return regexp.test(String(value));
  },


  /**
   * Check if the length of the given value is not less than the min length.
   *
   * @param {String} value
   * @param {Number} minLength
   * @return {Boolean} valid
   */

  minlength: function minlength(value) {
    var minLength = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;

    return String(value).length >= minLength;
  },


  /**
   * Check if the length of the given value is not great than the max length.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  maxlength: function maxlength(value) {
    var maxLength = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : Infinity;

    return String(value).length <= maxLength;
  },


  /**
   * Check if the given value is not less than the min value.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  min: function min(value) {
    var minValue = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;

    return Number(value) >= minValue;
  },


  /**
   * Check if the length of the given value is not great than the max value.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  max: function max(value) {
    var maxValue = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : Infinity;

    return Number(value) <= maxValue;
  }
};

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {
  return typeof obj;
} : function (obj) {
  return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj;
};





var classCallCheck = function (instance, Constructor) {
  if (!(instance instanceof Constructor)) {
    throw new TypeError("Cannot call a class as a function");
  }
};

var createClass = function () {
  function defineProperties(target, props) {
    for (var i = 0; i < props.length; i++) {
      var descriptor = props[i];
      descriptor.enumerable = descriptor.enumerable || false;
      descriptor.configurable = true;
      if ("value" in descriptor) descriptor.writable = true;
      Object.defineProperty(target, descriptor.key, descriptor);
    }
  }

  return function (Constructor, protoProps, staticProps) {
    if (protoProps) defineProperties(Constructor.prototype, protoProps);
    if (staticProps) defineProperties(Constructor, staticProps);
    return Constructor;
  };
}();







var get = function get(object, property, receiver) {
  if (object === null) object = Function.prototype;
  var desc = Object.getOwnPropertyDescriptor(object, property);

  if (desc === undefined) {
    var parent = Object.getPrototypeOf(object);

    if (parent === null) {
      return undefined;
    } else {
      return get(parent, property, receiver);
    }
  } else if ("value" in desc) {
    return desc.value;
  } else {
    var getter = desc.get;

    if (getter === undefined) {
      return undefined;
    }

    return getter.call(receiver);
  }
};

















var set = function set(object, property, value, receiver) {
  var desc = Object.getOwnPropertyDescriptor(object, property);

  if (desc === undefined) {
    var parent = Object.getPrototypeOf(object);

    if (parent !== null) {
      set(parent, property, value, receiver);
    }
  } else if ("value" in desc && desc.writable) {
    desc.value = value;
  } else {
    var setter = desc.set;

    if (setter !== undefined) {
      setter.call(receiver, value);
    }
  }

  return value;
};

var REGEXP_SPACES = /\s+/;
var REGEXP_HYPHENATE = /([a-z\d])([A-Z])/g;
var slice = Array.prototype.slice;
var hasOwnProperty = Object.prototype.hasOwnProperty;

function isObject(obj) {
  return (typeof obj === 'undefined' ? 'undefined' : _typeof(obj)) === 'object' && obj !== null;
}

function isFunction(fn) {
  return typeof fn === 'function';
}

function isPlainObject(obj) {
  if (!isObject(obj)) {
    return false;
  }

  try {
    var _constructor = obj.constructor;
    var prototype = _constructor.prototype;

    return _constructor && prototype && hasOwnProperty.call(prototype, 'isPrototypeOf');
  } catch (e) {
    return false;
  }
}

function toArray$$1(obj) {
  var offset = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 0;

  if (Array.from) {
    return Array.from(obj).slice(offset);
  }

  return slice.call(obj, offset);
}

function extend(obj) {
  var deep = obj === true;

  for (var _len = arguments.length, args = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
    args[_key - 1] = arguments[_key];
  }

  if (deep) {
    obj = args.shift();
  }

  if (isObject(obj) && args.length > 0) {
    args.forEach(function (arg) {
      if (isObject(arg)) {
        Object.keys(arg).forEach(function (key) {
          if (deep && isObject(obj[key])) {
            extend(true, obj[key], arg[key]);
          } else {
            obj[key] = arg[key];
          }
        });
      }
    });
  }

  return obj;
}

function hyphenate(str) {
  return str.replace(REGEXP_HYPHENATE, '$1-$2').toLowerCase();
}

function removeListener(element, type, handler) {
  var types = type.trim().split(REGEXP_SPACES);

  if (types.length > 1) {
    types.forEach(function (t) {
      return removeListener(element, t, handler);
    });
    return;
  }

  if (element.removeEventListener) {
    element.removeEventListener(type, handler, false);
  } else if (element.detachEvent) {
    element.detachEvent('on' + type, handler);
  }
}

function addListener(element, type, _handler, once) {
  var types = type.trim().split(REGEXP_SPACES);
  var originalHandler = _handler;

  if (types.length > 1) {
    types.forEach(function (t) {
      return addListener(element, t, _handler);
    });
    return;
  }

  if (once) {
    _handler = function handler() {
      for (var _len2 = arguments.length, args = Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
        args[_key2] = arguments[_key2];
      }

      removeListener(element, type, _handler);

      return originalHandler.apply(element, args);
    };
  }

  element.addEventListener(type, _handler, false);
}

function dispatchEvent(element, type, data) {
  var event = void 0;

  // Event and CustomEvent on IE9-11 are global objects, not constructors
  if (typeof Event === 'function' && typeof CustomEvent === 'function') {
    if (data === undefined) {
      event = new Event(type, {
        bubbles: true,
        cancelable: true
      });
    } else {
      event = new CustomEvent(type, {
        detail: data,
        bubbles: true,
        cancelable: true
      });
    }

    // IE9-11
  } else if (data === undefined) {
    event = document.createEvent('Event');
    event.initEvent(type, true, true);
  } else {
    event = document.createEvent('CustomEvent');
    event.initCustomEvent(type, true, true, data);
  }

  // IE9+
  return element.dispatchEvent(event);
}

// RegExps
var REGEXP_INPUTS = /^(input|textarea|select)$/i;
var REGEXP_TYPES = /^(checkbox|radio)$/i;
var REGEXP_NUMBER_RULES = /^m(in|ax)(length)?$/;

// Events
var EVENT_SUCCESS = 'success';
var EVENT_ERROR = 'error';
var OtherValidator = typeof window !== 'undefined' ? window.Validator : undefined;

var Validator = function () {
  function Validator(element, options) {
    classCallCheck(this, Validator);

    var self = this;

    if (!isPlainObject(options)) {
      options = {};
    }

    self.element = element;
    self.options = extend(true, {}, DEFAULTS, options);
    self.validators = extend({}, VALIDATORS, options.validators);
    self.messages = extend({}, MESSAGES, options.messages);
    self.elements = [element];
    self.valid = true;
    self.invalid = false;
    self.init();
  }

  createClass(Validator, [{
    key: 'init',
    value: function init() {
      var self = this;
      var element = self.element;
      var options = self.options;

      if (element.validator && isFunction(element.validator.destroy)) {
        element.validator.destroy();
      }

      element.validator = self;

      if (element.childElementCount && !REGEXP_INPUTS.test(element.tagName)) {
        var attrs = Object.keys(self.validators).map(function (rule) {
          return self.formatAttr(rule);
        });

        self.elements = self.elements.concat(toArray$$1(element.querySelectorAll('[' + attrs.join('],[') + ']')));
      }

      if (options.trigger) {
        addListener(element, options.trigger, self.onStart = self.start.bind(self));
      }

      if (options.autoStart) {
        self.start();
      }
    }
  }, {
    key: 'validate',
    value: function validate(elem) {
      var self = this;
      var options = self.options;
      var element = self.element;
      var rules = self.parseRules(elem);
      var keys = Object.keys(rules);
      var data = {
        rule: '',
        message: ''
      };
      var value = '';
      var valid = true;

      if (self.elements.indexOf(elem) < 0) {
        throw new Error('The given element is invalid');
      }

      if (!keys.length) {
        return;
      }

      if (REGEXP_INPUTS.test(elem.tagName)) {
        value = elem.value;

        if (REGEXP_TYPES.test(elem.type) && !elem.checked) {
          value = '';
        }
      } else {
        value = elem.textContent;
      }

      if (isFunction(options.filter)) {
        value = options.filter(value);
      }

      keys.forEach(function (rule) {
        var ruleValue = rules[rule];

        data.rule = rule;

        if (valid) {
          var validator = self.validators[rule];

          valid = validator.call(self, value, ruleValue, elem);

          if (!valid) {
            (function () {
              var message = elem.getAttribute(self.formatAttr(rule, 'message')) || elem.getAttribute(self.formatAttr('message')) || self.messages[rule] || elem.title || '';

              if (Array.isArray(ruleValue)) {
                ruleValue.forEach(function (s) {
                  message = message.replace('%s', s);
                });
              } else {
                message = message.replace('%s', ruleValue);
              }

              data.message = message;
            })();
          }
        }
      });

      if (valid) {
        if (isFunction(options.success)) {
          addListener(element, EVENT_SUCCESS, options.success, true);
        }

        dispatchEvent(elem, EVENT_SUCCESS, data);
      } else {
        if (isFunction(options.error)) {
          addListener(element, EVENT_ERROR, options.error, true);
        }

        dispatchEvent(elem, EVENT_ERROR, data);

        if (options.stopOnError) {
          self.stop();
        }
      }

      self.valid = valid;
      self.invalid = !valid;
    }
  }, {
    key: 'parseRules',
    value: function parseRules(element) {
      var self = this;
      var options = self.options;
      var rules = {};

      if (options.cache && element.parsedRules) {
        rules = element.parsedRules;
      } else {
        Object.keys(self.validators).forEach(function (rule) {
          var name = self.formatAttr(rule);

          if (element.hasAttribute(name)) {
            var value = element.getAttribute(name);

            if (rule === 'pattern') {
              value = RegExp(value);
            } else if (REGEXP_NUMBER_RULES.test(rule)) {
              value = Number(value);
            }

            rules[rule] = value;
          }
        });

        rules = extend(rules, options.rules);

        if (options.cache) {
          element.parsedRules = rules;
        }
      }

      return rules;
    }
  }, {
    key: 'formatAttr',
    value: function formatAttr() {
      var options = this.options;

      for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) {
        args[_key] = arguments[_key];
      }

      if (options.namespace) {
        args.unshift(options.namespace);
      }

      return hyphenate(args.join('-'));
    }

    /**
     * Start to validate the current element(s).
     *
     * @param {string} _event (internal) - the event object when used as event handler
     */

  }, {
    key: 'start',
    value: function start(_event) {
      var self = this;

      if (self.starting) {
        return;
      }

      self.starting = true;

      if (_event && _event.target) {
        self.validate(_event.target);
      } else {
        self.elements.forEach(function (elem) {
          if (self.starting) {
            self.validate(elem);
          }
        });
      }

      self.starting = false;
    }

    // Stop to validate the left elements if any.

  }, {
    key: 'stop',
    value: function stop() {
      this.starting = false;
    }

    /**
     * Check if the given element or the current element is valid.
     *
     * @param {element} element (optional) - the special element for validating
     */

  }, {
    key: 'isValid',
    value: function isValid(element) {
      var self = this;

      if (element) {
        self.validate(element);
      } else {
        self.start();
      }

      return self.valid;
    }

    /**
     * Check if the given element or the current element is invalid.
     *
     * @param {element} element (optional) - the special element for validating
     */

  }, {
    key: 'isInvalid',
    value: function isInvalid(element) {
      var self = this;

      if (element) {
        self.validate(element);
      } else {
        self.start();
      }

      return self.invalid;
    }

    // Destroy the validaor instance.

  }, {
    key: 'destroy',
    value: function destroy() {
      var self = this;
      var element = self.element;
      var options = self.options;

      self.stop();

      if (options.trigger) {
        removeListener(element, options.trigger, self.onStart);
      }

      if (options.cache) {
        self.elements.forEach(function (elem) {
          return delete elem.parsedRules;
        });
      }

      delete element.validator;
    }
  }], [{
    key: 'setDefaults',
    value: function setDefaults(options) {
      extend(true, DEFAULTS, options);
    }
  }, {
    key: 'setMessages',
    value: function setMessages(options) {
      extend(MESSAGES, options);
    }
  }, {
    key: 'setValidators',
    value: function setValidators(options) {
      extend(VALIDATORS, options);
    }
  }, {
    key: 'noConflict',
    value: function noConflict() {
      if (typeof window !== 'undefined') {
        window.Validator = OtherValidator;
      }

      return Validator;
    }
  }]);
  return Validator;
}();

return Validator;

})));
//# sourceMappingURL=validator.js.map
