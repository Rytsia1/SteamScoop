# SteamScoop Implementation Roadmap

**Document:** IMPLEMENTATION_ROADMAP.md\
**Version:** 1.0\
**Status:** Baseline implementation plan\
**Product:** SteamScoop --- Understand Games Through Data

------------------------------------------------------------------------

## 1. Purpose

This document defines a practical implementation sequence for
SteamScoop, including milestones, task breakdowns, dependencies,
development order, and Definition of Done (DoD).

It translates the product and engineering specifications into an
executable delivery plan for an MVP, followed by controlled post-MVP
improvements.

The roadmap is based on the current project baseline:

-   `SRS.md`
-   `SYSTEM_DESIGN.md`
-   `DATABASE_DESIGN.md`
-   `ML_SPECIFICATION.md`
-   `API_SPECIFICATION.md`
-   `CODING_STANDARDS.md`
-   `TESTING_STRATEGY.md`

**UI/UX documentation note:** `UI_UX_GUIDELINES.md` was not provided.
This roadmap does not assume that a finalized design system, wireframe
set, or interaction specification already exists. UI/UX discovery and
definition are therefore included as an explicit early task. Frontend
implementation may begin with agreed structural foundations, but visual
polish and detailed interaction behavior should not be treated as
finalized until the missing design guidance is created and approved.

## 2. Product and Delivery Principles

### 2.1 MVP objective

Deliver a usable public game-intelligence platform that allows users to:

1.  Discover indexed Steam games.
2.  Inspect game-level review and sentiment analytics.
3.  Explore review trends, aspects, and topics where those capabilities
    pass their ML release gates.
4.  Compare supported games using consistent metric definitions.
5.  Understand collection scope, model provenance, and analytical
    limitations.
6.  Use optional authenticated research workspaces and controlled
    exports if these features fit the agreed MVP capacity.

The MVP must prioritize correctness, traceability, and transparent
limitations over the number of features.

### 2.2 Implementation principles

-   Build a modular monolith with independent background workers.
-   Keep PostgreSQL as the authoritative store for application data,
    ingestion jobs, and checkpoints.
-   Use Redis for queue transport and optional caching, not as the only
    durable record of job progress.
-   Isolate Steam API behavior behind a dedicated adapter.
-   Keep ingestion independent of public browsing requests.
-   Version ML models, taxonomies, and prediction outputs.
-   Build vertical slices that can be tested end to end.
-   Do not introduce microservices, Kubernetes, Kafka, Spark,
    Elasticsearch, or other deferred infrastructure without a
    demonstrated requirement.
-   Treat UI/UX definition as a project dependency, not an informal
    implementation detail.

## 3. Roadmap Overview

`<escape>`{=html} Milestone 0 --- Project Alignment and UI/UX Definition
Milestone 1 --- Repository and Development Foundation Milestone 2 ---
Database and Core Backend Milestone 3 --- Steam Integration and Data
Ingestion Milestone 4 --- ML and Analytics Pipeline Milestone 5 ---
Public API and Frontend Experience Milestone 6 --- Research Workspace
and Export Milestone 7 --- Hardening, Acceptance, and MVP Release
Milestone 8 --- Post-MVP Improvements `</escape>`{=html}

Milestones may overlap when interfaces are stable, but their
dependencies must be respected. For example, frontend page scaffolding
can proceed while ingestion is being implemented, but production
analytics screens require stable API contracts and seeded data.

## 4. Milestones and Task Breakdown

## Milestone 0 --- Project Alignment and UI/UX Definition

**Objective:** Resolve product and design decisions that would otherwise
create rework during implementation.

**Deliverables:** - Confirmed MVP scope. - Initial navigation and
information architecture. - UI/UX guideline document. - Wireframes for
critical user journeys. - Agreed visual and interaction patterns. -
Prioritized implementation backlog.

### Tasks

  -----------------------------------------------------------------------------
  ID                Task              Description             Priority
  ----------------- ----------------- ----------------------- -----------------
  M0-01             Review product    Reconcile SRS, System   Critical
                    specifications    Design, Database        
                                      Design, ML              
                                      Specification, API      
                                      Specification, Coding   
                                      Standards, and Testing  
                                      Strategy                

  M0-02             Confirm MVP       Decide which modules    Critical
                    boundary          are required for first  
                                      public release and      
                                      which are deferred      

  M0-03             Define            Define navigation, page High
                    information       hierarchy, and public   
                    architecture      versus authenticated    
                                      areas                   

  M0-04             Define design     Establish typography,   High
                    foundations       spacing, color tokens,  
                                      responsive breakpoints, 
                                      chart conventions, and  
                                      component behavior      

  M0-05             Wireframe core    Cover home/dashboard,   High
                    pages             game explorer, game     
                                      overview, review        
                                      explorer, comparison,   
                                      methodology, and        
                                      workspace if in MVP     

  M0-06             Define chart and  Specify loading, empty, Critical
                    data states       partial-data, error,    
                                      unavailable, and        
                                      stale-data states       

  M0-07             Accessibility     Define keyboard, focus, High
                    baseline          contrast, labels, and   
                                      chart accessibility     
                                      expectations            

  M0-08             Approve UI/UX     Review and approve      High
                    baseline          `UI_UX_GUIDELINES.md`   
                                      and critical wireframes 
  -----------------------------------------------------------------------------

