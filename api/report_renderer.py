"""HTML report renderer for scan results."""

from typing import List
from jinja2 import Template
from .scanner_models import Scan, Finding


def render_scan_report(scan: Scan, findings: List[Finding]) -> str:
    """Render scan report as HTML."""
    
    template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaultSentinel Scan Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <h1 class="text-2xl font-bold text-gray-900">VaultSentinel</h1>
                        </div>
                    </div>
                    <div class="text-sm text-gray-500">
                        Scan Report
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Scan Overview -->
            <div class="bg-white rounded-lg shadow-sm border mb-8">
                <div class="px-6 py-4 border-b">
                    <h2 class="text-lg font-semibold text-gray-900">Scan Overview</h2>
                </div>
                <div class="px-6 py-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Repository</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ scan.repo_url }}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Branch</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ scan.branch }}</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Scan Duration</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ "%.2f"|format(scan.duration_ms / 1000) }}s</dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Files Scanned</dt>
                            <dd class="mt-1 text-sm text-gray-900">{{ scan.scanned_files }}</dd>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Risk Score Gauge -->
            <div class="bg-white rounded-lg shadow-sm border mb-8">
                <div class="px-6 py-4 border-b">
                    <h2 class="text-lg font-semibold text-gray-900">Risk Assessment</h2>
                </div>
                <div class="px-6 py-4">
                    <div class="flex items-center justify-center">
                        <div class="relative w-32 h-32">
                            <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="40" stroke="#e5e7eb" stroke-width="8" fill="none"/>
                                <circle cx="50" cy="50" r="40" stroke="{% if scan.risk_score >= 80 %}#dc2626{% elif scan.risk_score >= 60 %}#ea580c{% elif scan.risk_score >= 40 %}#d97706{% else %}#16a34a{% endif %}" 
                                        stroke-width="8" fill="none" 
                                        stroke-dasharray="{{ scan.risk_score * 2.51 }}" 
                                        stroke-dashoffset="0" 
                                        stroke-linecap="round"/>
                            </svg>
                            <div class="absolute inset-0 flex items-center justify-center">
                                <span class="text-2xl font-bold text-gray-900">{{ "%.1f"|format(scan.risk_score) }}</span>
                            </div>
                        </div>
                        <div class="ml-6">
                            <h3 class="text-lg font-semibold text-gray-900">Risk Score</h3>
                            <p class="text-sm text-gray-500">
                                {% if scan.risk_score >= 80 %}
                                    Critical risk level
                                {% elif scan.risk_score >= 60 %}
                                    High risk level
                                {% elif scan.risk_score >= 40 %}
                                    Medium risk level
                                {% else %}
                                    Low risk level
                                {% endif %}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI Tiles -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                                <span class="text-red-600 font-semibold text-sm">C</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Critical</p>
                            <p class="text-2xl font-semibold text-gray-900">{{ findings|selectattr('severity', 'equalto', 'CRITICAL')|list|length }}</p>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                                <span class="text-orange-600 font-semibold text-sm">H</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">High</p>
                            <p class="text-2xl font-semibold text-gray-900">{{ findings|selectattr('severity', 'equalto', 'HIGH')|list|length }}</p>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                                <span class="text-yellow-600 font-semibold text-sm">M</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Medium</p>
                            <p class="text-2xl font-semibold text-gray-900">{{ findings|selectattr('severity', 'equalto', 'MEDIUM')|list|length }}</p>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                                <span class="text-green-600 font-semibold text-sm">L</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <p class="text-sm font-medium text-gray-500">Low</p>
                            <p class="text-2xl font-semibold text-gray-900">{{ findings|selectattr('severity', 'equalto', 'LOW')|list|length }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Findings by Severity -->
            {% for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] %}
            {% set severity_findings = findings|selectattr('severity', 'equalto', severity)|list %}
            {% if severity_findings %}
            <div class="bg-white rounded-lg shadow-sm border mb-8">
                <div class="px-6 py-4 border-b">
                    <h2 class="text-lg font-semibold text-gray-900 flex items-center">
                        <span class="w-3 h-3 rounded-full mr-3 
                            {% if severity == 'CRITICAL' %}bg-red-500
                            {% elif severity == 'HIGH' %}bg-orange-500
                            {% elif severity == 'MEDIUM' %}bg-yellow-500
                            {% else %}bg-green-500{% endif %}"></span>
                        {{ severity }} ({{ severity_findings|length }})
                    </h2>
                </div>
                <div class="divide-y divide-gray-200">
                    {% for finding in severity_findings %}
                    <div class="px-6 py-4">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center">
                                    <h3 class="text-sm font-medium text-gray-900">{{ finding.type|title }}</h3>
                                    <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                        {% if finding.severity == 'CRITICAL' %}bg-red-100 text-red-800
                                        {% elif finding.severity == 'HIGH' %}bg-orange-100 text-orange-800
                                        {% elif finding.severity == 'MEDIUM' %}bg-yellow-100 text-yellow-800
                                        {% else %}bg-green-100 text-green-800{% endif %}">
                                        {{ finding.severity }}
                                    </span>
                                    <span class="ml-2 text-xs text-gray-500">Confidence: {{ "%.1f"|format(finding.confidence * 100) }}%</span>
                                </div>
                                <p class="mt-1 text-sm text-gray-600">{{ finding.description }}</p>
                                <p class="mt-2 text-sm text-gray-500">
                                    <span class="font-medium">File:</span> {{ finding.file_path }}:{{ finding.start_line }}
                                </p>
                                {% if finding.remediation_text %}
                                <div class="mt-3 p-3 bg-blue-50 rounded-md">
                                    <h4 class="text-sm font-medium text-blue-900">Remediation</h4>
                                    <p class="mt-1 text-sm text-blue-800">{{ finding.remediation_text }}</p>
                                </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% endfor %}

            <!-- Actions -->
            <div class="bg-white rounded-lg shadow-sm border">
                <div class="px-6 py-4 border-b">
                    <h2 class="text-lg font-semibold text-gray-900">Actions</h2>
                </div>
                <div class="px-6 py-4">
                    <div class="flex flex-wrap gap-4">
                        <button onclick="downloadPDF()" class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            Download PDF
                        </button>
                        <button onclick="downloadSARIF()" class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            Download SARIF
                        </button>
                        <button onclick="copyPRBody()" class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            Copy PR Body
                        </button>
                        <button onclick="copyCommands()" class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            Copy Commands
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function downloadPDF() {
            // Implement PDF download
            alert('PDF download functionality would be implemented here');
        }

        function downloadSARIF() {
            // Implement SARIF download
            alert('SARIF download functionality would be implemented here');
        }

        function copyPRBody() {
            // Implement PR body copy
            alert('PR body copy functionality would be implemented here');
        }

        function copyCommands() {
            // Implement commands copy
            alert('Commands copy functionality would be implemented here');
        }
    </script>
</body>
</html>
    """)
    
    return template.render(scan=scan, findings=findings)
