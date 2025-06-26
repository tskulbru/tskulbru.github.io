---
layout: ../../layouts/post.astro
title: "Building Resilient Microservices on Kubernetes: Circuit Breakers, Retries, and Chaos Engineering"
pubDate: 2025-06-26
description: "Implement production-grade resilience patterns in Kubernetes microservices using circuit breakers, intelligent retry mechanisms, and chaos engineering to handle failures gracefully and maintain system stability under adverse conditions."
author: "Torstein Skulbru"
isPinned: false
excerpt: "Production microservices fail in unpredictable ways. Learn how to implement circuit breaker patterns, exponential backoff strategies, and chaos engineering practices that transform brittle service interactions into resilient, self-healing systems capable of graceful degradation."
image:
  src: "/images/interconnected-microservices.jpg"
  alt: "Network of interconnected nodes representing resilient microservices architecture"
tags: ["kubernetes", "microservices", "resilience", "chaos-engineering", "golang"]
---

Distributed systems fail in fascinating ways. A single service timeout can cascade through your entire platform if you're not careful. A naive retry loop can turn a minor hiccup into a system-wide outage. A service that appears healthy can actually be failing every request because its dependencies are down.

Building resilient microservices means accepting that failures are inevitable and designing systems that handle them gracefully. This isn't about preventing failures—that's impossible in distributed systems. It's about containing failures, recovering quickly, and maintaining functionality even when individual components break.

This guide explores three interconnected patterns that transform brittle microservices into resilient systems: circuit breakers that prevent cascade failures, intelligent retry mechanisms that avoid overwhelming recovering services, and chaos engineering that validates your assumptions about how systems behave under stress. These patterns work together to create services that degrade gracefully rather than failing catastrophically.

## Circuit Breakers: Your First Line of Defense

Think of a circuit breaker like the electrical breakers in your house. When there's a power surge, the breaker trips to protect your appliances. In microservices, circuit breakers do the same thing—they monitor calls to external services and "trip" when those services start failing, protecting both your service and the failing dependency from further damage.

The genius of circuit breakers lies in their simplicity. Instead of continuously hammering a failing API, the circuit breaker steps in after a few failures and starts returning errors immediately. This gives the failing service breathing room to recover while your service can handle the situation gracefully—maybe by using cached data, showing a friendly error message, or falling back to a different service.

Circuit breakers operate in three states that mirror how you'd handle a problematic situation in real life. When everything's working (closed state), requests flow through normally. When failures pile up, the breaker opens and starts failing fast. After a timeout period, it enters a half-open state, cautiously testing if the service has recovered. If the test succeeds, normal operation resumes; if not, it snaps back to the open state.

### Building a Production-Ready Circuit Breaker

