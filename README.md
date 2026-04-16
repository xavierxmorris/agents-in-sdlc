# Tailspin Toys

[![Deploy Jekyll site to Pages](https://github.com/se-copilot-workshops/agents-in-sdlc/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/se-copilot-workshops/agents-in-sdlc/actions/workflows/deploy-pages.yml)

This repository contains the project for a 1 hour guided workshop to explore GitHub Copilot Agent Mode and related features in Visual Studio Code. The project is a website for a fictional game crowd-funding company, with a [Flask](https://flask.palletsprojects.com/en/stable/) backend using [SQLAlchemy](https://www.sqlalchemy.org/) and [Astro](https://astro.build/) frontend using [Svelte](https://svelte.dev/) for dynamic pages.

To begin the workshop, start at [docs/README.md](./docs/README.md)

Or, if just want to run the app...

## Launch the site

A script file has been created to launch the site. You can run it by:

```bash
./scripts/start-app.sh
```

Then navigate to the [website](http://localhost:4321) to see the site!

## API Endpoints

### Games

- `GET /api/games` — Returns all games. Supports optional query parameters:
  - `publisher_id` — Filter games by publisher ID
  - `category_id` — Filter games by category ID
  - Both filters can be combined (AND logic)
- `GET /api/games/<id>` — Returns a single game by ID

### Publishers

- `GET /api/publishers` — Returns all publishers (lightweight `{id, name}` list)

### Categories

- `GET /api/categories` — Returns all categories (lightweight `{id, name}` list)

## Documentation

The complete workshop documentation is automatically published at GitHub Pages and available at:
**https://connect.copilot-workshops.com**

The documentation is automatically deployed from the `docs/` directory when changes are pushed to main.

## License 

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) for the full terms.

## Maintainers 

You can find the list of maintainers in [CODEOWNERS](./.github/CODEOWNERS).

## Support

This project is provided as-is, and may be updated over time. If you have questions, please open an issue.
