"""
Helper module to support multiple LLM providers
Supports: Anthropic Claude, OpenAI GPT-4, and free alternatives
"""
import os
from typing import Dict, List

def get_llm_provider():
    """Determine which LLM provider to use based on available API keys"""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai"
    else:
        raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

async def generate_code_with_llm(brief: str, checks: List[str], attachments: Dict[str, str]) -> str:
    """
    Generate code using available LLM provider
    """
    provider = get_llm_provider()
    
    if provider == "anthropic":
        return await generate_with_anthropic(brief, checks, attachments)
    elif provider == "openai":
        return await generate_with_openai(brief, checks, attachments)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

async def generate_with_anthropic(brief: str, checks: List[str], attachments: Dict[str, str]) -> str:
    """Generate code using Anthropic Claude"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Build attachment context
    attachment_context = ""
    if attachments:
        attachment_context = "\n\nAttachments provided:\n"
        for name, content in attachments.items():
            preview = content[:500] + "..." if len(content) > 500 else content
            attachment_context += f"- {name}:\n```\n{preview}\n```\n"
    
    # Build checks context
    checks_context = "\n".join([f"- {check}" for check in checks])
    
    prompt = f"""Create a complete, production-ready single-page HTML application that satisfies this brief:

{brief}

The application must pass these checks:
{checks_context}

{attachment_context}

Requirements:
1. Create a SINGLE HTML file with embedded CSS and JavaScript
2. Use CDN links for any external libraries (Bootstrap, marked, highlight.js, etc.)
3. Handle all the requirements in the brief
4. Make it work immediately when opened in a browser
5. Include proper error handling
6. Use modern, clean design
7. Make sure all required IDs and elements mentioned in checks exist
8. If attachments are provided, embed them as data URIs or inline in the HTML

Return ONLY the complete HTML code, no explanations."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    html_code = message.content[0].text
    
    # Clean up if LLM wrapped in code blocks
    html_code = clean_code_response(html_code)
    
    return html_code

async def generate_with_openai(brief: str, checks: List[str], attachments: Dict[str, str]) -> str:
    """Generate code using OpenAI GPT-4"""
    from openai import OpenAI
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Build attachment context
    attachment_context = ""
    if attachments:
        attachment_context = "\n\nAttachments provided:\n"
        for name, content in attachments.items():
            preview = content[:500] + "..." if len(content) > 500 else content
            attachment_context += f"- {name}:\n```\n{preview}\n```\n"
    
    # Build checks context
    checks_context = "\n".join([f"- {check}" for check in checks])
    
    prompt = f"""Create a complete, production-ready single-page HTML application that satisfies this brief:

{brief}

The application must pass these checks:
{checks_context}

{attachment_context}

Requirements:
1. Create a SINGLE HTML file with embedded CSS and JavaScript
2. Use CDN links for any external libraries (Bootstrap, marked, highlight.js, etc.)
3. Handle all the requirements in the brief
4. Make it work immediately when opened in a browser
5. Include proper error handling
6. Use modern, clean design
7. Make sure all required IDs and elements mentioned in checks exist
8. If attachments are provided, embed them as data URIs or inline in the HTML

Return ONLY the complete HTML code, no explanations."""

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are an expert web developer. Generate clean, production-ready HTML code."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.7
    )
    
    html_code = response.choices[0].message.content
    
    # Clean up if LLM wrapped in code blocks
    html_code = clean_code_response(html_code)
    
    return html_code

def clean_code_response(code: str) -> str:
    """
    Clean up LLM response to extract just the HTML code
    """
    # Remove markdown code blocks
    if "```html" in code:
        code = code.split("```html")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    # Remove any leading/trailing whitespace
    code = code.strip()
    
    # Ensure it starts with <!DOCTYPE html> or <html>
    if not code.startswith("<!DOCTYPE") and not code.startswith("<html"):
        # Try to find the start of HTML
        if "<!DOCTYPE" in code:
            code = code[code.index("<!DOCTYPE"):]
        elif "<html" in code:
            code = code[code.index("<html"):]
    
    return code

# Update requirements.txt to include:
# openai (if using OpenAI)
# anthropic (if using Anthropic)
