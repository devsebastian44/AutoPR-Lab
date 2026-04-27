# Arquitectura DevSecOps: AutoPR-Lab

El proyecto AutoPR-Lab está diseñado de forma nativa para GitHub. Utiliza GitHub Actions para automatizar el análisis de Pull Requests y CI/CD, asegurando una integración continua eficiente y segura.

## Flujo de Trabajo (GitHub)

```mermaid
sequenceDiagram
    participant Dev as Desarrollador
    participant GitHub as GitHub

    Dev->>GitHub: 1. Desarrolla features y crea PR
    GitHub->>GitHub: 2. Ejecuta CI/CD (Ruff, Pytest, Bandit, Safety)
    GitHub->>GitHub: 3. Ejecuta AutoPR Scanner
    GitHub-->>Dev: 4. Resultados de revisión automáticos
```