**Dependencies:** Existing product and technical specifications.

**Exit criteria:** - MVP features and deferred features are explicit. -
Critical user journeys are documented. - `UI_UX_GUIDELINES.md` exists or
a documented interim design decision is approved. - Core page wireframes
and analytical chart conventions are reviewed.

**Important sequencing note:** Backend foundation work can start before
all visual details are finalized. However, frontend implementation
beyond reusable scaffolding should use approved wireframes and
documented states.

## Milestone 1 --- Repository and Development Foundation

**Objective:** Establish a repeatable development environment and
automated quality checks.

**Deliverables:** - Monorepo structure. - Backend and frontend
applications bootstrapped. - Docker Compose development environment. -
CI pipeline. - Environment and configuration conventions.

### Tasks

  ------------------------------------------------------------------------
  ID                Task               Description       Priority
  ----------------- ------------------ ----------------- -----------------
  M1-01             Create repository  Set up            Critical
                    structure          `apps/api`,       
                                       `apps/web`, `ml`, 
                                       `infra`, `docs`,  
                                       and scripts       

  M1-02             Initialize FastAPI Add application   Critical
                    application        factory,          
                                       settings, router  
                                       registration, and 
                                       health endpoint   

  M1-03             Initialize React   Set up React,     Critical
                    application        TypeScript strict 
                                       mode, Vite,       
                                       Tailwind CSS, and 
                                       routing           

  M1-04             Configure code     Configure Ruff,   High
                    quality tools      mypy, ESLint,     
                                       TypeScript, and   
                                       test runners      

  M1-05             Add Docker Compose Configure local   Critical
                                       PostgreSQL and    
                                       Redis services    

  M1-06             Configure          Add validated     Critical
                    environment        settings and safe 
                    variables          `.env.example`    
                                       files             

  M1-07             Add CI workflow    Run lint, type    Critical
                                       checks, unit      
                                       tests, and        
                                       frontend build on 
                                       pull requests     

  M1-08             Add application    Configure         High
                    logging            structured logs   
                                       with request/job  
                                       correlation       
                                       identifiers       

  M1-09             Add                Distinguish       High
                    health/readiness   process liveness  
                    checks             from dependency   
                                       readiness         

  M1-10             Add developer      Document setup,   Medium
                    documentation      commands,         
                                       configuration,    
                                       and               
                                       troubleshooting   
  ------------------------------------------------------------------------

**Dependencies:** Milestone 0 decisions for repository naming and
initial application boundaries.

**Exit criteria:** - A new developer can start the stack using
documented steps. - API and frontend start locally. - PostgreSQL and
Redis are reachable. - CI runs successfully on a clean checkout. - No
secrets are committed.

## Milestone 2 --- Database and Core Backend

**Objective:** Implement the persistent data model and backend
foundations required by all later modules.

**Deliverables:** - PostgreSQL schema and migrations. - SQLAlchemy
models and repositories. - Core domain services. - Authentication and
role foundations if accounts are included in MVP. - Database integration
tests.

### Tasks

  -----------------------------------------------------------------------
  ID                Task              Description       Priority
  ----------------- ----------------- ----------------- -----------------
  M2-01             Implement         Configure engine, Critical
                    SQLAlchemy base   session           
                    and session       lifecycle, and    
                    management        transaction       
                                      boundaries        

  M2-02             Implement Alembic Establish         Critical
                                      migration         
                                      configuration and 
                                      migration         
                                      workflow          

  M2-03             Create core       Implement games   Critical
                    catalog tables    and related       
                                      metadata tables   

  M2-04             Create review     Implement         Critical
                    tables            reviews,          
                                      uniqueness,       
                                      indexes, and      
                                      required          
                                      constraints       

  M2-05             Create ML         Implement model   High
                    metadata tables   versions,         
                                      predictions,      
                                      aspects, topics,  
                                      and provenance    
                                      relationships     

  M2-06             Create ingestion  Implement jobs,   Critical
                    operation tables  batches,          
                                      checkpoints, and  
                                      pipeline runs     

  M2-07             Create analytics  Implement         High
                    tables            game-level        
                                      aggregate storage 
                                      and model-version 
                                      attribution       

  M2-08             Create identity   Implement users,  High
                    and access tables roles,            
                                      memberships, and  
                                      audit logs if     
                                      accounts are in   
                                      MVP               

  M2-09             Implement         Add query and     Critical
                    repository layer  persistence       
                                      methods without   
                                      embedding         
                                      business rules in 
                                      route handlers    

  M2-10             Implement domain  Add game, review, Critical
                    services          access-control,   
                                      and analytics     
                                      domain logic      

  M2-11             Add database      Verify            Critical
                    integration tests constraints,      
                                      upserts,          
                                      transactions, and 
                                      migrations        

  M2-12             Seed development  Create            High
                    fixtures          deterministic     
                                      games, reviews,   
                                      predictions, and  
                                      users for local   
                                      development       
  -----------------------------------------------------------------------

