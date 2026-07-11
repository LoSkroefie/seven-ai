# Read-only GitHub access

Seven provides a bounded GitHub REST reader rather than pretending generic HTML scraping is repository analysis. Tools:

- `github_status` reports public/environment-token mode without returning the token;
- `github_repo` returns selected repository metadata;
- `github_contents` lists up to 200 entries or decodes bounded UTF-8 file content;
- `github_commits` returns one page of up to 100 commits;
- `github_issues` returns one page of up to 100 issues and pull requests with an explicit `kind`.

Public repositories require no credential. For private repositories or higher rate limits, set `GITHUB_TOKEN` in Seven's process environment. Seven reads it only when creating request headers; it does not write it to SQLite, configuration, logs, output, command arguments, or status. Use a fine-grained read-only token restricted to required repositories.

Every response includes the actual HTTP status and available `X-RateLimit-*` values. Authentication failure, authorization failure, not-found, rate limiting, invalid JSON, and network errors are returned as errors rather than empty repository data.

## Bounds and behavior

- The API base is fixed to `https://api.github.com`; callers cannot turn this tool into arbitrary HTTP/SSRF.
- Owner/repository slugs and repository-relative paths are validated. Parent traversal and absolute content paths are rejected.
- File output is capped between 100 and 200,000 characters and reports original character count/truncation.
- Only a single caller-bounded page is read. Seven does not hide extra API traffic behind unbounded recursive tree traversal.
- No line-count estimate is invented from byte size. Metadata values such as stars, language, issue count and size remain GitHub's values, not Seven's analysis.
- This surface does not create, modify, comment on, merge, star, clone, or delete anything. Existing coding-agent and `gh` workflows are separate L4 capabilities.

## Legacy disposition

The v3 reader returned `None` for materially different failures, recursively multiplied requests, labeled an arbitrary bytes/40 estimate as lines, and advertised comparative “full analysis” that its raw metadata did not prove. The useful REST reads were recovered; the marketing and fabricated estimate were rejected.
