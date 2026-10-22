import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="full", app_title="Hypothesis Lab", css_file="src/hypothesis_lab/ui/theme.css"
)


@app.cell
def _():
    import marimo as mo
    from hypothesis_lab.ui.widget import ResearchWorkspace

    return ResearchWorkspace, mo


@app.cell
def _(ResearchWorkspace, mo):
    workspace = mo.ui.anywidget(
        ResearchWorkspace(fullscreen=mo.app_meta().mode == "run")
    )
    workspace
    return (workspace,)


if __name__ == "__main__":
    app.run()
