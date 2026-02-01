import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
import random
import json
import os
import winsound
import webbrowser
import calendar
from datetime import datetime

# ==========================================
# 1. WIDGETS AUXILIARES
# ==========================================

class ScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    def set_bg(self, color):
        self.canvas.configure(bg=color)
        self.scrollable_frame.configure(bg=color)

class DatePicker(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Seleccionar Fecha")
        self.geometry("250x250")
        self.configure(bg="white")
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.crear_ui(); self.render()
    def crear_ui(self):
        top = tk.Frame(self, bg="#2C3E50"); top.pack(fill="x")
        tk.Button(top, text="<", command=self.prev, bg="#34495E", fg="white", relief="flat").pack(side="left", padx=10)
        self.lbl = tk.Label(top, text="", bg="#2C3E50", fg="white", font=("Arial", 10, "bold")); self.lbl.pack(side="left", expand=True)
        tk.Button(top, text=">", command=self.next, bg="#34495E", fg="white", relief="flat").pack(side="right", padx=10)
        self.grid_f = tk.Frame(self, bg="white"); self.grid_f.pack(fill="both", expand=True, padx=5, pady=5)
    def render(self):
        for w in self.grid_f.winfo_children(): w.destroy()
        self.lbl.config(text=f"{calendar.month_name[self.month]} {self.year}")
        cal = calendar.monthcalendar(self.year, self.month)
        for i, d in enumerate(["L","M","M","J","V","S","D"]): tk.Label(self.grid_f, text=d, bg="white", font=("Segoe UI", 8, "bold")).grid(row=0, column=i)
        for r, w in enumerate(cal):
            for c, d in enumerate(w):
                if d!=0: tk.Button(self.grid_f, text=str(d), bg="white", relief="flat", command=lambda x=d: self.sel(x)).grid(row=r+1, column=c, sticky="nsew", padx=1, pady=1)
        for i in range(7): self.grid_f.grid_columnconfigure(i, weight=1)
    def prev(self): self.month-=1; self.month==0 and (exec('self.month=12;self.year-=1')); self.render()
    def next(self): self.month+=1; self.month==13 and (exec('self.month=1;self.year+=1')); self.render()
    def sel(self, d): self.callback(f"{d:02d}/{self.month:02d}/{self.year}"); self.destroy()

class BorradoMasivoPopup(tk.Toplevel):
    def __init__(self, parent, app_data, cb):
        super().__init__(parent)
        self.title("Borrar Clases"); self.geometry("500x600"); self.configure(bg="white")
        self.app_data, self.cb, self.vars, self.refs = app_data, cb, [], []
        tk.Label(self, text="Selecciona para borrar", bg="white", font=("Segoe UI", 12, "bold")).pack(pady=10)
        c = tk.Frame(self, bg="white"); c.pack(fill="both", expand=True, padx=10)
        cv = tk.Canvas(c, bg="white"); sb = tk.Scrollbar(c, command=cv.yview)
        fr = tk.Frame(cv, bg="white"); fr.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0,0), window=fr, anchor="nw"); cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        has = False
        dias_ord = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        # FIX: Mostrar rango completo por si hay datos viejos, o ajustarlo
        for d in dias_ord:
            for h in range(24):
                clases = self.app_data["agenda"][d].get(str(h)) or self.app_data["agenda"][d].get(h)
                if clases:
                    if not isinstance(clases, list): clases = [clases]
                    for idx, cl in enumerate(clases):
                        has = True; v = tk.BooleanVar(); self.vars.append(v); self.refs.append((d, h, idx))
                        tk.Checkbutton(fr, text=f"{d} {h:02d}:00 - {cl['nombre']}", variable=v, bg="white", anchor="w", font=("Segoe UI", 10)).pack(fill="x", pady=2)
        if not has: tk.Label(fr, text="Sin clases", bg="white").pack()
        tk.Button(self, text="ELIMINAR", bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), command=self.borrar).pack(fill="x", padx=20, pady=10)
    def borrar(self):
        indices = [i for i, v in enumerate(self.vars) if v.get()]
        if not indices: return
        for i in sorted(indices, reverse=True):
            d, h, idx = self.refs[i]
            lista = self.app_data["agenda"][d].get(str(h)) or self.app_data["agenda"][d].get(h)
            if lista and idx < len(lista): lista.pop(idx)
            self.app_data["agenda"][d][str(h)] = lista
            if int(h) in self.app_data["agenda"][d]: self.app_data["agenda"][d][int(h)] = lista
        self.cb(); messagebox.showinfo("Listo", "Clases borradas"); self.destroy()

