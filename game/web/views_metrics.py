"""
Prometheus metrics endpoint for DorfinMUD.

Serves /metrics in Prometheus text exposition format. No authentication
required — intended for cluster-internal scraping only.
"""

import time

from django.http import HttpResponse


def metrics_view(request):
    """Return Prometheus text-format metrics."""
    lines = []

    def gauge(name, value, help_text, labels=None):
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
            lines.append(f"{name}{{{label_str}}} {value}")
        else:
            lines.append(f"{name} {value}")

    # --- Server uptime and runtime ---
    try:
        from evennia.utils import gametime

        gauge("evennia_uptime_seconds", int(gametime.uptime()),
              "Seconds since last server reload")
        gauge("evennia_runtime_seconds", int(gametime.runtime()),
              "Cumulative server runtime in seconds")
    except Exception:
        pass

    # --- Connected players ---
    try:
        from evennia.server.sessionhandler import SESSION_HANDLER

        gauge("evennia_sessions_total", SESSION_HANDLER.count_loggedin(),
              "Number of logged-in sessions")
        gauge("evennia_accounts_connected", SESSION_HANDLER.account_count(),
              "Number of unique connected accounts")
    except Exception:
        pass

    # --- Database object counts ---
    try:
        from evennia.objects.models import ObjectDB
        from evennia.accounts.models import AccountDB
        from evennia.scripts.models import ScriptDB

        gauge("evennia_accounts_total", AccountDB.objects.count(),
              "Total registered accounts")
        gauge("evennia_objects_total", ObjectDB.objects.count(),
              "Total objects in database")
        gauge("evennia_scripts_total", ScriptDB.objects.count(),
              "Total scripts in database")
    except Exception:
        pass

    # --- Object type breakdown ---
    try:
        from evennia.objects.models import ObjectDB

        type_counts = {}
        for obj in ObjectDB.objects.all().iterator():
            tpath = obj.db_typeclass_path or "unknown"
            short = tpath.rsplit(".", 1)[-1] if "." in tpath else tpath
            type_counts[short] = type_counts.get(short, 0) + 1

        lines.append("# HELP evennia_objects_by_type Object count by typeclass")
        lines.append("# TYPE evennia_objects_by_type gauge")
        for tname, count in sorted(type_counts.items()):
            lines.append(f'evennia_objects_by_type{{typeclass="{tname}"}} {count}')
    except Exception:
        pass

    # --- Active combat handlers ---
    try:
        from evennia.scripts.models import ScriptDB

        combat_handlers = ScriptDB.objects.filter(
            db_typeclass_path__contains="CombatHandler"
        ).count()
        gauge("evennia_combat_handlers_active", combat_handlers,
              "Number of active combat handler scripts")
    except Exception:
        pass

    # --- Memory usage (if psutil available) ---
    try:
        import os
        import psutil

        proc = psutil.Process(os.getpid())
        mem = proc.memory_info()
        gauge("evennia_memory_rss_bytes", mem.rss,
              "Resident set size in bytes")
        gauge("evennia_memory_vms_bytes", mem.vms,
              "Virtual memory size in bytes")
        gauge("evennia_cpu_percent", proc.cpu_percent(interval=0),
              "CPU usage percent")
    except ImportError:
        pass

    # --- Health flag (always 1 if we got here) ---
    gauge("evennia_up", 1, "Whether the Evennia server is responding")

    body = "\n".join(lines) + "\n"
    return HttpResponse(body, content_type="text/plain; version=0.0.4; charset=utf-8")