While several circuit breaker libraries exist (like [Sony's gobreaker](https://github.com/sony/gobreaker) which is widely used in production), building your own provides fine-grained control over behavior and helps you understand exactly how the pattern works. This implementation handles concurrent access safely, provides detailed metrics, and behaves predictably under load. The key insight is that circuit breakers need to be thread-safe and maintain accurate state even when hundreds of goroutines are making concurrent requests.

```go
// pkg/circuitbreaker/breaker.go
package circuitbreaker

import (
    "context"
    "errors"
    "sync"
    "time"
)

type State int

const (
    StateClosed State = iota
    StateOpen
    StateHalfOpen
)

type Config struct {
    MaxRequests      uint32
    Interval         time.Duration
    Timeout          time.Duration
    ReadyToTrip      func(counts Counts) bool
    OnStateChange    func(name string, from State, to State)
}

type Counts struct {
    Requests             uint32
    TotalSuccesses       uint32
    TotalFailures        uint32
    ConsecutiveSuccesses uint32
    ConsecutiveFailures  uint32
}

type CircuitBreaker struct {
    name          string
    maxRequests   uint32
    interval      time.Duration
    timeout       time.Duration
    readyToTrip   func(counts Counts) bool
    onStateChange func(name string, from State, to State)

    mutex      sync.Mutex
    state      State
    generation uint64
    counts     Counts
    expiry     time.Time
}

var (
    ErrTooManyRequests = errors.New("circuit breaker: too many requests")
    ErrOpenState       = errors.New("circuit breaker: circuit breaker is open")
)

func NewCircuitBreaker(name string, config Config) *CircuitBreaker {
    cb := &CircuitBreaker{
        name:          name,
        maxRequests:   config.MaxRequests,
        interval:      config.Interval,
        timeout:       config.Timeout,
        readyToTrip:   config.ReadyToTrip,
        onStateChange: config.OnStateChange,
    }

    if cb.maxRequests == 0 {
        cb.maxRequests = 1
    }

    if cb.interval <= 0 {
        cb.interval = time.Duration(0)
    }

    if cb.timeout <= 0 {
        cb.timeout = 60 * time.Second
    }

    if cb.readyToTrip == nil {
        cb.readyToTrip = func(counts Counts) bool {
            return counts.ConsecutiveFailures > 5
        }
    }

    cb.toNewGeneration(time.Now())
    return cb
}

func (cb *CircuitBreaker) Execute(ctx context.Context, req func() (interface{}, error)) (interface{}, error) {
    generation, err := cb.beforeRequest()
    if err != nil {
        return nil, err
    }

    defer func() {
        if r := recover(); r != nil {
            cb.afterRequest(generation, false)
            panic(r)
        }
    }()

    result, err := req()
    cb.afterRequest(generation, err == nil)
    return result, err
}

func (cb *CircuitBreaker) beforeRequest() (uint64, error) {
    cb.mutex.Lock()
    defer cb.mutex.Unlock()

    now := time.Now()
    state, generation := cb.currentState(now)

    if state == StateOpen {
        return generation, ErrOpenState
    } else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {
        return generation, ErrTooManyRequests
    }

    cb.counts.Requests++
    return generation, nil
}

func (cb *CircuitBreaker) afterRequest(before uint64, success bool) {
    cb.mutex.Lock()
    defer cb.mutex.Unlock()

    now := time.Now()
    state, generation := cb.currentState(now)
    if generation != before {
        return
    }

    if success {
        cb.onSuccess(state, now)
    } else {
        cb.onFailure(state, now)
    }
}

func (cb *CircuitBreaker) onSuccess(state State, now time.Time) {
    cb.counts.TotalSuccesses++
    cb.counts.ConsecutiveSuccesses++
    cb.counts.ConsecutiveFailures = 0

    if state == StateHalfOpen {
        cb.setState(StateClosed, now)
    }
}

func (cb *CircuitBreaker) onFailure(state State, now time.Time) {
    cb.counts.TotalFailures++
    cb.counts.ConsecutiveFailures++
    cb.counts.ConsecutiveSuccesses = 0

    if cb.readyToTrip(cb.counts) {
        cb.setState(StateOpen, now)
    }
}

func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {
    switch cb.state {
    case StateClosed:
        if !cb.expiry.IsZero() && cb.expiry.Before(now) {
            cb.toNewGeneration(now)
        }
    case StateOpen:
        if cb.expiry.Before(now) {
            cb.setState(StateHalfOpen, now)
        }
    }
    return cb.state, cb.generation
}

func (cb *CircuitBreaker) setState(state State, now time.Time) {
    if cb.state == state {
        return
    }

    prev := cb.state
    cb.state = state

    cb.toNewGeneration(now)

    if cb.onStateChange != nil {
        cb.onStateChange(cb.name, prev, state)
    }
}

func (cb *CircuitBreaker) toNewGeneration(now time.Time) {
    cb.generation++
    cb.counts = Counts{}

    var zero time.Time
    switch cb.state {
    case StateClosed:
        if cb.interval == 0 {
            cb.expiry = zero
        } else {
            cb.expiry = now.Add(cb.interval)
        }
    case StateOpen:
        cb.expiry = now.Add(cb.timeout)
    default: // StateHalfOpen
        cb.expiry = zero
    }
}

// GetState returns the current state of the circuit breaker
func (cb *CircuitBreaker) GetState() State {
    cb.mutex.Lock()
    defer cb.mutex.Unlock()
    
    now := time.Now()
    state, _ := cb.currentState(now)
    return state
}

// GetCounts returns the current counts
func (cb *CircuitBreaker) GetCounts() Counts {
    cb.mutex.Lock()
    defer cb.mutex.Unlock()
    
    return cb.counts
}
```

### Integrating Circuit Breakers into Your Services

The real magic happens when you integrate circuit breakers into your actual service calls. Wrapping HTTP clients with circuit breaker logic provides protection without cluttering your business logic. This approach keeps the resilience concerns separate from the core functionality.

The key insight is configuring the circuit breaker based on your service's specific needs. Different services have different tolerance levels for failures. A user lookup service might tolerate a 60% failure rate before tripping because users can wait for retries. A payment service might trip at 20% because failed payments have immediate business impact. The `OnStateChange` callback enables monitoring—you need visibility when circuit breakers start tripping in production.

```go
// internal/services/user_service.go
package services

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "your-app/pkg/circuitbreaker"
    "your-app/pkg/metrics"
)

type UserService struct {
    httpClient     *http.Client
    circuitBreaker *circuitbreaker.CircuitBreaker
    baseURL        string
    metrics        *metrics.ServiceMetrics
}

type User struct {
    ID       string `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
}

func NewUserService(baseURL string, metrics *metrics.ServiceMetrics) *UserService {
    config := circuitbreaker.Config{
        MaxRequests: 3,
        Interval:    10 * time.Second,
        Timeout:     30 * time.Second,
        ReadyToTrip: func(counts circuitbreaker.Counts) bool {
            failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
            return counts.Requests >= 3 && failureRatio >= 0.6
        },
        OnStateChange: func(name string, from circuitbreaker.State, to circuitbreaker.State) {
            metrics.RecordCircuitBreakerStateChange(name, from.String(), to.String())
        },
    }

    return &UserService{
        httpClient: &http.Client{
            Timeout: 5 * time.Second,
        },
        circuitBreaker: circuitbreaker.NewCircuitBreaker("user-service", config),
        baseURL:        baseURL,
        metrics:        metrics,
    }
}

func (s *UserService) GetUser(ctx context.Context, userID string) (*User, error) {
    result, err := s.circuitBreaker.Execute(ctx, func() (interface{}, error) {
        return s.fetchUser(ctx, userID)
    })

    if err != nil {
        s.metrics.RecordServiceCall("user-service", "get-user", "error")
        return nil, fmt.Errorf("failed to get user %s: %w", userID, err)
    }

    s.metrics.RecordServiceCall("user-service", "get-user", "success")
    return result.(*User), nil
}

func (s *UserService) fetchUser(ctx context.Context, userID string) (*User, error) {
    url := fmt.Sprintf("%s/users/%s", s.baseURL, userID)
    
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }

    resp, err := s.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("request failed: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
    }

    var user User
    if err := json.NewDecoder(resp.Body).Decode(&user); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }

    return &user, nil
}
```

## Smart Retries: When to Try Again (and When to Give Up)

Many developers implement retries without considering the broader implications. Some systems retry everything, including 404s and authentication failures, creating endless loops of futile attempts. Others give up too easily, treating temporary network hiccups as permanent failures. Both approaches miss the nuanced reality of distributed systems.

The art of intelligent retries lies in knowing what to retry, when to retry, and when to stop. A 500 Internal Server Error from your payment processor? Definitely worth retrying—their server might be temporarily overloaded. A 401 Unauthorized response? Don't bother retrying; your API key is wrong or expired, and hammering their server won't fix it.

But even when you know what to retry, the timing matters enormously. If your service and 50 others all retry a failing service at the same intervals, you create a thundering herd that can prevent the service from recovering. This is where exponential backoff with jitter becomes your friend—it spreads retry attempts across time, giving the failing service breathing room while still providing reasonable recovery times.

### The Math Behind Smart Retries

This retry mechanism demonstrates several important principles. The exponential backoff prevents overwhelming recovering services by increasing delays between attempts (100ms, 200ms, 400ms, etc.). The jitter adds randomness to prevent the thundering herd problem—instead of all clients retrying at exactly 200ms, they retry anywhere from 180ms to 220ms.

This randomization is more important than it might seem. Without jitter, synchronized retries can prevent a service from recovering by overwhelming it precisely when it tries to come back online. The small amount of randomness breaks this synchronization and gives failing services breathing room to stabilize.

```go
// pkg/retry/retry.go
package retry

