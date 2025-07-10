import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import threading

def generate_full_tree(start_path):
    """
    生成排除隱藏文件和文件夾的完整目錄結構樹。
    """
    def build_tree_structure(path, prefix="", is_last=True):
        """遞歸構建目錄樹結構"""
        lines = []
        
        if not os.path.exists(path):
            return lines
            
        # 獲取當前目錄的所有項目
        try:
            items = os.listdir(path)
        except PermissionError:
            return lines
            
        # 過濾掉隱藏檔案和資料夾
        items = [item for item in items if not item.startswith('.')]
        items.sort()
        
        # 分離資料夾和檔案
        dirs = []
        files = []
        
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                dirs.append(item)
            else:
                files.append(item)
        
        # 先處理資料夾
        total_items = len(dirs) + len(files)
        for i, dirname in enumerate(dirs):
            is_last_item = (i == total_items - 1)
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{dirname}/")
            
            # 遞歸處理子目錄
            subdir_path = os.path.join(path, dirname)
            extension = "    " if is_last_item else "│   "
            sub_lines = build_tree_structure(subdir_path, prefix + extension, True)
            lines.extend(sub_lines)
        
        # 再處理檔案
        for i, filename in enumerate(files):
            item_index = len(dirs) + i
            is_last_item = (item_index == total_items - 1)
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{filename}")
        
        return lines
    
    # 獲取根目錄名稱
    root_name = os.path.basename(os.path.abspath(start_path))
    result_lines = [f"{root_name}/"]
    
    # 構建目錄樹
    tree_lines = build_tree_structure(start_path)
    result_lines.extend(tree_lines)
    
    return "\n".join(result_lines)


