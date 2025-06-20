---
layout: ../../layouts/post.astro
title: "Database Schema Migrations with golang-migrate in Kubernetes"
pubDate: 2025-06-20
description: "A practical guide to implementing database schema migrations using golang-migrate, with MongoDB examples and production deployment strategies using Kubernetes init containers."
author: "Torstein Skulbru"
isPinned: false
excerpt: "Database schema evolution requires systematic management. Learn how to implement reliable migrations using golang-migrate with MongoDB examples and deploy them safely in Kubernetes environments."
image:
  src: "/images/migration.jpg"
  alt: "Birds migrating during sunset"
tags: ["golang", "kubernetes", "mongodb", "devops"]
blueskyUri: "at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3lrzybbc6y22u"
---

## Why Database Migrations Matter

Database migrations solve the problem of evolving data structures in production systems without losing data or causing downtime. Consider splitting a user's "name" field into separate "firstName" and "lastName" fields. Without migrations, you face manual updates to thousands of records, one-off scripts that might fail halfway through, or data loss.

Each migration defines exactly how to transform data from one state to another, with a rollback procedure if something goes wrong. This becomes essential when multiple developers deploy changes to different environments that must maintain data consistency. Production applications need predictable, repeatable database changes that can be tested and automatically applied during deployments.

Many developers assume NoSQL databases eliminate migration complexity, but production applications require consistent data structures, field validations, and index management regardless of the database technology. Document stores like MongoDB still need systematic approaches to restructure nested documents, add validation rules, and manage indexes across environments.

