# Arquitectura DevSecOps: AutoPR-Lab

El proyecto AutoPR-Lab utiliza una arquitectura de doble entorno para separar la **Zona de Laboratorio Privado (GitLab)** de la **Zona de Portafolio Público (GitHub)**. Esta estrategia asegura que los tests internos, las configuraciones sensibles y el código núcleo permanezcan completamente privados, mientras que una versión sanitizada se expone públicamente.

## Flujo de Publicación (GitLab → GitHub)

```mermaid
sequenceDiagram
    participant Dev as Desarrollador
    participant GitLab as GitLab (Privado)
    participant Script as publish_public.ps1
    participant GitHub as GitHub (Público)

    Dev->>GitLab: 1. Desarrolla features (tests, docs, features)
    GitLab->>GitLab: 2. CI/CD (Ruff, Pytest, Bandit, Safety)
    Dev->>Script: 3. Ejecuta publish_public.ps1 (rama main)
    activate Script
    Script->>Script: 4. Crea rama temporal 'public'
    Script->>Script: 5. git rm -r tests/, configs/, scripts/, src/core/
    Script->>GitHub: 6. Push forzado (public -> main)
    deactivate Script
    GitHub-->>Dev: 7. Portafolio Público Actualizado y Sanitizado
```
