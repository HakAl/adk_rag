"""
Code validation tools for various programming languages.
"""
import ast
import json
import subprocess
import re
import xml.etree.ElementTree as ET
from typing import Optional

from config import logger


def validate_code(code: str, language: str) -> str:
    """
    Validate code syntax for various programming languages.

    Args:
        code: Code to validate
        language: Programming language (python, javascript, js, json, html, css, xml, yaml, sql, typescript, ts, go, rust, java, c, cpp, c++)

    Returns:
        Validation result with details
    """
    # Default to python if language is empty
    if not language or not language.strip():
        language = "python"

    language = language.lower().strip()
    logger.debug(f"[Tool] validate_code called for {language}")

    try:
        if language == "python":
            return _validate_python(code)
        elif language in ["javascript", "js"]:
            return _validate_javascript(code)
        elif language in ["typescript", "ts"]:
            return _validate_typescript(code)
        elif language == "json":
            return _validate_json(code)
        elif language == "html":
            return _validate_html(code)
        elif language == "css":
            return _validate_css(code)
        elif language == "xml":
            return _validate_xml(code)
        elif language in ["yaml", "yml"]:
            return _validate_yaml(code)
        elif language == "sql":
            return _validate_sql(code)
        elif language == "go":
            return _validate_go(code)
        elif language == "rust":
            return _validate_rust(code)
        elif language == "java":
            return _validate_java(code)
        elif language in ["c", "cpp", "c++"]:
            return _validate_c_cpp(code, language)
        else:
            supported = "python, javascript, typescript, json, html, css, xml, yaml, sql, go, rust, java, c, c++"
            return f"⚠️ Language '{language}' not supported. Supported: {supported}"
    except Exception as e:
        logger.error(f"Code validation error: {e}")
        return f"❌ Validation error: {str(e)}"


def _validate_python(code: str) -> str:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return "✅ Python code syntax is valid."
    except SyntaxError as e:
        return f"❌ Python syntax error on line {e.lineno}: {e.msg}\n  {e.text or ''}"
    except Exception as e:
        return f"❌ Python validation error: {str(e)}"


