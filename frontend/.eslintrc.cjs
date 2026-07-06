/* ESLint config for the Vue 3 + TypeScript frontend. */
module.exports = {
  root: true,
  env: { browser: true, es2023: true, node: true },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier',
  ],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  ignorePatterns: ['dist', 'node_modules', 'coverage', 'playwright-report'],
}
