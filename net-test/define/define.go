package define

import (
	"io"
	"net"
	"log"
	"errors"
	"bytes"
	"encoding/binary"
)


type CmdPack struct {
	Cmd				uint16 
	Packsize 		int32
	Timedatasum   	uint64
}

type PackHead struct {
	Typ				uint16
	Size 			int32
}

var CmdPackSize, PackHeadSize int

func init() {
	CmdPackSize = binary.Size(CmdPack{})
	PackHeadSize = binary.Size(PackHead{})
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

func (cp *CmdPack) ByteToCmdPackReflect(b []byte) {
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

func (cp *CmdPack) ByteToCmdPack(b []byte) {
	cp.Cmd = binary.BigEndian.Uint16(b[:2])
	cp.Packsize = int32(binary.BigEndian.Uint32(b[2:6]))
	cp.Timedatasum = binary.BigEndian.Uint64(b[6:14])
}

func (ph *PackHead) ByteToPackHeadReflect(b []byte) {
	// c := PackHead{}
	buf := bytes.NewBuffer(b)
	err := binary.Read(buf, binary.BigEndian, ph)
	if err != nil {
		log.Fatal(err)
		return
	}
}

func (ph *PackHead) ByteToPackHead(b []byte) {
	ph.Typ = binary.BigEndian.Uint16(b[:2])
	ph.Size = int32(binary.BigEndian.Uint32(b[2:6]))
}

func (cp *CmdPack) ToByte() ([]byte, error) {
	buf := bytes.Buffer{}
	err := binary.Write(&buf, binary.BigEndian, cp)
	if err != nil {
		log.Println(err)
		return []byte{}, err
	}

	return buf.Bytes(), nil
}

func (ph *PackHead) ToByte() ([]byte, error) {
	buf := bytes.Buffer{}
	err := binary.Write(&buf, binary.BigEndian, ph)
	if err != nil {
		log.Println(err)
		return []byte{}, err
	}

	return buf.Bytes(), nil
}


// var bufsize int = 64*(1<<10)

// RecvSendPack 这算comments???
type RecvSendPack struct{
	net.Conn
	Buf []byte
	Cur int

	// packsize int
}

// NewRecvSendPack returns RecvSendPack 封装下收发包
func NewRecvSendPack(conn net.Conn, bufsize int32) *RecvSendPack {
	// cur = 0
	// for cur <
	return &RecvSendPack{conn, make([]byte, bufsize), 0}
}

// s <= 10M
func (rsp *RecvSendPack) GetSizePack(s int) (int, error) {

	rsp.Cur = 0
	for rsp.Cur < s {
		count, err := rsp.Read(rsp.Buf[rsp.Cur:s])

		if err != nil {

	       	if err == io.EOF {
				log.Println("peer close.")
				return rsp.Cur, err
			}

			log.Println(err)
			return -1, err
		}

		rsp.Cur += count
	}

	return rsp.Cur, nil
}

func (rsp *RecvSendPack) SendPack() error {
	Cur := 0
	for Cur < rsp.Cur {
		n, err := rsp.Write(rsp.Buf[Cur:rsp.Cur])

		if err != nil {
			log.Println("peer close.", err)
			return err
		}

		Cur += n
	}
	return nil
}

func (cp *CmdPack) RecvCmdPack(con net.Conn) error {
	// log.Printf("make([]byte, %d)\n", CmdPackSize)
	buf := make([]byte, CmdPackSize)
	Cur := 0
	for Cur < CmdPackSize {
		count, err := con.Read(buf[Cur:CmdPackSize])

		if err != nil {

	       	if err == io.EOF {
				log.Println("peer close.")
				return errors.New("peer close...")
			}

			log.Println(err)
			return err
		}

		Cur += count
	}

	cp.ByteToCmdPack(buf[:CmdPackSize])
	log.Printf("CmdPack{}: %#v\n", *cp)
	return nil
}

func (ph *PackHead) RecvPackHead(rsp *RecvSendPack) error {
	_, err := rsp.GetSizePack(PackHeadSize)
	if err != nil {
		// log.Println("没有收到一个完整的包，exit...")
		return errors.New("没有收到一个完整的包，exit")
	}

	// dp.byteToPackHead(data)
	ph.ByteToPackHeadReflect(rsp.Buf[:rsp.Cur])

	// 这种，会改变，所指向的对象
	// dp = &d
	return nil
}