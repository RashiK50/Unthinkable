# Migrations

`database/schema.sql` is the canonical schema. To bootstrap a new Supabase project:

1. Paste `schema.sql` into the Supabase SQL editor and run it, **or**
2. Use the CLI:

   ```bash
   supabase link --project-ref <project-ref>
   supabase migration new init         # creates supabase/migrations/<ts>_init.sql
   # copy schema.sql into that file, then:
   supabase db push
   ```

From then on, every schema change is a new ordered SQL file in this directory
(`0002_<description>.sql`, …) applied with `supabase db push`. Never edit an applied
migration — write a new one.
