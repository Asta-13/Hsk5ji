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