**Dependencies:** Milestone 1.

**Exit criteria:** - Migrations build the schema from an empty
database. - Constraints and indexes match the database design. - Review
uniqueness is enforced by `(game_id, steam_review_id)`. - Database
transactions preserve critical ingestion invariants. - Repositories and
services have automated tests. - Seed data can be loaded repeatedly
without unintended duplication.

## Milestone 3 --- Steam Integration and Data Ingestion

**Objective:** Collect and maintain review data using a controlled,
recoverable process.

**Deliverables:** - Steam API adapter. - Historical sample collection. -
Incremental update workflow. - Celery worker queues and scheduler. -
Recovery and monitoring behavior.

### Tasks

  -----------------------------------------------------------------------------------------------
  ID                Task              Description                               Priority
  ----------------- ----------------- ----------------------------------------- -----------------
  M3-01             Implement Steam   Isolate Steam request construction,       Critical
                    adapter interface response parsing, and transport behavior  

  M3-02             Implement current Use                                       Critical
                    review API        `IUserReviewsService/GetAppReviews/v1/`   
                    request           with the documented `input_json` payload  

  M3-03             Implement cursor  Support returned cursor continuation and  Critical
                    pagination        terminal-page handling                    

  M3-04             Implement         Convert source payloads into the internal Critical
                    response          review schema                             
                    normalization                                               

  M3-05             Implement         Apply the approved sample policy and      High
                    historical        temporal bucket strategy                  
                    sampling                                                    

  M3-06             Implement         Use the configured updated-review filter  Critical
                    incremental       and overlap policy                        
                    synchronization                                             

  M3-07             Implement         Upsert using `(game_id, steam_review_id)` Critical
                    idempotent                                                  
                    persistence                                                 

  M3-08             Implement atomic  Commit review records, batch accounting,  Critical
                    page processing   and checkpoint together                   

  M3-09             Implement Celery  Configure ingestion, NLP, aggregation,    High
                    queues            export, and maintenance routing as needed 

  M3-10             Implement retry   Handle transient failures, rate limits,   Critical
                    policy            and bounded backoff                       

  M3-11             Implement weekly  Configure the approved weekly collection  High
                    scheduler         schedule                                  

  M3-12             Implement         Reconstruct or resume incomplete work     High
                    recovery scan     using PostgreSQL state                    

  M3-13             Implement         Track job state, records processed,       High
                    ingestion         failures, duration, and retry count       
                    observability                                               

  M3-14             Add adapter and   Cover fixtures, pagination, interruption, Critical
                    worker tests      duplicate delivery, and recovery          
  -----------------------------------------------------------------------------------------------

**Dependencies:** Milestone 2. The adapter can be prototyped earlier,
but durable ingestion requires the database and job-state model.

**Exit criteria:** - Historical sampling can complete for a seeded
target game. - Incremental synchronization can resume from persisted
state. - Repeated pages or task deliveries do not create duplicate
logical reviews. - HTTP 429 and transient failures are handled without
unbounded retries. - Checkpoints and watermarks advance only after
successful durable commits. - Public browsing requests do not trigger
unbounded collection.

## Milestone 4 --- ML and Analytics Pipeline

**Objective:** Transform collected reviews into versioned, evaluated,
and queryable intelligence.

**Deliverables:** - Data preparation pipeline. - Baseline sentiment
model. - Evaluation report and model registry workflow. - Aspect/topic
capabilities according to MVP scope. - Aggregation pipeline and
analytics provenance.

