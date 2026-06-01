import sys
import os
import subprocess
import winreg
import threading
import re
import time
import customtkinter as ctk
from tkinter import messagebox, colorchooser, filedialog

FORMATS = {
    "VIDEO": ["MP4", "MKV", "AVI", "MOV", "FLV", "WEBM", "WMV", "3GP", "MPEG", "TS", "OGV", "M4V"],
    "AUDIO": ["MP3", "M4A", "FLAC", "WAV", "WMA", "AAC", "OGG", "OPUS", "AMR", "AIFF", "M4R"],
    "IMAGE": ["PNG", "JPG", "JPEG", "WEBP", "BMP", "TIFF", "GIF", "ICO"]
}

BLOCKED_EXTS = {".py", ".exe", ".bat", ".dll"}

def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)

def parse_time(time_str):
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


class UniversalConverterApp(ctk.CTk):
    def __init__(self, input_file=None):
        super().__init__()

        self.input_file = None
        if input_file and os.path.exists(input_file):
            if os.path.splitext(input_file)[1].lower() not in BLOCKED_EXTS:
                self.input_file = input_file

        self.title("Universal Media Converter v1.1")
        self.geometry("560x620")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.max_threads = os.cpu_count() or 4
        self.allocated_threads = max(4, self.max_threads // 2) if self.max_threads > 4 else self.max_threads

        self.current_process = None
        self.is_cancelled = False

        self.theme_buttons = []
        self.theme_labels = []

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.tabview = ctk.CTkTabview(self, width=530, height=580)
        self.tabview.pack(padx=15, pady=10)

        self.tab_converter = self.tabview.add("Converter")
        self.tab_themes   = self.tabview.add("Themes")
        self.tab_settings = self.tabview.add("⚙ Settings")
        self.tab_credits  = self.tabview.add("Credits")

        self._build_converter_tab()
        self._build_themes_tab()
        self._build_settings_tab()
        self._build_credits_tab()

        self.set_pitch_black()

    # ── UI CONSTRUCTION ────────────────────────────────────────────────────────

    def _build_converter_tab(self):
        self.source_label = ctk.CTkLabel(
            self.tab_converter, text="No file selected.",
            font=("Arial", 12, "bold"), wraplength=480
        )
        self.source_label.pack(pady=20)
        self.theme_labels.append(self.source_label)

        self.browse_btn = ctk.CTkButton(self.tab_converter, text="Browse File...", command=self.browse_file)
        self.browse_btn.pack(pady=5)
        self.theme_buttons.append(self.browse_btn)

        lbl_format = ctk.CTkLabel(self.tab_converter, text="Target Format:")
        lbl_format.pack(pady=(15, 0))
        self.theme_labels.append(lbl_format)

        self.format_dropdown = ctk.CTkComboBox(self.tab_converter, width=260)
        self.format_dropdown.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.tab_converter, width=380)
        self.progress_bar.pack(pady=25)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.tab_converter, text="Idle", font=("Arial", 11))
        self.status_label.pack(pady=2)
        self.theme_labels.append(self.status_label)

        action_frame = ctk.CTkFrame(self.tab_converter, fg_color="transparent")
        action_frame.pack(pady=15)

        self.convert_btn = ctk.CTkButton(
            action_frame, text="Convert Now", command=self.start_conversion,
            width=150, height=40, font=("Arial", 12, "bold")
        )
        self.convert_btn.pack(side="left", padx=10)
        self.theme_buttons.append(self.convert_btn)

        # Cancel stays red — intentionally excluded from the theme engine
        self.cancel_btn = ctk.CTkButton(
            action_frame, text="Cancel", command=self.cancel_conversion,
            width=100, height=40, fg_color="#b82323", hover_color="#8a1a1a",
            font=("Arial", 12, "bold"), state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=10)

        self._update_source_display()

    def _build_themes_tab(self):
        lbl_presets = ctk.CTkLabel(self.tab_themes, text="Preset Profiles:", font=("Arial", 12, "bold"))
        lbl_presets.pack(pady=10)
        self.theme_labels.append(lbl_presets)

        preset_frame = ctk.CTkFrame(self.tab_themes, fg_color="transparent")
        preset_frame.pack(pady=5)

        btn_black = ctk.CTkButton(preset_frame, text="Pitch Black", width=130, command=self.set_pitch_black, fg_color="#1a1a1a")
        btn_black.pack(side="left", padx=10)
        self.theme_buttons.append(btn_black)

        btn_white = ctk.CTkButton(preset_frame, text="Pure White", width=130, command=self.set_pure_white, fg_color="#e6e6e6", text_color="black")
        btn_white.pack(side="left", padx=10)
        self.theme_buttons.append(btn_white)

        lbl_custom = ctk.CTkLabel(self.tab_themes, text="Custom Element Color:", font=("Arial", 12, "bold"))
        lbl_custom.pack(pady=15)
        self.theme_labels.append(lbl_custom)

        paint_options = [
            ("App Background",      "bg"),
            ("Panel / Tab Color",   "panel"),
            ("Standard Buttons",    "buttons"),
            ("Progress & Sliders",  "progress_fill"),
            ("Tracks & Grooves",    "progress_track"),
            ("Text Elements",       "text"),
        ]
        for label, key in paint_options:
            ctk.CTkButton(
                self.tab_themes, text=f"🎨 Set {label}", width=260,
                command=lambda k=key: self.pick_element_color(k)
            ).pack(pady=4)

    def _build_settings_tab(self):
        lbl = ctk.CTkLabel(self.tab_settings, text="Windows Explorer Integration", font=("Arial", 12, "bold"))
        lbl.pack(pady=10)
        self.theme_labels.append(lbl)

        # Semantic colors kept outside the theme engine
        ctk.CTkButton(
            self.tab_settings, text="Enable Right-Click Integration",
            width=280, height=35, fg_color="#1e8a3a", hover_color="#145c26",
            command=self.registry_install
        ).pack(pady=5)
        ctk.CTkButton(
            self.tab_settings, text="Disable Right-Click Menu",
            width=280, height=35, fg_color="#b82323", hover_color="#8a1a1a",
            command=self.registry_uninstall
        ).pack(pady=5)

        ctk.CTkFrame(self.tab_settings, height=2, width=440, fg_color="#333333").pack(pady=12)

        lbl_perf = ctk.CTkLabel(self.tab_settings, text="Performance", font=("Arial", 12, "bold"))
        lbl_perf.pack(pady=2)
        self.theme_labels.append(lbl_perf)

        self.thread_label = ctk.CTkLabel(
            self.tab_settings,
            text=f"Thread Allocation: {self.allocated_threads} / {self.max_threads}",
            font=("Arial", 11)
        )
        self.thread_label.pack(pady=2)
        self.theme_labels.append(self.thread_label)

        self.thread_slider = ctk.CTkSlider(
            self.tab_settings, from_=1, to=self.max_threads,
            number_of_steps=self.max_threads - 1,
            command=self._update_thread_count, width=320
        )
        self.thread_slider.pack(pady=5)
        self.thread_slider.set(self.allocated_threads)

        note_frame = ctk.CTkFrame(self.tab_settings, width=460, fg_color="#141414", corner_radius=6)
        note_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(
            note_frame,
            text="⚠️  More threads speed up conversion but increase CPU heat and power draw.\n"
                 "Performance gains diminish past 6 threads on most hardware.",
            font=("Arial", 10, "bold"), justify="center", wraplength=430, text_color="#aaaaaa"
        ).pack(pady=12, padx=12)

    def _build_credits_tab(self):
        lbl_title = ctk.CTkLabel(self.tab_credits, text="Universal Media Converter v1.1", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=25)
        self.theme_labels.append(lbl_title)

        lbl_body = ctk.CTkLabel(
            self.tab_credits,
            text="developed by avkila\n\ngithub : avkila-tech\ndiscord : avkila\n\n1.06.2026  v1.1",
            font=("Arial", 12), justify="center"
        )
        lbl_body.pack(pady=10)
        self.theme_labels.append(lbl_body)

    # ── FILE HANDLING ──────────────────────────────────────────────────────────

    def browse_file(self):
        selected = filedialog.askopenfilename(title="Select File")
        if selected:
            self.input_file = selected
            self._update_source_display()

    def _update_source_display(self):
        if not self.input_file:
            self.source_label.configure(text="No file selected.")
            self.format_dropdown.configure(values=[])
            self.format_dropdown.set("")
            return

        self.source_label.configure(text=f"Source: {os.path.basename(self.input_file)}")
        ext = os.path.splitext(self.input_file)[1].lstrip(".").upper()

        if ext in FORMATS["IMAGE"]:
            self.format_dropdown.configure(values=FORMATS["IMAGE"])
            self.format_dropdown.set("JPG" if ext != "JPG" else "PNG")
        elif ext in FORMATS["AUDIO"]:
            self.format_dropdown.configure(values=FORMATS["AUDIO"])
            self.format_dropdown.set("MP3" if ext != "MP3" else "WAV")
        else:
            options = FORMATS["VIDEO"] + ["--- AUDIO EXTRACT ---"] + FORMATS["AUDIO"]
            self.format_dropdown.configure(values=options)
            self.format_dropdown.set("MP4" if ext != "MP4" else "MKV")

    # ── THEME ENGINE ───────────────────────────────────────────────────────────

    def set_pitch_black(self):
        self._apply_theme(bg="#000000", panel="#262626", text="#FFFFFF", accent="#3b8ed0", hover="#404040")

    def set_pure_white(self):
        self._apply_theme(bg="#FFFFFF", panel="#e6e6e6", text="#000000", accent="#3b8ed0", hover="#cccccc")

    def _apply_theme(self, bg, panel, text, accent, hover):
        self.configure(fg_color=bg)
        self.tabview.configure(
            fg_color=bg if bg == "#000000" else "#FFFFFF",
            segmented_button_fg_color=panel
        )
        self.progress_bar.configure(fg_color=panel, progress_color=accent)
        self.thread_slider.configure(fg_color=panel, progress_color=accent, button_color=accent, button_hover_color=hover)
        for btn in self.theme_buttons:
            btn.configure(fg_color=panel, text_color=text, hover_color=hover)
        for lbl in self.theme_labels:
            lbl.configure(text_color=text)

    def pick_element_color(self, element_type):
        color = colorchooser.askcolor(title="Select Color")[1]
        if not color:
            return

        if element_type == "bg":
            self.configure(fg_color=color)
            self.tabview.configure(fg_color=color)
        elif element_type == "panel":
            self.tabview.configure(segmented_button_fg_color=color)
        elif element_type == "buttons":
            hover = self._darken(color)
            for btn in self.theme_buttons:
                btn.configure(fg_color=color, hover_color=hover)
        elif element_type == "progress_fill":
            hover = self._darken(color)
            self.progress_bar.configure(progress_color=color)
            self.thread_slider.configure(progress_color=color, button_color=color, button_hover_color=hover)
        elif element_type == "progress_track":
            self.progress_bar.configure(fg_color=color)
            self.thread_slider.configure(fg_color=color)
        elif element_type == "text":
            for lbl in self.theme_labels:
                lbl.configure(text_color=color)

    def _darken(self, hex_color, factor=0.8):
        try:
            h = hex_color.lstrip("#")
            r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
            return "#{:02x}{:02x}{:02x}".format(
                max(0, min(255, int(r * factor))),
                max(0, min(255, int(g * factor))),
                max(0, min(255, int(b * factor))),
            )
        except Exception:
            return hex_color

    # ── SETTINGS ──────────────────────────────────────────────────────────────

    def _update_thread_count(self, value):
        self.allocated_threads = int(value)
        self.thread_label.configure(text=f"Thread Allocation: {self.allocated_threads} / {self.max_threads}")

    def registry_install(self):
        if getattr(sys, "frozen", False):
            exe_path = f'"{sys.executable}"'
        else:
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            exe_path = f'"{pythonw}" "{os.path.abspath(__file__)}"'
        try:
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\UniversalConverter")
            winreg.SetValueEx(key, "",     0, winreg.REG_SZ, "Universal Convert...")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{exe_path.split()[0].strip(chr(34))},0")
            sub = winreg.CreateKey(key, "command")
            winreg.SetValueEx(sub, "", 0, winreg.REG_SZ, f'{exe_path} "%1"')
            messagebox.showinfo("Success", "Added to Windows right-click menu.")
        except PermissionError:
            messagebox.showerror("Permission Denied", "Run as Administrator to modify the registry.")

    def registry_uninstall(self):
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\UniversalConverter\command")
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\UniversalConverter")
            messagebox.showinfo("Removed", "Removed from right-click menu.")
        except FileNotFoundError:
            pass
        except PermissionError:
            messagebox.showerror("Permission Denied", "Run as Administrator to modify the registry.")

    # ── CONVERSION ENGINE ──────────────────────────────────────────────────────

    def _set_running(self, is_running):
        self.convert_btn.configure(state="disabled" if is_running else "normal")
        self.format_dropdown.configure(state="disabled" if is_running else "normal")
        self.cancel_btn.configure(state="normal" if is_running else "disabled")

    def cancel_conversion(self):
        if self.current_process:
            self.is_cancelled = True
            self.status_label.configure(text="Cancelling...", text_color="orange")
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.current_process.pid)],
                    creationflags=0x08000000, check=False
                )
            except Exception:
                pass

    def start_conversion(self):
        if not self.input_file:
            messagebox.showwarning("No File", "Please select a file first.")
            return

        choice = self.format_dropdown.get()
        if "AUDIO EXTRACT" in choice:
            messagebox.showwarning("Invalid Selection", "Select a target audio format below the separator.")
            return

        self.is_cancelled = False
        self._set_running(True)
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting...", text_color="white")

        base, src_ext = os.path.splitext(self.input_file)
        output_file = f"{base}_converted.{choice.lower()}"

        # -threads and -thread_type must be output-side flags to control the encoder.
        # Placing them before -i only affects the demuxer, which ignores them for CPU work.
        # -filter_threads controls the filtergraph thread pool separately.
        t = str(self.allocated_threads)
        ffmpeg_args = ["ffmpeg", "-y", "-i", self.input_file]

        # Strip video stream when extracting audio from a video file
        if src_ext.lstrip(".").upper() in FORMATS["VIDEO"] and choice in FORMATS["AUDIO"]:
            ffmpeg_args += ["-vn"]

        ffmpeg_args += [
            "-threads", t,
            "-filter_threads", t,
            "-thread_type", "slice+frame",
            output_file,
        ]

        threading.Thread(target=self._run_worker, args=(ffmpeg_args,), daemon=True).start()

    def _run_worker(self, ffmpeg_args):
        duration_re = re.compile(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})")
        time_re     = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        total = 0.0
        start_wall = None

        try:
            self.current_process = subprocess.Popen(
                ffmpeg_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=0x08000000
            )

            for line in self.current_process.stdout:
                if self.is_cancelled:
                    break

                m = duration_re.search(line)
                if m:
                    total = parse_time(m.group(1))

                m = time_re.search(line)
                if m and total > 0:
                    current = parse_time(m.group(1))
                    progress = current / total

                    if start_wall is None:
                        start_wall = time.monotonic()

                    elapsed = time.monotonic() - start_wall
                    if progress > 0 and elapsed > 0:
                        eta = (elapsed / progress) * (1.0 - progress)
                        mins, secs = divmod(int(eta), 60)
                        eta_str = f"{mins}m {secs:02d}s left" if mins else f"{secs}s left"
                    else:
                        eta_str = "estimating..."

                    self.progress_bar.set(progress)
                    self.status_label.configure(text=f"Converting... {int(progress * 100)}%  —  {eta_str}")
                    self.update_idletasks()

            self.current_process.wait()

        except Exception:
            pass
        finally:
            self.current_process = None
            self._set_running(False)

            if self.is_cancelled:
                self.progress_bar.set(0)
                self.status_label.configure(text="Cancelled", text_color="orange")
            else:
                self.progress_bar.set(1.0)
                self.status_label.configure(text="Done", text_color="green")
                messagebox.showinfo("Done", "Conversion complete.\nFile saved to the source folder.")


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    app = UniversalConverterApp(input_file=file_arg)
    app.mainloop()