def _validate_javascript(code: str) -> str:
    """Validate JavaScript code syntax using Node.js if available."""
    try:
        result = subprocess.run(
            ['node', '--check', '-'],
            input=code,
            text=True,
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            return "✅ JavaScript code syntax is valid."
        else:
            return f"❌ JavaScript syntax error:\n{result.stderr}"

    except FileNotFoundError:
        if code.strip():
            return "⚠️ JavaScript validation requires Node.js (not installed). Basic check: code is non-empty."
        return "❌ JavaScript code is empty."
    except subprocess.TimeoutExpired:
        return "❌ JavaScript validation timed out."
    except Exception as e:
        return f"❌ JavaScript validation error: {str(e)}"


def _validate_json(code: str) -> str:
    """Validate JSON syntax."""
    try:
        json.loads(code)
        return "✅ JSON syntax is valid."
    except json.JSONDecodeError as e:
        return f"❌ JSON syntax error at line {e.lineno}, column {e.colno}: {e.msg}"
    except Exception as e:
        return f"❌ JSON validation error: {str(e)}"


def _validate_typescript(code: str) -> str:
    """Validate TypeScript code syntax using tsc if available."""
    try:
        result = subprocess.run(
            ['tsc', '--noEmit', '--stdin'],
            input=code,
            text=True,
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            return "✅ TypeScript code syntax is valid."
        else:
            return f"❌ TypeScript syntax error:\n{result.stderr}"

    except FileNotFoundError:
        if code.strip():
            return "⚠️ TypeScript validation requires tsc (not installed). Basic check: code is non-empty."
        return "❌ TypeScript code is empty."
    except subprocess.TimeoutExpired:
        return "❌ TypeScript validation timed out."
    except Exception as e:
        return f"❌ TypeScript validation error: {str(e)}"


def _validate_html(code: str) -> str:
    """Validate HTML syntax with basic checks."""
    try:
        code = code.strip()
        if not code:
            return "❌ HTML code is empty."

        # Basic checks
        issues = []

        # Check for basic structure
        if not re.search(r'<[^>]+>', code):
            return "⚠️ No HTML tags found in code."

        # Check for unclosed tags (basic)
        opening_tags = re.findall(r'<(\w+)[^/>]*(?<!/)>', code)
        closing_tags = re.findall(r'</(\w+)>', code)

        # Self-closing tags that don't need closing
        self_closing = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'param', 'source', 'track', 'wbr'}

        opening_count = {}
        for tag in opening_tags:
            if tag.lower() not in self_closing:
                opening_count[tag.lower()] = opening_count.get(tag.lower(), 0) + 1

        closing_count = {}
        for tag in closing_tags:
            closing_count[tag.lower()] = closing_count.get(tag.lower(), 0) + 1

        # Check for mismatched tags
        for tag, count in opening_count.items():
            if closing_count.get(tag, 0) < count:
                issues.append(f"Unclosed tag: <{tag}>")
            elif closing_count.get(tag, 0) > count:
                issues.append(f"Extra closing tag: </{tag}>")

        if issues:
            return "⚠️ HTML validation warnings:\n- " + "\n- ".join(issues)

        return "✅ HTML syntax appears valid."

    except Exception as e:
        return f"❌ HTML validation error: {str(e)}"


def _validate_css(code: str) -> str:
    """Validate CSS syntax with basic checks."""
    try:
        code = code.strip()
        if not code:
            return "❌ CSS code is empty."

        issues = []

        # Check for basic CSS structure
        if not re.search(r'[{;}]', code):
            return "⚠️ No CSS syntax found (missing {, }, or ;)."

        # Check for unclosed braces
        open_braces = code.count('{')
        close_braces = code.count('}')

        if open_braces != close_braces:
            issues.append(f"Mismatched braces: {open_braces} opening, {close_braces} closing")

        # Check for basic syntax patterns
        if re.search(r':\s*;', code):
            issues.append("Empty property value found")

        if re.search(r'[^:]\s*{', code):
            # Has selectors and rules
            pass
        else:
            issues.append("No valid CSS selectors found")

        if issues:
            return "⚠️ CSS validation warnings:\n- " + "\n- ".join(issues)

        return "✅ CSS syntax appears valid."

    except Exception as e:
        return f"❌ CSS validation error: {str(e)}"


def _validate_xml(code: str) -> str:
    """Validate XML syntax."""
    try:
        ET.fromstring(code)
        return "✅ XML syntax is valid."
    except ET.ParseError as e:
        return f"❌ XML syntax error at line {e.position[0]}: {e.msg}"
    except Exception as e:
        return f"❌ XML validation error: {str(e)}"


def _validate_yaml(code: str) -> str:
    """Validate YAML syntax."""
    try:
        import yaml
        yaml.safe_load(code)
        return "✅ YAML syntax is valid."
    except yaml.YAMLError as e:
        return f"❌ YAML syntax error: {str(e)}"
    except ImportError:
        # Basic validation without PyYAML
        if not code.strip():
            return "❌ YAML code is empty."

        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for tabs (YAML doesn't allow tabs for indentation)
            if '\t' in line:
                issues.append(f"Line {i}: Tabs not allowed in YAML (use spaces)")

        if issues:
            return "❌ YAML validation errors:\n- " + "\n- ".join(issues)

        return "⚠️ YAML validation requires PyYAML. Basic check: no obvious errors found."
    except Exception as e:
        return f"❌ YAML validation error: {str(e)}"


def _validate_sql(code: str) -> str:
    """Validate SQL syntax with basic checks."""
    try:
        code = code.strip()
        if not code:
            return "❌ SQL code is empty."

        # Basic SQL keyword validation
        sql_keywords = r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN|ON|GROUP|ORDER|BY|HAVING|LIMIT)\b'

        if not re.search(sql_keywords, code, re.IGNORECASE):
            return "⚠️ No SQL keywords found."

        # Check for basic syntax issues
        issues = []

        # Check for unclosed quotes
        single_quotes = code.count("'") - code.count("\\'")
        double_quotes = code.count('"') - code.count('\\"')

        if single_quotes % 2 != 0:
            issues.append("Unclosed single quote")
        if double_quotes % 2 != 0:
            issues.append("Unclosed double quote")

        # Check for unmatched parentheses
        open_paren = code.count('(')
        close_paren = code.count(')')
        if open_paren != close_paren:
            issues.append(f"Mismatched parentheses: {open_paren} opening, {close_paren} closing")

        if issues:
            return "❌ SQL validation errors:\n- " + "\n- ".join(issues)

        return "✅ SQL syntax appears valid."

    except Exception as e:
        return f"❌ SQL validation error: {str(e)}"


def _validate_go(code: str) -> str:
    """Validate Go code syntax using go compiler if available."""
    try:
        # Try using gofmt for syntax validation
        result = subprocess.run(
            ['gofmt', '-e'],
            input=code,
            text=True,
            capture_output=True,
            timeout=5
        )

        if result.stderr:
            return f"❌ Go syntax error:\n{result.stderr}"
        else:
            return "✅ Go code syntax is valid."

    except FileNotFoundError:
        if code.strip():
            return "⚠️ Go validation requires gofmt (not installed). Basic check: code is non-empty."
        return "❌ Go code is empty."
    except subprocess.TimeoutExpired:
        return "❌ Go validation timed out."
    except Exception as e:
        return f"❌ Go validation error: {str(e)}"


def _validate_rust(code: str) -> str:
    """Validate Rust code syntax using rustc if available."""
    try:
        # Use rustc with --crate-type lib for syntax checking
        result = subprocess.run(
            ['rustc', '--crate-type', 'lib', '-', '--error-format=short'],
            input=code,
            text=True,
            capture_output=True,
            timeout=10
        )

        if result.returncode != 0:
            return f"❌ Rust syntax error:\n{result.stderr}"
        else:
            return "✅ Rust code syntax is valid."

    except FileNotFoundError:
        if code.strip():
            return "⚠️ Rust validation requires rustc (not installed). Basic check: code is non-empty."
        return "❌ Rust code is empty."
    except subprocess.TimeoutExpired:
        return "❌ Rust validation timed out."
    except Exception as e:
        return f"❌ Rust validation error: {str(e)}"


def _validate_java(code: str) -> str:
    """Validate Java code syntax using javac if available."""
    try:
        import tempfile
        import os

        # Create a temporary file for the Java code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ['javac', '-Xdiags:compact', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return "✅ Java code syntax is valid."
            else:
                return f"❌ Java syntax error:\n{result.stderr}"
        finally:
            # Clean up temp files
            os.unlink(temp_file)
            class_file = temp_file.replace('.java', '.class')
            if os.path.exists(class_file):
                os.unlink(class_file)

    except FileNotFoundError:
        if code.strip():
            return "⚠️ Java validation requires javac (not installed). Basic check: code is non-empty."
        return "❌ Java code is empty."
    except subprocess.TimeoutExpired:
        return "❌ Java validation timed out."
    except Exception as e:
        return f"❌ Java validation error: {str(e)}"


def _validate_c_cpp(code: str, language: str) -> str:
    """Validate C/C++ code syntax using gcc/g++ if available."""
    try:
        import tempfile
        import os

        # Determine compiler
        if language in ["cpp", "c++"]:
            compiler = 'g++'
            suffix = '.cpp'
        else:
            compiler = 'gcc'
            suffix = '.c'

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                [compiler, '-fsyntax-only', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return f"✅ {language.upper()} code syntax is valid."
            else:
                return f"❌ {language.upper()} syntax error:\n{result.stderr}"
        finally:
            os.unlink(temp_file)

    except FileNotFoundError:
        if code.strip():
            return f"⚠️ {language.upper()} validation requires {compiler} (not installed). Basic check: code is non-empty."
        return f"❌ {language.upper()} code is empty."
    except subprocess.TimeoutExpired:
        return f"❌ {language.upper()} validation timed out."
    except Exception as e:
        return f"❌ {language.upper()} validation error: {str(e)}"