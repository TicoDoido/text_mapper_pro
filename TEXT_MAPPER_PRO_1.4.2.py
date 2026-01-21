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
        self.title('Text Translation Mapper Pro — 1.4.2')
        self.geometry('1024x720')
        self.minsize(1200, 750)

        # Estados
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.folder_c = tk.StringVar()

        # Codificações
        self.encoding_options = ['utf-8', 'cp1252', 'utf-16-le', 'utf-16-be', 'latin-1', 'shift-jis', 'big5']
        self.encoding_ab = tk.StringVar(value='utf-8')
        self.encoding_c_out = tk.StringVar(value='utf-8')
        self.force_encoding_c = tk.BooleanVar(value=False)

        # Opções
        self.dark_mode = tk.BooleanVar(value=False)
        self.recursive_search = tk.BooleanVar(value=True)
        self.file_extension = tk.StringVar(value='.txt')
        self.match_by_filename_only = tk.BooleanVar(value=False)
        
        # NOVO: Brute force por ORDEM (ignorar nomes)
        self.brute_force_by_order = tk.BooleanVar(value=False)
        
        # NOVO: Ignorar linhas que começam com certos caracteres
        self.ignore_prefixes = tk.StringVar(value="")
        
        # Modo de mapeamento
        self.mapping_mode = tk.StringVar(value="content")
        self.validate_positional = tk.BooleanVar(value=True)
        
        # Fuzzy Match
        self.fuzzy_threshold = tk.DoubleVar(value=100.0)

        self.mappings = {}
        self.mappings_by_name = {}
        self.mappings_list = []  # Lista ordenada de mapeamentos para brute force

        self.style = ttk.Style(self)
        self._setup_styles()
        self._build_ui()
        self._apply_theme()
        self._update_mode_options()

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

    def _update_mode_options(self, *args):
        mode = self.mapping_mode.get()
        if mode == "positional":
            self.validate_check.config(state='normal')
            self.validate_check.config(text="Validar similaridade na posição (usar limiar)")
        else:
            self.validate_check.config(state='disabled')
            self.validate_check.config(text="Validar orig. em C")
        self.fuzzy_scale.config(state='normal')
        self.fuzzy_label.config(state='normal')

    def _toggle_brute_force(self):
        """Desabilita 'Apenas Nome' quando Brute Force estiver ativo"""
        if self.brute_force_by_order.get():
            self.match_by_filename_only_check.config(state='disabled')
            self.match_by_filename_only.set(True)  # Força True
            self._log("Modo Brute Force ativado: Ignorando nomes, usando ORDEM", "INFO")
        else:
            self.match_by_filename_only_check.config(state='normal')

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
        ttk.Checkbutton(config_subframe, text="Forçar em C", variable=self.force_encoding_c).pack(side='left', padx=5)
        ttk.Label(config_subframe, text="Ext:").pack(side='left', padx=(10, 2))
        ttk.Entry(config_subframe, textvariable=self.file_extension, width=7).pack(side='left', padx=2)
        
        # NOVO: Checkbox para Brute Force por ORDEM
        ttk.Checkbutton(config_subframe, text="Brute Force (Usar ORDEM)", 
                       variable=self.brute_force_by_order,
                       command=self._toggle_brute_force).pack(side='left', padx=(20, 2))
        
        self.btn_apply = ttk.Button(actions_line, text="2. Aplicar em C + Relatório", command=self.apply_mappings, state='disabled', style="Action.TButton")
        self.btn_apply.pack(side='right', padx=4)
        self.btn_build = ttk.Button(actions_line, text="1. Construir Mapeamentos (A ↔ B)", command=self.build_mappings, style="Action.TButton")
        self.btn_build.pack(side='right', padx=4)

        options_frame = ttk.LabelFrame(main_container, text=" Opções de Processamento ", padding="10")
        options_frame.pack(fill='x', pady=(0, 10))
        
        search_subframe = ttk.Frame(options_frame)
        search_subframe.pack(side='left', fill='x')
        ttk.Checkbutton(search_subframe, text="Subpastas", variable=self.recursive_search).pack(side='left', padx=(0, 15))
        self.match_by_filename_only_check = ttk.Checkbutton(search_subframe, text="Apenas Nome (Ignorar Estrutura)", 
                                                           variable=self.match_by_filename_only)
        self.match_by_filename_only_check.pack(side='left', padx=5)
        
        mode_subframe = ttk.Frame(options_frame)
        mode_subframe.pack(side='left', padx=20)
        ttk.Label(mode_subframe, text="Modo:").pack(side='left')
        ttk.Radiobutton(mode_subframe, text="Conteúdo", variable=self.mapping_mode, value="content").pack(side='left', padx=5)
        ttk.Radiobutton(mode_subframe, text="Posicional", variable=self.mapping_mode, value="positional").pack(side='left', padx=5)
        
        validate_subframe = ttk.Frame(options_frame)
        validate_subframe.pack(side='left')
        self.validate_check = ttk.Checkbutton(validate_subframe, text="Validar similaridade na posição", variable=self.validate_positional)
        self.validate_check.pack(side='left', padx=10)
        
        # NOVO: Campo para ignorar prefixos
        ignore_subframe = ttk.Frame(options_frame)
        ignore_subframe.pack(side='left', padx=(10, 0))
        ttk.Label(ignore_subframe, text="Ignorar linhas:").pack(side='left')
        ttk.Entry(ignore_subframe, textvariable=self.ignore_prefixes, width=6).pack(side='left', padx=5)
        ttk.Label(ignore_subframe, text="(ex: ; //)").pack(side='left')

        fuzzy_subframe = ttk.Frame(options_frame)
        fuzzy_subframe.pack(side='right')
        ttk.Label(fuzzy_subframe, text="Similaridade:").pack(side='left', padx=(20, 5))
        self.fuzzy_scale = ttk.Scale(fuzzy_subframe, from_=0, to=100, orient='horizontal', variable=self.fuzzy_threshold, length=200)
        self.fuzzy_scale.pack(side='left', padx=5)
        self.fuzzy_label = ttk.Label(fuzzy_subframe, text=f"{self.fuzzy_threshold.get():.0f}%", width=6)
        self.fuzzy_label.pack(side='left', padx=2)
        
        def update_fuzzy_label(val): 
            self.fuzzy_label.config(text=f"{float(val):.0f}%")
        self.fuzzy_scale.config(command=update_fuzzy_label)
        
        self.mapping_mode.trace_add('write', self._update_mode_options)

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

    def _read_file(self, path, fallback_var, force_encoding=None):
        """Lê um arquivo com a codificação especificada ou detecta automaticamente"""
        try:
            if force_encoding is not None:
                with open(path, 'r', encoding=force_encoding) as f:
                    return f.read().splitlines(keepends=True)
            
            with open(path, 'rb') as f: raw = f.read()
        except Exception as e:
            self._log(f"Erro ao ler {path}: {e}", "WARN")
            return ["<ERRO>\n"]
        
        if not raw: return ["\n"]
        
        bom_map = {b'\xef\xbb\xbf': 'utf-8-sig', b'\xff\xfe': 'utf-16-le', b'\xfe\xff': 'utf-16-be'}
        for bom, enc in bom_map.items():
            if raw.startswith(bom):
                try: 
                    return raw.decode(enc).splitlines(keepends=True)
                except: 
                    pass
        
        detector = chardet.UniversalDetector()
        for line in raw.splitlines(keepends=True)[:200]:
            detector.feed(line)
            if detector.done: break
        detector.close()
        
        if detector.result['encoding'] and detector.result['confidence'] > 0.8:
            try: 
                return raw.decode(detector.result['encoding']).splitlines(keepends=True)
            except: 
                pass
        
        for enc in ['utf-8', 'cp1252', 'utf-16', 'latin-1', fallback_var.get().lower()]:
            try: 
                return raw.decode(enc).splitlines(keepends=True)
            except: 
                continue
        
        return raw.decode('utf-8', errors='replace').splitlines(keepends=True)

    def _should_ignore(self, line, prefixes):
        if not prefixes:
            return False
        stripped = line.lstrip()
        for p in prefixes:
            if p and stripped.startswith(p):
                return True
        return False

    def build_mappings(self):
        if not self.folder_a.get() or not self.folder_b.get():
            messagebox.showerror("Erro", "Selecione pastas A e B.")
            return
        
        pattern = self._get_pattern()
        mode = self.mapping_mode.get()
        prefixes = self.ignore_prefixes.get().split()
        self.btn_build.config(state='disabled')
        self.files_listbox.delete(0, 'end')
        self.tree.delete(*self.tree.get_children())
        self.mappings.clear()
        self.mappings_by_name.clear()
        self.mappings_list = []  # Resetar lista ordenada

        def worker():
            path_a, path_b = Path(self.folder_a.get()), Path(self.folder_b.get())
            files_a = {f.relative_to(path_a).as_posix(): f for f in path_a.glob(pattern)}
            files_b = {f.relative_to(path_b).as_posix(): f for f in path_b.glob(pattern)}
            
            # Para A e B: arquivos DEVEM ter os mesmos nomes
            common = sorted(set(files_a.keys()) & set(files_b.keys()))
            
            self.after(0, lambda: self.progress.config(maximum=len(common), value=0))
            
            # Criar lista ordenada de mapeamentos para brute force
            self.mappings_list = []
            
            for i, rel in enumerate(common):
                file_a = files_a[rel]
                file_b = files_b[rel]
                
                lines_a = self._read_file(file_a, self.encoding_ab, force_encoding=None)
                lines_b = self._read_file(file_b, self.encoding_ab, force_encoding=None)
                
                mapping = []
                for la, lb in zip(lines_a, lines_b):
                    orig = la.rstrip('\n\r')
                    trans = lb.rstrip('\n\r')
                    
                    # Ignorar se começar com prefixo
                    if self._should_ignore(orig, prefixes):
                        continue

                    mapping.append({
                        'orig': orig, 
                        'trans': trans
                    })

                if mode == "content":
                    content_map = {}
                    for item in mapping:
                        if item['trans'] is not None:
                            content_map[item['orig']] = item['trans'] + '\n' if not item['trans'].endswith('\n') else item['trans']
                    self.mappings[rel] = content_map
                    self.mappings_list.append(content_map)  # Adicionar à lista ordenada
                else:
                    self.mappings[rel] = mapping
                    self.mappings_list.append(mapping)  # Adicionar à lista ordenada
                
                fname = Path(rel).name
                if fname not in self.mappings_by_name:
                    self.mappings_by_name[fname] = self.mappings[rel]
                
                self.after(0, lambda d=rel: self.files_listbox.insert('end', d))
                self.after(0, lambda v=i+1: self.progress.config(value=v))
            
            self.after(0, self._build_finished)
        
        threading.Thread(target=worker, daemon=True).start()

    def _build_finished(self):
        self.btn_build.config(state='normal')
        if self.mappings: self.btn_apply.config(state='normal')
        self._log(f"Dicionários criados: {len(self.mappings)} arquivos mapeados.")
        messagebox.showinfo("Sucesso", f"Dicionários criados!\n{len(self.mappings)} arquivos mapeados.")

    def _on_file_select(self, event):
        sel = self.files_listbox.curselection()
        if not sel: return
        fname = self.files_listbox.get(sel[0])
        mapping = self.mappings.get(fname)
        if not mapping: return
        mode = self.mapping_mode.get()
        self.tree.delete(*self.tree.get_children())
        
        # CORREÇÃO: Verificar o tipo real do mapeamento, não apenas o modo atual
        if mode == "content" and isinstance(mapping, dict):
            for idx, (orig, trans) in enumerate(mapping.items(), 1):
                self.tree.insert('', 'end', values=(idx, orig, trans))
        else:
            # Assume que é uma lista (modo posicional)
            if isinstance(mapping, dict):
                # Se for um dicionário mas o modo for posicional, converter
                mapping_list = []
                for orig, trans in mapping.items():
                    mapping_list.append({'orig': orig, 'trans': trans})
                mapping = mapping_list
            
            for idx, item in enumerate(mapping, 1):
                trans = item['trans']
                if trans is None:
                    trans = "[SEM TRADUÇÃO]"
                elif not trans.endswith('\n'):
                    trans = trans + '\n'
                self.tree.insert('', 'end', values=(idx, item['orig'], trans))

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
        mode = self.mapping_mode.get()
        by_name_only = self.match_by_filename_only.get()
        threshold = self.fuzzy_threshold.get() / 100.0
        brute_force = self.brute_force_by_order.get()
        prefixes = self.ignore_prefixes.get().split()

        def worker():
            pattern = self._get_pattern()
            files_c_paths = list(Path(self.folder_c.get()).glob(pattern))
            
            # Ordenar arquivos C por nome para consistência
            files_c_paths.sort(key=lambda x: x.name)
            
            self.after(0, lambda: self.progress.config(maximum=len(files_c_paths), value=0))
            untranslated = {}
            processed = 0
            
            if self.force_encoding_c.get():
                force_enc_c = self.encoding_c_out.get()
                self._log(f"Forçando codificação em C: {force_enc_c}", "INFO")
            else:
                force_enc_c = None
            
            for i, file_c in enumerate(files_c_paths):
                rel = file_c.relative_to(Path(self.folder_c.get())).as_posix()
                
                # NOVA LÓGICA: Brute Force por ORDEM
                if brute_force:
                    # Usar mapeamento baseado na ORDEM (índice)
                    if i < len(self.mappings_list):
                        mapping = self.mappings_list[i]
                        self._log(f"Brute Force: índice {i} → '{rel}'", "INFO")
                    else:
                        mapping = None
                        self._log(f"Aviso: Arquivo C '{rel}' sem mapeamento correspondente (índice {i})", "WARN")
                else:
                    # Comportamento original
                    mapping = (self.mappings_by_name.get(file_c.name) if by_name_only 
                              else self.mappings.get(rel))
                
                lines_c = self._read_file(file_c, self.encoding_c_out, force_enc_c)
                output, issues_fail, issues_fuzzy = [], [], []
                
                if not mapping:
                    output = [line.rstrip('\r\n') + '\n' for line in lines_c]
                    issues_fail.append("[!] Sem mapeamento encontrado para este arquivo.")
                else:
                    if mode == "content":
                        # Se mapping for lista, converter para dicionário
                        if isinstance(mapping, list):
                            content_map = {}
                            for item in mapping:
                                if item['trans'] is not None:
                                    content_map[item['orig']] = item['trans'] + '\n' if not item['trans'].endswith('\n') else item['trans']
                            mapping = content_map
                        
                        keys = list(mapping.keys())
                        for idx, line in enumerate(lines_c, 1):
                            s = line.rstrip('\r\n')
                            if not s or self._should_ignore(line, prefixes):
                                output.append(s + '\n')
                                continue
                            if s in mapping:
                                output.append(mapping[s])
                                continue
                            if threshold < 1.0:
                                matches = difflib.get_close_matches(s, keys, n=1, cutoff=threshold)
                                if matches:
                                    best = matches[0]
                                    sim = difflib.SequenceMatcher(None, s, best).ratio()
                                    output.append(mapping[best])
                                    issues_fuzzy.append(f"L{idx}: [FUZZY GLOBAL {sim*100:.0f}%] \"{s}\" → \"{best}\"")
                                    continue
                            output.append(s + '\n')
                            issues_fail.append(f"L{idx}: [FALHA GLOBAL] \"{s}\"")
                    else:
                        # Se mapping for dicionário, converter para lista
                        if isinstance(mapping, dict):
                            mapping_list = []
                            for orig, trans in mapping.items():
                                mapping_list.append({'orig': orig, 'trans': trans})
                            mapping = mapping_list
                        
                        # Para modo posicional, precisamos de um mapeamento que ignore as linhas de comentário
                        # mas mantenha a correspondência de índice para as linhas de conteúdo.
                        # No entanto, o modo posicional original do programa parece ser 1:1 por linha.
                        # Se ignorarmos linhas no mapeamento, o índice mudará.
                        # Vamos manter a lógica de ignorar apenas para o conteúdo.
                        
                        for idx, line in enumerate(lines_c, 1):
                            s = line.rstrip('\r\n')
                            if not s or self._should_ignore(line, prefixes):
                                output.append(s + '\n')
                                continue
                            
                            map_idx = idx - 1
                            if map_idx < len(mapping):
                                item = mapping[map_idx]
                                orig_s = item['orig'].strip() if item['orig'] else ""
                                if not self.validate_positional.get():
                                    output.append(item['trans'] + '\n' if item['trans'] and not item['trans'].endswith('\n') else (item['trans'] or (s + '\n')))
                                else:
                                    sim = difflib.SequenceMatcher(None, s, orig_s).ratio()
                                    if sim >= threshold:
                                        output.append(item['trans'] + '\n' if item['trans'] and not item['trans'].endswith('\n') else (item['trans'] or (s + '\n')))
                                        if sim < 1.0:
                                            issues_fuzzy.append(f"L{idx}: [FUZZY POSICIONAL {sim*100:.0f}%] \"{s}\" → \"{orig_s}\"")
                                    else:
                                        output.append(s + '\n')
                                        issues_fail.append(f"L{idx}: [FALHA POSICIONAL {sim*100:.0f}%] \"{s}\" vs \"{orig_s}\"")
                            else:
                                output.append(s + '\n')
                                issues_fail.append(f"L{idx}: [FORA DE ÍNDICE] Sem tradução na linha {idx}")

                # Salvar arquivo traduzido
                out_file = out_dir / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                
                enc_out = self.encoding_c_out.get()
                try:
                    with open(out_file, 'w', encoding=enc_out) as f:
                        f.writelines(output)
                    processed += 1
                except Exception as e:
                    self._log(f"Erro ao salvar {out_file}: {e}", "WARN")
                
                if issues_fail or issues_fuzzy:
                    untranslated[rel] = issues_fail + issues_fuzzy
                
                self.after(0, lambda v=i+1: self.progress.config(value=v))

            # Gerar Relatório
            with open(report_path, 'w', encoding='utf-8') as r:
                validate_str = "Sim" if self.validate_positional.get() else "Não"
                brute_str = "Sim" if brute_force else "Não"
                r.write(f"RELATÓRIO v1.4.2 - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                r.write(f"Modo: {mode.capitalize()} | Validar similaridade: {validate_str} | Limiar: {threshold*100:.0f}% | Busca: {'Nome' if by_name_only else 'Estrutura'}\n")
                r.write(f"Brute Force por ORDEM: {brute_str}\n")
                r.write(f"Ignorar Prefixos: {' '.join(prefixes) if prefixes else 'Nenhum'}\n")
                r.write(f"Arquivos A/B mapeados: {len(self.mappings_list)} | Arquivos C processados: {len(files_c_paths)}\n")
                r.write(f"Forçar Codificação em C: {'Sim' if self.force_encoding_c.get() else 'Não'}\n")
                r.write(f"Codificação A/B: {self.encoding_ab.get()} | Codificação Saída: {self.encoding_c_out.get()}\n")
                r.write(f"Pasta de Saída: {out_dir_name}\n")
                r.write("="*80 + "\n\n")
                
                if untranslated:
                    r.write(f"ARQUIVOS COM PROBLEMAS ({len(untranslated)}):\n")
                    for p, iss in untranslated.items():
                        r.write(f"\nARQUIVO: {p}\n")
                        for item in iss:
                            if any(tag in item for tag in ["[FALHA", "[FORA DE ÍNDICE]", "[!]"]):
                                r.write(f"  {item}\n")
                        for item in iss:
                            if "[FUZZY" in item:
                                r.write(f"  {item}\n")
                        r.write("-" * 40 + "\n")
                else:
                    r.write("TODOS OS ARQUIVOS FORAM TRADUZIDOS COM SUCESSO!\n")
                
                r.write(f"\nTotal de arquivos processados: {processed}\n")
                r.write(f"Arquivos com problemas: {len(untranslated)}\n")
                if brute_force:
                    r.write(f"\nNOTA: Modo Brute Force por ORDEM foi usado.\n")
                    r.write(f"Primeiro arquivo A/B → Primeiro arquivo C\n")
                    r.write(f"Segundo arquivo A/B → Segundo arquivo C\n")
                    r.write(f"e assim por diante...\n")
            
            self.after(0, lambda: self._apply_finished(processed, out_dir, report_path))
        
        threading.Thread(target=worker, daemon=True).start()

    def _apply_finished(self, count, out_dir, report):
        self.btn_apply.config(state='normal')
        self._log(f"Concluído: {count} arquivos processados. Saída em: {out_dir}")
        messagebox.showinfo("Concluído!", 
                          f"Tradução finalizada!\n"
                          f"{count} arquivos processados.\n\n"
                          f"Relatório salvo em:\n{report}\n\n"
                          f"Arquivos traduzidos em:\n{out_dir}")

    def _show_instructions(self):
        help_window = tk.Toplevel(self)
        help_window.title("Ajuda v1.4.2")
        help_window.geometry("650x500")
        txt = tk.Text(help_window, wrap='word', padx=10, pady=10)
        txt.configure(font=("Segoe UI", 12))
        instructions = """TEXT TRANSLATION MAPPER PRO 1.4.2 — COM OPÇÃO DE IGNORAR PREFIXOS

NOVO NA VERSÃO 1.4.2:
→ Ignorar Linhas: Agora você pode definir caracteres que, se estiverem no
início da linha, farão com que a linha seja ignorada no mapeamento e mantida
original na saída.
→ Exemplo: Digite ";" ou "//" no campo "Ignorar linhas"
para pular comentários de código.
→ Forçar em C vai forçar a codificação de saída
→ Modo conteúdo aplica a tradução de A/B em qualquer linha de C
→ Modo posicional só aplica na mesma linha(ex: linha 9 em A/B na linha 9 em C)
→ Brute Force ignora os nomes dos arquivos em C, exige mesma ordem e quantidade
→ Subpastas e Apenas Nome para buscar o arquivo onde quer que ele esteja

---
1. CONCEITO DAS PASTAS
---
• PASTA A (Originais): Arquivos originais (ex: Inglês).
• PASTA B (Traduções): Mesmos arquivos de A, mas traduzidos (ex: Português). 
   A e B DEVEM ter os mesmos nomes e mesma quantidade!
• PASTA C (A Traduzir): Arquivos novos com nomes DIFERENTES.
   Mesma quantidade que A/B, na mesma ordem.

---
2. PASSO A PASSO
---
1. Selecione as pastas e a extensão.
2. Se necessário, defina os prefixos para ignorar (ex: ; //).
3. Se C tiver nomes diferentes de A/B, marque "Brute Force (Usar ORDEM)".
4. Ajuste o Limiar de Fuzzy Match (recomendado: 90%).
5. Clique em "1. Construir Mapeamentos".
6. Clique em "2. Aplicar em C + Relatório".

---
3. COMO FUNCIONA O IGNORAR PREFIXOS
---
1. Durante a construção do mapeamento (A/B), linhas que começam com os caracteres definidos são ignoradas.
2. Durante a aplicação em C, essas mesmas linhas são detectadas e mantidas exatamente como estão no arquivo original de C.
3. Isso evita que comentários ou códigos sejam "traduzidos" erroneamente ou causem falhas de mapeamento.

---
4. IMPORTANTE
---
• A e B DEVEM ter mesma quantidade e mesmos nomes.
• C DEVE ter mesma quantidade que A/B.
• A ordem é determinada pela ordenação ALFABÉTICA dos nomes.
"""
        txt.insert('1.0', instructions)
        txt.config(state='disabled')
        txt.pack(fill='both', expand=True)

if __name__ == "__main__":
    app = TextMapperApp()
    app.mainloop()
