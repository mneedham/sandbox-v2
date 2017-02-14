export default {
  /**
   * Check if the given value is not empty.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  required(value) {
    return String(value) !== '';
  },


  /**
   * Check if the given value is not empty.
   *
   * @param {String} value
   * @param {RegExp} regexp
   * @return {Boolean} valid
   */

  pattern(value, regexp = /.*/) {
    return regexp.test(String(value));
  },


  /**
   * Check if the length of the given value is not less than the min length.
   *
   * @param {String} value
   * @param {Number} minLength
   * @return {Boolean} valid
   */

  minlength(value, minLength = 0) {
    return String(value).length >= minLength;
  },


  /**
   * Check if the length of the given value is not great than the max length.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  maxlength(value, maxLength = Infinity) {
    return String(value).length <= maxLength;
  },


  /**
   * Check if the given value is not less than the min value.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  min(value, minValue = 0) {
    return Number(value) >= minValue;
  },


  /**
   * Check if the length of the given value is not great than the max value.
   *
   * @param {String} value
   * @return {Boolean} valid
   */

  max(value, maxValue = Infinity) {
    return Number(value) <= maxValue;
  },
};
