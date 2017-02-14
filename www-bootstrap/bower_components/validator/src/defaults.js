export default {
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
  validators: null,
};
