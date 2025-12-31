import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import chardet
import difflib

class TextMapperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Text Translation Mapper Pro — 1.5')
        self.geometry('1350x950')
        self.minsize(1200, 750)

        # Estados
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.folder_c = tk.StringVar()

        # Codificações
        self.encoding_options = ['utf-8', 'cp1252', 'utf-16-le', 'utf-16-be', 'latin-1', 'shift-jis', 'big5']
        self.encoding_ab = tk.StringVar(value='utf-8')
        self.encoding_c_out = tk.StringVar(value='utf-8')

        # Opções
        self.dark_mode = tk.BooleanVar(value=False)
        self.recursive_search = tk.BooleanVar(value=True)
        self.file_extension = tk.StringVar(value='.txt')
        self.match_by_filename_only = tk.BooleanVar(value=False)
        
        # Fuzzy Match
        self.fuzzy_threshold = tk.DoubleVar(value=100.0)

        self.mappings = {}
        self.mappings_by_name = {}

        self.style = ttk.Style(self)
        self._setup_styles()
        self._build_ui()
        self._apply_theme()

    def _setup_styles(self):
        self.style.configure("TButton", padding=4)
        self.style.configure("Header.TLabel", font=("Helvetica", 10, "bold"))
        self.style.configure("Action.TButton", font=("Helvetica", 9, "bold"))

    def _apply_theme(self):
        if self.dark_mode.get():
            bg, fg, entry_bg = "#2d2d2d", "#ffffff", "#3d3d3d"
            self.configure(bg=bg)
            self.style.theme_use('clam')
            for widget in ["TFrame", "TLabelframe", "TLabelframe.Label", "TLabel", "TCheckbutton"]:
                self.style.configure(widget, background=bg, foreground=fg)
            self.style.configure("TButton", background="#454545", foreground=fg)
            self.style.configure("Treeview", background="#3d3d3d", foreground=fg, fieldbackground="#3d3d3d")
            self.style.configure("Treeview.Heading", background="#454545", foreground=fg)
            self.log_text.configure(bg=entry_bg, fg="#00ff00", insertbackground=fg)
            self.files_listbox.configure(bg="#3d3d3d", fg=fg, selectbackground="#0078d4")
        else:
            self.style.theme_use('default')
            bg = "#f0f0f0"
            self.configure(bg=bg)
            self.style.configure("TFrame", background=bg)
            self.style.configure("TLabelframe", background=bg)
            self.style.configure("TLabel", background=bg, foreground="#000000")
            self.log_text.configure(bg="white", fg="black", insertbackground="black")
            self.files_listbox.configure(bg="white", fg="black", selectbackground="#0078d4")
            self.style.configure("Treeview", background="white", foreground="black", fieldbackground="white")

    def _toggle_theme(self):
        self._apply_theme()

    def _build_ui(self):
        main_container = ttk.Frame(self, padding="12")
        main_container.pack(fill='both', expand=True)

        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill='x', pady=(0, 8))
        ttk.Button(toolbar, text="📖 Guia de Uso / Ajuda", command=self._show_instructions).pack(side='left')
        ttk.Checkbutton(toolbar, text="Modo Escuro", variable=self.dark_mode, command=self._toggle_theme).pack(side='right')

        folders_frame = ttk.LabelFrame(main_container, text=" Configurações de Pastas ", padding="10")
        folders_frame.pack(fill='x', pady=(0, 10))
        for i, (label_text, var) in enumerate([
            ("Pasta A (Originais):", self.folder_a),
            ("Pasta B (Traduções):", self.folder_b),
            ("Pasta C (A Traduzir):", self.folder_c)
        ]):
            ttk.Label(folders_frame, text=label_text, style="Header.TLabel").grid(row=i, column=0, sticky='w', pady=4)
            ttk.Entry(folders_frame, textvariable=var, width=80).grid(row=i, column=1, padx=8, pady=4, sticky='ew')
            ttk.Button(folders_frame, text="Procurar", command=lambda v=var: self._select_folder(v)).grid(row=i, column=2, padx=4)
        folders_frame.columnconfigure(1, weight=1)

        actions_line = ttk.Frame(main_container)
        actions_line.pack(fill='x', pady=(0, 10))
        
        config_subframe = ttk.Frame(actions_line)
        config_subframe.pack(side='left', fill='x')
        ttk.Label(config_subframe, text="Enc A/B:").pack(side='left', padx=(0, 2))
        ttk.Combobox(config_subframe, textvariable=self.encoding_ab, values=self.encoding_options, width=9, state="readonly").pack(side='left', padx=2)
        ttk.Label(config_subframe, text="Enc C/Out:").pack(side='left', padx=(10, 2))
        ttk.Combobox(config_subframe, textvariable=self.encoding_c_out, values=self.encoding_options, width=9, state="readonly").pack(side='left', padx=2)
        ttk.Label(config_subframe, text="Ext:").pack(side='left', padx=(10, 2))
        ttk.Entry(config_subframe, textvariable=self.file_extension, width=7).pack(side='left', padx=2)
        
        self.btn_apply = ttk.Button(actions_line, text="2. Aplicar em C + Relatório", command=self.apply_mappings, state='disabled', style="Action.TButton")
        self.btn_apply.pack(side='right', padx=4)
        self.btn_build = ttk.Button(actions_line, text="1. Construir Mapeamentos (A ↔ B)", command=self.build_mappings, style="Action.TButton")
        self.btn_build.pack(side='right', padx=4)

        options_frame = ttk.LabelFrame(main_container, text=" Opções de Processamento ", padding="10")
        options_frame.pack(fill='x', pady=(0, 10))
        search_subframe = ttk.Frame(options_frame)
        search_subframe.pack(side='left', fill='x')
        ttk.Checkbutton(search_subframe, text="Subpastas", variable=self.recursive_search).pack(side='left', padx=(0, 15))
        ttk.Checkbutton(search_subframe, text="Apenas Nome (Ignorar Estrutura)", variable=self.match_by_filename_only).pack(side='left', padx=5)
        fuzzy_subframe = ttk.Frame(options_frame)
        fuzzy_subframe.pack(side='right', fill='x')
        ttk.Label(fuzzy_subframe, text="Fuzzy Match:").pack(side='left', padx=(20, 5))
        self.fuzzy_scale = ttk.Scale(fuzzy_subframe, from_=0, to=100, orient='horizontal', variable=self.fuzzy_threshold, length=200)
        self.fuzzy_scale.pack(side='left', padx=5)
        self.fuzzy_label = ttk.Label(fuzzy_subframe, text=f"{self.fuzzy_threshold.get():.0f}%", width=4)
        self.fuzzy_label.pack(side='left', padx=2)
        def update_fuzzy_label(val): self.fuzzy_label.config(text=f"{float(val):.0f}%")
        self.fuzzy_scale.config(command=update_fuzzy_label)

        paned = ttk.PanedWindow(main_container, orient='horizontal')
        paned.pack(fill='both', expand=True, pady=(0, 10))
        list_frame = ttk.LabelFrame(paned, text=" Arquivos Comuns (A/B) ", padding="5")
        self.files_listbox = tk.Listbox(list_frame, font=("Segoe UI", 9))
        self.files_listbox.pack(fill='both', expand=True)
        self.files_listbox.bind('<<ListboxSelect>>', self._on_file_select)
        paned.add(list_frame, weight=1)
        preview_frame = ttk.LabelFrame(paned, text=" Preview do Dicionário ", padding="5")
        self.tree = ttk.Treeview(preview_frame, columns=('idx', 'orig', 'trans'), show='headings')
        for col, txt, w in [('idx', '№', 50), ('orig', 'Original (A)', 350), ('trans', 'Tradução (B)', 350)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor='w' if col != 'idx' else 'center')
        self.tree.pack(fill='both', expand=True)
        paned.add(preview_frame, weight=3)

        self.progress = ttk.Progressbar(main_container, mode='determinate')
        self.progress.pack(fill='x', pady=(0, 5))
        self.log_text = tk.Text(main_container, height=8, state='disabled', font=("Consolas", 9))
        self.log_text.pack(fill='x')

    def _log(self, message, level="INFO"):
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{level}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _select_folder(self, var):
        path = filedialog.askdirectory()
        if path: var.set(path)

    def _get_pattern(self):
        ext = self.file_extension.get().strip()
        if not ext.startswith('.'): ext = '.' + ext
        return f"**/*{ext}" if self.recursive_search.get() else f"*{ext}"

    def _read_file(self, path, fallback_var):
        try:
            with open(path, 'rb') as f: raw = f.read()
        except: return ["<ERRO>\n"]
        if not raw: return ["\n"]
        bom_map = {b'\xef\xbb\xbf': 'utf-8-sig', b'\xff\xfe': 'utf-16-le', b'\xfe\xff': 'utf-16-be'}
        for bom, enc in bom_map.items():
            if raw.startswith(bom):
                try: return raw.decode(enc).splitlines(keepends=True)
                except: pass
        detector = chardet.UniversalDetector()
        for line in raw.splitlines(keepends=True)[:200]:
            detector.feed(line)
            if detector.done: break
        detector.close()
        if detector.result['encoding'] and detector.result['confidence'] > 0.8:
            try: return raw.decode(detector.result['encoding']).splitlines(keepends=True)
            except: pass
        for enc in ['utf-8', 'cp1252', 'utf-16', 'latin-1', fallback_var.get().lower()]:
            try: return raw.decode(enc).splitlines(keepends=True)
            except: continue
        return raw.decode('utf-8', errors='replace').splitlines(keepends=True)

    def build_mappings(self):
        if not self.folder_a.get() or not self.folder_b.get():
            messagebox.showerror("Erro", "Selecione pastas A e B.")
            return
        pattern = self._get_pattern()
        self.btn_build.config(state='disabled')
        self.files_listbox.delete(0, 'end')
        self.tree.delete(*self.tree.get_children())
        self.mappings.clear()
        self.mappings_by_name.clear()

        def worker():
            path_a, path_b = Path(self.folder_a.get()), Path(self.folder_b.get())
            files_a = {f.relative_to(path_a).as_posix(): f for f in path_a.glob(pattern)}
            files_b = {f.relative_to(path_b).as_posix(): f for f in path_b.glob(pattern)}
            common = sorted(set(files_a.keys()) & set(files_b.keys()))
            self.after(0, lambda: self.progress.config(maximum=len(common), value=0))
            for i, rel in enumerate(common):
                lines_a = self._read_file(files_a[rel], self.encoding_ab)
                lines_b = self._read_file(files_b[rel], self.encoding_ab)
                mapping_dict = {a.strip(): b for a, b in zip(lines_a, lines_b)}
                self.mappings[rel] = mapping_dict
                fname = Path(rel).name
                if fname not in self.mappings_by_name: self.mappings_by_name[fname] = mapping_dict
                self.after(0, lambda d=rel: self.files_listbox.insert('end', d))
                self.after(0, lambda v=i+1: self.progress.config(value=v))
            self.after(0, self._build_finished)
        threading.Thread(target=worker, daemon=True).start()

    def _build_finished(self):
        self.btn_build.config(state='normal')
        if self.mappings: self.btn_apply.config(state='normal')
        messagebox.showinfo("Sucesso", f"Dicionários criados!\n{len(self.mappings)} arquivos mapeados.")

    def _on_file_select(self, event):
        sel = self.files_listbox.curselection()
        if not sel: return
        fname = self.files_listbox.get(sel[0])
        mapping = self.mappings.get(fname)
        if not mapping: return
        self.tree.delete(*self.tree.get_children())
        for idx, (orig, trans) in enumerate(mapping.items(), 1):
            if orig: self.tree.insert('', 'end', values=(idx, orig, trans.rstrip('\n\r')))

    def apply_mappings(self):
        if not self.folder_c.get():
            messagebox.showerror("Erro", "Selecione a pasta C.")
            return
        
        parent_dir = Path(self.folder_c.get()).parent
        out_dir_name = Path(self.folder_c.get()).name + "_TRA"
        out_dir = parent_dir / out_dir_name
        out_dir.mkdir(exist_ok=True)
        report_path = parent_dir / f"relatorio_{out_dir_name}.txt"
        
        self.btn_apply.config(state='disabled')
        threshold = self.fuzzy_threshold.get() / 100.0
        by_name_only = self.match_by_filename_only.get()

        def worker():
            pattern = self._get_pattern()
            files_c_paths = list(Path(self.folder_c.get()).glob(pattern))
            self.after(0, lambda: self.progress.config(maximum=len(files_c_paths), value=0))
            untranslated = {}
            processed = 0
            for i, file_c in enumerate(files_c_paths):
                rel = file_c.relative_to(Path(self.folder_c.get())).as_posix()
                mapping = self.mappings_by_name.get(file_c.name, {}) if by_name_only else self.mappings.get(rel, {})
                lines_c = self._read_file(file_c, self.encoding_c_out)
                output, issues_fail, issues_fuzzy = [], [], []
                
                if not mapping:
                    output = lines_c
                    issues_fail.append("[!] Sem mapeamento encontrado para este arquivo.")
                else:
                    keys = [k for k in mapping.keys() if k]
                    for idx, line in enumerate(lines_c, 1):
                        s = line.strip()
                        if not s: output.append(line); continue
                        if s in mapping: output.append(mapping[s]); continue
                        
                        matches = difflib.get_close_matches(s, keys, n=1, cutoff=threshold) if threshold < 1.0 else []
                        if matches:
                            best = matches[0]
                            sim = difflib.SequenceMatcher(None, s, best).ratio()
                            output.append(mapping[best])
                            issues_fuzzy.append(f"L{idx}: [FUZZY {sim*100:.0f}%] \"{s}\"")
                        else:
                            output.append(line)
                            issues_fail.append(f"L{idx}: [FALHA] \"{s}\"")
                
                if issues_fail or issues_fuzzy:
                    # GARANTIA DE ORDEM: Primeiro Falhas, depois Fuzzy
                    untranslated[rel] = issues_fail + issues_fuzzy
                
                out_file = out_dir / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(out_file, 'w', encoding=self.encoding_c_out.get(), newline='') as f: f.writelines(output)
                except:
                    with open(out_file, 'w', encoding='utf-8', newline='') as f: f.writelines(output)
                processed += 1
                self.after(0, lambda v=i+1: self.progress.config(value=v))
            
            with open(report_path, 'w', encoding='utf-8') as r:
                r.write(f"RELATÓRIO v1.5 - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                r.write(f"Modo: {'Nome' if by_name_only else 'Estrutura'} | Fuzzy: {threshold*100:.0f}%\n")
                r.write(f"Pasta de Saída: {out_dir_name}\n")
                r.write("="*80 + "\n\n")
                for p, iss in untranslated.items():
                    r.write(f"ARQUIVO: {p}\n")
                    # Escreve as falhas primeiro
                    for item in iss:
                        if "[FALHA]" in item: r.write(f"  {item}\n")
                    # Escreve os fuzzy depois
                    for item in iss:
                        if "[FUZZY" in item: r.write(f"  {item}\n")
                    # Escreve avisos gerais
                    for item in iss:
                        if "[!]" in item: r.write(f"  {item}\n")
                    r.write("-" * 40 + "\n")
            
            self.after(0, lambda: self._apply_finished(processed, out_dir, report_path))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_finished(self, count, out_dir, report):
        self.btn_apply.config(state='normal')
        self._log(f"Concluído: {count} arquivos traduzidos.")
        messagebox.showinfo("Concluído!", f"Tradução finalizada!\nRelatório: {report}")

    def _show_instructions(self):
        help_window = tk.Toplevel(self)
        help_window.title("Ajuda v1.5")
        help_window.geometry("600x450")
        txt = tk.Text(help_window, wrap='word', padx=10, pady=10)
        instructions = """TEXT TRANSLATION MAPPER PRO 1.5 — FUZZY MATCH IMPLEMENTADO

NOVO NA VERSÃO 1.5:
→ Fuzzy Match: Agora o programa pode encontrar traduções mesmo que a linha original em C não seja 100% idêntica à de A.
→ Controle de Limiar: Você pode ajustar a sensibilidade do Fuzzy Match na interface. 
   - 100%: Apenas matches exatos (comportamento antigo).
   - 90%: Aceita pequenas variações (pontuação, espaços, typos).

---
1. CONCEITO DAS PASTAS
---
• PASTA A (Originais): Arquivos originais (ex: Inglês).
• PASTA B (Traduções): Mesmos arquivos de A, mas traduzidos (ex: Português).
• PASTA C (A Traduzir): Arquivos novos que receberão a tradução baseada no par A/B.

---
2. PASSO A PASSO
---
1. Selecione as pastas e a extensão.
2. Ajuste o Limiar de Fuzzy Match (recomendado: 90%).
3. Clique em "1. Construir Mapeamentos".
4. Clique em "2. Aplicar em C + Relatório".

---
3. RELATÓRIO E QUALIDADE
---
O arquivo 'relatorio.txt' agora indica:
• [EXATO]: Match 100% idêntico.
• [FUZZY XX%]: Match aproximado com a porcentagem de similaridade.
• [FALHA]: Linhas que não atingiram o limiar mínimo.
        """
        txt.insert('1.0', instructions)
        txt.config(state='disabled')
        txt.pack(fill='both', expand=True)

if __name__ == "__main__":
    app = TextMapperApp()
    app.mainloop()
