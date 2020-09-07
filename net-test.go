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
	"runtime"
	// "fmt"
)

func init(){
	runtime.GOMAXPROCS(1)
}

type CmdPack struct {
	Cmd				uint16 
	Packsize 		uint32
	Timedatasum   	uint64
}

type PackHead struct {
	Typ				uint16
	Size 			uint32
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

var EOF PackHead = PackHead{0xffff, 0x00000000}

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
	cp.Packsize = binary.BigEndian.Uint32(b[2:6])
	cp.Timedatasum = binary.BigEndian.Uint64(b[6:14])
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
	ph.Size = binary.BigEndian.Uint32(b[2:6])
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


var bufsize uint32 = 64*(1<<10)

// RecvSendPack 这算comments???
type RecvSendPack struct{
	net.Conn
	Buf []byte
	cur int
}

// NewRecvSendPack returns RecvSendPack 封装下收发包
func NewRecvSendPack(conn net.Conn) *RecvSendPack {
	return &RecvSendPack{conn, make([]byte, bufsize), 0}
}

// func getSizePack(con net.Conn, s int) ([]byte, error) {
func (rsp *RecvSendPack) getSizePack(s int) (int, error) {
	rsp.cur = 0
	for rsp.cur < s {
		count, err := rsp.Read(rsp.Buf[rsp.cur:s])

		if err != nil {

        	if err == io.EOF {
				log.Println("peer close.")
				return rsp.cur, err
			}

			log.Println(err)
			return -1, err
		}

		rsp.cur += count
	}

	return rsp.cur, nil
}

func (rsp *RecvSendPack) sendPack() error {
	cur := 0
	for cur < rsp.cur {
		n, err := rsp.Write(rsp.Buf[cur:rsp.cur])

		if err != nil {
			log.Println("peer close.", err)
			return err
		}

		cur += n
	}
	return nil
}

func (cp *CmdPack) recvCmdPack(rsp *RecvSendPack) error {

	_, err := rsp.getSizePack(cmdpack_size)
	if err != nil {
		log.Println("没有收到一个完整的包，exit...")
		return errors.New("没有收到一个完整的包，exit")
	}

	cp.byteToCmdPack(rsp.Buf[:cmdpack_size])
	log.Printf("CmdPack{}: %#v\n", *cp)
	return nil
}

func (ph *PackHead) recvPackHead(rsp *RecvSendPack) error {
	_, err := rsp.getSizePack(packhead_size)
	if err != nil {
		log.Println("没有收到一个完整的包，exit...")
		return errors.New("没有收到一个完整的包，exit")
	}

	// dp.byteToPackHead(data)
	ph.byteToPackHeadReflect(rsp.Buf[:rsp.cur])

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

		log.Println("client:", client.RemoteAddr(), "connected")

		tcpServer(client)
	}

}

func tcpServer(con net.Conn) {
	head := CmdPack{}

	acceptRsp := NewRecvSendPack(con)

	// 接收指令头
	err := head.recvCmdPack(acceptRsp)
	if err != nil {
		log.Println("recvCmdPack() Error: ", err)
		return
	}

	// 这里是相对于client 来说的
	log.Println("接收到的指令：", head)
	switch head.Cmd {
	case TCP_RECV_DATASUM:
		go tcpsend(con, head.Packsize, head.Timedatasum)
	case TCP_SEND_DATASUM:
		go tcprecv(con, head.Packsize, head.Timedatasum)
	/*
	case TCP_RECV_TIME:
		tcprecv_time(con, head.Packsize, head.Timedatasum)
	case TCP_SEND_TIME:
		tcpsend_time(con, head.Packsize, head.Timedatasum)
	*/
	default:
		log.Println("未知指令类型。断开连接... CmdPack.Cmd: ", head.Cmd, "CmdPack.PackSize:", head.Packsize)
		con.Close()
		return
	}
}

func tcprecv(con net.Conn, packsize uint32, datasum uint64) {
	defer con.Close()

	// 接收负载头信息
	playload := PackHead{}

	recvRsp := NewRecvSendPack(con)

end:
	for {

		err := playload.recvPackHead(recvRsp)

		if err != nil {
			log.Println("接收负载头错误: ", err)
			return
		}

		// log.Printf("tcprecv() playload: %#v\n", playload)

		if playload == EOF {
			break end
		}

		// 接收负载
		_, err = recvRsp.getSizePack(int(packsize))
		if err != nil {
			break
		}
	}
}

func tcpsend(con net.Conn, packsize uint32, datasum uint64) {
	defer con.Close()

	head := PackHead{TCP_SEND_DATASUM, packsize}

	headByte, _ := head.toByte()

	sendRsp := NewRecvSendPack(con)

	playload := append(headByte, make([]byte, packsize)...)
	copy(sendRsp.Buf[:len(playload)], playload)
	sendRsp.cur = len(playload)

	packcount := datasum / uint64(packsize)
	log.Println("packcount：", packcount)

	for packcount > 0 {
		// _, err := con.Write(playload)
		err := sendRsp.sendPack()
		if err != nil {
			log.Println(err)
			return
		}
		// log.Println("pack value:", pack)
		packcount--
	}
	// 发送结束
	eof, _ := EOF.toByte()
	con.Write(eof)
	log.Println("发送测试结束.")
}
