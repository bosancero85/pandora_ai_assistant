"""Sicherer Taschenrechner – nutzt ast.parse statt eval(), damit keine
beliebigen Python-Ausdrücke ausgeführt werden können."""

import ast
import operator

from plugin_base import AssistantPlugin

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("nur Zahlen sind erlaubt")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("ungültiger oder nicht erlaubter Ausdruck")


class CalculatePlugin(AssistantPlugin):
    action = "calculate"
    description = 'mathematischen Ausdruck berechnen (query = z. B. "12 * (3 + 4)")'
    needs_query = True

    def execute(self, query: str = "") -> str:
        expr = (query or "").strip()
        if not expr:
            return "Kein Rechenausdruck angegeben."
        try:
            tree = ast.parse(expr, mode="eval")
            result = _safe_eval(tree.body)
        except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as exc:
            return f"Konnte '{expr}' nicht berechnen: {exc}"
        return f"{expr} = {result}"
