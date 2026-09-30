"""
Modern, Cross-Platform Desktop GUI for UniversalTester (testx).
Built with CustomTkinter for sleek dark/light mode themes, responsive widgets, and live log streaming.
"""
import os
import sys
import io
import queue
from typing import Optional, Dict, Any, List

# Fallback for windowed/noconsole PyInstaller executables where sys.stdout is None
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

try:
    import customtkinter as ctk
    from tkinter import filedialog
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from core.service import TesterService
from core.models import RunRequest, RunResult
from core.events import ProgressEvent
from adapters.base import Capability
from gui.worker import AsyncTestRunner
from cli.interactive import load_config

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if HAS_CTK:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class UniversalTesterApp(ctk.CTk):
        """Modern CustomTkinter desktop interface for UniversalTester."""

        def __init__(self, service: Optional[TesterService] = None):
            super().__init__()
            self.service = service or TesterService()
            self.runner = AsyncTestRunner(self.service)
            self.event_queue: queue.Queue = queue.Queue()
            self.config = load_config(_ROOT_DIR)

            self.title("⚡ UniversalTester (testx) — Quality & Benchmark Engine")
            self.geometry("1040x680")
            self.minsize(840, 540)

            self.project_path_var = ctk.StringVar(value=os.getcwd())
            self.active_test_var = ctk.StringVar(value="Active Test: Full Assessment (All 5 Pillars)")
            self.status_var = ctk.StringVar(value="● READY")
            self.step_var = ctk.StringVar(value="Select a testing capability and click 'Start Test'.")
            self.active_capability: Optional[str] = "full_suite"
            self.cap_buttons: Dict[str, ctk.CTkButton] = {}
            self.cap_names: Dict[str, str] = {}

            self._build_ui()
            self._refresh_capabilities()
            self._poll_queue()

        def _build_ui(self):
            # 1. Top Header Bar
            header = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray14"))
            header.pack(fill="x", padx=12, pady=(12, 6))

            title_box = ctk.CTkFrame(header, fg_color="transparent")
            title_box.pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(title_box, text="⚡ UniversalTester", font=ctk.CTkFont(size=18, weight="bold"), text_color=("#1f538d", "#38bdf8")).pack(anchor="w")
            ctk.CTkLabel(title_box, text="5-Pillar Quality Engine & Algorithm Matrix", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

            theme_box = ctk.CTkFrame(header, fg_color="transparent")
            theme_box.pack(side="right", padx=12, pady=8)

            ctk.CTkLabel(theme_box, text="Theme:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
            ctk.CTkOptionMenu(theme_box, values=["Dark", "Light", "System"], width=95, command=ctk.set_appearance_mode).pack(side="left")

            # 2. Project Bar
            proj_bar = ctk.CTkFrame(self, corner_radius=10)
            proj_bar.pack(fill="x", padx=12, pady=6)

            ctk.CTkLabel(proj_bar, text="Target Project:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(12, 8), pady=10)
            self.proj_entry = ctk.CTkEntry(proj_bar, textvariable=self.project_path_var, font=ctk.CTkFont(family="Consolas", size=12))
            self.proj_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)

            ctk.CTkButton(proj_bar, text="Browse...", width=90, command=self._browse_dir).pack(side="left", padx=(0, 6), pady=10)
            ctk.CTkButton(proj_bar, text="Refresh", width=80, fg_color="gray30", hover_color="gray40", command=self._refresh_capabilities).pack(side="left", padx=(0, 12), pady=10)

            # 3. Main Panes: Left Sidebar (Capabilities) + Right Dashboard (Live Console)
            main_pane = ctk.CTkFrame(self, fg_color="transparent")
            main_pane.pack(fill="both", expand=True, padx=12, pady=(6, 12))

            # Left Sidebar
            left_side = ctk.CTkFrame(main_pane, width=320, corner_radius=10)
            left_side.pack(side="left", fill="y", padx=(0, 8))
            left_side.pack_propagate(False)

            ctk.CTkLabel(left_side, text="Testing Capabilities", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(12, 6))
            self.caps_scroll = ctk.CTkScrollableFrame(left_side, fg_color="transparent")
            self.caps_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 8))

            # Right Dashboard
            right_side = ctk.CTkFrame(main_pane, corner_radius=10)
            right_side.pack(side="left", fill="both", expand=True)

            # Execution Status Card
            status_card = ctk.CTkFrame(right_side, fg_color=("gray85", "gray17"), corner_radius=8)
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

            # Concurrency Load Selector
            concurrency_box = ctk.CTkFrame(active_row, fg_color="transparent")
            concurrency_box.pack(side="right")

            ctk.CTkLabel(
                concurrency_box,
                text="Load Users:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray"
            ).pack(side="left", padx=(0, 4))

            self.concurrency_var = ctk.StringVar(value="200")
            self.concurrency_menu = ctk.CTkOptionMenu(
                concurrency_box,
                variable=self.concurrency_var,
                values=["50", "100", "200", "500", "1000", "2000"],
                width=85,
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

            self.step_lbl = ctk.CTkLabel(status_card, textvariable=self.step_var, font=ctk.CTkFont(size=12), text_color="gray")
            self.step_lbl.pack(anchor="w", padx=10, pady=(0, 6))

            self.progress_bar = ctk.CTkProgressBar(status_card, height=10, corner_radius=5)
            self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
            self.progress_bar.set(0.0)

            # Live Log Terminal
            console_box = ctk.CTkFrame(right_side, fg_color="transparent")
            console_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

            ctk.CTkLabel(console_box, text="Live Execution Output:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
            self.log_text = ctk.CTkTextbox(console_box, font=ctk.CTkFont(family="Consolas", size=11), wrap="word", corner_radius=8)
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
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

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
                btn = ctk.CTkButton(
                    self.caps_scroll,
                    text=label,
                    anchor="w",
                    height=36,
                    corner_radius=6,
                    fg_color=("#0284c7", "#0369a1") if is_active else ("gray75", "gray25"),
                    hover_color=("#0369a1", "#0284c7") if is_active else ("gray65", "gray35"),
                    state="normal" if is_avail else "disabled",
                    command=lambda cid=cap_id: self._select_capability(cid)
                )
                btn.pack(fill="x", pady=4)
                self.cap_buttons[cap_id] = btn

            if self.active_capability and self.active_capability in self.cap_names:
                self.active_test_var.set(f"Active Test: {self.cap_names[self.active_capability]}")

        def _set_active_capability(self, capability: str):
            """Highlight the selected capability button in blue and reset others."""
            self.active_capability = capability
            for cid, btn in self.cap_buttons.items():
                if cid == capability:
                    btn.configure(
                        fg_color=("#0284c7", "#0369a1"),
                        hover_color=("#0369a1", "#0284c7")
                    )
                else:
                    btn.configure(
                        fg_color=("gray75", "gray25"),
                        hover_color=("gray65", "gray35")
                    )

        def _on_concurrency_change(self, value: str):
            """Update active test label and prompt when user changes concurrency."""
            if self.active_capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({value} Users)"
                self.active_test_var.set(f"Active Test: {label}")
                self.step_var.set(f"Ready to run {label}. Click 'Start Test' to begin.")

        def _select_capability(self, capability: str):
            """Select active capability from sidebar without directly launching execution."""
            if self.runner.is_running():
                return

            self._set_active_capability(capability)
            label = self.cap_names.get(capability, capability)
            if capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({self.concurrency_var.get()} Users)"
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

            users_val = int(self.concurrency_var.get()) if self.concurrency_var.get().isdigit() else 200
            label = self.cap_names.get(capability, capability)
            if capability in ("simulation", Capability.SIMULATION):
                label = f"Pillar 4: Concurrency Simulation ({users_val} Users)"

            self._set_active_capability(capability)
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
                        self.action_btn.configure(
                            text="Start Test",
                            fg_color="#10b981",
                            hover_color="#059669",
                            state="normal"
                        )
                        if res.is_success:
                            self.status_var.set("✔ PASSED")
                            self.status_lbl.configure(text_color="#10b981")
                        elif res.status == "canceled":
                            self.status_var.set("✖ CANCELED")
                            self.status_lbl.configure(text_color="#f59e0b")
                        else:
                            self.status_var.set(f"✖ {res.status}")
                            self.status_lbl.configure(text_color="#ef4444")

                        self.progress_bar.set(1.0)
                        summary = f"\n──────────────────────────────────────────────────\nRun ID: {res.run_id} | Status: {res.status} | Duration: {res.duration_s}s\n"
                        if res.metrics:
                            summary += f"Metrics: {res.metrics}\n"
                        self._append_log(summary)
            except queue.Empty:
                pass

            self.after(50, self._poll_queue)


def main() -> int:
    """Launch UniversalTester Desktop GUI."""
    if not HAS_CTK:
        print("CustomTkinter is not installed. Run: pip install customtkinter")
        return 1

    app = UniversalTesterApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