import (
    "context"
    "errors"
    "math"
    "math/rand"
    "time"
)

type Config struct {
    MaxAttempts     int
    InitialDelay    time.Duration
    MaxDelay        time.Duration
    BackoffFactor   float64
    JitterPercent   float64
    RetryableErrors []error
    IsRetryable     func(error) bool
}

type Retryer struct {
    config Config
    rand   *rand.Rand
}

func NewRetryer(config Config) *Retryer {
    if config.MaxAttempts <= 0 {
        config.MaxAttempts = 3
    }
    if config.InitialDelay <= 0 {
        config.InitialDelay = 100 * time.Millisecond
    }
    if config.MaxDelay <= 0 {
        config.MaxDelay = 30 * time.Second
    }
    if config.BackoffFactor <= 0 {
        config.BackoffFactor = 2.0
    }
    if config.JitterPercent < 0 || config.JitterPercent > 1 {
        config.JitterPercent = 0.1
    }

    return &Retryer{
        config: config,
        rand:   rand.New(rand.NewSource(time.Now().UnixNano())),
    }
}

func (r *Retryer) Execute(ctx context.Context, operation func() error) error {
    var lastErr error

    for attempt := 0; attempt < r.config.MaxAttempts; attempt++ {
        if attempt > 0 {
            delay := r.calculateDelay(attempt)
            select {
            case <-time.After(delay):
            case <-ctx.Done():
                return ctx.Err()
            }
        }

        err := operation()
        if err == nil {
            return nil
        }

        lastErr = err

        if !r.isRetryable(err) {
            return err
        }

        if attempt == r.config.MaxAttempts-1 {
            break
        }
    }

    return lastErr
}

