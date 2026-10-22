# Local interpretation with Ollama

Run Hypothesis Lab and Ollama on the same computer. Install [Ollama](https://ollama.com/download), download the chat model you prefer with `ollama pull MODEL`, and start Ollama (the desktop app or `ollama serve`). No model is downloaded automatically by Hypothesis Lab.

In **Analysis → Interpret findings with Ollama**, select **Refresh local models**, choose an installed model, then **Analyze findings**. The initial model load can take time; generation has a three-minute timeout. On timeout, try a smaller model or wait for loading to finish and retry.

The default endpoint is `http://127.0.0.1:11434`. An optional `HYPOTHESIS_OLLAMA_URL` in `.env` supports a different loopback HTTP port. The browser never connects directly to Ollama. Calls go from the local Python process, ignore proxy environment variables, and do not follow redirects. Remote endpoints and known cloud model entries are excluded. Disable cloud features in your Ollama installation for local-only operation, as described in [Ollama's FAQ](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud).

## What the model receives

An explicit snapshot: the research question, event definition, sampling description, notes (first 12,000 characters), up to 50 attached source records and abstracts (first 1,800 characters each), review annotations, declared assumptions, synthetic-data status, and computed numerical results when analysis is ready. It does not read full papers, arbitrary local files, credentials, or other investigations. Inspect the exact material under the generated draft.

Source identifiers `[S1]`, `[S2]`, etc. map to the source records in that snapshot. Check generated references and conclusions against those records. Text generation can contain errors or unsupported claims. No tool execution or automatic evidence classification is enabled.

## Review and reproducibility

The result is a draft, distinct from deterministic inference. It does not change priors, observations, evidence annotations, or posterior calculations. Literature-only investigations can receive a qualitative review while numerical inference remains pending.

Save the investigation to retain its latest draft. JSON and Markdown exports include the interpretation, model name/digest, timestamp, bounded input snapshot, and fingerprint. Changes to the supplied context mark the draft stale. The record preserves what was supplied and returned; it does not guarantee identical future generation. Every draft remains labeled as requiring researcher review.

The static Pages preview demonstrates the workspace and video only. Download and run the repository to use Ollama.
