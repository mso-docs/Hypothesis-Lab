# Getting started: from a question to a reproducible report

The question-mark tool opens **Help & docs**, the single home for all documentation. Watch the **2:02 captioned illustrated walkthrough** under **Video walkthrough**; **Starting assumptions** and **Model methodology** are sibling guides nested in that same Help section. The same page is linked as **Watch getting started**, immediately below **New investigation**, and from inside the new-investigation dialog. No audio, API key, or network connection is required for the bundled video or practice example.

The video is an animated illustration of the application workflow, not a live screen recording. Its MP4, poster, captions, and chapter track are bundled in `src/hypothesis_lab/ui/frontend/media/`. The chapter script and the practice scenario share one source in `src/hypothesis_lab/tutorial.py`.

## 0:00 — From question to report

An investigation connects a testable question to source papers, review annotations, explicit observations, model assumptions, and a portable report. The app assists research organization and statistical inspection; it does not automatically produce a publication-ready paper.

## 0:10 — Create an investigation

Choose **New investigation** in the explorer. Name it **Radish germination**. This starts with an empty hypothesis, no sources, and no observations. Use **Watch getting started** if you need to return to the guide.

To explore the completed teaching scenario instead, use **Load practice example** on the help page. Unsaved work prompts you to save or discard before switching. Saved investigations are preserved; an existing practice name receives a suffix rather than being overwritten.

## 0:24 — Define a testable hypothesis

In `hypothesis.md`, enter:

> At least 60% of radish seeds germinate within seven days under controlled conditions.

In **analysis.py → Guided analysis setup**, answer **What event are you measuring?** Define success as a visible radicle by day seven. Record the growing conditions and sampling frame before interpreting numerical results. This is a probability-estimation example, not a treatment-effect or causal model.

## 0:40 — Attach a real paper

Open **literature → Add a link**, then paste:

```text
https://doi.org/10.4236/ajps.2011.23050
```

The paper is **Influence of Pressure on Germination of Garden Cress, Leaf Mustard, and Radish Seeds at Various Temperatures**, by Akio Shimizu and Jun Kumakura (2011). Its metadata snapshot was verified against OpenAlex on October 22, 2026. You can also search OpenAlex by title or topic, inspect the abstract, and add selected results.

This paper provides context under different pressure and temperature conditions. Its observations are not the synthetic counts used in this tutorial. Loading the bundled practice scenario uses cached metadata and does not require live retrieval.

## 0:56 — Review the excerpt

Open `evidence.json`. Read the verbatim excerpt and follow the original source. The practice scenario suggests **Inconclusive** because the paper's conditions do not directly match our teaching question. Review that judgment yourself before checking **I reviewed this excerpt**.

A relationship annotation never becomes a numerical likelihood. No Bayesian calculation changes when you classify or review an excerpt.

## 1:12 — Choose starting assumptions and add data

Open `analysis.py` and follow the guided questions:

1. **What event are you measuring?** Visible radicle within seven days.
2. **Do you have observations?** Choose **I have event counts**, enter 50 total eligible observations and 34 observations with the event, and check **Synthetic / teaching observations**.
3. **What do you already know?** Choose **Little previous knowledge**. The app uses a uniform Beta(1,1) starting assumption. This is a documented assumption, not an assumption-free choice. You do not need to enter alpha, beta, or a posterior.

The app calculates **Beta(35,17)**, with mean **67.3%** and an equal-tailed 95% credible interval of **54.1%–79.2%**. These counts are invented teaching data, not extracted from the paper.

If you have no suitable quantitative observations, choose **Not yet**. Continue collecting sources, reviewing excerpts, and keeping notes. You can save and export a source-review report with numerical analysis explicitly pending. The app does not infer measurements from qualitative claims.

For an independent previous study, enter historical counts and a source, and confirm the data are comparable and do not overlap the current sample. Advanced users can choose **Specify my own assumptions** to enter custom Beta parameters and a rationale. Existing saved priors remain intact.

The interval crosses 60%. A posterior mean above 60% does not by itself confirm the hypothesis. Inspect the prior sensitivity and verify independence, event definitions, and sampling before using real data.

## 1:32 — Keep methods and limitations with the analysis

In `research-notes.md`, document the event definition, sampling design, growing conditions, prior choice, independence assumptions, and limitations. The practice scenario includes these notes as a starting point. Replace the teaching scenario with your actual protocol before collecting or interpreting real observations.

## 1:46 — Save and export

Save with the toolbar or **Ctrl/Cmd S**. Reopen named saved investigations from the project selector. In `report.md`, export **Markdown** for review or **JSON** for a structured reproducibility record. Source metadata, excerpts, annotations, observations, priors, notes, assumptions, and results remain together.

The resulting artifact is an investigation report. A finished research paper still needs appropriate scientific review, a complete methods section, and discipline-specific reporting requirements.

## Rebuilding the video

The video renderer is a development tool, not an app dependency. It uses Pillow and either an installed GStreamer with `rawvideoparse`, `videoconvert`, `x264enc`, and `mp4mux`, or the `imageio-ffmpeg` fallback:

```bash
uv pip install --python .venv/bin/python pillow imageio-ffmpeg
uv run python scripts/render_walkthrough.py
```

It reads only the bundled public paper snapshot and synthetic scenario. It does not read the local database, notes, credentials, or browser. Review chapter frames after changing the UI, then regenerate the MP4, poster, and VTT tracks together. Generated chapter-preview JPGs are written to `/tmp` for visual checks.
