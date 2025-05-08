# Adaptive Cards Templating for Python

This library largely implements the JSON-to-JSON Adaptive Cards Template language for Python. It allows you to dynamically expand Adaptive Card templates using data and host-specific information.

## Features

- Supports most standard features of the Adaptive Cards Template language.
- Inline data expansion with `$data`.
- Conditional rendering with `$when`.
- Expression evaluation using `${}` syntax.
- Custom functions like `if()` and `json()`.
- Supports `$root`, `$host`, and `$index` for advanced templating.

## Currently unsupported

- Adaptive expressions prebuilt functions.

## Installation

To install the package, use:

```bash
pip install adaptive-cards-templating-py
```

## Usage

Here's a quick example of how to use the library:

```python
import json
from adaptive_cards_templating_py import Template

# Define a template
template_json = {
    "type": "AdaptiveCard",
    "body": [
        {
            "type": "TextBlock",
            "text": "${message}"
        }
    ]
}

# Create a Template instance
template = Template(template_json)

# Expand the template with data
data = {
    "$root": {
        "message": "Hello, Adaptive Cards!"
    }
}
card = template.expand(data)

# Pretty-print the card
print(json.dumps(card, indent=2))
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write tests for your changes.
4. Commit your changes and push the branch.
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.