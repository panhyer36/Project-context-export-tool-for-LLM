import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading

def generate_full_tree(start_path):
    """
    生成包含所有文件和文件夾的完整目錄結構樹。
    """
    tree_lines = []
    
    # 獲取並添加根目錄名稱
    root_name = os.path.basename(os.path.abspath(start_path))
    tree_lines.append(f"{root_name}/\n")

    for dirpath, dirnames, filenames in os.walk(start_path, topdown=True):
        # 為了保持一致的排序
        dirnames.sort()
        filenames.sort()

        level = dirpath.replace(start_path, '').count(os.sep)
        indent = '│   ' * level
        
        # 處理子資料夾
        for i, d in enumerate(dirnames):
            # 如果是最後一個項目（無論是文件夾還是文件），使用不同的連接符
            is_last = (i == len(dirnames) - 1) and not filenames
            connector = '└── ' if is_last else '├── '
            tree_lines.append(f"{indent}{connector}{d}/\n")
            
        # 處理檔案
        for i, f in enumerate(filenames):
            connector = '└── ' if i == len(filenames) - 1 else '├── '
            tree_lines.append(f"{indent}{connector}{f}\n")
            
    return "".join(tree_lines)

def create_project_summary(input_folder, output_file, excluded_extensions, excluded_dirs, excluded_files, include_tree, progress_text_widget):
    """
    遍歷指定資料夾，讀取檔案內容，並將其寫入單一輸出檔案。
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            progress_text_widget.insert(tk.END, "處理開始...\n", "info")
            
            # --- 1. 寫入完整的目錄結構 (Tree) ---
            if include_tree:
                progress_text_widget.insert(tk.END, "正在生成完整目錄結構 (包含所有檔案)...\n", "info")
                progress_text_widget.see(tk.END)
                # **核心改動：調用新的 tree 函數，不傳遞排除列表**
                tree_structure = generate_full_tree(input_folder)
                outfile.write("專案完整目錄結構:\n")
                outfile.write("```\n")
                outfile.write(tree_structure)
                outfile.write("```\n\n")
                progress_text_widget.insert(tk.END, "完整目錄結構已生成。\n\n", "success")

            # 準備排除列表，供後續內容讀取使用
            excluded_exts = [ext.strip().lower() for ext in excluded_extensions if ext.strip()]
            excluded_dirs_set = {d.strip() for d in excluded_dirs if d.strip()}
            excluded_files_set = {f.strip() for f in excluded_files if f.strip()}
            
            progress_text_widget.insert(tk.END, "--- 檔案內容處理 (將遵守以下排除規則) ---\n", "info_header")
            progress_text_widget.insert(tk.END, f"排除的資料夾: {', '.join(excluded_dirs_set)}\n", "info")
            progress_text_widget.insert(tk.END, f"排除的副檔名: {', '.join(excluded_exts)}\n", "info")
            progress_text_widget.insert(tk.END, f"排除的檔案名: {', '.join(excluded_files_set)}\n\n", "info")

            # --- 2. 遍歷並寫入檔案內容 (遵守排除規則) ---
            for dirpath, dirnames, filenames in os.walk(input_folder, topdown=True):
                # 這裡的排除是為了內容讀取，避免進入 .git 等資料夾
                dirnames[:] = [d for d in dirnames if d not in excluded_dirs_set]
                
                for filename in sorted(filenames):
                    file_path = os.path.join(dirpath, filename)
                    file_ext = os.path.splitext(filename)[1].lower()

                    # 檢查副檔名
                    if file_ext in excluded_exts:
                        message = f"已跳過 (副檔名排除): {file_path}\n"
                        progress_text_widget.insert(tk.END, message, "skipped")
                        progress_text_widget.see(tk.END)
                        continue
                    
                    # 檢查特定檔案名
                    if filename in excluded_files_set:
                        message = f"已跳過 (檔案名排除): {file_path}\n"
                        progress_text_widget.insert(tk.END, message, "skipped")
                        progress_text_widget.see(tk.END)
                        continue

                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()
                        
                        relative_path = os.path.relpath(file_path, input_folder)
                        formatted_relative_path = relative_path.replace('\\', '/')
                        
                        outfile.write(f"({formatted_relative_path}的內容)\n")
                        outfile.write("```\n")
                        outfile.write(content)
                        outfile.write("\n```\n\n")
                        
                        message = f"已處理: {file_path}\n"
                        progress_text_widget.insert(tk.END, message, "processed")
                        
                    except Exception as e:
                        message = f"讀取失敗: {file_path} - {e}\n"
                        progress_text_widget.insert(tk.END, message, "error")
                    
                    progress_text_widget.see(tk.END)

        progress_text_widget.insert(tk.END, f"\n處理完成！檔案已儲存至: {output_file}\n", "success")
        progress_text_widget.see(tk.END)
        messagebox.showinfo("成功", f"專案內容已成功匯出至\n{output_file}")

    except Exception as e:
        messagebox.showerror("錯誤", f"發生錯誤: {e}")
        progress_text_widget.insert(tk.END, f"\n發生錯誤: {e}\n", "error")
        progress_text_widget.see(tk.END)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("專案內容匯出工具 (For LLM) v1.3")
        self.root.geometry("800x680")

        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. 選擇資料夾 ---
        folder_frame = tk.LabelFrame(main_frame, text="1. 選擇要分析的專案資料夾", padx=10, pady=10)
        folder_frame.pack(fill=tk.X, pady=5)
        self.folder_path = tk.StringVar()
        tk.Entry(folder_frame, textvariable=self.folder_path, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(folder_frame, text="瀏覽...", command=self.select_folder).pack(side=tk.LEFT)

        # --- 2. 設定 ---
        config_frame = tk.LabelFrame(main_frame, text="2. 設定", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=5)
        
        # 目錄樹選項
        self.include_tree = tk.BooleanVar(value=True)
        cb_tree = tk.Checkbutton(config_frame, text="在開頭插入專案完整目錄結構 (Tree)", variable=self.include_tree)
        cb_tree.pack(anchor='w')
        tk.Label(config_frame, text=" (此目錄結構會顯示所有檔案與資料夾，忽略下方排除規則)", fg="grey").pack(anchor='w', padx=(20, 0))


        # 排除資料夾
        tk.Label(config_frame, text="\n要排除的資料夾 (僅影響檔案內容匯出):").pack(anchor='w')
        self.exclude_dirs = tk.StringVar(value=".git, .vscode, __pycache__, node_modules, venv, .idea, build, dist")
        tk.Entry(config_frame, textvariable=self.exclude_dirs).pack(fill=tk.X)
        
        # 排除副檔名
        tk.Label(config_frame, text="\n要排除的副檔名 (僅影響檔案內容匯出):").pack(anchor='w')
        self.exclude_exts = tk.StringVar(value=".png, .jpg, .jpeg, .gif, .bmp, .ico, .svg, .webp, .zip, .rar, .7z, .tar, .gz, .exe, .dll, .db, .sqlite3, .log, .pyc, .o, .a, .so, .pt, .pth, .pkl, .bin, .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .mp3, .mp4, .avi, .mov, .csv")
        tk.Entry(config_frame, textvariable=self.exclude_exts).pack(fill=tk.X)
        
        # 排除特定檔案名
        tk.Label(config_frame, text="\n要排除的特定檔案名 (僅影響檔案內容匯出):").pack(anchor='w')
        self.exclude_files = tk.StringVar(value=".DS_Store, Thumbs.db, desktop.ini, .gitkeep")
        tk.Entry(config_frame, textvariable=self.exclude_files).pack(fill=tk.X)

        # --- 3. 開始 ---
        start_button = tk.Button(main_frame, text="3. 開始匯出", command=self.start_processing, bg="#4CAF50", font=("Arial", 12, "bold"))
        start_button.pack(pady=15, fill=tk.X)

        # --- 4. 進度顯示 ---
        progress_frame = tk.LabelFrame(main_frame, text="處理進度", padx=10, pady=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.progress_text = scrolledtext.ScrolledText(progress_frame, wrap=tk.WORD, height=15)
        self.progress_text.pack(fill=tk.BOTH, expand=True)
        # 設定不同訊息的顏色標籤
        self.progress_text.tag_config("info", foreground="blue")
        self.progress_text.tag_config("info_header", foreground="navy", font=("Arial", 10, "bold"))
        self.progress_text.tag_config("success", foreground="green")
        self.progress_text.tag_config("skipped", foreground="orange")
        self.progress_text.tag_config("processed", foreground="black")
        self.progress_text.tag_config("error", foreground="red")

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def start_processing(self):
        input_folder = self.folder_path.get()
        if not input_folder:
            messagebox.showwarning("警告", "請先選擇一個資料夾！")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="請選擇儲存位置與檔名",
            initialfile="project_summary.txt"
        )
        if not output_file:
            return

        self.progress_text.delete('1.0', tk.END)
        
        # 使用執行緒來執行，避免 GUI 卡住
        thread = threading.Thread(
            target=create_project_summary,
            args=(
                input_folder, 
                output_file, 
                self.exclude_exts.get().split(','), 
                self.exclude_dirs.get().split(','), 
                self.exclude_files.get().split(','), 
                self.include_tree.get(), 
                self.progress_text
            )
        )
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()