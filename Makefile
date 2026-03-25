.PHONY: help install install-dev test lint format clean security-check security-scan run-example validate-detectors

# Default target
help:
	@echo "AutoPR Lab - Makefile"
	@echo "====================="
	@echo ""
	@echo "Disponibles:"
	@echo "  install       - Instalar el paquete en modo edición"
	@echo "  install-dev   - Instalar dependencias de desarrollo"
	@echo "  test          - Ejecutar tests con cobertura"
	@echo "  lint          - Ejecutar linting (ruff + mypy)"
	@echo "  format        - Formatear código con ruff"
	@echo "  clean         - Limpiar archivos temporales"
	@echo "  security-check- Escaneo de seguridad básico"
	@echo "  security-scan - Escaneo de seguridad completo"
	@echo "  run-example   - Ejecutar ejemplo del decision engine"
	@echo "  validate-detectors - Validar estructura de detectores"
	@echo ""

# Install package in development mode
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev,security]"
	@echo "✅ Dependencias de desarrollo instaladas"

# Run tests with coverage
test:
	@echo "🧪 Ejecutando tests..."
	python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term
	@echo "✅ Tests completados. Ver reporte en htmlcov/index.html"

# Linting with ruff and mypy
lint:
	@echo "🔍 Ejecutando linting..."
	ruff check .
	mypy .
	@echo "✅ Linting completado"

# Format code with ruff
format:
	@echo "📝 Formateando código..."
	ruff format .
	@echo "✅ Código formateado"

# Clean temporary files and build artifacts
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name __pycache__ -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf build/ dist/
	rm -f scan_result.json safety-report.json security-scan.json
	@echo "✅ Limpieza completada"

# Basic security check
security-check:
	@echo "🔒 Ejecitando verificación de seguridad básica..."
	python -m safety scan --short-report
	@echo "✅ Verificación de seguridad completada"

# Full security scan
security-scan:
	@echo "🛡️ Ejecitando escaneo de seguridad completo..."
	python -m safety scan --json --output safety-report.json
	python -m bandit -r . -f json -o bandit-report.json || true
	@echo "✅ Escaneo de seguridad completado"
	@echo "📊 Reportes generados: safety-report.json, bandit-report.json"

# Run example with decision engine
run-example:
	@echo "🤖 Ejecutando ejemplo del decision engine..."
	@if [ -z "$(GITHUB_TOKEN)" ] || [ -z "$(GITHUB_REPOSITORY)" ] || [ -z "$(PR_NUMBER)" ]; then \
		echo "❌ Se requieren variables de entorno:"; \
		echo "   GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER"; \
		echo "   Ejemplo: make run-example GITHUB_TOKEN=xxx GITHUB_REPOSITORY=owner/repo PR_NUMBER=123"; \
		exit 1; \
	fi
	export DRY_RUN="true" && python scripts/decision_engine.py

# Validate all detectors
validate-detectors:
	@echo "🔍 Validando estructura de detectores..."
	python scripts/validate_detectors.py

# Development setup (install + validate)
setup: install-dev validate-detectors
	@echo "🚀 Entorno de desarrollo configurado"

# Pre-commit checks (used by CI)
pre-commit: lint test security-check
	@echo "✅ Verificaciones pre-commit completadas"

# Quick development cycle
dev: format lint test
	@echo "🔄 Ciclo de desarrollo completado"

# Check for outdated dependencies
outdated:
	@echo "📦 Verificando dependencias desactualizadas..."
	pip list --outdated

# Update dependencies
update:
	@echo "⬆️ Actualizando dependencias..."
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -e ".[dev,security]"
	@echo "✅ Dependencias actualizadas"
