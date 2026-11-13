"""Резервирование станций радиорелейной линии методом динамического программирования.

Модель повторяет пример лекции: на каждом интервале работает одна станция,
к ней можно добавить резервные. Отказы интервалов независимы, поэтому
надёжность линии равна произведению надёжностей интервалов. Суммарная
стоимость станций не должна превысить заданный бюджет.

Решение строится обратной прогонкой. Сначала для каждого остатка ресурса
считаются условные оптимумы от последнего интервала к первому, затем
по этим таблицам восстанавливается безусловный план.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class InputError(ValueError):
    """Неверные исходные данные, которые можно показать пользователю."""


@dataclass(frozen=True)
class Interval:
    name: str
    single_reliability: float
    station_cost: int


@dataclass(frozen=True)
class Problem:
    intervals: tuple[Interval, ...]
    budget: int
    max_reserve: int


@dataclass(frozen=True)
class Variant:
    reserve: int
    reliability: float
    cost: int


@dataclass(frozen=True)
class StateRow:
    resource: int
    values: tuple[float | None, ...]
    best_value: float
    best_reserve: int
    best_cost: int


@dataclass(frozen=True)
class StageResult:
    """Один шаг обратной прогонки.

    step_number равен 1 для последнего интервала линии: так шаги
    пронумерованы в лекции.
    """

    step_number: int
    interval_index: int
    interval_name: str
    resource_min: int
    resource_max: int
    variants: tuple[Variant, ...]
    rows: tuple[StateRow, ...]
    final_step: bool


@dataclass(frozen=True)
class PlanStep:
    interval_index: int
    interval_name: str
    resource_before: int
    reserve: int
    reliability: float
    cost: int
    resource_after: int


@dataclass(frozen=True)
class Solution:
    money_step: int
    stages: tuple[StageResult, ...]
    plan: tuple[PlanStep, ...]
    line_reliability: float
    total_cost: int
    budget: int


HELP_TEXT = """\
Резервирование радиорелейной линии

Линия состоит из нескольких интервалов. На каждом интервале стоит одна
рабочая станция, и можно поставить резервные. Отказы интервалов считаются
независимыми, поэтому вероятность безотказной работы линии равна
произведению вероятностей интервалов.

Если одна станция на интервале работает с вероятностью pᵢ, то при xᵢ
резервных станциях

    Pᵢ(xᵢ) = 1 − (1 − pᵢ)¹⁺ˣⁱ.

Стоимость интервала при том же xᵢ равна (1 + xᵢ) · cᵢ: в неё входят рабочая
станция и резерв. Деньги задаются целыми тысячами рублей: 100 означает
100 000 руб. В исходном примере cᵢ равно 100, 200 и 300 тыс. руб.

Нужно выбрать целое x на каждом интервале, от 0 до заданного максимума,
так чтобы произведение P(x) было наибольшим, а сумма стоимостей не
превысила бюджет.

Расчёт идёт методом динамического программирования, обратной прогонкой.

Состояние sᵢ — сколько денег выделено на текущий и все следующие интервалы.
На последнем интервале

    Fₙ(sₙ) = max pₙ(xₙ)  при cₙ(xₙ) ≤ sₙ.

На предыдущем интервале

    Fᵢ(sᵢ) = max pᵢ(xᵢ) · Fᵢ₊₁(sᵢ − cᵢ(xᵢ)).

Так получаются таблицы условных решений. Затем от полного бюджета
программа идёт к началу линии и по остатку ресурса снимает с каждой
таблицы уже безусловное число резервных станций.

