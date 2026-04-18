import os
import re
import streamlit as st
import streamlit.components.v1 as components

def render_mermaid(code: str, key: str):
    """
    Renders a Mermaid diagram with enhanced error handling and theme support.
    """
    try:
        # Resolve the local path to mermaid.min.js
        js_path = os.path.join(os.path.dirname(__file__), "..", "mermaid.min.js")
        mermaid_js = ""
        if os.path.exists(js_path):
            try:
                with open(js_path, "r") as f:
                    mermaid_js = f.read()
            except Exception:
                pass
        
        # If local JS fails, we'll use a CDN script tag
        script_block = f"<script>{mermaid_js}</script>" if mermaid_js else '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>'
        
        html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                {script_block}
                <style>
                    body {{ margin: 0; background-color: transparent; }}
                    #container {{ 
                        background: #1e1e1e; 
                        padding: 15px; 
                        border-radius: 8px; 
                        border: 1px solid #333;
                        display: flex;
                        justify-content: center;
                    }}
                    .error-box {{
                        color: #ff4b4b;
                        background: #262730;
                        padding: 15px;
                        border-radius: 5px;
                        font-family: monospace;
                    }}
                </style>
            </head>
            <body>
                <div id="container">
                    <div id="mermaid-{key}" class="mermaid">
                        {code}
                    </div>
                </div>
                <script>
                    try {{
                        mermaid.initialize({{ 
                            startOnLoad: true, 
                            theme: 'dark',
                            securityLevel: 'loose',
                            fontFamily: 'Inter, system-ui, sans-serif'
                        }});
                        mermaid.init(undefined, document.getElementById('mermaid-{key}'));
                    }} catch (e) {{
                        console.error('Mermaid render failed:', e);
                        document.getElementById('container').innerHTML = '<div class="error-box"><b>Diagram Rendering Error:</b><br>' + e.message + '</div>';
                    }}
                </script>
            </body>
            </html>
        """
        components.html(html_code, height=500, scrolling=True)
    except Exception as e:
        st.error(f"Critical error in diagram component: {e}")
        st.code(code, language="mermaid")

def display_enriched_report(report_text: str):
    """
    Parses a markdown report and renders Mermaid blocks using the local component.
    """
    # Split by mermaid code blocks
    parts = re.split(r"(```mermaid\s*\n[\s\S]*?\n```)", report_text)
    
    for i, part in enumerate(parts):
        if part.strip().startswith("```mermaid"):
            # Extract content between backticks
            code = re.sub(r"^```mermaid\s*\n|```$", "", part, flags=re.DOTALL).strip()
            render_mermaid(code, key=f"diag-{i}")
        else:
            if part.strip():
                st.markdown(part)