### Tasks

  ----------------------------------------------------------------------------
  ID                Task              Description            Priority
  ----------------- ----------------- ---------------------- -----------------
  M4-01             Define labeled    Document annotation    Critical
                    evaluation        guidelines, language   
                    dataset           scope, and split       
                                      strategy               

  M4-02             Implement text    Validate text, handle  High
                    preparation       empty input, normalize 
                                      supported fields, and  
                                      preserve raw source    
                                      text according to      
                                      policy                 

  M4-03             Implement         Add language detection High
                    language          and                    
                    identification    unsupported-language   
                                      handling               

  M4-04             Train baseline    Establish TF-IDF +     Critical
                    sentiment model   Logistic Regression or 
                                      Linear SVM baseline    

  M4-05             Evaluate          Report macro F1,       Critical
                    sentiment model   per-class metrics,     
                                      confusion matrix, and  
                                      relevant subgroup      
                                      performance            

  M4-06             Register model    Store immutable model  Critical
                    artifacts         version and provenance 

  M4-07             Implement         Load the active model  Critical
                    inference service version and produce    
                                      structured predictions 

  M4-08             Implement         Persist predictions    Critical
                    prediction        linked to review and   
                    persistence       model version          

  M4-09             Implement aspect  Establish versioned    High
                    taxonomy          aspect definitions and 
                                      annotation rules       

  M4-10             Implement ABSA    Train/evaluate aspect  Medium
                                      detection and aspect   
                                      sentiment if included  
                                      in MVP                 

  M4-11             Implement topic   Evaluate candidate     Medium
                    modeling          topic methods and      
                                      human interpretability 
                                      if included in MVP     

  M4-12             Implement         Generate game-level    Critical
                    aggregation       analytics with         
                                      explicit model and     
                                      taxonomy versions      

  M4-13             Implement         Check totals,          Critical
                    analytics         denominators, missing  
                    validation        values, and version    
                                      consistency            

  M4-14             Add ML evaluation Run reproducible       High
                    automation        evaluation and produce 
                                      machine-readable       
                                      reports                

  M4-15             Add drift         Record input and       Medium
                    monitoring        output distribution    
                    foundations       summaries              
  ----------------------------------------------------------------------------

**Dependencies:** Milestone 3 for collected review data; Milestone 2 for
prediction and analytics tables. Work on dataset annotation and baseline
experiments may begin earlier using approved fixtures.

**Scope control:** Sentiment is the first ML capability. ABSA and topic
modeling should be enabled for the MVP only if their evaluation and
human-review gates are satisfied. A feature that has not passed its gate
must remain disabled or clearly marked unavailable.

**Exit criteria:** - Sentiment model has a documented evaluation
report. - Approved release thresholds are met. - Predictions are linked
to immutable model versions. - Aggregates do not silently mix
incompatible model versions. - Empty and insufficient-data states are
defined. - Aspect/topic capabilities are either validated for release or
explicitly deferred.

## Milestone 5 --- Public API and Frontend Experience

**Objective:** Deliver the public-facing game intelligence experience
using stable API contracts and approved UI/UX guidance.

**Deliverables:** - Public API endpoint groups. - Shared frontend layout
and navigation. - Game discovery and game overview. - Review explorer
and analytical visualizations. - Comparison experience. - Methodology
and transparency pages.

### Tasks

  ------------------------------------------------------------------------------
  ID                Task              Description              Priority
  ----------------- ----------------- ------------------------ -----------------
  M5-01             Finalize API      Align request/response   Critical
                    schemas           models with              
                                      `API_SPECIFICATION.md`   

  M5-02             Implement public  Search, list, detail,    Critical
                    game endpoints    and overview             

  M5-03             Implement         Sentiment, aspects,      Critical
                    analytics         topics, trends, and      
                    endpoints         comparison data          

  M5-04             Implement review  Filtered review listing  High
                    endpoints         and review intelligence  

  M5-05             Implement         Expose collection scope, Critical
                    methodology       model versions, and      
                    endpoint/page     limitations              
                    data                                       

  M5-06             Build application Navigation, layout,      Critical
                    shell             routing, and responsive  
                                      foundations              

  M5-07             Build game        Search, filters,         Critical
                    discovery page    sorting, and result      
                                      states                   

  M5-08             Build game        Summary metrics, trend   Critical
                    overview          views, and provenance    

  M5-09             Build review      Filters, pagination, and High
                    explorer          review detail            

  M5-10             Build             Display only             Medium
                    aspect/topic      capabilities that passed 
                    views             their release gates      

  M5-11             Build comparison  Compare supported games  High
                    lab               using consistent         
                                      definitions              

  M5-12             Build methodology Explain sampling, model  Critical
                    center            limitations, and metric  
                                      definitions              

  M5-13             Implement loading Handle loading, empty,   Critical
                    and failure       partial, stale, and      
                    states            error states             

  M5-14             Add accessibility Keyboard navigation,     High
                    checks            accessible labels,       
                                      focus, and chart         
                                      alternatives             

  M5-15             Add frontend/API  Verify data mapping and  High
                    integration tests filter behavior          
  ------------------------------------------------------------------------------

**Dependencies:** Milestones 0, 1, 2, and 4. API and frontend
scaffolding can begin earlier, but analytical pages require stable
response contracts and representative data.

**UI/UX dependency:** `UI_UX_GUIDELINES.md` is currently absent. Before
detailed page implementation, create and approve it with the information
architecture, wireframes, design tokens, responsive behavior, chart
conventions, and all analytical states. Do not invent final visual
specifications inside implementation tickets.

