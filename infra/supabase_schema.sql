create extension if not exists pgcrypto;

create table if not exists public.projects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    project_name text not null,
    species text,
    system_type text,
    report_profile text default 'Produtor',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.project_inputs (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    version_no integer not null default 1,
    payload_json jsonb not null,
    created_at timestamptz not null default now()
);

create table if not exists public.project_results (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    input_version integer not null,
    results_json jsonb not null,
    created_at timestamptz not null default now()
);

alter table public.projects enable row level security;
alter table public.project_inputs enable row level security;
alter table public.project_results enable row level security;
