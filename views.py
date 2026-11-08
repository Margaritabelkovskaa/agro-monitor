import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from models import *

BG_MAIN = "#f4f4f4"
BG_WHITE = "#ffffff"
COLOR_TEXT = "#333333"
COLOR_MUTED = "#888888"


def make_btn(parent, text, cmd=None):
    return tk.Button(parent, text=text, command=cmd, font=("Arial", 9), bg="#e0e0e0", relief="raised", bd=1,
                     cursor="hand2", padx=10, pady=4)


def make_entry(parent, width=30, show=None):
    return tk.Entry(parent, font=("Arial", 9), bd=1, relief="solid", width=width, show=show)


def center_window(win, w, h):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


class CustomTable(tk.Frame):
    def __init__(self, parent, columns, on_click=None, on_double_click=None):
        super().__init__(parent, bg=BG_WHITE, bd=1, relief="solid")
        self.on_click = on_click;
        self.on_double_click = on_double_click
        if len(columns) == 5:
            self.col_widths = [130, 100, 110, 110, 170]
        elif len(columns) == 4:
            self.col_widths = [100, 100, 250, 100]
        elif len(columns) == 3:
            self.col_widths = [150, 100, 150]
        else:
            self.col_widths = [150] * len(columns)
        self._selected_row = None
        self.header = tk.Frame(self, bg="#f5f5f5", height=30);
        self.header.pack(fill="x");
        self.header.pack_propagate(False)
        for i, col in enumerate(columns):
            tk.Label(self.header, text=col, font=("Arial", 9, "bold"), bg="#f5f5f5", anchor="w").place(
                x=sum(self.col_widths[:i]) + 5, y=6)
        main = tk.Frame(self, bg=BG_WHITE);
        main.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main, bg=BG_WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(main, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y");
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=BG_WHITE)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel);
        self.inner.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists(): self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def draw_row(self, data, status_idx, status_text, status_bg, status_fg, row_id=None):
        row = tk.Frame(self.inner, bg=BG_WHITE, height=34);
        row.pack(fill="x", expand=True);
        row.pack_propagate(False)
        row.bind("<Button-1>", lambda e, r=row, rid=row_id: self._on_click(r, rid))
        row.bind("<Double-1>", lambda e, rid=row_id: self._on_double(rid))
        for i, text in enumerate(data):
            x = sum(self.col_widths[:i]) + 5
            if i == status_idx:
                b = tk.Label(row, text=status_text, bg=status_bg, fg=status_fg, font=("Arial", 8, "bold"), padx=8,
                             pady=2)
                b.place(x=x, y=7)
                b.bind("<Button-1>", lambda e, r=row, rid=row_id: self._on_click(r, rid));
                b.bind("<Double-1>", lambda e, rid=row_id: self._on_double(rid));
                b.bind("<MouseWheel>", self._on_mousewheel)
            else:
                l = tk.Label(row, text=text, bg=BG_WHITE, anchor="w", font=("Arial", 9))
                l.place(x=x, y=7)
                l.bind("<Button-1>", lambda e, r=row, rid=row_id: self._on_click(r, rid));
                l.bind("<Double-1>", lambda e, rid=row_id: self._on_double(rid));
                l.bind("<MouseWheel>", self._on_mousewheel)
        tk.Frame(self.inner, height=1, bg="#e0e0e0").pack(fill="x")

    def _on_click(self, row, row_id):
        if self._selected_row and self._selected_row.winfo_exists():
            self._selected_row.configure(bg=BG_WHITE)
            for c in self._selected_row.winfo_children():
                if c.cget("bg") not in ("#d4edda", "#fcf8e3", "#f2dede", "#d9edf7"): c.configure(bg=BG_WHITE)
        row.configure(bg="#e6f0fa")
        for c in row.winfo_children():
            if c.cget("bg") not in ("#d4edda", "#fcf8e3", "#f2dede", "#d9edf7"): c.configure(bg="#e6f0fa")
        self._selected_row = row
        if self.on_click and row_id: self.on_click(row_id)

    def _on_double(self, row_id):
        if self.on_double_click and row_id: self.on_double_click(row_id)

    def clear(self):
        for w in self.inner.winfo_children(): w.destroy()
        self._selected_row = None


class BaseWindow:
    def __init__(self, title, geometry="1000x650"):
        self.root = tk.Toplevel()
        self.root.title(title)
        w, h = map(int, geometry.split('x'))
        center_window(self.root, w, h)
        self.root.configure(bg=BG_MAIN)

    def показать(self): self.root.mainloop()


