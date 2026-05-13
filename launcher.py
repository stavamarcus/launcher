"""
MDSM-Lite Launcher
Umístění: C:\\Users\\stava\\Projects\\launcher.py

Spuštění: dvojklik na start.bat
"""

import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Konfigurace cest ────────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent

MDSM_PATH         = BASE / "MDSM-Lite"
UNIVERSE_MGR_PATH = BASE / "UniverseManager"

# ── Registr modulů ──────────────────────────────────────────────────────────────
# Přidej nový modul sem když ho vytvoříš.
# Modul se zobrazí v menu pouze pokud adresář fyzicky existuje.
#
# no_params: True = modul se spustí bez jakýchkoliv CLI parametrů

MODULES = {
    "sector_rank_calendar": {
        "module_path": BASE / "sector_rank_calendar",
        "label":       "SectorRankCalendar",
        "conda_env":   "sector_rank_calendar",
        "entry_point": "sector_rank.py",
        "no_params":   False,
    },
    "sector_internals_rank_calendar": {
        "module_path": BASE / "sector_internals_rank_calendar",
        "label":       "SectorInternalsRankCalendar",
        "conda_env":   "sector_internals_rank_calendar",
        "entry_point": "main.py",
        "no_params":   False,
    },
    "market_breadth": {
        "module_path": BASE / "market_breadth",
        "label":       "MarketBreadth",
        "conda_env":   "market_breadth",
        "entry_point": "main.py",
        "no_params":   True,
    },
    "sp500_rank_calendar": {
        "module_path": BASE / "sp500_rank_calendar",
        "label":       "SP500RankCalendar",
        "conda_env":   "sp500_rank_calendar",
        "entry_point": "main.py",
        "no_params":   False,
    },
}

# ── Per-modul default start date pro Data Collector ─────────────────────────────
# "dynamic:N" = dnes - N kalendářních dní (počítáno za běhu)
# "YYYY-MM-DD" = pevné datum

MODULE_DEFAULT_START = {
    "market_breadth":     "dynamic:550",
    "sp500_rank_calendar": "dynamic:180",
}
GLOBAL_DEFAULT_START = "2018-06-19"

# ── Conda prostředí ─────────────────────────────────────────────────────────────

CONDA_ENV_MDSM    = "mdsm"
CONDA_ENV_UNIVMGR = "universe_manager"

# ── Helpers ─────────────────────────────────────────────────────────────────────

def separator():
    print("=" * 85)

def get_available_modules() -> list:
    """Vrátí pouze moduly jejichž adresář fyzicky existuje."""
    return [
        (key, cfg) for key, cfg in MODULES.items()
        if cfg["module_path"].exists()
    ]

def run_cmd(cmd: list, cwd: Path, conda_env: str) -> int:
    """Spustí příkaz v daném conda prostředí a adresáři."""
    full_cmd = ["conda", "run", "-n", conda_env, "--no-capture-output"] + cmd
    print(f"\n[CMD] {' '.join(str(c) for c in full_cmd)}")
    print(f"[CWD] {cwd}\n")
    result = subprocess.run(full_cmd, cwd=str(cwd))
    return result.returncode

def select_module(available: list) -> tuple | None:
    """Zobrazí seznam dostupných modulů a nechá uživatele vybrat."""
    if len(available) == 1:
        return available[0]

    print("\nDostupné moduly:")
    for i, (key, cfg) in enumerate(available, 1):
        print(f"  {i}. {cfg['label']}")
    print("  0. Zpět")

    while True:
        try:
            choice = int(input("\nVyber modul: ").strip())
        except ValueError:
            print("Zadej číslo.")
            continue
        if choice == 0:
            return None
        if 1 <= choice <= len(available):
            return available[choice - 1]
        print("Neplatná volba.")

