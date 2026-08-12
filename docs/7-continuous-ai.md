---
nav_order: 9
---

# Exercise 7: Continuous AI with agentic workflows

> [!NOTE]
> **Advanced extension · approximately 25 minutes.** This exercise involves CLI installation, repository settings, and GitHub Actions permissions. If you're running this as a timed lab, allow extra time — the setup is where it's slowest.

Every agent you've used so far has waited for you. You opened chat, you assigned the issue, you selected the agent. Useful — but it means the work only happens when someone remembers to ask.

Some work shouldn't wait. When an issue is filed at 2am, someone still has to decide what area it touches, how big it is, and whether it's a duplicate of something filed last week. That work is repetitive, it's judgement-based, and it's exactly what an agent is good at.

**GitHub Agentic Workflows** (`gh-aw`) lets you write that automation in Markdown and run it in GitHub Actions — with the security controls that running an unsupervised agent demands.

In this exercise you will learn how to:

- write an agentic workflow as Markdown with YAML frontmatter.
- define **inline subagents** inside a workflow file.
- apply the security model: read-only agents, safe outputs, and least privilege.
- compile, run, and debug the workflow.

## Scenario

Tailspin Toys' backlog is growing. Issues arrive untriaged, and duplicates slip through. You'll ship a workflow that triages every new issue automatically — classifying it by area, estimating size, checking for duplicates, and applying labels.

## How agentic workflows work

