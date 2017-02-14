import DEFAULTS from './defaults';
import MESSAGES from './messages';
import VALIDATORS from './validators';
import * as _ from './utilities';

// RegExps
const REGEXP_INPUTS = /^(input|textarea|select)$/i;
const REGEXP_TYPES = /^(checkbox|radio)$/i;
const REGEXP_NUMBER_RULES = /^m(in|ax)(length)?$/;

// Events
const EVENT_SUCCESS = 'success';
const EVENT_ERROR = 'error';
const OtherValidator = typeof window !== 'undefined' ? window.Validator : undefined;

export default class Validator {
  constructor(element, options) {
    const self = this;

    if (!_.isPlainObject(options)) {
      options = {};
    }

    self.element = element;
    self.options = _.extend(true, {}, DEFAULTS, options);
    self.validators = _.extend({}, VALIDATORS, options.validators);
    self.messages = _.extend({}, MESSAGES, options.messages);
    self.elements = [element];
    self.valid = true;
    self.invalid = false;
    self.init();
  }

  init() {
    const self = this;
    const element = self.element;
    const options = self.options;

    if (element.validator && _.isFunction(element.validator.destroy)) {
      element.validator.destroy();
    }

    element.validator = self;

    if (element.childElementCount && !REGEXP_INPUTS.test(element.tagName)) {
      const attrs = Object.keys(self.validators).map(rule => self.formatAttr(rule));

      self.elements = self.elements.concat(
        _.toArray(element.querySelectorAll(`[${attrs.join('],[')}]`)),
      );
    }

    if (options.trigger) {
      _.addListener(element, options.trigger, (self.onStart = self.start.bind(self)));
    }

    if (options.autoStart) {
      self.start();
    }
  }

  validate(elem) {
    const self = this;
    const options = self.options;
    const element = self.element;
    const rules = self.parseRules(elem);
    const keys = Object.keys(rules);
    const data = {
      rule: '',
      message: '',
    };
    let value = '';
    let valid = true;

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

    if (_.isFunction(options.filter)) {
      value = options.filter(value);
    }

    keys.forEach((rule) => {
      const ruleValue = rules[rule];

      data.rule = rule;

      if (valid) {
        const validator = self.validators[rule];

        valid = validator.call(self, value, ruleValue, elem);

        if (!valid) {
          let message = elem.getAttribute(self.formatAttr(rule, 'message')) ||
            elem.getAttribute(self.formatAttr('message')) ||
            self.messages[rule] || elem.title || '';

          if (Array.isArray(ruleValue)) {
            ruleValue.forEach((s) => {
              message = message.replace('%s', s);
            });
          } else {
            message = message.replace('%s', ruleValue);
          }

          data.message = message;
        }
      }
    });

    if (valid) {
      if (_.isFunction(options.success)) {
        _.addListener(element, EVENT_SUCCESS, options.success, true);
      }

      _.dispatchEvent(elem, EVENT_SUCCESS, data);
    } else {
      if (_.isFunction(options.error)) {
        _.addListener(element, EVENT_ERROR, options.error, true);
      }

      _.dispatchEvent(elem, EVENT_ERROR, data);

      if (options.stopOnError) {
        self.stop();
      }
    }

    self.valid = valid;
    self.invalid = !valid;
  }

  parseRules(element) {
    const self = this;
    const options = self.options;
    let rules = {};

    if (options.cache && element.parsedRules) {
      rules = element.parsedRules;
    } else {
      Object.keys(self.validators).forEach((rule) => {
        const name = self.formatAttr(rule);

        if (element.hasAttribute(name)) {
          let value = element.getAttribute(name);

          if (rule === 'pattern') {
            value = RegExp(value);
          } else if (REGEXP_NUMBER_RULES.test(rule)) {
            value = Number(value);
          }

          rules[rule] = value;
        }
      });

      rules = _.extend(rules, options.rules);

      if (options.cache) {
        element.parsedRules = rules;
      }
    }

    return rules;
  }

  formatAttr(...args) {
    const options = this.options;

    if (options.namespace) {
      args.unshift(options.namespace);
    }

    return _.hyphenate(args.join('-'));
  }

  /**
   * Start to validate the current element(s).
   *
   * @param {string} _event (internal) - the event object when used as event handler
   */
  start(_event) {
    const self = this;

    if (self.starting) {
      return;
    }

    self.starting = true;

    if (_event && _event.target) {
      self.validate(_event.target);
    } else {
      self.elements.forEach((elem) => {
        if (self.starting) {
          self.validate(elem);
        }
      });
    }

    self.starting = false;
  }

  // Stop to validate the left elements if any.
  stop() {
    this.starting = false;
  }

  /**
   * Check if the given element or the current element is valid.
   *
   * @param {element} element (optional) - the special element for validating
   */
  isValid(element) {
    const self = this;

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
  isInvalid(element) {
    const self = this;

    if (element) {
      self.validate(element);
    } else {
      self.start();
    }

    return self.invalid;
  }

  // Destroy the validaor instance.
  destroy() {
    const self = this;
    const element = self.element;
    const options = self.options;

    self.stop();

    if (options.trigger) {
      _.removeListener(element, options.trigger, self.onStart);
    }

    if (options.cache) {
      self.elements.forEach(elem => delete elem.parsedRules);
    }

    delete element.validator;
  }

  static setDefaults(options) {
    _.extend(true, DEFAULTS, options);
  }

  static setMessages(options) {
    _.extend(MESSAGES, options);
  }

  static setValidators(options) {
    _.extend(VALIDATORS, options);
  }

  static noConflict() {
    if (typeof window !== 'undefined') {
      window.Validator = OtherValidator;
    }

    return Validator;
  }
}
