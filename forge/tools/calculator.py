"""Arithmetic over an AST whitelist. No eval: the expression comes from a model."""

import ast
import operator

OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
             ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
FUNCTIONS = {"round": round, "min": min, "max": max}
LIMIT = 1e15


def _value(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        result = node.value
    elif isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        result = OPERATORS[type(node.op)](_value(node.operand))
    elif isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _value(node.left), _value(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        result = OPERATORS[type(node.op)](left, right)
    elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
          and node.func.id in FUNCTIONS and not node.keywords):
        result = FUNCTIONS[node.func.id](*map(_value, node.args))
    else:
        raise ValueError("only numbers, + - * / **, round, min and max are allowed")
    if isinstance(result, complex) or abs(result) > LIMIT:
        raise ValueError("result out of range")
    return result


def evaluate(expression: str) -> float:
    if len(expression) > 200:
        raise ValueError("expression too long")
    return _value(ast.parse(expression, mode="eval").body)


def run(expression: str) -> str:
    return f"{expression} = {round(evaluate(str(expression)), 6)}"
