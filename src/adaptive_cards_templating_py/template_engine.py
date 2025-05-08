import re
import json
from collections import defaultdict

class Template:
    EXPRESSION_PATTERN = r'\$\{([^\}]+)\}'

    def __init__(self, template: dict, undefined_field_value_substitution=None):
        self.template = template
        self.undefined_field_value_substitution = undefined_field_value_substitution

    def expand(self, context: dict = None):
        context = context or {}
    
        # Extract root data from context
        root_data = context.get('$root', {})
        
        # Check for inline data in the root
        if '$data' in self.template:
            root_data = self.template['$data']
            
        # Extract host data from context
        host_data = context.get('$host', {})

        root_data = DotDict.wrap_object(root_data or {})
        host_data = DotDict.wrap_object(host_data or {})
        return self._expand(self.template, root_data, root_data, host_data, 0)

    def _expand(self, node, data, root, host, index):
        if isinstance(node, dict):
            if '$data' in node:
                data = self._expand_data(node, data, root, host, index)
                if isinstance(data, list):
                    node_copy = {k: v for k, v in node.items() if k != '$data'}
                    result = []
                    for i, item in enumerate(data):
                        expanded = self._expand(node_copy, item, root, host, i)
                        if expanded is not None:
                            result.append(expanded)
                    return result

            if '$when' in node:
                when_expr = node['$when']
                m = re.fullmatch(self.EXPRESSION_PATTERN, when_expr.strip())
                if not m or not self._eval_expr(m.group(1), data, root, host, index):
                    return None

            expanded_nodes = {}
            for k, v in node.items():
                if k not in ('$data', '$when'):
                    expanded = self._expand(v, data, root, host, index)
                    if expanded is not None:
                        expanded_nodes[k] = expanded
            return expanded_nodes
        elif isinstance(node, list):
            result = []
            for i, item in enumerate(node):
                expanded = self._expand(item, data, root, host, i)
                if isinstance(expanded, list):
                    result.extend(expanded)
                elif expanded is not None:
                    result.append(expanded)
            return result
        elif isinstance(node, str):
            return self._replace_expressions(node, data, root, host, index)
        else:
            return node

    def _expand_data(self, node, data, root, host, index):
        data_expr = node['$data']
        # if $data is exactly one expression, evaluate as expression
        if isinstance(data_expr, str):
            expr_match = re.fullmatch(self.EXPRESSION_PATTERN, data_expr.strip())
            if expr_match:
                return self._eval_expr(expr_match.group(1), data, root, host, index)
            else:
                print (f"\n*** Invalid $data expression: {data_expr}")
                return {}
        else:
            return DotDict.wrap_object(data_expr)

    def _replace_expressions(self, s, data, root, host, index):
        def replacer(match):
            expr = match.group(1).strip()
            val = self._eval_expr(expr, data, root, host, index)
            return str(val) if val is not None else ''
        return re.sub(self.EXPRESSION_PATTERN, replacer, s)
    
    def _sanitize_expr(self, expr):
        # replace $root, $host, $index with valid Python names
        expr = re.sub(r'\$root\b', '_root', expr)
        expr = re.sub(r'\$index\b', '_index', expr)
        expr = re.sub(r'\$host\b', '_host', expr)
        # support for if(,,) and json() functions
        expr = re.sub(r'\bif\s*\(', '_if(', expr)
        expr = re.sub(r'\bjson\s*\(', '_json(', expr)
        # support for boolean literals
        expr = re.sub(r'\bfalse\b', 'False', expr)
        expr = re.sub(r'\btrue\b', 'True', expr)
        # support for logical operators
        expr = re.sub(r'\b&&\b', ' and ', expr)
        expr = re.sub(r'\b\|\|\b', ' or ', expr)
        expr = re.sub(r'\b!\b', ' not ', expr)
        # note: Adaptive expressions prebuilt functions are not supported
        return expr
    
    # supports ${if(expr, a, b)}
    @staticmethod
    def _if_func(condition, true_val, false_val):
        return true_val if condition else false_val
    
    # supports ${json(json_string).property}
    @staticmethod
    def _json_func(json_string):
        return DotDict.wrap_object(json.loads(json_string))

    def _eval_expr(self, expr, data, root, host, index):
        expr_sanitized = self._sanitize_expr(expr.strip())
        local_scope = {}
        if isinstance(data, dict):
            local_scope.update(data)
        local_scope['_root'] = root
        local_scope['_index'] = index
        local_scope['_host'] = host
        local_scope['_if'] = self._if_func
        local_scope['_json'] = self._json_func
        try:
            eval_result = eval(expr_sanitized, {"__builtins__": {}}, defaultdict(lambda: None, local_scope))
            if eval_result is None:
                return f"${{{expr}}}" if self.undefined_field_value_substitution is None else self.undefined_field_value_substitution
            return eval_result
        except Exception:
            print(f"\n*** Error evaluating expression: {expr} (sanitized: {expr_sanitized})")
            return f"${{{expr}}}" # Return the original expression if evaluation fails
        
class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, obj=None):
        obj = obj or {}
        for key, value in obj.items():
            self[key] = self.wrap_object(value)

    @staticmethod
    def wrap_object(obj):
        if isinstance(obj, dict):
            return DotDict(obj)
        elif isinstance(obj, list):
            return LengthList([DotDict.wrap_object(v) for v in obj])
        return obj
    
class LengthList(list):
    @property
    def length(self): return len(self)