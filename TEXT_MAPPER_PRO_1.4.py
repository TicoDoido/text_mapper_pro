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
        self.encoding_options = ['utf-8', 'cp1252', 'utf-16-le', 'utf-16-be', 'latin-1']
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
        help_window.title("Instruções - Text Translation Mapper Pro 1.8")
        help_window.geometry("800x600")
        help_window.transient(self)
        help_window.grab_set()

        frame = ttk.Frame(help_window, padding="15")
        frame.pack(fill='both', expand=True)

        text_widget = tk.Text(frame, wrap='word', font=("Helvetica", 11), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        instructions = """
TEXT TRANSLATION MAPPER PRO 1.4

NOVO NA VERSÃO 1.4:
→ Detecção automática inteligente de codificação:
   1. Prioridade máxima: BOM (se presente)
   2. Depois: chardet (detecção estatística)
   3. Fallback: escolha do usuário
→ Logs detalhados mostrando exatamente qual encoding foi usado

FUNCIONALIDADES:
→ Tradução por conteúdo (ordem das linhas não importa)
→ Dicionário separado para cada arquivo
→ Suporte robusto a qualquer encoding (UTF-8, CP1252, UTF-16, etc.)

USO:
1. Selecione pastas A, B e C
2. Configure extensão
3. Clique em "1. Construir Mapeamentos"
4. Clique em "2. Aplicar em C + Relatório"

Agora funciona com praticamente qualquer arquivo texto do mundo! 🚀
        """
        text_widget.insert('end', instructions.strip())
        text_widget.config(state='disabled')
        ttk.Button(help_window, text="Fechar", command=help_window.destroy).pack(pady=10)

    def _build_ui(self):
        main_container = ttk.Frame(self, padding="12")
        main_container.pack(fill='both', expand=True)

        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill='x', pady=(0, 8))
        ttk.Button(toolbar, text="Ajuda / Instruções", command=self._show_instructions).pack(side='left')
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

    def _read_file(self, path, encoding_var):
        try:
            with open(path, 'rb') as f:
                raw = f.read()
        except Exception as e:
            self._log(f"Erro ao ler binário {path.name}: {e}", "ERROR")
            return ["<ERRO AO LER ARQUIVO>\n"]

        if len(raw) == 0:
            return ["\n"]

        # 1. Detecção de BOM (prioridade máxima)
        bom_encoding = None
        bom_length = 0
        if raw.startswith(b'\xef\xbb\xbf'):
            bom_encoding = 'utf-8'
            bom_length = 3
            self._log(f"BOM detectado → usando UTF-8 para {path.name}", "INFO")
        elif raw.startswith(b'\xff\xfe'):
            bom_encoding = 'utf-16-le'
            bom_length = 2
            self._log(f"BOM detectado → usando UTF-16-LE para {path.name}", "INFO")
        elif raw.startswith(b'\xfe\xff'):
            bom_encoding = 'utf-16-be'
            bom_length = 2
            self._log(f"BOM detectado → usando UTF-16-BE para {path.name}", "INFO")

        if bom_encoding:
            raw = raw[bom_length:]
            final_encoding = bom_encoding
        else:
            # 2. Detecção com chardet
            detector = chardet.UniversalDetector()
            detector.reset()
            for line in raw.splitlines(keepends=True)[:100]:  # otimiza velocidade
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            result = detector.result
            confidence = result['confidence']
            detected = result['encoding']

            if detected and confidence > 0.7:
                if detected.lower() in ['ascii', 'utf-8', 'utf8']:
                    detected = 'utf-8'
                elif '1252' in detected.lower():
                    detected = 'cp1252'
                elif 'latin' in detected.lower():
                    detected = 'latin-1'
                self._log(f"chardet detectou {detected.upper()} (conf: {confidence:.2f}) → {path.name}", "INFO")
                final_encoding = detected
            else:
                # 3. Fallback: escolha do usuário
                fallback_map = {
                    'utf-8': 'utf-8', 'cp1252': 'cp1252',
                    'utf-16-le': 'utf-16-le', 'utf-16-be': 'utf-16-be',
                    'latin-1': 'latin-1'
                }
                final_encoding = fallback_map.get(encoding_var.get().lower(), 'utf-8')
                self._log(f"chardet incerto (conf: {confidence:.2f}). Usando fallback: {final_encoding.upper()} → {path.name}", "WARNING")

        # Decodificação final
        try:
            text = raw.decode(final_encoding)
            return text.splitlines(keepends=True)
        except Exception as e:
            self._log(f"Falha com {final_encoding}. Usando utf-8 replace → {path.name}", "ERROR")
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
            files_c = list(Path(self.folder_c.get()).glob(pattern))
            self.after(0, lambda: self.progress.config(maximum=len(files_c), value=0))

            untranslated = []
            processed = 0

            for i, file_c in enumerate(files_c):
                rel = file_c.relative_to(Path(self.folder_c.get())).as_posix()
                lines_c = self._read_file(file_c, self.encoding_c_out)
                mapping = self.mappings.get(rel, {})

                output = []
                for idx, line in enumerate(lines_c):
                    stripped = line.strip()
                    if stripped == "":
                        output.append(line)
                        continue
                    if stripped in mapping:
                        output.append(mapping[stripped])
                    else:
                        output.append(line)
                        untranslated.append(f"Arquivo: {rel} | Linha {idx+1} | Texto: \"{stripped}\"")

                out_file = out_dir / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                with open(out_file, 'w', encoding=self.encoding_c_out.get(), newline='') as f:
                    f.writelines(output)
                processed += 1
                self.after(0, lambda v=i+1: self.progress.config(value=v))

            with open(report_path, 'w', encoding='utf-8') as r:
                r.write("RELATÓRIO — Versão 1.8 (Detecção Automática)\n")
                r.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                r.write(f"Arquivos processados: {processed}\n")
                r.write("="*80 + "\n\n")
                if untranslated:
                    r.write("LINHAS NÃO TRADUZIDAS:\n\n")
                    r.write("\n".join(untranslated[:1000]))
                    if len(untranslated) > 1000:
                        r.write(f"\n... e mais {len(untranslated)-1000} linhas")
                else:
                    r.write("SUCESSO TOTAL! Todas as linhas traduzíveis foram processadas.\n")

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