# Evidence assistant and voice observations

Implemented on 30 September 2026. These features help users interpret and navigate the existing mineral evidence. They do not change the segmentation model, its measured accuracy, or plant-control safety gates.

## What works without a key

The **Ask the evidence** panel calls the authenticated backend. Its default mode is a deterministic local evidence helper, not a language model. It answers supported questions about the selected prediction, analysis scope, actual recorded runtime, checkpoint-bound held-out accuracy, the simulator advisory and requirements for spatial data. Answers carry `predicted`, `measured` and `simulated` source labels. No matching accuracy report means no reported score. Unknown questions receive a clear boundary rather than invented geology.

The helper can propose four tasks: open Reports, open Spatial, run analysis of the selected sample, or append a note to the editable sample-record draft. Each task needs its own user click. Changing the selected result invalidates old proposals. A note proposal does not save the record. The assistant cannot operate the simulator, apply plant parameters, execute SQL or shell commands, read arbitrary files, expose credentials or erase data.

Example questions:

- `Summarise this result`
- `How accurate is the model?`
- `Explain the process advisory`
- `What does the spatial view require?`
- `Run analysis of this sample`
- `Add note: Reflected-light acquisition; fine sulphide intergrowths observed. Confirm mineral names against the overlay.`

The API route must resolve the selected sample and result within the signed-in user's workspace. It must construct context from server records and the active report, not accept metrics or result contents from the browser.

## Optional language model connection

The provider integration uses the Chat Completions contract, server credentials and a fixed endpoint allowlist. AIMLAPI documents its versioned endpoint and OpenAI-compatible client configuration in [Supported SDKs](https://docs.aimlapi.com/quickstart/supported-sdks). Featherless provides the same contract in its [Quickstart](https://featherless.ai/docs/quickstart-guide). Hugging Face exposes its provider router for [Chat Completion](https://huggingface.co/docs/inference-providers/tasks/chat-completion). These are optional explanation services; they do not supply segmentation labels or accuracy evidence.

| Provider setting | Fixed server destination | Setup requirement |
|---|---|---|
| `aimlapi` | `https://api.aimlapi.com/v1/chat/completions` | API key, account quota, a currently available chat model ID |
| `featherless` | `https://api.featherless.ai/v1/chat/completions` | API key, compatible subscription/model access |
| `huggingface` | `https://router.huggingface.co/v1/chat/completions` | Token with Inference Providers permission and available model/provider quota |
| `ollama` | `http://127.0.0.1:11434/v1/chat/completions` | Running local Ollama server and a downloaded compatible model; no API key required |

Ollama's official [OpenAI compatibility documentation](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx) describes the local endpoint. Ollama can also expose cloud models; choose a downloaded local model when local-only execution is required and verify its runtime. Installing or downloading an LLM is not part of this change. Its performance depends on this machine's RAM, CPU/GPU and model size.

Set these in the server's ignored environment/secret configuration, never frontend code, Git, browser storage, a screenshot or chat:

```text
REEFPRINT_ASSISTANT_PROVIDER=featherless
REEFPRINT_ASSISTANT_MODEL=Qwen/Qwen2.5-7B-Instruct
REEFPRINT_ASSISTANT_API_KEY=<server secret>
```

`Qwen/Qwen2.5-7B-Instruct` is Featherless's documented integration example, not a claim that it is the best model for mineral interpretation. Confirm the chosen model is available under your account using the [Featherless model catalogue API](https://featherless.ai/docs/api-reference-models). Compare any model on a fixed set of evidence questions before adopting it: absent metrics, zero-IoU magnetite, ambiguous visual phases, low confidence, area versus grade, unlocated samples and unsafe task requests. External accounts and quota may cost money; the local evidence helper has no provider charge.

The optional `REEFPRINT_ASSISTANT_BASE_URL` must exactly match the approved provider base. Arbitrary URLs, metadata endpoints, credentials in URLs, redirects, alternate ports and request-supplied endpoints are rejected. Provider calls have a 35-second timeout, an 800-token answer budget and a maximum of two simultaneous requests. Provider error bodies and credential-bearing exception text are not returned to the browser.

The server's `/api/assistant/status` returns only configuration readiness, provider name, model ID and the context-sharing policy. It never returns the key. **Ready means configured, not a successful provider call.** A live call still requires a real key, quota, model access and network connectivity.

The user must enable the provider and explicitly approve context sharing. The request includes the question and bounded selected result/report facts. No images, audio, saved field notes, assay attachments, geographic coordinates or protected URLs are sent. A user can type sensitive material into the question itself; the consent message states that the question will be shared. Provider text is labelled as a generated explanation and must be checked against the source evidence. Provider tool calls are rejected, and task proposals remain governed by local allowlisted policy. Prompting an LLM to stay grounded cannot guarantee factual correctness; its answer is never written into measured model metrics or automatically saved as a field observation.

## Voice observations

The sample-record form provides explicit start/stop microphone controls, an editable transcript draft and **Add to note draft**. Mineral names, units and values must be reviewed before saving.

Browser speech recognition is feature-detected. It is not supported consistently across browsers, and [MDN's SpeechRecognition documentation](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) notes that some implementations use a server speech service. The user explicitly acknowledges this before dictation. This feature does not claim offline speech recognition, REEFPRINT-hosted transcription or guaranteed scientific spelling.

Where `MediaRecorder` and microphone access are available in a secure context, the user can instead record a local voice memo, play it back and download it. It stops after two minutes and is held in browser memory only. It is not uploaded or transcribed. Permission denial, unsupported browsers and speech-service failures leave typed notes usable. Closing the form or leaving the page can discard an undownloaded recording or unused draft.

## Files and contracts

- `webapi/assistant.py`: `get_status()`, `respond(question, context, use_provider=False, context_opt_in=False)` and safe `AssistantError.status_code`.
- `frontend/src/AssistantPanel.tsx`: `{sampleId, resultId?, busy?, onExecute(proposal)}` and exported `AssistantProposal`.
- `frontend/src/VoiceNotes.tsx`: `{onAppend(text), disabled?}`; append is an editable draft action.
- `frontend/src/assistant.css`: scoped white-workbench component styling, mobile layouts, focus indicators and reduced-motion support.
- `tests/test_workbench_assistant.py`: 25 checks cover evidence separation, missing metrics, bounded tasks, unsafe requests, opt-in, fixed provider destinations, credential privacy, rejected tool calls and transport failures.
- `tests/test_workbench_assistant_routes.py`: seven HTTP checks cover authenticated access, tenant ownership, server-owned evidence, rejected client metric injection, source-image hash changes, stale checkpoints and consent errors.
- `frontend/e2e/assistant.spec.ts`: controlled browser fixtures cover task approval, note draft versus explicit save, speech consent/transcript review and provider opt-in. A mocked speech recognizer does not verify real microphone or speech-service accuracy.

## Verification and remaining work

All 32 focused backend checks passed locally on 30 September 2026, including tenant ownership and active result/source identity checks. `npx tsc --noEmit` also passed. These checks use a mock provider transport; no external key, live paid model or microphone service was used in the tests. The parent integration runs the browser fixtures together with the workbench release suite. A real microphone still needs verification in a supported browser; a live provider proof requires user-configured secrets and an explicitly opted-in request.

Possible later additions: a real offline speech model with documented model download/license and measured latency; user-owned voice attachments in private storage; an expert-approved retrieval corpus with page-level citations; and a provider-evaluation report. None should replace image-grounded segmentation or the human-reviewed simulator pathway.
