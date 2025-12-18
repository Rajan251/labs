package main

import (
    "context"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "go.uber.org/zap"
    "go-ha-service/pkg/db"
)

func main() {
    // 1. Structured Logging
    logger, _ := zap.NewProduction()
    defer logger.Sync()
    sugar := logger.Sugar()

    // 2. Database Connection
    _, err := db.NewConnection(db.Config{
        Host: "localhost", Port: 5432, User: "postgres", Password: "password", DBName: "postgres",
    })
    if err != nil {
        sugar.Fatalf("Failed to connect to DB: %v", err)
    }

    // 3. Router & Middleware
    r := chi.NewRouter()
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.Timeout(60 * time.Second))

    r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("OK"))
    })

    server := &http.Server{
        Addr:    ":8080",
        Handler: r,
    }

    // 4. Graceful Shutdown
    go func() {
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            sugar.Fatalf("Listen: %s\n", err)
        }
    }()
    sugar.Info("Server started on :8080")

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    sugar.Info("Shutting down server...")

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        sugar.Fatal("Server forced to shutdown:", err)
    }

    sugar.Info("Server exiting")
}
