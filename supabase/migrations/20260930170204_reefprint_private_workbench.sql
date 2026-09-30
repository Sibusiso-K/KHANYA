create table public.samples (
  owner_id uuid not null references auth.users(id) on delete cascade,
  sample_id text not null check (sample_id ~ '^[A-Za-z0-9_-]{1,100}$'),
  object_path text,
  dataset text not null,
  created_at timestamptz not null default now(),
  primary key (owner_id, sample_id)
);
create table public.results (
  owner_id uuid not null,
  result_id text not null check (result_id ~ '^[A-Za-z0-9]{1,100}$'),
  sample_id text not null,
  payload jsonb not null,
  artifacts jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (owner_id, result_id),
  foreign key (owner_id, sample_id) references public.samples(owner_id, sample_id) on delete cascade
);
create index results_sample_owner_idx on public.results(owner_id, sample_id);
create table public.sample_records (
  owner_id uuid not null,
  sample_id text not null,
  version integer not null check (version > 0),
  updated_at timestamptz not null default now(),
  record jsonb not null default '{}'::jsonb,
  primary key (owner_id, sample_id),
  foreign key (owner_id, sample_id) references public.samples(owner_id, sample_id) on delete cascade
);
alter table public.samples enable row level security;
alter table public.results enable row level security;
alter table public.sample_records enable row level security;
revoke all on public.samples, public.results, public.sample_records from anon;
grant select, insert, update, delete on public.samples, public.results, public.sample_records to authenticated;
create policy samples_owner on public.samples for all to authenticated
  using ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true')
  with check ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true');
create policy results_owner on public.results for all to authenticated
  using ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true')
  with check ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true');
create policy records_owner on public.sample_records for all to authenticated
  using ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true')
  with check ((select auth.uid()) = owner_id and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true');

create function public.save_sample_record(p_sample_id text, p_expected_version integer, p_record jsonb)
returns setof public.sample_records language plpgsql security invoker set search_path = '' as $$
begin
  if p_expected_version = 0 then
    return query insert into public.sample_records(owner_id, sample_id, version, record)
      values (auth.uid(), p_sample_id, 1, p_record)
      on conflict (owner_id, sample_id) do nothing returning *;
  else
    return query update public.sample_records set version = version + 1, record = p_record, updated_at = now()
      where owner_id = auth.uid() and sample_id = p_sample_id and version = p_expected_version returning *;
  end if;
end;
$$;
revoke all on function public.save_sample_record(text,integer,jsonb) from public, anon;
grant execute on function public.save_sample_record(text,integer,jsonb) to authenticated;

insert into storage.buckets(id, name, public, file_size_limit)
values ('reefprint-private', 'reefprint-private', false, 26214400);
create policy reefprint_storage_select on storage.objects for select to authenticated
 using (bucket_id = 'reefprint-private' and (storage.foldername(name))[1] = (select auth.uid())::text
        and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true');
create policy reefprint_storage_insert on storage.objects for insert to authenticated
 with check (bucket_id = 'reefprint-private' and (storage.foldername(name))[1] = (select auth.uid())::text
             and coalesce((select auth.jwt())->>'is_anonymous','false') <> 'true');
create policy reefprint_storage_update on storage.objects for update to authenticated
 using (bucket_id = 'reefprint-private' and (storage.foldername(name))[1] = (select auth.uid())::text)
 with check (bucket_id = 'reefprint-private' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy reefprint_storage_delete on storage.objects for delete to authenticated
 using (bucket_id = 'reefprint-private' and (storage.foldername(name))[1] = (select auth.uid())::text);