class LoginWindow:
    def __init__(self, auth, injector):
        self.root = tk.Tk()
        self.root.title("Вход");
        center_window(self.root, 450, 350);
        self.root.configure(bg=BG_MAIN)
        self.auth = auth;
        self.injector = injector
        card = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        card.place(relx=0.5, rely=0.5, anchor="center", width=340, height=280)
        tk.Label(card, text="Агро-монитор — Вход", font=("Arial", 12, "bold"), bg=BG_WHITE).pack(pady=20)
        tk.Label(card, text="Логин", bg=BG_WHITE).pack(anchor="w", padx=30)
        self.e_login = make_entry(card);
        self.e_login.pack(padx=30, pady=(5, 15), ipady=3)
        tk.Label(card, text="Пароль", bg=BG_WHITE).pack(anchor="w", padx=30)
        self.e_pass = make_entry(card, show="*");
        self.e_pass.pack(padx=30, pady=(5, 20), ipady=3)
        make_btn(card, "Войти", self.do_login).pack();
        make_btn(card, "Отмена", self.root.destroy).pack(pady=10)

    def do_login(self):
        user = self.auth.войти(self.e_login.get().strip(), self.e_pass.get().strip())
        if user:
            self.root.withdraw()
            self.injector.создать_главное_окно(user).показать()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def показать(self):
        self.root.mainloop()


class MainWindow(BaseWindow):
    def __init__(self, user: Пользователь, injector):
        super().__init__("Агро-монитор — Мои культуры", "1100x600")
        self.user = user;
        self.injector = injector;
        self._selected_cid = None
        toolbar = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        toolbar.pack(fill="x", padx=10, pady=10)
        if user.может_регистрировать_культуры(): make_btn(toolbar, "+ Зарегистрировать культуру",
                                                          self.open_register).pack(side="left", padx=5, pady=5)
        if user.может_вносить_наблюдения(): make_btn(toolbar, "Внести наблюдение", self.open_add_obs).pack(side="left",
                                                                                                           padx=5,
                                                                                                           pady=5)
        self.btn_notif = make_btn(toolbar, "Оповещения (0)", self.open_notifications);
        self.btn_notif.pack(side="left", padx=5, pady=5)
        if user.может_смотреть_отчеты(): make_btn(toolbar, "Сводный отчёт", self.open_report).pack(side="left", padx=5,
                                                                                                   pady=5)
        if user.может_управлять_датчиками(): make_btn(toolbar, "Админ", self.open_admin).pack(side="left", padx=5,
                                                                                              pady=5)
        make_btn(toolbar, "Выход", self.root.destroy).pack(side="right", padx=5, pady=5)

        content = tk.Frame(self.root, bg=BG_MAIN);
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid", width=180);
        left.pack(side="left", fill="y", padx=(0, 10));
        left.pack_propagate(False)
        tk.Label(left, text="Участки", font=("Arial", 9, "bold"), bg=BG_WHITE, anchor="w").pack(fill="x", padx=10,
                                                                                                pady=10)
        self.lb_plots = tk.Listbox(left, bd=0, font=("Arial", 9), selectbackground="#e6f0fa", highlightthickness=0)
        self.lb_plots.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        self.lb_plots.insert(tk.END, "Все участки")
        for p in injector.plot_repo.get_all(): self.lb_plots.insert(tk.END, p.название)
        self.lb_plots.bind("<<ListboxSelect>>", self.filter_by_plot)

        right = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid");
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Культуры хозяйства", font=("Arial", 9, "bold"), bg=BG_WHITE, anchor="w").pack(fill="x",
                                                                                                            padx=10,
                                                                                                            pady=10)
        self.table = CustomTable(right, ["Культура", "Сорт", "Участок", "Фаза роста", "Состояние"],
                                 on_click=self.select_culture, on_double_click=self.open_card)
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.refresh();
        self.root.after(2000, self.auto_update)

    def auto_update(self):
        if not self.root.winfo_exists(): return
        self.refresh()
        unread = len([n for n in self.injector.notification_controller.все() if not n.прочитано])
        self.btn_notif.config(text=f"Оповещения ({unread})")
        self.root.after(2000, self.auto_update)

    def select_culture(self, cid):
        self._selected_cid = cid

    def open_card(self, cid):
        self.injector.создать_окно_карточки(cid, self.user).показать()

    def refresh(self, plot_name=None):
        self.table.clear()
        for c in self.injector.culture_controller.все():
            plot = self.injector.plot_repo.get_by_id(c.id_участка);
            pname = plot.название if plot else ""
            if plot_name and plot_name != "Все участки" and pname != plot_name: continue
            bg, fg = ("#d4edda", "#155724") if c.оценка == ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ else (
                ("#fcf8e3", "#8a6d3b") if c.оценка == ОценкаСостояния.ТРЕБУЕТ_ВНИМАНИЯ else ("#f2dede", "#a94442"))
            self.table.draw_row([c.название, c.сорт, pname, c.фаза_роста.value, ""], 4, c.оценка.value, bg, fg,
                                row_id=c.id)

    def filter_by_plot(self, _):
        sel = self.lb_plots.curselection()
        if sel: self.refresh(self.lb_plots.get(sel[0]))

    def open_register(self):
        self.injector.создать_окно_регистрации(self.user).показать()

    def open_notifications(self):
        self.injector.создать_окно_оповещений(self.user).показать()

    def open_report(self):
        self.injector.создать_окно_отчета().показать()

    def open_admin(self):
        self.injector.создать_окно_админа().показать()

    def open_add_obs(self):
        if self._selected_cid:
            self.injector.создать_окно_наблюдения(self._selected_cid, self.user).показать()
        else:
            messagebox.showinfo("Инфо", "Сначала кликните по культуре в таблице")


