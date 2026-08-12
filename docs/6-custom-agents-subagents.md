---
nav_order: 8
---

# Exercise 6: Orchestrating specialist agents

> [!NOTE]
> **Advanced extension · approximately 20 minutes.** Exercises 6 and 7 go beyond the core lab. They assume you've finished exercises 0–5 and are comfortable with agent mode, instruction files, and reading a diff.

In [Exercise 4][agent-mode-lesson] you used agent mode to make a change across the whole site. One agent, one long conversation, one very large context window. That works well — right up until it doesn't.

As a task grows, a single agent starts to struggle. It holds the Flask conventions, the Svelte conventions, the test conventions, and the feature requirements all at once. Details get dropped. The instructions you gave at the top of the conversation compete with the file it read forty steps later.

The answer is not a bigger model. It's **delegation**.

In this exercise you will learn how to:

- define **custom agents** with their own instructions, tools, and model.
- apply the **planner–worker pattern** to split a feature across specialists.
- use an **adversarial reviewer** to verify the result.
- choose models deliberately, because model choice is the main cost lever.

## Scenario

Tailspin Toys wants players to be able to **search games by title**. It's a small feature that touches everything:

- a Flask endpoint that accepts a search term
- a Svelte search box on the game listing page
- tests for both

Three areas, three sets of conventions. This is exactly the shape of task where orchestration beats a single long conversation.

## What is a custom agent?

A custom agent is a Markdown file that defines a persona: its instructions, the tools it may use, and the model it runs on. Switching to an agent applies that whole configuration at once, instead of you re-explaining it every time.

