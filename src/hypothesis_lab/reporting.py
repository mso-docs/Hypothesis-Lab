import json
from datetime import datetime, timezone


def snapshot(
    statement, alpha, beta_prior, observations, result, publications, evidence
):
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hypothesis": statement,
        "model": "Beta-Binomial",
        "prior": {"alpha": alpha, "beta": beta_prior},
        "observations": [o.model_dump() for o in observations],
        "posterior": result.to_dict(),
        "publications": [p.model_dump() for p in publications],
        "evidence": evidence,
        "assumptions": [
            "Independent Bernoulli trials",
            "Constant event probability",
            "Common event definition",
        ],
        "limitations": "Demo observations are synthetic. Qualitative evidence does not update the posterior. No causal inference.",
    }


def markdown(payload):
    p = payload["posterior"]
    model_text = (
        f"Prior: Beta({payload['prior']['alpha']}, {payload['prior']['beta']})\n"
        f"Posterior (calculated): Beta({p['alpha']}, {p['beta']})\n"
        f"Posterior mean: {p['mean']:.4f}\n95% credible interval: {p['interval']}"
        if p
        else "Numerical analysis pending. No posterior has been calculated.\n"
        + "\n".join(payload.get("missing_setup", []))
    )
    draft = payload.get("interpretation")
    interpretation = (
        f"Model: {draft.get('model')} · Researcher review required · "
        f"{'STALE: investigation changed' if draft.get('stale') else 'Snapshot matches investigation'}\n\n"
        + draft.get("text", "")
        if draft
        else "No model interpretation requested."
    )
    return f"""# Hypothesis Lab investigation

{payload["hypothesis"]}

Generated: {payload["created_at"]}

## Model and result
{model_text}

## Starting assumptions
{payload.get("assumption_summary", "See recorded prior parameters.")}

## Research notes
{payload.get("notes", "")}

## Optional local-model interpretation
{interpretation}

## Limitations
{payload["limitations"]}

## Reproducibility record
```json
{json.dumps(payload, indent=2)}
```
"""
