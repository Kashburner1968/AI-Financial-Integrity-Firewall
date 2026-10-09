-- Apply once in Supabase SQL Editor. Read-only public telemetry, secret-only ingestion.
create table if not exists public.market_bars (
  symbol text not null, bar_time_utc timestamptz not null,
  open double precision, high double precision, low double precision,
  close double precision not null, volume double precision,
  source text not null, retrieved_utc timestamptz not null,
  primary key (symbol, bar_time_utc, source)
);
create index if not exists market_bars_time_idx on public.market_bars(bar_time_utc desc);
create table if not exists public.market_alerts (
  event_id text primary key, symbol text not null, bar_time_utc timestamptz not null,
  signal text not null, change_pct double precision,
  volume_ratio double precision, classification text not null,
  source text not null, retrieved_utc timestamptz not null
);
create index if not exists market_alerts_time_idx on public.market_alerts(bar_time_utc desc);
create table if not exists public.collection_runs (
  run_id text primary key, collected_utc timestamptz not null,
  bar_count integer not null, alert_count integer not null,
  status text not null, details jsonb not null default '{}'::jsonb
);
alter table public.market_bars enable row level security;
alter table public.market_alerts enable row level security;
alter table public.collection_runs enable row level security;
-- Only read permissions to public anonymous clients; never permit anonymous writes.
grant usage on schema public to anon;
grant select on public.market_bars,public.market_alerts,public.collection_runs to anon;
create policy "Public market bars read" on public.market_bars for select to anon using (true);
create policy "Public candidate alerts read" on public.market_alerts for select to anon using (true);
create policy "Public collection status read" on public.collection_runs for select to anon using (true);
-- Supabase secret API key (server side only) can write via service role privileges.
