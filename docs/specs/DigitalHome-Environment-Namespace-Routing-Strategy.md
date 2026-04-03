# DigitalHome.Cloud

# Environment Namespace Routing Strategy

------------------------------------------------------------------------

# 1. Objective

Ensure deterministic navigation between applications while:

-   Preserving environment context
-   Avoiding accidental cross-environment jumps
-   Supporting local development
-   Supporting stage validation
-   Supporting production isolation

Core principle:

Always stay in the same namespace.

------------------------------------------------------------------------

# 2. Supported Namespaces

DigitalHome.Cloud has three environments:

  Environment   Namespace Pattern   Purpose
  ------------- ------------------- ---------------------------
  DEV           localhost:800x      Local development
  STAGE         stage-\*            Pre-production validation
  PROD          no prefix           Production

------------------------------------------------------------------------

# 3. Application Mapping

## Portal

-   DEV: localhost:8000
-   STAGE: stage-portal.digitalhome.cloud
-   PROD: portal.digitalhome.cloud

## Designer

-   DEV: localhost:8001
-   STAGE: stage-designer.digitalhome.cloud
-   PROD: designer.digitalhome.cloud

## Modeler

-   DEV: localhost:8002
-   STAGE: stage-modeler.digitalhome.cloud
-   PROD: modeler.digitalhome.cloud

------------------------------------------------------------------------

# 4. Core Routing Rule

When navigating between applications:

1.  Detect current namespace.
2.  Replace only the application segment.
3.  Preserve environment prefix.

------------------------------------------------------------------------

# 5. Routing Examples

Example --- Stage to Stage

Current: stage-designer.digitalhome.cloud

Target: stage-modeler.digitalhome.cloud

------------------------------------------------------------------------

Example --- Local to Local

Current: localhost:8001

Target: localhost:8000

------------------------------------------------------------------------

Example --- Production to Production

Current: designer.digitalhome.cloud

Target: portal.digitalhome.cloud

------------------------------------------------------------------------

# 6. Forbidden Behavior

The system must NEVER:

-   Jump from stage-\* to production
-   Jump from localhost to stage
-   Jump from production to stage
-   Hardcode target URLs

------------------------------------------------------------------------

# 7. Implementation Logic (Conceptual)

Pseudo-logic:

IF hostname starts with "localhost" use localhost mapping ELSE IF
hostname starts with "stage-" use stage mapping ELSE use production
mapping

Only the app name changes, not the namespace.

------------------------------------------------------------------------

# 8. Architectural Rationale

This rule ensures:

-   Clear separation of environments
-   No accidental data cross-contamination
-   Predictable UX behavior
-   Safe testing workflows
-   Alignment with DarkFactory isolation principles

------------------------------------------------------------------------

# 9. Design Principle

Environment is a first-class architectural dimension.

Navigation must respect it.

------------------------------------------------------------------------

End of Environment Namespace Routing Strategy
