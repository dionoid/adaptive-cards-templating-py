import re
from collections import defaultdict
from .prebuilt_functions import PrebuiltFunctions
from .dot_dict import DotDict

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
        # replace $data, $root, $host, $index with valid Python names
        expr = re.sub(r'\$data\b', '_data', expr)
        expr = re.sub(r'\$root\b', '_root', expr)
        expr = re.sub(r'\$index\b', '_index', expr)
        expr = re.sub(r'\$host\b', '_host', expr)
        # support for boolean literals
        expr = re.sub(r'\bfalse\b', 'False', expr)
        expr = re.sub(r'\btrue\b', 'True', expr)
        # support for logical operators
        expr = re.sub(r'\b&&\b', ' and ', expr)
        expr = re.sub(r'\b\|\|\b', ' or ', expr)
        expr = re.sub(r'\b!\b', ' not ', expr)
        # santize Adaptive expressions prebuilt functions (although most are not supported)
        expr = PrebuiltFunctions.sanitize_expr(expr)
        return expr

    def _eval_expr(self, expr, data, root, host, index):
        expr_sanitized = self._sanitize_expr(expr.strip())
        local_scope = {}
        # if data is a dictionary, expand its keys to local scope
        if isinstance(data, dict):
            local_scope.update(data)
        local_scope['_data'] = data
        local_scope['_root'] = root
        local_scope['_index'] = index
        local_scope['_host'] = host
        # Add prebuilt functions to local_scope
        PrebuiltFunctions.add_functions_to_scope(local_scope)

        try:
            eval_result = eval(expr_sanitized, {"__builtins__": {}}, defaultdict(lambda: None, local_scope))
            if eval_result is None:
                return f"${{{expr}}}" if self.undefined_field_value_substitution else self.undefined_field_value_substitution
            return eval_result
        except Exception:
            print(f"\n*** Error evaluating expression: {expr} (sanitized: {expr_sanitized})")
            return f"${{{expr}}}" # Return the original expression if evaluation fails
        
