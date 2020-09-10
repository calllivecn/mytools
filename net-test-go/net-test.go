//
//
//
//
// 比同种算法的python3 版的慢一倍。。。(但是避免下GC性能就比python快2倍多了。快还是要相对于packsize来看)
// 好像是TCP 的发和收包，所耗CPU资源不一样。接收耗的多。差不多正好是发送的一倍。
//
//
//

package main

import (
	"log"
	"net"
	"flag"
	// "fmt"
)

var (
	address string = ""
	port = "6789"
	server = false
)


func init(){
	// runtime.GOMAXPROCS(1)
	// flag.

	flag.StringVar(&address, "address", "0.0.0.0", "listen address Or server address")
	flag.StringVar(&port, "port", "6789", "server port  Or client port")
	flag.BoolVar(&server, "server", false, "启动server")

	flag.Parse()

	log.Println("server: ", server, "address: ", address, "port: ", port)
}


// ##################################################################

func main() {
	if server {
		tcpServer(address, port)
	}
}


func tcpServer(address, port string) {

	listener, err := net.Listen("tcp", address+ ":" +port)

	if err != nil {
		log.Fatal(err)
		return
	}

	log.Println("Server running, listen: ", address, port)

	for {
		client, err := listener.Accept()

		if err != nil {
			log.Println(err, "continue...")
			continue
		}

		log.Println("client:", client.RemoteAddr(), "connected")

		// 开始！
		head := CmdPack{}

		// 接收指令头
		err = head.RecvCmdPack(client)
		if err != nil {
			log.Println("recvCmdPack() Error: ", err)
			return
		}

		// 这里是相对于client 来说的
		log.Println("接收到的指令：", head)
		switch head.Cmd {
		case TCP_RECV_DATASUM:
			go tcpsend(client, head.Packsize, head.Timedatasum)
		case TCP_SEND_DATASUM:
			go tcprecv(client, head.Packsize, head.Timedatasum)
		/*
		case TCP_RECV_TIME:
			tcprecv_time(client, head.Packsize, head.Timedatasum)
		case TCP_SEND_TIME:
			tcpsend_time(client, head.Packsize, head.Timedatasum)
		*/
		default:
			log.Println("未知指令类型。断开连接... CmdPack.Cmd: ", head.Cmd, "CmdPack.PackSize:", head.Packsize)
			client.Close()
		}
	}
}

func tcprecv(con net.Conn, packsize int32, datasum uint64) {
	defer con.Close()

	// 接收负载头信息
	playload := PackHead{}

	recvRsp := NewRecvSendPack(con, packsize)

	for {

		err := playload.RecvPackHead(recvRsp)

		if err != nil {
			log.Println("接收负载头错误: ", err)
			return
		}

		// log.Printf("tcprecv() playload: %#v\n", playload)

		if playload == EOF {
			log.Println("接收测试结束.")
			break
		}

		// 接收负载
		_, err = recvRsp.GetSizePack(int(packsize))
		if err != nil {
			break
		}
	}

}

func tcpsend(con net.Conn, packsize int32, datasum uint64) {
	defer con.Close()

	head := PackHead{Typ: TCP_SEND_DATASUM, Size: packsize}

	headByte, _ := head.ToByte()

	sendRsp := NewRecvSendPack(con, packsize + int32(PackHeadSize))

	copy(sendRsp.Buf[:PackHeadSize], headByte)

	packcount := datasum / uint64(packsize)
	log.Println("packcount：", packcount)

	for packcount > 0 {
		_, err := con.Write(sendRsp.Buf)
		// err := sendRsp.SendPack()
		if err != nil {
			log.Println(err)
			return
		}
		// log.Println("pack value:", pack)
		packcount--
	}
	// 发送结束
	eof, _ := EOF.ToByte()
	con.Write(eof)
	log.Println("发送测试结束.")

}
