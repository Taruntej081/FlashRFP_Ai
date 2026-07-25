/* FlashRFP.ai - Supabase Database Schema - Run in SQL Editor */

/* Enable UUID extension */
create extension if not exists "uuid-ossp";

/* USERS TABLE */
create table if not exists public.users (
    id                   uuid default uuid_generate_v4() primary key,
    username             text unique not null,
    name                 text not null,
    email                text unique not null,
    company              text,
    plan                 text not null default 'trial'
                             check (plan in ('trial','starter','professional','enterprise')),
    status               text not null default 'trial'
                             check (status in ('active','trial','suspended','cancelled')),
    is_admin             boolean not null default false,
    created_at           date not null default current_date,
    trial_expires_at     date,
    subscription_id      text,
    responses_this_month integer not null default 0,
    documents_count      integer not null default 0,
    batches_this_month   integer not null default 0,
    last_active          date default current_date,
    monthly_amount       integer not null default 0,
    updated_at           timestamptz default now()
);

/* Auto-update updated_at on any row change */
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_users_updated_at
    before update on public.users
    for each row execute function update_updated_at();

/* SUBSCRIPTIONS TABLE */
create table if not exists public.subscriptions (
    id                  uuid default uuid_generate_v4() primary key,
    subscription_id     text unique not null,
    username            text not null references public.users(username) on delete cascade,
    plan                text not null,
    status              text not null default 'active'
                            check (status in ('created','authenticated','active','pending','halted','cancelled','completed','expired')),
    amount              integer not null,
    currency            text not null default 'INR',
    billing_cycle       text not null default 'monthly',
    start_date          date,
    next_billing_date   date,
    total_paid          integer not null default 0,
    invoices            integer not null default 0,
    razorpay_payment_id text,
    created_at          timestamptz default now(),
    updated_at          timestamptz default now()
);

create trigger trg_subs_updated_at
    before update on public.subscriptions
    for each row execute function update_updated_at();

/* USAGE LOGS TABLE */
create table if not exists public.usage_logs (
    id         uuid default uuid_generate_v4() primary key,
    username   text not null,
    action     text not null
                   check (action in ('response_generated','batch_processed','document_uploaded','document_deleted')),
    metadata   jsonb default '{}'::jsonb,
    created_at timestamptz default now()
);

create index if not exists idx_usage_logs_username on public.usage_logs(username);
create index if not exists idx_usage_logs_created  on public.usage_logs(created_at desc);

/* AUDIT LOGS TABLE */
create table if not exists public.audit_logs (
    id             uuid default uuid_generate_v4() primary key,
    username       text not null,
    question_asked text,
    source_docs    jsonb default '[]'::jsonb,
    llm_response   text,
    provider       text,
    model          text,
    latency_ms     integer,
    created_at     timestamptz default now()
);

create index if not exists idx_audit_logs_username on public.audit_logs(username);
create index if not exists idx_audit_logs_created  on public.audit_logs(created_at desc);

/* SYSTEM METRICS TABLE */
create table if not exists public.system_metrics (
    id                  uuid default uuid_generate_v4() primary key,
    metric_date         date unique not null default current_date,
    new_signups         integer default 0,
    responses_generated integer default 0,
    api_errors          integer default 0,
    p50_latency_ms      integer default 0,
    p95_latency_ms      integer default 0,
    llm_cost_usd        numeric(8,4) default 0
);

/* SEED DEFAULT ADMIN USER */
insert into public.users (username, name, email, company, plan, status, is_admin, monthly_amount)
values ('admin', 'Administrator', 'admin@flashrfp.ai', 'FlashRFP Internal', 'enterprise', 'active', true, 0)
on conflict (username) do nothing;

/* ROW LEVEL SECURITY */
alter table public.users          enable row level security;
alter table public.subscriptions  enable row level security;
alter table public.usage_logs     enable row level security;
alter table public.audit_logs     enable row level security;
alter table public.system_metrics enable row level security;

/* Only the service_role key (used by backend) can read/write all tables */
create policy "service_role_all_users"
    on public.users for all
    to service_role using (true) with check (true);

create policy "service_role_all_subs"
    on public.subscriptions for all
    to service_role using (true) with check (true);

create policy "service_role_all_usage"
    on public.usage_logs for all
    to service_role using (true) with check (true);

create policy "service_role_all_audit"
    on public.audit_logs for all
    to service_role using (true) with check (true);

create policy "service_role_all_metrics"
    on public.system_metrics for all
    to service_role using (true) with check (true);

/* Atomic increment function for response counter (call via RPC) */
create or replace function inc_responses(uname text)
returns void language sql as $$
    update public.users
    set responses_this_month = responses_this_month + 1,
        last_active = current_date
    where username = uname;
$$;

/* Reset monthly usage counters - run on 1st of each month */
create or replace function reset_monthly_usage()
returns void language plpgsql as $$
begin
    update public.users
    set responses_this_month = 0,
        batches_this_month   = 0;
end;
$$;
