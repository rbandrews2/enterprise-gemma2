-- REVIEW PROPOSAL ONLY. Not an applied or CLI-generated migration.
-- Validate against current schema in disposable PostgreSQL before creating a migration.
begin;
alter table public.company_billing_2 add column if not exists seat_limit integer
  check (seat_limit between 1 and 30);
alter table public.company_billing_2 add column if not exists last_stripe_event_at bigint;
-- NULL preserves existing accounts until their purchased allowance is reconciled.
-- Do not infer paid allowances from the current employee count.
revoke all on public.company_billing_2 from public, anon, authenticated;
grant select on public.company_billing_2 to authenticated;
drop policy if exists "Company admins can initialize billing status" on public.company_billing_2;

create table public.tracker_checkout_requests (
  request_id uuid primary key,
  company_id uuid not null references public.companies_2(id),
  user_id uuid not null,
  seats integer not null check (seats between 1 and 30),
  state text not null default 'pending' check (state in ('pending','fulfilled','expired')),
  session_id text unique,
  created_at timestamptz not null default now()
);
create unique index tracker_one_pending_checkout on public.tracker_checkout_requests(company_id)
  where state = 'pending';
create table public.tracker_billing_events (
  event_id text primary key,
  company_id uuid not null references public.companies_2(id),
  event_at bigint not null,
  processed_at timestamptz not null default now()
);
alter table public.tracker_checkout_requests enable row level security;
alter table public.tracker_billing_events enable row level security;
revoke all on public.tracker_checkout_requests, public.tracker_billing_events from public, anon, authenticated;
grant select, insert, update on public.tracker_checkout_requests, public.tracker_billing_events to service_role;
grant select, insert, update on public.company_billing_2 to service_role;

create function public.tracker_reserve_checkout(p_company uuid,p_user uuid,p_request uuid,p_seats integer)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare r public.tracker_checkout_requests; b public.company_billing_2;
begin
  -- Serialize all checkout and fulfillment mutations for this company.
  perform pg_advisory_xact_lock(hashtextextended(p_company::text,0));
  if p_seats is null or p_seats not between 1 and 30 then raise exception 'Invalid seats'; end if;
  if not exists (select 1 from public.memberships_2 where company_id=p_company
    and user_id=p_user and role in ('owner','admin')) then raise exception 'Admin required'; end if;
  select * into b from public.company_billing_2 where company_id=p_company;
  if b.stripe_subscription_id is not null or b.status in ('active','trialing') then
    raise exception 'Existing billing requires management';
  end if;
  if p_seats < (select count(*) from public.memberships_2 where company_id=p_company) then
    raise exception 'Purchase enough seats for existing members';
  end if;
  select * into r from public.tracker_checkout_requests where company_id=p_company and state='pending';
  if found then
    if r.user_id<>p_user or r.seats<>p_seats then raise exception 'Checkout already pending'; end if;
    if r.created_at < now()-interval '23 hours' then
      raise exception 'Pending checkout requires reconciliation';
    end if;
    return jsonb_build_object('request_id',r.request_id,'seats',r.seats);
  end if;
  insert into public.tracker_checkout_requests(request_id,company_id,user_id,seats)
    values(p_request,p_company,p_user,p_seats);
  return jsonb_build_object('request_id',p_request,'seats',p_seats);
end;
$$;