class CultureCardWindow(BaseWindow):
    def __init__(self, cid, user, injector):
        self.culture = injector.culture_repo.get_by_id(cid);
        plot = injector.plot_repo.get_by_id(self.culture.id_участка)
        super().__init__(f"Карточка: {self.culture.название}", "850x600");
        self.user = user;
        self.injector = injector
        top = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        top.pack(fill="x", padx=10, pady=10)
        make_btn(top, "← К списку", self.root.destroy).pack(side="left", padx=5, pady=5)
        if self.user.может_вносить_наблюдения(): make_btn(top, "Внести наблюдение", self.open_add).pack(side="left",
                                                                                                        padx=5, pady=5)
        make_btn(top, "Журнал", self.open_journal).pack(side="left", padx=5, pady=5)
        content = tk.Frame(self.root, bg=BG_MAIN);
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        left = tk.Frame(content, bg=BG_WHITE, bd=1, relief="solid", width=280);
        left.pack(side="left", fill="y", padx=(0, 10));
        left.pack_propagate(False)
        tk.Label(left, text="Общие сведения", font=("Arial", 9, "bold"), bg=BG_WHITE, anchor="w").pack(fill="x",
                                                                                                       padx=10, pady=10)
        self._info(left, "Культура", self.culture.название);
        self._info(left, "Сорт", self.culture.сорт)
        self._info(left, "Участок", plot.название if plot else "");
        self._info(left, "Дата посадки", self.culture.дата_посадки.strftime("%d.%m.%Y"))
        self._info(left, "Фаза роста", self.culture.фаза_роста.value)
        f = tk.Frame(left, bg=BG_WHITE);
        f.pack(fill="x", padx=10, pady=4);
        tk.Label(f, text="Состояние", width=15, anchor="w", bg=BG_WHITE, fg=COLOR_MUTED, font=("Arial", 9)).pack(
            side="left")
        bg, fg = ("#d4edda", "#155724") if self.culture.оценка == ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ else (
            ("#fcf8e3", "#8a6d3b") if self.culture.оценка == ОценкаСостояния.ТРЕБУЕТ_ВНИМАНИЯ else (
            "#f2dede", "#a94442"))
        tk.Label(f, text=self.culture.оценка.value, bg=bg, fg=fg, font=("Arial", 8, "bold"), padx=8, pady=2).pack(
            side="left")

        rec = tk.Frame(left, bg="#fff9e6", bd=1, relief="solid");
        rec.pack(fill="x", padx=10, pady=20)
        tk.Label(rec, text="Рекомендации системы", font=("Arial", 9, "bold"), bg="#fff9e6", fg="#8a6d3b").pack(
            anchor="w", padx=5, pady=2)
        рекомендация = injector.evaluator.сформировать_рекомендацию(self.culture)
        tk.Label(rec, text=рекомендация, bg="#fff9e6", font=("Arial", 8), wraplength=240, justify="left").pack(padx=5,
                                                                                                               pady=5,
                                                                                                               anchor="w")

        right = tk.Frame(content, bg=BG_MAIN);
        right.pack(side="left", fill="both", expand=True)
        env_frame = tk.Frame(right, bg=BG_WHITE, bd=1, relief="solid");
        env_frame.pack(fill="x", pady=(0, 10))
        tk.Label(env_frame, text="Показатели окружающей среды", font=("Arial", 9, "bold"), bg=BG_WHITE,
                 anchor="w").pack(fill="x", padx=10, pady=10)
        env_table = CustomTable(env_frame, ["Показатель", "Значение", "Оценка"]);
        env_table.pack(fill="x", padx=10, pady=(0, 10))

        def get_badge(o): return ("#d4edda", "#155724") if o == ОценкаПоказателя.НОРМАЛЬНАЯ else (
            ("#fcf8e3", "#8a6d3b") if o in (ОценкаПоказателя.НИЗКАЯ, ОценкаПоказателя.ВЫСОКАЯ) else (
            "#f2dede", "#a94442"))

        b1, f1 = get_badge(self.culture.влажность_оценка);
        env_table.draw_row(["Влажность почвы", self.culture.влажность_почвы, ""], 2,
                           self.culture.влажность_оценка.value, b1, f1)
        b2, f2 = get_badge(self.culture.температура_оценка);
        env_table.draw_row(["Температура", self.culture.температура, ""], 2, self.culture.температура_оценка.value, b2,
                           f2)
        b3, f3 = get_badge(self.culture.освещенность_оценка);
        env_table.draw_row(["Освещённость", self.culture.освещенность, ""], 2, self.culture.освещенность_оценка.value,
                           b3, f3)

    def _info(self, parent, label, value):
        f = tk.Frame(parent, bg=BG_WHITE);
        f.pack(fill="x", padx=10, pady=3)
        tk.Label(f, text=label, width=15, anchor="w", bg=BG_WHITE, fg=COLOR_MUTED, font=("Arial", 9)).pack(side="left")
        tk.Label(f, text=value, anchor="w", bg=BG_WHITE, fg=COLOR_TEXT, font=("Arial", 9, "bold")).pack(side="left")

    def open_add(self): self.injector.создать_окно_наблюдения(self.culture.id,
                                                              self.user).показать(); self.root.destroy()

    def open_journal(self): self.injector.создать_окно_журнала(self.culture.id).показать()


