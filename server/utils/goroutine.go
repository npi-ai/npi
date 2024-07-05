package utils

import (
	"time"
)

func RunAfter(f func(), d time.Duration) {
	go func() {
		time.Sleep(d)
		f()
	}()
}
