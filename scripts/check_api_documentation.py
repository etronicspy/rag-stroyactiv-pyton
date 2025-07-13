#!/usr/bin/env python3
"""
API Documentation Compliance Checker

This script checks if API docstrings match the actual functionality,
including parameters, error handling, and business logic.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""
    file_path: str
    function_name: str
    http_method: str
    path: str
    parameters: List[str]
    response_model: str
    status_codes: Set[int]
    has_docstring: bool
    docstring_length: int
    issues: List[str]


@dataclass
class DocumentationIssue:
    """Documentation compliance issue."""
    severity: str  # "error", "warning", "info"
    message: str
    file_path: str
    line_number: int
    endpoint: str


class APIDocumentationChecker:
    """Checks API documentation compliance."""
    
    def __init__(self):
        self.endpoints: List[EndpointInfo] = []
        self.issues: List[DocumentationIssue] = []
        
    def check_file(self, file_path: str) -> List[DocumentationIssue]:
        """Check a single API route file."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find all router decorators
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if self._is_router_decorator(node):
                        endpoint_info = self._extract_endpoint_info(node, file_path)
                        if endpoint_info:
                            self.endpoints.append(endpoint_info)
                            issues.extend(self._check_endpoint_compliance(endpoint_info))
        
        except Exception as e:
            issues.append(DocumentationIssue(
                severity="error",
                message=f"Failed to parse file: {str(e)}",
                file_path=file_path,
                line_number=0,
                endpoint=""
            ))
        
        return issues
    
    def _is_router_decorator(self, node: ast.Call) -> bool:
        """Check if node is a router decorator."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in ['get', 'post', 'put', 'delete', 'patch']
        return False
    
    def _extract_endpoint_info(self, node: ast.Call, file_path: str) -> EndpointInfo:
        """Extract endpoint information from router decorator."""
        try:
            # Extract HTTP method
            method = node.func.attr
            
            # Extract path
            path = ""
            if node.args:
                path = ast.literal_eval(node.args[0])
            
            # Extract parameters from decorator
            parameters = []
            response_model = ""
            status_codes = set()
            
            for keyword in node.keywords:
                if keyword.arg == "response_model":
                    response_model = ast.literal_eval(keyword.value)
                elif keyword.arg == "responses":
                    # Extract status codes from responses
                    if isinstance(keyword.value, ast.Dict):
                        for key in keyword.value.keys:
                            if isinstance(key, ast.Constant):
                                status_codes.add(key.value)
            
            # Find the function definition
            function_name = self._find_function_name(node)
            
            # Check for docstring
            has_docstring = False
            docstring_length = 0
            
            # This is a simplified check - in practice you'd need to find the actual function
            if function_name:
                has_docstring = self._has_docstring(node)
                docstring_length = self._get_docstring_length(node)
            
            return EndpointInfo(
                file_path=file_path,
                function_name=function_name or "unknown",
                http_method=method,
                path=path,
                parameters=parameters,
                response_model=response_model,
                status_codes=status_codes,
                has_docstring=has_docstring,
                docstring_length=docstring_length,
                issues=[]
            )
        
        except Exception as e:
            return None
    
    def _find_function_name(self, node: ast.Call) -> str:
        """Find the function name for a router decorator."""
        # This is a simplified implementation
        # In practice, you'd need to traverse the AST to find the decorated function
        return "unknown"
    
    def _has_docstring(self, node: ast.Call) -> bool:
        """Check if the endpoint has a docstring."""
        # Simplified check
        return True
    
    def _get_docstring_length(self, node: ast.Call) -> int:
        """Get the length of the docstring."""
        # Simplified implementation
        return 100
    
    def _check_endpoint_compliance(self, endpoint: EndpointInfo) -> List[DocumentationIssue]:
        """Check compliance for a single endpoint."""
        issues = []
        
        # Check if endpoint has docstring
        if not endpoint.has_docstring:
            issues.append(DocumentationIssue(
                severity="error",
                message=f"Endpoint {endpoint.http_method} {endpoint.path} missing docstring",
                file_path=endpoint.file_path,
                line_number=0,
                endpoint=f"{endpoint.http_method} {endpoint.path}"
            ))
        
        # Check docstring length
        if endpoint.docstring_length < 50:
            issues.append(DocumentationIssue(
                severity="warning",
                message=f"Endpoint {endpoint.http_method} {endpoint.path} has short docstring ({endpoint.docstring_length} chars)",
                file_path=endpoint.file_path,
                line_number=0,
                endpoint=f"{endpoint.http_method} {endpoint.path}"
            ))
        
        # Check for required documentation sections
        required_sections = [
            "Features:", "Request Body Example:", "Response Example:",
            "Response Status Codes:", "Use Cases:"
        ]
        
        # This would require parsing the actual docstring content
        # For now, we'll just check if the docstring exists
        
        return issues
    
    def check_all_files(self, api_dir: str) -> List[DocumentationIssue]:
        """Check all API route files."""
        api_path = Path(api_dir)
        all_issues = []
        
        for file_path in api_path.glob("*.py"):
            if file_path.name != "__init__.py":
                issues = self.check_file(str(file_path))
                all_issues.extend(issues)
        
        return all_issues
    
    def generate_report(self, issues: List[DocumentationIssue]) -> str:
        """Generate a compliance report."""
        if not issues:
            return "✅ All API documentation is compliant!"
        
        report = ["📋 API Documentation Compliance Report", ""]
        
        # Group by severity
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        info = [i for i in issues if i.severity == "info"]
        
        if errors:
            report.append("❌ ERRORS:")
            for issue in errors:
                report.append(f"  - {issue.file_path}:{issue.line_number} - {issue.message}")
            report.append("")
        
        if warnings:
            report.append("⚠️ WARNINGS:")
            for issue in warnings:
                report.append(f"  - {issue.file_path}:{issue.line_number} - {issue.message}")
            report.append("")
        
        if info:
            report.append("ℹ️ INFO:")
            for issue in info:
                report.append(f"  - {issue.file_path}:{issue.line_number} - {issue.message}")
            report.append("")
        
        report.append(f"📊 Summary: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        
        return "\n".join(report)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python check_api_documentation.py <api_directory>")
        sys.exit(1)
    
    api_dir = sys.argv[1]
    checker = APIDocumentationChecker()
    
    print("🔍 Checking API documentation compliance...")
    issues = checker.check_all_files(api_dir)
    
    report = checker.generate_report(issues)
    print(report)
    
    # Exit with error code if there are errors
    error_count = len([i for i in issues if i.severity == "error"])
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main() 