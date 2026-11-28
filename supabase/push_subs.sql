-- Өдрийн сануулга (Web Push) бүртгэл. Хэрэглэгч бүр зөвхөн өөрийн мөрийг харна/өөрчилнө.
create table if not exists public.push_subs (
  endpoint   text primary key,
  uid        uuid not null references auth.users(id) on delete cascade,
  p256dh     text not null,
  auth       text not null,
  hour       smallint not null default 20 check (hour between 0 and 23),  -- орон нутгийн цаг
  tzo        smallint not null default 480 check (tzo between -840 and 840), -- UTC-аас минутаар
  lang       text not null default 'mn' check (lang in ('mn','en','ru','ja')),
  last_sent  date,
  created_at timestamptz not null default now()
);
create index if not exists push_subs_uid_idx on public.push_subs(uid);
alter table public.push_subs enable row level security;
create policy push_subs_select_own on public.push_subs for select to authenticated using (uid = (select auth.uid()));
create policy push_subs_insert_own on public.push_subs for insert to authenticated with check (uid = (select auth.uid()));
create policy push_subs_update_own on public.push_subs for update to authenticated using (uid = (select auth.uid())) with check (uid = (select auth.uid()));
create policy push_subs_delete_own on public.push_subs for delete to authenticated using (uid = (select auth.uid()));
-- Илгээгч (GitHub Action) service_role түлхүүрээр RLS-г тойрч уншина; anon-д эрх өгөхгүй.
revoke all on public.push_subs from anon;

alter table public.push_subs add column if not exists minute smallint not null default 0 check (minute between 0 and 59);