The [golang-migrate](https://github.com/golang-migrate/migrate) library provides versioned, reversible migrations for [multiple database systems](https://github.com/golang-migrate/migrate), including PostgreSQL, MySQL, MongoDB, and CockroachDB. This guide demonstrates golang-migrate using MongoDB as a practical example, though the concepts and Kubernetes deployment patterns apply to any supported database.

## Understanding Database Migration Requirements with MongoDB

MongoDB migrations differ fundamentally from traditional SQL migrations due to their document-oriented nature. Document transformations, index management, and validation rule updates replace table structure modifications. Adding new fields with default values, restructuring nested documents, removing deprecated fields, and creating compound indexes for query optimization represent common MongoDB migration scenarios.

MongoDB's distributed nature and eventual consistency model present unique challenges compared to traditional relational databases. Write concerns, read preferences, and potential race conditions during migration execution require careful consideration, unlike SQL transactions that provide ACID guarantees. These considerations illustrate why golang-migrate provides database-specific drivers to handle the nuances of different database systems.

## Setting Up golang-migrate for MongoDB

The golang-migrate library supports MongoDB through its dedicated driver, similar to how it provides drivers for PostgreSQL, MySQL, and other databases. Installation requires both the CLI tool and the database-specific driver components.

```bash
# Install the CLI tool
go install -tags 'mongodb' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Verify installation with MongoDB support
migrate -version
```

For programmatic usage within Go applications, import the necessary packages. Note that different database drivers require different import paths:

```go
import (
    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/mongodb"  // For MongoDB
    // _ "github.com/golang-migrate/migrate/v4/database/postgres" // For PostgreSQL
    // _ "github.com/golang-migrate/migrate/v4/database/mysql"    // For MySQL
    _ "github.com/golang-migrate/migrate/v4/source/file"
)
```

The MongoDB driver expects connection strings in the standard MongoDB URI format. Authentication, replica set configuration, and connection pooling parameters are specified through URL parameters. Each database driver has its own connection string format requirements:

```bash
# MongoDB connection string
mongodb://username:password@host1:27017,host2:27017/database?replicaSet=rs0&authSource=admin

# PostgreSQL connection string (for comparison)
# postgres://username:password@host:5432/database?sslmode=disable

# MySQL connection string (for comparison)  
# mysql://username:password@host:3306/database
```

## Creating Migration Files

Migration files follow a specific naming convention that includes version numbers and descriptive names across all database systems. Each migration consists of two files: an "up" migration that applies changes and a "down" migration that reverses them. The file extension depends on the target database (`.sql` for SQL databases, `.json` for MongoDB).

```bash
# Create a new migration for MongoDB
migrate create -ext json -dir migrations add_user_preferences

# For SQL databases, you would use:
# migrate create -ext sql -dir migrations add_user_preferences
```

This command generates two files for MongoDB: `000001_add_user_preferences.up.json` and `000001_add_user_preferences.down.json`. For SQL databases, the files would use `.sql` extensions instead of `.json`.

The version number (000001) ensures migrations execute in the correct order. Sequential numbering prevents conflicts when multiple developers create migrations simultaneously.

### Implementing Database-Specific Operations

MongoDB migrations use JSON format to define aggregation pipelines and operations, while SQL databases use standard SQL DDL statements. Each migration file contains database-specific operations that are executed sequentially. Based on the [official golang-migrate MongoDB examples](https://github.com/golang-migrate/migrate/blob/master/database/mongodb/examples/migrations/004_replace_field_value_from_another_field.up.json), MongoDB migrations use raw MongoDB query syntax in JSON format.

Here's a detailed example that adds a new field with computed values:

```json
[
    {
        "aggregate": "users",
        "pipeline": [
            {
                "$match": {
                    "preferences": {"$exists": false}
                }
            },
            {
                "$addFields": {
                    "preferences": {
                        "theme": {
                            "$ifNull": ["$theme", "light"]
                        },
                        "notifications": {
                            "email": true,
                            "push": false,
                            "sms": false
                        },
                        "privacy": {
                            "profileVisibility": "public",
                            "activityTracking": true
                        },
                        "createdAt": "$$NOW",
                        "updatedAt": "$$NOW"
                    },
                    "migrationVersion": 1
                }
            },
            {
                "$unset": "theme"
            },
            {
                "$out": "users"
            }
        ],
        "cursor": {}
    },
    {
        "createIndexes": "users",
        "indexes": [
            {
                "key": {"preferences.theme": 1},
                "name": "preferences_theme_1"
            },
            {
                "key": {"preferences.privacy.profileVisibility": 1},
                "name": "preferences_privacy_profileVisibility_1"
            }
        ]
    }
]
```

The corresponding down migration reverses these changes:

```json
[
    {
        "aggregate": "users",
        "pipeline": [
            {
                "$match": {
                    "preferences": {"$exists": true}
                }
            },
            {
                "$addFields": {
                    "theme": {
                        "$ifNull": ["$preferences.theme", null]
                    }
                }
            },
            {
                "$unset": ["preferences", "migrationVersion"]
            },
            {
                "$out": "users"
            }
        ],
        "cursor": {}
    },
    {
        "dropIndexes": "users",
        "index": ["preferences_theme_1", "preferences_privacy_profileVisibility_1"]
    }
]
```

### Handling Large Collections

Large collections require special consideration to prevent memory exhaustion and minimize downtime. The aggregation pipeline approach with `$out` operations provides memory-efficient document processing by leveraging MongoDB's internal optimization:

```json
[
    {
        "aggregate": "orders",
        "pipeline": [
            {
                "$match": {
                    "items.0": {"$exists": true},
                    "itemsRestructured": {"$exists": false}
                }
            },
            {
                "$addFields": {
                    "items": {
                        "$map": {
                            "input": "$items",
                            "as": "item",
                            "in": {
                                "productId": {
                                    "$ifNull": ["$$item.product_id", "$$item.productId"]
                                },
                                "quantity": {
                                    "$ifNull": [
                                        {"$ifNull": ["$$item.qty", "$$item.quantity"]},
                                        1
                                    ]
                                },
                                "price": {
                                    "amount": {"$ifNull": ["$$item.price", 0]},
                                    "currency": {"$ifNull": ["$$item.currency", "USD"]}
                                },
                                "metadata": {
                                    "addedAt": {
                                        "$ifNull": ["$$item.added_at", "$$NOW"]
                                    },
                                    "source": {"$ifNull": ["$$item.source", "web"]}
                                }
                            }
                        }
                    },
                    "itemsRestructured": true,
                    "migrationVersion": 2
                }
            },
            {
                "$out": "orders"
            }
        ],
        "cursor": {},
        "allowDiskUse": true
    },
    {
        "createIndexes": "orders",
        "indexes": [
            {
                "key": {"items.productId": 1},
                "name": "items_productId_1"
            },
            {
                "key": {"items.price.amount": 1},
                "name": "items_price_amount_1"
            }
        ]
    }
]
```

## Programmatic Migration Execution

Production applications often require programmatic migration control integrated with application startup routines. The golang-migrate library provides a complete API for migration management with version tracking, error handling, and graceful shutdown capabilities:

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/mongodb"
    _ "github.com/golang-migrate/migrate/v4/source/file"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
)

type MigrationManager struct {
    migrate *migrate.Migrate
    client  *mongo.Client
}

func NewMigrationManager(mongoURI, migrationsPath string) (*MigrationManager, error) {
    // Create MongoDB client for health checks
    client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(mongoURI))
    if err != nil {
        return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
    }

    // Initialize migrate instance
    m, err := migrate.New(
        fmt.Sprintf("file://%s", migrationsPath),
        mongoURI,
    )
    if err != nil {
        return nil, fmt.Errorf("failed to initialize migrate: %w", err)
    }

    return &MigrationManager{
        migrate: m,
        client:  client,
    }, nil
}

