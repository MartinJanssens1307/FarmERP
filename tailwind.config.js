/** @type {import('tailwindcss').Config} */
module.exports = {
  // CRUCIAL: This content array must list all files that contain Tailwind utility classes.
  content: [
    // 1. Explicitly search for all HTML files starting within the ERP/ directory.
    //    This catches templates inside sub-folders like ERP/customers/templates/
    './ERP/**/*.html', 
    
    // 2. Explicitly search for all Python files starting within the ERP/ directory.
    //    This ensures any utility classes you use in views or forms are found.
    './ERP/**/*.py',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