func (r *Retryer) calculateDelay(attempt int) time.Duration {
    delay := float64(r.config.InitialDelay) * math.Pow(r.config.BackoffFactor, float64(attempt-1))
    
    if delay > float64(r.config.MaxDelay) {
        delay = float64(r.config.MaxDelay)
    }

    // Add jitter to prevent thundering herd
    jitter := delay * r.config.JitterPercent
    jitterRange := jitter * 2
    actualJitter := r.rand.Float64()*jitterRange - jitter
    
    finalDelay := time.Duration(delay + actualJitter)
    if finalDelay < 0 {
        finalDelay = time.Duration(delay)
    }

    return finalDelay
}

func (r *Retryer) isRetryable(err error) bool {
    if r.config.IsRetryable != nil {
        return r.config.IsRetryable(err)
    }

    for _, retryableErr := range r.config.RetryableErrors {
        if errors.Is(err, retryableErr) {
            return true
        }
    }

    return false
}
```

### Bringing It All Together: Resilient HTTP Clients

A resilient HTTP client combines circuit breakers and retry logic to handle the messy reality of distributed systems. This implementation automatically handles network timeouts, server errors, and circuit breaker states while making intelligent decisions about what should and shouldn't be retried.

Notice how the retry logic respects circuit breaker decisions. If the circuit breaker is open, we don't retry—the breaker has already determined the service is unhealthy. This prevents the retry mechanism from fighting against the circuit breaker's protective behavior.

```go
// pkg/httpclient/resilient_client.go
package httpclient

import (
    "context"
    "fmt"
    "net"
    "net/http"
    "syscall"
    "time"

    "your-app/pkg/circuitbreaker"
    "your-app/pkg/retry"
)

type ResilientClient struct {
    httpClient     *http.Client
    circuitBreaker *circuitbreaker.CircuitBreaker
    retryer        *retry.Retryer
}

func NewResilientClient(name string) *ResilientClient {
    // Configure circuit breaker for HTTP calls
    cbConfig := circuitbreaker.Config{
        MaxRequests: 5,
        Interval:    30 * time.Second,
        Timeout:     60 * time.Second,
        ReadyToTrip: func(counts circuitbreaker.Counts) bool {
            return counts.ConsecutiveFailures >= 3
        },
    }

    // Configure retry with intelligent error classification
    retryConfig := retry.Config{
        MaxAttempts:   3,
        InitialDelay:  200 * time.Millisecond,
        MaxDelay:      5 * time.Second,
        BackoffFactor: 2.0,
        JitterPercent: 0.1,
        IsRetryable:   isHTTPRetryable,
    }

    return &ResilientClient{
        httpClient: &http.Client{
            Timeout: 10 * time.Second,
            Transport: &http.Transport{
                MaxIdleConns:        100,
                MaxIdleConnsPerHost: 10,
                IdleConnTimeout:     90 * time.Second,
            },
        },
        circuitBreaker: circuitbreaker.NewCircuitBreaker(name, cbConfig),
        retryer:        retry.NewRetryer(retryConfig),
    }
}

func (c *ResilientClient) Do(ctx context.Context, req *http.Request) (*http.Response, error) {
    var resp *http.Response
    var err error

    // Wrap the HTTP call with retry logic
    retryErr := c.retryer.Execute(ctx, func() error {
        // Execute through circuit breaker
        result, cbErr := c.circuitBreaker.Execute(ctx, func() (interface{}, error) {
            return c.httpClient.Do(req.WithContext(ctx))
        })

        if cbErr != nil {
            return cbErr
        }

        resp = result.(*http.Response)
        
        // Check if response indicates a retryable server error
        if resp.StatusCode >= 500 {
            return fmt.Errorf("server error: %d", resp.StatusCode)
        }

        return nil
    })

    if retryErr != nil {
        return nil, retryErr
    }

    return resp, nil
}

