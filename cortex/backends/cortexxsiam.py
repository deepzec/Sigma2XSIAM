# File: sigma/backends/cortexxsiam.py
import re
from sigma.conversion.state import ConversionState
from sigma.rule import SigmaRule
from sigma.conversion.base import TextQueryBackend
from sigma.conditions import ConditionAND, ConditionOR, ConditionNOT

class CortexXSIAMBackend(TextQueryBackend):
    """Cortex XSIAM backend."""
    name = "Cortex XSIAM backend"
    formats = {
        "default": "Plain XQL queries for Cortex XSIAM",
    }
    requires_pipeline = True

    precedence = (
        ConditionNOT,
        ConditionAND,
        ConditionOR,
    )
    group_expression = "({expr})"
    parenthesize_or = True

    token_separator = " "
    or_token = "or"
    and_token = "and"
    not_token = "not"
    eq_token = "="

    eq_expression = "{field} {token} {value}"

    string_quoting = ('"', '"', '\\')
    field_quote_pattern = re.compile(r"^[\w.]+$")
    field_quote = None

    wildcard_multi = "*"

    re_expression = "{field} ~= \"{regex}\""
    cidr_expression = "cidrtype({field}, \"{value}\")"
    null_expression = "{field} = null"

    wildcard_match = "{field} = {value}"

    def convert_condition_field_contains_val_str(self, cond, state: ConversionState) -> str:
        value = self.convert_value_str(cond.value, state)
        return f"{self.escape_and_quote_field(cond.field)} contains {value}"

    def convert_condition_field_startswith_val_str(self, cond, state: ConversionState) -> str:
        value = self.convert_value_str(cond.value, state).strip('"')
        return f'{self.escape_and_quote_field(cond.field)} = "{value}*"'

    def convert_condition_field_endswith_val_str(self, cond, state: ConversionState) -> str:
        value = self.convert_value_str(cond.value, state).strip('"')
        return f'{self.escape_and_quote_field(cond.field)} = "*{value}"'

    def convert_condition_field_eq_val_str(self, cond, state: ConversionState) -> str:
        if cond.value.contains_special():
            return self.wildcard_match.format(
                field=self.escape_and_quote_field(cond.field), 
                value=self.convert_value_str(cond.value, state)
            )

        return self.eq_expression.format(
            field=self.escape_and_quote_field(cond.field),
            token=self.eq_token,
            value=self.convert_value_str(cond.value, state)
        )

    def convert_condition_or(self, cond, state: ConversionState) -> str:
        """Convert OR conditions to XQL."""
        args = [self.convert_condition(arg, state) for arg in cond.args]
        result = f" {self.or_token} ".join(args)
        if self.parenthesize_or and len(args) > 1:
            result = self.group_expression.format(expr=result)
        return result

    def convert_condition_and(self, cond, state: ConversionState) -> str:
        """Convert AND conditions to XQL."""
        args = [self.convert_condition(arg, state) for arg in cond.args]
        result = f" {self.and_token} ".join(args)
        return result

    def convert_condition_not(self, cond, state: ConversionState) -> str:
        """Convert NOT conditions to XQL."""
        arg = self.convert_condition(cond.args[0], state)
        # Always parenthesize NOT argument to ensure correct precedence
        if not (arg.startswith('(') and arg.endswith(')')):
            arg = self.group_expression.format(expr=arg)
        return f"{self.not_token} {arg}"

    def convert_rule(self, rule: SigmaRule, output_format: str = "default"):
        """Convert a Sigma rule into a Cortex XSIAM XQL query."""
        converted = super().convert_rule(rule, output_format)

        final_queries = []
        for query in converted:
            final_queries.append(f"datamodel dataset = * | filter {query}")

        return final_queries