def resolve_default_start(module_name: str) -> str:
    """
    Vrátí default start date pro daný modul jako YYYY-MM-DD string.
    Podporuje dynamické hodnoty (dynamic:N = dnes - N dní).
    """
    raw = MODULE_DEFAULT_START.get(module_name, GLOBAL_DEFAULT_START)
    if raw.startswith("dynamic:"):
        days = int(raw.split(":")[1])
        return (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    return raw

def ask_date_optional(prompt: str) -> str | None:
    """
    Zeptá se na datum ve formátu DD-MM-YYYY.
    Enter = None (použij default).
    Převede na YYYY-MM-DD pro CLI.
    """
    while True:
        val = input(prompt).strip()
        if val == "":
            return None
        try:
            d = datetime.strptime(val, "%d-%m-%Y")
            return d.strftime("%Y-%m-%d")
        except ValueError:
            print("  Neplatný formát. Zadej DD-MM-YYYY (např. 01-01-2016) nebo Enter.")


def ask_date_optional_yyyymmdd(prompt: str) -> str | None:
    """Enter = None. Přijímá YYYY-MM-DD formát."""
    while True:
        val = input(prompt).strip()
        if val == "":
            return None
        try:
            date.fromisoformat(val)
            return val
        except ValueError:
            print("  Neplatný formát. Zadej YYYY-MM-DD nebo Enter.")


def ask_date(prompt: str) -> str:
    """Zeptá se na datum ve formátu DD-MM-YYYY. Převede na YYYY-MM-DD pro program."""
    while True:
        val = input(prompt).strip()
        try:
            d = datetime.strptime(val, "%d-%m-%Y")
            return d.strftime("%Y-%m-%d")
        except ValueError:
            print("  Neplatný formát. Zadej datum jako DD-MM-YYYY (např. 02-01-2025).")

# Minimální start_date garantovaný GDU pro každý modul (musí odpovídat start_days v GDU).
# Pokud uživatel zadá starší datum, launcher zobrazí varování.
GDU_GUARANTEED_START = {
    "sector_rank_calendar":           date(2018, 8, 27),   # 2800 dní
    "sector_internals_rank_calendar": date.today() - timedelta(days=180),
    "sp500_rank_calendar":            date.today() - timedelta(days=180),
    "market_breadth":                 date.today() - timedelta(days=550),
}

LOOKBACKS_PER_MODULE = {
    "sector_rank_calendar":          ("1", "5", "10", "20", "30"),
    "sector_internals_rank_calendar": ("1", "5", "10", "20", "30", "50"),
    "sp500_rank_calendar":           ("1", "5", "10", "20", "30", "50"),
}

def ask_lookback(module_name: str = "") -> str:
    """Zeptá se na lookback. Povolené hodnoty závisí na modulu."""
    valid  = LOOKBACKS_PER_MODULE.get(module_name, ("1", "5", "20"))
    prompt = "/".join(valid)
    while True:
        val = input(f"Lookback ({prompt}): ").strip()
        if val in valid:
            return val
        print(f"  Neplatná volba. Zadej {prompt}.")

# ── Akce ────────────────────────────────────────────────────────────────────────

def run_global_daily_update(force_refresh: bool = False) -> None:
    """Spustí Global Daily Update Manager pro všechny moduly najednou."""
    print("\n>>> Global Daily Update Manager")
    print("    Aktualizuje cache pro všechny moduly (513 unikátních conidů).")
    print("    Každý ticker stažen pouze jednou.\n")

    if force_refresh:
        confirm = input("  --force-refresh: stáhne VŠECHNA data znovu. Pokračovat? (ano/ne): ").strip().lower()
        if confirm != "ano":
            print("  Zrušeno.")
            return

    cmd = ["python", "src/collector/global_daily_update.py"]
    if force_refresh:
        cmd.append("--force-refresh")

    rc = run_cmd(cmd, cwd=MDSM_PATH, conda_env=CONDA_ENV_MDSM)

    if rc == 0:
        print("\n[OK] Global Daily Update dokončen.")
    else:
        print(f"\n[CHYBA] Global Daily Update skončil s chybou (kód {rc}).")


def run_mdsm_only(module_name: str, module_path: Path) -> None:
    """Spustí pouze Data Collector pro daný modul."""
    universe_csv = MDSM_PATH / "data" / "universe" / f"{module_name}_universe.csv"

    if not universe_csv.exists():
        print(f"\n[CHYBA] Universe CSV nenalezeno: {universe_csv}")
        print("Nejdřív spusť variantu 2 (UniverseManager + MDSM-Lite).")
        return

    default_start = resolve_default_start(module_name)

    print("\nZadej rozsah dat (Enter = použij výchozí hodnoty):\n")
    start_str = ask_date_optional(f"Start date (DD-MM-YYYY, Enter = {default_start}): ")
    end_str   = ask_date_optional("End date   (DD-MM-YYYY, Enter = dnes):             ")

    if not start_str:
        start_str = default_start

    cmd = [
        "python", "src/collector/data_collector.py",
        "--universe-path", str(universe_csv),
        "--module-name", module_name,
        "--start-date", start_str,
    ]
    if end_str:
        cmd += ["--end-date", end_str]

    print(f"\n>>> Data Collector — {module_name}")
    rc = run_cmd(cmd, cwd=MDSM_PATH, conda_env=CONDA_ENV_MDSM)

    if rc == 0:
        print("\n[OK] Data Collector dokončen.")
    else:
        print(f"\n[CHYBA] Data Collector skončil s chybou (kód {rc}).")


def run_universe_then_mdsm(module_name: str, module_path: Path) -> None:
    """Spustí UniverseManager a pak Data Collector."""
    raw_tickers = module_path / "module_raw_tickers.csv"
    if not raw_tickers.exists():
        print(f"\n[CHYBA] Soubor nenalezen: {raw_tickers}")
        print("Vytvoř module_raw_tickers.csv v adresáři modulu.")
        return

    print(f"\n>>> UniverseManager — {module_name}")
    rc = run_cmd(
        [
            "python", "run_universe_manager_normal.py",
            "--module-path", str(module_path),
            "--mdsm-path",   str(MDSM_PATH),
            "--module-name", module_name,
        ],
        cwd=UNIVERSE_MGR_PATH,
        conda_env=CONDA_ENV_UNIVMGR,
    )

    if rc != 0:
        print(f"\n[CHYBA] UniverseManager skončil s chybou (kód {rc}).")
        print("Data Collector nebude spuštěn.")
        return

    print("\n[OK] UniverseManager dokončen.")
    run_mdsm_only(module_name, module_path)


def run_analytical_module(module_name: str, cfg: dict) -> None:
    """Spustí analytický modul."""
    module_path = cfg["module_path"]
    entry_point = cfg["entry_point"]
    conda_env   = cfg["conda_env"]
    no_params   = cfg.get("no_params", False)

    print(f"\n>>> {cfg['label']}")

    if no_params:
        rc = run_cmd(
            ["python", entry_point],
            cwd=module_path,
            conda_env=conda_env,
        )
    else:
        print("Zadej parametry:\n")
        DEFAULT_FROM = {
            "sector_rank_calendar":           "2018-09-01",
            "sector_internals_rank_calendar":  "2026-02-01",
            "sp500_rank_calendar":             (date.today() - timedelta(days=90)).strftime("%Y-%m-%d"),
        }
        default_from  = DEFAULT_FROM.get(module_name, datetime.now().strftime("%Y-%m-01"))
        from_date_str = ask_date_optional(f"Od kdy? (DD-MM-YYYY, Enter = {default_from}): ")
        from_date     = from_date_str if from_date_str else default_from

        # Varování pokud requested start_date je starší než GDU garantuje
        guaranteed = GDU_GUARANTEED_START.get(module_name)
        try:
            requested_dt = date.fromisoformat(from_date)
            if guaranteed and requested_dt < guaranteed:
                print(f"\n  [VAROVÁNÍ] Požadovaný start ({from_date}) je starší než GDU garantuje ({guaranteed}).")
                print(f"             Cache nemusí pokrývat celý rozsah → modul selže s insufficient_cache.")
                print(f"             Řešení: spusť volbu 1 (MDSM-Lite) s --start-date {from_date} a --force-refresh.")
                confirm = input("  Pokračovat přesto? (ano/ne): ").strip().lower()
                if confirm != "ano":
                    return
        except ValueError:
            pass

        to_date_str = ask_date_optional("Do kdy?  (DD-MM-YYYY, Enter = dnes):       ")
        to_date     = to_date_str if to_date_str else datetime.now().strftime("%Y-%m-%d")
        lookback    = ask_lookback(module_name)

        rc = run_cmd(
            [
                "python", entry_point,
                "-f", from_date,
                "-t", to_date,
                "--lookback", lookback,
            ],
            cwd=module_path,
            conda_env=conda_env,
        )

    if rc != 0:
        print(f"\n[CHYBA] {cfg['label']} skončil s chybou (kód {rc}).")


# ── Hlavní menu ─────────────────────────────────────────────────────────────────

def main():
    while True:
        separator()
        print("MDSM-Lite Launcher".center(85))
        separator()

        available = get_available_modules()

        if not available:
            print("\n  Žádný modul nenalezen.")
            print("  Vytvoř adresář modulu v:")
            print(f"  {BASE}")
            print("\n  Moduly registrované v konfiguraci:")
            for key, cfg in MODULES.items():
                print(f"    - {cfg['label']} ({cfg['module_path']})")
            separator()
            input("\nStiskni Enter pro konec...")
            sys.exit(0)

        print("  G. Global Daily Update                         (aktualizuje cache pro všechny moduly)")
        print("  1. Spustit MDSM-Lite                           (stáhne nová tržní data – jeden modul)")
        print("  2. Spustit s UniverseManager                   (aktualizuje tickery a stáhne data)")
        for i, (key, cfg) in enumerate(available, 3):
            label = cfg["label"]
            print(f"  {i}. Spustit modul {label:<30} (zobrazí ranking)")
        print("  0. Konec")
        separator()

        max_choice = 2 + len(available)
        choice = input(f"Vyber (G / 0-{max_choice}): ").strip().upper()

        if choice == "0":
            print("Konec.")
            sys.exit(0)

        elif choice == "G":
            print("\n  a. Standardní update (pouze chybějící bary)")
            print("  b. Force refresh (stáhne vše znovu)")
            print("  0. Zpět")
            sub = input("\nVolba: ").strip().lower()
            if sub == "a":
                run_global_daily_update(force_refresh=False)
            elif sub == "b":
                run_global_daily_update(force_refresh=True)
            input("\nStiskni Enter pro návrat do menu...")

        elif choice in ("1", "2"):
            selected = select_module(available)
            if selected is None:
                continue
            module_name, cfg = selected
            module_path = cfg["module_path"]
            if choice == "1":
                run_mdsm_only(module_name, module_path)
            else:
                run_universe_then_mdsm(module_name, module_path)
            input("\nStiskni Enter pro návrat do menu...")

        elif choice.isdigit() and 3 <= int(choice) <= max_choice:
            idx = int(choice) - 3
            module_name, cfg = available[idx]
            run_analytical_module(module_name, cfg)
            input("\nStiskni Enter pro návrat do menu...")

        else:
            print(f"Neplatná volba. Zadej G nebo 0–{max_choice}.")


if __name__ == "__main__":
    main()