func isHTTPRetryable(err error) bool {
    // Network-level errors are typically retryable
    if netErr, ok := err.(*net.OpError); ok {
        if netErr.Timeout() {
            return true
        }
        if netErr.Temporary() {
            return true
        }
    }

    // Connection refused and connection reset are retryable
    if err == syscall.ECONNREFUSED || err == syscall.ECONNRESET {
        return true
    }

    // Context timeout is not retryable (caller's decision)
    if err == context.DeadlineExceeded {
        return false
    }

    // Circuit breaker errors are not retryable (circuit breaker handles the logic)
    if err == circuitbreaker.ErrOpenState || err == circuitbreaker.ErrTooManyRequests {
        return false
    }

    // HTTP 5xx errors are retryable, 4xx are not
    if httpErr, ok := err.(*HTTPError); ok {
        return httpErr.StatusCode >= 500
    }

    return false
}

type HTTPError struct {
    StatusCode int
    Message    string
}

func (e *HTTPError) Error() string {
    return fmt.Sprintf("HTTP %d: %s", e.StatusCode, e.Message)
}
```

## Making It Production-Ready on Kubernetes

Having resilient code is only half the battle—you need to deploy it properly on Kubernetes to get the full benefits. Perfectly resilient application code can still cause outages if your Kubernetes configuration doesn't support graceful failures and recovery.

The deployment configuration below demonstrates several important principles. Proper resource limits prevent one failing service from consuming all cluster resources. Health checks ensure Kubernetes knows when your service is actually ready to handle traffic. Pod disruption budgets prevent too many instances from being terminated simultaneously during cluster maintenance.

### The Deployment Configuration That Actually Works

This deployment manifest demonstrates several resilience principles in action. The anti-affinity rules ensure your pods don't all land on the same node, protecting against node failures. The three different health check endpoints serve different purposes—liveness checks if the process is alive, readiness checks if it can handle traffic, and startup checks give slow-starting applications time to initialize properly.

```yaml
# deployments/order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
  labels:
    app: order-service
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: order-service
        image: myregistry.com/order-service:v1.2.3
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8081
          name: health
        env:
        - name: USER_SERVICE_URL
          value: "http://user-service:8080"
        - name: PAYMENT_SERVICE_URL
          value: "http://payment-service:8080"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: connection-string
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - order-service
              topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: production
  labels:
    app: order-service
spec:
  selector:
    app: order-service
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: order-service-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: order-service
```

### Health Checks That Tell the Truth

Naive health checks can make problems worse. If your health check only verifies that your web server is responding but doesn't check if your database connection is working, Kubernetes will happily send traffic to a service that can't actually fulfill requests.

The health checker below implements a nuanced approach. The liveness check is simple—it just confirms the service process is alive. The readiness check is more thorough, verifying that all dependencies are available. This separation is crucial because you want different behaviors: if liveness fails, restart the pod; if readiness fails, stop sending traffic but don't restart (the dependencies might recover).

```go
// internal/health/health.go
package health

import (
    "context"
    "encoding/json"
    "net/http"
    "sync"
    "time"

    "your-app/internal/services"
)

type HealthChecker struct {
    userService    *services.UserService
    paymentService *services.PaymentService
    database       *Database
}

type HealthStatus struct {
    Status      string            `json:"status"`
    Timestamp   time.Time         `json:"timestamp"`
    Duration    string            `json:"duration"`
    Checks      map[string]Check  `json:"checks"`
}

type Check struct {
    Status   string `json:"status"`
    Duration string `json:"duration,omitempty"`
    Error    string `json:"error,omitempty"`
}

func NewHealthChecker(userSvc *services.UserService, paymentSvc *services.PaymentService, db *Database) *HealthChecker {
    return &HealthChecker{
        userService:    userSvc,
        paymentService: paymentSvc,
        database:       db,
    }
}

