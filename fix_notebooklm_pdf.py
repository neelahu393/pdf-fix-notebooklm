#!/usr/bin/env python3
"""
NotebookLM PDF 繁體中文破字修復工具 — GUI 版
使用 PyMuPDF 引擎，高容錯率解決繁中渲染問題
"""

import sys
import os
import threading
import tempfile
import shutil
from pathlib import Path


def fix_pdf(input_path: str, output_path: str = None, dpi: int = 200,
            progress_cb=None, log_cb=None) -> str:
    import fitz  # PyMuPDF

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"找不到檔案：{input_path}")

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_fixed.pdf"
    output_path = Path(output_path)

    def log(msg):
        if log_cb:
            log_cb(msg)
        else:
            print(msg)

    log(f"📂 輸入：{input_path.name}")
    log(f"🎯 解析度：{dpi} DPI")

    # 判斷是否為網路磁碟機 (UNC) 路徑
    is_unc = str(input_path).startswith(("\\\\", "//")) or str(output_path).startswith(("\\\\", "//"))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        if is_unc:
            log("🌐 偵測到網路路徑，移至本機暫存區處理以防卡死...")
            local_input = Path(temp_dir) / input_path.name
            local_output = Path(temp_dir) / f"temp_{output_path.name}"
            shutil.copy2(input_path, local_input)
            process_input = local_input
            process_output = local_output
        else:
            process_input = input_path
            process_output = output_path

        log("⏳ 載入 PyMuPDF 渲染引擎...")
        doc = fitz.open(str(process_input))
        out_pdf = fitz.open()

        total = len(doc)
        log(f"📄 共 {total} 頁")
        if total == 0:
            raise ValueError("PDF 沒有任何頁面")

        for i in range(total):
            page = doc.load_page(i)
            # 依指定 DPI 將頁面渲染為圖片
            pix = page.get_pixmap(dpi=dpi)
            # 建立與原頁面等比例的新頁面
            img_page = out_pdf.new_page(width=page.rect.width, height=page.rect.height)
            # 將圖片資料寫入新頁面
            img_page.insert_image(page.rect, stream=pix.tobytes("png"))

            if progress_cb:
                progress_cb(int((i + 1) / total * 90))

        log("💾 儲存處理結果...")
        out_pdf.save(str(process_output))
        out_pdf.close()
        doc.close()

        if is_unc:
            log("📤 寫回網路路徑...")
            shutil.copy2(process_output, output_path)

    if progress_cb:
        progress_cb(100)

    size_mb = output_path.stat().st_size / 1024 / 1024
    log(f"✅ 完成！{output_path.name}（{size_mb:.1f} MB）")
    return str(output_path)


# ── GUI ────────────────────────────────────────────────────────────────────

