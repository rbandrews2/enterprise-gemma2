# Atlas concise guidance and demeanor — November 24, 2026

Candidate only; not deployed. User requested faster responses without losing accuracy/references and a relaxed wise-professor demeanor.

Changes: shared style asks for patient, respectful conversational explanations, explicit uncertainty and a focused follow-up. Ordinary first answers target120–180words, explicitly allowing longer answers for important conditions/exceptions. No promise of permanent learning or human experiences. Shared style applies to Ask Atlas and managed/private floating chat.

Performance hypothesis: reducing repetitive output should reduce generation time, but reasoning tokens may dominate and no live speed gain is claimed. Full reviewed source context, thinking enabled,4096-token ceiling, strict schema, exact passage lookup, errata handling and server calculations are unchanged. No model-size downgrade, cached answers or automatic paid retries.

DOT timing instrumentation records prepare/auth/tokenize/generate/validation/total milliseconds and input/output token counts only, never question, response, source text or credentials. This makes subsequent tuning evidence-based.

Validation: unittest discover test_dot_reasoning.py31 passed; test_vllm_intelligence.py3 passed; test_managed_intelligence.py4 passed. Total38, no skips/failures. Test import via module name initially failed because fixtures require tests on discovery path; corrected discovery passed. Diff check passed. No migration/IAM/cloud changes.

Next: deploy through existing release workflow and compare the same55mph lane closure question on the pinned model. Accept only with preserved relevant conditions and citations; report actual generation and total latency. Do not claim prompt changes guarantee model accuracy or a measured speedup. Rollback these three runtime files to prior commit if quality regresses.
