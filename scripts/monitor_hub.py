"""Print one-second Linux host and AChPrak process samples as CSV.

Run on the Hub host through SSH. RSS is the sum of process resident sets and may
double-count shared memory; MemAvailable and swap are host-wide kernel values.
"""

import csv
from datetime import datetime, timezone
import subprocess
import sys
import time


def read_cpu():
    fields = [int(value) for value in open("/proc/stat").readline().split()[1:]]
    return sum(fields), fields[3] + fields[4]


def read_memory():
    values = {}
    with open("/proc/meminfo") as handle:
        for line in handle:
            key, value = line.split(":", 1)
            if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
                values[key] = int(value.split()[0])
    return values


def read_processes():
    output = subprocess.check_output(
        ["ps", "-eo", "rss=,args="], universal_newlines=True
    )
    counts = {"proxy": 0, "app": 0, "worker": 0, "mopac": 0}
    rss = {key: 0 for key in counts}
    for line in output.splitlines():
        try:
            memory, command = line.strip().split(None, 1)
        except ValueError:
            continue
        if "jupyter-standaloneproxy" in command:
            key = "proxy"
        elif "-m achprak.web.worker" in command:
            key = "worker"
        elif "-m achprak.web" in command:
            key = "app"
        elif "mopac" in command.lower() and "grep" not in command:
            key = "mopac"
        else:
            continue
        counts[key] += 1
        rss[key] += int(memory)
    return counts, rss


def main():
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        [
            "utc",
            "cpu_busy_pct",
            "mem_available_mib",
            "swap_used_mib",
            "proxy_count",
            "app_count",
            "worker_count",
            "mopac_count",
            "proxy_rss_mib",
            "app_rss_mib",
            "worker_rss_mib",
            "mopac_rss_mib",
        ]
    )
    previous_total, previous_idle = read_cpu()
    while True:
        time.sleep(1)
        total, idle = read_cpu()
        cpu = 100 * (1 - (idle - previous_idle) / max(total - previous_total, 1))
        previous_total, previous_idle = total, idle
        memory = read_memory()
        counts, rss = read_processes()
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                round(cpu, 2),
                round(memory["MemAvailable"] / 1024, 1),
                round((memory["SwapTotal"] - memory["SwapFree"]) / 1024, 1),
                *(counts[key] for key in ("proxy", "app", "worker", "mopac")),
                *(round(rss[key] / 1024, 1) for key in ("proxy", "app", "worker", "mopac")),
            ]
        )
        sys.stdout.flush()


if __name__ == "__main__":
    main()
