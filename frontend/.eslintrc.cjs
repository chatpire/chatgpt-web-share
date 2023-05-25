module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  overrides: [],
  parser: 'vue-eslint-parser',
  extends: [
    'plugin:vue/base',
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:vue/essential',
    'plugin:@typescript-eslint/recommended',
    'plugin:import/recommended',
    'plugin:import/typescript',
    // "plugin:prettier/recommended",
    // "eslint-config-prettier",
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    parser: '@typescript-eslint/parser',
  },
  plugins: ['vue', '@typescript-eslint', 'import', 'simple-import-sort'],
  rules: {
    indent: ['warn', 2],
    'linebreak-style': ['error', 'unix'],
    quotes: ['warn', 'single'],
    semi: ['warn', 'always'],
    'vue/no-v-model-argument': ['off'],
    'vue/no-multiple-template-root': ['off'],
    'vue/multi-word-component-names': ['off'],
    '@typescript-eslint/no-explicit-any': ['off'],
    'simple-import-sort/imports': 'error',
    'simple-import-sort/exports': 'error',
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
      },
    ],
    "vue/max-attributes-per-line": ["error", {
      "singleline": {
        "max": 5
      },      
      "multiline": {
        "max": 1
      }
    }],
    "@typescript-eslint/no-non-null-assertion": ["off"],
    "import/no-named-as-default": ["off"]
  },
  settings: {
    'import/parsers': {
      '@typescript-eslint/parser': ['.ts', '.tsx'],
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true, // always try to resolve types under `<root>@types` directory even it doesn't contain any source code, like `@types/unist`
        project: ['tsconfig.json', 'tsconfig.node.json'],
      },
    },
  },
};
