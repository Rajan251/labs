package mutex

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
)

// LocalLocker uses sync.Mutex for single-instance locking
type LocalLocker struct {
	mu sync.Mutex
}

func (l *LocalLocker) Lock() {
	l.mu.Lock()
}

func (l *LocalLocker) Unlock() {
	l.mu.Unlock()
}

// DistributedLocker uses Redis to lock across services
type DistributedLocker struct {
	client *redis.Client
}

func NewDistributedLocker(rdb *redis.Client) *DistributedLocker {
	return &DistributedLocker{client: rdb}
}

func (d *DistributedLocker) Acquire(ctx context.Context, key string, ttl time.Duration) (bool, string, error) {
	// Simple setnx based lock
	// In production, use Redlock algorithm for higher reliability
	lockKey := fmt.Sprintf("lock:%s", key)
	token := fmt.Sprintf("%d", time.Now().UnixNano())
	
	success, err := d.client.SetNX(ctx, lockKey, token, ttl).Result()
	if err != nil {
		return false, "", err
	}
	
	return success, token, nil
}

func (d *DistributedLocker) Release(ctx context.Context, key string, token string) error {
	lockKey := fmt.Sprintf("lock:%s", key)
	
	// Lua script to safely release lock only if token matches
	script := `
	if redis.call("get", KEYS[1]) == ARGV[1] then
		return redis.call("del", KEYS[1])
	else
		return 0
	end
	`
	_, err := d.client.Eval(ctx, script, []string{lockKey}, token).Result()
	return err
}
