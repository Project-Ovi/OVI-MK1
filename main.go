package main

import (
	"bufio"
	"fmt"
	"net"
	"net/http"
	"os"
	"path"
	"time"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

var live_feed []byte
var commands_feed = []byte{}

// readFullMessage reads the entire message from the reader
func readFullMessage(reader *bufio.Reader) (string, error) {
	var message string
	for {
		// Read bytes from the connection
		line, err := reader.ReadString('\n')
		if err != nil {
			return message, err
		}
		message += line
		// Check if message ends with newline
		if line[len(line)-1] == '\n' {
			return message, nil
		}
	}
}

func handler(w http.ResponseWriter, r *http.Request) {
	// Upgrade the HTTP connection to a WebSocket connection
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		//fmt.Println("Error upgrading to WebSocket:", err)
		return
	}
	defer conn.Close()

	for {
		go func() {
			defer func() {
				if r := recover(); r != nil {
					//fmt.Println("Recovered from panic:", r)
					return
				}
			}()

			_, commands_feed, err = conn.ReadMessage()
			if err != nil {
				//log.Println(err)
				time.Sleep(time.Second)
			}
		}()

		// Echo message back to client
		err = conn.WriteMessage(websocket.TextMessage, live_feed)
		if err != nil {
			//fmt.Println("Error writing message:", err)
			time.Sleep(time.Second)
		}

		time.Sleep(time.Millisecond)
	}
}

func main() {
	http.Handle("/styles/", http.StripPrefix("/styles/", http.FileServer(http.Dir("static/styles"))))
	http.Handle("/scripts/", http.StripPrefix("/scripts/", http.FileServer(http.Dir("static/scripts"))))

	http.HandleFunc("/ws", handler)

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		html, err := openHTML("index.html")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
		fmt.Fprintln(w, html)
	})

	fmt.Println("Listening")

	go func() {
		var conn net.Conn
		var err error
		for {
			for {
				conn, err = net.Dial("tcp", "127.0.0.1:8888")
				if err != nil {
					//fmt.Println("Error connecting:", err)
					continue
				} else {
					fmt.Println("Connected!")
					break
				}
			}
			defer conn.Close()

			// Create a reader to read from the connection
			reader := bufio.NewReader(conn)

			for {
				// Read bytes from the connection
				message, err := readFullMessage(reader)
				if err != nil {
					//log.Println(err.Error())
					break
				}
				live_feed = []byte(message)

				_, err = conn.Write(commands_feed)
				if err != nil {
					//log.Println(err)
				}
				commands_feed = []byte{}
			}
		}
	}()

	http.ListenAndServe("127.0.0.1:80", nil)
}

func openHTML(file string) (string, error) {
	WD, err := os.Getwd()
	if err != nil {
		return "", err
	}
	b, err := os.ReadFile(path.Join(WD, "/static/", file))
	if err != nil {
		return "", err
	}
	return string(b), nil
}
