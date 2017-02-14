(function (factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as anonymous module.
    define('validator.zh-CN', ['validator'], factory);
  } else if (typeof exports === 'object') {
    // Node / CommonJS
    factory(require('validator'));
  } else {
    // Browser globals.
    factory(Validator);
  }
})(function (Validator) {

  'use strict';

  Validator.setMessages({
    required: '这是必填字段。',
    pattern: '请输入匹配的值。',
    min: '请输入一个不小于 %s 的数值。',
    max: '请输入一个不大于 %s 的数值。',
    minlength: '最少 %s 个字。',
    maxlength: '最多 %s 个字。',
  });
});