An agentic workflow is a Markdown file in **.github/workflows/**. The YAML frontmatter configures triggers, permissions, tools, and outputs. The Markdown body is the prompt.

The `gh aw compile` command turns that source into a standard GitHub Actions workflow — a **.lock.yml** file — which is what Actions actually runs.

```text
issue-triage.md  ──  gh aw compile  ──▶  issue-triage.lock.yml  ──▶  GitHub Actions
   (you write)                              (generated)
```

> [!IMPORTANT]
> The `.lock.yml` is generated output. Never hand-edit it — your changes will be overwritten on the next compile. Edit the `.md` and recompile.

Agentic workflows complement conventional CI; they don't replace it. Use normal GitHub Actions for builds, tests, and deployments. Reach for an agentic workflow when the task needs **interpretation** — triage, review, investigating a CI failure, summarising activity.

## Install the CLI

1. Return to your codespace and open a terminal.
2. Install the extension:

   ```bash
   gh extension install github/gh-aw
   ```

3. Verify it's available:

   ```bash
   gh aw version
   ```

> [!NOTE]
> If the install fails with a **SAML enforcement** error, your token needs authorising for the `github` organization. Open the URL in the error message and authorise, then retry. Alternatively install without a token:
>
> ```bash
> curl -sL https://raw.githubusercontent.com/github/gh-aw/main/install-gh-aw.sh | bash
> ```

## Explore the workflow

This repository already contains a triage workflow. Let's read it before running it.

1. Open **.github/workflows/issue-triage.md**.
2. Look at the frontmatter first:

   ```yaml
   on:
     issues:
       types: [opened, reopened]
   permissions:
     contents: read
     issues: read
     copilot-requests: write
   strict: true
   max-ai-credits: 200
   network:
     allowed: [defaults, github]
   tools:
     github:
       mode: gh-proxy
       toolsets: [issues]
     cli-proxy: true
   safe-outputs:
     add-comment:
     add-labels:
       allowed:
         - area:backend
         # ...
   ```

3. Note what the permissions **do not** include. The agent has `issues: read` — not `issues: write`. It cannot label anything directly.

   So how does it apply labels? Through `safe-outputs`. The agent *requests* a label; a separate job validates that request and applies it with its own scoped permission. The agent never holds write access.

   `copilot-requests: write` is the exception, and it isn't a repository-data permission — it lets the run spend Copilot inference on the Actions token.

4. Note the other three controls while you're here:
   - `toolsets: [issues]` rather than `[default]`. The default set includes pull-request tools this workflow never uses, and asking for them would require a broader permission.
   - `network.allowed` restricts outbound traffic to GitHub and the engine's own endpoints.
   - `max-ai-credits: 200` caps what a single run can spend.

5. Note that `add-labels` has an `allowed` list. Even through the safe-output path, the agent can only apply labels from that list. It cannot invent `priority:drop-everything`.

## Inline subagents

Scroll to the bottom of the file. You'll find three blocks like this:

```markdown
## agent: `area-classifier`
---
description: Decides which area of the codebase an issue affects
model: small
---
You are given an issue title and body. Decide which single area it primarily affects:
...
```

This is the same planner–worker pattern from [Exercise 6][orchestration-lesson], expressed inside a workflow. The main prompt orchestrates; these three do bounded classification work on a **small** model.

Points worth noting:

- The heading form is `## agent: ` followed by the name in backticks. Names are lowercase.
- A block ends at the next `##` heading, so subagents go at the **bottom** of the file.
- Only `description` and `model` are supported in a subagent's frontmatter. Anything else is stripped at runtime. Subagents inherit the parent's engine, tools, and network config.
- `model: small` maps to whichever cheap, fast model the engine provides. Using the alias rather than a specific model ID means the workflow keeps working as models are updated.

Read the `duplicate-finder` block and note this instruction:

> When uncertain, return `false` — a missed duplicate costs less than a wrongly closed issue.

Tell an agent which way to fail. Left to itself it will not know which error is cheaper.

## Create the labels

The workflow can only apply labels that already exist in the repository.

1. In your terminal, create them:

   ```bash
   for label in "area:backend" "area:frontend" "area:tests" "area:docs" \
                "size:s" "size:m" "size:l" \
                "priority:high" "priority:normal" "priority:low" \
                "needs-detail"; do
     gh label create "$label" --force
   done
   ```

2. Confirm they exist:

   ```bash
   gh label list
   ```

> [!IMPORTANT]
> If a label in the `allowed` list doesn't exist in the repository, the workflow will run but fail to apply it. The `allowed` list and your actual labels have to agree.

## Configure authentication

The workflow uses the Copilot engine, which needs permission to spend inference. There are two paths, and they are **mutually exclusive** — pick one.

### Path A — organisation billing (default in this workflow)

The `copilot-requests: write` permission already in the frontmatter uses the per-run Actions token, with billing through your organisation's Copilot plan. Nothing else to do.

This requires an **organisation** Copilot subscription with centralised billing. If you're working in a personal repository, use Path B.

### Path B — personal access token

1. Open **.github/workflows/issue-triage.md** and **delete** the `copilot-requests: write` line from `permissions:`.

   > [!IMPORTANT]
   > This step is not optional. While `copilot-requests: write` is present, `COPILOT_GITHUB_TOKEN` is **ignored for inference** — so leaving both configured means your token is never used and the run still fails.

2. [Create a fine-grained personal access token][copilot-pat-link]. The link pre-fills the name and the required permission. Before generating, confirm:
   - **Resource owner** is your **user account**, not an organisation
   - **Permissions → Account permissions → Copilot Requests** is set to **Read**

3. Add it as a repository secret:

   ```bash
   gh aw secrets set COPILOT_GITHUB_TOKEN --value "<your-token>"
   ```

> [!NOTE]
> The token must be a fine-grained PAT. gh-aw rejects OAuth tokens (those beginning `gho_`) at startup with a clear error, so if you paste the wrong kind of token you'll find out immediately rather than mid-run.

## Preflight

A few things are worth confirming before you compile, because each one produces a confusing failure later.

```bash
gh auth status                    # authenticated, with workflow scope
git remote -v                     # pointing at your fork
git branch --show-current         # note this — it matters below
```

Also check **Settings → Actions → General** and confirm Actions are enabled for the repository.

## Compile and merge to the default branch

1. Compile the workflow:

   ```bash
   gh aw compile issue-triage
   ```

2. Confirm the lock file was generated:

   ```bash
   ls .github/workflows/issue-triage.lock.yml
   ```

> [!IMPORTANT]
> A workflow only runs on `issues` events if it exists on the repository's **default branch**. If you leave these files on a feature branch, creating an issue will do nothing at all — no run, no error, no clue. This is the single most common way this exercise goes wrong.

3. Commit both files:

   ```bash
   git add .github/workflows/issue-triage.md .github/workflows/issue-triage.lock.yml .gitattributes
   git commit -m "Add agentic issue triage workflow"
   ```

4. Get them onto `main`. If you're on a feature branch from the previous exercise, push and merge it:

   ```bash
   git push -u origin $(git branch --show-current)
   gh pr create --fill
   gh pr merge --squash --delete-branch
   ```

   If you were already working on `main`, just push:

   ```bash
   git push
   ```

5. Confirm the workflow is registered on the default branch:

   ```bash
   gh workflow list
   ```

   **Issue Triage** should appear. If it doesn't, the lock file hasn't reached `main` yet — recheck step 4 before continuing.

> [!NOTE]
> Both files are committed. The `.md` is the source you maintain; the `.lock.yml` is what Actions runs. The `.gitattributes` entry marks the lock file as generated so it collapses in diffs.

## Watch it run

1. Create a test issue:

   ```bash
   gh issue create --title "Game titles overflow their card on mobile" \
     --body "On a narrow viewport, long game titles run outside the card border on the listing page. Expected: the title wraps or truncates."
   ```

2. Open the **Actions** tab of your repository. You should see an **Issue Triage** run start.
3. Open the run and watch the steps. You'll see the agent execute, then the safe-output jobs apply the results.
4. Return to the issue. Within a couple of minutes it should carry labels and a short comment explaining the priority call.

For the issue above, a sensible triage is `area:frontend` with a small size. Priority is a judgement call, so `high` and `normal` are both defensible — what matters is that the comment gives a *reason*, not that it picked a particular value.

5. Now try one deliberately vague:

   ```bash
   gh issue create --title "Search is broken" --body "doesn't work"
   ```

   This should attract `needs-detail` and a comment asking **specific** questions. The prompt explicitly forbids generic requests for more information.

> [!TIP]
> Runs take a couple of minutes. Use `gh aw status` to see workflow state, or `gh run watch` to stream the latest run.

> [!NOTE]
> These are probabilistic tools. Your labels may differ from your neighbour's, and a rerun on the same issue may not produce identical output. Judge the result by whether the reasoning holds up, not by whether it matched a predicted label.

## When things go wrong

Work through the mechanical causes before you start editing the prompt.

| Symptom | Most likely cause |
| --- | --- |
| No run appears at all | Lock file isn't on the default branch. Check `gh workflow list` |
| Run fails immediately on auth | Both `copilot-requests: write` and `COPILOT_GITHUB_TOKEN` configured, or no org Copilot billing |
| Run succeeds but no labels applied | Label doesn't exist in the repository, or isn't in the `allowed` list |
| Compile succeeds but behaviour is stale | Frontmatter changed without recompiling. Rerun `gh aw compile` |
| Workflow doesn't appear in Actions | Actions disabled, or the push didn't include the `.lock.yml` |

Then use the CLI:

```bash
gh aw logs issue-triage   # recent runs and their output
gh aw audit <run-id>      # detailed breakdown of a single run
```

The audit output shows the execution transcript, the tool calls the agent made, and an analysis of the prompt — which is usually where the answer is. Once you've ruled out the mechanical causes above, a wrong label is normally a prompt problem rather than a frontmatter one.

## Change its behaviour

Reading a workflow isn't the same as owning one. Let's change how it triages.

1. Open **.github/workflows/issue-triage.md** and find the `size-estimator` subagent block at the bottom.
2. Add a fourth size to its instructions, and to the `allowed` list in the frontmatter:

   ```yaml
   safe-outputs:
     add-labels:
       allowed:
         # ...existing labels...
         - size:xl
   ```

   In the subagent block, add a line describing when `xl` applies — for example, work that changes a data model *and* spans both backend and frontend.

3. Create the new label:

   ```bash
   gh label create "size:xl" --force
   ```

4. Recompile. You changed the frontmatter, so this is required:

   ```bash
   gh aw compile issue-triage
   ```

   > [!IMPORTANT]
   > Editing only the Markdown body doesn't need a recompile — the body is read at run time. Editing the **frontmatter** does, because that's what becomes the `.lock.yml`. Forgetting this is why a workflow sometimes appears to ignore your changes.

5. Commit, push to `main`, and file an issue that should qualify:

   ```bash
   gh issue create --title "Add user accounts so backers can track pledges" \
     --body "Backers need to sign in and see everything they've pledged to. Needs a user model, auth on the API, and a profile page."
   ```

6. Check whether it earns `size:xl`. If it doesn't, read the run with `gh aw audit` and sharpen the wording in the subagent block — the classifier only knows what you told it.

## The security model

This is the part worth internalising, because you're running an agent with no human watching.

**The agent job is sandboxed and holds no repository write permission.** It works in its own checkout, but it cannot push, label, or comment directly. Every change that reaches your repository goes through a validated safe-output job with its own narrow permission.

**Outputs are allow-listed.** `add-labels.allowed` bounds what the agent can do even when it's behaving unexpectedly.

**Least privilege in `permissions:` and `toolsets:`.** Grant only what the workflow needs. This one reads issues and repository contents, and takes the `issues` toolset rather than the default set — which would have pulled in pull-request tools and the broader permission to match.

**Untrusted input stays out of shell steps.** An issue body is attacker-controlled — anyone can open an issue. Never interpolate `${{ github.event.issue.body }}` into a `run:` script. Pass it through `env:` instead:

```yaml
# Unsafe — the issue title is executed as shell
- run: echo "${{ github.event.issue.title }}"

# Safe — passed as data
- env:
    TITLE: ${{ github.event.issue.title }}
  run: echo "$TITLE"
```

**Cost has a ceiling.** `max-ai-credits` caps spend per run — this workflow sets `200`. There is a default budget if you omit it, but setting it deliberately means you've thought about what a single run is worth, which matters most for workflows on high-volume triggers.

**`strict: true`** enables the stronger validation set. Use it for anything running unsupervised.

> [!IMPORTANT]
> Treat an agentic workflow like any other privileged automation. Review the permissions, the network access, and the generated lock file before merging — the same care you'd apply to a workflow with deploy credentials.

## Optional: build your own

Some ideas that fit this repository:

- **PR test-coverage comment** — on `pull_request`, report which changed files gained or lost coverage, using `add-comment`.
- **CI failure triage** — on `workflow_run` for the test workflow, read the failed job logs and open an issue with a probable cause. Search for an existing open incident first so reruns don't spam duplicates.
- **Weekly backlog digest** — on a schedule, summarise what moved and what's stalled.

Two rules to carry across: give the agent an explicit `noop` condition so it can decide to do nothing, and route every write through `safe-outputs`.

You can also ask Copilot to build it. Point it at the guidance:

```plaintext
Read https://raw.githubusercontent.com/github/gh-aw/main/create.md and create an agentic workflow that comments on pull requests with a test coverage summary.
```

## Summary

Congratulations — you've reached the end of the lab, and your repository now works when you don't.

In this exercise you:

- wrote automation as **Markdown with frontmatter**, compiled to a real GitHub Actions workflow.
- used **inline subagents** to run cheap bounded classification under an orchestrating prompt.
- applied the security model: a **read-only agent**, **allow-listed safe outputs**, least-privilege permissions, and untrusted input kept out of shell steps.
- debugged a run with `gh aw logs` and `gh aw audit`.

Across the whole lab you've moved through three layers. You gave agents **context** with instruction files and `AGENTS.md`. You **delegated** to specialists with custom agents and subagents. And now you've handed work to agents that run **continuously**, without you.

The constant across all three is that the fundamentals didn't change. You still review what's generated, you still run the tests, and you still apply least privilege. The agents got more capable; the engineering judgement is still yours.

## Resources

- [GitHub Agentic Workflows documentation][gh-aw-docs]
- [Quick start][gh-aw-quickstart]
- [Security architecture][gh-aw-security]
- [Inline sub-agents][gh-aw-subagents]
- [Multi-agent research workflows][gh-aw-research]
- [Workflow examples by task][gh-aw-examples]

---

[orchestration-lesson]: ./6-custom-agents-subagents.md
[copilot-pat-link]: https://github.com/settings/personal-access-tokens/new?name=COPILOT_GITHUB_TOKEN&description=GitHub+Agentic+Workflows+-+Copilot+engine+authentication&user_copilot_requests=read
[gh-aw-docs]: https://github.github.com/gh-aw/
[gh-aw-quickstart]: https://github.github.com/gh-aw/setup/quick-start/
[gh-aw-security]: https://github.github.com/gh-aw/introduction/architecture/
[gh-aw-subagents]: https://github.com/github/gh-aw/blob/main/.github/aw/subagents.md
[gh-aw-research]: https://github.com/github/gh-aw/blob/main/.github/aw/multi-agent-research.md
[gh-aw-examples]: https://github.github.com/gh-aw/examples/