**Exit criteria:** - Public users can search and open indexed games
without an account. - Analytics are clearly labeled and have valid
empty/partial states. - Filters and pagination produce consistent
results. - Methodology and limitations are discoverable. - Core pages
follow the approved UI/UX baseline and accessibility expectations.

## Milestone 6 --- Research Workspace and Export

**Objective:** Add optional authenticated workflows for saving and
reproducing research activity.

**Deliverables:** - Authentication and session flow. - Research project
management. - Saved analysis and snapshot support. - Asynchronous export
jobs. - Role-based access control and audit events.

### Tasks

  ----------------------------------------------------------------------------------
  ID                Task              Description                  Priority
  ----------------- ----------------- ---------------------------- -----------------
  M6-01             Implement         Registration/login/session   High
                    authentication    behavior according to the    
                                      approved auth design         

  M6-02             Implement RBAC    Enforce guest, member,       Critical
                    enforcement       researcher, and admin        
                                      permissions on the backend   

  M6-03             Implement project Create, view, update, and    High
                    CRUD              archive research projects    

  M6-04             Implement project Add/remove members and       High
                    membership        enforce membership rules     

  M6-05             Implement saved   Persist filters, selected    High
                    analyses          games, and relevant          
                                      model/data provenance        

  M6-06             Implement         Preserve reproducibility     High
                    analysis          metadata and documented      
                    snapshots         snapshot semantics           

  M6-07             Implement export  Submit, process, inspect,    High
                    job workflow      and retrieve asynchronous    
                                      exports                      

  M6-08             Enforce export    Apply role-based limits and  Critical
                    quotas            request validation           

  M6-09             Implement audit   Record sensitive             High
                    logging           administrative and workspace 
                                      actions without logging      
                                      secrets                      

  M6-10             Build workspace   Project list, project        Medium
                    UI                details, saved analyses, and 
                                      export status                

  M6-11             Add authorization Verify ownership,            Critical
                    tests             membership, role changes,    
                                      and object-level access      

  M6-12             Add export        Verify job lifecycle, file   High
                    integration/E2E   contents, and download       
                    tests             authorization                
  ----------------------------------------------------------------------------------

**Dependencies:** Milestones 1 and 2; API foundations from Milestone 5.
Export requires stable data-selection and serialization rules.

**MVP scope decision:** Research workspace and export can be deferred if
schedule or team capacity is limited. If deferred, public analytics and
methodology must remain usable without authentication.

**Exit criteria:** - Backend authorization is enforced independently of
frontend visibility. - Users cannot access another user's private
project or export. - Saved analyses preserve the required provenance. -
Export jobs are asynchronous, quota-controlled, and auditable. -
Download links or endpoints enforce authorization and expiry policy.

## Milestone 7 --- Hardening, Acceptance, and MVP Release

**Objective:** Verify the complete product, resolve release blockers,
and prepare a controlled MVP deployment.

**Deliverables:** - Completed regression suite. - Staging E2E results. -
ML release reports. - Acceptance decision. - Deployment and rollback
checklist. - Operational runbook.

### Tasks

  -----------------------------------------------------------------------
  ID                Task              Description       Priority
  ----------------- ----------------- ----------------- -----------------
  M7-01             Run full          Execute unit,     Critical
                    regression suite  integration, API, 
                                      and E2E suites    

  M7-02             Validate          Rehearse          Critical
                    migrations        migrations from   
                                      the previous      
                                      supported schema  

  M7-03             Run security      Review auth,      Critical
                    checks            object access,    
                                      rate limits,      
                                      secrets,          
                                      dependencies, and 
                                      logs              

  M7-04             Run performance   Measure key       High
                    checks            search,           
                                      analytics,        
                                      review, and       
                                      export paths      

  M7-05             Verify recovery   Test worker       Critical
                    behavior          interruption,     
                                      retry, recovery   
                                      scan, and         
                                      checkpoint safety 

  M7-06             Verify monitoring Confirm health    High
                                      checks,           
                                      structured logs,  
                                      job metrics, and  
                                      alert conditions  

  M7-07             Run ML release    Verify model      Critical
                    review            gates,            
                                      provenance,       
                                      subgroup          
                                      performance, and  
                                      rollback          
                                      readiness         

  M7-08             Conduct           Execute agreed    Critical
                    acceptance        scenarios with    
                    testing           representative    
                                      users             

  M7-09             Fix release       Resolve critical  Critical
                    blockers          and high-severity 
                                      issues or         
                                      document approved 
                                      exceptions        

  M7-10             Prepare           Configure         Critical
                    deployment        secrets,          
                                      migrations,       
                                      workers,          
                                      scheduler,        
                                      backups, and      
                                      deployment steps  

  M7-11             Prepare rollback  Document          High
                    plan              application,      
                                      schema, and model 
                                      rollback          
                                      procedures        

  M7-12             Publish           Ensure collection Critical
                    methodology       and ML            
                                      limitations are   
                                      visible in the    
                                      released product  

  M7-13             Approve MVP       Record the        Critical
                    release           release decision  
                                      and known         
                                      limitations       
  -----------------------------------------------------------------------

