package main

import (
	"crypto/aes"
	"crypto/sha256"
	"encoding/json"
	"net/http"
	"time"
)

func main() {
	var v map[string]any
	json.Unmarshal([]byte(`{"a":1,"b":[1,2,3]}`), &v)
	b, _ := json.Marshal(v)
	sha256.Sum256(b)
	aes.NewCipher(make([]byte, 16))
	_ = &http.Client{Timeout: 5 * time.Second}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("OK")) })
	http.ListenAndServe(":8080", nil)
}