# Frozen application cf357802f6d979667225ebb0eed3ce5cea19d826.
# Build context comes from git archive of services/shared/knowledge and requirements.
# Keeps the already verified source binaries from the immutable rollback image.
FROM us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:13cb755a8973dc9923c76ea4eed229a57b16ba357db2f19178ea8ca953222284
USER root
WORKDIR /app
RUN rm -rf /app/services /app/shared /app/knowledge
COPY requirements-v2.txt requirements-accounts.txt ./
RUN pip install --no-cache-dir -r requirements-accounts.txt
COPY services ./services
COPY shared ./shared
COPY knowledge ./knowledge
COPY scripts/package_source_library.py /app/scripts/package_source_library.py
RUN chmod -R a+rX /app/services /app/shared /app/knowledge /app/scripts
USER wzos
RUN python /app/scripts/package_source_library.py --verify /app/.local-data/knowledge
RUN python -c "import hashlib; assert hashlib.sha256(open('/app/.local-data/knowledge/snapshot.json','rb').read()).hexdigest() == '070ec5e461a56fbdf60ad81c0b91a699e87316d500af7dc6245b94e81a3dcd4', 'Inherited source snapshot differs from frozen release'"
CMD ["sh","-c","exec uvicorn services.workspace_preview.account_app:application --factory --host 0.0.0.0 --port ${PORT:-8080}"]
