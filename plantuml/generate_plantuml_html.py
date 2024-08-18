import io
import sys
import jinja2
import functools
from plantuml.plantuml_compress import deflate_and_encode

def escape_html(text: str) -> str:
    # Replace special characters with their corresponding HTML entities
    text = text.replace("&", "&amp;")  # Replace '&' first to avoid double replacement
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text
    
def redirect_output_to_html(file_name, title):
    def decorator(func):
        """Decorator to capture stdout output of a function."""
        def wrapper(*args, **kwargs):
            # Redirect stdout to capture print statements
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout

            try:
                res = func(*args, **kwargs)
                generate_html_with_plantuml(new_stdout.getvalue(), file_name, title)
            finally:
                # Reset stdout
                sys.stdout = old_stdout
            return res
        return wrapper
    return decorator


@redirect_output_to_html('output/output1.html', "Test title.")
def generate_plantuml_script():
    """Function that generates and prints PlantUML script."""
    print("""
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response
@enduml
""")

def generate_html_with_plantuml(plantuml_script, output_path = "output.html", title="PlantUML"):
    """Generate HTML with embedded PlantUML diagram and original script."""
    encoded_script = deflate_and_encode(plantuml_script)
    print("encoded_script = ", encoded_script)
    img_url = f"http://www.plantuml.com/plantuml/png/{encoded_script}"
    print("img_url = ", img_url)

    template_str = r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.css" rel="stylesheet" />
        <style>
			code[class*="language-"],
			pre[class*="language-"] {
				text-shadow: none;
				color: white;
				background: #2c2421;
                font-weight: normal !important;
                font-style: normal !important;
                border-radius: 8px; /* Rounded corners */
			}
            pre code.language-plantuml .keyword {
				text-shadow: none;
                color: #007acc; /* Custom color for keywords */
                font-weight: bold;
            }
            pre code.language-plantuml .arrow {
				text-shadow: none;
                color: #d73a49; /* Custom color for arrows */
                font-weight: bold;
            }
            pre code.language-plantuml .directive {
				text-shadow: none;
                color: #22863a; /* Custom color for directives like skinparam, note, etc. */
                font-style: italic;
            }
            pre code.language-plantuml .string {
				text-shadow: none;
                color: #d14; /* Custom color for strings */
            }
            pre code.language-plantuml .comment {
				text-shadow: none;
                color: #999; /* Custom color for comments */
                font-style: italic;
            }
            pre code.language-plantuml .special-char {
				text-shadow: none;
                color: #e36209; /* Custom color for special characters like : { } ( ) */
                font-weight: bold;
            }
            pre code.language-plantuml .symbol {
				text-shadow: none;
                color: #c33ff3; /* Custom color for words starting with # and $ */
            }
        </style>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <h2>Diagram</h2>
        <img src="{{ img_url }}" alt="PlantUML Diagram">
        <h2>Original Script</h2>
        <pre><code class="language-plantuml">{{ plantuml_script }}</code></pre>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script>
            Prism.languages.plantuml = {
                'keyword': /@(?:startuml|enduml)/,
                'arrow': /(?:->|<-|--|~|\.|-|>|<|<#\w+>)/,
                'directive': /\b(?:skinparam|note|agent|interface|component|actor|as)\b/,
                'string': /".*?"/,
                'comment': /'.*$/m,
                'special-char': /[:{}();#]/,
                'symbol': /(?:\$\w+)/
            };
        </script>
    </body>
    </html>
    """

    template = jinja2.Template(template_str)
    html_output = template.render(img_url=img_url, plantuml_script=escape_html(plantuml_script), title=title)

    #output_path = "output.html"
    with open(output_path, "w") as f:
        f.write(html_output)

    print(f"HTML file generated: {output_path}")