def create_project_summary(input_folder, output_file, selected_files, include_tree, progress_text_widget, success_callback=None):
    """
    根據選擇的檔案列表，讀取內容並寫入單一輸出檔案。
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            progress_text_widget.insert(tk.END, "🚀 處理開始...\n", "info")
            
            # --- 1. 寫入完整目錄結構 (Tree) ---
            if include_tree:
                progress_text_widget.insert(tk.END, "📂 正在生成專案完整目錄結構...\n", "info")
                progress_text_widget.see(tk.END)
                tree_structure = generate_full_tree(input_folder)
                outfile.write("專案完整目錄結構 (已排除隱藏檔案):\n")
                outfile.write("```\n")
                outfile.write(tree_structure)
                outfile.write("```\n\n")
                progress_text_widget.insert(tk.END, "✅ 完整目錄結構已生成\n\n", "success")

            progress_text_widget.insert(tk.END, "📝 開始處理選定檔案內容...\n", "info_header")

            # --- 2. 遍歷選擇的檔案並寫入內容 ---
            for file_path in sorted(selected_files):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                    
                    relative_path = os.path.relpath(file_path, input_folder)
                    formatted_relative_path = relative_path.replace('\\', '/')
                    
                    outfile.write(f"({formatted_relative_path}的內容)\n")
                    outfile.write("```\n")
                    outfile.write(content)
                    outfile.write("\n```\n\n")
                    
                    message = f"✅ 已處理: {file_path}\n"
                    progress_text_widget.insert(tk.END, message, "processed")
                    
                except Exception as e:
                    message = f"❌ 讀取失敗: {file_path} - {e}\n"
                    progress_text_widget.insert(tk.END, message, "error")
                
                progress_text_widget.see(tk.END)

        progress_text_widget.insert(tk.END, f"\n🎉 處理完成！檔案已儲存至: {output_file}\n", "success")
        progress_text_widget.insert(tk.END, "✨ 匯出成功完成！您可以打開檔案查看結果。\n", "success")
        progress_text_widget.see(tk.END)
        
        # 調用成功回調函數（在主線程中執行）
        if success_callback:
            success_callback(output_file)

    except Exception as e:
        error_message = f"發生錯誤: {str(e)}" if str(e) else "發生未知錯誤"
        progress_text_widget.insert(tk.END, f"\n❌ {error_message}\n", "error")
        progress_text_widget.see(tk.END)

class ModernButton(tk.Button):
    """現代化按鈕類別"""
    def __init__(self, parent, **kwargs):
        # 設定預設樣式
        default_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "borderwidth": 0,
            "cursor": "hand2",
            "padx": 20,
            "pady": 10
        }
        default_style.update(kwargs)
        super().__init__(parent, **default_style)
        
        # 添加懸停效果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # 儲存原始顏色
        self.original_bg = default_style.get("bg", "#007ACC")
        
    def _on_enter(self, event):
        self.config(bg=self._darken_color(self.original_bg))
        
    def _on_leave(self, event):
        self.config(bg=self.original_bg)
    
    def _darken_color(self, color):
        """將顏色變暗"""
        if color == "#007ACC": return "#005a99"
        if color == "#28A745": return "#1e7e34"
        if color == "#6C757D": return "#545b62"
        return color

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 AI 專案內容匯出工具 v2.0")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f8f9fa")
        
        # 設定主題樣式
        self.setup_styles()
        
        # 創建主要容器
        main_container = tk.Frame(root, bg="#f8f9fa")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 標題區域
        self.create_header(main_container)
        
        # 內容區域
        content_frame = tk.Frame(main_container, bg="#f8f9fa")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左側面板
        left_panel = tk.Frame(content_frame, bg="#ffffff", relief="solid", borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 右側面板
        right_panel = tk.Frame(content_frame, bg="#ffffff", relief="solid", borderwidth=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)

    def setup_styles(self):
        """設定主題樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置 Treeview 樣式
        style.configure("Modern.Treeview", 
                       background="#ffffff",
                       foreground="#212529",
                       fieldbackground="#ffffff",
                       font=("Segoe UI", 10))
        
        style.configure("Modern.Treeview.Heading",
                       background="#e9ecef",
                       foreground="#495057",
                       font=("Segoe UI", 11, "bold"))

    def create_header(self, parent):
        """創建標題區域"""
        header_frame = tk.Frame(parent, bg="#ffffff", height=80, relief="solid", borderwidth=1)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # 標題
        title_label = tk.Label(header_frame, 
                              text="🤖 AI 專案內容匯出工具", 
                              font=("Segoe UI", 20, "bold"),
                              fg="#007ACC",
                              bg="#ffffff")
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # 副標題
        subtitle_label = tk.Label(header_frame,
                                 text="輕鬆將專案檔案匯出為 LLM 友善格式",
                                 font=("Segoe UI", 12),
                                 fg="#6C757D",
                                 bg="#ffffff")
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20), pady=25, anchor="s")

    def setup_left_panel(self, parent):
        """設定左側面板"""
        # 面板標題
        panel_title = tk.Label(parent, 
                              text="📁 專案設定",
                              font=("Segoe UI", 16, "bold"),
                              fg="#495057",
                              bg="#ffffff")
        panel_title.pack(pady=20, padx=20, anchor="w")
        
        # --- 1. 選擇資料夾 ---
        folder_section = tk.Frame(parent, bg="#ffffff")
        folder_section.pack(fill=tk.X, padx=20, pady=10)
        
        folder_label = tk.Label(folder_section,
                               text="選擇專案資料夾",
                               font=("Segoe UI", 12, "bold"),
                               fg="#495057",
                               bg="#ffffff")
        folder_label.pack(anchor="w", pady=(0, 5))
        
        folder_input_frame = tk.Frame(folder_section, bg="#ffffff")
        folder_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.folder_path = tk.StringVar()
        folder_entry = tk.Entry(folder_input_frame, 
                               textvariable=self.folder_path, 
                               state="readonly",
                               font=("Segoe UI", 10),
                               bg="#f8f9fa",
                               relief="solid",
                               borderwidth=1)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ModernButton(folder_input_frame, 
                                 text="📂 瀏覽",
                                 command=self.select_folder,
                                 bg="#007ACC",
                                 fg="white")
        browse_btn.pack(side=tk.RIGHT)
        
        # --- 2. 檔案樹狀圖 ---
        tree_section = tk.Frame(parent, bg="#ffffff")
        tree_section.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tree_label = tk.Label(tree_section,
                             text="選擇要匯出的檔案",
                             font=("Segoe UI", 12, "bold"),
                             fg="#495057",
                             bg="#ffffff")
        tree_label.pack(anchor="w", pady=(0, 5))
        
        tree_container = tk.Frame(tree_section, bg="#e9ecef", relief="solid", borderwidth=1)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tree = ttk.Treeview(tree_container, show="tree", style="Modern.Treeview")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 滾動條
        tree_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        tree_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # 儲存 Treeview item 的狀態
        self.checked_items = {}
        self.item_paths = {}
        self.tree.bind("<Button-1>", self._on_tree_click)
        
        # 選項
        options_frame = tk.Frame(tree_section, bg="#ffffff")
        options_frame.pack(fill=tk.X)
        
        self.include_tree = tk.BooleanVar(value=True)
        tree_checkbox = tk.Checkbutton(options_frame,
                                     text="📋 在開頭插入完整專案目錄結構",
                                     variable=self.include_tree,
                                     font=("Segoe UI", 10),
                                     bg="#ffffff",
                                     fg="#495057")
        tree_checkbox.pack(anchor="w")
        
        # --- 3. 開始按鈕 ---
        start_btn = ModernButton(parent,
                               text="🚀 開始匯出",
                               command=self.start_processing,
                               bg="#28A745",
                               fg="white",
                               font=("Segoe UI", 14, "bold"))
        start_btn.pack(pady=20, padx=20, fill=tk.X)

    def setup_right_panel(self, parent):
        """設定右側面板"""
        # 面板標題
        panel_title = tk.Label(parent,
                              text="📊 處理進度",
                              font=("Segoe UI", 16, "bold"),
                              fg="#495057",
                              bg="#ffffff")
        panel_title.pack(pady=20, padx=20, anchor="w")
        
        # 進度顯示區域
        progress_container = tk.Frame(parent, bg="#ffffff")
        progress_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 進度文字區域
        text_container = tk.Frame(progress_container, bg="#f8f9fa", relief="solid", borderwidth=1)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        self.progress_text = scrolledtext.ScrolledText(text_container,
                                                     wrap=tk.WORD,
                                                     font=("Consolas", 10),
                                                     bg="#ffffff",
                                                     fg="#212529",
                                                     relief="flat",
                                                     borderwidth=0)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 設定不同訊息的顏色標籤
        self.progress_text.tag_config("info", foreground="#007ACC", font=("Consolas", 10))
        self.progress_text.tag_config("info_header", foreground="#495057", font=("Consolas", 10, "bold"))
        self.progress_text.tag_config("success", foreground="#28A745", font=("Consolas", 10, "bold"))
        self.progress_text.tag_config("processed", foreground="#212529", font=("Consolas", 9))
        self.progress_text.tag_config("error", foreground="#DC3545", font=("Consolas", 10, "bold"))
        
        # 初始提示
        welcome_text = """🎯 歡迎使用 AI 專案內容匯出工具！

📋 使用步驟：
1️⃣ 點擊「瀏覽」選擇您的專案資料夾
2️⃣ 在檔案樹中勾選要匯出的檔案
3️⃣ 點擊「開始匯出」按鈕
4️⃣ 選擇儲存位置，完成匯出"""
        
        self.progress_text.insert(tk.END, welcome_text, "info")

    def _populate_tree(self, start_path):
        """填充 Treeview 控件，顯示檔案結構"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.checked_items.clear()
        self.item_paths.clear()

        root_name = os.path.basename(start_path)
        root_iid = self.tree.insert("", "end", text=f"✅ 📁 {root_name}", open=True)
        self.item_paths[root_iid] = start_path
        self.checked_items[root_iid] = True
        
        path_to_iid = {start_path: root_iid}

        for dirpath, dirnames, filenames in os.walk(start_path, topdown=True):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]
            
            parent_iid = path_to_iid.get(dirpath)
            if not parent_iid: continue

            for d in sorted(dirnames):
                full_path = os.path.join(dirpath, d)
                iid = self.tree.insert(parent_iid, "end", text=f"✅ 📁 {d}", open=False)
                path_to_iid[full_path] = iid
                self.item_paths[iid] = full_path
                self.checked_items[iid] = True

            for f in sorted(filenames):
                full_path = os.path.join(dirpath, f)
                file_icon = self._get_file_icon(f)
                iid = self.tree.insert(parent_iid, "end", text=f"✅ {file_icon} {f}", open=False)
                self.item_paths[iid] = full_path
                self.checked_items[iid] = True

    def _get_file_icon(self, filename):
        """根據檔案類型返回對應的圖標"""
        ext = os.path.splitext(filename)[1].lower()
        icon_map = {
            '.py': '🐍', '.js': '🟨', '.ts': '🔷', '.html': '🌐', '.css': '🎨',
            '.json': '📋', '.md': '📝', '.txt': '📄', '.yml': '⚙️', '.yaml': '⚙️',
            '.xml': '📊', '.csv': '📈', '.sql': '🗃️', '.sh': '🖥️', '.bat': '⚡',
            '.php': '🐘', '.java': '☕', '.cpp': '⚡', '.c': '🔧', '.h': '📋',
            '.go': '🐹', '.rs': '🦀', '.swift': '🍎', '.kt': '🤖', '.dart': '🎯'
        }
        return icon_map.get(ext, '📄')

    def _update_tree_item_visual(self, iid):
        """更新單個 Treeview item 的複選框外觀"""
        checked = self.checked_items.get(iid, False)
        current_text = self.tree.item(iid, "text")
        
        # 移除舊的複選框
        if current_text.startswith(('✅ ', '❌ ')):
            base_text = current_text[2:]
        else:
            base_text = current_text
        
        new_text = f"{'✅' if checked else '❌'} {base_text}"
        self.tree.item(iid, text=new_text)

    def _toggle_check(self, iid):
        """切換一個 item 的選中狀態，並遞歸更新所有子項"""
        new_state = not self.checked_items.get(iid, False)
        
        items_to_update = [iid]
        queue = list(self.tree.get_children(iid))
        while queue:
            item = queue.pop(0)
            items_to_update.append(item)
            queue.extend(self.tree.get_children(item))
            
        for item_iid in items_to_update:
            self.checked_items[item_iid] = new_state
            self._update_tree_item_visual(item_iid)
            
    def _on_tree_click(self, event):
        """處理 Treeview 上的點擊事件"""
        iid = self.tree.identify_row(event.y)
        if iid and self.tree.identify_column(event.x) == '#0':
            self._toggle_check(iid)

    def _get_selected_files(self):
        """從 Treeview 收集所有被選中的檔案的完整路徑"""
        selected_files = []
        for iid, checked in self.checked_items.items():
            if checked:
                path = self.item_paths.get(iid)
                if path and os.path.isfile(path):
                    selected_files.append(path)
        return selected_files

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self._populate_tree(folder_selected)
            
            # 更新進度顯示
            self.progress_text.delete('1.0', tk.END)
            self.progress_text.insert(tk.END, f"📁 已選擇專案資料夾: {folder_selected}\n\n", "success")
            self.progress_text.insert(tk.END, "💡 提示：點擊檔案樹中的項目來選擇或取消選擇檔案\n", "info")
            self.progress_text.insert(tk.END, "✅ = 已選擇  ❌ = 未選擇\n\n", "info")
            self.progress_text.insert(tk.END, "準備好後，點擊「開始匯出」按鈕！🚀", "info_header")

    def start_processing(self):
        input_folder = self.folder_path.get()
        if not input_folder:
            messagebox.showwarning("⚠️ 警告", "請先選擇一個資料夾！")
            return

        selected_files = self._get_selected_files()
        if not selected_files:
            messagebox.showwarning("⚠️ 警告", "您沒有選擇任何要匯出的檔案！")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="選擇儲存位置與檔名",
            initialfile="project_summary.txt"
        )
        if not output_file:
            return

        self.progress_text.delete('1.0', tk.END)
        
        def success_callback(saved_file):
            """成功完成後的回調函數，安全地在主線程中顯示對話框"""
            self.root.after(0, lambda: messagebox.showinfo("✅ 成功", f"專案內容已成功匯出至\n{saved_file}"))
        
        thread = threading.Thread(
            target=create_project_summary,
            args=(
                input_folder, 
                output_file, 
                selected_files,
                self.include_tree.get(), 
                self.progress_text,
                success_callback
            )
        )
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()