# nyt-mcp

MCP server for the [New York Times APIs](https://developer.nytimes.com/apis).

## Tools

| Tool | NYT API | Description |
|---|---|---|
| `search_articles` | Article Search | Search by keyword with Lucene filters, date ranges, pagination |
| `get_top_stories` | Top Stories | Current top stories by section (home, world, science, …) |
| `get_most_popular` | Most Popular | Most emailed / shared / viewed articles (1, 7, or 30 days) |
| `get_newswire` | Times Newswire | Live stream of just-published articles |
| `get_bestsellers` | Books | NYT Best Sellers lists (hardcover-fiction, etc.) |
| `get_archive` | Archive | Article metadata for any month back to 1851 |
| `read_article` | *(scrape)* | Fetch and extract the full text of an NYT article URL |

## Setup

1. **Get an API key** at <https://developer.nytimes.com/get-started>.

2. Set the `API_KEY` environment variable (or create a `.env` file):

   ```sh
   export API_KEY=your-nyt-api-key
   ```

## Installation

No installation needed — just run with [`uvx`](https://docs.astral.sh/uv/guides/tools/):

```sh
# From PyPI (after publishing)
uvx nyt-mcp

# From GitHub
uvx --from git+https://github.com/joe5saia/nyt-mcp nyt-mcp
```

Or install permanently:

```sh
uv tool install nyt-mcp
# or from GitHub:
uv tool install git+https://github.com/joe5saia/nyt-mcp
```

## Running as an MCP Server

### Claude Code

```sh
claude mcp add nyt-mcp -- uvx nyt-mcp
```

### Amp

Add to your MCP config (e.g. `~/.config/amp/settings.json`):

```json
{
  "mcpServers": {
    "nyt-mcp": {
      "command": "uvx",
      "args": ["nyt-mcp"],
      "env": {
        "API_KEY": "your-nyt-api-key"
      }
    }
  }
}
```

### Standalone (stdio)

```sh
API_KEY=your-key uvx nyt-mcp
```

## Development

```sh
uv run ruff check src/ tests/   # lint
uv run ruff format src/ tests/  # format
uv run ty check src/             # type check
uv run pytest tests/ -v          # test
```
