# Atlas / Field Voice L4 investigation

Investigation only. User requested review of the USD1.42/hour option after explicitly keeping model hosting OFF. No model download, GPU launch, IAM change, provider test or public activation is authorized by this investigation. Existing conditional activation approval targets the previous RTX model arrangement; do not apply it to changed model weights/runtime without review.

## Conclusion

Cloud Run L4 with 8 CPU/32 GiB is a supported configuration and costs approximately USD1.42092 per allocated instance-hour in us-central1 without GPU zonal redundancy. It is a viable infrastructure candidate, not yet an accepted Field Voice model deployment. Preserve Gemma 31B if its official compressed checkpoint fits and passes the focused report check; do not silently substitute a smaller model.

## Verified cost and availability

Google recommends 8 CPU/32 GiB for L4 (minimum4CPU/16GiB). L4 provides24GB GPU memory, separate from the32GiB system RAM. us-central1 is supported. Existing project quota readback returned3 non-zonal L4 GPUs for us-central1; quota does not reserve capacity or guarantee a deployment. Quota evidence: Cloud Shell `/tmp/wzos-l4-quota-review.json`, filtered metric `run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy`. No quota request or change was made.

Sources: [GPU configuration](https://docs.cloud.google.com/run/docs/configuring/services/gpu), [pricing](https://cloud.google.com/run/pricing), checked October18.

| Component | Calculation | USD/hour |
|---|---|---:|
| CPU | 8 x0.000018 x3600 | 0.51840 |
| System RAM | 32 x0.000002 x3600 | 0.23040 |
| Non-zonal L4 | 0.0001867 x3600 | 0.67212 |
| Total | | 1.42092 |

Compared with the reviewed RTX20CPU/80GiB rate3.186792/hour, allocation-hour savings are55.41%. Continuously allocated24hours costs34.10/day, about1023.06/30days. Ten allocated hours cost14.21. These are compute estimates before allowances; Speech, model storage/transfer, builds, logs and network are additional. Billing includes startup and time an instance remains allocated, not just model-generation seconds. Slower inference/cold starts can reduce savings per report. Min0/max1 and no keep-warm probes remain appropriate; they are not a spending cap or instant shutdown guarantee.

## Models and memory

Current deploy_atlas_vllm.sh loads the retained full31B GCS checkpoint, applies onlineFP8, serves two sequences and32767tokens on RTX. It cannot simply switch GPU names:31B8-bit memory exceeds24GB. CPU RAM increases cannot replace missing GPU memory without a different, potentially slower offloading arrangement; offloading is not this recommendation.

Google publishes `google/gemma-4-31B-it-qat-w4a16-ct`, 4-bit weights/16-bit activations in compressed-tensors format for vLLM. Google's generic Q4 memory estimate is17.5GB; vLLM's current main recipe reports19.8GB for its31B W4A16 checkpoint. These are different estimates/formats and are not proof of our runtime peak. The actual checkpoint tree currently lists23.3GB of weights. We must allow for activations, attention cache, runtime workspaces and load-time peaks. Feasibility on one24GB L4 remains UNVERIFIED.

Sources: [Google overview](https://ai.google.dev/gemma/docs/core), [vLLM recipe](https://github.com/vllm-project/recipes/blob/main/Google/Gemma4.md), [Google checkpoint files](https://huggingface.co/google/gemma-4-31B-it-qat-w4a16-ct/tree/main). Observed model repository revision52f3f65bc7a02d555763bc923bd1d9094898219d; verify immutable metadata before any future download. No weights downloaded here.

The smaller official Gemma4E4B is documented by vLLM for24GB+ GPUs and provides a lower-memory alternative. Its suitability for counts, negation, ambiguity and incident extraction is not established by generic benchmarks. Do not substitute it without a deliberate product decision and model-specific acceptance.

## Proposed implementation, not applied

1. Inspect/pin a vLLM runtime with Gemma4 compressed-tensors W4A16 support on Ada/L4. Current pinned container support for this exact checkpoint has not been verified. Keep schema-constrained output and supported no-request-logging flags. Avoid latest/nightly production tags and remote custom code.
2. Stage the exact official compressed checkpoint in a separate immutable GCS prefix. Retain original weights and rollback evidence; preserve private dedicated identity/network. Verify size/hash/generation metadata. Do not bind HF_TOKEN to serving merely for convenience. Model acquisition, storage cost and any new access require review before execution.
3. Start with text-only, one sequence/concurrency1, no draft model/speculative decoding, and a bounded context candidate8192tokens. Verify total input plus2048 output tokens fit; current client has no matching tokenizer budget, so do not silently truncate job/transcript context. Confirm the selected runtime really omits unused multimodal memory allocations. Context/cache choices remain hypotheses until measured.
4. Remove forced online `--quantization=fp8`; use the checkpoint's native quantization configuration, as documented by vLLM. Review KV-cache precision separately rather than blindly copying RTX flags. Confirm GCS streaming loader compatibility with this checkpoint format.
5. Update Field Voice's fixed model identity and saved report provenance to identify QAT weights/revision accurately. Do not hide the change behind the old unqualified31B alias. Existing build238ef05b and acceptanceb564dfa1 assume the old model identity; activation/model-check helpers also assert RTX20CPU/80GiB. They require a separate reviewed L4 configuration, not bypassed assertions. Ordinary Atlas chat stays unchanged.
6. Only after scoped approval: one bounded startup/memory plus synthetic report acceptance, no paid retry loop. Measure peak VRAM, cold/warm response and exact quantities/incident fields. Retain tenant/review/zeroSMS guarantees. If memory fails, clean up and report it rather than automatically escalating compute or switching models. No full unchanged app-suite repeat for this investigation.

## Remaining decision

The L4 rate and quota are confirmed;31B QAT fit, pinned-runtime support, model loading, latency and report quality are not. Recommendation: prepare the official31B QAT candidate first without paid execution. Treat E4B as an explicit fallback choice. Any paid pilot/ongoing hosting/public activation needs a fresh exact scope because the user kept hosting OFF. Existing repaired836PostgreSQL/149Node results remain valid for their frozen source, not evidence of a new model's correctness.
