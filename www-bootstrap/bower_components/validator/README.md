# Validator

> JavaScript form validator.



## Table of contents

- [Main](#main)
- [Getting started](#getting-started)
- [Rules](#rules)
- [Options](#options)
- [Methods](#methods)
- [Events](#events)
- [Messages](#messages)
- [Validators](#validators)
- [No conflict](#no-conflict)
- [Browser support](#browser-support)
- [Versioning](#versioning)
- [License](#license)



## Main

```
dist/
├── validator.js     (18 KB)
└── validator.min.js ( 7 KB)
```



## Getting started


### Download

- [Download the latest release](https://github.com/xkeshi/validator/archive/master.zip).
- Clone the repository: `git clone https://github.com/xkeshi/validator.git`.


### Usage

Initialize with `Validator` constructor:

- Browser: `window.Validator`
- CommonJS: `var Validator = require('validator')`
- ES2015: `import Validator from 'validator'`

```html
<form>
  <input type="text" required>
  <button>Submit</button>
</form>
```

```js
const form = document.querySelector('form');
const validator = new Validator(form, {
  success(e) {
    console.log(e.detail.rule);
  },
  error(e) {
    console.log(e.detail.rule);
    console.log(e.detail.message);
  },
});

form.querySelector('button').addEventListener('click', (e) => {
  // Prevent submit when it is invalid
  if (validator.isInvalid()) {
    e.preventDefault();
  }
});
```


[⬆ back to top](#table-of-contents)



## Rules

Here is the list of built-in rules, you can also customize rule with the `validators` and `messages` options or the `Validator.setValidators` and `Validator.setMessages` static methods.

You can use rules in the element attributes (hyphen-case) or in the `rules` option (camelCase).


### required

- Type: `Boolean`

The enter value must be not empty.


```html
<input type="text" required>
```

Or

```js
new Validator(element, {
  rules: {
    required: true,
  },
});
```


### pattern

- Type: `RegExp`

The enter value must match the pattern.


```html
<input type="text" pattern="j(ava)?s(cript)?">
```

Or

```js
new Validator(element, {
  rules: {
    pattern: /j(ava)?s(cript)?/,
  },
});
```


### min

- Type: `Number`

The enter number must greater than or equal to this value.

```html
<input type="number" min="1">
```

Or

```js
new Validator(element, {
  rules: {
    min: 1,
  },
});
```


### max

- Type: `Number`

The enter number must less than or equal to this value.

Usage:

```html
<input type="number" max="100">
```

Or

```js
new Validator(element, {
  rules: {
    max: 100,
  },
});
```


### minlength

- Type: `Number`

The enter characters' length must greater than or equal to this value.

```html
<input type="text" minlength="1">
```

Or

```js
new Validator(element, {
  rules: {
    minlength: 1,
  },
});
```


### maxlength

- Type: `Number`

The enter characters' length must less than or equal to this value.

```html
<input type="text" maxlength="1000">
```

Or

```js
new Validator(element, {
  rules: {
    maxlength: 1000,
  },
});
```


[⬆ back to top](#table-of-contents)



## Options

### autoStart

- Type: `Boolean`
- Default: `false`

Define if start validation automatically after initialized.


### cache

- Type: `Boolean`
- Default: `true`

Define if cache the parsed attribute rules after the first validation.


### filter

- Type: `Function`
- Default: `null`

Filter the element value before validate it.

```js
new Validator(element, {
  filter(value) {
    return value.trim();
  }
});
```


### messages

- Type: `Object`
- Default: `null`

Customize error messages for rules.

```js
new Validator(element, {
  messages: {
    required: 'Empty value is not allowed!',
    customRule: 'Custom error message...',
  },
});
```


### namespace

- Type: `String`
- Default: `''`

Specify a namespace (or prefix) for each attribute rule.

```html
<input type="text" v-required>
```

```js
new Validator(document.querySelector('input'), {
  namespace: 'v',
});
```


### rules

- Type: `Object`
- Default: `null`

Add extra built-in or custom rules which are not defined in the element attributes.

> Available built-in rules: `required`, `pattern`, `min`, `max`, `minlength` and `maxlength`.

```js
new Validator(element, {
  rules: {
    required: true,
    maxlength: 1000,
    customRule: 'custom rule value',
  },
});
```


### stopOnError

- Type: `Boolean`
- Default: `false`

Define if stop to validate the other elements when the current element validate error.


### success

- Type: `Function`
- Default: `null`

A shortcut for the "success" event.


### error

- Type: `Function`
- Default: `null`

A shortcut for the "error" event.


### trigger

- Type: `String`
- Default: `''`

Specify event(s) for triggering validation automatically.

```js
new Validator(element, {
  trigger: 'change',
});
```


### validators

- Type: `Object`
- Default: `null`

Customize validators for rules.

```js
new Validator(element, {
  rules: {
    number: true,
  },
  messages: {
    number: 'Please enter a valid number (only digits).'
  },
  validators: {
    number(value) {
      return /^-?\d+$/.test(value);
    },
  },
});
```


[⬆ back to top](#table-of-contents)



## Methods


### start()

Start to validate the current element(s).


### stop()

Stop to validate the left elements if any.


### isValid([element])

- **element (optional)**
  - Type: `Element`
  - A special element for validating, should be a child element of the current element.

Check if the given element or the current element is valid.

```js
const input = document.createElement('input');
const validator = new Validator(input, {
  rules: {
    required: true,
  },
});

console.log(validator.isValid());
// > false

input.value = 'Hello, world!';

console.log(validator.isValid());
// > true
```


### isInvalid([element])

- **element (optional)**
  - Type: `Element`
  - A special element for validating, should be a child element of the current element.

Check if the given element or the current element is invalid.


### destroy()

Destroy the validaor instance.


[⬆ back to top](#table-of-contents)



## Events


### success

- **event.detail.rule**
  - Type: `String`
  - The name of the current validating rule.

This event fires when success to validate a element.

```js
const input = document.createElement('input');

input.addEventListener('success', function (e) {
  console.log(e.detail.rule);
  // > required
}, false);

input.value = 'Hello, world!';

new Validator(input, {
  autoStart: true,
  rules: {
    required: true,
  },
});
```


### error

- **event.detail.rule**
  - Type: `String`
  - The name of the current validating rule.

- **event.detail.message**
  - Type: `String`
  - The error message of the current validating rule.

This event fires when fail to validate a element.

```js
const input = document.createElement('input');

input.addEventListener('error', function (e) {
  console.log(e.detail.rule);
  // > required
  console.log(e.detail.message);
  // > This field is required.
}, false);

new Validator(input, {
  autoStart: true,
  rules: {
    required: true,
  },
});
```


[⬆ back to top](#table-of-contents)



## Messages

You can change the global default messages or add global custom messages with the `Validator.setMessages(options)` static method.

For example:

```js
// zh-CN
Validator.setMessages({
  required: '这是必填字段。',
  pattern: '请输入匹配的值。',
  min: '请输入一个不小于 %s 的数值。',
  max: '请输入一个不大于 %s 的数值。',
  minlength: '最少 %s 个字。',
  maxlength: '最多 %s 个字。',
});
```



## Validators

You can change the global default validators or add global custom validators with the `Validator.setValidators(options)` static method.

For example:

```html
<input type="password" id="new-password">
<input type="password" id="new-password-again" equal-to="#new-password">
```

```js
Validator.setValidators({
  equalTo(value, ruleValue) {
    return value === document.querySelector(ruleValue).value;
  },
});
```


[⬆ back to top](#table-of-contents)



## No conflict

If you have to use other validator with the same namespace, just call the `Validator.noConflict` static method to revert to it.

```html
<script src="other-validator.js"></script>
<script src="validator.js"></script>
<script>
  Validator.noConflict();
  // Code that uses other `Validator` can follow here.
</script>
```



## Browser support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)
- Edge (latest)
- Internet Explorer 9+



## Versioning

Maintained under the [Semantic Versioning guidelines](http://semver.org/).



## License

[MIT](http://opensource.org/licenses/MIT) © [xkeshi](http://xkeshi.com)

[⬆ back to top](#table-of-contents)
