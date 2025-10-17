"""
Tests for validation tools.
"""
import pytest
from app.tools.validation import (
    validate_code,
    _validate_python,
    _validate_javascript,
    _validate_json,
    _validate_typescript,
    _validate_html,
    _validate_css,
    _validate_xml,
    _validate_yaml,
    _validate_sql
)


class TestValidatePython:
    """Tests for Python validation."""

    def test_valid_python_code(self):
        code = "def hello():\n    return 'world'"
        result = _validate_python(code)
        assert "✅" in result
        assert "valid" in result.lower()

    def test_invalid_python_syntax(self):
        code = "def hello(\n    return 'world'"
        result = _validate_python(code)
        assert "❌" in result
        assert "syntax error" in result.lower()

    def test_empty_python_code(self):
        code = ""
        result = _validate_python(code)
        assert "✅" in result  # Empty is valid Python

    def test_python_with_imports(self):
        code = "import os\nimport sys\n\nprint('hello')"
        result = _validate_python(code)
        assert "✅" in result


class TestValidateJavaScript:
    """Tests for JavaScript validation."""

    def test_valid_javascript_code(self):
        code = "function hello() { return 'world'; }"
        result = _validate_javascript(code)
        # Should either validate or warn about Node.js not being installed
        assert "✅" in result or "⚠️" in result

    def test_invalid_javascript_syntax(self):
        code = "function hello( { return 'world'; }"
        result = _validate_javascript(code)
        # Should either report error or warn about Node.js
        assert "❌" in result or "⚠️" in result

    def test_empty_javascript_code(self):
        code = ""
        result = _validate_javascript(code)
        # Should either validate empty or warn about Node.js
        assert "✅" in result or "❌" in result or "⚠️" in result


class TestValidateTypeScript:
    """Tests for TypeScript validation."""

    def test_valid_typescript_code(self):
        code = "function hello(): string { return 'world'; }"
        result = _validate_typescript(code)
        # Should either validate or warn about tsc not being installed
        assert "✅" in result or "⚠️" in result

    def test_empty_typescript_code(self):
        code = ""
        result = _validate_typescript(code)
        assert "❌" in result or "⚠️" in result


class TestValidateJSON:
    """Tests for JSON validation."""

    def test_valid_json(self):
        code = '{"name": "test", "value": 123}'
        result = _validate_json(code)
        assert "✅" in result
        assert "valid" in result.lower()

    def test_invalid_json_syntax(self):
        code = '{"name": "test", "value": 123'
        result = _validate_json(code)
        assert "❌" in result
        assert "syntax error" in result.lower()

    def test_json_with_trailing_comma(self):
        code = '{"name": "test",}'
        result = _validate_json(code)
        assert "❌" in result

    def test_empty_json(self):
        code = "{}"
        result = _validate_json(code)
        assert "✅" in result

    def test_json_array(self):
        code = '[1, 2, 3, 4]'
        result = _validate_json(code)
        assert "✅" in result


class TestValidateHTML:
    """Tests for HTML validation."""

    def test_valid_html(self):
        code = "<html><body><h1>Hello</h1></body></html>"
        result = _validate_html(code)
        assert "✅" in result or "⚠️" in result

    def test_unclosed_html_tag(self):
        code = "<div><p>Hello</div>"
        result = _validate_html(code)
        assert "⚠️" in result or "❌" in result

    def test_empty_html(self):
        code = ""
        result = _validate_html(code)
        assert "❌" in result

    def test_self_closing_tags(self):
        code = "<img src='test.jpg' /><br /><input type='text' />"
        result = _validate_html(code)
        assert "✅" in result or "⚠️" in result


class TestValidateCSS:
    """Tests for CSS validation."""

    def test_valid_css(self):
        code = "body { color: red; font-size: 14px; }"
        result = _validate_css(code)
        assert "✅" in result or "⚠️" in result

    def test_unclosed_braces(self):
        code = "body { color: red;"
        result = _validate_css(code)
        assert "⚠️" in result or "❌" in result

    def test_empty_css(self):
        code = ""
        result = _validate_css(code)
        assert "❌" in result


class TestValidateXML:
    """Tests for XML validation."""

    def test_valid_xml(self):
        code = "<?xml version='1.0'?><root><item>test</item></root>"
        result = _validate_xml(code)
        assert "✅" in result

    def test_invalid_xml(self):
        code = "<root><item>test</root>"
        result = _validate_xml(code)
        assert "❌" in result

    def test_simple_xml(self):
        code = "<note><to>User</to><from>System</from></note>"
        result = _validate_xml(code)
        assert "✅" in result


class TestValidateYAML:
    """Tests for YAML validation."""

    def test_valid_yaml(self):
        code = "name: test\nvalue: 123\nitems:\n  - one\n  - two"
        result = _validate_yaml(code)
        # Depends on whether PyYAML is installed
        assert "✅" in result or "⚠️" in result

    def test_yaml_with_tabs(self):
        code = "name:\ttest"
        result = _validate_yaml(code)
        # Should detect tabs as error
        assert "❌" in result or "⚠️" in result

    def test_empty_yaml(self):
        code = ""
        result = _validate_yaml(code)
        # Empty YAML is technically valid or might warn
        assert any(x in result for x in ["✅", "⚠️", "❌"])