func (mm *MigrationManager) RunMigrations(ctx context.Context) error {
    // Verify database connectivity
    if err := mm.client.Ping(ctx, nil); err != nil {
        return fmt.Errorf("database connectivity check failed: %w", err)
    }

    // Get current migration version
    version, dirty, err := mm.migrate.Version()
    if err != nil && err != migrate.ErrNilVersion {
        return fmt.Errorf("failed to get current migration version: %w", err)
    }

    log.Printf("Current migration version: %d, dirty: %t", version, dirty)

    // Handle dirty state
    if dirty {
        log.Printf("Database is in dirty state, attempting to force version %d", version)
        if err := mm.migrate.Force(int(version)); err != nil {
            return fmt.Errorf("failed to force migration version: %w", err)
        }
    }

    // Apply migrations
    if err := mm.migrate.Up(); err != nil && err != migrate.ErrNoChange {
        return fmt.Errorf("failed to apply migrations: %w", err)
    }

    // Get final version
    finalVersion, _, err := mm.migrate.Version()
    if err != nil {
        return fmt.Errorf("failed to get final migration version: %w", err)
    }

    log.Printf("Migrations completed successfully, current version: %d", finalVersion)
    return nil
}

func (mm *MigrationManager) Close() error {
    if err := mm.client.Disconnect(context.Background()); err != nil {
        log.Printf("Error disconnecting MongoDB client: %v", err)
    }
    
    sourceErr, dbErr := mm.migrate.Close()
    if sourceErr != nil {
        log.Printf("Error closing migration source: %v", sourceErr)
    }
    if dbErr != nil {
        log.Printf("Error closing migration database: %v", dbErr)
    }
    
    return nil
}

func main() {
    mongoURI := "mongodb://localhost:27017/myapp"
    migrationsPath := "./migrations"

    mm, err := NewMigrationManager(mongoURI, migrationsPath)
    if err != nil {
        log.Fatalf("Failed to create migration manager: %v", err)
    }
    defer mm.Close()

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
    defer cancel()

    if err := mm.RunMigrations(ctx); err != nil {
        log.Fatalf("Migration failed: %v", err)
    }

    log.Println("Application starting with up-to-date database schema")
}
```

## Kubernetes Integration with Init Containers

Production Kubernetes deployments benefit from running migrations as init containers before application pods start. This approach ensures database schema consistency across all application replicas and prevents race conditions during rolling updates.

### Creating a Migration Docker Image

First, create a dedicated Docker image for running migrations:

```dockerfile
# Dockerfile.migrations
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

# Install migrate CLI with MongoDB support
RUN go install -tags 'mongodb' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Copy migration files
COPY migrations/ ./migrations/
COPY migrate-entrypoint.sh ./

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

# Copy migrate binary and migration files
COPY --from=builder /go/bin/migrate /usr/local/bin/migrate
COPY --from=builder /app/migrations ./migrations
COPY --from=builder /app/migrate-entrypoint.sh ./

RUN chmod +x migrate-entrypoint.sh

ENTRYPOINT ["./migrate-entrypoint.sh"]
```

The entrypoint script handles connection retries and graceful error handling:

```bash
#!/bin/sh
# migrate-entrypoint.sh

set -e

# Default values
MIGRATION_DIR=${MIGRATION_DIR:-"/root/migrations"}
MAX_RETRIES=${MAX_RETRIES:-30}
RETRY_INTERVAL=${RETRY_INTERVAL:-2}

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is required"
    exit 1
fi

echo "Starting MongoDB migration process..."
echo "Migration directory: $MIGRATION_DIR"
echo "Database URL: ${DATABASE_URL%/*}/***"

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
for i in $(seq 1 $MAX_RETRIES); do
    if migrate -path "$MIGRATION_DIR" -database "$DATABASE_URL" version > /dev/null 2>&1; then
        echo "MongoDB is ready"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "ERROR: MongoDB not ready after $MAX_RETRIES attempts"
        exit 1
    fi
    
    echo "Attempt $i/$MAX_RETRIES: MongoDB not ready, waiting ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

