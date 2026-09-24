-- Read-only metadata export. Run on the legacy project, export the single result
-- as CSV, and preserve it in ignored recovery storage. No customer/auth rows.
-- Not a pg_dump replacement or an executable migration.
WITH definitions AS (
 SELECT 'table' AS kind, n.nspname AS schema_name, c.relname AS object_name,
 jsonb_build_object('rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,
 'columns',(SELECT jsonb_agg(jsonb_build_object('name',a.attname,'type',format_type(a.atttypid,a.atttypmod),
 'not_null',a.attnotnull,'identity',a.attidentity,'generated',a.attgenerated,'default',pg_get_expr(d.adbin,d.adrelid)) ORDER BY a.attnum)
 FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped),
 'constraints',(SELECT jsonb_agg(jsonb_build_object('name',conname,'definition',pg_get_constraintdef(oid))) FROM pg_constraint WHERE conrelid=c.oid)) AS definition
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p')
 UNION ALL SELECT 'view',n.nspname,c.relname,to_jsonb(pg_get_viewdef(c.oid,true)) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('v','m')
 UNION ALL SELECT 'function',n.nspname,p.proname||'('||pg_get_function_identity_arguments(p.oid)||')',to_jsonb(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.prokind IN ('f','p')
 UNION ALL SELECT 'policy',schemaname,tablename||'.'||policyname,to_jsonb(p) FROM pg_policies p WHERE schemaname IN ('public','storage')
 UNION ALL SELECT 'trigger',n.nspname,c.relname||'.'||t.tgname,to_jsonb(pg_get_triggerdef(t.oid,true)) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE NOT t.tgisinternal AND n.nspname IN ('public','auth','storage')
 UNION ALL SELECT 'index',schemaname,indexname,to_jsonb(indexdef) FROM pg_indexes WHERE schemaname='public'
 UNION ALL SELECT 'enum',n.nspname,t.typname,jsonb_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace JOIN pg_enum e ON e.enumtypid=t.oid WHERE n.nspname='public' GROUP BY n.nspname,t.typname
 UNION ALL SELECT 'table_grant',table_schema,table_name||'.'||grantee||'.'||privilege_type,to_jsonb(g) FROM information_schema.role_table_grants g WHERE table_schema='public'
 UNION ALL SELECT 'bucket','storage',id,jsonb_build_object('name',name,'public',public,'file_size_limit',file_size_limit,'allowed_mime_types',allowed_mime_types) FROM storage.buckets
)
SELECT 'wzos-legacy-definitions' AS export_name, now() AS retrieved_at,
 count(*) AS definition_count,
 jsonb_agg(to_jsonb(definitions) ORDER BY kind,schema_name,object_name) AS definitions
FROM definitions;
