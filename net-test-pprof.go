package main

// # 性能分析 code begin

import (
	"log"
	"os"
	"runtime/pprof"
)

func StartCpuProf() {
    f, err := os.Create("cpu.prof")
    if err != nil {
        log.Println("create cpu profile file error: ", err)
        return
    }
    if err := pprof.StartCPUProfile(f); err != nil {
        log.Println("can not start cpu profile,  error: ", err)
        f.Close()
    }
}

func StopCpuProf() {
    pprof.StopCPUProfile()
}

// # 性能分析 code end


func main(){
}