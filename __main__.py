# coding: utf-8
import io
import sys
#sys.stdout.reconfigure(encoding='gb18030')#IDE调试
sys.stdout.reconfigure(encoding='utf-8')#直接运行
import my_server
if __name__ == '__main__':
    # print(sys.getdefaultencoding())
    # sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')
    my_server.Run()
