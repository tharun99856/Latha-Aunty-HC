import random
import statistics


CLINIC_HOURS = (6 * 60, 14 * 60)
CONSULT_MEAN = 5.5
CONSULT_STDEV = 1.8
RETURN_BUFFER = 15
NOTIFY_AT_AHEAD = 3


def arrival_times(n, peak_hour=7, spread_hours=2, seed=0):
    rng = random.Random(seed)
    peak_min = peak_hour * 60
    spread = spread_hours * 60
    return sorted(int(rng.gauss(peak_min, spread / 2.5)) for _ in range(n))


def baseline(arrivals):
    consult_start = max(arrivals[0], 9 * 60)
    waits = []
    served_at = []
    for arr in arrivals:
        start = max(arr, consult_start)
        duration = max(1, int(random.gauss(CONSULT_MEAN, CONSULT_STDEV)))
        waits.append(start - arr)
        served_at.append(start + duration)
        consult_start = start + duration
    return waits, served_at


def with_queue_system(arrivals, adoption_pct):
    consult_start = max(arrivals[0], 9 * 60)
    physical_waits = []
    served_at = []
    for i, arr in enumerate(arrivals):
        start = max(arr, consult_start)
        duration = max(1, int(random.gauss(CONSULT_MEAN, CONSULT_STDEV)))

        trusts_estimate = random.random() < adoption_pct
        if trusts_estimate and i >= NOTIFY_AT_AHEAD:
            return_anchor = served_at[i - NOTIFY_AT_AHEAD] if i - NOTIFY_AT_AHEAD < len(served_at) else start
            physical_arrival = max(arr, return_anchor - RETURN_BUFFER)
            physical_wait = max(0, start - physical_arrival)
        else:
            physical_wait = start - arr

        physical_waits.append(physical_wait)
        served_at.append(start + duration)
        consult_start = start + duration
    return physical_waits, served_at


def in_clinic_count_at(t, arrivals, served_at, return_times=None):
    count = 0
    arrival_data = return_times if return_times else arrivals
    for arr, served in zip(arrival_data, served_at):
        if arr <= t <= served:
            count += 1
    return count


def peak_occupancy(arrivals, served_at, return_times=None):
    samples = range(min(arrivals), max(served_at) + 1, 5)
    return max(in_clinic_count_at(t, arrivals, served_at, return_times) for t in samples)


def return_times_for(arrivals, served_at, adoption_pct, seed):
    rng = random.Random(seed + 99)
    returns = []
    for i, arr in enumerate(arrivals):
        trusts_estimate = rng.random() < adoption_pct
        if trusts_estimate and i >= NOTIFY_AT_AHEAD:
            return_anchor = served_at[i - NOTIFY_AT_AHEAD]
            returns.append(max(arr, return_anchor - RETURN_BUFFER))
        else:
            returns.append(arr)
    return returns


def fmt(minutes):
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m:02d}m"


def run(n_patients=100, adoption_pct=0.75, seed=42):
    random.seed(seed)
    arrivals = arrival_times(n_patients, seed=seed)

    random.seed(seed)
    base_waits, base_served = baseline(arrivals)
    base_peak = peak_occupancy(arrivals, base_served)

    random.seed(seed)
    new_waits, new_served = with_queue_system(arrivals, adoption_pct)
    new_returns = return_times_for(arrivals, new_served, adoption_pct, seed)
    new_peak = peak_occupancy(arrivals, new_served, new_returns)

    return {
        "n": n_patients,
        "adoption_pct": adoption_pct,
        "baseline_avg_wait": statistics.mean(base_waits),
        "baseline_p90_wait": sorted(base_waits)[int(0.9 * len(base_waits))],
        "baseline_peak_occupancy": base_peak,
        "new_avg_wait": statistics.mean(new_waits),
        "new_p90_wait": sorted(new_waits)[int(0.9 * len(new_waits))],
        "new_peak_occupancy": new_peak,
        "reduction_pct": (1 - statistics.mean(new_waits) / statistics.mean(base_waits)) * 100,
    }


def main():
    print("=" * 60)
    print(" PHC QUEUE - Throughput Simulation")
    print("=" * 60)
    print()
    print(" Model assumptions:")
    print(f"   - Single doctor, OPD 9 AM to 2 PM")
    print(f"   - Consultation: {CONSULT_MEAN} min mean (+/- {CONSULT_STDEV})")
    print(f"   - Patients arrive between 6:30 - 8:30 AM (peak ~7 AM)")
    print(f"   - Patients trusting the estimate return ~{RETURN_BUFFER} min before slot")
    print(f"   - Trust window: when 3 patients are ahead")
    print()

    runs = []
    for seed in range(1, 11):
        runs.append(run(n_patients=100, adoption_pct=0.75, seed=seed))

    avg_baseline = statistics.mean(r["baseline_avg_wait"] for r in runs)
    avg_new = statistics.mean(r["new_avg_wait"] for r in runs)
    avg_baseline_peak = statistics.mean(r["baseline_peak_occupancy"] for r in runs)
    avg_new_peak = statistics.mean(r["new_peak_occupancy"] for r in runs)
    avg_reduction = statistics.mean(r["reduction_pct"] for r in runs)

    print(" Results (10 runs x 100 patients x 75% trust adoption):")
    print(" " + "-" * 58)
    print(f"   Average physical wait time")
    print(f"     Baseline (status quo):     {fmt(avg_baseline)}")
    print(f"     With queue system:         {fmt(avg_new)}")
    print(f"     Reduction:                 {avg_reduction:.1f}%")
    print()
    print(f"   Peak waiting room occupancy")
    print(f"     Baseline:                  {avg_baseline_peak:.0f} patients")
    print(f"     With queue system:         {avg_new_peak:.0f} patients")
    print(f"     Reduction:                 {(1 - avg_new_peak/avg_baseline_peak)*100:.1f}%")
    print()

    print(" Sensitivity to patient-trust adoption rate:")
    print(" " + "-" * 58)
    for pct in (0.3, 0.5, 0.7, 0.9):
        results = [run(n_patients=100, adoption_pct=pct, seed=s)["reduction_pct"] for s in range(1, 6)]
        print(f"   {int(pct*100)}% adoption -> {statistics.mean(results):.1f}% wait reduction")
    print()
    print(" Target met: " + ("YES" if avg_reduction >= 30 else "NO") + f" (target: >=30% reduction)")
    print()
    print(" Note: V1 ships with printed-token estimates and stored phone numbers.")
    print(" V2 roadmap: automated WhatsApp / SMS notifications to lift adoption further.")
    print()


if __name__ == "__main__":
    main()