# Get current migration status
echo "Checking current migration status..."
CURRENT_VERSION=$(migrate -path "$MIGRATION_DIR" -database "$DATABASE_URL" version 2>/dev/null || echo "nil")
echo "Current migration version: $CURRENT_VERSION"

# Apply migrations
echo "Applying migrations..."
if migrate -path "$MIGRATION_DIR" -database "$DATABASE_URL" up; then
    echo "Migrations applied successfully"
    
    # Get final version
    FINAL_VERSION=$(migrate -path "$MIGRATION_DIR" -database "$DATABASE_URL" version 2>/dev/null || echo "unknown")
    echo "Final migration version: $FINAL_VERSION"
else
    echo "ERROR: Migration failed"
    exit 1
fi

echo "Migration process completed successfully"
```

### Kubernetes Deployment Configuration

Integrate the migration init container into your application deployment:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      initContainers:
      - name: mongodb-migrations
        image: myregistry.com/myapp-migrations:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: connection-string
        - name: MAX_RETRIES
          value: "60"
        - name: RETRY_INTERVAL
          value: "5"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
      containers:
      - name: app
        image: myregistry.com/myapp:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: connection-string
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Secret
metadata:
  name: mongodb-credentials
  namespace: production
type: Opaque
data:
  connection-string: <base64-encoded-mongodb-uri>
```

### Advanced Kubernetes Patterns

For complex deployments, consider using Jobs for one-time migrations or CronJobs for maintenance tasks:

```yaml
# migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: mongodb-migration-v2
  namespace: production
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: migration
        image: myregistry.com/myapp-migrations:v2.0.0
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mongodb-credentials
              key: connection-string
        - name: TARGET_VERSION
          value: "5"  # Migrate to specific version
        command: ["./migrate-entrypoint.sh"]
        args: ["goto", "$(TARGET_VERSION)"]
        resources:
          requests:
            memory: "128Mi"
            cpu: "200m"
          limits:
            memory: "256Mi"
            cpu: "400m"
      backoffLimit: 3
```

## Error Handling and Rollback Strategies

Production migrations require detailed error handling and rollback capabilities that include backup creation, timeout management, and state tracking. The golang-migrate library tracks migration state in a dedicated collection, enabling precise rollback operations:

```go
func (mm *MigrationManager) SafeMigrate(ctx context.Context, targetVersion uint) error {
    // Create backup before migration
    backupName := fmt.Sprintf("pre-migration-%d-%d", targetVersion, time.Now().Unix())
    if err := mm.createBackup(ctx, backupName); err != nil {
        return fmt.Errorf("backup creation failed: %w", err)
    }

    // Apply migration with timeout
    migrationCtx, cancel := context.WithTimeout(ctx, 30*time.Minute)
    defer cancel()

    if err := mm.migrate.Migrate(targetVersion); err != nil {
        log.Printf("Migration failed, attempting rollback...")
        
        // Attempt to rollback to previous version
        if rollbackErr := mm.rollbackToPreviousVersion(); rollbackErr != nil {
            log.Printf("Rollback failed: %v", rollbackErr)
            return fmt.Errorf("migration failed and rollback failed: migration=%w, rollback=%v", err, rollbackErr)
        }
        
        return fmt.Errorf("migration failed but rollback succeeded: %w", err)
    }

    return nil
}

func (mm *MigrationManager) rollbackToPreviousVersion() error {
    version, _, err := mm.migrate.Version()
    if err != nil {
        return err
    }
    
    if version > 0 {
        return mm.migrate.Migrate(version - 1)
    }
    
    return nil
}
```

The implementation patterns demonstrated here provide a complete foundation for managing database schema evolution in production environments across multiple database systems. Versioned migrations, Kubernetes init containers, and detailed error handling with backup strategies work together to ensure reliable database schema management across deployment lifecycles, whether using MongoDB, PostgreSQL, MySQL, or any other supported database.

Migration complexity scales from simple field additions to complex restructuring operations while maintaining reversibility through down scripts. This systematic approach enables safe rollbacks when deployment issues arise, supporting continuous delivery practices in distributed environments regardless of the underlying database technology.

## Migration Ownership in Microservice Architectures

Microservice architectures present unique challenges for migration ownership and placement. The fundamental question becomes whether migrations live with individual services, in centralized repositories, or through hybrid approaches that balance autonomy with coordination.

### Service-Owned Migrations

