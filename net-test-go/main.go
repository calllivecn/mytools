
package main

import (
	"flag"
	"log"
)


var (
	address string = ""
	port = "6789"
	server = false
    pprof = false
)


func init(){
	// runtime.GOMAXPROCS(1)
	// flag.
	log.SetFlags(log.Lshortfile | log.Ldate | log.Ltime)

	flag.StringVar(&address, "address", "0.0.0.0", "listen address Or server address")
	flag.StringVar(&port, "port", "6789", "server port  Or client port")
	flag.BoolVar(&server, "server", false, "启动server")
	flag.BoolVar(&pprof, "prof", false, "启动pprof")

	flag.Parse()

	log.Println("server: ", server, "address: ", address, "port: ", port)
}


// ##################################################################

func main() {
	if server {
		tcpServer(address, port)
	}else{
        tcpClient(address, port, packsize, total)
    }
}
