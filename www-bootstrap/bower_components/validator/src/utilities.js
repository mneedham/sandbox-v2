const REGEXP_SPACES = /\s+/;
const REGEXP_HYPHENATE = /([a-z\d])([A-Z])/g;
const slice = Array.prototype.slice;
const hasOwnProperty = Object.prototype.hasOwnProperty;

export function isObject(obj) {
  return typeof obj === 'object' && obj !== null;
}

export function isFunction(fn) {
  return typeof fn === 'function';
}

export function isPlainObject(obj) {
  if (!isObject(obj)) {
    return false;
  }

  try {
    const constructor = obj.constructor;
    const prototype = constructor.prototype;

    return constructor && prototype && hasOwnProperty.call(prototype, 'isPrototypeOf');
  } catch (e) {
    return false;
  }
}

export function toArray(obj, offset = 0) {
  if (Array.from) {
    return Array.from(obj).slice(offset);
  }

  return slice.call(obj, offset);
}

export function extend(obj, ...args) {
  const deep = obj === true;

  if (deep) {
    obj = args.shift();
  }

  if (isObject(obj) && args.length > 0) {
    args.forEach((arg) => {
      if (isObject(arg)) {
        Object.keys(arg).forEach((key) => {
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

export function hyphenate(str) {
  return str.replace(REGEXP_HYPHENATE, '$1-$2').toLowerCase();
}

export function removeListener(element, type, handler) {
  const types = type.trim().split(REGEXP_SPACES);

  if (types.length > 1) {
    types.forEach(t => removeListener(element, t, handler));
    return;
  }

  if (element.removeEventListener) {
    element.removeEventListener(type, handler, false);
  } else if (element.detachEvent) {
    element.detachEvent(`on${type}`, handler);
  }
}

export function addListener(element, type, handler, once) {
  const types = type.trim().split(REGEXP_SPACES);
  const originalHandler = handler;

  if (types.length > 1) {
    types.forEach(t => addListener(element, t, handler));
    return;
  }

  if (once) {
    handler = (...args) => {
      removeListener(element, type, handler);

      return originalHandler.apply(element, args);
    };
  }

  element.addEventListener(type, handler, false);
}

export function dispatchEvent(element, type, data) {
  let event;

  // Event and CustomEvent on IE9-11 are global objects, not constructors
  if (typeof Event === 'function' && typeof CustomEvent === 'function') {
    if (data === undefined) {
      event = new Event(type, {
        bubbles: true,
        cancelable: true,
      });
    } else {
      event = new CustomEvent(type, {
        detail: data,
        bubbles: true,
        cancelable: true,
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
