#!/usr/bin/python  
# -*- coding: UTF-8 -*-

from gl import *
from wrap import *
from cmd2 import Cmd
import pexpect

class Loop(Cmd):
    def __init__(self):
        #将变量纳入环境变量，就可以通过set命令修改和查询
        self.cmdask = False
        self.settable['cmdask'] = 'whether to ask when cmd is called'
        self.branch = False
        GL.setBranch(self.branch)
        self.settable['branch'] = 'merge from branch, not trunk'
        self.jksOptions = { #jenkins操作的选项与对应业务功能的映射
            'build': 'jenkinsBuild',
            'info': 'jenkinsInfo'
        }
        Cmd.__init__(self)

    def _onchange_branch(self, old, new):
        GL.setBranch(new)

    #事件循环开始时执行
    def preloop(self):
        #验证管理密码
        #password = getpass.getpass('请输入使用密码：')
        #if verifyPwd(password) == False:
            #exit()
        #GL.setPwd(password)

        #给ssh-agent加入本程序需要的ssh key
        if os.environ.has_key('SSH_AGENT_PID') == False:
            print '启动方式: ssh-agent ./main.py'
            exit()
        f = open('%s/key' % GL.rsaDir())
        pwd = f.readline()
        f.close()
        ch = pexpect.spawn('ssh-add %s/maintenance_rsa' % GL.rsaDir())
        ch.expect('Enter passphrase for %s/maintenance_rsa: ' % GL.rsaDir())
        ch.sendline (pwd)
        output = commands.getoutput('ssh-add -l')
        ch.close()
        if 'maintenance_rsa' not in output:
            print '添加ssh key到ssh-agent失败！请检查！'
            exit()

        #选择要管理的环境
        env = self.select(GL.deploy().keys())
        GL.setEnv(env)
        GL.initJenkins()
        GL.LOG = getLogger('TheLogger', 'ops-toolkit.log')

        intro_proj = GL.conf()[GL.project()]['intro']
        intro_proj = cipher(GL.key(),intro_proj, False)
        intro_env = GL.deploy()[GL.env()]['intro']
        self.intro = '进入运维工具事件循环，项目：%s，选择的环境是：%s。' % (intro_proj,intro_env)
        self.prompt = "运维 %s %s ->> " % (intro_proj,intro_env)
        GL.loop = self

    #事件循环结束时执行
    def postloop(self):
        #for ip,remote in GL.remote.items():
            #remote.logout()
        network.disconnect_all()

    #输入为空时啥都不做
    def emptyline(self):
        return

    #exit指令，当指令返回是True时事件循环结束
    def do_exit(self, arg):
        return True

    #自定义指令中默认的自动补全内容
    def completedefault(self, text, line, begidx, endidx):
        lst = GL.proj().keys()
        hosts = GL.hosts().keys()
        lst.extend(hosts)
        if text==None or text=='':
            return lst
        else:
            ret = []
            for l in lst:
                if l.startswith(text):
                    ret.append(l)
            return ret

    def do_cmd(self, arg):
        args = arg.split(None, 1)
        if len(args) == 2:
            item = args[0]
            drt = args[1]
            if drt.startswith("'") and drt.endswith("'"):
                drt = 'eval ' + drt
            if GL.proj().has_key(item) or item=='!$':
                mod = getMod(item)
                if mod != None:
                    cmd(mod.deploy(), drt, self.cmdask)
            elif GL.dplHosts().has_key(item) or GL.ipHosts().has_key(item):
                lst = [item,]
                ip_list = GL.getRealIPs(lst)
                cmd(ip_list, drt, self.cmdask)
            elif item == 'all':
                lst = GL.dplHosts().keys()
                ip_list = GL.getRealIPs(lst)
                cmd(ip_list, drt, self.cmdask)
            else:
                self.help_cmd()
        else:
            self.help_cmd()

    def help_cmd(self):
        print '在指定工程所在主机或指定IP的主机上执行命令，用法：cmd <工程名/ip/all> <命令>'

    def do_local(self, cmd):
        if cmd!=None and cmd!='':
            if cmd.startswith("'") and cmd.endswith("'"):
                cmd = 'eval ' + cmd
            GL.LOG.info('本地执行命令：%s' % cmd)
            localCmd(cmd)

    def do_backup(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod != None:
                backup(mod)
        else:
            self.help_backup()

    def help_backup(self):
        print '备份指定的工程，用法：backup <工程名>'

    def do_clean(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod != None:
                clean(mod)
        else:
            self.help_clean()

    def help_clean(self):
        print '清理指定的工程的备份，用法：clean <工程名>'

    def do_rollback(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod != None:
                rollback(mod)
        else:
            self.help_rollback()

    def help_rollback(self):
        print '还原指定的工程，用法：rollback <工程名>'

    def do_show(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod != None:
                show(mod)
        else:
            self.help_show()

    def help_show(self):
        print '查看指定的工程目录和更新包的信息，用法：show <工程名>'

    def do_up(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.form()!='node':
                update(mod)
            else:
                self.help_up()
        else:
            self.help_up()

    def help_up(self):
        print '更新指定的工程(node请使用svn更新)，用法：up <工程名>'

    def do_patch(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.name()=='wap':
                up_wap(mod, True)
            else:
                self.help_patch()
        else:
            self.help_patch()

    def help_patch(self):
        print '更新指定的工程的补丁(当前只支持wap)，用法：patch <工程名>'

    def do_svn(self, arg):
        if GL.env() == 'dev':
            GL.LOG.error('开发环境不需要svn操作')
            return
        args = arg.split()
        if len(args)!=2 and len(args)!=3:
            self.help_svn()
        else:
            mod = getMod(args[1])
            if mod != None:
                opt = args[0]
                if len(args) == 2:
                    svn(mod, opt)
                if len(args) == 3:
                    svn(mod, opt, args[2])
            else:
                self.help_svn()

    def help_svn(self):
        print '用法：svn <操作 [info/up/switch/merge/cp/del/ls/ci/cii]> <工程名> [详细路径]'

    def do_svncnf(self, arg):
        #if GL.env() == 'dev':
            #GL.LOG.error('开发环境不需要svn操作')
            #return
        args = arg.split()
        if len(args) != 2:
            self.help_svncnf()
        else:
            mod = getMod(args[1])
            if mod!=None and (mod.form()=='center' or mod.form()=='process' or mod.form()=='server' or mod.form()=='newserver' or mod.form()=='module'):
                opt = args[0]
                svncnf(mod, opt)
            else:
                self.help_svncnf()

    def help_svncnf(self):
        print '用法：svncnf <操作 [up/merge/cp/del/ls/ci]> <工程名> //注意当前只有center/process/server有配置文件'

    def do_start(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.form()!='node':
                start(mod)
            else:
                self.help_start()
        else:
            self.help_start()

    def help_start(self):
        print '启动Java工程，用法：start <工程名>'

    def do_stop(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.form()!='node':
                stop(mod)
            else:
                self.help_stop()
        else:
            self.help_stop()

    def help_stop(self):
        print '停止Java工程，用法：stop <工程名>'

    def do_restart(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.form()!='node':
                restart(mod)
            else:
                self.help_restart()
        else:
            self.help_restart()

    def help_restart(self):
        print '重启Java工程(node请使用pm2 reload)，用法：restart <工程名>'

    def do_pm2(self, arg):
        if arg=='l' or arg=='list':
            pm2(arg)
        else:
            args = arg.split(None, 1)
            if len(args) == 2:
                mod = getMod(args[1])
                if mod!=None and mod.form()=='node':
                    pm2(args[0], mod)
                else:
                    self.help_pm2()
            else:
                self.help_pm2()

    def help_pm2(self):
        print '''操作node工程的pm2命令，用法：
        pm2 <l/list>        
        pm2 reload <工程名>'''


    def do_status(self, proj):
        if proj!=None and proj!='':
            mod = getMod(proj)
            if mod!=None and mod.form()!='node':
                status(mod)
            else:
                self.help_status()
        else:
            self.help_status()

    def help_status(self):
        print '查询指定Java工程的进程情况，用法：status <工程名>'

    def do_monitor(self, arg):
        args = arg.split(None, 2)
        if len(args)==1 and args[0]=='save':
            monitorSave()
        elif len(args)==2 and (args[0]=='show' or args[0]=='save' or args[0]=='close' or args[0]=='start'):
            mod = getMod(args[1])
            if mod != None:
                monitor(args[0], mod)
        else:
            self.help_monitor()

    def help_monitor(self):
        print '''控制工程的定时任务和队列监控，用法：
        monitor save                    显示当前save的jobs和queues
        monitor save <工程名>           保存指定工程的jobs和queues
        monitor show <工程名>           显示指定工程的jobs和queues，和它们的运行状态
        monitor <start/close> <工程名>  开启/关闭已save中对应工程的jobs和queues'''

    def do_devclose(self, proj):
        if proj!=None and proj!='' and GL.env()!="pro":
            mod = getMod(proj)
            if mod != None:
                monitor("save", mod)
                monitor("close", mod)
            else:
                self.help_devclose()
        else:
            self.help_devclose()

    def help_devclose(self):
        print '''用于开发测试环境，直接关闭指定工程当前所有定时任务和队列监控，用法：
        devclose <工程名>'''

    def do_dubbo(self, arg):
        args = arg.split(None, 2)
        if len(args)==2 and (args[0]=='disable' or args[0]=='enable'):
            mod = getMod(args[1])
            if mod != None:
                for ip in mod.deploy():
                    dubboAdmin(mod, ip, args[0])
        elif len(args)==3 and (args[0]=='disable' or args[0]=='enable'):
            mod = getMod(args[1])
            if mod != None:
                dubboAdmin(mod, args[2], args[0])
        else:
            self.help_dubbo()

    def help_dubbo(self):
        print '''启用/禁用DubboAdmin,只用于center工程, 用法: 
        dubbo enable/disable <工程名>
        dubbo enable/disable <工程名> <ip>'''

    def do_encrypt(self, arg):
        if arg!=None and arg!='':
            print cipher(GL.key(),arg)

    def do_decrypt(self, arg):
        if arg!=None and arg!='':
            print cipher(GL.key(),arg, False)

    def do_info(self, arg):
        if GL.proj().has_key(arg) or arg=='!$':
            mod = getMod(arg)
            if mod != None:
                print dumpJson(mod.deploy())
                print dumpJson(mod.hosts())
                print dumpJson(GL.proj()[mod.name()])
        elif GL.dplHosts().has_key(arg):
            print dumpJson(GL.dplHosts()[arg])
        elif arg == 'all':
            print dumpJson(GL.deploy()[GL.env()])
        else:
            pass

    def do_scp(self, arg):
        args = arg.split(None, 2)
        if len(args) != 3:
            self.help_scp()
            return
        if (args[1].startswith(':') and args[2].startswith(':')) or (args[1].startswith(':')==False and args[2].startswith(':')==False):
            self.help_scp()
            return
        src = args[1]
        dest = args[2]
        if GL.proj().has_key(args[0]) or args[0]=='!$':
            mod = getMod(args[0])
            if mod != None:
                ip_list = mod.deploy()
                scp(ip_list, src, dest)
        elif GL.hosts().has_key(args[0]):
            ip = GL.getRealIP(args[0])
            ip_list = [ip,]
            scp(ip_list, src, dest)
        elif GL.dplHosts().has_key(args[0]) or GL.ipHosts().has_key(args[0]):
            ip_list = [args[0],]
            scp(ip_list, src, dest)
        elif args[0] == 'all':
            lst = GL.dplHosts().keys()
            ip_list = GL.getRealIPs(lst)
            scp(ip_list, src, dest)
        else:
            self.help_scp()
    
    def help_scp(self):
        print '''远程拷贝文件，用法：
        scp <工程名/ip/all> <src> <dest>  通过参数2得到机器，src和dest前面加:则表示为远程目录，有且只有一个为远程目录
        '''

    def do_rsync(self, arg):
        args = arg.split(None, 2)
        if len(args) != 3:
            self.help_rsync()
            return
        if (args[1].startswith(':') and args[2].startswith(':')) or (args[1].startswith(':')==False and args[2].startswith(':')==False):
            self.help_rsync()
            return
        src = args[1]
        dest = args[2]
        if GL.proj().has_key(args[0]) or args[0]=='!$':
            mod = getMod(args[0])
            if mod != None:
                ip_list = mod.deploy()
                rsync(ip_list, src, dest)
        elif GL.hosts().has_key(args[0]):
            ip = GL.getRealIP(args[0])
            ip_list = [ip,]
            rsync(ip_list, src, dest)
        elif GL.dplHosts().has_key(args[0]) or GL.ipHosts().has_key(args[0]):
            ip_list = [args[0],]
            rsync(ip_list, src, dest)
        elif args[0] == 'all':
            lst = GL.dplHosts().keys()
            ip_list = GL.getRealIPs(lst)
            rsync(ip_list, src, dest)
        else:
            self.help_rsync()
    
    def help_rsync(self):
        print '''远程同步目录，用法：
        rsync <工程名/ip/all> <src> <dest>  通过参数2得到机器，src和dest前面加:则表示为远程目录，有且只有一个为远程目录
        '''

    #自定义jks命令, 实现jenkins相关操作, 用法见函数help_jks
    def do_jks(self, arg):
        args = arg.split()   #以空格分隔参数
        if len(args) == 2:
            #直接接受两个参数, 第一为选项, 第二为工程
            if args[0] in self.jksOptions:
                #以eval来实现对字符串形式的函数名进行调用
                eval(self.jksOptions[args[0]])(getMod(args[1]))
                return
        self.help_jks()

    #自定义jks命令的帮助内容，循环中输入help jks时调用
    def help_jks(self):
        print('''
        jks命令：jks相关操作；用法：jks [选项] [工程名];
            选项：
                build   立即构建
                info    查看信息
        ''')

    def do_ssh(self, arg):
        if GL.proj().has_key(arg) or arg=='!$':
            mod = getMod(arg)
            if mod != None:
                for ip in mod.deploy():
                    self.do_local('ssh %s' % ip)
                    break
        elif GL.hosts().has_key(arg):
            self.do_local('ssh %s' % GL.getRealIP(arg))
        elif GL.ipHosts().has_key(arg):
            self.do_local('ssh %s' % arg)
        else:
            self.help_ssh()

    def help_ssh(self):
        print('''
        ssh命令：远程连接主机；用法：ssh [工程名/主机名/IP地址]
        ''')

    #def do_set(self, arg):
        #args = arg.split()
        #if len(args)==1 and arg=='show':
            #set(arg)
        #elif len(args) == 2:
            #set(args[0], args[1])
        #else:
            #self.help_set()
##
    #def help_set(self):
        #print '设置变量，当前只支持版本变量issue，用法：set <show/变量> [变量值]'
        