**Dependencies:** All MVP-required features from Milestones 1--6.

**Exit criteria:** - All release-critical automated tests pass. -
Acceptance scenarios pass. - No unresolved critical defects remain. -
High-severity defects are resolved or formally accepted with mitigation
and owner. - Data collection and ML methodology disclosures are
available. - Deployment, monitoring, backup, and rollback procedures are
reviewed. - Release approval is recorded.

## Milestone 8 --- Post-MVP Improvements

**Objective:** Improve coverage, quality, scale, and research
capabilities based on observed usage and validated needs.

Potential tasks:

-   Expand language support after per-language evaluation.
-   Improve sentiment and aspect models using new labeled data.
-   Improve topic stability and human-readable topic labels.
-   Add richer research exports and reproducibility features.
-   Add additional comparison dimensions.
-   Improve query performance using measured bottlenecks.
-   Add advanced accessibility and localization.
-   Add more operational dashboards and drift alerts.
-   Evaluate additional infrastructure only when current architecture
    has demonstrated limits.

Post-MVP work must be prioritized using user value, measured defects,
model evaluation, and operational evidence---not technology novelty
alone.

## 5. Dependency Map

### 5.1 High-level dependency graph

``` mermaid
flowchart TD
    M0["M0: Product Alignment and UI/UX"]
    M1["M1: Repository and Development Foundation"]
    M2["M2: Database and Core Backend"]
    M3["M3: Steam Integration and Ingestion"]
    M4["M4: ML and Analytics"]
    M5["M5: Public API and Frontend"]
    M6["M6: Research Workspace and Export"]
    M7["M7: Hardening and MVP Release"]
    M8["M8: Post-MVP Improvements"]

    M0 --> M1
    M0 --> M5
    M1 --> M2
    M2 --> M3
    M2 --> M4
    M3 --> M4
    M2 --> M5
    M4 --> M5
    M2 --> M6
    M5 --> M6
    M3 --> M7
    M4 --> M7
    M5 --> M7
    M6 --> M7
    M7 --> M8
```

### 5.2 Critical dependency notes

  -----------------------------------------------------------------------
  Dependency              Why it matters          What can proceed in
                                                  parallel
  ----------------------- ----------------------- -----------------------
  UI/UX baseline →        Prevents page and chart Repository setup,
  detailed frontend       rework                  backend, data contracts

  Database schema →       Jobs, checkpoints,      Steam adapter prototype
  durable ingestion       reviews, and batches    using fixtures
                          need persistence        

  Ingestion → production  ML requires collected   Annotation guideline
  ML pipeline             and versioned review    design and baseline
                          data                    experiments on approved
                                                  fixtures

  ML output contract →    Analytics must identify Public API scaffolding
  analytics API           prediction/model        and non-ML catalog
                          versions                endpoints

  API contract → frontend Prevents                Wireframes, design
  integration             frontend/backend schema tokens, component
                          drift                   prototypes

  Authentication/RBAC →   Protects private        Public game
  private                 research resources      intelligence
  workspace/export                                

  All MVP slices →        Acceptance requires a   Documentation and
  acceptance/release      coherent deployed       operational preparation
                          product                 
  -----------------------------------------------------------------------

### 5.3 Critical path

The likely critical path for an analytics-focused MVP is:

**Project foundation → database → ingestion → sentiment evaluation and
inference → aggregation → public analytics API → frontend analytical
pages → acceptance and release.**

UI/UX definition is an early parallel workstream that becomes a hard
dependency for detailed frontend implementation. Research workspace and
export may be developed as a separate branch if they are included in the
MVP.

## 6. Recommended Development Sequence

Use vertical slices where possible. A vertical slice delivers a small,
testable user-facing capability across the required layers.

### Phase A --- Establish the foundation

1.  Review and reconcile the existing specifications.
2.  Confirm the MVP boundary and UI/UX deliverables.
3.  Create the repository and local development environment.
4.  Configure CI, linting, typing, and test runners.
5.  Bootstrap FastAPI, React, PostgreSQL, and Redis.
6.  Add health checks and developer documentation.

**Completion signal:** a clean checkout can run locally and pass
baseline CI.

### Phase B --- Build a reliable data foundation

1.  Implement database migrations and core tables.
2.  Implement game and review repositories.
3.  Implement deterministic seed data.
4.  Build the Steam adapter against recorded fixtures.
5.  Implement historical sample collection.
6.  Implement incremental synchronization.
7.  Add atomic persistence, checkpointing, retry, and recovery.
8.  Verify ingestion invariants with PostgreSQL and worker integration
    tests.

**Completion signal:** a seeded game can be collected and synchronized
repeatedly without duplicate logical reviews or unsafe checkpoint
advancement.

