package reservation

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"reservation-service/mutex"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/sony/gobreaker"
)

type ReservationRequest struct {
	ResourceID string `json:"resource_id"`
	UserID     string `json:"user_id"`
}

type Handler struct {
	rdb        *redis.Client
	distLocker *mutex.DistributedLocker
	cb         *gobreaker.CircuitBreaker
}

func NewHandler(rdb *redis.Client) *Handler {
	st := gobreaker.Settings{
		Name:        "ReservationDB",
		MaxRequests: 5,
		Interval:    10 * time.Second,
		Timeout:     30 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 3 && failureRatio >= 0.6
		},
	}

	return &Handler{
		rdb:        rdb,
		distLocker: mutex.NewDistributedLocker(rdb),
		cb:         gobreaker.NewCircuitBreaker(st),
	}
}

func (h *Handler) MakeReservation(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// 1. Idempotency Check
	idempotencyKey := r.Header.Get("Idempotency-Key")
	if idempotencyKey == "" {
		http.Error(w, "Missing Idempotency-Key", http.StatusBadRequest)
		return
	}

	cached, err := h.rdb.Get(ctx, "idem:"+idempotencyKey).Result()
	if err == nil {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(cached))
		return
	}

	var req ReservationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// 2. Distributed Lock
	acquired, token, err := h.distLocker.Acquire(ctx, req.ResourceID, 5*time.Second)
	if err != nil {
		http.Error(w, "Locking error", http.StatusInternalServerError)
		return
	}
	if !acquired {
		http.Error(w, "Resource currently locked, try again", http.StatusConflict)
		return
	}
	defer h.distLocker.Release(ctx, req.ResourceID, token)

	// 3. Circuit Breaker for DB Operation
	_, err = h.cb.Execute(func() (interface{}, error) {
		// Simulate DB call
		// In real app: db.Save(reservation)
		time.Sleep(100 * time.Millisecond) // Simulated latency
		return nil, nil
	})

	if err != nil {
		http.Error(w, "Service unavailable (Circuit Breaker)", http.StatusServiceUnavailable)
		return
	}

	// 4. Save Response for Idempotency
	resp := map[string]string{"status": "reserved", "id": req.ResourceID}
	respBytes, _ := json.Marshal(resp)
	
	h.rdb.Set(ctx, "idem:"+idempotencyKey, respBytes, 24*time.Hour)

	w.Header().Set("Content-Type", "application/json")
	w.Write(respBytes)
}
