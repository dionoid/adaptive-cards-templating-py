import json
import re
from .dot_dict import DotDict

class PrebuiltFunctions:
    """
    Prebuilt functions for Adaptive Cards Templating.
    These functions are used to evaluate expressions in the template.

    Note that only the most common functions are supported for now.
    """
    @staticmethod
    def sanitize_expr(expr):
        expr = re.sub(r'\bif\s*\(', '_if(', expr)
        expr = re.sub(r'\bjson\s*\(', '_json(', expr)
        expr = re.sub(r'\bstring\s*\(', '_string(', expr)
        expr = re.sub(r'\bformatNumber\s*\(', '_format_number(', expr)
        return expr

    @staticmethod
    def add_functions_to_scope(scope: dict):
        for key, value in [
            ('_if', PrebuiltFunctions._if),
            ('_json', PrebuiltFunctions._json),
            ('_string', PrebuiltFunctions._string),
            ('_format_number', PrebuiltFunctions._format_number),
        ]: scope[key] = value

    # supports ${if(expr, a, b)}
    @staticmethod
    def _if(condition, true_val, false_val):
        return true_val if condition else false_val
    
    # supports ${json(json_string).property}
    @staticmethod
    def _json(json_string):
        return DotDict.wrap_object(json.loads(json_string))
    
    # supports ${string(obj)}
    @staticmethod
    def _string(obj, locale: str = None):
        # ignore locale for now
        if isinstance(obj, dict):
            return json.dumps(obj)
        elif isinstance(obj, list):
            return ', '.join(map(str, obj))
        else:
            return str(obj)
    
    # supports ${formatNumber(number, precision)}
    @staticmethod
    def _format_number(number: float, precision: int = 0, locale: str = None):
        # ignore locale for now
        return f"{number:,.{precision}f}"
        