def run_gui():
    import tkinter as tk
    from tkinter import filedialog, ttk

    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        RootClass = TkinterDnD.Tk
        HAS_DND = True
    except ImportError:
        RootClass = tk.Tk
        HAS_DND = False

    root = RootClass()
    root.title("PDF 繁中破字修復 (PyMuPDF 版)")
    root.geometry("520x540")
    root.resizable(False, True)
    root.configure(bg="#0f0f0f")

    FONT_TITLE  = ("Microsoft JhengHei UI", 15, "bold")
    FONT_LABEL  = ("Microsoft JhengHei UI", 10)
    FONT_SMALL  = ("Microsoft JhengHei UI", 9)
    FONT_MONO   = ("Consolas", 9)

    BG      = "#0f0f0f"
    SURFACE = "#1a1a1a"
    BORDER  = "#2e2e2e"
    ACCENT  = "#e8c84a"
    TEXT    = "#f0ede6"
    MUTED   = "#666666"
    SUCCESS = "#4ade80"
    ERROR   = "#f87171"

    selected_file = tk.StringVar()
    dpi_var       = tk.IntVar(value=200)

    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=24, pady=(22, 0))
    tk.Label(header, text="PDF 修復工具", font=FONT_TITLE,
             bg=BG, fg=TEXT).pack(side="left")
    tk.Label(header, text="NotebookLM 繁中破字專用", font=FONT_SMALL,
             bg=BG, fg=MUTED).pack(side="left", padx=(10, 0), pady=(4, 0))
    tk.Frame(root, height=1, bg=BORDER).pack(fill="x", padx=24, pady=(12, 0))

    drop_frame = tk.Frame(root, bg=SURFACE, bd=0, highlightthickness=2,
                          highlightbackground=BORDER, highlightcolor=ACCENT)
    drop_frame.pack(fill="x", padx=24, pady=16)
    drop_inner = tk.Frame(drop_frame, bg=SURFACE)
    drop_inner.pack(fill="both", padx=2, pady=2)

    drop_icon = tk.Label(drop_inner, text="⬇", font=("Segoe UI Emoji", 28),
                         bg=SURFACE, fg=ACCENT)
    drop_icon.pack(pady=(18, 4))
    drop_hint = tk.Label(drop_inner, text="將 PDF 拖曳至此，或點擊選擇檔案",
                         font=FONT_LABEL, bg=SURFACE, fg=MUTED)
    drop_hint.pack()
    file_label = tk.Label(drop_inner, textvariable=selected_file,
                          font=FONT_SMALL, bg=SURFACE, fg=ACCENT,
                          wraplength=420, justify="center")
    file_label.pack(pady=(4, 14))

    def pick_file(*_):
        path = filedialog.askopenfilename(
            title="選擇 PDF",
            filetypes=[("PDF 檔案", "*.pdf"), ("所有檔案", "*.*")]
        )
        if path:
            selected_file.set(path)
            drop_hint.config(fg=TEXT)

    for w in (drop_frame, drop_inner, drop_icon, drop_hint, file_label):
        w.bind("<Button-1>", pick_file)

    if HAS_DND:
        def on_drop(event):
            path = event.data.strip().strip("{}")
            selected_file.set(path)
            drop_hint.config(fg=TEXT)
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind("<<Drop>>", on_drop)

    opt_frame = tk.Frame(root, bg=BG)
    opt_frame.pack(fill="x", padx=24)
    tk.Label(opt_frame, text="輸出解析度", font=FONT_LABEL,
             bg=BG, fg=MUTED).pack(side="left")
    for label, val in [("200 DPI（簡報用）", 200), ("300 DPI（高清列印）", 300)]:
        tk.Radiobutton(opt_frame, text=label, variable=dpi_var, value=val,
                       font=FONT_SMALL, bg=BG, fg=TEXT,
                       selectcolor=BG, activebackground=BG,
                       activeforeground=ACCENT).pack(side="left", padx=(14, 0))

    prog_frame = tk.Frame(root, bg=BG)
    prog_frame.pack(fill="x", padx=24, pady=(14, 0))
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Gold.Horizontal.TProgressbar",
                    troughcolor=SURFACE, background=ACCENT,
                    bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)
    progress = ttk.Progressbar(prog_frame, style="Gold.Horizontal.TProgressbar",
                                length=472, mode="determinate")
    progress.pack()

    log_frame = tk.Frame(root, bg=SURFACE, highlightthickness=1,
                         highlightbackground=BORDER)
    log_frame.pack(fill="both", padx=24, pady=(10, 0), ipady=4)
    log_text = tk.Text(log_frame, height=5, bg=SURFACE, fg=TEXT,
                       font=FONT_MONO, bd=0, relief="flat",
                       state="disabled", wrap="word", insertbackground=ACCENT)
    log_text.pack(fill="both", padx=8, pady=4)

    def log(msg, color=None):
        log_text.config(state="normal")
        tag = f"c{id(msg)}"
        log_text.insert("end", msg + "\n", tag)
        if color:
            log_text.tag_config(tag, foreground=color)
        log_text.see("end")
        log_text.config(state="disabled")

    def set_progress(v):
        progress["value"] = v
        root.update_idletasks()

    def do_fix():
        path = selected_file.get().strip()
        if not path:
            log("⚠ 請先選擇 PDF 檔案", ERROR)
            return
        btn.config(state="disabled", text="處理中…")
        progress["value"] = 0

        def worker():
            try:
                result = fix_pdf(
                    path,
                    dpi=dpi_var.get(),
                    progress_cb=lambda v: root.after(0, set_progress, v),
                    log_cb=lambda m: root.after(0, log, m),
                )
                root.after(0, log, f"🎉 輸出：{result}", SUCCESS)
            except Exception as e:
                root.after(0, log, f"❌ {e}", ERROR)
            finally:
                root.after(0, lambda: btn.config(state="normal", text="開始修復"))

        threading.Thread(target=worker, daemon=True).start()

    btn = tk.Button(root, text="開始修復",
                    font=("Microsoft JhengHei UI", 11, "bold"),
                    bg=ACCENT, fg="#0f0f0f",
                    activebackground="#f5d96b", activeforeground="#0f0f0f",
                    relief="flat", bd=0, cursor="hand2",
                    padx=0, pady=10, command=do_fix)
    btn.pack(fill="x", padx=24, pady=(12, 18))

    log("準備就緒，請選擇或拖曳 PDF 檔案。")
    root.mainloop()


def main():
    if len(sys.argv) >= 2:
        input_file  = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        dpi_val     = int(sys.argv[3]) if len(sys.argv) > 3 else 200
        try:
            result = fix_pdf(input_file, output_file, dpi_val)
            print(f"\n🎉 修復完成：{result}")
        except Exception as e:
            print(f"\n❌ 錯誤：{e}")
        input("\n按 Enter 關閉...")
    else:
        run_gui()


if __name__ == "__main__":
    main()