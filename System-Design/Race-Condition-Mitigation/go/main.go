package main

import (
	"log"
	"net/http"
	"os"
	"reservation-service/reservation"

	"github.com/go-redis/redis/v8"
)

func main() {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	rdb := redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	handler := reservation.NewHandler(rdb)

	http.HandleFunc("/reserve", handler.MakeReservation)

	log.Println("Starting Go Reservation Service on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}