class TareasPopup(tk.Toplevel):
    def __init__(self, parent, app_data, cb):
        super().__init__(parent)
        self.title("Tareas ✅"); self.geometry("550x700"); self.configure(bg="white")
        self.app_data, self.cb = app_data, cb
        if "tareas" not in self.app_data: self.app_data["tareas"]=[]
        self.mats = set()
        for d in ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]:
            for h in range(24):
                clases = self.app_data["agenda"][d].get(h) or self.app_data["agenda"][d].get(str(h)) or []
                if not isinstance(clases, list): clases = [clases] if clases else []
                for c in clases: self.mats.add(c["nombre"])
        self.ui(); self.render()
    def ui(self):
        tk.Label(self, text="Nueva Tarea", bg="white", font=("Segoe UI", 12, "bold"), fg="#2C3E50").pack(pady=(10,5))
        f = tk.Frame(self, bg="#f1f2f6", padx=10, pady=10); f.pack(fill="x", padx=15)
        tk.Label(f, text="Título:", bg="#f1f2f6").grid(row=0, column=0, sticky="w"); self.et = tk.Entry(f, width=30); self.et.grid(row=0, column=1, pady=2)
        tk.Label(f, text="Materia:", bg="#f1f2f6").grid(row=1, column=0, sticky="w"); self.cm = ttk.Combobox(f, values=list(self.mats), width=27); self.cm.grid(row=1, column=1, pady=2)
        tk.Label(f, text="Fecha:", bg="#f1f2f6").grid(row=2, column=0, sticky="w")
        fd = tk.Frame(f, bg="#f1f2f6"); fd.grid(row=2, column=1, sticky="w"); self.ef = tk.Entry(fd, width=15); self.ef.pack(side="left")
        tk.Button(fd, text="📅", command=lambda: DatePicker(self, lambda x: (self.ef.delete(0,tk.END), self.ef.insert(0,x))), relief="flat", bg="#bdc3c7").pack(side="left")
        tk.Label(f, text="Desc:", bg="#f1f2f6").grid(row=3, column=0, sticky="nw"); self.td = tk.Text(f, width=30, height=3, font=("Segoe UI", 9)); self.td.grid(row=3, column=1, pady=2)
        tk.Button(f, text="➕ Agregar", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=self.agregar_tarea).grid(row=4, column=0, columnspan=2, pady=10, sticky="we")
        tk.Label(self, text="Pendientes", bg="white", font=("Segoe UI", 12, "bold")).pack(pady=(15,5))
        self.frame_lista = tk.Frame(self, bg="white"); self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)
        self.canvas_lista = tk.Canvas(self.frame_lista, bg="white", highlightthickness=0)
        sb = tk.Scrollbar(self.frame_lista, orient="vertical", command=self.canvas_lista.yview)
        self.inner_frame = tk.Frame(self.canvas_lista, bg="white")
        self.inner_frame.bind("<Configure>", lambda e: self.canvas_lista.configure(scrollregion=self.canvas_lista.bbox("all")))
        self.canvas_lista.create_window((0,0), window=self.inner_frame, anchor="nw", width=500)
        self.canvas_lista.configure(yscrollcommand=sb.set)
        self.canvas_lista.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
    def render(self):
        for w in self.inner_frame.winfo_children(): w.destroy()
        for i, t in enumerate(self.app_data["tareas"]):
            bg = "#dff9fb" if t["hecho"] else "#ffffff"
            c = tk.Frame(self.inner_frame, bg=bg, pady=5, padx=5, bd=1, relief="solid"); c.pack(fill="x", pady=3, padx=2)
            tk.Button(c, text="☑" if t["hecho"] else "⬜", bg=bg, relief="flat", command=lambda x=i: self.tog(x)).pack(side="left")
            info = tk.Frame(c, bg=bg); info.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(info, text=t["titulo"], bg=bg, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(info, text=f"{t.get('materia','-')} | {t['fecha']}", bg=bg, fg="#636e72", font=("Segoe UI", 8), anchor="w").pack(fill="x")
            if t.get("desc"): tk.Label(info, text=t["desc"], bg=bg, fg="#2d3436", font=("Segoe UI", 8), anchor="w").pack(fill="x")
            tk.Button(c, text="🗑", bg="#fab1a0", fg="red", relief="flat", command=lambda x=i: self.rem(x)).pack(side="right")
    def agregar_tarea(self):
        tit = self.et.get().strip()
        if not tit: return messagebox.showwarning("Error", "El título es obligatorio")
        self.app_data["tareas"].append({"titulo": tit, "materia": self.cm.get(), "fecha": self.ef.get(), "desc": self.td.get("1.0", tk.END).strip(), "hecho": False})
        self.cb(); self.et.delete(0, tk.END); self.td.delete("1.0", tk.END); self.entry_fecha.delete(0, tk.END); self.render()
    def tog(self, i): self.app_data["tareas"][i]["hecho"] = not self.app_data["tareas"][i]["hecho"]; self.cb(); self.render()
    def rem(self, i): 
        if messagebox.askyesno("Borrar", "¿Eliminar tarea?"): self.app_data["tareas"].pop(i); self.cb(); self.render()

class GestionDiaDialog(tk.Toplevel):
    def __init__(self, parent, fecha_str, dia_semana, app_data, callback_guardar):
        super().__init__(parent)
        self.title(f"Gestionar: {fecha_str}")
        self.geometry("500x500")
        self.configure(bg="white")
        self.fecha_str, self.dia_semana, self.app_data, self.callback_guardar = fecha_str, dia_semana, app_data, callback_guardar
        self.crear_ui(); self.cargar_listas()
    def crear_ui(self):
        tk.Label(self, text=f"📅 {self.dia_semana}", bg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)
        tk.Label(self, text="📚 Clases", bg="#ecf0f1", anchor="w", padx=10).pack(fill="x")
        self.list_clases = tk.Listbox(self, height=6, bg="#f9f9f9"); self.list_clases.pack(fill="both", expand=True, padx=20)
        tk.Label(self, text="🔴 Eventos", bg="#fad390", anchor="w", padx=10).pack(fill="x")
        self.list_eventos = tk.Listbox(self, height=6, bg="#fff5e6"); self.list_eventos.pack(fill="both", expand=True, padx=20)
        f = tk.Frame(self, bg="white"); f.pack(fill="x", pady=10)
        tk.Button(f, text="➕ Evento", command=self.add).pack(side="left", padx=20)
        tk.Button(f, text="🗑 Borrar Evento", command=self.rem).pack(side="right", padx=20)
    def cargar_listas(self):
        self.list_clases.delete(0, tk.END); self.list_eventos.delete(0, tk.END)
        ag = self.app_data["agenda"].get(self.dia_semana, {})
        for h in range(24):
            clases = ag.get(h) or ag.get(str(h)) or []
            if not isinstance(clases, list): clases = [clases] if clases else []
            for c in clases: self.list_clases.insert(tk.END, f"{h:02d}:00 - {c['nombre']}")
        for e in self.app_data.get("eventos", {}).get(self.fecha_str, []): self.list_eventos.insert(tk.END, e)
    def add(self):
        n = simpledialog.askstring("Nuevo", "Evento:")
        if n:
            if "eventos" not in self.app_data: self.app_data["eventos"]={}
            if self.fecha_str not in self.app_data["eventos"]: self.app_data["eventos"][self.fecha_str]=[]
            self.app_data["eventos"][self.fecha_str].append(n); self.callback_guardar(); self.cargar_listas()
    def rem(self):
        s = self.list_eventos.curselection()
        if s: self.app_data["eventos"][self.fecha_str].pop(s[0]); self.callback_guardar(); self.cargar_listas()

class CalendarioPopup(tk.Toplevel):
    def __init__(self, parent, app_data, on_save, modo_oscuro):
        super().__init__(parent)
        self.title("Calendario 📅")
        self.geometry("1000x750")
        self.app_data = app_data
        self.on_save = on_save
        self.colors = {"bg": "#2d2d2d" if modo_oscuro else "white", "fg": "white" if modo_oscuro else "black", "card": "#3d3d3d" if modo_oscuro else "white"}
        self.configure(bg=self.colors["bg"])
        self.dt = datetime.now()
        self.year = self.current_date = self.dt.year
        self.month = self.dt.month
        self.crear_ui()
        self.renderizar_calendario()
    def crear_ui(self):
        top = tk.Frame(self, bg="#2C3E50", pady=10); top.pack(fill="x")
        tk.Button(top, text="<", command=self.prev, bg="#34495E", fg="white", relief="flat").pack(side="left", padx=20)
        self.lbl_mes = tk.Label(top, text="", bg="#2C3E50", fg="white", font=("Arial", 16))
        self.lbl_mes.pack(side="left", expand=True)
        tk.Button(top, text=">", command=self.next, bg="#34495E", fg="white", relief="flat").pack(side="right", padx=20)
        self.grid_frame = tk.Frame(self, bg=self.colors["bg"]); self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
    def renderizar_calendario(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.lbl_mes.config(text=f"{calendar.month_name[self.month]} {self.year}")
        cal = calendar.monthcalendar(self.year, self.month)
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, d in enumerate(["L", "M", "M", "J", "V", "S", "D"]): 
            tk.Label(self.grid_frame, text=d, bg=self.colors["bg"], fg=self.colors["fg"], font=("Arial", 10, "bold")).grid(row=0, column=i)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0: continue
                f_str = f"{self.year}-{self.month:02d}-{day:02d}"
                fr = tk.Frame(self.grid_frame, bg=self.colors["card"], highlightbackground="grey", highlightthickness=1)
                fr.grid(row=r+1, column=c, sticky="nsew", padx=1, pady=1)
                tk.Label(fr, text=str(day), bg=self.colors["card"], fg=self.colors["fg"], font=("Arial", 9, "bold")).pack(anchor="nw")
                agenda_dia = self.app_data["agenda"].get(dias_nombres[c], {})
                vistos = set()
                for h in range(24):
                    clases = agenda_dia.get(str(h)) or agenda_dia.get(h) or []
                    if not isinstance(clases, list): clases = [clases] if clases else []
                    for cl in clases:
                        if cl and cl["nombre"] not in vistos:
                            tk.Label(fr, text=f"• {cl['nombre']}", bg=self.colors["card"], fg="#3498db", font=("Arial", 7)).pack(anchor="w")
                            vistos.add(cl["nombre"])
                for e in self.app_data.get("eventos", {}).get(f_str, []):
                    tk.Label(fr, text=f"🔴 {e}", bg=self.colors["card"], fg="#e74c3c", font=("Arial", 7)).pack(anchor="w")
                fr.bind("<Button-1>", lambda e, f=f_str, d=dias_nombres[c]: self.abrir_gestor(f, d))
                for ch in fr.winfo_children(): ch.bind("<Button-1>", lambda e, f=f_str, d=dias_nombres[c]: self.abrir_gestor(f, d))
        for i in range(7): self.grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(cal)+1): self.grid_frame.grid_rowconfigure(i, weight=1)
    def abrir_gestor(self, f, d): 
        # FIX: Esperar a cerrar
        dlg = GestionDiaDialog(self, f, d, self.app_data, self.on_save)
        self.wait_window(dlg)
        self.renderizar_calendario()
    def prev(self): self.month-=1; self.month==0 and (exec('self.month=12;self.year-=1')); self.renderizar_calendario()
    def next(self): self.month+=1; self.month==13 and (exec('self.month=1;self.year+=1')); self.renderizar_calendario()

class NotasPopup(tk.Toplevel):
    def __init__(self, parent, app_data, callback_guardar, materias_unicas):
        super().__init__(parent)
        self.title("Gestor Académico 📊")
        self.geometry("750x550")
        self.configure(bg="white")
        self.app_data = app_data
        self.callback_guardar = callback_guardar
        self.materias = list(materias_unicas)
        if "academico" not in self.app_data: self.app_data["academico"] = {}
        self.entries = {}
        self.crear_ui()

    def crear_ui(self):
        tk.Label(self, text="Control de Calificaciones y Asistencia", bg="white", font=("Segoe UI", 14, "bold"), fg="#2C3E50").pack(pady=15)
        h_frame = tk.Frame(self, bg="#2D3748")
        h_frame.pack(fill="x", padx=20)
        cols = ["Materia", "Nota (0-100)", "Faltas", "Estado"]
        widths = [30, 15, 10, 20]
        for i, c in enumerate(cols):
            tk.Label(h_frame, text=c, bg="#2D3748", fg="white", font=("Segoe UI", 9, "bold"), width=widths[i]).pack(side="left", padx=1, pady=5)
        container = tk.Frame(self, bg="white")
        container.pack(fill="both", expand=True, padx=20, pady=5)
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for i, materia in enumerate(self.materias):
            bg_row = "#F7F9FC" if i % 2 == 0 else "#FFFFFF"
            row = tk.Frame(scroll_frame, bg=bg_row, pady=5)
            row.pack(fill="x")
            dat = self.app_data["academico"].get(materia, {"nota": "0", "faltas": "0"})
            tk.Label(row, text=materia, bg=bg_row, width=30, anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
            v_nota = tk.StringVar(value=dat["nota"])
            e_nota = tk.Entry(row, textvariable=v_nota, width=10, justify="center")
            e_nota.pack(side="left", padx=30)
            v_fal = tk.StringVar(value=dat["faltas"])
            tk.Spinbox(row, from_=0, to=99, textvariable=v_fal, width=5, justify="center").pack(side="left", padx=20)
            lbl_est = tk.Label(row, text="-", width=15, font=("Segoe UI", 9, "bold"), bg=bg_row)
            lbl_est.pack(side="left", padx=10)
            self.entries[materia] = {"n": v_nota, "f": v_fal, "l": lbl_est}
            e_nota.bind("<KeyRelease>", lambda e, m=materia: self.calc_estado(m))
            self.calc_estado(materia)
        tk.Button(self, text="💾 Guardar Cambios", bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", command=self.guardar).pack(pady=15)

    def calc_estado(self, m):
        try:
            val = float(self.entries[m]["n"].get())
            lbl = self.entries[m]["l"]
            if val >= 90: lbl.config(text="🔥 Excelente", fg="#27ae60")
            elif val >= 70: lbl.config(text="✅ Aprobado", fg="#f39c12")
            else: lbl.config(text="⚠️ Reprobando", fg="#c0392b")
        except: self.entries[m]["l"].config(text="...", fg="grey")

    def guardar(self):
        for m, r in self.entries.items():
            self.app_data["academico"][m] = {"nota": r["n"].get(), "faltas": r["f"].get()}
        self.callback_guardar(); self.destroy()

# ==========================================
# 3. APP PRINCIPAL
# ==========================================

class HorarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enger's Scheduler 🚀")
        try: self.root.state('zoomed') 
        except: self.root.geometry("1200x780")
        self.DB_FILE = "mi_horario_data.json"
        self.dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        self.tiempo_pomodoro = 25 * 60; self.timer_corriendo = False
        self.modo_oscuro = False; self.custom_bg = None
        self.estado_dias = {dia: False for dia in self.dias}
        self.botones_dias = {}; self.memoria_colores = {}; self.seleccionado = None 
        self.temas = {"light": {"bg_app": "#F7F9FC", "bg_panel": "white", "fg_text": "#2D3436", "bg_header": "#2D3748", "bg_input": "#F7F9FC", "fg_input": "black", "grid_line": "#E2E8F0", "chip_off": "#F1F2F6", "chip_text": "#636E72"}, "dark": {"bg_app": "#1e1e1e", "bg_panel": "#2d2d2d", "fg_text": "#dfe6e9", "bg_header": "#000000", "bg_input": "#3d3d3d", "fg_input": "white", "grid_line": "#444444", "chip_off": "#444444", "chip_text": "#b2bec3"}}
        self.colores_bloques = ["#FFCCB6", "#E6F3B1", "#B3E5FC", "#D1C4E9", "#FFCDD2", "#C8E6C9", "#FFF9C4", "#F8BBD0", "#E1BEE7", "#B2DFDB"]
        self.start_hour = 5 # Inicio 5:00 AM
        
        self.crear_menu_contextual()
        self.cargar_datos()
        self.crear_barra_superior()
        self.crear_panel_control() 
        self.crear_encabezados_tabla()
        self.container = ScrollableFrame(self.root, bg_color=self.temas["light"]["bg_app"])
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        try: self.renderizar_horario()
        except tk.TclError: self.reparacion_emergencia()
        self.aplicar_tema()

    # --- FUNCIONES ---
    def abrir_tareas(self): TareasPopup(self.root, self.datos_globales, self.guardar_datos)
    def abrir_calendario(self): CalendarioPopup(self.root, self.datos_globales, self.guardar_datos, self.modo_oscuro)
    def borrar_masivo(self): BorradoMasivoPopup(self.root, self.datos_globales, lambda: (self.guardar_datos(), self.renderizar_horario()))
    def cambiar_fondo(self):
        c = colorchooser.askcolor()[1]
        if c: self.custom_bg = c; self.guardar_datos(); self.aplicar_tema()
    
    def alternar_tema(self): self.modo_oscuro = not self.modo_oscuro; self.aplicar_tema(); self.guardar_datos()
    
    def aplicar_tema(self):
        t = self.temas["dark" if self.modo_oscuro else "light"]
        if self.modo_oscuro: bg = t["bg_app"]
        else: bg = self.custom_bg if self.custom_bg else t["bg_app"]
            
        self.root.configure(bg=bg); self.container.set_bg(bg)
        self.frame_panel.configure(bg=t["bg_panel"])
        self.frame_fila1.configure(bg=t["bg_panel"])
        self.frame_fila2.configure(bg=t["bg_panel"])
        self.lbl_select.configure(bg=t["bg_panel"], fg=t["fg_text"])
        self.lbl_tip.configure(bg=t["bg_panel"], fg="#A0AEC0")
        for lbl in [self.lbl_mat, self.lbl_ini, self.lbl_fin, self.lbl_aul, self.lbl_pro]: lbl.configure(bg=t["bg_panel"], fg="#A0AEC0")
        for inp in [self.entry_materia, self.entry_aula, self.entry_prof]: inp.configure(bg=t["bg_input"], fg=t["fg_input"], insertbackground=t["fg_input"])
        self.header_frame.configure(bg=t["bg_header"])
        for widget in self.header_frame.winfo_children(): widget.configure(bg=t["bg_header"], fg="white")
        
        for dia in self.dias:
            if not self.estado_dias[dia]: self.botones_dias[dia].configure(bg=t["chip_off"], fg=t["chip_text"])
        
        self.btn_theme.config(text="☀️" if self.modo_oscuro else "🌙")
        self.renderizar_horario()

    def renderizar_horario(self):
        for w in self.container.scrollable_frame.winfo_children(): w.destroy()
        t = self.temas["dark" if self.modo_oscuro else "light"]
        bg = t["bg_app"] if self.modo_oscuro else (self.custom_bg if self.custom_bg else t["bg_app"])
        hora_color = "#A0AEC0" if not self.modo_oscuro else "#b2bec3"

        for h in range(self.start_hour, 24):
            lbl = tk.Label(self.container.scrollable_frame, text=f"{h:02d}:00", bg=bg, fg=hora_color, width=8, height=3, font=("Segoe UI", 9)); lbl.grid(row=h, column=0, sticky="ns")
            tk.Frame(self.container.scrollable_frame, bg=t["grid_line"], height=1).grid(row=h, column=0, columnspan=8, sticky="s")
            for i, d in enumerate(self.dias):
                dat = self.agenda[d].get(h) or self.agenda[d].get(str(h))
                wrap = tk.Frame(self.container.scrollable_frame, bg=bg); wrap.grid(row=h, column=i+1, sticky="nsew")
                if dat:
                    clases = dat if isinstance(dat, list) else [dat]
                    for idx, c in enumerate(clases):
                        card = tk.Frame(wrap, bg=c["color"], cursor="hand2"); card.pack(side="left", fill="both", expand=True, padx=1, pady=1)
                        tk.Frame(card, bg="#2d3436", width=4).pack(side="left", fill="y")
                        tf = tk.Frame(card, bg=c["color"]); tf.pack(side="left", fill="both", expand=True, padx=2, pady=2)
                        tk.Label(tf, text=c["nombre"], bg=c["color"], fg="#2D3748", font=("Segoe UI Semibold", 9), anchor="center").pack(fill="x")
                        dt = ""
                        if c.get("aula"): dt += f"📍{c['aula']} "
                        if c.get("profesor"): dt += f"👤{c['profesor']}"
                        if dt: tk.Label(tf, text=dt, bg=c["color"], fg="#4a5568", font=("Segoe UI", 7), anchor="center").pack(fill="x")
                        for w in [card, tf]:
                            w.bind("<Button-3>", lambda e, dd=d, hh=h, ii=idx: self.mostrar_menu(e, dd, hh, ii))
                            w.bind("<Button-2>", lambda e, dd=d, hh=h, ii=idx: self.mostrar_menu(e, dd, hh, ii))
        self.container.scrollable_frame.grid_columnconfigure(0, minsize=60)
        for i in range(1, 8): self.container.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=110)
        self.actualizar_contador_hoy()

    def agregar_clase(self):
        m = self.entry_materia.get().strip()
        if not m: return messagebox.showwarning("Error", "Falta nombre")
        ds = [d for d in self.dias if self.estado_dias[d]]
        if not ds: return messagebox.showwarning("Error", "Selecciona días")
        h1 = int(self.combo_inicio.get()[:2]); h2 = int(self.combo_fin.get()[:2])
        if h2 <= h1: return messagebox.showerror("Error", "Hora fin menor")
        c = self.obtener_color(m)
        for d in ds:
            for h in range(h1, h2):
                current = self.agenda[d].get(h) or self.agenda[d].get(str(h)) or []
                if not isinstance(current, list): current = [current] if current else []
                current.append({"nombre": m, "color": c, "aula": self.entry_aula.get(), "profesor": self.entry_prof.get()})
                self.agenda[d][h] = current
        self.guardar_datos(); self.renderizar_horario()
        for d in self.dias: self.estado_dias[d] = False; self.update_dia_visual(d)
        self.entry_materia.delete(0, tk.END); self.entry_aula.delete(0, tk.END); self.entry_prof.delete(0, tk.END)
        messagebox.showinfo("Éxito", "Clase guardada")

    def toggle_dia_click(self, d):
        self.estado_dias[d] = not self.estado_dias[d]
        self.update_dia_visual(d)

    def update_dia_visual(self, d):
        c = self.temas["dark" if self.modo_oscuro else "light"]
        self.botones_dias[d].config(bg="#6C5CE7" if self.estado_dias[d] else c["chip_off"], fg="white" if self.estado_dias[d] else c["chip_text"])

    def cargar_datos(self):
        if os.path.exists(self.DB_FILE):
            try:
                with open(self.DB_FILE, "r") as f: self.datos_globales = json.load(f)
                self.agenda = {}
                da = self.datos_globales.get("agenda", {})
                for d in self.dias:
                    self.agenda[d] = {}
                    if d in da:
                        for h, c in da[d].items(): 
                            self.agenda[d][int(h)] = c if isinstance(c, list) else ([c] if c else [])
                            if isinstance(c, list):
                                for item in c: self.memoria_colores[item["nombre"].lower()] = item["color"]
                            elif c: self.memoria_colores[c["nombre"].lower()] = c["color"]
                    else:
                        for h in range(24): self.agenda[d][h] = []
                self.modo_oscuro = self.datos_globales.get("modo_oscuro", False)
                self.custom_bg = self.datos_globales.get("custom_bg", None)
            except: self.iniciar_vacio()
        else: self.iniciar_vacio()
    def iniciar_vacio(self):
        self.agenda = {d: {h: [] for h in range(24)} for d in self.dias}
        self.datos_globales = {"agenda": self.agenda, "modo_oscuro": False, "eventos": {}, "tareas": [], "custom_bg": None}
    def guardar_datos(self):
        self.datos_globales["agenda"] = self.agenda
        self.datos_globales["modo_oscuro"] = self.modo_oscuro
        self.datos_globales["custom_bg"] = self.custom_bg
        try:
            with open(self.DB_FILE, "w") as f: json.dump(self.datos_globales, f, indent=4)
        except Exception as e: messagebox.showerror("Error", str(e))
    def crear_barra_superior(self):
        self.top_banner = tk.Frame(self.root, bg="#2C3E50", height=50); self.top_banner.pack(fill="x", side="top")
        self.lbl_contador = tk.Label(self.top_banner, text="...", bg="#2C3E50", fg="#ECF0F1", font=("Segoe UI", 11)); self.lbl_contador.pack(side="left", padx=20)
        rf = tk.Frame(self.top_banner, bg="#2C3E50"); rf.pack(side="right", padx=20)
        tk.Button(rf, text="🗑 Borrar Masivo", command=self.borrar_masivo, bg="#c0392b", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(rf, text="✅ Tareas", command=self.abrir_tareas, bg="#27ae60", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(rf, text="📊 Notas", command=self.abrir_notas, bg="#2980b9", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(rf, text="📅 Calendario", command=self.abrir_calendario, bg="#8e44ad", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(rf, text="📄 PDF", command=self.exportar_html, bg="#E67E22", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(rf, text="🎨 Fondo", command=self.cambiar_fondo, bg="#16a085", fg="white", relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        pomo = tk.Frame(rf, bg="#34495E", padx=10, pady=2); pomo.pack(side="left", padx=10)
        self.lbl_timer = tk.Label(pomo, text="25:00", bg="#34495E", fg="#F1C40F", font=("Consolas", 14, "bold")); self.lbl_timer.pack(side="left", padx=5)
        st = {"bg": "#2C3E50", "fg": "white", "relief": "flat", "width": 3}
        tk.Button(pomo, text="▶", command=self.iniciar_pomodoro, **st).pack(side="left")
        tk.Button(pomo, text="⏸", command=self.pausar_pomodoro, **st).pack(side="left")
        tk.Button(pomo, text="⚡", command=self.reset_pomodoro, **st).pack(side="left")
        self.btn_theme = tk.Button(rf, text="🌙", bg="#34495E", fg="white", relief="flat", command=self.alternar_tema); self.btn_theme.pack(side="left", padx=10)

    def crear_panel_control(self):
        self.frame_panel = tk.Frame(self.root, bg="white", pady=15, padx=20); self.frame_panel.pack(fill="x", pady=10, padx=20)
        font_lbl, font_ent = ("Segoe UI", 8, "bold"), ("Segoe UI", 9)
        self.frame_fila1 = tk.Frame(self.frame_panel, bg="white"); self.frame_fila1.pack(fill="x", pady=5)
        self.lbl_mat = tk.Label(self.frame_fila1, text="MATERIA", font=font_lbl); self.lbl_mat.pack(side="left", padx=5)
        self.entry_materia = tk.Entry(self.frame_fila1, width=18, font=font_ent, relief="flat", highlightthickness=1); self.entry_materia.pack(side="left", padx=15)
        self.lbl_ini = tk.Label(self.frame_fila1, text="INICIO", font=font_lbl); self.lbl_ini.pack(side="left", padx=5)
        self.combo_inicio = ttk.Combobox(self.frame_fila1, values=[f"{h:02d}:00" for h in range(self.start_hour, 24)], state="readonly", width=7, font=font_ent); self.combo_inicio.current(8-self.start_hour); self.combo_inicio.pack(side="left", padx=10)
        self.lbl_fin = tk.Label(self.frame_fila1, text="FIN", font=font_lbl); self.lbl_fin.pack(side="left", padx=5)
        self.combo_fin = ttk.Combobox(self.frame_fila1, values=[f"{h:02d}:00" for h in range(self.start_hour, 24)], state="readonly", width=7, font=font_ent); self.combo_fin.current(10-self.start_hour); self.combo_fin.pack(side="left", padx=15)
        self.lbl_aul = tk.Label(self.frame_fila1, text="AULA", font=font_lbl); self.lbl_aul.pack(side="left", padx=5)
        self.entry_aula = tk.Entry(self.frame_fila1, width=8, font=font_ent, relief="flat", highlightthickness=1); self.entry_aula.pack(side="left", padx=15)
        self.lbl_pro = tk.Label(self.frame_fila1, text="PROFESOR", font=font_lbl); self.lbl_pro.pack(side="left", padx=5)
        self.entry_prof = tk.Entry(self.frame_fila1, width=18, font=font_ent, relief="flat", highlightthickness=1); self.entry_prof.pack(side="left")
        self.frame_fila2 = tk.Frame(self.frame_panel, bg="white"); self.frame_fila2.pack(fill="x", pady=15)
        self.lbl_select = tk.Label(self.frame_fila2, text="SELECCIONAR DÍAS:", font=("Segoe UI", 9, "bold")); self.lbl_select.pack(side="left", padx=10)
        for d in self.dias:
            btn = tk.Button(self.frame_fila2, text=d[:3].upper(), font=("Segoe UI", 8, "bold"), relief="flat", width=5, cursor="hand2", command=lambda x=d: self.toggle_dia_click(x))
            btn.pack(side="left", padx=4); self.botones_dias[d] = btn
        tk.Button(self.frame_fila2, text="＋ Guardar Clases", bg="#48BB78", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=15, pady=4, cursor="hand2", command=self.agregar_clase).pack(side="right", padx=5)
        self.lbl_tip = tk.Label(self.frame_fila2, text="💡 Click derecho para editar", font=("Segoe UI", 8, "italic")); self.lbl_tip.pack(side="right", padx=20)

    def crear_encabezados_tabla(self):
        self.header_frame = tk.Frame(self.root, height=40); self.header_frame.pack(fill="x", padx=20)
        self.header_frame.grid_columnconfigure(0, minsize=60) # Mismo width
        tk.Label(self.header_frame, text="HORA", width=8, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="ns")
        for i, d in enumerate(self.dias):
            self.header_frame.grid_columnconfigure(i+1, weight=1, minsize=110)
            tk.Label(self.header_frame, text=d.upper(), width=1, font=("Segoe UI", 10, "bold")).grid(row=0, column=i+1, sticky="nsew")

    def actualizar_contador_hoy(self):
        n = self.dias[datetime.now().weekday()]
        c = sum(1 for h in range(24) if self.agenda[n].get(h))
        self.lbl_contador.config(text=f"📅 {n}: {c} hrs de clase")

    def crear_menu_contextual(self):
        self.menu_popup = tk.Menu(self.root, tearoff=0)
        self.menu_popup.add_command(label="✏️ Editar", command=self.editar_clase_contextual)
        self.menu_popup.add_separator(); self.menu_popup.add_command(label="🗑️ Eliminar", command=self.eliminar_clase_contextual)
    def mostrar_menu(self, e, d, h, idx): self.seleccionado = (d, h, idx); self.menu_popup.post(e.x_root, e.y_root)
    def editar_clase_contextual(self):
        d, h, idx = self.seleccionado
        clases = self.agenda[d][h]
        if not clases or idx >= len(clases): return
        dat = clases[idx]
        self.entry_materia.delete(0, tk.END); self.entry_materia.insert(0, dat["nombre"])
        self.entry_aula.delete(0, tk.END); self.entry_aula.insert(0, dat["aula"])
        self.entry_prof.delete(0, tk.END); self.entry_prof.insert(0, dat["profesor"])
        self.combo_inicio.set(f"{h:02d}:00"); self.combo_fin.set(f"{h+1:02d}:00")
        for x in self.dias: self.estado_dias[x] = False; self.update_dia_visual(x)
        self.estado_dias[d] = True; self.update_dia_visual(d)
        if messagebox.askyesno("Editar", "Se cargarán los datos. ¿Borrar la entrada original para moverla?"):
            clases.pop(idx); self.guardar_datos(); self.renderizar_horario()
    def eliminar_clase_contextual(self): 
        d, h, idx = self.seleccionado
        clases = self.agenda[d][h]
        if clases and idx < len(clases): clases.pop(idx); self.guardar_datos(); self.renderizar_horario()
    def obtener_color(self, n):
        if n.lower() in self.memoria_colores: return self.memoria_colores[n.lower()]
        c = random.choice(self.colores_bloques); self.memoria_colores[n.lower()] = c; return c
    def reparacion_emergencia(self):
        if os.path.exists(self.DB_FILE): os.remove(self.DB_FILE)
        self.iniciar_vacio(); self.renderizar_horario()
    def iniciar_pomodoro(self): 
        if not self.timer_corriendo: self.timer_corriendo=True; self.actualizar_reloj()
    def pausar_pomodoro(self): self.timer_corriendo=False
    def reset_pomodoro(self): self.timer_corriendo=False; self.tiempo_pomodoro=25*60; self.lbl_timer.config(text="25:00", fg="#F1C40F")
    def actualizar_reloj(self):
        if self.timer_corriendo:
            if self.tiempo_pomodoro>0:
                m,s=divmod(self.tiempo_pomodoro,60); self.lbl_timer.config(text=f"{m:02d}:{s:02d}", fg="#2ECC71"); self.tiempo_pomodoro-=1; self.root.after(1000, self.actualizar_reloj)
            else: self.timer_corriendo=False; winsound.Beep(1000,1000)
    
    def abrir_notas(self):
        ms = set()
        for d in self.dias:
            for h in range(24):
                clases = self.agenda[d].get(h) or []
                if isinstance(clases, list):
                    for c in clases: ms.add(c["nombre"])
        if not ms: return messagebox.showinfo("Info", "Añade clases primero")
        NotasPopup(self.root, self.datos_globales, self.guardar_datos, ms)

    def exportar_html(self):
        header_bg = "#2C3E50"
        header_text = "#FFFFFF"
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Mi Horario</title>
        <style>@import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
        body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; background-color: #f4f4f9; color: #333; }}
        h1 {{ text-align: center; color: {header_bg}; text-transform: uppercase; }}
        .table-container {{ width: 100%; overflow-x: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-radius: 8px; background: white; }}
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        th {{ background-color: {header_bg}; color: {header_text}; padding: 15px; text-transform: uppercase; border-right: 1px solid rgba(255,255,255,0.1); }}
        td {{ border: 1px solid #e0e0e0; padding: 4px; height: 60px; vertical-align: top; background-color: #fff; }}
        .time-col {{ background-color: #f8f9fa; color: #7f8c8d; font-weight: bold; text-align: center; vertical-align: middle; width: 60px; font-size: 12px; }}
        .cell-content {{ display: flex; gap: 4px; height: 100%; width: 100%; }}
        .materia-card {{ flex: 1; padding: 6px; border-radius: 4px; font-size: 11px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; flex-direction: column; justify-content: center; overflow: hidden; border-left: 4px solid rgba(0,0,0,0.2); }}
        .materia-name {{ font-weight: 700; margin-bottom: 2px; color: #2c3e50; }}
        .materia-info {{ font-size: 10px; color: #555; opacity: 0.9; }}
        @media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; background: white; }} .table-container {{ box-shadow: none; }} }}
        </style></head><body><h1>📅 Mi Horario Semanal</h1><div class="table-container"><table><thead><tr><th style="width: 60px;">Hora</th>{''.join([f'<th>{d.upper()}</th>' for d in self.dias])}</tr></thead><tbody>"""

        for h in range(self.start_hour, 24):
            html += f"<tr><td class='time-col'>{h:02d}:00</td>"
            for d in self.dias:
                clases = self.agenda[d].get(h) or self.agenda[d].get(str(h)) or []
                if not isinstance(clases, list): clases = [clases] if clases else []
                cell_content = "<div class='cell-content'>"
                for c in clases:
                    details = []
                    if c.get('aula'): details.append(f"📍 {c['aula']}")
                    if c.get('profesor'): details.append(f"👤 {c['profesor']}")
                    info_html = "<br>".join(details)
                    cell_content += f"""<div class="materia-card" style="background-color: {c['color']};"><div class="materia-name">{c['nombre']}</div><div class="materia-info">{info_html}</div></div>"""
                cell_content += "</div>"
                html += f"<td>{cell_content}</td>"
            html += "</tr>"
        html += """</tbody></table></div><p style="text-align: center; color: #aaa; margin-top: 20px; font-size: 12px;">Generado con Enger's Scheduler 🚀</p></body></html>"""
        
        filename = "Horario_Pro.html"
        with open(filename, "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open('file://' + os.path.realpath(filename))

if __name__ == "__main__":
    root = tk.Tk()
    app = HorarioApp(root)
    root.mainloop()