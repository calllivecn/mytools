
getdatetime(){
	date +%Y%m%d%H%M%S
}

getch(){

local TTY

TTY=$(tty)

stty -icanon -echo

dd if=$TTY bs=8 count=1 2> /dev/null

stty icanon echo

}



