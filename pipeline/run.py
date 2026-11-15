import argparse
import pathlib
import subprocess
import sys

from pipeline.db import connect

SKIPPED_EXIT = 75
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "pipeline" / "logs"


def status_for(exit_code: int) -> str:
    return {0: "done", SKIPPED_EXIT: "skipped"}.get(exit_code, "failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job")
    parser.add_argument("--trigger", default="cron", choices=["cron", "admin", "auto"])
    parser.add_argument("--run-id", type=int)
    opts, job_args = parser.parse_known_args()

    LOG_DIR.mkdir(exist_ok=True)
    with connect() as conn:
        if opts.run_id is None:
            (run_id,) = conn.execute(
                "INSERT INTO job_runs (job, args, trigger) VALUES (%s, %s, %s) RETURNING id",
                (opts.job.removeprefix("jobs."), " ".join(job_args), opts.trigger),
            ).fetchone()
        else:
            run_id = opts.run_id
        log_path = LOG_DIR / f"{run_id}.log"
        conn.execute("UPDATE job_runs SET log_path = %s WHERE id = %s", (str(log_path), run_id))

    last_line = ""
    with open(log_path, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, "-u", "-m", f"pipeline.{opts.job}", *job_args],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=REPO_ROOT,
        )
        for line in proc.stdout:
            log.write(line)
            log.flush()
            sys.stdout.write(line)
            if line.strip():
                last_line = line.strip()
        code = proc.wait()

    with connect() as conn:
        conn.execute(
            "UPDATE job_runs SET status = %s, finished_at = now(), summary = %s WHERE id = %s",
            (status_for(code), last_line[:500], run_id),
        )
    sys.exit(code)


if __name__ == "__main__":
    main()
