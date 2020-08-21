//
//
// 
// 
// 比同种算法的python3 版的慢一倍。。。
// 
// 
// 
// 

package main

import (
	"bytes"
	"encoding/binary"
	"log"
	"net"
	"io"
	// "fmt"
)

type CmdPack struct {
	Cmd, Packsize    uint16
	Timedatasum uint64
}

type PackHead struct {
	Typ, Size  uint16
}

var cmdpack_size, packhead_size int

func init() {
	cmdpack_size = binary.Size(CmdPack{})
	packhead_size = binary.Size(PackHead{})
	log.SetFlags(log.Lshortfile | log.Ldate |log.Ltime)
}


// 这里的定义是相对client来说
const (
	TCP_SEND_DATASUM = 0x0001
	TCP_RECV_DATASUM = 0x0002

	TCP_SEND_TIME = 0x0003
	TCP_RECV_TIME = 0x0004

	END = 0xffff
)

var EOF PackHead = PackHead{0xffff, 0x0000}



func (cp *CmdPack) byteToCmdPackReflect(b []byte) {
	// c := CmdPack{}
	buf := bytes.NewBuffer(b)
	// 这种方式用到反射，导致性能很差!!! 
	// 这种方式用到反射，导致性应该会变差!!! 但这里的性能瓶颈并不是这里。。。
	err := binary.Read(buf, binary.BigEndian, cp)
	if err != nil {
		log.Fatal(err)
		return
	}

}

func (cp *CmdPack) byteToCmdPack(b []byte) {
	cp.Cmd = binary.BigEndian.Uint16(b[:2])
	cp.Packsize = binary.BigEndian.Uint16(b[2:4])
	cp.Timedatasum = binary.BigEndian.Uint64(b[4:12])
}

func (ph *PackHead) byteToPackHeadReflect(b []byte) {
	// c := PackHead{}
	buf := bytes.NewBuffer(b)
	err := binary.Read(buf, binary.BigEndian, ph)
	if err != nil {
		log.Fatal(err)
		return
	}
}

func (ph *PackHead) byteToPackHead(b []byte) {
	ph.Typ = binary.BigEndian.Uint16(b[:2])
	ph.Size = binary.BigEndian.Uint16(b[2:4])
}

func (cp *CmdPack) toByte() ([]byte, error) {
	buf := bytes.Buffer{}
	err := binary.Write(&buf, binary.BigEndian, cp)
	if err != nil {
		log.Println(err)
		return []byte{}, err
	}

	return buf.Bytes(), nil
}

func (dp *PackHead) toByte() ([]byte, error) {
	buf := bytes.Buffer{}
	err := binary.Write(&buf, binary.BigEndian, dp)
	if err != nil {
		log.Println(err)
		return []byte{}, err
	}

	return buf.Bytes(), nil
}

func (dp *CmdPack) recvCmdPack(con net.Conn) error {
	data := []byte{}
	buf := make([]byte, cmdpack_size)
	n := 0
	for n <= cmdpack_size {
		count, err := con.Read(buf)
		if err != nil {
			log.Println(err)
			return err
		}
		if count == 0 {
			// peer close
			log.Println("peer close.")
			return err
		}

		n += count
		data = append(data, buf[:count]...)
	}

	dp.byteToCmdPack(data)
	log.Printf("CmdPack{}: %#v\n", *dp)
	return nil
}

func (dp *PackHead) recvPackHead(con net.Conn) error {
	data := []byte{}
	buf := make([]byte, packhead_size)
	n := 0
	for n <= packhead_size {
		count, err := con.Read(buf)
		if err != nil {
			log.Println(err)
			return err
		}

		if err == io.EOF {
			log.Println("err == io.EOF")
		}
		
		if count == 0 {
			// peer close
			log.Println("peer close.")
			return err
		}

		n += count
		data = append(data, buf[:count]...)
	}

	// dp.byteToPackHead(data)
	dp.byteToPackHeadReflect(data)

	// 这种，会改变，所指向的对象
	// dp = &d 
	return nil
}

// ##################################################################

func main() {

	listener, err := net.Listen("tcp", ":6789")
	if err != nil {
		log.Fatal(err)
		return
	}

	log.Println("Server running, listen: 0.0.0.0:6789")

	for {
		client, err := listener.Accept()

		if err != nil {
			log.Println(err, "continue...")
			continue
		}

		log.Println("client: ", client.RemoteAddr(), "connected")

		go tcpServer(client)
	}

}

func tcpServer(con net.Conn) {
	defer con.Close()

	head := CmdPack{}

	// 接收指令头
	err := head.recvCmdPack(con)
	if err != nil {
		log.Println("recvCmdPack() Error: ", err)
		return
	}

	// 这里是相对于client 来说的
	log.Println("接收到的指令：", head)
	switch head.Cmd {
	case TCP_RECV_DATASUM:
		tcpsend(con, head.Packsize, head.Timedatasum)
	case TCP_SEND_DATASUM:
		tcprecv(con, head.Packsize, head.Timedatasum)
		/*
	case TCP_RECV_TIME:
		tcprecv_time(con, head.Packsize, head.Timedatasum)
	case TCP_SEND_TIME:
		tcpsend_time(con, head.Packsize, head.Timedatasum)
		*/
	default:
		log.Println("未知指令类型。断开连接... CmdPack.Cmd: ", head.Cmd, "CmdPack.PackSize:", head.Packsize)
		return
	}
}

func tcprecv(con net.Conn, packsize uint16, datasum uint64) {
	// 接收负载头信息
	playload := PackHead{}

	end:
	for {

		err := playload.recvPackHead(con)

		if err != nil {
			log.Println("接收负载头错误: ", err)
			return
		}

		// log.Printf("tcprecv() playload: %#v\n", playload)

		if playload == EOF {
			break end
		}

		// 接收负载
		buf := make([]byte, packsize)
		count := packsize
		for count > 0 {
			n, err := con.Read(buf)

			if err == io.EOF {
				// log.Println("err == io.EOF n ==", n)
				log.Println("接收测试结束.")
				break end
			}
		
			if err != nil {
				log.Println("peer error: ", err, "n ==", n)
				break end
			}

			if n == 0 {
				log.Println("peer close.")
				break end
			}

			count -= uint16(n)
		}
	}
}

func tcpsend(con net.Conn, packsize uint16, datasum uint64) {

	head := PackHead{TCP_SEND_DATASUM, packsize}

	head_byte, err := head.toByte()
	if err != nil {
		log.Println(err)
		return
	}

	playload := make([]byte, packsize)

	for datasum > 0 {
		n, err := con.Write(append(head_byte, playload...))
		if err != nil {
			log.Println(err)
			return
		}

		datasum -= uint64(n)
	}
	log.Println("发送测试结束.")
}
