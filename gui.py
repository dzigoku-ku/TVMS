"""Окно расчёта резерва станций радиорелейной линии."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from guide import open_guide
from model import HELP_TEXT, InputError, Interval, Problem, lecture_problem, solve, format_number
from report_view import FormulaLine, ReportView
from theme import ACCENT, ACCENT_ACTIVE, APP, CHIP, FIELD, INK, LINE, MUTED, WHITE

FONT = ("DejaVu Sans", 11)
FONT_TITLE = ("DejaVu Sans", 16, "bold")
FONT_HINT = ("DejaVu Sans", 10)
MAX_INTERVALS = 15


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Резервирование радиорелейной линии")
        self.geometry("1100x900")
        self.minsize(920, 700)
        self.configure(bg=APP)
        self.rows: list[_IntervalRow] = []

        self._style()
        self._menu()
        self._build()
        self._load_problem(lecture_problem())
        self.bind("<Return>", lambda _event: self.calculate())
        self.after(80, self.calculate)

    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=APP, foreground=INK, font=FONT)
        style.configure("TFrame", background=APP)
        style.configure("Card.TFrame", background=WHITE)
        style.configure("TLabel", background=WHITE, foreground=INK, font=FONT)
        style.configure("Title.TLabel", background=APP, foreground=INK, font=FONT_TITLE)
        style.configure("Hint.TLabel", background=WHITE, foreground=MUTED, font=FONT_HINT)
        style.configure("Summary.TLabel", background=WHITE, foreground=MUTED, font=FONT)
        style.configure(
            "TLabelframe",
            background=WHITE,
            bordercolor=LINE,
            lightcolor=WHITE,
            darkcolor=LINE,
            relief="solid",
            borderwidth=1,
        )
        style.configure("TLabelframe.Label", background=WHITE, foreground=ACCENT, font=FONT)
        style.configure(
            "TButton",
            background=WHITE,
            foreground=ACCENT,
            bordercolor=LINE,
            lightcolor=WHITE,
            darkcolor=LINE,
            font=FONT,
            padding=(12, 6),
            focuscolor=ACCENT,
        )
        style.map(
            "TButton",
            background=[("active", CHIP), ("pressed", CHIP)],
            foreground=[("disabled", MUTED)],
        )
        style.configure(
            "Field.TButton",
            background=WHITE,
            foreground=ACCENT,
            bordercolor=FIELD,
            lightcolor=FIELD,
            darkcolor=FIELD,
            borderwidth=2,
            relief="solid",
            font=FONT,
            padding=(12, 6),
            focuscolor=FIELD,
        )
        style.map(
            "Field.TButton",
            background=[("active", CHIP), ("pressed", CHIP)],
            foreground=[("disabled", MUTED), ("active", ACCENT), ("pressed", ACCENT)],
            bordercolor=[("focus", ACCENT), ("active", FIELD), ("pressed", FIELD)],
            lightcolor=[("focus", ACCENT), ("active", FIELD), ("pressed", FIELD)],
            darkcolor=[("focus", ACCENT), ("active", FIELD), ("pressed", FIELD)],
        )
        style.configure(
            "Primary.TButton",
            background=ACCENT,
            foreground=WHITE,
            bordercolor=ACCENT,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
            font=FONT,
            padding=(12, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", ACCENT_ACTIVE), ("pressed", ACCENT_ACTIVE)],
            foreground=[("active", WHITE), ("pressed", WHITE), ("disabled", WHITE)],
        )
        style.configure(
            "TEntry",
            fieldbackground=WHITE,
            foreground=INK,
            bordercolor=FIELD,
            lightcolor=FIELD,
            darkcolor=FIELD,
            borderwidth=2,
            relief="solid",
            padding=4,
            insertcolor=INK,
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", ACCENT)],
            lightcolor=[("focus", ACCENT)],
            darkcolor=[("focus", ACCENT)],
        )
        style.configure(
            "Flat.TSpinbox",
            fieldbackground=WHITE,
            background=WHITE,
            foreground=INK,
            bordercolor=WHITE,
            lightcolor=WHITE,
            darkcolor=WHITE,
            troughcolor=WHITE,
            arrowcolor=ACCENT,
            borderwidth=0,
            relief="flat",
            padding=(6, 3, 2, 3),
            insertcolor=INK,
            arrowsize=11,
        )
        style.configure(
            "TScrollbar",
            background=CHIP,
            troughcolor=APP,
            bordercolor=APP,
            arrowcolor=ACCENT,
            lightcolor=CHIP,
            darkcolor=LINE,
        )

    def _menu(self) -> None:
        menu = tk.Menu(self, bg=WHITE, fg=INK, activebackground=ACCENT, activeforeground=WHITE, bd=0)
        menu.add_command(label="Руководство пользователя", command=self.show_guide)
        help_menu = tk.Menu(menu, tearoff=0, bg=WHITE, fg=INK, activebackground=ACCENT, activeforeground=WHITE)
        help_menu.add_command(label="О модели", command=self.show_help)
        menu.add_cascade(label="Справка", menu=help_menu)
        self.configure(menu=menu)

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=(20, 16, 20, 16))
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(2, weight=1)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text="Резервирование радиорелейной линии", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        form = ttk.LabelFrame(outer, text="Исходные данные", padding=(14, 10, 14, 12))
        form.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        form.columnconfigure(0, weight=1)

        controls = ttk.Frame(form, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ew")
        ttk.Label(controls, text="Бюджет, тыс. руб.").pack(side="left")
        self.budget_var = tk.StringVar(value="1200")
        ttk.Entry(controls, textvariable=self.budget_var, width=10, font=FONT).pack(side="left", padx=(8, 18))
        ttk.Label(controls, text="Максимум резерва").pack(side="left")
        self.reserve_var = tk.StringVar(value="2")
        reserve_shell = tk.Frame(controls, bg=FIELD, padx=2, pady=2)
        reserve_shell.pack(side="left", padx=(8, 18))
        reserve_box = ttk.Spinbox(
            reserve_shell,
            from_=0,
            to=6,
            textvariable=self.reserve_var,
            width=4,
            font=FONT,
            style="Flat.TSpinbox",
        )
        reserve_box.pack()
        reserve_box.bind("<FocusIn>", lambda _event: reserve_shell.configure(bg=ACCENT), add="+")
        reserve_box.bind("<FocusOut>", lambda _event: reserve_shell.configure(bg=FIELD), add="+")
        ttk.Button(controls, text="Добавить интервал", command=self.add_interval, style="Field.TButton").pack(side="left")

        self.interval_box = ttk.Frame(form, style="Card.TFrame")
        self.interval_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for column, text in enumerate(("№", "Интервал", "Вероятность одной станции", "Стоимость одной станции, тыс. руб.")):
            ttk.Label(self.interval_box, text=text).grid(row=0, column=column, sticky="w", padx=(0, 8), pady=(0, 4))

        ttk.Label(
            form,
            text="На интервале одна рабочая станция и xᵢ резервных. "
            "Pᵢ(xᵢ) = 1 − (1 − pᵢ)¹⁺ˣⁱ, стоимость Cᵢ(xᵢ) = (1 + xᵢ) · cᵢ. "
            "Надёжность линии — произведение Pᵢ, сумма стоимостей не выше бюджета. "
            "Бюджет и цены станций вводятся целыми тысячами рублей.",
            style="Hint.TLabel",
            wraplength=1000,
            justify="left",
        ).grid(row=2, column=0, sticky="ew", pady=(10, 0))

        result = ttk.LabelFrame(outer, text="Решение", padding=(14, 10, 14, 12))
        result.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
        result.rowconfigure(1, weight=1)
        result.columnconfigure(0, weight=1)

        top = ttk.Frame(result, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.summary_box = tk.Frame(top, bg=WHITE)
        self.summary_box.pack(side="left", fill="x", expand=True)
        self._show_summary(None)
        ttk.Button(top, text="Рассчитать", command=self.calculate, style="Primary.TButton").pack(side="right", anchor="center")

        self.report = ReportView(result)
        self.report.grid(row=1, column=0, sticky="nsew")

    def add_interval(self) -> None:
        if len(self.rows) >= MAX_INTERVALS:
            messagebox.showerror(
                "Исходные данные",
                f"В этой версии линии не больше {MAX_INTERVALS} интервалов.",
                parent=self,
            )
            return
        number = len(self.rows) + 1
        self._append_row(f"Интервал {number}", "0,8", "100")

    def calculate(self) -> None:
        try:
            problem = self._read_problem()
            solution = solve(problem)
        except InputError as error:
            messagebox.showerror("Исходные данные", str(error), parent=self)
            return
        self._show_summary(solution)
        self.report.render(problem, solution)

    def _show_summary(self, solution) -> None:
        for child in self.summary_box.winfo_children():
            child.destroy()
        if solution is None:
            ttk.Label(self.summary_box, text="Нажмите «Рассчитать».", style="Summary.TLabel").pack(side="left", anchor="w")
            return
        reserves = ", ".join(str(step.reserve) for step in solution.plan)
        FormulaLine(
            self.summary_box,
            [
                ("t", "x"), ("sup", "опт"), ("t", f"  =  {{ {reserves} }}"),
                ("sp", 22),
                ("t", "P"), ("sub", "л"), ("t", f"  =  {format_number(solution.line_reliability)}"),
                ("sp", 22),
                ("t", "C"), ("sub", "∑"), ("t", f"  =  {solution.total_cost} из {solution.budget} тыс. руб."),
            ],
        ).pack(side="left", anchor="w")

    def show_guide(self) -> None:
        open_guide(self)

    def show_help(self) -> None:
        self._show_text("О модели", HELP_TEXT, "680x560")

    def _show_text(self, title: str, body: str, geometry: str) -> None:
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry(geometry)
        window.minsize(520, 360)
        window.configure(bg=WHITE)
        window.transient(self)
        frame = ttk.Frame(window, style="Card.TFrame", padding=(8, 8, 8, 8))
        frame.pack(fill="both", expand=True)
        text = tk.Text(
            frame,
            wrap="word",
            font=FONT,
            padx=14,
            pady=12,
            bg=WHITE,
            fg=INK,
            relief="flat",
            highlightthickness=0,
            insertbackground=INK,
        )
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        text.insert("1.0", body)
        text.configure(state="disabled")

    def _load_problem(self, problem: Problem) -> None:
        self.budget_var.set(str(problem.budget))
        self.reserve_var.set(str(problem.max_reserve))
        for row in self.rows:
            row.destroy()
        self.rows.clear()
        for interval in problem.intervals:
            self._append_row(
                interval.name,
                format(interval.single_reliability, "g").replace(".", ","),
                str(interval.station_cost),
            )

    def _append_row(self, name: str, probability: str, cost: str) -> None:
        row = _IntervalRow(self.interval_box, len(self.rows) + 1, self._remove_row)
        row.name_var.set(name)
        row.probability_var.set(probability)
        row.cost_var.set(cost)
        self.rows.append(row)

    def _remove_row(self, row: _IntervalRow) -> None:
        if len(self.rows) == 1:
            messagebox.showerror("Исходные данные", "На линии должен остаться хотя бы один интервал.", parent=self)
            return
        self.rows.remove(row)
        row.destroy()
        for index, item in enumerate(self.rows, start=1):
            item.place(index)

    def _read_problem(self) -> Problem:
        budget = _parse_int(self.budget_var.get(), "Бюджет")
        max_reserve = _parse_int(self.reserve_var.get(), "Максимум резерва")
        if not 0 <= max_reserve <= 6:
            raise InputError("Максимум резервных станций задаётся целым числом от 0 до 6.")
        intervals: list[Interval] = []
        for index, row in enumerate(self.rows, start=1):
            name = row.name_var.get().strip() or f"Интервал {index}"
            probability = _parse_probability(row.probability_var.get(), index)
            cost = _parse_int(row.cost_var.get(), f"Стоимость станции на интервале {index}")
            intervals.append(Interval(name, probability, cost))
        return Problem(tuple(intervals), budget, max_reserve)

class _IntervalRow:
    def __init__(self, parent: ttk.Frame, grid_row: int, on_remove) -> None:
        self.number_var = tk.StringVar(value=str(grid_row))
        self.name_var = tk.StringVar()
        self.probability_var = tk.StringVar()
        self.cost_var = tk.StringVar()
        self.widgets = (
            ttk.Label(parent, textvariable=self.number_var, width=4),
            ttk.Entry(parent, textvariable=self.name_var, width=22, font=FONT),
            ttk.Entry(parent, textvariable=self.probability_var, width=28, font=FONT),
            ttk.Entry(parent, textvariable=self.cost_var, width=32, font=FONT),
            ttk.Button(parent, text="Удалить", command=lambda: on_remove(self)),
        )
        self.place(grid_row)

    def place(self, grid_row: int) -> None:
        self.number_var.set(str(grid_row))
        for column, widget in enumerate(self.widgets):
            widget.grid(row=grid_row, column=column, sticky="w", padx=(0, 8), pady=2)

    def destroy(self) -> None:
        for widget in self.widgets:
            widget.destroy()


def _parse_int(text: str, label: str) -> int:
    value = _parse_float(text, label)
    if abs(value - round(value)) > 1e-9:
        raise InputError(f"{label} задаётся целым числом тысяч рублей.")
    return int(round(value))


def _parse_probability(text: str, index: int) -> float:
    value = _parse_float(text, f"Вероятность на интервале {index}")
    if not 0.0 < value <= 1.0:
        raise InputError(f"Вероятность на интервале {index} должна быть больше 0 и не больше 1.")
    return value


def _parse_float(text: str, label: str) -> float:
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    if not cleaned:
        raise InputError(f"Поле «{label}» пустое.")
    try:
        return float(cleaned)
    except ValueError as error:
        raise InputError(f"Поле «{label}» должно быть числом.") from error


def main() -> None:
    app = App()
    app.mainloop()
