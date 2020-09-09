//
//
//
//
// 比同种算法的python3 版的慢一倍。。。(但是避免下GC性能就比python快2倍多了。)
// 好像是TCP 的发和收包，所耗CPU资源不一样。接收耗的多。差不多正好是发送的一倍。
//
//
//

package main

import (
	"log"
	"net"
	"flag"
	// "runtime"
	// "fmt"

	"./define"
)

// var address = ""
// var port = "6789"
// var server = false

var	address = *flag.String("address", "0.0.0.0", "listen address Or server address")
var	port = *flag.String("port", "6789", "server port  Or client port")
var	server = *flag.Bool("server", true, "启动server")

func init(){
	// runtime.GOMAXPROCS(1)
	// flag.
	flag.Parse()
}


// ##################################################################

func main() {
	log.Println(server, address, port)
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
		head := define.CmdPack{}

		// 接收指令头
		err = head.RecvCmdPack(client)
		if err != nil {
			log.Println("recvCmdPack() Error: ", err)
			return
		}

		// 这里是相对于client 来说的
		log.Println("接收到的指令：", head)
		switch head.Cmd {
		case define.TCP_RECV_DATASUM:
			go tcpsend(client, head.Packsize, head.Timedatasum)
		case define.TCP_SEND_DATASUM:
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
			return
		}
	}
}

func tcprecv(con net.Conn, packsize int32, datasum uint64) {
	defer con.Close()

	// 接收负载头信息
	playload := define.PackHead{}

	recvRsp := define.NewRecvSendPack(con, packsize)

	for {

		err := playload.RecvPackHead(recvRsp)

		if err != nil {
			log.Println("接收负载头错误: ", err)
			return
		}

		// log.Printf("tcprecv() playload: %#v\n", playload)

		if playload == define.EOF {
			log.Println("接收测试结束.")
			break
		}

		// 接收负载
		_, err = recvRsp.GetSizePack(int(packsize))
		if err != nil {
			log.Println("接收数据包错误.")
			break
		}
	}
}

func tcpsend(con net.Conn, packsize int32, datasum uint64) {
	defer con.Close()

	head := define.PackHead{Typ: define.TCP_SEND_DATASUM, Size: packsize}

	headByte, _ := head.ToByte()

	sendRsp := define.NewRecvSendPack(con, packsize + int32(define.PackHeadSize))

	copy(sendRsp.Buf[:define.PackHeadSize], headByte)

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
	eof, _ := define.EOF.ToByte()
	con.Write(eof)
	log.Println("发送测试结束.")
}
