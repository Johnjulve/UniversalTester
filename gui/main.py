"""
Modern, Cross-Platform Desktop GUI for UniversalTester (testx).
Built with CustomTkinter for sleek dark/light mode themes, responsive widgets, and live log streaming.
"""
import os
import sys
import queue
from typing import Optional, Dict, Any, List

try:
    import customtkinter as ctk
    from tkinter import filedialog
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from core.service import TesterService
from core.models import RunRequest, RunResult
from core.events import ProgressEvent
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
            self.status_var = ctk.StringVar(value="● READY")
            self.step_var = ctk.StringVar(value="Select a testing capability to begin.")

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

            top_row = ctk.CTkFrame(status_card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 4))

            self.status_lbl = ctk.CTkLabel(top_row, textvariable=self.status_var, font=ctk.CTkFont(size=13, weight="bold"), text_color="#10b981")
            self.status_lbl.pack(side="left")

            self.cancel_btn = ctk.CTkButton(top_row, text="Cancel Run", width=90, fg_color="#ef4444", hover_color="#dc2626", state="disabled", command=self._cancel_run)
            self.cancel_btn.pack(side="right")

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
            self.log_text.pack(fill="both", expand=True)

        def _browse_dir(self):
            selected = filedialog.askdirectory(initialdir=self.project_path_var.get())
            if selected:
                self.project_path_var.set(selected)
                self._refresh_capabilities()

        def _refresh_capabilities(self):
            for widget in self.caps_scroll.winfo_children():
                widget.destroy()

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

                is_primary = cap_id == "full_suite"
                btn = ctk.CTkButton(
                    self.caps_scroll,
                    text=label,
                    anchor="w",
                    height=36,
                    corner_radius=6,
                    fg_color=("#0284c7", "#0369a1") if is_primary else ("gray75", "gray25"),
                    hover_color=("#0369a1", "#0284c7") if is_primary else ("gray65", "gray35"),
                    state="normal" if is_avail else "disabled",
                    command=lambda cid=cap_id: self._trigger_run(cid)
                )
                btn.pack(fill="x", pady=4)

        def _trigger_run(self, capability: str):
            if self.runner.is_running():
                return

            self.status_var.set("● RUNNING...")
            self.status_lbl.configure(text_color="#38bdf8")
            self.step_var.set(f"Executing {capability}...")
            self.progress_bar.set(0.0)
            self.cancel_btn.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", f"▶ Starting workload: {capability}\n\n")

            req = RunRequest(
                capability=capability,
                project_path=self.project_path_var.get(),
                options={"concurrent_users": 200}
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
                        if evt.message:
                            self.log_text.insert("end", f"{evt.message}\n")
                            self.log_text.see("end")
                    elif mtype == "result":
                        res: RunResult = payload
                        self.cancel_btn.configure(state="disabled")
                        if res.is_success:
                            self.status_var.set("✔ PASSED")
                            self.status_lbl.configure(text_color="#10b981")
                        else:
                            self.status_var.set(f"✖ {res.status}")
                            self.status_lbl.configure(text_color="#ef4444")

                        self.progress_bar.set(1.0)
                        summary = f"\n──────────────────────────────────────────────────\nRun ID: {res.run_id} | Status: {res.status} | Duration: {res.duration_s}s\n"
                        if res.metrics:
                            summary += f"Metrics: {res.metrics}\n"
                        self.log_text.insert("end", summary)
                        self.log_text.see("end")
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