### Phase C --- Produce trustworthy analytics

1.  Establish annotation guidelines and evaluation dataset.
2.  Train and evaluate a baseline sentiment model.
3.  Register an immutable model version.
4.  Implement inference and prediction persistence.
5.  Implement version-aware aggregation.
6.  Validate aggregate counts and denominators.
7.  Enable ABSA or topic modeling only after their release gates pass.

**Completion signal:** a game has reproducible analytics traceable to
its review scope and model version.

### Phase D --- Deliver the public product

1.  Finalize UI/UX guidance and wireframes.
2.  Finalize public API contracts.
3.  Implement game discovery and overview endpoints.
4.  Build the application shell and discovery page.
5.  Build game overview and analytical charts.
6.  Build review exploration and comparison.
7.  Add methodology and limitations.
8.  Run browser E2E tests against staging.

**Completion signal:** a guest can discover a game, inspect analytics,
understand the limitations, and compare supported games.

### Phase E --- Add research capabilities if included

1.  Implement authentication and RBAC.
2.  Implement projects and membership.
3.  Implement saved analyses and provenance.
4.  Implement asynchronous exports and quotas.
5.  Add object-level authorization tests.
6.  Verify the workflow through E2E tests.

**Completion signal:** authorized users can save and retrieve research
work without exposing private resources.

### Phase F --- Release

1.  Run full regression and security checks.
2.  Validate migrations and recovery procedures.
3.  Run performance checks on representative data.
4.  Complete ML model release review.
5.  Conduct acceptance testing.
6.  Resolve release blockers.
7.  Deploy with monitoring and rollback readiness.
8.  Record the release decision and known limitations.

**Completion signal:** all MVP release criteria are satisfied and the
release is approved.

## 7. Workstream Organization

For a small team, responsibilities may be combined. A single developer
can own multiple workstreams, but each deliverable should still have a
clear owner.

  -----------------------------------------------------------------------
  Workstream              Main responsibilities   Key outputs
  ----------------------- ----------------------- -----------------------
  Product and UX          Scope, user journeys,   Approved MVP and design
                          information             baseline
                          architecture, UI/UX     
                          guidelines, acceptance  

  Backend                 FastAPI, domain         Tested backend modules
                          services, repositories, and endpoints
                          API contracts, RBAC     

  Data engineering        Steam adapter,          Reliable review dataset
                          ingestion, workers,     and operational jobs
                          checkpoints, recovery   

  ML and analytics        Dataset annotation,     Versioned models and
                          model training,         trusted analytics
                          evaluation, inference,  
                          aggregation             

  Frontend                React application,      Public user experience
                          charts, filters,        and optional workspace
                          responsive and          
                          accessible UI           

  QA and release          Test strategy,          Test evidence and
                          automation, regression, release decision
                          acceptance, release     
                          verification            

  Operations              CI/CD, secrets,         Repeatable deployment
                          deployment, backups,    and recovery
                          monitoring              
  -----------------------------------------------------------------------

## 8. Definition of Done

Definition of Done applies at task, feature, milestone, and release
levels. A task is not complete merely because code has been written or a
page renders.

### 8.1 Task-level DoD

A task is done when:

-   [ ] The implementation satisfies the task's stated scope.
-   [ ] Code follows `CODING_STANDARDS.md`.
-   [ ] Relevant unit tests are added or updated.
-   [ ] Relevant integration/API/UI tests are added where appropriate.
-   [ ] Input validation and error behavior are handled.
-   [ ] Authorization is enforced for protected operations.
-   [ ] No secrets or unnecessary personal data are introduced.
-   [ ] Logging is useful and does not expose sensitive information.
-   [ ] Documentation and configuration examples are updated.
-   [ ] CI checks pass.
-   [ ] The change has been reviewed and merged through the agreed
    workflow.

### 8.2 Feature-level DoD

A feature is done when:

-   [ ] Its user story and acceptance criteria are satisfied.
-   [ ] API and database contracts are implemented and documented.
-   [ ] Loading, empty, partial, success, and failure states are handled
    where applicable.
-   [ ] Accessibility and responsive behavior are checked for
    user-facing features.
-   [ ] Relevant permissions and rate limits are enforced server-side.
-   [ ] Automated tests cover expected behavior and important edge
    cases.
-   [ ] Observability is sufficient to diagnose failures.
-   [ ] No unresolved critical or high-severity defect remains without
    an approved exception.
-   [ ] The feature is deployed and verified in the target test
    environment.

### 8.3 Data-ingestion DoD

An ingestion feature is done only when:

-   [ ] Request parameters and response parsing match the supported
    Steam API contract.
-   [ ] Cursor pagination and terminal-page behavior are tested.
-   [ ] Duplicate delivery is safe and idempotent.
-   [ ] Review persistence, batch accounting, and checkpoint updates
    obey the atomicity invariant.
