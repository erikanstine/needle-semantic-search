# Needle Coding Guidelines

These guidelines capture the coding style used throughout this repository.

## Python
- Target **Python 3.11** and follow PEP8 conventions.
- Use 4 spaces per indentation level.
- Name functions and variables using `snake_case`. Use `CamelCase` for classes.
- Provide type hints for all function arguments and return values.
- Each public function should include a short docstring describing parameters and returns.
- Use f-strings for string interpolation.
- Data models typically inherit from `pydantic.BaseModel`.

## JavaScript / React
- Components are written as **functional components** using hooks (e.g. `useState`, `useEffect`).
- Use arrow functions and keep JSX in `.jsx` files.
- Styling is handled with Tailwind CSS.
- ESLint is configured for linting; run `npm run lint` before committing frontend changes.

## Testing and Pre‑commit
- The repo uses a pre‑commit hook (`scripts/run_changed_tests.sh`) that runs
  `pytest` for directories with staged tests. Install the hook with `pre-commit install`.
- When modifying code in `backend` or `scraper`, run the relevant unit tests
  with `pytest` to ensure they pass.

## Commit Messages
- Write commit summaries in the **imperative present tense** (e.g. `Add unit tests`).
- Prefix with `feat:`, `fix:`, or `docs:` when helpful.
- When referencing issues in a commit message, refer to the GitHub issue number
  (e.g. `#123`).

