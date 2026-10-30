"""Print the E0 numbers (from runs/e0/*/e0_probe.json) as markdown rows, so the report is copied from data, not typed."""
import glob, json, os
root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", "e0")
for p in sorted(glob.glob(os.path.join(root, "*", "e0_probe.json"))):
    r = json.load(open(p)); f = r["frame"]; t = f["orchestrator_step_plus_readback_ms"]
    print(f"| {os.path.basename(os.path.dirname(p))} | {t['p50']} / {t['p95']} (n={t['n']}) | mean px {f['mean_pixel']} | VRAM before/after app/after render/peak "
          f"{r['vram_mib_before_app']}/{r['vram_mib_after_app']}/{r['vram_mib_after_render']}/{r['vram_mib_peak_seen']} MiB | phys {r['physics_direct'].get('simulate_fetch_ms_per_step')} ms | "
          f"cube z {r['cube_z_after_30_updates']} | app start {r['app_start_s']} s | ext {json.dumps({k: (v['enabled_now'] if isinstance(v, dict) else v) for k, v in r['extensions'].items()})} |")