func (h *HealthChecker) LivenessHandler(w http.ResponseWriter, r *http.Request) {
    // Liveness check should only verify the service itself is running
    status := HealthStatus{
        Status:    "UP",
        Timestamp: time.Now(),
        Duration:  "0ms",
        Checks:    make(map[string]Check),
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(status)
}

func (h *HealthChecker) ReadinessHandler(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    status := HealthStatus{
        Status:    "UP",
        Timestamp: start,
        Checks:    make(map[string]Check),
    }

    // Check all dependencies concurrently
    var wg sync.WaitGroup
    var mu sync.Mutex

    checks := []struct {
        name string
        fn   func(context.Context) error
    }{
        {"database", h.database.Ping},
        {"user-service", h.userService.HealthCheck},
        {"payment-service", h.paymentService.HealthCheck},
    }

    for _, check := range checks {
        wg.Add(1)
        go func(name string, fn func(context.Context) error) {
            defer wg.Done()
            
            checkStart := time.Now()
            err := fn(ctx)
            duration := time.Since(checkStart)

            mu.Lock()
            defer mu.Unlock()

            if err != nil {
                status.Status = "DOWN"
                status.Checks[name] = Check{
                    Status:   "DOWN",
                    Duration: duration.String(),
                    Error:    err.Error(),
                }
            } else {
                status.Checks[name] = Check{
                    Status:   "UP",
                    Duration: duration.String(),
                }
            }
        }(check.name, check.fn)
    }

    wg.Wait()
    status.Duration = time.Since(start).String()

    w.Header().Set("Content-Type", "application/json")
    if status.Status == "UP" {
        w.WriteHeader(http.StatusOK)
    } else {
        w.WriteHeader(http.StatusServiceUnavailable)
    }
    json.NewEncoder(w).Encode(status)
}

func (h *HealthChecker) StartupHandler(w http.ResponseWriter, r *http.Request) {
    // Startup probe can be more thorough than readiness
    h.ReadinessHandler(w, r)
}
```

## Chaos Engineering: Breaking Things on Purpose

Chaos engineering involves intentionally breaking your system to see how it behaves. This might sound counterintuitive, but systematically introducing failures in controlled environments helps you discover weaknesses before they cause real problems.

Chaos experiments often reveal unexpected behaviors. Circuit breakers might work perfectly for single service failures but behave differently during network partitions. Retry logic might handle timeouts well but create cascading failures when services return partial data. These are issues that traditional testing rarely uncovers because it focuses on happy path scenarios.

Litmus provides Kubernetes-native chaos engineering because it's designed specifically for cloud-native environments. Instead of trying to simulate failures from outside the cluster, Litmus runs experiments as Kubernetes resources, making them easy to version control, schedule, and integrate into your CI/CD pipeline.

### Getting Litmus Running on Your Kubernetes Cluster

Setting up Litmus is straightforward, but start with a staging environment that mirrors your production setup. Understanding how your system behaves under controlled chaos is essential before considering production experiments. Some teams do run chaos experiments in production, but that requires significant maturity in monitoring, alerting, and incident response.

```bash
# Install Litmus operator
kubectl apply -f https://litmuschaos.github.io/litmus/2.14.0/litmus-2.14.0.yaml

# Verify installation
kubectl get pods -n litmus

# Install chaos experiments
kubectl apply -f https://hub.litmuschaos.io/api/chaos/2.14.0?file=charts/generic/experiments.yaml
```

### Your First Chaos Experiments

Pod deletion experiments are the most straightforward and reveal common issues. The experiment below kills 33% of your order service pods and monitors whether your service remains available. This simulates what happens during deployments, node failures, or when Kubernetes reschedules pods for resource optimization.

The network latency experiment simulates real-world conditions where services don't fail completely but become slow and unreliable. This reveals whether your timeouts are configured correctly and whether your circuit breakers trip at appropriate thresholds. Partial failures are often more dangerous than complete failures because they're harder to detect and can cause subtle degradation.

```yaml
# chaos-experiments/pod-delete-experiment.yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: order-service-pod-delete
  namespace: production
spec:
  engineState: 'active'
  appinfo:
    appns: 'production'
    applabel: 'app=order-service'
    appkind: 'deployment'
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-delete
    spec:
      components:
        env:
        - name: TOTAL_CHAOS_DURATION
          value: '60'
        - name: CHAOS_INTERVAL
          value: '10'
        - name: FORCE
          value: 'false'
        - name: PODS_AFFECTED_PERC
          value: '33'
      probe:
      - name: order-service-availability
        type: httpProbe
        mode: Continuous
        runProperties:
          probeTimeout: 5s
          retry: 3
          interval: 2s
          probePollingInterval: 2s
        httpProbe/inputs:
          url: http://order-service:8080/health/ready
          insecureSkipTLS: false
          method:
            get:
              criteria: ==
              responseCode: "200"
---
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: user-service-network-chaos
  namespace: production
spec:
  engineState: 'active'
  appinfo:
    appns: 'production'
    applabel: 'app=user-service'
    appkind: 'deployment'
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-network-latency
    spec:
      components:
        env:
        - name: TARGET_CONTAINER
          value: 'user-service'
        - name: NETWORK_INTERFACE
          value: 'eth0'
        - name: NETWORK_LATENCY
          value: '2000'
        - name: TOTAL_CHAOS_DURATION
          value: '120'
        - name: PODS_AFFECTED_PERC
          value: '50'
        - name: JITTER
          value: '0'
      probe:
      - name: order-service-response-time
        type: httpProbe
        mode: Continuous
        runProperties:
          probeTimeout: 10s
          retry: 2
          interval: 5s
        httpProbe/inputs:
          url: http://order-service:8080/orders/health-check
          insecureSkipTLS: false
          method:
            get:
              criteria: <=
              responseTimeout: 8000ms
```

### Automating Chaos: Making It Part of Your Process

The real power of chaos engineering comes from making it a regular part of your development process. Automated chaos experiments can catch regressions that would cause production outages. The key is treating chaos experiments like any other test—they should be automated, repeatable, and integrated into your CI/CD pipeline.

The GitHub Actions workflow below shows how to run chaos experiments as part of your deployment process. Running them on a schedule during off-hours allows teams to respond to any issues discovered without the pressure of active development work.

```yaml
# .github/workflows/chaos-testing.yml
name: Chaos Engineering Tests

on:
  schedule:
    - cron: '0 2 * * 1-5'  # Run weekdays at 2 AM
  workflow_dispatch:

jobs:
  chaos-tests:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Run Pod Delete Chaos
      run: |
        kubectl apply -f chaos-experiments/pod-delete-experiment.yaml
        
        # Wait for experiment completion
        timeout 300 bash -c 'until kubectl get chaosengine order-service-pod-delete -n production -o jsonpath="{.status.engineStatus}" | grep -q "stopped"; do sleep 10; done'
        
        # Check experiment result
        RESULT=$(kubectl get chaosengine order-service-pod-delete -n production -o jsonpath="{.status.experimentStatus[0].verdict}")
        if [ "$RESULT" != "Pass" ]; then
          echo "Chaos experiment failed: $RESULT"
          exit 1
        fi

    - name: Run Network Latency Chaos
      run: |
        kubectl apply -f chaos-experiments/network-latency-experiment.yaml
        
        timeout 400 bash -c 'until kubectl get chaosengine user-service-network-chaos -n production -o jsonpath="{.status.engineStatus}" | grep -q "stopped"; do sleep 10; done'
        
        RESULT=$(kubectl get chaosengine user-service-network-chaos -n production -o jsonpath="{.status.experimentStatus[0].verdict}")
        if [ "$RESULT" != "Pass" ]; then
          echo "Network chaos experiment failed: $RESULT"
          exit 1
        fi

    - name: Cleanup
      if: always()
      run: |
        kubectl delete chaosengine --all -n production
```

## Watching Your Resilience Patterns in Action

Resilience patterns are only effective if you can observe their behavior. You need to know when circuit breakers are tripping, how often retries are happening, and whether your chaos experiments are actually validating the right behaviors. Without visibility, you might have perfectly functioning resilience mechanisms that you can't understand or debug.

Monitoring resilience patterns reveals important insights about system health. Circuit breakers that trip frequently might indicate upstream service issues. Retry patterns that show exponential growth might suggest cascading failures. Service call duration spikes during chaos experiments validate whether your resilience mechanisms are working as expected.

### The Metrics That Matter

The metrics implementation below captures information needed during incidents. Circuit breaker state changes indicate when services are degrading. Retry attempt patterns reveal whether your backoff strategies are working. Service call duration histograms show the impact of resilience patterns on user experience—sometimes a circuit breaker that fails fast provides a better user experience than slow retries.

```go
// pkg/metrics/resilience_metrics.go
package metrics

import (
    "fmt"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

type ResilienceMetrics struct {
    circuitBreakerState     *prometheus.GaugeVec
    circuitBreakerRequests  *prometheus.CounterVec
    retryAttempts          *prometheus.CounterVec
    serviceCallDuration    *prometheus.HistogramVec
    dependencyHealth       *prometheus.GaugeVec
}

func NewResilienceMetrics() *ResilienceMetrics {
    return &ResilienceMetrics{
        circuitBreakerState: promauto.NewGaugeVec(
            prometheus.GaugeOpts{
                Name: "circuit_breaker_state",
                Help: "Current state of circuit breakers (0=closed, 1=open, 2=half-open)",
            },
            []string{"service", "circuit_breaker"},
        ),
        circuitBreakerRequests: promauto.NewCounterVec(
            prometheus.CounterOpts{
                Name: "circuit_breaker_requests_total",
                Help: "Total number of requests through circuit breakers",
            },
            []string{"service", "circuit_breaker", "state", "result"},
        ),
        retryAttempts: promauto.NewCounterVec(
            prometheus.CounterOpts{
                Name: "retry_attempts_total",
                Help: "Total number of retry attempts",
            },
            []string{"service", "operation", "attempt"},
        ),
        serviceCallDuration: promauto.NewHistogramVec(
            prometheus.HistogramOpts{
                Name:    "service_call_duration_seconds",
                Help:    "Duration of service calls including retries",
                Buckets: prometheus.DefBuckets,
            },
            []string{"service", "operation", "result"},
        ),
        dependencyHealth: promauto.NewGaugeVec(
            prometheus.GaugeOpts{
                Name: "dependency_health_status",
                Help: "Health status of service dependencies (1=healthy, 0=unhealthy)",
            },
            []string{"service", "dependency"},
        ),
    }
}

func (m *ResilienceMetrics) RecordCircuitBreakerState(service, name string, state int) {
    m.circuitBreakerState.WithLabelValues(service, name).Set(float64(state))
}

func (m *ResilienceMetrics) RecordCircuitBreakerRequest(service, name, state, result string) {
    m.circuitBreakerRequests.WithLabelValues(service, name, state, result).Inc()
}

func (m *ResilienceMetrics) RecordRetryAttempt(service, operation string, attempt int) {
    m.retryAttempts.WithLabelValues(service, operation, fmt.Sprintf("%d", attempt)).Inc()
}

func (m *ResilienceMetrics) RecordServiceCall(service, operation, result string, duration time.Duration) {
    m.serviceCallDuration.WithLabelValues(service, operation, result).Observe(duration.Seconds())
}

func (m *ResilienceMetrics) RecordDependencyHealth(service, dependency string, healthy bool) {
    value := 0.0
    if healthy {
        value = 1.0
    }
    m.dependencyHealth.WithLabelValues(service, dependency).Set(value)
}
```

### Dashboards That Tell the Story

The Grafana dashboard configuration below creates visualizations that help you understand system behavior at a glance. The circuit breaker state panel uses color coding to immediately show which services are experiencing issues. The success rate panel helps you understand the business impact of failures. The retry attempts graph reveals patterns that might indicate systemic issues rather than isolated failures.

```json
{
  "dashboard": {
    "title": "Microservices Resilience Dashboard",
    "panels": [
      {
        "title": "Circuit Breaker States",
        "type": "stat",
        "targets": [
          {
            "expr": "circuit_breaker_state",
            "legendFormat": "{{service}}-{{circuit_breaker}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "CLOSED", "color": "green"}}},
              {"options": {"1": {"text": "OPEN", "color": "red"}}},
              {"options": {"2": {"text": "HALF-OPEN", "color": "yellow"}}}
            ]
          }
        }
      },
      {
        "title": "Service Call Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(circuit_breaker_requests_total{result=\"success\"}[5m]) / rate(circuit_breaker_requests_total[5m]) * 100",
            "legendFormat": "{{service}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 95},
                {"color": "green", "value": 99}
              ]
            }
          }
        }
      },
      {
        "title": "Retry Attempts by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(retry_attempts_total[5m])",
            "legendFormat": "{{service}}-{{operation}}-attempt-{{attempt}}"
          }
        ]
      },
      {
        "title": "Service Call Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(service_call_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile - {{service}}"
          },
          {
            "expr": "histogram_quantile(0.50, rate(service_call_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile - {{service}}"
          }
        ]
      }
    ]
  }
}
```

## The Resilience Mindset

Building resilient microservices isn't just about implementing circuit breakers and retry logic—it's about fundamentally changing how you think about failure. Instead of trying to prevent all failures (impossible), you design systems that handle failures gracefully and recover automatically.

These patterns represent proven approaches to handling distributed system failures. They're not theoretical concepts but practical solutions that address real problems in production environments. The circuit breakers stop cascade failures before they spread. The intelligent retry mechanisms handle transient issues without overwhelming recovering services. The chaos engineering validates that everything actually works when things go wrong.

Most importantly, these patterns work together as a system. Circuit breakers and retries complement each other rather than fighting. Monitoring provides visibility into their effectiveness. Chaos engineering validates their behavior under realistic failure conditions. When you implement all these patterns together, you get something greater than the sum of their parts—a truly resilient system that maintains functionality even when individual components fail.

When designing microservices, remember that failures are not edge cases to be handled later—they're fundamental characteristics of distributed systems that should be designed for from the beginning. Building resilience into your architecture from the start is far easier than retrofitting it later when you're dealing with production incidents. 