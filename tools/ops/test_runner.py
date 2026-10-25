"""Tests for tools/ops/runner.py.  Run: python3 -P -m pytest tools/ops -q   (or: python3 -P tools/ops/test_runner.py)"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["OPS_RUNNER_NO_LEDGER"] = "1"
import runner  # noqa: E402

WF = """
name: t
on:
  workflow_dispatch:
    inputs:
      flag: {type: boolean, default: false}
      word: {default: "hi"}
jobs:
  a:
    runs-on: ubuntu-latest
    env: {JOBVAR: job}
    steps:
      - uses: actions/checkout@v4
      - id: one
        run: |
          echo "go=yes" >> "$GITHUB_OUTPUT"
          echo "FROM_ENV=carried" >> "$GITHUB_ENV"
          echo "${{ inputs.word }}|$JOBVAR|${{ secrets.T_SECRET }}" > "$OUT/one.txt"
      - if: steps.one.outputs.go == 'yes'
        run: echo "$FROM_ENV|${{ inputs.flag && 'F' || 'nf' }}" > "$OUT/two.txt"
      - name: soft failure
        continue-on-error: true
        run: exit 3
      - name: still runs
        run: touch "$OUT/three.txt"
      - name: hard failure
        run: exit 1
      - name: skipped after failure
        run: touch "$OUT/never.txt"
      - name: cleanup
        if: always()
        run: touch "$OUT/always.txt"
      - name: only on failure
        if: failure()
        run: touch "$OUT/failure.txt"
  b:
    needs: a
    runs-on: ubuntu-latest
    steps:
      - run: touch "$OUT/b.txt"
"""


def _run(**kw):
    d = Path(tempfile.mkdtemp())
    f = d / "t.yml"
    f.write_text(WF)
    os.environ["OUT"] = str(d)
    os.environ["T_SECRET"] = "s3cret"
    rc = runner.run_workflow(str(f), log=lambda *_: None, **kw)
    return rc, d


def test_semantics():
    rc, d = _run(given={"word": "yo", "flag": "true"})
    assert rc == 1                                   # a hard failure fails the run
    assert (d / "one.txt").read_text().strip() == "yo|job|s3cret"
    assert (d / "two.txt").read_text().strip() == "carried|F"   # GITHUB_OUTPUT, GITHUB_ENV, boolean input
    assert (d / "three.txt").exists()                # continue-on-error doesn't stop the job
    assert not (d / "never.txt").exists()            # steps after a failure are skipped
    assert (d / "always.txt").exists() and (d / "failure.txt").exists()
    assert not (d / "b.txt").exists()                # job b (needs a) is skipped because a failed, like GitHub


def test_defaults():
    rc, d = _run()
    assert (d / "one.txt").read_text().strip() == "hi|job|s3cret"
    assert (d / "two.txt").read_text().strip() == "carried|nf"


def test_expressions():
    ctx = runner.Ctx(github=runner.Ctx(event=runner.Ctx(schedule="40 9 * * 0"), ref_name="renders/x"),
                     inputs=runner.Ctx(slot="", path="a"))
    st = {"failed": False}
    e = "github.event.schedule == '40 9 * * 0' && '21:30' || inputs.slot || '18:30'"
    assert runner.evaluate(e, ctx, st) == "21:30"
    assert runner.condition("inputs.path != '' && startsWith(github.ref_name, 'renders/')", ctx, st) is True
    assert runner.condition("always()", ctx, {"failed": True}) is True
    assert runner.condition("inputs.path == ''", ctx, st) is False
    assert runner.render("x ${{ inputs.missing || 'd' }} y", ctx, st) == "x d y"


def test_every_workflow_parses():
    for name, status in runner.check_all():
        if status == "ok":
            assert runner.run_workflow(name, plan_only=True, log=lambda *_: None) == 0, name


if __name__ == "__main__":
    for t in (test_semantics, test_defaults, test_expressions, test_every_workflow_parses):
        t()
        print("ok", t.__name__)
