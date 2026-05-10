"""
MDSM-Lite Launcher
Umístění: C:\\Users\\stava\\Projects\\launcher.py

Spuštění: dvojklik na start.bat
"""

import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

# ── Konfigurace cest ────────────────────────────────────────────────────────────

BASE = Path(__file__).resolve().parent

MDSM_PATH         = BASE / "MDSM-Lite"
UNIVERSE_MGR_PATH = BASE / "UniverseManager"

# ── Registr modulů ──────────────────────────────────────────────────────────────
# Přidej nový modul sem když ho vytvoříš.
# Modul se zobrazí v menu pouze pokud adresář fyzicky existuje.

MODULES = {
    "sector_rank_calendar": {
        "module_path": BASE / "sector_rank_calendar",
        "label":       "SectorRankCalendar",
        "conda_env":   "sector_rank_calendar",
        "entry_point": "sector_rank.py",
    },
    "sector_internals_rank_calendar": {
        "module_path": BASE / "sector_internals_rank_calendar",
        "label":       "SectorInternalsRankCalendar",
        "conda_env":   "sector_internals_rank_calendar",
        "entry_point": "main.py",
    },
}

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


def ask_date(prompt: str) -> str:
    """Zeptá se na datum ve formátu DD-MM-YYYY. Převede na YYYY-MM-DD pro program."""
    while True:
        val = input(prompt).strip()
        try:
            d = datetime.strptime(val, "%d-%m-%Y")
            return d.strftime("%Y-%m-%d")
        except ValueError:
            print("  Neplatný formát. Zadej datum jako DD-MM-YYYY (např. 02-01-2025).")

LOOKBACKS_PER_MODULE = {
    "sector_rank_calendar":          ("1", "5", "10", "20", "30"),
    "sector_internals_rank_calendar": ("1", "5", "10", "20", "30", "50"),
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

def run_mdsm_only(module_name: str, module_path: Path) -> None:
    """Spustí pouze Data Collector pro daný modul."""
    universe_csv = MDSM_PATH / "data" / "universe" / f"{module_name}_universe.csv"

    if not universe_csv.exists():
        print(f"\n[CHYBA] Universe CSV nenalezeno: {universe_csv}")
        print("Nejdřív spusť variantu 2 (UniverseManager + MDSM-Lite).")
        return

    # Volitelné datum rozsahu
    print("\nZadej rozsah dat (Enter = použij výchozí hodnoty):\n")
    start_str = ask_date_optional("Start date (DD-MM-YYYY, Enter = default 2018-06-19): ")
    end_str   = ask_date_optional("End date   (DD-MM-YYYY, Enter = dnes):               ")

    cmd = [
        "python", "src/collector/data_collector.py",
        "--universe-path", str(universe_csv),
        "--module-name", module_name,
    ]
    if start_str:
        cmd += ["--start-date", start_str]
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
    """Spustí analytický modul s interaktivním zadáním parametrů."""
    module_path = cfg["module_path"]
    entry_point = cfg["entry_point"]
    conda_env   = cfg["conda_env"]

    print(f"\n>>> {cfg['label']}")
    print("Zadej parametry:\n")
    DEFAULT_FROM = {
        "sector_rank_calendar":           "2018-09-01",
        "sector_internals_rank_calendar":  "2026-02-01",
    }
    default_from  = DEFAULT_FROM.get(module_name, datetime.now().strftime("%Y-%m-01"))
    from_date_str = ask_date_optional(f"Od kdy? (DD-MM-YYYY, Enter = {default_from}): ")
    from_date     = from_date_str if from_date_str else default_from

    to_date_str = ask_date_optional("Do kdy?  (DD-MM-YYYY, Enter = dnes):       ")
    to_date     = to_date_str if to_date_str else datetime.now().strftime("%Y-%m-%d")
    lookback  = ask_lookback(module_name)

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

        print("  1. Spustit MDSM-Lite                           (stáhne nová tržní data)")
        print("  2. Spustit s UniverseManager                   (aktualizuje tickery a stáhne data)")
        for i, (key, cfg) in enumerate(available, 3):
            label = cfg["label"]
            print(f"  {i}. Spustit modul {label:<30} (zobrazí ranking)")
        print("  0. Konec")
        separator()

        max_choice = 2 + len(available)
        choice = input(f"Vyber (0-{max_choice}): ").strip()

        if choice == "0":
            print("Konec.")
            sys.exit(0)

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
            print(f"Neplatná volba. Zadej 0–{max_choice}.")


if __name__ == "__main__":
    main()
