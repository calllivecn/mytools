//
//
//
//
// 比同种算法的python3 版的慢一倍。。。
// 好像是TCP 的发和收包，所耗CPU资源不一样。接收耗的多。差不多正好是发送的一倍。
//
//
//

package main

import (
	"bytes"
	"errors"
	"encoding/binary"
	"io"
	"log"
	"net"
	// "fmt"
)

type CmdPack struct {
	Cmd, Packsize uint16
	Timedatasum   uint64
}

type PackHead struct {
	Typ, Size uint16
}

var cmdpack_size, packhead_size int

func init() {
	cmdpack_size = binary.Size(CmdPack{})
	packhead_size = binary.Size(PackHead{})
	log.SetFlags(log.Lshortfile | log.Ldate | log.Ltime)
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

func (ph *PackHead) toByte() ([]byte, error) {
	buf := bytes.Buffer{}
	err := binary.Write(&buf, binary.BigEndian, ph)
	if err != nil {
		log.Println(err)
		return []byte{}, err
	}

	return buf.Bytes(), nil
}

func getSizePack(con net.Conn, s int) ([]byte, error) {
	data := []byte{}
	buf := make([]byte, s)
	for 0 < s {
		count, err := con.Read(buf)

        if err == io.EOF {
			log.Println("client close.")
			return append(data, buf[:count]...), err
        }

		if err != nil {
			log.Println(err)
			return append(data, buf[:count]...), err
		}

		s -= count
		data = append(data, buf[:count]...)
	}

	return data, nil
}

func (cp *CmdPack) recvCmdPack(con net.Conn) error {

	data, err := getSizePack(con, cmdpack_size)
	if err != nil {
		log.Println("没有收到一个完整的包，exit...")
		return errors.New("没有收到一个完整的包，exit")
	}

	cp.byteToCmdPack(data)
	log.Printf("CmdPack{}: %#v\n", *cp)
	return nil
}

func (ph *PackHead) recvPackHead(con net.Conn) error {
	data, err := getSizePack(con, packhead_size)
	if err != nil {
		log.Println("没有收到一个完整的包，exit...")
		return errors.New("没有收到一个完整的包，exit")
	}

	// dp.byteToPackHead(data)
	ph.byteToPackHeadReflect(data)

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
		_, err = getSizePack(con, int(packsize))
		if err != nil {
			break
		}
	}
}

func tcpsend(con net.Conn, packsize uint16, datasum uint64) {
	head := PackHead{TCP_SEND_DATASUM, packsize}

	headByte, _ := head.toByte()

	playload := append(headByte, make([]byte, packsize)...)

	// datasum / packsize
	pack := datasum / uint64(packsize)
	for pack > 0 {
		// n, err := con.Write(playload)
		_, err := con.Write(playload)
		if err != nil {
			log.Println(err)
			return
		}

		// datasum -= uint64(n)
		pack--
	}
	// 发送结束
	eof, _ := EOF.toByte()
	con.Write(eof)
	log.Println("发送测试结束.")
}
