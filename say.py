
import sys
import time
# import subprocess
from subprocess import run, Popen, PIPE

__all__ = (
    "Say",
    "say",
)

# check 依赖
check = run("type -p espeak".split(), stdout=PIPE, shell=True)
if check.returncode != 0:
    print("请安装 apt install espeak")
    sys.exit(1)


class Say:

    # def __init__(self, language="zh", speed=150, delay=0.1):
    def __init__(self, language="zh", speed=150):
        cmd = f"espeak -v {language} -s {speed} --stdin"
        self.popen = Popen(cmd.split(), stdin=PIPE, text=True)
        self.closed = False
        # self.delay = delay

        # self.__time = time.time()
    
    def say(self, text):
        # self.__delay()
        self.popen.stdin.write(text)
        self.popen.stdin.flush()
    

    def close(self):
        if not self.closed:
            self.popen.communicate()
    
    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        self.close()
    
    def __delay(self):
        internal = self.__time - time.time()
        if internal >= self.delay:
            return
        else:
            t = self.delay - internal
            time.sleep(t)
            return

def say(text):
    with Say() as s:
        s.say(text)


def main():
    import argparse
    parse = argparse.ArgumentParser(usage="%(prog)s <句子>",
                                    description="使用 espeak 的语音合成工具",
                                    )
    parse.add_argument("-s", "--speed", type=int, default=150, help="说话的速度（default: 150）")

    parse.add_argument("text", help="要说的句子")

    args = parse.parse_args()

    with Say(speed=args.speed) as s:
        s.say(args.text)

def __test():

    s = Say()
    s.say("这是天天")
    s.say("这是从标准输入开始的speaking")
    s.close()

if __name__ == "__main__":
    main()