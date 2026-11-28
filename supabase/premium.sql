-- Premium эрх + төлбөрийн хүсэлт. Зөвхөн админ олгоно (RLS); хэрэглэгч өөрийнхөө мөрийг л харна.
create table if not exists public.premium (
  uid uuid primary key references auth.users(id) on delete cascade,
  until date not null, plan text, updated_at timestamptz not null default now());
alter table public.premium enable row level security;
create policy premium_select on public.premium for select to authenticated using (uid = (select auth.uid()) or (select public.is_admin()));
create policy premium_admin_ins on public.premium for insert to authenticated with check ((select public.is_admin()));
create policy premium_admin_upd on public.premium for update to authenticated using ((select public.is_admin())) with check ((select public.is_admin()));
create policy premium_admin_del on public.premium for delete to authenticated using ((select public.is_admin()));
revoke all on public.premium from anon;
create table if not exists public.premium_requests (
  id bigint generated always as identity primary key,
  uid uuid not null references auth.users(id) on delete cascade,
  plan text not null check (plan in ('30','90','365')),
  ref text not null default '' check (char_length(ref) <= 160),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at timestamptz not null default now());
create index if not exists premium_requests_uid_idx on public.premium_requests(uid);
alter table public.premium_requests enable row level security;
create policy preq_select on public.premium_requests for select to authenticated using (uid = (select auth.uid()) or (select public.is_admin()));
create policy preq_insert on public.premium_requests for insert to authenticated with check (uid = (select auth.uid()) and status = 'pending');
create policy preq_admin_upd on public.premium_requests for update to authenticated using ((select public.is_admin())) with check ((select public.is_admin()));
create policy preq_admin_del on public.premium_requests for delete to authenticated using ((select public.is_admin()));
revoke all on public.premium_requests from anon;
-- Тохиргоо (хаалт асаах, үнэ, төлбөрийн заавар) нь site хүснэгтийн id='prem' мөрөнд JSON-оор хадгалагдана.

-- 3 хоногийн үнэгүй туршилт: нэг хэрэглэгч насан туршдаа ганц удаа (сервер талд хамгаалсан)
create table if not exists public.premium_trials (uid uuid primary key references auth.users(id) on delete cascade, claimed_at timestamptz not null default now());
alter table public.premium_trials enable row level security;
create policy ptrial_select on public.premium_trials for select to authenticated using (uid = (select auth.uid()) or (select public.is_admin()));
revoke all on public.premium_trials from anon;
create or replace function public.claim_premium_trial() returns date language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid(); d date;
begin
  if u is null then raise exception 'not authenticated'; end if;
  if exists (select 1 from premium_trials where uid = u) then raise exception 'trial already used'; end if;
  if exists (select 1 from premium where uid = u) then raise exception 'already premium'; end if;
  d := current_date + 3; insert into premium_trials(uid) values (u); insert into premium(uid, until, plan) values (u, d, 'trial'); return d;
end $$;
revoke all on function public.claim_premium_trial() from public, anon;
grant execute on function public.claim_premium_trial() to authenticated;
