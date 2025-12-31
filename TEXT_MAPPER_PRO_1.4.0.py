import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import chardet  # Necessário para detecção automática

class TextMapperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Text Translation Mapper Pro — 1.4')
        self.geometry('1300x900')
        self.minsize(1100, 700)

        # Estados
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.folder_c = tk.StringVar()

        # Codificações (agora como fallback)
        self.encoding_options = ['utf-8', 'cp1252', 'utf-16-le', 'utf-16-be', 'latin-1', 'shift-jis', 'big5']
        self.encoding_ab = tk.StringVar(value='utf-8')
        self.encoding_c_out = tk.StringVar(value='utf-8')

        # Opções
        self.dark_mode = tk.BooleanVar(value=False)
        self.recursive_search = tk.BooleanVar(value=True)
        self.file_extension = tk.StringVar(value='.txt')

        # Mapeamentos: rel_path → {stripped_orig: translated_line_with_newline}
        self.mappings = {}

        self.style = ttk.Style(self)
        self._setup_styles()
        self._build_ui()
        self._apply_theme()

    def _setup_styles(self):
        self.style.configure("TButton", padding=6)
        self.style.configure("Header.TLabel", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview", rowheight=25)

    def _apply_theme(self):
        if self.dark_mode.get():
            bg = "#2d2d2d"
            fg = "#ffffff"
            entry_bg = "#3d3d3d"
            self.configure(bg=bg)
            self.style.theme_use('clam')
            self.style.configure("TFrame", background=bg)
            self.style.configure("TLabelframe", background=bg, foreground=fg)
            self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
            self.style.configure("TLabel", background=bg, foreground=fg)
            self.style.configure("TCheckbutton", background=bg, foreground=fg)
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

    def _show_instructions(self):
        help_window = tk.Toplevel(self)
        help_window.title("Guia de Uso - Text Translation Mapper Pro 1.4")
        help_window.geometry("900x700")
        help_window.transient(self)
        help_window.grab_set()

        frame = ttk.Frame(help_window, padding="20")
        frame.pack(fill='both', expand=True)

        text_widget = tk.Text(frame, wrap='word', font=("Segoe UI", 11), padx=15, pady=15)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        instructions = """
TEXT TRANSLATION MAPPER PRO 1.4 — DETECÇÃO ULTRA-ROBUSTA

NOVO NA VERSÃO 1.4:
→ Motor de Encoding Inteligente: O programa agora usa 3 camadas de detecção:
   1. Assinatura Digital (BOM)
   2. Análise Estatística (Chardet)
   3. Validação por Tentativa (Brute-force Fallback)
Isso garante que mesmo arquivos sem assinatura ou com caracteres raros sejam lidos corretamente.

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
2. Clique em "1. Construir Mapeamentos". O programa criará o dicionário.
3. Clique em "2. Aplicar em C + Relatório". Os arquivos traduzidos serão gerados em uma nova pasta.

---
3. RELATÓRIO E QUALIDADE
---
O arquivo 'relatorio.txt' mostrará:
• Arquivos que faltam em alguma das pastas.
• Linhas específicas que não foram encontradas no dicionário (Divergências).

---
4. DICAS DE ENCODING
---
Se o arquivo ainda apresentar problemas, verifique se ele não está corrompido. O motor 1.4 tenta automaticamente as codificações mais comuns do mundo (UTF-8, Windows-1252, UTF-16).
        """
        text_widget.insert('end', instructions.strip())
        text_widget.config(state='disabled')
        ttk.Button(help_window, text="Entendi!", command=help_window.destroy).pack(pady=15)

    def _build_ui(self):
        main_container = ttk.Frame(self, padding="12")
        main_container.pack(fill='both', expand=True)

        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill='x', pady=(0, 8))
        ttk.Button(toolbar, text="📖 Guia de Uso / Ajuda", command=self._show_instructions).pack(side='left')
        ttk.Checkbutton(toolbar, text="Modo Escuro", variable=self.dark_mode, command=self._toggle_theme).pack(side='right')

        folders_frame = ttk.LabelFrame(main_container, text=" Configurações de Pastas ", padding="12")
        folders_frame.pack(fill='x', pady=(0, 12))
        for i, (label_text, var) in enumerate([
            ("Pasta A (Originais):", self.folder_a),
            ("Pasta B (Traduções):", self.folder_b),
            ("Pasta C (A Traduzir):", self.folder_c)
        ]):
            ttk.Label(folders_frame, text=label_text, style="Header.TLabel").grid(row=i, column=0, sticky='w', pady=6)
            ttk.Entry(folders_frame, textvariable=var, width=85).grid(row=i, column=1, padx=8, pady=6, sticky='ew')
            ttk.Button(folders_frame, text="Procurar", command=lambda v=var: self._select_folder(v)).grid(row=i, column=2, padx=4)
        folders_frame.columnconfigure(1, weight=1)

        options_line1 = ttk.Frame(main_container)
        options_line1.pack(fill='x', pady=(0, 6))
        ttk.Label(options_line1, text="Codificação A/B (fallback):").pack(side='left', padx=(0, 4))
        ttk.Combobox(options_line1, textvariable=self.encoding_ab, values=self.encoding_options, width=12, state="readonly").pack(side='left', padx=4)
        ttk.Label(options_line1, text="Codificação C/Saída (fallback):").pack(side='left', padx=(20, 4))
        ttk.Combobox(options_line1, textvariable=self.encoding_c_out, values=self.encoding_options, width=12, state="readonly").pack(side='left', padx=4)
        ttk.Label(options_line1, text="Extensão:").pack(side='left', padx=(40, 4))
        ttk.Entry(options_line1, textvariable=self.file_extension, width=12).pack(side='left', padx=4)
        ttk.Label(options_line1, text="(ex: .txt, .lua)").pack(side='left', padx=(0, 20))
        ttk.Checkbutton(options_line1, text="Buscar em subpastas", variable=self.recursive_search).pack(side='left', padx=10)

        options_line2 = ttk.Frame(main_container)
        options_line2.pack(fill='x', pady=(0, 12))
        self.btn_build = ttk.Button(options_line2, text="1. Construir Mapeamentos (A ↔ B)", command=self.build_mappings)
        self.btn_build.pack(side='right', padx=8)
        self.btn_apply = ttk.Button(options_line2, text="2. Aplicar em C + Relatório", command=self.apply_mappings, state='disabled')
        self.btn_apply.pack(side='right', padx=8)

        paned = ttk.PanedWindow(main_container, orient='horizontal')
        paned.pack(fill='both', expand=True, pady=(0, 10))

        list_frame = ttk.LabelFrame(paned, text=" Arquivos Comuns Encontrados (A/B) ", padding="8")
        self.files_listbox = tk.Listbox(list_frame)
        self.files_listbox.pack(fill='both', expand=True)
        self.files_listbox.bind('<<ListboxSelect>>', self._on_file_select)
        paned.add(list_frame, weight=1)

        preview_frame = ttk.LabelFrame(paned, text=" Preview do Dicionário do Arquivo Selecionado ", padding="8")
        self.tree = ttk.Treeview(preview_frame, columns=('idx', 'orig', 'trans'), show='headings')
        self.tree.heading('idx', text='№')
        self.tree.heading('orig', text='Original (A)')
        self.tree.heading('trans', text='Tradução (B)')
        self.tree.column('idx', width=60, anchor='center')
        self.tree.column('orig', width=400, anchor='w')
        self.tree.column('trans', width=400, anchor='w')
        self.tree.pack(fill='both', expand=True)
        paned.add(preview_frame, weight=3)

        self.progress = ttk.Progressbar(main_container, mode='determinate')
        self.progress.pack(fill='x', pady=(0, 6))
        self.log_text = tk.Text(main_container, height=10, state='disabled', font=("Consolas", 10))
        self.log_text.pack(fill='x')

    def _log(self, message, level="INFO"):
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{level}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _select_folder(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _get_pattern(self):
        ext = self.file_extension.get().strip()
        if not ext.startswith('.'):
            ext = '.' + ext
        return f"**/*{ext}" if self.recursive_search.get() else f"*{ext}"

    def _read_file(self, path, fallback_var):
        """Motor de detecção de encoding ultra-robusto v1.4"""
        try:
            with open(path, 'rb') as f:
                raw = f.read()
        except Exception as e:
            self._log(f"Erro ao ler binário {path.name}: {e}", "ERROR")
            return ["<ERRO AO LER ARQUIVO>\n"]

        if len(raw) == 0:
            return ["\n"]

        # CAMADA 1: Detecção de BOM (assinatura digital)
        bom_map = {
            b'\xef\xbb\xbf': 'utf-8-sig',
            b'\xff\xfe': 'utf-16-le',
            b'\xfe\xff': 'utf-16-be'
        }
        for bom, enc in bom_map.items():
            if raw.startswith(bom):
                try:
                    self._log(f"BOM detectado ({enc}) -> {path.name}", "INFO")
                    return raw.decode(enc).splitlines(keepends=True)
                except: pass

        # CAMADA 2: Análise Estatística (Chardet)
        detector = chardet.UniversalDetector()
        detector.reset()
        for line in raw.splitlines(keepends=True)[:200]:
            detector.feed(line)
            if detector.done: break
        detector.close()
        
        detected_enc = detector.result['encoding']
        confidence = detector.result['confidence']

        if detected_enc and confidence > 0.8:
            try:
                self._log(f"Chardet detectou {detected_enc.upper()} ({confidence:.2f}) -> {path.name}", "INFO")
                return raw.decode(detected_enc).splitlines(keepends=True)
            except: pass

        # CAMADA 3: Brute-force Fallback (Tentativa e Erro)
        # Lista de encodings por ordem de probabilidade
        trial_encodings = [
            'utf-8', 
            'cp1252',      # Windows Latin-1 (muito comum)
            'utf-16', 
            'latin-1', 
            'iso-8859-1',
            fallback_var.get().lower() # Escolha do usuário
        ]
        
        # Remove duplicatas mantendo a ordem
        trial_encodings = list(dict.fromkeys(trial_encodings))

        for enc in trial_encodings:
            try:
                text = raw.decode(enc)
                # Validação simples: se decodificou sem erro, aceitamos
                self._log(f"Recuperação: Usando {enc.upper()} para {path.name}", "WARNING")
                return text.splitlines(keepends=True)
            except UnicodeDecodeError:
                continue

        # ÚLTIMO RECURSO: Decode com substituição de caracteres inválidos
        self._log(f"CRÍTICO: Falha total de encoding em {path.name}. Usando UTF-8 com substituição.", "ERROR")
        return raw.decode('utf-8', errors='replace').splitlines(keepends=True)

    def build_mappings(self):
        if not self.folder_a.get() or not self.folder_b.get():
            messagebox.showerror("Erro", "Selecione pastas A e B.")
            return
        if not self.file_extension.get().strip():
            messagebox.showerror("Erro", "Digite uma extensão.")
            return

        pattern = self._get_pattern()
        self.btn_build.config(state='disabled')
        self.btn_apply.config(state='disabled')
        self.files_listbox.delete(0, 'end')
        self.tree.delete(*self.tree.get_children())
        self.mappings.clear()

        def worker():
            path_a = Path(self.folder_a.get())
            path_b = Path(self.folder_b.get())

            files_a = {f.relative_to(path_a).as_posix(): f for f in path_a.glob(pattern)}
            files_b = {f.relative_to(path_b).as_posix(): f for f in path_b.glob(pattern)}
            common = sorted(set(files_a.keys()) & set(files_b.keys()))

            self.after(0, lambda: self.progress.config(maximum=len(common), value=0))

            for i, rel in enumerate(common):
                lines_a = self._read_file(files_a[rel], self.encoding_ab)
                lines_b = self._read_file(files_b[rel], self.encoding_ab)

                max_len = max(len(lines_a), len(lines_b))
                lines_a += ['\n'] * (max_len - len(lines_a))
                lines_b += ['\n'] * (max_len - len(lines_b))

                mapping_dict = {}
                for a, b in zip(lines_a, lines_b):
                    key = a.strip()
                    if key == "":
                        mapping_dict[""] = a
                    else:
                        mapping_dict[key] = b

                self.mappings[rel] = mapping_dict

                display = rel if self.recursive_search.get() else Path(rel).name
                self.after(0, lambda d=display: self.files_listbox.insert('end', d))
                self.after(0, lambda v=i+1: self.progress.config(value=v))

            self.after(0, self._build_finished)

        threading.Thread(target=worker, daemon=True).start()

    def _build_finished(self):
        self.btn_build.config(state='normal')
        if self.mappings:
            self.btn_apply.config(state='normal')
        self._log(f"Mapeamentos concluídos: {len(self.mappings)} arquivos processados.")
        messagebox.showinfo("Sucesso", f"Dicionários criados automaticamente!\n{len(self.mappings)} arquivos mapeados.")

    def _on_file_select(self, event):
        sel = self.files_listbox.curselection()
        if not sel:
            return
        fname = self.files_listbox.get(sel[0])
        key = next((k for k in self.mappings if k.endswith(fname) or k == fname), None)
        if not key or key not in self.mappings:
            return

        self.tree.delete(*self.tree.get_children())
        mapping = self.mappings[key]
        idx = 1
        for orig_key, trans in mapping.items():
            if orig_key != "":
                self.tree.insert('', 'end', values=(idx, orig_key, trans.rstrip('\n\r')))
                idx += 1

    def apply_mappings(self):
        if not self.folder_c.get():
            messagebox.showerror("Erro", "Selecione a pasta C.")
            return
        if not self.mappings:
            messagebox.showerror("Erro", "Construa os mapeamentos primeiro.")
            return

        out_dir = Path(self.folder_c.get()).parent / (Path(self.folder_c.get()).name + "_TRA")
        out_dir.mkdir(exist_ok=True)
        report_path = out_dir / "relatorio.txt"

        self.btn_apply.config(state='disabled')

        def worker():
            pattern = self._get_pattern()
            files_c_paths = list(Path(self.folder_c.get()).glob(pattern))
            files_c_rel = {f.relative_to(Path(self.folder_c.get())).as_posix() for f in files_c_paths}
            
            # Arquivos em A/B mas não em C
            missing_in_c = sorted(set(self.mappings.keys()) - files_c_rel)
            # Arquivos em C mas não em A/B
            missing_in_ab = sorted(files_c_rel - set(self.mappings.keys()))

            self.after(0, lambda: self.progress.config(maximum=len(files_c_paths), value=0))

            untranslated_by_file = {}
            processed = 0

            for i, file_c in enumerate(files_c_paths):
                rel = file_c.relative_to(Path(self.folder_c.get())).as_posix()
                lines_c = self._read_file(file_c, self.encoding_c_out)
                mapping = self.mappings.get(rel, {})

                output = []
                file_issues = []
                
                for idx, line in enumerate(lines_c):
                    stripped = line.strip()
                    if stripped == "":
                        output.append(line)
                        continue
                    if stripped in mapping:
                        output.append(mapping[stripped])
                    else:
                        output.append(line)
                        file_issues.append(f"Linha {idx+1}: \"{stripped}\"")

                if file_issues:
                    untranslated_by_file[rel] = file_issues

                out_file = out_dir / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Salva com o encoding de saída preferencial
                try:
                    with open(out_file, 'w', encoding=self.encoding_c_out.get(), newline='') as f:
                        f.writelines(output)
                except:
                    # Fallback de escrita caso o encoding de saída não suporte os caracteres
                    with open(out_file, 'w', encoding='utf-8', newline='') as f:
                        f.writelines(output)
                        
                processed += 1
                self.after(0, lambda v=i+1: self.progress.config(value=v))

            with open(report_path, 'w', encoding='utf-8') as r:
                r.write("RELATÓRIO DE TRADUÇÃO — Versão 1.4\n")
                r.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                r.write(f"Arquivos processados em C: {processed}\n")
                r.write("="*80 + "\n\n")
                
                # Seção de Arquivos Ausentes
                r.write("CONTROLE DE ARQUIVOS:\n")
                r.write("-" * 80 + "\n")
                if missing_in_c:
                    r.write(f"AVISO: {len(missing_in_c)} arquivos encontrados em A/B mas AUSENTES na pasta C:\n")
                    for m in missing_in_c:
                        r.write(f"  [!] {m}\n")
                else:
                    r.write("✓ Todos os arquivos de A/B estão presentes em C.\n")
                
                r.write("\n")
                
                if missing_in_ab:
                    r.write(f"AVISO: {len(missing_in_ab)} arquivos encontrados em C mas SEM MAPEAMENTO em A/B:\n")
                    for m in missing_in_ab:
                        r.write(f"  [?] {m}\n")
                else:
                    r.write("✓ Todos os arquivos de C possuem mapeamento correspondente em A/B.\n")
                
                r.write("\n" + "="*80 + "\n\n")

                # Seção de Divergências de Conteúdo
                if untranslated_by_file:
                    r.write("DIVERGÊNCIAS DE CONTEÚDO (LINHAS NÃO MAPEADAS):\n")
                    r.write("-" * 80 + "\n")
                    for rel_path, issues in untranslated_by_file.items():
                        r.write(f"\nARQUIVO: {rel_path}\n")
                        for issue in issues:
                            r.write(f"  → {issue}\n")
                        r.write("-" * 40 + "\n")
                else:
                    r.write("SUCESSO TOTAL! Todas as linhas dos arquivos processados foram traduzidas.\n")

            self.after(0, lambda: self._apply_finished(processed, out_dir, report_path))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_finished(self, count, out_dir, report):
        self.btn_apply.config(state='normal')
        self._log(f"Concluído: {count} arquivos traduzidos.")
        self._log(f"Saída: {out_dir}")
        self._log(f"Relatório: {report}")
        messagebox.showinfo("Concluído!", f"Tradução finalizada!\n\n{count} arquivos processados.\nPasta: {out_dir}\nRelatório: {report}")

if __name__ == "__main__":
    app = TextMapperApp()
    app.mainloop()
