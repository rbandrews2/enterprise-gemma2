// Local embedded PostgreSQL validation. Does not connect to Supabase or production.
import { PGlite } from '../../../.local-data/pg-validation/node_modules/@electric-sql/pglite/dist/index.js';
import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const db = new PGlite();
const company='11111111-1111-4111-8111-111111111111';
const user='22222222-2222-4222-8222-222222222222';
const request='33333333-3333-4333-8333-333333333333';
await db.exec(`
create role anon; create role authenticated; create role service_role bypassrls;
create table companies_2(id uuid primary key);
create table memberships_2(company_id uuid references companies_2,user_id uuid,role text,unique(company_id,user_id));
create table company_billing_2(company_id uuid primary key references companies_2,stripe_customer_id text,
stripe_subscription_id text,stripe_product_id text,status text,current_period_end timestamptz);
grant usage on schema public to anon,authenticated,service_role;
grant select,insert,update on companies_2,memberships_2 to authenticated,service_role;
grant select,insert on company_billing_2 to authenticated;
insert into companies_2 values('${company}');
insert into memberships_2 values('${company}','${user}','owner');
`);
await db.exec(await readFile(new URL('../billing-schema-proposal.sql',import.meta.url),'utf8'));
let checks=0;
const ok = () => checks++;
async function denied(sql) { await assert.rejects(db.exec(sql)); ok(); }
await db.exec('set role authenticated');
await denied(`insert into company_billing_2(company_id,status) values('${company}','active')`);
await denied(`select tracker_reserve_checkout('${company}','${user}','${request}',2)`);
await db.exec('reset role; set role service_role');
const reserve=async (id,seats=2) => (await db.query('select tracker_reserve_checkout($1,$2,$3,$4) as result',[company,user,id,seats])).rows[0].result;
assert.equal((await reserve(request)).request_id,request); ok();
assert.equal((await reserve('44444444-4444-4444-8444-444444444444')).request_id,request); ok();
await assert.rejects(reserve('44444444-4444-4444-8444-444444444444',3)); ok();
async function event(id,at,status='active',initial=true,sub='sub_test') {
  return (await db.query('select tracker_apply_billing_event($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) as result',
    [id,at,company,request,'cs_test',sub,'cus_test','prod_test',status,2,null,initial])).rows[0].result;
}
assert.equal(await event('evt_1',100),'applied'); ok();
assert.equal(await event('evt_1',100),'duplicate'); ok();
assert.equal(await event('evt_2',101),'duplicate-session'); ok();
await assert.rejects(event('evt_wrong',102,'active',false,'sub_other')); ok();
assert.equal(await event('evt_late',99,'canceled',false),'stale'); ok();
assert.equal((await db.query('select status,seat_limit from company_billing_2')).rows[0].status,'active'); ok();
assert.equal(await event('evt_cancel',103,'canceled',false),'applied'); ok();
await assert.rejects(event('evt_equal',103,'active',false)); ok();
await db.exec('reset role; set role authenticated');
await db.exec(`insert into memberships_2 values('${company}','55555555-5555-4555-8555-555555555555','worker')`); ok();
await denied(`insert into memberships_2 values('${company}','66666666-6666-4666-8666-666666666666','worker')`);
await denied(`update memberships_2 set user_id='77777777-7777-4777-8777-777777777777' where user_id='${user}'`);
await db.exec('reset role');
assert.equal((await db.query('select count(*)::integer as n from memberships_2')).rows[0].n,2); ok();
await db.close();
console.log(`${checks} embedded PostgreSQL checks PASS; live RLS/schema and cross-connection concurrency validation still required.`);