При запуске подставлены три интервала с бюджетом 1200 тыс. руб.
и максимумом в две резервные станции.
"""


def lecture_problem() -> Problem:
    """Числовой пример лекции: три интервала, бюджет 1200, не больше двух резервных."""

    return Problem(
        intervals=(
            Interval("Интервал 1", 0.70, 100),
            Interval("Интервал 2", 0.60, 200),
            Interval("Интервал 3", 0.50, 300),
        ),
        budget=1200,
        max_reserve=2,
    )


def interval_reliability(single_reliability: float, reserve: int) -> float:
    """Вероятность безотказной работы интервала при заданном числе резервных станций."""

    failure = 1.0 - single_reliability
    return 1.0 - failure ** (1 + reserve)


def variants_for(interval: Interval, max_reserve: int) -> tuple[Variant, ...]:
    return tuple(
        Variant(
            reserve=reserve,
            reliability=interval_reliability(interval.single_reliability, reserve),
            cost=interval.station_cost * (1 + reserve),
        )
        for reserve in range(max_reserve + 1)
    )


def solve(problem: Problem) -> Solution:
    """Условная оптимизация с конца линии и восстановление безусловного плана."""

    intervals = problem.intervals
    count = len(intervals)
    if count == 0:
        raise InputError("Добавьте хотя бы один интервал.")
    if problem.max_reserve < 0:
        raise InputError("Число резервных станций не может быть отрицательным.")
    if problem.budget <= 0:
        raise InputError("Бюджет должен быть положительным.")

    prepared: list[tuple[Variant, ...]] = []
    for index, interval in enumerate(intervals, start=1):
        if not interval.name.strip():
            raise InputError(f"У интервала {index} нет названия.")
        probability = interval.single_reliability
        if not 0.0 < probability <= 1.0:
            raise InputError(
                f"Вероятность одной станции на интервале {index} должна быть больше 0 и не больше 1."
            )
        if interval.station_cost <= 0:
            raise InputError(f"Стоимость станции на интервале {index} должна быть положительной.")
        prepared.append(variants_for(interval, problem.max_reserve))

    minimum_costs = [options[0].cost for options in prepared]
    if sum(minimum_costs) > problem.budget:
        raise InputError(
            "Бюджета не хватает даже на рабочие станции без резерва: "
            f"нужно не меньше {sum(minimum_costs)} тыс. руб., задано {problem.budget} тыс. руб."
        )

    option_costs = [variant.cost for options in prepared for variant in options]
    money_step = _money_step([*option_costs, problem.budget])
    estimated_states = (problem.budget // money_step + 1) * count
    if estimated_states > 250_000:
        raise InputError(
            "Сетка состояний слишком мелкая для этого бюджета. "
            "Задайте суммы более крупным шагом: в исходном примере все стоимости кратны 100 тыс. руб."
        )

    prefix_min = [0]
    for cost in minimum_costs:
        prefix_min.append(prefix_min[-1] + cost)

    # stages_by_interval[i] заполняется от конца линии к началу.
    stages_by_interval: list[StageResult | None] = [None] * count
    for index in range(count - 1, -1, -1):
        resource_min = prefix_min[count] - prefix_min[index]
        resource_max = problem.budget - prefix_min[index]
        if index == 0:
            resources = (problem.budget,)
        else:
            resources = tuple(range(resource_min, resource_max + 1, money_step))

        rows: list[StateRow] = []
        for resource in resources:
            values: list[float | None] = []
            best_value = -1.0
            best_reserve = 0
            best_cost = 0
            found = False
            for variant in prepared[index]:
                if variant.cost > resource:
                    values.append(None)
                    continue
                if index == count - 1:
                    value = variant.reliability
                else:
                    rest = resource - variant.cost
                    next_stage = stages_by_interval[index + 1]
                    assert next_stage is not None
                    next_row = _row_by_resource(next_stage, rest)
                    if next_row is None:
                        values.append(None)
                        continue
                    value = variant.reliability * next_row.best_value
                values.append(value)
                better_value = value > best_value + 1e-12
                same_value_cheaper = abs(value - best_value) <= 1e-12 and variant.reserve < best_reserve
                if not found or better_value or same_value_cheaper:
                    found = True
                    best_value = value
                    best_reserve = variant.reserve
                    best_cost = variant.cost
            if not found:
                raise InputError(
                    f"Для интервала {index + 1} при остатке {resource} тыс. руб. нет допустимого варианта."
                )
            rows.append(
                StateRow(
                    resource=resource,
                    values=tuple(values),
                    best_value=best_value,
                    best_reserve=best_reserve,
                    best_cost=best_cost,
                )
            )

        stages_by_interval[index] = StageResult(
            step_number=count - index,
            interval_index=index,
            interval_name=intervals[index].name.strip(),
            resource_min=resource_min,
            resource_max=resource_max,
            variants=prepared[index],
            rows=tuple(rows),
            final_step=index == 0,
        )

    plan: list[PlanStep] = []
    resource = problem.budget
    for index, interval in enumerate(intervals):
        stage = stages_by_interval[index]
        assert stage is not None
        row = _row_by_resource(stage, resource)
        if row is None:
            raise InputError(
                f"Не удалось восстановить план: для интервала {index + 1} нет состояния {resource} тыс. руб."
            )
        reliability = interval_reliability(interval.single_reliability, row.best_reserve)
        cost = row.best_cost
        plan.append(
            PlanStep(
                interval_index=index,
                interval_name=interval.name.strip(),
                resource_before=resource,
                reserve=row.best_reserve,
                reliability=reliability,
                cost=cost,
                resource_after=resource - cost,
            )
        )
        resource -= cost

    line_reliability = 1.0
    total_cost = 0
    for step in plan:
        line_reliability *= step.reliability
        total_cost += step.cost

    stages = tuple(stage for stage in reversed(stages_by_interval) if stage is not None)
    return Solution(
        money_step=money_step,
        stages=stages,
        plan=tuple(plan),
        line_reliability=line_reliability,
        total_cost=total_cost,
        budget=problem.budget,
    )


def format_report(problem: Problem, solution: Solution) -> str:
    """Текст с исходной таблицей, таблицами Беллмана и восстановленным планом."""

    lines: list[str] = [
        "Резервирование радиорелейной линии",
        "Динамическое программирование, обратная прогонка",
        "",
        f"Бюджет: {solution.budget} тыс. руб.",
        f"Интервалов: {len(problem.intervals)}",
        f"Резервных станций на интервале: от 0 до {problem.max_reserve}",
        f"Шаг ресурса в таблицах: {solution.money_step} тыс. руб.",
        "",
        "Исходные варианты",
        "P(x) = 1 − (1 − p)^(1 + x), стоимость = (1 + x) · c.",
        "",
    ]

    for index, interval in enumerate(problem.intervals, start=1):
        stage = next(item for item in solution.stages if item.interval_index == index - 1)
        parts = [
            f"x={variant.reserve}: P={format_number(variant.reliability)}, C={variant.cost}"
            for variant in stage.variants
        ]
        lines.append(
            f"{index}. {interval.name.strip()} — p одной станции {format_number(interval.single_reliability)}, "
            f"c = {interval.station_cost} тыс. руб."
        )
        lines.append("   " + "; ".join(parts))
    lines.append("")

    kept_resources = {step.resource_before for step in solution.plan}
    for stage in solution.stages:
        title = "безусловная оптимизация" if stage.final_step else "условная оптимизация"
        lines.append(
            f"Шаг {stage.step_number}. {stage.interval_name} "
            f"(интервал {stage.interval_index + 1} линии), {title}"
        )
        lines.append(
            f"Границы состояния: от {stage.resource_min} до {stage.resource_max} тыс. руб. "
            "Состояние s — стоимость оборудования на этом и следующих интервалах."
        )
        shown, truncated = _rows_for_report(stage.rows, kept_resources)
        headers = ["s"] + [f"x={variant.reserve}" for variant in stage.variants] + ["F*(s)", "x*"]
        table_rows: list[list[str]] = []
        for row in shown:
            cells = [str(row.resource)]
            cells.extend("-" if value is None else format_number(value) for value in row.values)
            cells.append(format_number(row.best_value))
            cells.append(str(row.best_reserve))
            table_rows.append(cells)
        lines.append(_format_table(headers, table_rows))
        if truncated:
            lines.append(
                f"Показаны {len(shown)} из {len(stage.rows)} состояний, "
                "включая состояния оптимального плана."
            )
        lines.append("")

    lines.append("Восстановление безусловного плана")
    for step in solution.plan:
        lines.append(
            f"s = {step.resource_before} → {step.interval_name}: "
            f"x = {step.reserve}, P = {format_number(step.reliability)}, "
            f"стоимость {step.cost}, остаток {step.resource_after}"
        )
    lines.append("")

    reserves = ", ".join(str(step.reserve) for step in solution.plan)
    reliabilities = " · ".join(format_number(step.reliability) for step in solution.plan)
    costs = " + ".join(str(step.cost) for step in solution.plan)
    lines.extend(
        [
            "Оптимальная стратегия",
            f"x* = {{{reserves}}}",
            f"Вероятности интервалов: {reliabilities}",
            f"Вероятность безотказной работы линии P = {format_number(solution.line_reliability)}",
            f"Затраты: {costs} = {solution.total_cost} тыс. руб. из {solution.budget} тыс. руб.",
            f"Неиспользованный остаток: {solution.budget - solution.total_cost} тыс. руб.",
        ]
    )
    return "\n".join(lines)


def format_number(value: float, digits: int = 4) -> str:
    """Десятичная запись с запятой, без хвостовых нулей."""

    rounded = round(float(value), digits)
    text = f"{rounded:.{digits}f}".rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        text = "0"
    return text.replace(".", ",")


def format_summary(solution: Solution) -> str:
    reserves = ", ".join(str(step.reserve) for step in solution.plan)
    return (
        f"x опт = {{{reserves}}}    "
        f"P = {format_number(solution.line_reliability)}    "
        f"затраты {solution.total_cost} из {solution.budget} тыс. руб."
    )


def _money_step(amounts: list[int]) -> int:
    step = 0
    for amount in amounts:
        step = math.gcd(step, int(amount))
    if step <= 0:
        raise InputError("Не удалось определить шаг стоимости.")
    return step


def _row_by_resource(stage: StageResult, resource: int) -> StateRow | None:
    for row in stage.rows:
        if row.resource == resource:
            return row
    return None


def _rows_for_report(rows: tuple[StateRow, ...], keep_resources: set[int], limit: int = 40) -> tuple[tuple[StateRow, ...], bool]:
    if len(rows) <= limit:
        return rows, False
    must = [row for row in rows if row.resource in keep_resources]
    rest_budget = max(0, limit - len(must))
    if rest_budget == 0:
        return tuple(must[:limit]), True
    others = [row for row in rows if row.resource not in keep_resources]
    if len(others) <= rest_budget:
        chosen = must + others
    else:
        chosen = list(must)
        last_index = len(others) - 1
        for position in range(rest_budget):
            index = round(position * last_index / max(1, rest_budget - 1))
            chosen.append(others[index])
    chosen.sort(key=lambda row: row.resource)
    unique: list[StateRow] = []
    seen: set[int] = set()
    for row in chosen:
        if row.resource in seen:
            continue
        seen.add(row.resource)
        unique.append(row)
    return tuple(unique), True


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def paint(cells: list[str]) -> str:
        return "  ".join(cell.rjust(widths[index]) for index, cell in enumerate(cells))

    separator = paint(["-" * width for width in widths])
    body = [paint(row) for row in rows]
    return "\n".join([paint(headers), separator, *body])


def _check_lecture_example() -> None:
    problem = lecture_problem()
    solution = solve(problem)
    reserves = tuple(step.reserve for step in solution.plan)
    reliabilities = tuple(step.reliability for step in solution.plan)
    costs = tuple(step.cost for step in solution.plan)
    if reserves != (1, 1, 1):
        raise AssertionError(reserves)
    if costs != (200, 400, 600):
        raise AssertionError(costs)
    expected_probabilities = (0.91, 0.84, 0.75)
    for actual, expected in zip(reliabilities, expected_probabilities, strict=True):
        if not math.isclose(actual, expected, abs_tol=1e-12):
            raise AssertionError((actual, expected))
    if not math.isclose(solution.line_reliability, 0.5733, abs_tol=1e-12):
        raise AssertionError(solution.line_reliability)
    if solution.total_cost != 1200 or solution.money_step != 100:
        raise AssertionError((solution.total_cost, solution.money_step))

    by_index = {stage.interval_index: stage for stage in solution.stages}
    last = by_index[2]
    expected_last = {300: (0, 0.5), 600: (1, 0.75), 900: (2, 0.875)}
    for row in last.rows:
        if row.resource not in expected_last:
            continue
        reserve, value = expected_last[row.resource]
        if row.best_reserve != reserve or not math.isclose(row.best_value, value, abs_tol=1e-12):
            raise AssertionError((row.resource, row.best_reserve, row.best_value))

    middle = by_index[1]
    expected_middle = {500: (0, 0.3), 800: (0, 0.45), 900: (2, 0.468), 1000: (1, 0.63), 1100: (1, 0.63)}
    for row in middle.rows:
        if row.resource not in expected_middle:
            continue
        reserve, value = expected_middle[row.resource]
        if row.best_reserve != reserve or not math.isclose(row.best_value, value, abs_tol=1e-9):
            raise AssertionError((row.resource, row.best_reserve, row.best_value))

    first = by_index[0]
    if len(first.rows) != 1 or first.rows[0].best_reserve != 1:
        raise AssertionError(first.rows)
    if not math.isclose(first.rows[0].best_value, 0.5733, abs_tol=1e-12):
        raise AssertionError(first.rows[0].best_value)

    report = format_report(problem, solution)
    if "x* = {1, 1, 1}" not in report or "0,5733" not in report:
        raise AssertionError(report)


def _check_edges() -> None:
    too_small = Problem((Interval("Интервал 1", 0.5, 300),), budget=200, max_reserve=2)
    try:
        solve(too_small)
    except InputError:
        pass
    else:
        raise AssertionError("маленький бюджет должен отклоняться")

    single = solve(Problem((Interval("Плечо", 0.5, 300),), budget=600, max_reserve=2))
    if single.plan[0].reserve != 1 or not math.isclose(single.line_reliability, 0.75, abs_tol=1e-12):
        raise AssertionError(single)

    no_reserve = solve(Problem(lecture_problem().intervals, budget=1200, max_reserve=0))
    if tuple(step.reserve for step in no_reserve.plan) != (0, 0, 0):
        raise AssertionError(no_reserve.plan)
    if not math.isclose(no_reserve.line_reliability, 0.7 * 0.6 * 0.5, abs_tol=1e-12):
        raise AssertionError(no_reserve.line_reliability)


if __name__ == "__main__":
    _check_lecture_example()
    _check_edges()
    solution = solve(lecture_problem())
    print(format_report(lecture_problem(), solution))
    print()
    print("Проверка примера лекции и граничных случаев прошла.")
