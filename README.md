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

## API

The Flask backend serves a JSON API from `server/routes/`. Endpoints are registered as blueprints in `server/app.py`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/games` | List all games |
| `GET` | `/api/games/<id>` | Get a single game by ID. Returns `404` with `{"error": "Game not found"}` if it does not exist |

A game is returned in the following shape:

```json
{
  "id": 1,
  "title": "DevOps Dominion",
  "description": "In DevOps Dominion, strategic planning meets advanced deployment tactics...",
  "publisher": { "id": 1, "name": "CodeForge Studios" },
  "category": { "id": 1, "name": "Strategy" },
  "starRating": 3.0
}
```

`publisher` and `category` are `null` when the game has no related record. Note that `starRating` is camelCase in the API response while the underlying column is `star_rating`.

> [!NOTE]
> Keep this section current when you add or change an endpoint — see the `docs-worker` agent in [.github/agents](./.github/agents).

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
