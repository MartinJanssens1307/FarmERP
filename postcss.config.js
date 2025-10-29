/** @type {import('tailwindcss').Config} */
module.exports = {
  // PostCSS is the program that reads your source CSS.
  // We use the `plugins` object to tell it which transformations to apply.
  plugins: {
    // 1. tailwindcss: This plugin interprets all the @tailwind and @apply directives.
    //    This is the crucial step that solves the "unknown at rule" error.
    tailwindcss: {},
    
    // 2. autoprefixer: This automatically adds vendor prefixes (like -webkit-, -moz-) 
    //    to your CSS, which is good practice for cross-browser support.
    autoprefixer: {},
  },
};
