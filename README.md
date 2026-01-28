# Reddit Post Summary Engine

A small, flexible engine to fetch Reddit posts/threads and generate concise summaries. This project is useful for quickly understanding the contents of a post or thread without reading every comment — ideal for research, monitoring, or content curation workflows.

> NOTE: This README is a template. Adjust configuration keys, commands, and dependency names to match the actual implementation of this repository.

## Features

- Fetch posts, comments, or entire threads from Reddit
- Generate short and long-form summaries
- Configurable summarization backend (e.g., OpenAI, other LLMs, or local models)
- CLI and programmatic usage
- Optional Docker container for consistent environment
- Tests and basic CI-ready commands

## Quickstart

Prerequisites
- Python 3.10+ (or the project's supported version)
- pip
- A Reddit API application (client ID & secret) if you use PRAW or direct Reddit calls
- API key for your chosen LLM provider (if used)

Install
```bash
# create virtual env (recommended)
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# Windows (PowerShell): .venv\Scripts\Activate.ps1

pip install -r requirements.txt
# or, if the repo is packaged:
pip install -e .
```

Environment variables
- REDDIT_CLIENT_ID — Reddit app client id
- REDDIT_CLIENT_SECRET — Reddit app client secret
- REDDIT_USER_AGENT — user agent for Reddit API
- OPENAI_API_KEY — API key for OpenAI (if using OpenAI)
- SUMMARY_MODEL — (optional) model name or config for local LLM backend

Example (Linux/macOS)
```bash
export REDDIT_CLIENT_ID=xxx
export REDDIT_CLIENT_SECRET=yyy
export REDDIT_USER_AGENT="reddit-summary-bot:v1.0 (by /u/youruser)"
export OPENAI_API_KEY=sk-...
```

## Usage

CLI
```bash
# summarize a single post by URL
python -m reddit_summary_engine.cli summarize --url "https://www.reddit.com/r/.../comments/POST_ID" --length short

# summarize top N comments for a thread
python -m reddit_summary_engine.cli summarize-thread --url "..." --top-comments 20 --length long
```

Programmatic
```python
from reddit_summary_engine import Summarizer, RedditClient

rc = RedditClient(client_id="...", client_secret="...", user_agent="...")
post = rc.fetch_post("https://www.reddit.com/r/.../comments/POST_ID")
summ = Summarizer(model="openai-gpt-4").summarize(post, style="concise")
print(summ)
```

Configuration options
- `length` or `style` — e.g., `short`, `concise`, `detailed`
- `max_comments` — limit how many comments are included in the summary
- `include_media` — whether to attempt to summarize linked content/media (if supported)
- `cache` — enable caching to avoid repeated API calls

## Docker

Build
```bash
docker build -t reddit-summary-engine:latest .
```

Run
```bash
docker run --rm -e REDDIT_CLIENT_ID -e REDDIT_CLIENT_SECRET -e REDDIT_USER_AGENT -e OPENAI_API_KEY reddit-summary-engine:latest \
  python -m reddit_summary_engine.cli summarize --url "https://www.reddit.com/..."
```

## Tests

Run tests with pytest (adjust command if the repo uses a different test runner)
```bash
pytest
```

## Examples

- Summarize a "AskReddit" thread to extract the most-common suggestions
- Summarize a news post + top comments for quick briefing
- Produce daily digests by summarizing multiple posts from a subreddit

(Consider adding a `examples/` directory with runnable example scripts and sample outputs.)

## Contributing

Contributions are welcome! A suggested workflow:
1. Fork the repo
2. Create a branch: `git checkout -b feat/add-feature`
3. Make your changes and add tests
4. Run tests locally
5. Open a pull request describing changes and rationale

Please follow these guidelines:
- Keep changes small and focused
- Add or update tests for new behavior
- Follow existing code style and linters (if any)

## Roadmap / Ideas

- Add thread-topic extraction
- Provide multi-lingual summarization support
- Add webhook / API server for on-demand summarization
- Add integrated caching and rate-limiting for API backends

## License

This repository should include a license. If you want a permissive license, add an `MIT` license file. Replace this section with the repo's actual license if already provided.

## Acknowledgements

- Reddit API
- Any LLM provider used (OpenAI, etc.)
- Contributors and maintainers

## Contact

Maintainer: sapritanand (update with preferred contact method)

---

If you'd like I can:
- adapt the README to the exact repo implementation (I can scan files and match commands/env names),
- or push this README.md to `main` or create a new branch and open a PR. Tell me which you prefer.
