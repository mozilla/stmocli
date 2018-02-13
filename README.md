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

**Implemented**!

`stmocli init`

Creates an empty `.stmocli.conf` file in the current directory.

## `track` an existing query

**Implemented**!

`stmocli track <redash_id> <filename>`

This command downloads the SQL statements associated with the given redash_id
and saves it in a file with the given name.
The necessary metadata is then added to the config file.

For example, calling
`stmocli track 49741 poc.sql`
would create a file in the current directory called `poc.sql`,
with the following content:

```sql
SELECT
    normalized_channel
FROM longitudinal
LIMIT 10
```

Assuming this is the first query being tracked, `.stmocli.conf` would look like this:

```json
{
  "poc.sql": {
    "query_id": 49741,
    "data_source_id": <data source>,
    "name": <query name>,
    "description": <query description>,
    "schedule": <schedule interval in seconds>,
    "options": <query options>
  }
}
```

## `pull` a linked query

**Not Yet Implemented**

`stmocli pull [<id>]`

Pulls the current SQL statements and metadata from re:dash for the given query.
If no query id is specified, pull data for all queries.
This will **overwrite local data**.
Be sure to use version control.

`<id>` must be a key in the dictionary stored in `.stmocli.conf`

## `push` a query

**Implemented!**

`stmocli push <filename>`

Pushes the current SQL statements and metadata to re:dash for the given query file.

`<filename>` must be a key in the dictionary stored in `.stmocli.conf`

# Roadmap

## Push-only and Automatic deploys

This tool assumes no edits happen in re:dash, which is a bad assumption.
Edits made in re:dash get overwritten if you `push` without `pull`ing first.

Ideally, there would be a Mocli-user in re:dash that owns all Mocli queries.
This would ensure all queries controlled by Mocli cannot be edited in re:dash.
We could then remove the `pull` command, and this tool becomes `push`-only.

From there we can have a scheduled job (hourly?) that pushes master to STMO.
Maybe we add a git-hook that pushes master on commit. Seamless.

## `preview` a query

Users will need to upload queries to a temporary re:dash query to preview the results.
This should be easy to do with a `preview` command.
It may also be useful to execute queries against presto directly.

## `start` a new query

Currently, St. Mocli can only track existing queries.
We should add a `start` command that will make it easy to start queries from the cli.