class RegisterWindow(BaseWindow):
    def __init__(self, injector, user):
        super().__init__("Регистрация культуры", "650x550");
        self.injector = injector;
        self.user = user
        form = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid", padx=20, pady=20);
        form.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(form, text="Название", bg=BG_WHITE).grid(row=0, column=0, sticky="w");
        self.e_name = make_entry(form);
        self.e_name.grid(row=1, column=0, sticky="w", pady=(0, 10), ipady=3)
        tk.Label(form, text="Сорт", bg=BG_WHITE).grid(row=0, column=1, sticky="w", padx=20);
        self.e_sort = make_entry(form);
        self.e_sort.grid(row=1, column=1, sticky="w", padx=20, pady=(0, 10), ipady=3)
        tk.Label(form, text="Участок", bg=BG_WHITE).grid(row=2, column=0, sticky="w");
        self.cb_plot = ttk.Combobox(form, values=[p.название for p in injector.plot_repo.get_all()], state="readonly");
        self.cb_plot.grid(row=3, column=0, sticky="w", pady=(0, 10), ipady=3)
        tk.Label(form, text="Дата (ГГГГ-ММ-ДД)", bg=BG_WHITE).grid(row=2, column=1, sticky="w", padx=20);
        self.e_date = make_entry(form);
        self.e_date.insert(0, "2026-04-12");
        self.e_date.grid(row=3, column=1, sticky="w", padx=20, pady=(0, 10), ipady=3)
        bf = tk.Frame(form, bg=BG_WHITE);
        bf.grid(row=4, column=0, columnspan=2, pady=20)
        make_btn(bf, "Зарегистрировать", self.save).pack(side="left", padx=10);
        make_btn(bf, "Отмена", self.root.destroy).pack(side="left", padx=10)

    def save(self):
        try:
            plot = next(p for p in self.injector.plot_repo.get_all() if p.название == self.cb_plot.get().strip())
            d = datetime.strptime(self.e_date.get().strip(), "%Y-%m-%d").date()
            self.injector.culture_controller.зарегистрировать(self.user, self.e_name.get().strip(),
                                                              self.e_sort.get().strip(), plot.id, d)
            messagebox.showinfo("Успех", "Культура зарегистрирована");
            self.root.destroy()
        except StopIteration:
            messagebox.showerror("Ошибка", "Выберите участок")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class JournalWindow(BaseWindow):
    def __init__(self, cid, injector):
        super().__init__("Журнал наблюдений", "850x500");
        self.injector = injector
        top = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        top.pack(fill="x", padx=10, pady=10);
        make_btn(top, "← К карточке", self.root.destroy).pack(side="left", padx=5, pady=5)
        frame = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(frame, text="История", font=("Arial", 9, "bold"), bg=BG_WHITE, anchor="w").pack(fill="x", padx=10,
                                                                                                 pady=10)
        tree = CustomTable(frame, ["Дата", "Тип", "Автор", "Запись"]);
        tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        for o in injector.history_service.история(cid): tree.draw_row(
            [o.дата_время.strftime("%d.%m.%Y %H:%M"), o.тип.value, o.автор, o.запись], -1, "", "", "")