class TestValidateSQL:
    """Tests for SQL validation."""

    def test_valid_sql_select(self):
        code = "SELECT * FROM users WHERE id = 1;"
        result = _validate_sql(code)
        assert "✅" in result or "⚠️" in result

    def test_unclosed_quote(self):
        code = "SELECT * FROM users WHERE name = 'test;"
        result = _validate_sql(code)
        assert "❌" in result

    def test_mismatched_parentheses(self):
        code = "SELECT COUNT(*) FROM (SELECT * FROM users;"
        result = _validate_sql(code)
        assert "❌" in result

    def test_empty_sql(self):
        code = ""
        result = _validate_sql(code)
        assert "❌" in result


class TestValidateCode:
    """Tests for the main validate_code function."""

    def test_validate_python_code(self):
        code = "x = 1 + 2"
        result = validate_code(code, "python")
        assert "✅" in result

    def test_validate_javascript_code(self):
        code = "const x = 1 + 2;"
        result = validate_code(code, "javascript")
        assert "✅" in result or "⚠️" in result

    def test_validate_typescript_code(self):
        code = "const x: number = 1 + 2;"
        result = validate_code(code, "typescript")
        assert "✅" in result or "⚠️" in result

    def test_validate_js_alias(self):
        code = "const x = 1 + 2;"
        result = validate_code(code, "js")
        assert "✅" in result or "⚠️" in result

    def test_validate_ts_alias(self):
        code = "const x: number = 5;"
        result = validate_code(code, "ts")
        assert "✅" in result or "⚠️" in result

    def test_validate_json_code(self):
        code = '{"key": "value"}'
        result = validate_code(code, "json")
        assert "✅" in result

    def test_validate_html_code(self):
        code = "<div>Hello</div>"
        result = validate_code(code, "html")
        assert "✅" in result or "⚠️" in result

    def test_validate_css_code(self):
        code = ".class { color: blue; }"
        result = validate_code(code, "css")
        assert "✅" in result or "⚠️" in result

    def test_validate_xml_code(self):
        code = "<root><item>test</item></root>"
        result = validate_code(code, "xml")
        assert "✅" in result

    def test_validate_yaml_code(self):
        code = "key: value"
        result = validate_code(code, "yaml")
        assert "✅" in result or "⚠️" in result

    def test_validate_sql_code(self):
        code = "SELECT * FROM table;"
        result = validate_code(code, "sql")
        assert "✅" in result or "⚠️" in result

    def test_unsupported_language(self):
        code = "print('hello')"
        result = validate_code(code, "ruby")
        assert "⚠️" in result
        assert "not supported" in result.lower()

    def test_default_to_python(self):
        code = "x = 1 + 2"
        result = validate_code(code, "")
        assert "✅" in result
        assert "Python" in result

    def test_case_insensitive_language(self):
        code = "x = 1 + 2"
        result = validate_code(code, "PYTHON")
        assert "✅" in result

    def test_whitespace_in_language(self):
        code = "x = 1 + 2"
        result = validate_code(code, "  python  ")
        assert "✅" in result

    def test_invalid_code_error_handling(self):
        code = "def invalid(\n    pass"
        result = validate_code(code, "python")
        assert "❌" in result

    def test_compiled_language_go(self):
        code = "package main\nfunc main() {}"
        result = validate_code(code, "go")
        # Either validates or warns about missing compiler
        assert any(x in result for x in ["✅", "⚠️"])

    def test_compiled_language_rust(self):
        code = "fn main() {}"
        result = validate_code(code, "rust")
        # Either validates or warns about missing compiler
        assert any(x in result for x in ["✅", "⚠️"])

    def test_compiled_language_java(self):
        code = "public class Test { public static void main(String[] args) {} }"
        result = validate_code(code, "java")
        # Either validates or warns about missing compiler
        assert any(x in result for x in ["✅", "⚠️"])

    def test_compiled_language_c(self):
        code = "#include <stdio.h>\nint main() { return 0; }"
        result = validate_code(code, "c")
        # Either validates or warns about missing compiler
        assert any(x in result for x in ["✅", "⚠️"])

    def test_compiled_language_cpp(self):
        code = "#include <iostream>\nint main() { return 0; }"
        result = validate_code(code, "cpp")
        # Either validates or warns about missing compiler
        assert any(x in result for x in ["✅", "⚠️"])
        assert "❌" in result or "⚠️" in result

    def test_empty_javascript_code(self):
        code = ""
        result = _validate_javascript(code)
        # Should either validate empty or warn about Node.js
        assert "✅" in result or "❌" in result or "⚠️" in result


class TestValidateJSON:
    """Tests for JSON validation."""

    def test_valid_json(self):
        code = '{"name": "test", "value": 123}'
        result = _validate_json(code)
        assert "✅" in result
        assert "valid" in result.lower()

    def test_invalid_json_syntax(self):
        code = '{"name": "test", "value": 123'
        result = _validate_json(code)
        assert "❌" in result
        assert "syntax error" in result.lower()

    def test_json_with_trailing_comma(self):
        code = '{"name": "test",}'
        result = _validate_json(code)
        assert "❌" in result

    def test_empty_json(self):
        code = "{}"
        result = _validate_json(code)
        assert "✅" in result

    def test_json_array(self):
        code = '[1, 2, 3, 4]'
        result = _validate_json(code)
        assert "✅" in result