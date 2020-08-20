package main


import (
	"fmt"
	"log"
	"net"
	"bytes"
	"encoding/binary"
)

type cmdpack struct {
	cmd uint16
	packsize uint16
	time_datasum uint32
}

type protopack struct {
	typ uint16
	size uint16
}

func main(){

}


func (cmd cmdpack) newCmdPack(c, p uint16, td uint32) cmdpack {
	d := cmdpack{c, p, td}
	return d
}


func (cmd cmdpack) toByte() []byte {

	buf := &bytes.Buffer{}

	err := binary.Write(buf, binary.BigEndian, cmd)

	if err != nil {
		log.Fatal(err)
	}

	return buf.Bytes()
}