class AddObservationWindow(BaseWindow):
    def __init__(self, cid, user, injector):
        super().__init__("Новое наблюдение", "600x500");
        self.injector = injector;
        self.user = user
        self.culture = injector.culture_repo.get_by_id(cid)
        form = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid", padx=20, pady=20);
        form.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(form, text=f"{self.culture.название}, {self.culture.сорт}", font=("Arial", 10, "bold"),
                 bg=BG_WHITE).pack(anchor="w", pady=(0, 10))
        tk.Label(form, text="Тип записи", bg=BG_WHITE).pack(anchor="w")
        self.var_type = tk.StringVar(value=ТипНаблюдения.ВЫПОЛНЕННАЯ_РАБОТА.value)
        f = tk.Frame(form, bg=BG_WHITE);
        f.pack(anchor="w", pady=(5, 10))
        for t in [ТипНаблюдения.ВИЗУАЛЬНЫЙ_ОСМОТР, ТипНаблюдения.ВЫПОЛНЕННАЯ_РАБОТА, ТипНаблюдения.ЗАМЕТКА]:
            tk.Radiobutton(f, text=t.value, variable=self.var_type, value=t.value, bg=BG_WHITE).pack(side="left",
                                                                                                     padx=5)
        tk.Label(form, text="Описание", bg=BG_WHITE).pack(anchor="w")
        self.txt = tk.Text(form, height=5, bd=1, relief="solid");
        self.txt.pack(fill="x", pady=(5, 15))
        bf = tk.Frame(form, bg=BG_WHITE);
        bf.pack()
        make_btn(bf, "Сохранить", self.save).pack(side="left", padx=10);
        make_btn(bf, "Отмена", self.root.destroy).pack(side="left")

    def save(self):
        desc = self.txt.get("1.0", "end").strip()
        if not desc: return
        try:
            t = next(t for t in ТипНаблюдения if t.value == self.var_type.get())
            self.injector.observation_controller.добавить(self.user, self.culture, t, desc)
            messagebox.showinfo("Успех", "Сохранено");
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class NotificationWindow(BaseWindow):
    def __init__(self, injector, user):
        super().__init__("Оповещения", "750x500");
        self.injector = injector
        top = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        top.pack(fill="x", padx=10, pady=10)
        make_btn(top, "Прочитано", self.mark_all).pack(side="left", padx=5);
        make_btn(top, "Выход", self.root.destroy).pack(side="right", padx=5)
        frame = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tree = CustomTable(frame, ["Время", "Культура", "Сообщение", "Важность"]);
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for n in self.injector.notification_controller.все():
            c = self.injector.culture_repo.get_by_id(n.id_культуры);
            bg, fg = ("#f2dede", "#a94442") if n.важность == "Критическое" else ("#fcf8e3", "#8a6d3b")
            tree.draw_row([n.время.strftime("%d.%m %H:%M"), c.название if c else "", n.сообщение, ""], 3, n.важность,
                          bg, fg)

    def mark_all(self): self.injector.notification_controller.mark_all_read(); messagebox.showinfo("ОК", "Прочитано")


