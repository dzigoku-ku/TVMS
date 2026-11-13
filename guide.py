"""Окно руководства пользователя."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from report_view import FormulaLine
from theme import ACCENT, CHIP, INK, LINE, MUTED, NOTE, WHITE

FONT = ("DejaVu Sans", 11)
FONT_TITLE = ("DejaVu Sans", 15, "bold")
FONT_TOPIC = ("DejaVu Sans", 18, "bold")
FONT_NAV = ("DejaVu Sans", 11)
FONT_SMALL = ("DejaVu Sans", 10)
FONT_FIELD = ("DejaVu Sans", 12, "bold")

Block = tuple


def open_guide(master: tk.Misc) -> None:
    GuideWindow(master)


class GuideWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Руководство пользователя")
        self.geometry("980x680")
        self.minsize(760, 520)
        self.configure(bg=WHITE)
        self.transient(master)

        self._nav_rows: list[tuple[tk.Frame, tk.Label]] = []
        self._labels: list[tk.Label] = []
        self._current = 0

        header = tk.Frame(self, bg=WHITE)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Руководство",
            font=FONT_TITLE,
            fg=INK,
            bg=WHITE,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 0))
        tk.Label(
            header,
            text="Резерв станций при наибольшей надёжности линии и заданном бюджете. Деньги — в тысячах рублей.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=WHITE,
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=18, pady=(4, 12))
        self._header_wrap = header.winfo_children()[-1]
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        body = tk.Frame(self, bg=WHITE)
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=WHITE, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self._nav = tk.Frame(side, bg=WHITE)
        self._nav.pack(fill="both", expand=True, pady=10)
        tk.Frame(body, bg=LINE, width=1).pack(side="left", fill="y")

        self._stage = tk.Frame(body, bg=WHITE)
        self._stage.pack(side="left", fill="both", expand=True)

        for index, (title, _blocks) in enumerate(_TOPICS):
            self._nav_item(index, title)
        self._select(0)
        self.bind("<Configure>", self._fit_header)

    def _nav_item(self, index: int, title: str) -> None:
        row = tk.Frame(self._nav, bg=WHITE, cursor="hand2")
        row.pack(fill="x", padx=10, pady=1)
        label = tk.Label(
            row,
            text=title,
            font=FONT_NAV,
            fg=INK,
            bg=WHITE,
            anchor="w",
            padx=12,
            pady=7,
            cursor="hand2",
        )
        label.pack(fill="x")
        for widget in (row, label):
            widget.bind("<Button-1>", lambda _event, item=index: self._select(item))
        self._nav_rows.append((row, label))

    def _select(self, index: int) -> None:
        self._current = index
        for item, (row, label) in enumerate(self._nav_rows):
            color = ACCENT if item == index else WHITE
            ink = WHITE if item == index else INK
            row.configure(bg=color)
            label.configure(bg=color, fg=ink)
        for child in self._stage.winfo_children():
            child.destroy()
        self._labels.clear()
        self._show_topic(_TOPICS[index][0], _TOPICS[index][1])

    def _show_topic(self, title: str, blocks: list[Block]) -> None:
        canvas = tk.Canvas(self._stage, bg=WHITE, highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(self._stage, command=canvas.yview)
        scroll_x = ttk.Scrollbar(self._stage, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scroll.set, xscrollcommand=scroll_x.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        holder = tk.Frame(canvas, bg=WHITE)
        window_id = canvas.create_window((0, 0), window=holder, anchor="nw")
        holder.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))

        pad = tk.Frame(holder, bg=WHITE)
        pad.pack(fill="both", expand=True, padx=22, pady=18)
        heading = tk.Label(pad, text=title, font=FONT_TOPIC, fg=ACCENT, bg=WHITE, anchor="w")
        heading.pack(anchor="w", pady=(0, 8))
        self._labels.append(heading)

        for kind, payload in blocks:
            if kind == "p":
                self._paragraph(pad, payload)
            elif kind == "formula":
                self._formula(pad, payload)
            elif kind == "note":
                self._note(pad, payload)
            elif kind == "bullets":
                self._bullets(pad, payload)
            elif kind == "fields":
                self._fields(pad, payload)

        def fit(event: tk.Event) -> None:
            holder.update_idletasks()
            needed = max(holder.winfo_reqwidth(), 1)
            width = max(event.width, needed)
            canvas.itemconfigure(window_id, width=width)
            inner = max(240, event.width - 56)
            for label in self._labels:
                label.configure(wraplength=inner)
            canvas.configure(scrollregion=canvas.bbox("all") or (0, 0, width, 1))
            if needed > event.width + 8:
                scroll_x.pack(side="bottom", fill="x", before=canvas)
            else:
                scroll_x.pack_forget()
                canvas.xview_moveto(0)

        canvas.bind("<Configure>", fit)
        self._bind_wheel(canvas, holder)

    def _paragraph(self, parent: tk.Frame, text: str) -> None:
        label = tk.Label(
            parent,
            text=text,
            font=FONT,
            fg=INK,
            bg=WHITE,
            justify="left",
            anchor="w",
            wraplength=480,
        )
        label.pack(anchor="w", pady=(8, 0))
        self._labels.append(label)

    def _formula(self, parent: tk.Frame, tokens: list[tuple]) -> None:
        holder = tk.Frame(parent, bg=WHITE)
        holder.pack(fill="x", pady=(8, 2))
        FormulaLine(holder, tokens).pack(anchor="center")

    def _note(self, parent: tk.Frame, text: str) -> None:
        box = tk.Frame(parent, bg=NOTE)
        box.pack(fill="x", pady=(10, 0))
        tk.Frame(box, bg=ACCENT, width=4).pack(side="left", fill="y")
        label = tk.Label(
            box,
            text=text,
            font=FONT,
            fg=INK,
            bg=NOTE,
            justify="left",
            anchor="w",
            wraplength=460,
            padx=12,
            pady=10,
        )
        label.pack(side="left", fill="x", expand=True)
        self._labels.append(label)

    def _bullets(self, parent: tk.Frame, items: list[str]) -> None:
        for item in items:
            row = tk.Frame(parent, bg=WHITE)
            row.pack(fill="x", pady=(6, 0))
            tk.Label(row, text="●", font=("DejaVu Sans", 8), fg=ACCENT, bg=WHITE).pack(side="left", anchor="n", padx=(2, 8), pady=4)
            label = tk.Label(
                row,
                text=item,
                font=FONT,
                fg=INK,
                bg=WHITE,
                justify="left",
                anchor="w",
                wraplength=440,
            )
            label.pack(side="left", fill="x", expand=True)
            self._labels.append(label)

    def _fields(self, parent: tk.Frame, rows: list[tuple[str, str, str, str]]) -> None:
        for name, unit, what, source in rows:
            card = tk.Frame(parent, bg=WHITE, highlightbackground=LINE, highlightthickness=1)
            card.pack(fill="x", pady=(8, 0))
            top = tk.Frame(card, bg=WHITE)
            top.pack(fill="x", padx=12, pady=(10, 0))
            tk.Label(top, text=name, font=FONT_FIELD, fg=INK, bg=WHITE).pack(side="left")
            tk.Label(top, text=unit, font=FONT_SMALL, fg=ACCENT, bg=CHIP, padx=8, pady=2).pack(side="left", padx=(10, 0))
            what_label = tk.Label(
                card,
                text=what,
                font=FONT,
                fg=INK,
                bg=WHITE,
                anchor="w",
                justify="left",
                wraplength=440,
            )
            what_label.pack(fill="x", padx=12, pady=(6, 0))
            source_label = tk.Label(
                card,
                text=source,
                font=FONT_SMALL,
                fg=MUTED,
                bg=WHITE,
                anchor="w",
                justify="left",
                wraplength=440,
            )
            source_label.pack(fill="x", padx=12, pady=(2, 10))
            self._labels.extend((what_label, source_label))

    def _bind_wheel(self, canvas: tk.Canvas, holder: tk.Frame) -> None:
        def up(_event: tk.Event) -> None:
            canvas.yview_scroll(-3, "units")

        def down(_event: tk.Event) -> None:
            canvas.yview_scroll(3, "units")

        def walk(widget: tk.Widget) -> None:
            widget.bind("<Button-4>", up, add="+")
            widget.bind("<Button-5>", down, add="+")
            for child in widget.winfo_children():
                walk(child)

        walk(canvas)
        walk(holder)

    def _fit_header(self, event: tk.Event) -> None:
        if event.widget is self:
            self._header_wrap.configure(wraplength=max(280, event.width - 40))


_TOPICS: list[tuple[str, list[Block]]] = [
    (
        "Окно",
        [
            (
                "p",
                "Сверху задаётся линия: бюджет, потолок резерва и строки интервалов. "
                "Снизу после расчёта появляется план.",
            ),
            (
                "bullets",
                [
                    "«Рассчитать» и клавиша Enter строят план заново.",
                    "«Добавить интервал» добавляет пролёт, «Удалить» убирает строку.",
                    "Краткие формулы открываются в меню «Справка» → «О модели».",
                ],
            ),
            (
                "note",
                "Программа ищет наибольшую вероятность безотказной работы линии при лимите на рабочие и резервные станции. "
                "Деньги во всех полях — целые тысячи рублей.",
            ),
        ],
    ),
    (
        "Поля",
        [
            (
                "p",
                "На план влияют бюджет, максимум резерва, вероятность одной станции и её стоимость. "
                "Название интервала остаётся подписью в таблицах.",
            ),
            (
                "fields",
                [
                    ("Бюджет", "тыс. руб.", "Целое положительное число", "Лимит денег на всю линию"),
                    ("Максимум резерва", "станции", "Целое число от 0 до 6", "Потолок запасных станций на одном интервале"),
                    ("Интервал", "подпись", "Название пролёта", "Схема линии"),
                    ("Вероятность", "доля 0…1", "Например 0,7", "Надёжность станции без резерва"),
                    ("Стоимость станции", "тыс. руб.", "Цена станции интервала", "Условие задачи или цена комплекта"),
                ],
            ),
            (
                "note",
                "Число 100 в денежном поле означает 100 тысяч рублей, то есть 100 000 руб. "
                "Во всех денежных полях одна и та же единица: программа сравнивает числа как есть.",
            ),
        ],
    ),
    (
        "Бюджет",
        [
            (
                "p",
                "Бюджет — предельная сумма на все станции линии, и на рабочие, и на резервные. "
                "Число задаётся целыми тысячами рублей. Дробная запись, например 500,5, не принимается.",
            ),
            (
                "p",
                "Если цены известны в рублях, их делят на 1000, округляют до целых тысяч и в бюджет переносят уже эту сумму.",
            ),
            (
                "p",
                "При нуле резервных станций интервал всё равно имеет стоимость. Она равна цене одной рабочей станции.",
            ),
        ],
    ),
    (
        "Резерв",
        [
            (
                "p",
                "Максимум резерва — наибольшее целое число запасных станций на одном интервале. "
                "При значении 2 допустимы три решения: ноль, одна и две резервные станции.",
            ),
            (
                "p",
                "Ноль оставляет на линии только рабочие станции. Верхняя граница поля — 6. Единица измерения — одна станция.",
            ),
        ],
    ),
    (
        "Вероятность",
        [
            (
                "p",
                "В строке интервала записывается вероятность безотказной работы одной станции без резерва. "
                "В модели она обозначена p. Это доля: 0,7 соответствует 70 процентам. "
                "Допустимы значения больше 0 и до 1 включительно. Запятая и точка равносильны: 0,7 и 0.7 — одно число.",
            ),
            (
                "p",
                "Единица означает, что станция на выбранном сроке не отказывает, и резерв эту вероятность уже не повышает.",
            ),
            ("p", "Откуда берётся p:"),
            (
                "bullets",
                [
                    "Из условия задачи, уже в виде доли.",
                    "Из паспорта станции или отдельного расчёта надёжности на срок работы линии. В окно переносится готовая вероятность.",
                    "Если известны средняя наработка на отказ T0 и срок T, долю считают заранее: p = exp(−T / T0). Экспоненту программа сама не вычисляет.",
                ],
            ),
            (
                "p",
                "Вероятности при резерве в окно не вводятся: программа считает их сама. Формула есть в пункте «Надёжность».",
            ),
        ],
    ),
    (
        "Цена станции",
        [
            (
                "p",
                "Число c — цена одной станции на данном интервале, в тех же тысячах рублей, что и бюджет. "
                "У разных интервалов цены могут различаться.",
            ),
            (
                "p",
                "Рабочая станция и каждая резервная станция одного интервала стоят одинаково. "
                "Стоимость интервала растёт пропорционально числу станций.",
            ),
        ],
    ),
    (
        "Интервалы",
        [
            (
                "p",
                "Одна строка — один интервал, один пролёт между соседними станциями трассы. "
                "Последнюю строку удалить нельзя. В этой версии интервалов не больше пятнадцати.",
            ),
            (
                "p",
                "Порядок строк — порядок интервалов от начала линии к концу.",
            ),
        ],
    ),
    (
        "Ответ",
        [
            (
                "p",
                "Под кнопкой «Рассчитать» появляется короткая строка. В ней три части.",
            ),
            (
                "formula",
                [
                    ("t", "x"), ("sup", "опт"),
                    ("t", "  =  { x"), ("sub", "1"),
                    ("t", ", x"), ("sub", "2"),
                    ("t", ", … }"),
                    ("sp", 24),
                    ("t", "P  =  …"),
                    ("sp", 24),
                    ("t", "затраты … из … тыс. руб."),
                ],
            ),
            (
                "bullets",
                [
                    "Числа в фигурных скобках — сколько резервных станций ставится на интервалах по порядку.",
                    "P — вероятность безотказной работы всей линии.",
                    "Затраты — какая часть бюджета занята, в тысячах рублей.",
                ],
            ),
            ("p", "В поле «Решение» печатается полный протокол, сверху вниз."),
            (
                "bullets",
                [
                    "Первая таблица: для каждого числа резервных станций показаны вероятность интервала и его стоимость. Оба числа программа считает из p и c.",
                    "Шаги динамического программирования. Шаг 1 относится к последнему интервалу, следующий шаг — к предыдущему, последний шаг — к первому.",
                    "Состояние s — сумма в тысячах рублей на текущий интервал и на все интервалы после него.",
                    "Столбец варианта — значение критерия при этом числе резервных станций. Прочерк означает, что вариант дороже текущего s.",
                    "Оптимум строки — лучшее значение и число резервных станций, на котором оно достигнуто.",
                    "Восстановление плана идёт от полного бюджета по остаткам и выписывает одно решение на каждом интервале.",
                    "В конце повторены стратегия, произведение вероятностей, итоговое P, сумма затрат и неиспользованный остаток.",
                ],
            ),
            (
                "note",
                "Вероятности на экране округляются до четырёх знаков после запятой, лишние нули отбрасываются. "
                "Сравнение вариантов выполняется до этого округления.",
            ),
        ],
    ),
    (
        "Надёжность",
        [
            (
                "p",
                "На интервале всегда стоит одна рабочая станция. К ней добавляют x резервных, "
                "и всего на интервале оказывается 1 + x одинаковых станций. "
                "Интервал теряет связь, когда отказали все они. Пока работает хотя бы одна, интервал считается исправным.",
            ),
            (
                "p",
                "Отказы станций внутри интервала независимы. Вероятность отказа одной станции равна q = 1 − p. "
                "Вероятность, что отказали все станции интервала, равна q в степени 1 + x.",
            ),
            (
                "formula",
                [
                    ("t", "P"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
                    ("t", ") = 1 − (1 − p"), ("sub", "i"), ("t", ")"), ("sup", "1+xᵢ"),
                ],
            ),
            (
                "bullets",
                [
                    "При x = 0 станция одна, и вероятность интервала равна p.",
                    "При x = 1 интервал отказывает, только если отказали обе станции.",
                    "При x = 2 интервал отказывает, только если отказали все три станции.",
                ],
            ),
        ],
    ),
    (
        "Стоимость",
        [
            (
                "p",
                "Стоимость складывается из рабочей станции и резерва. Станции одного интервала одинаковы по цене.",
            ),
            (
                "formula",
                [
                    ("t", "C"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
                    ("t", ") = (1 + x"), ("sub", "i"), ("t", ") · c"), ("sub", "i"),
                ],
            ),
            (
                "p",
                "При нуле резервных станций стоимость равна c, при одной — 2c, при двух — 3c. "
                "Сумма выражена в тысячах рублей. Пары «вероятность / стоимость» программа собирает сама и печатает в первой таблице решения.",
            ),
        ],
    ),
    (
        "Линия",
        [
            (
                "p",
                "Отказы разных интервалов независимы. Линия работает, когда работают все интервалы сразу, "
                "поэтому вероятности перемножаются.",
            ),
            (
                "formula",
                [
                    ("t", "P"), ("sub", "л"), ("t", " = "),
                    ("stack", "∏", "n", "i = 1"),
                    ("t", " P"), ("sub", "i"), ("t", "(x"), ("sub", "i"), ("t", ")"),
                ],
            ),
            ("p", "Деньги складываются. План допустим, когда сумма стоимостей не выше бюджета."),
            (
                "formula",
                [
                    ("stack", "∑", "n", "i = 1"),
                    ("sp", 4),
                    ("t", "C"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
                    ("t", ")  ≤  бюджет"),
                ],
            ),
            (
                "p",
                "Каждое x — целое число от 0 до максимума резерва. Нужен набор, при котором произведение вероятностей максимально.",
            ),
            (
                "p",
                "При n интервалах и максимуме резерва m полное число планов равно (m + 1) в степени n. "
                "Динамическое программирование собирает план по одному интервалу и заново не перебирает уже посчитанный хвост линии.",
            ),
        ],
    ),
    (
        "Расчёт",
        [
            (
                "p",
                "Расчёт идёт обратной прогонкой. Один шаг — один интервал, управление на шаге — целое число резервных станций. "
                "После выбора x и оплаты его стоимости для оставшихся интервалов важно, сколько тысяч рублей осталось.",
            ),
            ("p", "Состояние s — деньги на текущий интервал и на все следующие. На последнем интервале хвоста уже нет."),
            (
                "formula",
                [
                    ("t", "F"), ("sub", "n"), ("t", "(s"), ("sub", "n"), ("t", ") = "),
                    ("stack", "max", "", "xₙ"),
                    ("t", "  { P"), ("sub", "n"), ("t", "(x"), ("sub", "n"), ("t", ") }"),
                ],
            ),
            (
                "formula",
                [
                    ("t", "при   C"), ("sub", "n"), ("t", "(x"), ("sub", "n"),
                    ("t", ") ≤ s"), ("sub", "n"),
                ],
            ),
            (
                "p",
                "На предыдущем интервале выбранный x забирает C(x) из s. На хвост остаётся s − C(x). "
                "Текущий интервал умножает свою вероятность на уже посчитанный оптимум хвоста.",
            ),
            (
                "formula",
                [
                    ("t", "F"), ("sub", "i"), ("t", "(s"), ("sub", "i"), ("t", ") = "),
                    ("stack", "max", "", "xᵢ"),
                    ("t", "  { P"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
                    ("t", ") · F"), ("sub", "i+1"),
                    ("t", "(s"), ("sub", "i"), ("t", " − C"), ("sub", "i"),
                    ("t", "(x"), ("sub", "i"), ("t", ")) }"),
                ],
            ),
            (
                "formula",
                [
                    ("t", "при   C"), ("sub", "i"), ("t", "(x"), ("sub", "i"),
                    ("t", ") ≤ s"), ("sub", "i"),
                ],
            ),
            (
                "p",
                "Если два варианта дают одно значение, остаётся меньший резерв. "
                "Шаг строк в таблице — наибольший общий делитель всех стоимостей и бюджета. "
                "Чем мельче этот делитель, тем длиннее таблицы. Затем программа идёт от полного бюджета к концу линии и снимает безусловное x.",
            ),
        ],
    ),
    (
        "Другие данные",
        [
            (
                "bullets",
                [
                    "Менять можно бюджет, потолок резерва, число интервалов, вероятность и цену станции. После правки план строится кнопкой «Рассчитать» или клавишей Enter.",
                    "Ноль в поле максимума резерва оставляет только рабочие станции. Неизрасходованный остаток бюджета допустим: программа ищет наибольшую вероятность.",
                    "Если бюджет меньше суммы цен рабочих станций, допустимого плана нет. Сообщение показывает, сколько тысяч рублей нужно минимум.",
                    "Новая строка интервала добавляет шаг: в произведение входит ещё один множитель, в сумму стоимостей — ещё одно слагаемое. Формулы в пунктах «Надёжность», «Стоимость» и «Расчёт» остаются теми же.",
                ],
            ),
        ],
    ),
    (
        "Ошибки ввода",
        [
            (
                "bullets",
                [
                    "Вероятность записана процентом, например 70. В поле нужна доля 0,7.",
                    "В одном денежном поле стоят рубли, в другом — тысячи рублей. Все денежные поля заполняются целыми тысячами рублей.",
                    "В бюджет заложили только резерв и не включили цены рабочих станций. Лимит тогда оказывается ниже стоимости линии.",
                    "Цена или бюджет заданы дробью. Окно принимает целые тысячи рублей.",
                    "Поле пустое или в нём буква. Текст ошибки называет это поле.",
                ],
            ),
        ],
    ),
]