create function public.tracker_apply_billing_event(
  p_event text,p_event_at bigint,p_company uuid,p_request uuid,p_session text,
  p_subscription text,p_customer text,p_product text,p_status text,p_seats integer,
  p_period_end timestamptz,p_initial boolean
) returns text language plpgsql security invoker set search_path = '' as $$
declare b public.company_billing_2; r public.tracker_checkout_requests;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_company::text,0));
  if exists(select 1 from public.tracker_billing_events where event_id=p_event) then return 'duplicate'; end if;
  if p_event is null or p_event_at is null or p_event_at<0 or p_subscription is null
    or p_customer is null or p_product is null or p_status is null
    or p_seats is null or p_seats not between 1 and 30
    or p_status not in ('active','trialing','past_due','canceled','unpaid','inactive') then
    raise exception 'Invalid billing event';
  end if;
  select * into b from public.company_billing_2 where company_id=p_company;
  if b.stripe_subscription_id is not null and b.stripe_subscription_id<>p_subscription then
    raise exception 'Subscription mismatch';
  end if;
  if b.last_stripe_event_at is not null and p_event_at<b.last_stripe_event_at then return 'stale'; end if;
  -- Equal timestamps for different events require reconciliation, never a blind overwrite.
  if b.last_stripe_event_at=p_event_at then raise exception 'Concurrent Stripe event requires reconciliation'; end if;
  if p_initial then
    select * into r from public.tracker_checkout_requests where request_id=p_request;
    if found and r.company_id=p_company and r.seats=p_seats and r.state='fulfilled'
      and r.session_id=p_session and b.stripe_subscription_id=p_subscription then
      insert into public.tracker_billing_events(event_id,company_id,event_at) values(p_event,p_company,p_event_at);
      return 'duplicate-session';
    end if;
    if not found or r.company_id<>p_company or r.seats<>p_seats or r.state<>'pending'
      or p_status<>'active' or p_session is null then raise exception 'Checkout binding mismatch'; end if;
    update public.tracker_checkout_requests set state='fulfilled',session_id=p_session where request_id=p_request;
  elsif b.stripe_subscription_id is null then
    raise exception 'Initial paid checkout required';
  end if;
  insert into public.company_billing_2(company_id,stripe_customer_id,stripe_subscription_id,
    stripe_product_id,status,seat_limit,current_period_end,last_stripe_event_at)
  values(p_company,p_customer,p_subscription,p_product,p_status,p_seats,p_period_end,p_event_at)
  on conflict(company_id) do update set stripe_customer_id=excluded.stripe_customer_id,
    stripe_subscription_id=excluded.stripe_subscription_id,stripe_product_id=excluded.stripe_product_id,
    status=excluded.status,seat_limit=excluded.seat_limit,current_period_end=excluded.current_period_end,
    last_stripe_event_at=excluded.last_stripe_event_at;
  insert into public.tracker_billing_events(event_id,company_id,event_at) values(p_event,p_company,p_event_at);
  return 'applied';
end;
$$;
revoke all on function public.tracker_reserve_checkout(uuid,uuid,uuid,integer) from public,anon,authenticated;
revoke all on function public.tracker_apply_billing_event(text,bigint,uuid,uuid,text,text,text,text,text,integer,timestamptz,boolean) from public,anon,authenticated;
grant execute on function public.tracker_reserve_checkout(uuid,uuid,uuid,integer) to service_role;
grant execute on function public.tracker_apply_billing_event(text,bigint,uuid,uuid,text,text,text,text,text,integer,timestamptz,boolean) to service_role;

create function public.tracker_expire_checkout(p_company uuid,p_request uuid)
returns void language plpgsql security invoker set search_path = '' as $$
begin
  perform pg_advisory_xact_lock(hashtextextended(p_company::text,0));
  update public.tracker_checkout_requests set state='expired'
    where company_id=p_company and request_id=p_request and state='pending';
end;
$$;
revoke all on function public.tracker_expire_checkout(uuid,uuid) from public,anon,authenticated;
grant execute on function public.tracker_expire_checkout(uuid,uuid) to service_role;

-- Trigger runs for direct client writes and existing privileged join/create functions.
-- INVOKER is sufficient: existing membership/billing SELECT policies are tenant scoped.
create function public.tracker_enforce_seats() returns trigger
language plpgsql security invoker set search_path = '' as $$
declare cap integer;
begin
  if tg_op='UPDATE' then
    if new.company_id<>old.company_id or new.user_id<>old.user_id then
      raise exception 'Membership identity is immutable';
    end if;
    return new;
  end if;
  perform pg_advisory_xact_lock(hashtextextended(new.company_id::text,0));
  select seat_limit into cap from public.company_billing_2 where company_id=new.company_id;
  if cap is not null and (select count(*) from public.memberships_2 where company_id=new.company_id)>=cap then
    raise exception 'Purchased user allowance reached';
  end if;
  return new;
end;
$$;
revoke all on function public.tracker_enforce_seats() from public,anon,authenticated;
create trigger tracker_membership_seat_limit before insert or update on public.memberships_2
for each row execute function public.tracker_enforce_seats();
-- Existing owner/member checks still apply. Only NEW shifts require paid access;
-- closing an existing shift and reviewing historical records remain possible.
create policy tracker_paid_new_shift on public.time_entries_2 as restrictive
for insert to authenticated with check (
  exists(select 1 from public.company_billing_2 b where b.company_id=time_entries_2.company_id
    and b.status in ('active','trialing')
    and (b.current_period_end is null or b.current_period_end>now()))
);
notify pgrst,'reload schema';
commit;