class ReportWindow(BaseWindow):
    def __init__(self, injector):
        super().__init__("Отчёт", "850x600")
        stats, cultures = injector.report_controller.сформировать(date(2026, 1, 1), date(2026, 12, 31))
        top = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        top.pack(fill="x", padx=10, pady=10)
        make_btn(top, "Выход", self.root.destroy).pack(side="right", padx=5)
        sf = tk.Frame(self.root, bg=BG_MAIN);
        sf.pack(fill="x", padx=10, pady=5)
        for n, l, c in [(str(stats['total']), "Всего", BG_WHITE), (str(stats['ok']), "Норма", "#dff0d8"),
                        (str(stats['warn']), "Внимание", "#fcf8e3"), (str(stats['crit']), "Критично", "#f2dede")]:
            f = tk.Frame(sf, bg=c, bd=1, relief="solid");
            f.pack(side="left", expand=True, fill="both", padx=5)
            tk.Label(f, text=n, font=("Arial", 20, "bold"), bg=c).pack(pady=(10, 0));
            tk.Label(f, text=l, bg=c).pack(pady=(0, 10))
        frame = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tree = CustomTable(frame, ["Участок", "Культура", "Фаза", "Состояние"]);
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for c in cultures:
            p = injector.plot_repo.get_by_id(c.id_участка);
            bg, fg = ("#d4edda", "#155724") if c.оценка == ОценкаСостояния.УДОВЛЕТВОРИТЕЛЬНОЕ else (
                ("#fcf8e3", "#8a6d3b") if c.оценка == ОценкаСостояния.ТРЕБУЕТ_ВНИМАНИЯ else ("#f2dede", "#a94442"))
            tree.draw_row([p.название if p else "", c.название, c.фаза_роста.value, ""], 3, c.оценка.value, bg, fg)


class AdminWindow(BaseWindow):
    def __init__(self, injector, tab=0):
        super().__init__("Администрирование", "800x550");
        self.injector = injector
        top = tk.Frame(self.root, bg=BG_WHITE, bd=1, relief="solid");
        top.pack(fill="x", padx=10, pady=10)
        make_btn(top, "Датчики", lambda: self.show_tab(0)).pack(side="left", padx=5);
        make_btn(top, "Пользователи", lambda: self.show_tab(1)).pack(side="left", padx=5);
        make_btn(top, "Выход", self.root.destroy).pack(side="right", padx=5)
        self.body = tk.Frame(self.root, bg=BG_MAIN);
        self.body.pack(fill="both", expand=True, padx=10, pady=10);
        self.show_tab(tab)

    def show_tab(self, tab):
        for w in self.body.winfo_children(): w.destroy()
        if tab == 0:
            f = tk.Frame(self.body, bg=BG_WHITE, bd=1, relief="solid");
            f.pack(fill="both", expand=True)
            tree = CustomTable(f, ["Код", "Тип", "Участок", "Показание"]);
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            for s in self.injector.admin_controller.датчики():
                plot = self.injector.plot_repo.get_by_id(s.id_участка)
                tree.draw_row([s.id, s.тип_датчика, plot.название if plot else "Не привязан", s.последнее_показание],
                              -1, "", "", "")
            bf = tk.Frame(f, bg=BG_WHITE);
            bf.pack(fill="x", padx=10, pady=5)
            tk.Label(bf, text="Участок:", bg=BG_WHITE).pack(side="left")
            cb = ttk.Combobox(bf, values=[p.название for p in self.injector.plot_repo.get_all()], state="readonly",
                              width=15);
            cb.pack(side="left", padx=5)
            tk.Label(bf, text="Тип:", bg=BG_WHITE).pack(side="left")
            cb_type = ttk.Combobox(bf, values=["Влажность почвы", "Температура", "Освещённость"], state="readonly",
                                   width=15);
            cb_type.pack(side="left", padx=5)
            make_btn(bf, "+ Подключить датчик", lambda: self.add_sensor(cb.get(), cb_type.get())).pack(side="left",
                                                                                                       padx=5)
        else:
            f = tk.Frame(self.body, bg=BG_WHITE, bd=1, relief="solid");
            f.pack(fill="both", expand=True)
            tree = CustomTable(f, ["ФИО", "Логин", "Роль", "Статус"]);
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            for u in self.injector.admin_controller.пользователи():
                bg, fg = ("#d4edda", "#155724") if u.статус == "Активен" else ("#f2dede", "#a94442")
                tree.draw_row([u.фио, u.логин, type(u).__name__, ""], 3, u.статус, bg, fg)

    def add_sensor(self, plot_name, sensor_type):
        if not plot_name or not sensor_type: return
        plot = next(p for p in self.injector.plot_repo.get_all() if p.название == plot_name)
        self.injector.admin_controller.создать_датчик(plot.id, sensor_type)
        messagebox.showinfo("Успех", f"Датчик подключен")
        self.show_tab(0)