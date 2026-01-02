# supabase_infra

This repo tracks the Supabase infrastructure SQL used for the project. Migrations now follow the Supabase CLI layout so they can be applied and audited in chronological order.

## Structure

```
supabase/
  migrations/
    20240101000000_init_schema.sql
    20240102000000_signup_trigger.sql
    20240103000000_admin_init.sql
    20240104000000_soft_deleted.sql
```

## Working with migrations

- Add new changes as timestamped files under `supabase/migrations/` using the `YYYYMMDDHHMMSS_<name>.sql` convention. This keeps the history ordered for Supabase.
- Run migrations with the Supabase CLI (e.g. `supabase db push` or `supabase db reset`) so the files above stay in sync with your database state.
- Keep each migration focused on a single change to simplify future reviews and rollbacks.
- If you do not have the Supabase CLI installed locally, use the helper script to run the official CLI image against the Compose network:

  ```bash
  # Pull the remote schema into supabase/migrations
  SUPABASE_ACCESS_TOKEN=... ./utils/supabase-cli.sh db pull

  # Push local migrations to the remote project
  SUPABASE_ACCESS_TOKEN=... ./utils/supabase-cli.sh db push
  ```

  The script attaches the CLI container to the `supabase_default` network by default and mounts the repository root at `/workspace` so it can read the local `supabase/` folder. Override the image or network with `SUPABASE_CLI_IMAGE` or `SUPABASE_NETWORK` if needed.

## Generating `supabase/config.toml`

- A starter example lives at `supabase/config.example.toml`. Update the `ref` and database password to match your environment if you prefer to copy it manually.
- To generate `supabase/config.toml` from the values in your `.env`, run:

  ```bash
  cp .env.example .env # or edit your existing .env
  ./utils/generate-config.sh             # writes supabase/config.toml
  ./utils/generate-config.sh path/to/.env # alternate env file
  ```

  The script reads database credentials, Kong port, and schema settings from the env file and produces a ready-to-use Supabase CLI configuration in `supabase/config.toml`.