Agents live in **.github/agents/** and use the **.agent.md** extension. They are checked into the repository, so the whole team gets the same specialists.

The file has YAML frontmatter followed by the instructions:

| Field | Purpose |
| --- | --- |
| `name` | Display name in the agent picker |
| `description` | What the agent is for |
| `tools` | Which tools it may use. Omit to allow all |
| `agents` | Which agents it may call as **subagents** |
| `model` | Which model it runs on |
| `user-invocable` | Set `false` to hide it from the picker so only other agents call it |
| `handoffs` | Suggested next agents, shown as buttons after a response |

> [!NOTE]
> The `agents` field is what makes orchestration possible. An agent that lists other agents can delegate to them. For that to work, the `agent` tool must also appear in its `tools` list.

## Explore the agents in this repository

This repository already ships a set of specialists. Let's look at how they fit together.

1. Return to your codespace.
2. Open the **.github/agents/** folder. You should see five files:

   | Agent | Role | Model |
   | --- | --- | --- |
   | `feature-orchestrator` | Plans and delegates. Writes no feature code | large |
   | `api-worker` | Flask endpoints only | small |
   | `ui-worker` | Svelte and Astro only | small |
   | `test-worker` | unittest and Playwright only | small |
   | `reviewer` | Adversarial audit | large |

   > [!NOTE]
   > Each agent's `name` matches its filename. That matters because the orchestrator refers to the others by name in its `agents:` list — if the two disagree, delegation won't resolve.

3. Open **.github/agents/feature-orchestrator.agent.md** and read the frontmatter. Note that it lists the other four in `agents`, and includes `agent` in `tools`.
4. Note this line in its instructions:

   > You **plan, delegate, and synthesise**. You have no `edit` tool — you cannot write feature code.

   That restriction is enforced, not just requested: the orchestrator's `tools` list genuinely omits `edit`. It spends its context on *decisions*, not on the mechanics of writing a Svelte component.

5. Open **.github/agents/api-worker.agent.md**. Note three things:
   - it owns `server/` implementation and is told never to touch `client/` or the test files
   - it runs on a **small** model
   - it must return a short structured report, not file contents or raw logs

> [!IMPORTANT]
> Workers don't share your conversation, so anything you leave unstated gets invented independently. If the orchestrator doesn't fix the API contract up front — the exact route and the exact JSON keys — the backend and frontend workers will each guess, and the feature won't work. Watch for this when you run it.
>
> Note that they *do* share the same workspace. Directory ownership is an instruction the agents follow, not a filesystem boundary, so always confirm it in the diff.

> [!TIP]
> The `model` values are written as a prioritised list, so the first available option wins. If your organisation doesn't have these models enabled, open the model picker in Copilot Chat, note a name you do have, and edit the `model:` line. The pattern matters more than the specific model — one capable model for reasoning, one cheap one for bounded work.

## Why the planner–worker pattern works

Three things happen when you split work this way.

**Context stays clean.** Each worker holds only its own conventions. The UI worker never loads the Flask testing rules.

**Cost drops.** Writing a Flask route to an existing template is mechanical. It does not need a frontier model. Reasoning about *how to decompose the feature* does. Putting workers on a small model while the orchestrator stays on a large one is one of the main cost levers available to you — alongside how many workers you fan out to, and how much context each one carries.

**Failures are contained.** If the UI worker goes wrong, it went wrong inside the files it was told to own, and it reported back. Because workers share one workspace, that containment comes from the instructions rather than from a hard boundary — which is exactly why you still read the diff.

> [!NOTE]
> Keep delegation **one level deep**. Workers do not delegate to other workers. Recursive fan-out is difficult to reason about, hard to cost, and hard to stop.

## Run the orchestrator

Let's build the search feature.

1. Return to your codespace and make sure you're on a working branch:

   ```bash
   git checkout -b add-search
   ```

2. Open **Copilot Chat**.
3. Create a new chat session with the **New Chat** button so no earlier context leaks in.
4. Open the agent picker and select **feature-orchestrator**.
5. Send the following prompt. Note that it states the acceptance criteria explicitly — an underspecified request is the fastest way to get three workers building three different features:

   ```plaintext
   Add the ability to search games by title.

   Acceptance criteria:
   - GET /api/games accepts an optional `search` query parameter
   - Matching is case-insensitive substring match on the game title
   - A missing or empty `search` parameter returns all games unchanged
   - The response shape stays exactly as it is today
   - The game listing page gets a search box that filters results as the user types
   - Tests cover: a match, no matches, and an empty search term

   State the exact JSON contract before delegating to any worker.
   ```

6. **Read the plan before approving anything.** The orchestrator should decompose the work and restate the contract. Look specifically for:
   - the route, for example `GET /api/games?search=<term>`
   - the exact JSON keys the endpoint returns
   - which worker owns which files

7. If the contract is still vague, push back before it delegates:

   ```plaintext
   State the exact JSON keys the endpoint returns before delegating.
   ```

   This is the most valuable habit in this exercise. A vague contract is where multi-agent work fails.

8. Let the orchestrator delegate. Each worker runs as a nested call in the chat.

9. **Confirm the delegation actually happened.** Subagent calls may appear collapsed. Expand them and check that `api-worker`, `ui-worker`, and `test-worker` each ran. If the orchestrator did the work itself, say so and ask it to delegate:

   ```plaintext
   You edited files directly. Delegate the remaining work to the named workers.
   ```

10. Watch what comes **back** from each worker. It should be a short report — files touched, the endpoint shape, test counts. If a worker returns a wall of raw test output, that's a sign its instructions need tightening.

> [!TIP]
> Because these tools are probabilistic, your run will differ from your neighbour's. The orchestrator may delegate in a different order, or handle the tests itself. What matters is the *shape*: plan, delegate, synthesise, verify.

## Audit the result

A worker reporting success is not evidence of success. That's what the reviewer is for.

1. In Copilot Chat, switch to the **reviewer** agent — or use the **Adversarial review** handoff button if it appeared after the orchestrator's response.
2. Send:

   ```plaintext
   Audit the changes on this branch against your hunt list.
   ```

3. Open **.github/agents/reviewer.agent.md** while it works and read the hunt list.

Notice that it does not say "review the code carefully." It lists **specific failure modes**, including:

- *Does the frontend consume a field name the API does not actually return?*
- *A test asserting only status 200 without asserting the response body*
- *A test that would still pass if the feature were deleted*
- *Does the change assume the very thing it is supposed to establish?*

Generic review instructions produce generic review. Naming the exact ways this codebase breaks is what makes an automated reviewer useful.

Notice also the **Scope** section at the top. The reviewer diffs against `main` and ignores anything the branch didn't touch. Without that, it would report pre-existing quirks — this codebase already has one, where `GameList.svelte` reads flat `publisher_name` fields while `GameDetails.svelte` reads nested `publisher.name` — and you'd never get a clean verdict on your own work.

4. The reviewer returns a verdict — `pass` with what it verified, or `fail` with up to five findings, each citing a line in the diff.
5. If it returns `fail`, hand the findings back to the orchestrator and ask it to fix them. Then audit again.

> [!TIP]
> If the reviewer reports something that isn't in your diff, that's a scoping bug in the agent, not a defect in your feature. Tell it to re-read its Scope section and re-run.

> [!IMPORTANT]
> The reviewer is instructed to run the tests itself rather than trusting a worker's claim about them, and to treat "this step is routine" as a failure. An auditor that accepts optimistic summaries provides no assurance at all.

## Verify it actually works

Agents report. You verify.

1. Run the backend tests:

   ```bash
   ./scripts/run-server-tests.sh
   ```

2. Build the frontend and run the end-to-end tests:

   ```bash
   cd client
   npm run build
   npm run test:e2e
   cd ..
   ```

3. Start the app and try the search box yourself:

   ```bash
   ./scripts/start-app.sh
   ```

4. Commit your work once everything passes.

## Optional: write your own worker

The set of agents in this repository is a starting point, not a fixed list.

Create **.github/agents/docs-worker.agent.md** for a specialist that keeps `README.md` current when endpoints change. Give it a small model, restrict its tools to search and edit, and require a compact structured return. Then add `docs-worker` to the orchestrator's `agents` list so it can be delegated to.

Ask yourself what the *specific* failure modes are for documentation in this repo, and name them — the same way the reviewer names its own.

## Summary

You moved from driving one agent to operating several. In particular you:

- defined specialists in **.github/agents/**, each with its own instructions, tools, and model.
- used the **planner–worker pattern** to keep context clean and cost low, with the orchestrator reasoning and small models doing bounded work.
- saw why the **contract between workers** must be explicit, because workers cannot see each other.
- used an **adversarial reviewer** with a domain-specific hunt list rather than a request to "check carefully".

Every agent so far still waits for you to start it. Next we remove that requirement.

## Next step

[Next exercise: Continuous AI with agentic workflows](./7-continuous-ai.md)

## Resources

- [Custom agents in VS Code][custom-agents-vscode]
- [Subagents][subagents-docs]
- [Custom agents configuration reference][custom-agents-config]
- [Creating custom agents for Copilot cloud agent][custom-agents-cloud]

> [!NOTE]
> The `agents` and `handoffs` fields used here are VS Code features. Copilot's cloud coding agent reads custom agent files too, but ignores those two properties — so an orchestrator like this one delegates in your editor, not when you assign an issue to Copilot on GitHub.com.

---

[agent-mode-lesson]: ./4-copilot-agent-mode-vscode.md
[custom-agents-vscode]: https://code.visualstudio.com/docs/agent-customization/custom-agents
[custom-agents-config]: https://docs.github.com/en/copilot/reference/custom-agents-configuration
[subagents-docs]: https://code.visualstudio.com/docs/agents/run/subagents
[custom-agents-cloud]: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
