import json
import re
from .dot_dict import DotDict

class PrebuiltFunctions:
    """
    Partial implementation of Adaptive expressions prebuilt functions 
    for Adaptive Cards Templating.
    Note that only the most common functions are supported for now.
    """
    @staticmethod
    def sanitize_expr(expr):
        expr = re.sub(r'\bif\s*\(', '__if(', expr)
        expr = re.sub(r'\bjson\s*\(', '__json(', expr)
        expr = re.sub(r'\bstring\s*\(', '__string(', expr)
        expr = re.sub(r'\bformatNumber\s*\(', '__formatNumber(', expr)
        return expr

    @staticmethod
    def add_functions_to_scope(scope: dict):
        for key, value in [
            ('__if', PrebuiltFunctions._if),
            ('__json', PrebuiltFunctions._json),
            ('__string', PrebuiltFunctions._string),
            ('__formatNumber', PrebuiltFunctions._format_number),
        ]: scope[key] = value

    # supports ${if(expr, a, b)}
    @staticmethod
    def __if(condition, true_val, false_val):
        return true_val if condition else false_val
    
    # supports ${json(json_string).property}
    @staticmethod
    def __json(json_string):
        return DotDict.wrap_object(json.loads(json_string))
    
    # supports ${string(obj)}
    @staticmethod
    def __string(obj, locale: str = None):
        # ignore locale for now
        if isinstance(obj, dict):
            return json.dumps(obj)
        elif isinstance(obj, list):
            return ', '.join(map(str, obj))
        else:
            return str(obj)
    
    # supports ${formatNumber(number, precision)}
    @staticmethod
    def __formatNumber(number: float, precision: int = 0, locale: str = None):
        # ignore locale for now
        return f"{number:,.{precision}f}"
        