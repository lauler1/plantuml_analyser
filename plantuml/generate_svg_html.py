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
    
def redirect_svg_output_to_html(file_name, title="SVG Example", description="To be defined."):
    """
    This ia a decorator to create a HTML using the SVG model instead of plantuml.
    file_name: The output HTML file.
    title: A title to the HTML file.
    description: A description to the HTML file. It can use HTML tags.
    """
    def decorator(func):
        """Decorator to capture stdout output of a function."""
        def wrapper(*args, **kwargs):
            # Redirect stdout to capture print statements
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout

            try:
                res = func(*args, **kwargs)
                generate_html_with_svg(new_stdout.getvalue(), file_name, title, description)
            finally:
                # Reset stdout
                sys.stdout = old_stdout
            return res
        return wrapper
    return decorator


# @redirect_svg_output_to_html('output/output1.html', "Test title.")
# def generate_plantuml_script():
    # """Function that generates and prints PlantUML script."""
    # print("""
# @startuml
# Alice -> Bob: Authentication Request
# Bob --> Alice: Authentication Response
# @enduml
# """)

def generate_html_with_svg(svg_script, output_path = "output.html", title="", description=""):
    """Generate HTML with embedded SVG diagram and original script."""

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
{{ svg_script }}
        <details>
            <summary>Show/Hide SVG Code</summary>
                <pre><code class="language-svg">{{ html_svg_script }}</code></pre>
        </details>    
        <h2>Description</h2>
        {{ description }}
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
    html_output = template.render(svg_script=svg_script, html_svg_script=escape_html(svg_script), title=title, description=description)

    #output_path = "output.html"
    with open(output_path, "w") as f:
        f.write(html_output)

    print(f"HTML file generated: {output_path}")

