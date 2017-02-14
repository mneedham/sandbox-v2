const babel = require('rollup-plugin-babel');
const commonjs = require('rollup-plugin-commonjs');
const nodeResolve = require('rollup-plugin-node-resolve');
const pkg = require('./package');
const now = new Date();

export default {
  entry: 'src/index.js',
  targets: [
    {
      dest: 'dist/validator.js',
    },
    {
      dest: 'docs/js/validator.js',
    },
  ],
  format: 'umd',
  moduleName: 'Validator',
  plugins: [
    babel({
      exclude: '/node_modules/**',
    }),
    nodeResolve({ jsnext: true }),
    commonjs(),
  ],
  banner: `/*!
 * Validator v${pkg.version}
 * https://github.com/${pkg.repository}
 *
 * Copyright (c) ${now.getFullYear()} ${pkg.author}
 * Released under the ${pkg.license} license
 *
 * Date: ${now.toISOString()}
 */
`,
  sourceMap: true,
};
