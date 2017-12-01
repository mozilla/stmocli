# Introduction

St. Mocli allows you to keep SQL queries in github repositories
and easily deploy to
[re:dash](https://redash.io/).

[Re:dash](https://redash.io/)
is great for quickly creating and sharing simple analyses.
However, sometimes we want to **treat our queries like code**.
In re:dash, it's difficult to get review, track revisions, or collaborate on queries.

# Workflow

St. Mocli is currently [vaporware](https://en.wikipedia.org/wiki/Vaporware),
so this workflow is going to change.

## `init` a directory

`stmocli init` creates an empty `.stmocli.conf` file in the current directory.

## `track` an existing query

`stmocli track <redash_id> <filename>`
downloads the sql

`.stmocli.conf` contains a dictionary of configuration files
St. Mocli's atomic unit is a query.
`.stmocli.conf` contains a dictionary of lists

```json
{
  "poc_query": {
    "redash_id": 49741,
    "query_title": "St. Mocli POC",
    "query_filename": "poc.sql"
  }
}
```


## `start` a new query



## `pull` a linked query



## `push` a query



# Roadmap

This tool assumes no edits happen in re:dash, which is a bad assumption.
Edits made in re:dash get overwritten if you `push` without `pull`ing first.

Ideally, there would be a Mocli-user in re:dash that owns all Mocli queries.
This would ensure all queries controlled by Mocli cannot be edited in re:dash.
We could then remove the `pull` command, and this tool becomes `push`-only.

From there we can have a scheduled job (hourly?) that pushes master to STMO.
Maybe we add a git-hook that pushes master on commit. Seamless.

Users will need to upload queries to a temporary re:dash query to preview the results.
This should be easy to do with a `preview` command.
It may also be useful to execute queries against presto directly.