The most common pattern places migrations within each service's repository alongside application code. Each service owns its database schema and manages migrations independently. This approach aligns with microservice principles of service autonomy and bounded contexts.

```bash
user-service/
├── cmd/
├── internal/
├── migrations/
│   ├── 000001_create_users.up.json
│   ├── 000001_create_users.down.json
│   └── 000002_add_preferences.up.json
└── Dockerfile

order-service/
├── cmd/
├── internal/
├── migrations/
│   ├── 000001_create_orders.up.json
│   └── 000001_create_orders.down.json
└── Dockerfile
```

Teams can deploy schema changes independently without coordinating with other services when migrations live within service repositories. Migration versioning stays synchronized with application code changes, preventing version drift between schema and application logic. Service boundaries remain clear, with each team responsible for their data model evolution.

However, this approach requires careful coordination when services share data or need synchronized schema changes. Cross-service migrations become complex, requiring orchestrated deployments and potential data consistency challenges during transition periods.

### Centralized Migration Repository

Some organizations choose centralized migration repositories that contain all database schema changes across services. This pattern provides better visibility into system-wide schema evolution and enables coordinated changes across multiple services.

```bash
database-migrations/
├── user-service/
│   ├── 000001_create_users.up.json
│   └── 000002_add_preferences.up.json
├── order-service/
│   ├── 000001_create_orders.up.json
│   └── 000002_add_order_status.up.json
├── shared/
│   └── 000001_create_audit_log.up.json
└── deployment/
    ├── Dockerfile
    └── apply-migrations.sh
```

Database administrators can review all changes in a single location with centralized repositories. Cross-service dependencies become explicit through shared migration files. Shared infrastructure like audit logs or reference data maintains consistency across services through unified management.

This centralization reduces service autonomy and creates potential deployment bottlenecks. Teams must coordinate schema changes through the central repository, potentially slowing development velocity. The migration deployment process becomes more complex, requiring knowledge of service dependencies and deployment ordering.

### Hybrid Approaches

Many organizations adopt hybrid patterns that combine service ownership with centralized coordination. Services maintain their migrations locally but register schema changes through shared tooling or governance processes.

```yaml
# .migration-registry.yaml in each service
service: user-service
database: users_db
migrations:
  - version: 1
    description: "Create users collection"
    breaking: false
  - version: 2
    description: "Add user preferences"
    breaking: false
    dependencies:
      - service: notification-service
        min-version: 3
```

Platform teams often provide shared migration infrastructure while allowing services to maintain their own migration files. This might include common Docker images, Kubernetes operators, or CI/CD pipeline templates that standardize migration execution while preserving service autonomy.

### Cross-Service Migration Coordination

Complex systems occasionally require coordinated migrations across multiple services. Consider splitting a monolithic user table into separate user profile and authentication services. This requires careful orchestration to maintain data consistency and avoid service disruption.

Temporary data synchronization during transition periods handles these complex scenarios. The original service continues operating while new services gradually take ownership of specific data subsets. Migration scripts in both services coordinate the data transfer and validation processes.

```go
// Coordinated migration example
type CrossServiceMigration struct {
    sourceService string
    targetService string
    migrationID   string
}

func (csm *CrossServiceMigration) Execute(ctx context.Context) error {
    // Phase 1: Create target schema
    if err := csm.createTargetSchema(ctx); err != nil {
        return err
    }
    
    // Phase 2: Start dual-write to both services
    if err := csm.enableDualWrite(ctx); err != nil {
        return err
    }
    
    // Phase 3: Migrate existing data
    if err := csm.migrateExistingData(ctx); err != nil {
        return err
    }
    
    // Phase 4: Validate data consistency
    if err := csm.validateConsistency(ctx); err != nil {
        return err
    }
    
    // Phase 5: Switch to target service
    return csm.switchToTarget(ctx)
}
```

### Organizational Considerations

Organizational structure and team responsibilities drive migration ownership decisions. Teams with specialized database expertise often choose centralized approaches that capitalize on concentrated knowledge. Organizations prioritizing service autonomy select service-owned patterns despite coordination complexity.

Consider your team's deployment frequency, cross-service dependencies, and operational expertise when choosing migration ownership patterns. High-velocity organizations with independent service teams often benefit from service-owned migrations. Organizations with complex data relationships or regulatory requirements might prefer centralized coordination.

The golang-migrate library supports all these patterns through its flexible architecture and multiple database drivers. Whether migrations live in individual services, centralized repositories, or hybrid configurations, the core migration execution and safety mechanisms remain consistent across different organizational approaches.