import math

from mcdreforged.api.types import PluginServerInterface
from mcdreforged.api.command import GreedyText, SimpleCommandBuilder

class Calculator:
    def __init__(self):
        self.functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'log': math.log,
            'exp': math.exp,
            'sqrt': math.sqrt,
            'abs': abs,
            'ceil': math.ceil,
            'floor': math.floor,
            'round': round,
            'radians': math.radians,
            'degrees': math.degrees,
        }
        self.operator = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '%': 2,
            '^': 3,
        }
        self.unit = {
            'k': 1000,
            'm': 1000000,
            'g': 1000000000,
            't': 1000000000000,
            'p': 1000000000000000,
            'ulv': 8,
            'lv': 32,
            'mv': 128,
            'hv': 512,
            'ev': 2048,
            'iv': 8192,
            'luv': 32768,
            'zpm': 131072,
            'uv': 524288,
            'uhv': 2097152,
            'uev': 8388608,
            'uiv': 33554432,
            'uxv': 134217728,
            'opv': 536870912,
            'max': 2147483648,
        }

    def get_priority(self, op: str) -> int:
        if op in self.operator:
            return self.operator[op]
        elif op == '(':
            return 0
        elif op in self.unit:
            return 4
        else:
            return 5

    def calculate(self, number_stack: list, operator_stack: list):
        op = operator_stack.pop()
        if op in self.functions:
            arg = number_stack.pop()
            num = self.functions[op](arg)
            number_stack.append(num)
        elif op in self.operator:
            try:
                b = number_stack.pop()
                a = number_stack.pop()
            except:
                raise ValueError(f"运算符{op}缺少足够参数")
            if op == '+':
                number_stack.append(a + b)
            elif op == '-':
                number_stack.append(a - b)
            elif op == '*':
                number_stack.append(a * b)
            elif op == '/':
                if abs(b) < 1e-10:
                    raise ValueError("除以零")
                number_stack.append(a / b)
            elif op == '%':
                if abs(b) < 1e-10:
                    raise ValueError("对0取余")
                number_stack.append(a % b)
            elif op == '^':
                number_stack.append(a ** b)
        elif op == '(':
            operator_stack.append(op)
        elif op in self.unit:
            num = number_stack.pop()
            num = num * self.unit[op]
            number_stack.append(num)
        elif 'max' in op:
            num = number_stack.pop()
            add = ord(op[3]) - ord('a') + 1
            num = num * self.unit['max'] * (4 ** add)
            number_stack.append(num)
        else:
            raise ValueError(f'无效的运算: {op}')
        return number_stack, operator_stack

    def expression_parse(self, expr: str) -> float:
        number_stack = []
        operator_stack = []
        i = 0
        length = len(expr)
        while i < length:
            char = expr[i]
            if char == '(':
                operator_stack.append(char)
            elif char == ')':
                while operator_stack and operator_stack[-1] != '(':
                    number_stack, operator_stack = self.calculate(number_stack, operator_stack)
                if not operator_stack:
                    raise ValueError('括号不匹配')
                operator_stack.pop()
            elif char.isdigit():
                number = ""
                while i < length and (expr[i].isdigit() or expr[i] == '.'):
                    number += expr[i]
                    i += 1
                number_stack.append(float(number))
                continue
            elif char.isalpha():
                function_name = ""
                while i < length and expr[i].isalpha():
                    function_name += expr[i].lower()
                    i += 1
                if function_name in self.functions:
                    operator_stack.append(function_name)
                elif function_name in self.unit or 'max' in function_name:
                    operator_stack.append(function_name)
                else:
                    raise ValueError(f'未知的函数或单位: {function_name}')
                continue
            elif char in self.operator:
                while (operator_stack and (
                        self.get_priority(char) < self.get_priority(operator_stack[-1]) or (
                            self.get_priority(char) == self.get_priority(operator_stack[-1]) and
                            char != '^'
                        )
                    )
                ):
                    number_stack, operator_stack = self.calculate(number_stack, operator_stack)
                operator_stack.append(char)
            else:
                raise ValueError(f'非法字符: {char}')
            i = i + 1
        while operator_stack:
            if operator_stack[-1] == '(':
                raise ValueError('括号不匹配')
            number_stack, operator_stack = self.calculate(number_stack, operator_stack)
        result = float(number_stack.pop())
        if number_stack:
            raise ValueError('数字多余')
        return result

    def format_result(self, value: float) -> str:
        if value == 0:
            return "0"
        if abs(value - round(value)) < 1e-10:
            return str(int(round(value)))
        formatted = f"{value:.10f}"
        formatted = formatted.rstrip('0').rstrip('.')
        return formatted

    def solve(self, expression: str) -> str:
        result = self.expression_parse(expression.replace(" ",""))
        if math.isinf(result):
            return "Inf" if result > 0 else "-Inf"
        elif math.isnan(result):
            return "Nan"
        return self.format_result(result)

def on_load(server: PluginServerInterface, prev_module):
    server.logger.info('loaded MLC Calculator plugin')
    server.register_help_message('!!calc', '查看计算器帮助')
    builder = SimpleCommandBuilder()
    builder.command('!!calc', say_help_msg)
    builder.command('!!calc <expression>', calc_expression)
    builder.arg('expression', GreedyText)
    builder.register(server)

HELP_MSG = '''§7!!calc <expression> §f计算表达式
§7支持运算符：+ - * / % ^
§7支持计量单位: K-P
§7支持格雷电压: ULV-MAX+26
§7MAX+n以MAX后接字母表示，如MAXA表示MAX+1
§7支持数学函数: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, log, exp, sqrt, abs, ceil, floor, round, radians, degrees
§7表达式允许含有空格、括号
§7表达式对字母大小写不敏感'''

def say_help_msg(src, ctx):
    return src.reply(HELP_MSG)

def calc_expression(src, ctx):
    expression = ctx['expression']
    calculator = Calculator()
    try:
        src.get_server().say(f'§7{expression}=§e{calculator.solve(expression)}')
    except ValueError as e:
        src.get_server().say(f'§7{expression}表达式错误: §c{e}')