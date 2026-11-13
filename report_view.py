"""Лист решения в вёрстке примера 2 лекции.

Формулы набраны с верхними и нижними индексами, таблицы повторяют
шапку лекции: состояние, варианты с вероятностью и стоимостью,
условный или безусловный оптимум.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from model import Problem, Solution, StageResult, _rows_for_report, format_number
from theme import ACCENT, INK, MUTED, RULE, WHITE

PAPER = WHITE

FONT_TEXT = ("DejaVu Serif", 12)
FONT_HEAD = ("DejaVu Serif", 13, "bold")
FONT_CAPTION = ("DejaVu Serif", 12, "bold")
FONT_CAPTION_PLAIN = ("DejaVu Serif", 12)
FONT_TABLE = ("DejaVu Serif", 11)

_DIGITS = "₀₁₂₃₄₅₆₇₈₉"


def sub_digits(number: int) -> str:
    return "".join(_DIGITS[int(char)] for char in str(number))


def format_source(value: float) -> str:
    """Два знака после запятой, если хватает, иначе до четырёх, как в таблице 1 лекции."""

    text = f"{round(float(value), 4):.4f}"
    whole, frac = text.split(".")
    frac = frac.rstrip("0")
    if len(frac) < 2:
        frac = frac.ljust(2, "0")
    return f"{whole},{frac}"


class FormulaLine(tk.Canvas):
    """Одна выключенная формула: обычный текст, индексы и знак с пределами."""

    def __init__(self, parent: tk.Widget, tokens: list[tuple]) -> None:
        super().__init__(parent, bg=PAPER, highlightthickness=0, bd=0, height=96)
        base = tkfont.Font(family="DejaVu Serif", size=16)
        small = tkfont.Font(family="DejaVu Serif", size=11)
        symbol = tkfont.Font(family="DejaVu Serif", size=20)
        baseline = 46
        x = 8
        small_space = small.metrics("linespace")
        symbol_space = symbol.metrics("linespace")

        for token in tokens:
            kind = token[0]
            if kind == "t":
                self.create_text(x, baseline, text=token[1], anchor="w", font=base, fill=INK)
                x += base.measure(token[1])
            elif kind == "sub":
                self.create_text(x, baseline + 8, text=token[1], anchor="w", font=small, fill=INK)
                x += small.measure(token[1])
            elif kind == "sup":
                self.create_text(x, baseline - 10, text=token[1], anchor="w", font=small, fill=INK)
                x += small.measure(token[1])
            elif kind == "ss":
                sub_text, sup_text = token[1], token[2]
                self.create_text(x, baseline + 8, text=sub_text, anchor="w", font=small, fill=INK)
                self.create_text(x, baseline - 10, text=sup_text, anchor="w", font=small, fill=INK)
                x += max(small.measure(sub_text), small.measure(sup_text))
            elif kind == "stack":
                sign, over, under = token[1], token[2], token[3]
                under_lines = under.split("\n") if under else []
                width = symbol.measure(sign)
                if over:
                    width = max(width, small.measure(over))
                for line in under_lines:
                    width = max(width, small.measure(line))
                width += 10
                center = x + width / 2
                self.create_text(center, baseline, text=sign, font=symbol, fill=INK)
                if over:
                    self.create_text(
                        center,
                        baseline - symbol_space / 2 - 1,
                        text=over,
                        anchor="s",
                        font=small,
                        fill=INK,
                    )
                for index, line in enumerate(under_lines):
                    self.create_text(
                        center,
                        baseline + symbol_space / 2 + 2 + index * small_space,
                        text=line,
                        anchor="n",
                        font=small,
                        fill=INK,
                    )
                x += width
            elif kind == "sp":
                x += token[1]

        box = self.bbox("all")
        if box is None:
            self.configure(width=4, height=4)
            return
        pad = 4
        self.move("all", pad - box[0], pad - box[1])
        box = self.bbox("all")
        self.configure(width=box[2] + pad, height=box[3] + pad)


class _Table(tk.Frame):
    """Сетка с одинарной чёрной линией, как в таблицах лекции."""

    def __init__(self, parent: tk.Widget, rows: int, cols: int, cells: list[dict]) -> None:
        super().__init__(parent, bg=RULE, padx=1, pady=1)
        covered = [[False for _ in range(cols)] for _ in range(rows)]
        for cell in cells:
            row, col = cell["row"], cell["col"]
            row_span = cell.get("rowspan", 1)
            col_span = cell.get("colspan", 1)
            for r in range(row, row + row_span):
                for c in range(col, col + col_span):
                    if covered[r][c]:
                        raise RuntimeError(f"ячейка таблицы перекрыта: {r}, {c}")
                    covered[r][c] = True
        if not all(all(line) for line in covered):
            raise RuntimeError("в таблице осталась пустая клетка")

        measure = tkfont.Font(family="DejaVu Serif", size=11)
        widths = [72 for _ in range(cols)]
        for cell in cells:
            if cell.get("colspan", 1) != 1:
                continue
            text = cell["text"]
            width = max(measure.measure(line) for line in text.split("\n")) + 22
            widths[cell["col"]] = max(widths[cell["col"]], width)
        for col, width in enumerate(widths):
            self.columnconfigure(col, minsize=width)

        for cell in cells:
            row, col = cell["row"], cell["col"]
            row_span = cell.get("rowspan", 1)
            col_span = cell.get("colspan", 1)
            last_row = row + row_span == rows
            last_col = col + col_span == cols
            label = tk.Label(
                self,
                text=cell["text"],
                font=FONT_TABLE,
                bg=PAPER,
                fg=INK,
                justify="center",
                anchor="center",
                padx=8,
                pady=4,
                wraplength=cell.get("wrap", 0),
                highlightthickness=0,
                bd=0,
            )
            label.grid(
                row=row,
                column=col,
                rowspan=row_span,
                columnspan=col_span,
                sticky="nsew",
                padx=(0, 0 if last_col else 1),
                pady=(0, 0 if last_row else 1),
            )


class ReportView(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=PAPER)
        self._wrap = 760
        self._wrapping: list[tk.Label] = []

        self.canvas = tk.Canvas(self, bg=PAPER, highlightthickness=0, bd=0)
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._overflow = False

        self.inner = tk.Frame(self.canvas, bg=PAPER)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

    def render(self, problem: Problem, solution: Solution) -> None:
        for child in self.inner.winfo_children():
            child.destroy()
        self._wrapping.clear()

        self._open(problem, solution)
        self._reliability_formulas()
        self._source_table(problem, solution)
        self._objective(solution)
        self._bellman()
        kept = {step.resource_before for step in solution.plan}
        for stage in solution.stages:
            self._stage(problem, solution, stage, kept)
        self._restoration(solution)
        self._strategy(solution)
        tk.Frame(self.inner, bg=PAPER, height=8).pack()

        self._bind_tree(self.inner)
        self.update_idletasks()
        self._sync()
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def _open(self, problem: Problem, solution: Solution) -> None:
        count = len(problem.intervals)
        reserve = "0" if problem.max_reserve == 0 else f"0, 1, …, {problem.max_reserve}"
        self._paragraph(
            f"Линия из {count} интервалов. На каждом одна рабочая станция и xᵢ резервных, "
            f"xᵢ = {reserve}. Бюджет {solution.budget} тыс. руб., шаг ресурса в таблицах "
            f"{solution.money_step} тыс. руб.",
            space_before=2,
        )
        self._paragraph(
            "Отказы интервалов независимы, поэтому вероятность безотказной работы линии "
            "равна произведению вероятностей интервалов.",
            space_before=4,
        )
        self._formula([
            ("t", "P"), ("sub", "л"), ("t", " = "),
            ("stack", "∏", "n", "i = 1"),
            ("t", " P"), ("sub", "i"),
        ])

    def _reliability_formulas(self) -> None:
        self._paragraph(
            "Для интервала i вероятность отказа одной станции qᵢ = 1 − pᵢ. "
            "При xᵢ резервных станциях интервал отказывает, только если отказали все 1 + xᵢ станций:",
            space_before=8,
        )
        self._formula([
            ("t", "P"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
            ("t", ") = 1 − q"), ("ss", "i", "1+xᵢ"),
            ("t", " = 1 − (1 − p"), ("sub", "i"), ("t", ")"), ("sup", "1+xᵢ"),
        ])
        self._paragraph("Стоимость интервала включает рабочую станцию и резерв:", space_before=6)
        self._formula([
            ("t", "C"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
            ("t", ") = (1 + x"), ("sub", "i"), ("t", ") · c"), ("sub", "i"),
        ])

    def _source_table(self, problem: Problem, solution: Solution) -> None:
        by_index = {stage.interval_index: stage for stage in solution.stages}
        intervals = problem.intervals
        count = len(intervals)
        rows = 2 + problem.max_reserve + 1
        cols = 1 + 2 * count
        cells: list[dict] = [
            {"row": 0, "col": 0, "rowspan": 2, "text": "xᵢ"},
        ]
        for reserve in range(problem.max_reserve + 1):
            cells.append({"row": 2 + reserve, "col": 0, "text": str(reserve)})
        for index in range(count):
            number = sub_digits(index + 1)
            cells.append({"row": 0, "col": 1 + 2 * index, "colspan": 2, "text": f"i = {index + 1}"})
            cells.append({"row": 1, "col": 1 + 2 * index, "text": f"p{number}(xᵢ)"})
            cells.append({"row": 1, "col": 2 + 2 * index, "text": f"C{number}(xᵢ)"})
            for variant in by_index[index].variants:
                cells.append({
                    "row": 2 + variant.reserve,
                    "col": 1 + 2 * index,
                    "text": format_source(variant.reliability),
                })
                cells.append({
                    "row": 2 + variant.reserve,
                    "col": 2 + 2 * index,
                    "text": str(variant.cost),
                })

        self._paragraph(
            "Исходные вероятности и стоимости. Вероятность в строке посчитана по формуле интервала, "
            "стоимость — по числу станций.",
            space_before=10,
        )
        self._block("Исходные данные", "Таблица № 1", rows, cols, cells)

    def _objective(self, solution: Solution) -> None:
        self._paragraph("Нужно выбрать целые xᵢ с наибольшей надёжностью линии:", space_before=10)
        self._formula([
            ("t", "P"), ("sub", "л"), ("t", "(x"), ("sup", "опт"), ("t", ") = "),
            ("stack", "∏", "n", "i = 1"),
            ("sp", 4),
            ("t", "[ 1 − (1 − p"), ("sub", "i"), ("t", ")"), ("sup", "1+xᵢ"),
            ("t", " ]  →  max"),
        ])
        self._paragraph("при ограничении на суммарную стоимость станций:", space_before=4)
        self._formula([
            ("stack", "∑", "n", "i = 1"),
            ("sp", 2),
            ("t", "C"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
            ("t", ")  ≤  C"), ("sub", "∑"),
            ("t", f"  =  {solution.budget} тыс. руб."),
        ])

    def _bellman(self) -> None:
        self._paragraph(
            "Решение строится обратной прогонкой. Номер шага идёт от последнего интервала к первому. "
            "Состояние sᵢ — стоимость оборудования на i-м интервале и на всех следующих.",
            space_before=10,
        )
        self._paragraph("На последнем интервале:", space_before=6)
        self._formula([
            ("t", "F"), ("sub", "n"), ("t", "(s"), ("sub", "n"), ("t", ") = "),
            ("stack", "max", "", "xₙ"),
            ("t", "  { p"), ("sub", "n"), ("t", "(x"), ("sub", "n"), ("t", ") }"),
        ])
        self._formula([
            ("t", "при   c"), ("sub", "n"), ("t", "(x"), ("sub", "n"),
            ("t", ") ≤ s"), ("sub", "n"),
        ])
        self._paragraph("На предыдущем интервале значение варианта умножается на уже посчитанный оптимум хвоста:", space_before=6)
        self._formula([
            ("t", "F"), ("sub", "i"), ("t", "(s"), ("sub", "i"), ("t", ") = "),
            ("stack", "max", "", "xᵢ"),
            ("t", "  { p"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
            ("t", ") · F"), ("sub", "i+1"),
            ("t", "(s"), ("sub", "i"), ("t", " − c"), ("sub", "i"),
            ("t", "(x"), ("sub", "i"), ("t", ")) }"),
        ])
        self._formula([
            ("t", "при   c"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
            ("t", ") ≤ s"), ("sub", "i"),
        ])
        self._paragraph("Состояние на шаге связано с бюджетом и уже выбранными затратами:", space_before=6)
        self._formula([
            ("t", "s"), ("sub", "i"), ("t", " = C"), ("sub", "∑"), ("t", " − "),
            ("stack", "∑", "i − 1", "k = 1"),
            ("sp", 2),
            ("t", "c"), ("sub", "k"), ("t", "(x"), ("sub", "k"), ("t", ")"),
        ])
        self._paragraph(
            "Прочерк в клетке означает, что стоимость варианта выше текущего состояния "
            "или остатка не хватает на станции хвоста. Если два варианта дают одно значение, "
            "оставляется меньший резерв.",
            space_before=6,
        )

    def _stage(self, problem: Problem, solution: Solution, stage: StageResult, kept: set[int]) -> None:
        number = stage.interval_index + 1
        index = sub_digits(number)
        shown, truncated = _rows_for_report(stage.rows, kept)
        if stage.final_step:
            bounds = (
                f"{stage.interval_name}. Состояние одно: s{index} = C∑ = {problem.budget} тыс. руб. "
                "Это безусловная оптимизация: в клетках произведение вероятности интервала "
                "на оптимум оставшейся линии."
            )
            decision = "Безусловное\nоптимальное решение"
        else:
            if stage.interval_index == len(problem.intervals) - 1:
                tail = "Последний интервал линии, хвоста нет: в клетке стоит сама вероятность."
            else:
                tail = "В клетке — вероятность интервала, умноженная на оптимум хвоста."
            bounds = (
                f"{stage.interval_name}. {tail} "
                f"Состояние s{index} меняется от {stage.resource_min} до {stage.resource_max} тыс. руб. "
                f"с шагом {solution.money_step}."
            )
            decision = "Условное\nоптимальное решение"
        self._paragraph(bounds, space_before=12)

        variants = stage.variants
        rows = 3 + len(shown)
        cols = 1 + len(variants) + 2
        state = f"S{index} = C∑" if stage.final_step else f"S{index}"
        if stage.interval_index == len(problem.intervals) - 1:
            title = f"P{index}(X{index})"
        else:
            nxt = sub_digits(number + 1)
            title = f"P{index}(X{index}) = p{index}(x{index}) · F{nxt}(s{index} − c{index}(x{index}))"
        cells: list[dict] = [
            {"row": 0, "col": 0, "rowspan": 3, "text": state},
            {"row": 0, "col": 1, "colspan": len(variants), "text": title, "wrap": max(220, 150 * len(variants))},
            {"row": 0, "col": 1 + len(variants), "colspan": 2, "text": decision},
            {"row": 1, "col": 1 + len(variants), "rowspan": 2, "text": f"F{index}(s{index})"},
            {"row": 1, "col": 2 + len(variants), "rowspan": 2, "text": f"X{index}\nопт"},
        ]
        for offset, variant in enumerate(variants):
            cells.append({"row": 1, "col": 1 + offset, "text": f"X{index} = {variant.reserve}"})
            cells.append({
                "row": 2,
                "col": 1 + offset,
                "text": f"P = {format_number(variant.reliability)}\nC{index} = {variant.cost}",
            })
        for row_index, row in enumerate(shown):
            values = [str(row.resource)]
            values.extend("–" if value is None else format_number(value) for value in row.values)
            values.append(format_number(row.best_value))
            values.append(str(row.best_reserve))
            for col, text in enumerate(values):
                cells.append({"row": 3 + row_index, "col": col, "text": text})

        table_number = stage.step_number + 1
        self._block(f"Шаг № {stage.step_number}", f"Таблица № {table_number}", rows, cols, cells)
        if truncated:
            self._paragraph(
                f"Показаны {len(shown)} из {len(stage.rows)} состояний, включая состояния оптимального плана.",
                space_before=4,
            )

    def _restoration(self, solution: Solution) -> None:
        self._paragraph("Восстановление безусловного плана идёт от первого интервала к последнему.", space_before=14)
        plan = solution.plan
        for position, step in enumerate(plan):
            number = step.interval_index + 1
            index = sub_digits(number)
            if position == 0:
                text = (
                    f"При s{index} = {step.resource_before} тыс. руб. из таблицы первого интервала "
                    f"x{index} опт = {step.reserve}. Вероятность интервала {format_number(step.reliability)}, "
                    f"стоимость {step.cost} тыс. руб. Остаток s = {step.resource_before} − {step.cost} = {step.resource_after} тыс. руб."
                )
            else:
                text = (
                    f"При s{index} = {step.resource_before} тыс. руб. из таблицы интервала {number} "
                    f"x{index} опт = {step.reserve}. Вероятность {format_number(step.reliability)}, "
                    f"стоимость {step.cost} тыс. руб. Остаток {step.resource_after} тыс. руб."
                )
            self._paragraph(text, space_before=4)

    def _strategy(self, solution: Solution) -> None:
        reserves = ", ".join(str(step.reserve) for step in solution.plan)
        factors = " · ".join(format_number(step.reliability) for step in solution.plan)
        costs = " + ".join(str(step.cost) for step in solution.plan)
        self._paragraph("Оптимальная стратегия распределения резерва:", space_before=12)
        self._formula([
            ("t", "x"), ("sup", "опт"), ("t", f"  =  {{ {reserves} }}"),
        ])
        self._formula([
            ("t", "P"), ("sub", "л"),
            ("t", f"  =  {factors}  =  {format_number(solution.line_reliability)}"),
        ])
        self._formula([
            ("t", "C"), ("sub", "∑"),
            ("t", f"  =  {costs}  =  {solution.total_cost} тыс. руб."),
        ])
        details = "; ".join(
            f"p{sub_digits(step.interval_index + 1)}(x{sub_digits(step.interval_index + 1)} = {step.reserve}) "
            f"= {format_number(step.reliability)}, C{sub_digits(step.interval_index + 1)} = {step.cost}"
            for step in solution.plan
        )
        self._paragraph(f"По интервалам: {details}.", space_before=6)
        rest = solution.budget - solution.total_cost
        if rest:
            self._paragraph(f"Неиспользованный остаток бюджета: {rest} тыс. руб.", space_before=4)
        else:
            self._paragraph("Бюджет выбран полностью, неиспользованный остаток 0 тыс. руб.", space_before=4)

    def _formula(self, tokens: list[tuple]) -> None:
        holder = tk.Frame(self.inner, bg=PAPER)
        FormulaLine(holder, tokens).pack(anchor="center")
        holder.pack(fill="x", pady=(2, 2))

    def _paragraph(self, text: str, space_before: int = 8) -> None:
        label = tk.Label(
            self.inner,
            text=text,
            font=FONT_TEXT,
            bg=PAPER,
            fg=INK,
            justify="left",
            anchor="w",
            wraplength=self._wrap,
            highlightthickness=0,
            bd=0,
        )
        label.pack(fill="x", pady=(space_before, 2))
        self._wrapping.append(label)

    def _block(self, left: str, right: str, rows: int, cols: int, cells: list[dict]) -> None:
        block = tk.Frame(self.inner, bg=PAPER)
        bar = tk.Frame(block, bg=PAPER)
        tk.Label(bar, text=left, font=FONT_CAPTION, bg=PAPER, fg=ACCENT, highlightthickness=0, bd=0).pack(side="left")
        tk.Label(bar, text=right, font=FONT_CAPTION_PLAIN, bg=PAPER, fg=MUTED, highlightthickness=0, bd=0).pack(side="right")
        bar.pack(fill="x", pady=(0, 3))
        _Table(block, rows, cols, cells).pack()
        block.pack(pady=(4, 8))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        wrap = max(520, int(event.width) - 36)
        if wrap != self._wrap:
            self._wrap = wrap
            for label in self._wrapping:
                if label.winfo_exists():
                    label.configure(wraplength=wrap)
        self._sync()

    def _sync(self) -> None:
        self.inner.update_idletasks()
        content_width = 0
        for child in self.inner.winfo_children():
            child.update_idletasks()
            content_width = max(content_width, child.winfo_reqwidth())
        content_width += 8
        view_width = max(self.canvas.winfo_width(), 1)
        width = max(view_width, content_width, self.inner.winfo_reqwidth())
        height = max(self.inner.winfo_reqheight(), 1)
        self.canvas.itemconfigure(self._window, width=width)
        self.canvas.configure(scrollregion=(0, 0, width, height))
        overflow = content_width > view_width + 12
        if overflow != self._overflow:
            self._overflow = overflow
            if overflow:
                self.scroll_x.grid(row=1, column=0, sticky="ew")
            else:
                self.scroll_x.grid_remove()
                self.canvas.xview_moveto(0)

    def _on_wheel(self, event: tk.Event) -> str:
        step = -3 if getattr(event, "num", None) == 4 or event.delta > 0 else 3
        if event.state & 0x0001:
            self.canvas.xview_scroll(step, "units")
        else:
            self.canvas.yview_scroll(step, "units")
        return "break"

    def _bind_tree(self, widget: tk.Widget) -> None:
        widget.bind("<Button-4>", self._on_wheel)
        widget.bind("<Button-5>", self._on_wheel)
        widget.bind("<MouseWheel>", self._on_wheel)
        for child in widget.winfo_children():
            self._bind_tree(child)