-   [ ] Failed or incomplete work does not advance the committed
    watermark.
-   [ ] HTTP 429 and transient failures use bounded retry behavior.
-   [ ] Recovery can resume from PostgreSQL-backed state.
-   [ ] Job metrics and failure details are observable.
-   [ ] Collection policy and limitations are documented.

### 8.4 ML-feature DoD

An ML feature is done only when:

-   [ ] The task and label definitions are documented.
-   [ ] Dataset snapshot and split methodology are recorded.
-   [ ] Leakage checks are completed.
-   [ ] Baseline comparison is available.
-   [ ] Required metrics and subgroup results are reported.
-   [ ] Approved release thresholds are met.
-   [ ] Robustness and unsupported-input behavior are evaluated.
-   [ ] Model artifacts and provenance are versioned.
-   [ ] Predictions retain model-version attribution.
-   [ ] Aggregations use compatible prediction versions.
-   [ ] Human review is completed for outputs that require
    interpretation, such as topics.
-   [ ] Rollback or deactivation behavior is defined.

### 8.5 API DoD

An API operation is done only when:

-   [ ] Method, path, request, and response follow
    `API_SPECIFICATION.md`.
-   [ ] Success and error status codes are tested.
-   [ ] Authentication and object-level authorization are tested where
    applicable.
-   [ ] Pagination and filter behavior are deterministic under the
    documented contract.
-   [ ] Validation errors use stable machine-readable codes.
-   [ ] OpenAPI documentation is accurate.
-   [ ] Rate limits and cache behavior are applied where specified.
-   [ ] No internal stack trace or secret is returned to clients.

### 8.6 UI/UX DoD

A user-facing feature is done only when:

-   [ ] It follows the approved `UI_UX_GUIDELINES.md` or a documented
    interim design decision.
-   [ ] Its information hierarchy and interaction behavior match the
    approved wireframe or design.
-   [ ] Loading, empty, partial, error, and unavailable states are
    defined.
-   [ ] Charts identify metric definitions, units, date scope, and
    relevant sample context.
-   [ ] Keyboard navigation, focus behavior, and accessible labels are
    checked.
-   [ ] Responsive behavior is checked at the agreed viewport sizes.
-   [ ] Visual regressions are reviewed in the supported browser set.

Because `UI_UX_GUIDELINES.md` has not yet been supplied, this DoD item
is a dependency: detailed UI work cannot be considered fully done until
the design baseline is approved.

### 8.7 Milestone-level DoD

A milestone is done when:

-   [ ] All milestone deliverables are present.
-   [ ] All critical milestone tasks satisfy task-level DoD.
-   [ ] Dependencies and interfaces are verified.
-   [ ] Milestone exit criteria pass.
-   [ ] Known limitations and deferred work are documented.
-   [ ] The milestone owner records completion.

### 8.8 MVP release DoD

The MVP is done when:

-   [ ] All MVP milestones are complete or formally scoped out.
-   [ ] Critical unit, integration, API, and E2E tests pass.
-   [ ] Database migrations are validated.
-   [ ] Ingestion integrity and recovery invariants pass.
-   [ ] ML release gates pass for every enabled ML capability.
-   [ ] Public analytics expose methodology and limitations.
-   [ ] Role and export security checks pass for enabled authenticated
    features.
-   [ ] Acceptance testing is completed and approved.
-   [ ] No unresolved critical defect remains.
-   [ ] High-severity exceptions have an owner, mitigation, and
    approval.
-   [ ] Deployment, monitoring, backup, and rollback procedures are
    ready.
-   [ ] Release notes and known limitations are published.

## 9. Change Management and Roadmap Updates

This roadmap is a planning baseline, not an immutable schedule.

Update it when:

-   MVP scope changes.
-   An external API contract changes.
-   Database or architecture decisions materially change.
-   A model capability is deferred or fails its evaluation gate.
-   UI/UX approval changes navigation or page behavior.
-   A milestone dependency changes.
-   Acceptance testing reveals a material product gap.

For every change, record the affected milestone, dependency, risk, and
required documentation updates. Avoid silently moving unfinished
critical work into a later milestone while still reporting the original
milestone as complete.

## 10. Final Implementation Policy

SteamScoop should be implemented in dependency order, with data
integrity and analytical validity established before broad public
presentation.

The recommended priority is:

1.  Establish the development and database foundation.
2.  Build reliable, recoverable Steam ingestion.
3.  Validate and version the ML/analytics pipeline.
4.  Deliver the public discovery and intelligence experience.
5.  Add authenticated research and export workflows if included in the
    MVP.
6.  Complete hardening, acceptance, and release verification.

The missing `UI_UX_GUIDELINES.md` is an explicit early deliverable. It
does not block repository, backend, database, or ingestion foundations,
but it must be resolved before detailed frontend implementation is
treated as design-complete.
