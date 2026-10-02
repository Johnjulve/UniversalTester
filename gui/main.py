"""
Modern, Cross-Platform Desktop GUI for UniversalTester (testx).
Built with CustomTkinter for sleek dark/light mode themes, responsive widgets, and live log streaming.
"""
import os
import sys
import io
import queue
import time
from typing import Optional, Dict, Any, List

# Fallback for windowed/noconsole PyInstaller executables where sys.stdout is None
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENDOR_DIR = os.path.join(_ROOT_DIR, "vendor")
if os.path.exists(_VENDOR_DIR) and _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

_IMPORT_ERROR: Optional[str] = None
try:
    import customtkinter as ctk
    from tkinter import filedialog
    HAS_CTK = True
except Exception as e:
    HAS_CTK = False
    _IMPORT_ERROR = str(e)

from core.service import TesterService
from core.models import RunRequest, RunResult
from core.events import ProgressEvent
from core.ui import get_session_memory_mb
from adapters.base import Capability
from gui.worker import AsyncTestRunner
from cli.interactive import load_config


if HAS_CTK:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class UniversalTesterApp(ctk.CTk):
        """Modern CustomTkinter desktop interface for UniversalTester."""

        def __init__(self, service: Optional[TesterService] = None):
            super().__init__()
            if sys.platform == "win32" and getattr(sys, "frozen", False):
                try:
                    import ctypes
                    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                    if hwnd:
                        ctypes.windll.user32.ShowWindow(hwnd, 0)
                except Exception:
                    pass

            self.service = service or TesterService()
            self.runner = AsyncTestRunner(self.service)
            self.event_queue: queue.Queue = queue.Queue()
            self.config = load_config(_ROOT_DIR)

            self.title("⚡ UniversalTester v2.0.1 (testx) — Quality & Benchmark Engine")
            self.geometry("1060x700")
            self.minsize(920, 600)

            self.project_path_var = ctk.StringVar(value=os.getcwd())
            self.active_test_var = ctk.StringVar(value="Active Test: Full Assessment (All 5 Pillars)")
            self.status_var = ctk.StringVar(value="● READY")
            self.step_var = ctk.StringVar(value="Select a testing capability and click 'Start Test'.")
            self.stat_duration_var = ctk.StringVar(value="--")
            self.stat_ram_var = ctk.StringVar(value="--")
            self.stat_tests_var = ctk.StringVar(value="--")
            self.stat_grade_var = ctk.StringVar(value="--")
            self.autoscroll_var = ctk.BooleanVar(value=True)
            self.active_capability: Optional[str] = "full_suite"
            self.cap_buttons: Dict[str, ctk.CTkButton] = {}
            self.cap_names: Dict[str, str] = {}
            self.stat_labels: Dict[str, ctk.CTkLabel] = {}

            self._build_ui()
            self._refresh_capabilities()
            self._poll_queue()

        def _build_ui(self):
            # 1. Top Header Bar
            header = ctk.CTkFrame(self, corner_radius=10, fg_color=("#ffffff", "gray14"), border_width=1, border_color=("#e2e8f0", "#334155"))
            header.pack(fill="x", padx=12, pady=(12, 6))

            title_box = ctk.CTkFrame(header, fg_color="transparent")
            title_box.pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(title_box, text="⚡ UniversalTester  v2.0.1", font=ctk.CTkFont(size=18, weight="bold"), text_color=("#1f538d", "#38bdf8")).pack(anchor="w")
            ctk.CTkLabel(title_box, text="5-Pillar Quality Engine & Algorithm Matrix", font=ctk.CTkFont(size=11), text_color=("#334155", "#94a3b8")).pack(anchor="w")

            theme_box = ctk.CTkFrame(header, fg_color="transparent")
            theme_box.pack(side="right", padx=12, pady=8)

            ctk.CTkLabel(theme_box, text="Theme:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
            ctk.CTkOptionMenu(theme_box, values=["Dark", "Light", "System"], width=95, command=ctk.set_appearance_mode).pack(side="left")

            # 2. Project Bar
            proj_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("#ffffff", "gray17"), border_width=1, border_color=("#e2e8f0", "#334155"))
            proj_bar.pack(fill="x", padx=12, pady=6)

            ctk.CTkLabel(proj_bar, text="Target Project:", font=ctk.CTkFont(weight="bold"), text_color=("#0f172a", "#f8fafc")).pack(side="left", padx=(12, 8), pady=10)
            self.proj_entry = ctk.CTkEntry(proj_bar, textvariable=self.project_path_var, font=ctk.CTkFont(family="Consolas", size=12))
            self.proj_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)

            self.proj_browse_btn = ctk.CTkButton(proj_bar, text="Browse...", width=90, command=self._browse_dir)
            self.proj_browse_btn.pack(side="left", padx=(0, 6), pady=10)
            self.proj_refresh_btn = ctk.CTkButton(
                proj_bar,
                text="Refresh",
                width=80,
                fg_color=("#e2e8f0", "gray30"),
                hover_color=("#cbd5e1", "gray40"),
                text_color=("#0f172a", "#f8fafc"),
                text_color_disabled=("#64748b", "gray50"),
                border_width=1,
                border_color=("#cbd5e1", "#334155"),
                command=self._refresh_capabilities
            )
            self.proj_refresh_btn.pack(side="left", padx=(0, 12), pady=10)

            # 3. Main Panes: Left Sidebar (Capabilities) + Right Dashboard (Live Console)
            main_pane = ctk.CTkFrame(self, fg_color="transparent")
            main_pane.pack(fill="both", expand=True, padx=12, pady=(6, 12))

            # Left Sidebar
            left_side = ctk.CTkFrame(main_pane, width=320, corner_radius=10, fg_color=("#ffffff", "gray17"), border_width=1, border_color=("#e2e8f0", "#334155"))
            left_side.pack(side="left", fill="y", padx=(0, 8))
            left_side.pack_propagate(False)

            ctk.CTkLabel(left_side, text="Testing Capabilities", font=ctk.CTkFont(size=14, weight="bold"), text_color=("#0f172a", "#f8fafc")).pack(anchor="w", padx=12, pady=(12, 6))
            self.caps_scroll = ctk.CTkScrollableFrame(left_side, fg_color="transparent")
            self.caps_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 8))

            # Right Dashboard
            right_side = ctk.CTkFrame(main_pane, corner_radius=10, fg_color=("#ffffff", "gray17"), border_width=1, border_color=("#e2e8f0", "#334155"))
            right_side.pack(side="left", fill="both", expand=True)

            # Execution Status Card
            status_card = ctk.CTkFrame(right_side, fg_color=("#f8fafc", "gray14"), corner_radius=8, border_width=1, border_color=("#e2e8f0", "gray25"))
            status_card.pack(fill="x", padx=12, pady=12)

            # Active Test Header (above status)
            active_row = ctk.CTkFrame(status_card, fg_color="transparent")
            active_row.pack(fill="x", padx=10, pady=(8, 2))

            self.active_test_lbl = ctk.CTkLabel(
                active_row,
                textvariable=self.active_test_var,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#0284c7", "#38bdf8")
            )
            self.active_test_lbl.pack(side="left")

            # Concurrency Load Selector (Editable ComboBox allowing custom numbers)
            self.concurrency_box = ctk.CTkFrame(active_row, fg_color="transparent")
            self.concurrency_box.pack(side="right")

            ctk.CTkLabel(
                self.concurrency_box,
                text="Load Users:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#0f172a", "#cbd5e1")
            ).pack(side="left", padx=(0, 4))

            self.concurrency_var = ctk.StringVar(value="200")
            self.concurrency_menu = ctk.CTkComboBox(
                self.concurrency_box,
                variable=self.concurrency_var,
                values=["50", "100", "200", "500", "1000", "2000"],
                width=90,
                height=26,
                font=ctk.CTkFont(size=11),
                command=self._on_concurrency_change
            )
            self.concurrency_menu.pack(side="left")

            top_row = ctk.CTkFrame(status_card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(2, 4))

            self.status_lbl = ctk.CTkLabel(top_row, textvariable=self.status_var, font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981")
            self.status_lbl.pack(side="left")

            self.action_btn = ctk.CTkButton(
                top_row,
                text="Start Test",
                width=100,
                fg_color="#10b981",
                hover_color="#059669",
                state="normal",
                command=self._handle_action_click
            )
            self.action_btn.pack(side="right")
            self.cancel_btn = self.action_btn

            self.step_lbl = ctk.CTkLabel(status_card, textvariable=self.step_var, font=ctk.CTkFont(size=12), text_color=("#0f172a", "#cbd5e1"))
            self.step_lbl.pack(anchor="w", padx=10, pady=(0, 6))

            self.progress_bar = ctk.CTkProgressBar(status_card, height=10, corner_radius=5)
            self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
            self.progress_bar.set(0.0)

            # Live Metrics Stat Cards Dashboard (Duration, Peak RAM, Tests/Result, Grade)
            self.stats_panel = ctk.CTkFrame(right_side, fg_color="transparent")
            self.stats_panel.pack(fill="x", padx=12, pady=(0, 8))
            for i in range(4):
                self.stats_panel.grid_columnconfigure(i, weight=1)

            cards_def = [
                ("duration", "⏱ DURATION", self.stat_duration_var, ("#0284c7", "#38bdf8")),
                ("ram", "🧠 PEAK RAM", self.stat_ram_var, ("#7c3aed", "#c084fc")),
                ("tests", "🎯 TESTS / RESULT", self.stat_tests_var, ("#16a34a", "#4ade80")),
                ("grade", "🏆 SYSTEM GRADE", self.stat_grade_var, ("#d97706", "#fbbf24")),
            ]
            for col, (key, title, var, default_color) in enumerate(cards_def):
                card = ctk.CTkFrame(self.stats_panel, corner_radius=8, fg_color=("#f8fafc", "gray14"), border_width=1, border_color=("#e2e8f0", "gray25"))
                card.grid(row=0, column=col, padx=3, pady=2, sticky="nsew")
                ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=("#334155", "#94a3b8")).pack(anchor="w", padx=10, pady=(6, 2))
                val_lbl = ctk.CTkLabel(card, textvariable=var, font=ctk.CTkFont(size=13, weight="bold"), text_color=default_color)
                val_lbl.pack(anchor="w", padx=10, pady=(0, 6))
                self.stat_labels[key] = val_lbl

            # Live Log Terminal with Action Toolbar
            console_box = ctk.CTkFrame(right_side, fg_color="transparent")
            console_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            toolbar = ctk.CTkFrame(console_box, fg_color="transparent")
            toolbar.pack(fill="x", pady=(0, 4))

            ctk.CTkLabel(toolbar, text="Live Execution Output:", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#0f172a", "#f8fafc")).pack(side="left")

            # Toolbar Actions: Auto-scroll, Export, Copy, Clear
            ctk.CTkCheckBox(
                toolbar,
                text="Auto-scroll",
                variable=self.autoscroll_var,
                font=ctk.CTkFont(size=11),
                text_color=("#0f172a", "#f8fafc"),
                width=85,
                height=22
            ).pack(side="right", padx=(6, 0))

            ctk.CTkButton(toolbar, text="Export...", width=65, height=24, fg_color=("#e2e8f0", "gray30"), hover_color=("#cbd5e1", "gray40"), text_color=("#0f172a", "#f8fafc"), text_color_disabled=("#64748b", "gray50"), border_width=1, border_color=("#cbd5e1", "#334155"), font=ctk.CTkFont(size=11), command=self._export_log).pack(side="right", padx=3)
            ctk.CTkButton(toolbar, text="Copy", width=55, height=24, fg_color=("#e2e8f0", "gray30"), hover_color=("#cbd5e1", "gray40"), text_color=("#0f172a", "#f8fafc"), text_color_disabled=("#64748b", "gray50"), border_width=1, border_color=("#cbd5e1", "#334155"), font=ctk.CTkFont(size=11), command=self._copy_log).pack(side="right", padx=3)
            ctk.CTkButton(toolbar, text="Clear", width=55, height=24, fg_color=("#e2e8f0", "gray30"), hover_color=("#cbd5e1", "gray40"), text_color=("#0f172a", "#f8fafc"), text_color_disabled=("#64748b", "gray50"), border_width=1, border_color=("#cbd5e1", "#334155"), font=ctk.CTkFont(size=11), command=self._clear_log).pack(side="right", padx=3)

            self.log_text = ctk.CTkTextbox(console_box, font=ctk.CTkFont(family="Consolas", size=11), wrap="word", corner_radius=8, border_width=1, border_color=("#cbd5e1", "#334155"))
            self.log_text.configure(state="disabled")
            self.log_text.pack(fill="both", expand=True)

            # Bind Ctrl+A / Ctrl+a to highlight all text
            def _select_all(e=None):
                self.log_text._textbox.tag_add("sel", "1.0", "end")
                return "break"

            self.log_text._textbox.bind("<Control-a>", _select_all)
            self.log_text._textbox.bind("<Control-A>", _select_all)

        def _clear_log(self):
            """Clear log text while keeping widget read-only for user."""
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")

        def _append_log(self, text: str):
            """Append text to log while keeping widget read-only for user."""
            self.log_text.configure(state="normal")
            self.log_text.insert("end", text)
            if self.autoscroll_var.get():
                self.log_text.see("end")
            self.log_text.configure(state="disabled")

        def _copy_log(self):
            """Copy current console log output to system clipboard."""
            text = self.log_text.get("1.0", "end-1c")
            if text.strip():
                try:
                    self.clipboard_clear()
                    self.clipboard_append(text)
                    self.step_var.set("✔ Console logs copied to clipboard.")
                except Exception as e:
                    self.step_var.set(f"Could not copy to clipboard: {e}")

        def _export_log(self):
            """Export console logs to a text file."""
            text = self.log_text.get("1.0", "end-1c")
            if not text.strip():
                self.step_var.set("No logs to export.")
                return
            fn = filedialog.asksaveasfilename(
                title="Export Execution Logs",
                defaultextension=".txt",
                filetypes=[("Text File", "*.txt"), ("Log File", "*.log"), ("All Files", "*.*")],
                initialfile=f"test_run_{int(time.time())}.txt"
            )
            if fn:
                try:
                    with open(fn, "w", encoding="utf-8") as f:
                        f.write(text)
                    self.step_var.set(f"✔ Exported logs to: {os.path.basename(fn)}")
                except Exception as e:
                    self.step_var.set(f"Error exporting logs: {e}")

        def _update_stat_cards(self, res: Optional[RunResult] = None):
            """Update stat cards with execution metrics or reset to baseline."""
            if res is None:
                self.stat_duration_var.set("--")
                self.stat_ram_var.set("--")
                self.stat_tests_var.set("--")
                self.stat_grade_var.set("--")
                return

            self.stat_duration_var.set(f"{res.duration_s:.2f}s")

            mem = get_session_memory_mb()
            if mem.get("peak_mb", 0) > 0:
                self.stat_ram_var.set(f"{mem['peak_mb']:.1f} MB")
            elif res.metrics and "ram_kb" in res.metrics:
                self.stat_ram_var.set(f"{res.metrics['ram_kb'] / 1024:.1f} MB")
            else:
                self.stat_ram_var.set("Normal")

            passed = res.metrics.get("passed", 0) if res.metrics else 0
            failed = res.metrics.get("failed", 0) if res.metrics else 0
            total = passed + failed
            if total > 0:
                pct = (passed / total) * 100
                self.stat_tests_var.set(f"{passed}/{total} ({pct:.0f}%)")
                lbl = self.stat_labels.get("tests")
                if lbl:
                    lbl.configure(text_color=("#16a34a", "#4ade80") if failed == 0 else ("#d97706", "#fbbf24") if res.is_success else ("#dc2626", "#f87171"))
            else:
                status_txt = "PASSED" if res.is_success else res.status.upper()
                self.stat_tests_var.set(status_txt)
                lbl = self.stat_labels.get("tests")
                if lbl:
                    lbl.configure(text_color=("#16a34a", "#4ade80") if res.is_success else ("#dc2626", "#f87171"))

            grade = res.metrics.get("grade") if res.metrics else None
            if not grade:
                if res.is_success and failed == 0:
                    grade = "Grade A+"
                elif res.is_success:
                    grade = "Grade B+ (Caution)"
                elif res.status == "canceled":
                    grade = "Canceled"
                else:
                    grade = "Grade F"

            self.stat_grade_var.set(grade)
            lbl = self.stat_labels.get("grade")
            if lbl:
                if "A" in grade:
                    lbl.configure(text_color=("#16a34a", "#4ade80"))
                elif "B" in grade or "Caution" in grade:
                    lbl.configure(text_color=("#d97706", "#fbbf24"))
                else:
                    lbl.configure(text_color=("#dc2626", "#f87171"))

        def _set_controls_enabled(self, enabled: bool):
            """Enable or disable interactive widgets during test execution."""
            state = "normal" if enabled else "disabled"
            if hasattr(self, "proj_browse_btn"):
                self.proj_browse_btn.configure(state=state)
            if hasattr(self, "proj_refresh_btn"):
                self.proj_refresh_btn.configure(state=state)
            self.proj_entry.configure(state=state)
            self.concurrency_menu.configure(state=state)
            for cid, btn in self.cap_buttons.items():
                is_avail = "[N/A]" not in btn.cget("text")
                if enabled and is_avail:
                    btn.configure(state="normal")
                else:
                    btn.configure(state="disabled")

        def _browse_dir(self):
            selected = filedialog.askdirectory(initialdir=self.project_path_var.get())
            if selected:
                self.project_path_var.set(selected)
                self._refresh_capabilities()

        def _refresh_capabilities(self):
            for widget in self.caps_scroll.winfo_children():
                widget.destroy()
            self.cap_buttons.clear()
            self.cap_names.clear()

            path = self.project_path_var.get()
            caps = self.service.list_capabilities(path)

            for cap in caps:
                cap_id = cap["id"]
                name = cap["name"]
                is_avail = cap.get("available", True)
                pillar = cap.get("pillar")
                label = f"Pillar {pillar}: {name}" if pillar not in ('ALL', 'SYS') else name
                if not is_avail:
                    label += " [N/A]"

                self.cap_names[cap_id] = label

                is_active = (cap_id == self.active_capability)
                if not is_avail:
                    btn = ctk.CTkButton(
                        self.caps_scroll,
                        text=label,
                        anchor="w",
                        height=36,
                        corner_radius=6,
                        fg_color=("#f1f5f9", "#1e293b"),
                        hover_color=("#f1f5f9", "#1e293b"),
                        text_color=("#0f172a", "#94a3b8"),
                        text_color_disabled=("#0f172a", "#94a3b8"),
                        border_width=1,
                        border_color=("#94a3b8", "#475569"),
                        state="disabled",
                        command=lambda cid=cap_id: self._select_capability(cid)
                    )
                else:
                    btn = ctk.CTkButton(
                        self.caps_scroll,
                        text=label,
                        anchor="w",
                        height=36,
                        corner_radius=6,
                        fg_color=("#0284c7", "#0369a1") if is_active else ("#f1f5f9", "#1e293b"),
                        hover_color=("#0369a1", "#0284c7") if is_active else ("#e2e8f0", "#334155"),
                        text_color=("#ffffff", "#ffffff") if is_active else ("#0f172a", "#f8fafc"),
                        text_color_disabled=("#ffffff", "#ffffff") if is_active else ("#0f172a", "#f8fafc"),
                        border_width=0 if is_active else 1,
                        border_color=("#cbd5e1", "#334155"),
                        state="normal",
                        command=lambda cid=cap_id: self._select_capability(cid)
                    )
                btn.pack(fill="x", pady=4)
                self.cap_buttons[cap_id] = btn

            if self.active_capability and self.active_capability in self.cap_names:
                self.active_test_var.set(f"Active Test: {self.cap_names[self.active_capability]}")
            self._update_concurrency_visibility(self.active_capability)

        def _set_active_capability(self, capability: str):
            """Highlight the selected capability button and style inactive ones."""
            self.active_capability = capability
            for cid, btn in self.cap_buttons.items():
                is_avail = "[N/A]" not in btn.cget("text")
                if not is_avail:
                    btn.configure(
                        fg_color=("#f1f5f9", "#1e293b"),
                        hover_color=("#f1f5f9", "#1e293b"),
                        text_color=("#0f172a", "#94a3b8"),
                        text_color_disabled=("#0f172a", "#94a3b8"),
                        border_width=1,
                        border_color=("#94a3b8", "#475569")
                    )
                elif cid == capability:
                    btn.configure(
                        fg_color=("#0284c7", "#0369a1"),
                        hover_color=("#0369a1", "#0284c7"),
                        text_color=("#ffffff", "#ffffff"),
                        text_color_disabled=("#ffffff", "#ffffff"),
                        border_width=0
                    )
                else:
                    btn.configure(
                        fg_color=("#f1f5f9", "#1e293b"),
                        hover_color=("#e2e8f0", "#334155"),
                        text_color=("#0f172a", "#f8fafc"),
                        text_color_disabled=("#0f172a", "#f8fafc"),
                        border_width=1,
                        border_color=("#cbd5e1", "#334155")
                    )

        def _update_concurrency_visibility(self, capability: str):
            """Show concurrency selector only for Full Assessment and Pillar 4 Simulation."""
            needs = capability in (
                "full_suite", "simulation", Capability.SIMULATION, "all", "overall", "reliability"
            )
            if needs:
                self.concurrency_box.pack(side="right")
            else:
                self.concurrency_box.pack_forget()

        def _on_concurrency_change(self, value: Optional[str] = None):
            """Update active test label and prompt when user changes concurrency."""
            val = self.concurrency_var.get().strip() or "200"
            if self.active_capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({val} Users)"
                self.active_test_var.set(f"Active Test: {label}")
                self.step_var.set(f"Ready to run {label}. Click 'Start Test' to begin.")

        def _select_capability(self, capability: str):
            """Select active capability from sidebar without directly launching execution."""
            if self.runner.is_running():
                return

            self._set_active_capability(capability)
            self._update_concurrency_visibility(capability)
            val = self.concurrency_var.get().strip() or "200"
            label = self.cap_names.get(capability, capability)
            if capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({val} Users)"
            self.active_test_var.set(f"Active Test: {label}")
            self.status_var.set("● READY")
            self.status_lbl.configure(text_color="#10b981")
            self.step_var.set(f"Ready to run {label}. Click 'Start Test' to begin.")
            self.action_btn.configure(
                text="Start Test",
                fg_color="#10b981",
                hover_color="#059669",
                state="normal"
            )
            self.progress_bar.set(0.0)

        def _handle_action_click(self):
            """Start test execution or cancel active run."""
            if self.runner.is_running():
                self._cancel_run()
            else:
                self._trigger_run(self.active_capability or "full_suite")

        def _trigger_run(self, capability: str):
            if self.runner.is_running():
                return

            raw_val = self.concurrency_var.get().strip()
            users_val = int(raw_val) if raw_val.isdigit() and int(raw_val) > 0 else 200
            label = self.cap_names.get(capability, capability)
            if capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({users_val} Users)"

            self._set_active_capability(capability)
            self._update_concurrency_visibility(capability)
            self.active_test_var.set(f"Active Test: {label}")
            self.status_var.set("● RUNNING...")
            self.status_lbl.configure(text_color="#38bdf8")
            self.step_var.set(f"Executing {label}...")
            self.progress_bar.set(0.0)
            self.action_btn.configure(
                text="Cancel Run",
                fg_color="#ef4444",
                hover_color="#dc2626",
                state="normal"
            )
            self._clear_log()
            self._append_log(f"▶ Starting workload: {label}\n\n")

            self._set_controls_enabled(False)
            self.stat_duration_var.set("Running...")
            self.stat_ram_var.set("Measuring...")
            self.stat_tests_var.set("In progress")
            self.stat_grade_var.set("Evaluating...")

            req = RunRequest(
                capability=capability,
                project_path=self.project_path_var.get(),
                options={
                    "concurrent_users": users_val,
                    "gui_mode": True,
                    "capture_stdout": True
                }
            )

            self.runner.start_run(
                req,
                on_event=lambda evt: self.event_queue.put(("event", evt)),
                on_complete=lambda res: self.event_queue.put(("result", res))
            )

        def _cancel_run(self):
            self.runner.cancel()
            self.step_var.set("Cancellation requested...")

        def _poll_queue(self):
            try:
                while True:
                    mtype, payload = self.event_queue.get_nowait()
                    if mtype == "event":
                        evt: ProgressEvent = payload
                        if evt.percent >= 0:
                            self.progress_bar.set(min(1.0, max(0.0, evt.percent / 100.0)))
                            self.step_var.set(f"[{evt.step}] {evt.message}")
                        if evt.message is not None:
                            self._append_log(f"{evt.message}\n")
                    elif mtype == "result":
                        res: RunResult = payload
                        self._set_controls_enabled(True)
                        self._update_stat_cards(res)
                        self.action_btn.configure(
                            text="Start Test",
                            fg_color="#10b981",
                            hover_color="#059669",
                            state="normal"
                        )
                        if res.is_success:
                            failed_cnt = res.metrics.get("failed", 0) if res.metrics else 0
                            if failed_cnt > 0:
                                self.status_var.set("⚠ PASSED (CAUTION)")
                                self.status_lbl.configure(text_color="#f59e0b")
                            else:
                                self.status_var.set("✔ PASSED")
                                self.status_lbl.configure(text_color="#10b981")
                        elif res.status == "canceled":
                            self.status_var.set("✖ CANCELED")
                            self.status_lbl.configure(text_color="#f59e0b")
                        else:
                            self.status_var.set(f"✖ {res.status}")
                            self.status_lbl.configure(text_color="#ef4444")

                        self.progress_bar.set(1.0)
                        mem = get_session_memory_mb()
                        ram_str = f" • Session RAM: {mem['current_mb']:.1f} MB (Peak: {mem['peak_mb']:.1f} MB)" if mem['peak_mb'] > 0 else ""
                        self.step_var.set(f"Completed in {res.duration_s:.2f}s{ram_str}")
                        summary = f"\n──────────────────────────────────────────────────\nRun ID: {res.run_id} | Status: {res.status} | Duration: {res.duration_s}s{ram_str}\n"
                        if res.metrics:
                            summary += f"Metrics: {res.metrics}\n"
                        self._append_log(summary)
            except queue.Empty:
                pass

            self.after(50, self._poll_queue)


UniversalTesterGUI = UniversalTesterApp


def main() -> int:
    """Launch UniversalTester Desktop GUI."""
    if not HAS_CTK:
        err_detail = _IMPORT_ERROR or "CustomTkinter could not be loaded."
        msg = (
            f"UniversalTester Desktop GUI requires Python Tkinter and PIL:\n\n"
            f"Error details: {err_detail}\n\n"
            f"To resolve on Ubuntu/Debian, install the required packages:\n"
            f"  sudo apt install python3-tk python3-pil python3-pil.imagetk"
        )
        print(msg, file=sys.stderr)
        if sys.platform != "win32":
            try:
                import subprocess
                import shutil
                if shutil.which("zenity"):
                    subprocess.run(["zenity", "--error", "--title=Universal Tester", "--text=" + msg])
                elif shutil.which("kdialog"):
                    subprocess.run(["kdialog", "--error", msg])
            except Exception:
                pass
        return 1

    app = UniversalTesterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
