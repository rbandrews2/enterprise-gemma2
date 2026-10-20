"""Arithmetic for operator-reviewed, revision-bound formulas. No eval or tools."""
import ast
from decimal import Decimal, InvalidOperation, localcontext
import re

from pydantic import Field
from shared.contracts import StrictModel


class CalculationInput(StrictModel):
    name: str = Field(pattern=r'^[A-Za-z][A-Za-z0-9_]{0,15}$')
    value: str = Field(pattern=r'^-?[0-9]{1,9}(?:\.[0-9]{1,6})?$')
    unit: str = Field(min_length=1, max_length=30)
    question_quote: str = Field(min_length=1, max_length=300)


class Calculation(StrictModel):
    formula_id: str = Field(min_length=1, max_length=100)
    inputs: list[CalculationInput] = Field(min_length=1, max_length=8)


def arithmetic(expression, values):
    """Small arithmetic language; disallow functions, attributes and arbitrary code."""
    if not isinstance(expression, str) or len(expression) > 150:
        raise ValueError('Invalid reviewed expression')
    try:
        values = {name: Decimal(str(value)) for name, value in values.items()}
        if any(not value.is_finite() or abs(value) > Decimal('1e9') for value in values.values()):
            raise ValueError('Input outside bounds')
    except (InvalidOperation, TypeError) as error:
        raise ValueError('Invalid numeric input') from error
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as error:
        raise ValueError('Invalid reviewed expression') from error
    if len(list(ast.walk(tree))) > 64:
        raise ValueError('Expression too complex')

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = Decimal(str(node.value))
        elif isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): result = left + right
            elif isinstance(node.op, ast.Sub): result = left - right
            elif isinstance(node.op, ast.Mult): result = left * right
            elif isinstance(node.op, ast.Div): result = left / right
            elif isinstance(node.op, ast.Pow) and right in (Decimal(2), Decimal(3)): result = left ** int(right)
            else: raise ValueError('Unsupported arithmetic')
        else:
            raise ValueError('Unsupported arithmetic')
        if not result.is_finite() or abs(result) > Decimal('1e15'):
            raise ValueError('Arithmetic outside bounds')
        return result

    try:
        with localcontext() as context:
            context.prec = 28
            return visit(tree)
    except (ArithmeticError, InvalidOperation, SyntaxError) as error:
        raise ValueError('Invalid arithmetic') from error


def verify_calculations(calculations, packet):
    rules = {r['formula_id']: r for r in packet.get('formulas', [])}
    evidence = {p['citation_id']: p for p in packet['evidence'] if p['answer_eligible']}
    results = []
    normalize = lambda value: ' '.join(value.split())
    for calculation in calculations:
        rule = rules.get(calculation.formula_id)
        if not rule or rule['citation_id'] not in evidence:
            raise ValueError('Calculation requires a reviewed cited formula')
        page = evidence[rule['citation_id']]
        if normalize(rule['supporting_quote']) not in normalize(page['text']):
            raise ValueError('Formula evidence changed')
        values = {}
        expected = rule['inputs']
        for item in calculation.inputs:
            if (item.name in values or item.name not in expected or item.unit != expected[item.name]
                    or normalize(item.question_quote) not in normalize(packet['question'])
                    or not re.search(r'\b' + re.escape(item.unit) + r'\b', item.question_quote, re.I)
                    or not re.search(r'(?<![\d.])' + re.escape(item.value) + r'(?![\d.])', item.question_quote)):
                raise ValueError('Confirm calculation inputs and units explicitly')
            values[item.name] = Decimal(item.value)
            bounds = rule.get('input_bounds', {}).get(item.name)
            if not bounds or not Decimal(bounds[0]) <= values[item.name] <= Decimal(bounds[1]):
                raise ValueError('Input outside the reviewed formula range')
        if set(values) != set(expected):
            raise ValueError('Missing formula inputs')
        result = arithmetic(rule['expression'], values)
        results.append({'formula_id': calculation.formula_id, 'citation_id': rule['citation_id'],
                        'expression': rule['expression'], 'inputs': [i.model_dump() for i in calculation.inputs],
                        'result': str(result), 'unit': rule['result_unit'],
                        'arithmetic_verified': True, 'applicability_verified': False})
    return results
