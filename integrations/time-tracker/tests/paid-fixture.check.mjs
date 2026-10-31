// Actual Stripe test-object replay; no network delivery or production database claim.
import { PGlite } from '../../../.local-data/pg-validation/node_modules/@electric-sql/pglite/dist/index.js';
import { readFile } from 'node:fs/promises';
import { createHmac } from 'node:crypto';
import assert from 'node:assert/strict';
import handler from '../netlify/functions/stripe-webhook.mjs';
const fixturePath=process.argv[2];
if (!fixturePath) throw new Error('Provide captured synthetic Stripe test fixture JSON');
const captured=JSON.parse(await readFile(fixturePath,'utf8'));
const {session,event}=captured;
let subscription=captured.subscription;
assert.equal(session.livemode,false);assert.equal(subscription.livemode,false);assert.equal(event.livemode,false);
assert.equal(session.metadata.purpose,'synthetic_validation');
const company=session.metadata.company_id;
const request=session.metadata.request_id;
const user='22222222-2222-4222-8222-222222222222';
const db=new PGlite();
await db.exec(`
create role anon; create role authenticated; create role service_role bypassrls;
create table companies_2(id uuid primary key);
create table memberships_2(company_id uuid references companies_2,user_id uuid,role text,unique(company_id,user_id));
create table company_billing_2(company_id uuid primary key references companies_2,stripe_customer_id text,
stripe_subscription_id text,stripe_product_id text,status text,current_period_end timestamptz);
create table time_entries_2(company_id uuid,user_id uuid);
grant select,insert,update on time_entries_2 to authenticated;
alter table time_entries_2 enable row level security;
create policy own_time_insert on time_entries_2 for insert to authenticated with check(true);
grant usage on schema public to anon,authenticated,service_role;
grant select,insert,update on companies_2,memberships_2 to authenticated,service_role;
grant all on company_billing_2 to anon,authenticated;
create schema auth;
grant usage on schema auth to authenticated,service_role;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
create function public.company_role(c uuid) returns text language sql stable security definer set search_path=public as $$ select role from memberships_2 where company_id=c and user_id=auth.uid() limit 1 $$;
create function public.is_company_admin(c uuid) returns boolean language sql stable security definer set search_path=public as $$ select coalesce(company_role(c) in ('owner','admin'),false) $$;
create function public.is_company_member(c uuid) returns boolean language sql stable security definer set search_path=public as $$ select exists(select 1 from memberships_2 where company_id=c and user_id=auth.uid()) $$;
alter table company_billing_2 enable row level security;
alter table memberships_2 enable row level security;
create policy billing_read on company_billing_2 for select to authenticated using(is_company_member(company_id));
create policy membership_read on memberships_2 for select to authenticated using(user_id=auth.uid() or is_company_admin(company_id));
create policy membership_insert on memberships_2 for insert to authenticated with check(is_company_admin(company_id));
create policy membership_update on memberships_2 for update to authenticated using(is_company_admin(company_id)) with check(is_company_admin(company_id));
insert into companies_2 values('${company}');
insert into memberships_2 values('${company}','${user}','owner');
`);

await db.exec(await readFile(new URL('../supabase/migrations/20261031070800_tracker_checkout_activation.sql',import.meta.url),'utf8'));
await db.exec('set role service_role');
await db.query('select tracker_reserve_checkout($1,$2,$3,$4)',[company,user,request,3]);
const settings={TRACKER_CHECKOUT_V2_ENABLED:'true', STRIPE_SECRET_KEY:'synthetic-only',
 STRIPE_WEBHOOK_SECRET:'local-replay-only', SUPABASE_URL:'https://fixture.invalid',SUPABASE_SERVICE_ROLE_KEY:'synthetic-only',
 STRIPE_PRODUCT_ID:session.metadata.product_id,
 STRIPE_MONTHLY_PRICE_ID:subscription.items.data.find(i=>i.quantity===1).price.id,
 STRIPE_EXTRA_USER_PRICE_ID:subscription.items.data.find(i=>i.quantity===2).price.id};
globalThis.Netlify={env:{get:key=>settings[key]}};
let rpcCalls=0;
globalThis.fetch=async(url,options={})=>{
 if(url===`https://api.stripe.com/v1/checkout/sessions/${session.id}`) return Response.json(session);
 if(url===`https://api.stripe.com/v1/subscriptions/${subscription.id}`) return Response.json(subscription);
 if(url.startsWith('https://fixture.invalid/rest/v1/company_billing_2?')) return Response.json((await db.query('select stripe_subscription_id from company_billing_2')).rows);
 if(url==='https://fixture.invalid/rest/v1/rpc/tracker_apply_billing_event') {
  rpcCalls++;const p=JSON.parse(options.body);
  const names=['event','event_at','company','request','session','subscription','customer','product','status','seats','period_end','initial'];
  const r=await db.query('select tracker_apply_billing_event($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) as result',names.map(n=>p['p_'+n]));
  return Response.json(r.rows[0].result);
 }
 throw new Error('Unexpected network destination: '+url);
};
const send=async(e,valid=true)=>{
 const payload=JSON.stringify(e),t=Math.floor(Date.now()/1000);
 const sig=createHmac('sha256',settings.STRIPE_WEBHOOK_SECRET).update(`${t}.${payload}`).digest('hex');
 return handler(new Request('https://fixture.invalid/api/stripe-webhook',{method:'POST',body:payload,headers:{'stripe-signature':`t=${t},v1=${valid?sig:'0'.repeat(64)}`}}));
};
let checks=0;
const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
try {
 check((await send(event,false)).status,400);check(rpcCalls,0);
 check((await send(event)).status,200);
 let row=(await db.query('select * from company_billing_2')).rows[0];
 check(row.status,'active');check(row.seat_limit,3);check(row.stripe_subscription_id,subscription.id);
 check(new Date(row.current_period_end).getTime(),subscription.items.data[0].current_period_end*1000);
 check((await db.query('select state from tracker_checkout_requests')).rows[0].state,'fulfilled');
 check((await send(event)).status,200);
 check((await db.query('select count(*)::int as n from tracker_billing_events')).rows[0].n,1);
 await db.exec(`reset role;set request.jwt.claim.sub='${user}';set role authenticated`);
 await db.query('insert into time_entries_2 values($1,$2)',[company,user]);checks++;
 for(const id of ['55555555-5555-4555-8555-555555555555','66666666-6666-4666-8666-666666666666']) await db.query("insert into memberships_2 values($1,$2,'worker')",[company,id]);checks++;
 await assert.rejects(db.query("insert into memberships_2 values($1,$2,'worker')",[company,'77777777-7777-4777-8777-777777777777']));checks++;
 await db.exec("set request.jwt.claim.sub='88888888-8888-4888-8888-888888888888'");
 check((await db.query('select count(*)::int as n from company_billing_2')).rows[0].n,0);
 if(captured.cancellation && captured.cancelEvent) {
  subscription=captured.cancellation;
  assert.equal(subscription.livemode,false);assert.equal(captured.cancelEvent.livemode,false);
  await db.exec('reset role;set role service_role');
  check((await send(captured.cancelEvent)).status,200);
  check((await db.query('select status from company_billing_2')).rows[0].status,'canceled');
  await db.exec(`reset role;set request.jwt.claim.sub='${user}';set role authenticated`);
  await assert.rejects(db.query('insert into time_entries_2 values($1,$2)',[company,user]));checks++;
 }
 console.log(`${checks} paid Stripe fixture + real webhook + isolated PostgreSQL checks PASS. Local signatures; no Stripe network delivery claim.`);
} finally {await db.close();}
