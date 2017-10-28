#!/usr/bin/python  
# -*- coding: UTF-8 -*-

from base import *
from model import *

def cmd(ip_list, cmd, cmdask):
    for ip in ip_list:
        if cmdask:
            out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
            if out == 'no':
                continue
        remoteCmd(ip, cmd)

def scp(ip_list, src, dest):
    for ip in ip_list:
        if src.startswith(':'):
            cmd = 'scp -r root@%s%s %s' % (ip,src,dest)
            localCmd(cmd)
        elif dest.startswith(':'):
            cmd = 'scp -r %s root@%s%s' % (src,ip,dest)
            localCmd(cmd)
        else:
            pass

def rsync(ip_list, src, dest):
    if src.endswith('/') == False:
        src += '/'
    if dest.endswith('/') == False:
        dest += '/'
    for ip in ip_list:
        if src.startswith(':'):
            cmd = 'rsync -avz root@%s%s %s' % (ip,src,dest)
            out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
            if out == 'yes':
                localCmd(cmd)
        elif dest.startswith(':'):
            cmd = 'rsync -avz %s root@%s%s' % (src,ip,dest)
            out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
            if out == 'yes':
                localCmd(cmd)
        else:
            pass

def backup(mod):
    for ip in mod.deploy():
        if mod.form()=='server' or mod.form()=='module':
            src = mod.appdir() + '.war'
        else:
            src = mod.appdir()
        dest = mod.bakdir()
        srcDir = src[:src.rfind('/')]   #源文件(夹)所在路径
        name = src[src.rfind('/')+1:]   #源文件(夹)名称
        bakname = '%s-%s.tar' % (mod.name(),getTimestamp())   #备份文件的名字
        GL.LOG.info('backup %s to %s/%s' % (src,dest,bakname))
        cmd = 'tar -cf %s/%s -C %s %s' % (dest,bakname,srcDir,name)
        if mod.name() == 'cdn':
            cmd += ' --exclude=apks'
        remoteCmd(ip, cmd)

def up_wap(mod, patch=False):
    pk = '%s/wap.tar.gz' % GL.pkdir()
    if os.path.exists(pk) == False:
        GL.LOG.error('未发现更新包：%s' % pk)
        return
    tmp = '%s/wap' % GL.pkdir()
    if patch:
        src = '%s/patch' % tmp
    elif GL.env() == 'pro':
        src = '%s/prod' % tmp
    elif GL.env() == 'test':
        src = '%s/test' % tmp
    else:
        GL.LOG.error('该环境(%s)暂不支持wap的更新' % GL.env())
        return
    localCmd('mkdir -p %s' % tmp)
    localCmd('rm -rf %s/*' % tmp)
    localCmd('tar -zxf %s -C %s' % (pk,tmp))
    if os.path.exists(src) == False:
        GL.LOG.error('未发现目录: %s' % src)
        return
    for ip in mod.deploy():
        cmd = 'rsync -azv %s/ webuser@%s:%s/' % (src,ip,mod.appdir())
        out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
        if out == 'yes':
            localCmd(cmd)

def up_wap_cdn(mod):
    if GL.env()!='pro' and GL.env()!='test':
        GL.LOG.error('该环境(%s)暂不支持wap_cdn的更新' % GL.env())
    #src_wap = '%s/wap/prod' % GL.pkdir()
    mod_wap = getMod('wap')
    for ip in mod.deploy():
        cmdlist = [
            'sudo -u webuser rsync -azv %s/js/ %s/js/' % (mod_wap.appdir(),mod.appdir()),
            'sudo -u webuser rsync -azv %s/css/ %s/css/' % (mod_wap.appdir(),mod.appdir()),
            'sudo -u webuser rsync -azv %s/images/ %s/images/' % (mod_wap.appdir(),mod.appdir()),
            'sudo -u webuser rsync -azv %s/fonts/ %s/fonts/' % (mod_wap.appdir(),mod.appdir())
            #'chown -R webuser:web %s' % mod.appdir()
        ]
        for cmd in cmdlist:
            out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
            if out == 'yes':
                remoteCmd(ip, cmd)

def up_wapv2(mod, patch=False):
    pk = '%s/wapv2.tar.gz' % GL.pkdir()
    if os.path.exists(pk) == False:
        GL.LOG.error('未发现更新包：%s' % pk)
        return
    tmp = '%s/wapv2' % GL.pkdir()
    localCmd('mkdir -p %s' % tmp)
    localCmd('rm -rf %s/*' % tmp)
    localCmd('tar -zxf %s -C %s' % (pk,tmp))
    src = '%s/dist' % tmp
    if os.path.exists(src) == False:
        GL.LOG.error('未发现目录: %s' % src)
        return
    for ip in mod.deploy():
        cmd = 'rsync -azv %s/ webuser@%s:%s/' % (src,ip,mod.appdir())
        out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
        if out == 'yes':
            localCmd(cmd)

def up_wapv2_cdn(mod):
    if GL.env()!='pro' and GL.env()!='test':
        GL.LOG.error('该环境(%s)暂不支持wapv2_cdn的更新' % GL.env())
    mod_wapv2 = getMod('wapv2')
    for ip in mod.deploy():
        cmd = 'sudo -u webuser rsync -azv %s/static/ %s/' % (mod_wapv2.appdir(),mod.appdir())
        out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
        if out == 'yes':
            remoteCmd(ip, cmd)

def up_server(mod):
    for ip in mod.deploy():
        #cmd = 'rm -rf %s/%s; cp %s %s' % (mod.appdir(),GL.proj()[mod.name()]['pack'],mod.pack(),mod.upappdir())
        cmd = 'cp %s %s' % (mod.pack(),mod.upappdir())
        out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
        if out == 'yes':
            remoteCmd(ip, cmd)

def up_center(mod):
    for ip in mod.deploy():
        cmd = 'rm -rf %s; unzip %s -d %s' % (mod.appdir(),mod.pack(),mod.upappdir())
        out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
        if out == 'yes':
            remoteCmd(ip, cmd)

def up_process(mod):
    up_center(mod)

def update(mod):
    if mod.name() == 'wap':
        up_wap(mod)
    elif mod.name() == 'wap_cdn':
        up_wap_cdn(mod)
    if mod.name() == 'wapv2':
        up_wapv2(mod)
    elif mod.name() == 'wapv2_cdn':
        up_wapv2_cdn(mod)
    elif mod.form() == 'center':
        up_center(mod)
    elif mod.form() == 'process':
        up_process(mod)
    elif mod.form()=='server' or mod.form()=='module':
        up_server(mod)
    else:
        GL.LOG.error('不支持的更新: %s %s' % (mod.form(),mod.name()))

def svncnf(mod, opt):
    if opt!='up' and opt!='merge' and opt!='ci':
        print '不支持的操作 %s' % opt
        return
    if opt == 'up':
        src = '%s/%s' % (mod.workcopy_cnf(),GL.env())
        dest = ':%s' % mod.cnfdir()
        rsync(mod.deploy(),src,dest)
        #cmd = 'svn %s %s' % (opt,dest)
        #for ip in mod.deploy():
            #if opt == 'up':
                #out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
                #if out == 'yes':
                    #remoteCmd(ip, cmd)
            #else:
                #remoteCmd(ip, cmd)
    elif opt == 'merge':
        #先更新本地拷贝
        cmd = 'svn up %s' % mod.workcopy_cnf()
        GL.LOG.info('更新本地的工作拷贝，执行命令 (%s)' % cmd)
        localCmd(cmd)
        #svn路径信息
        tag = mod.tag_cnf()
        trunk = mod.trunk_cnf()
        wcopy = mod.workcopy_cnf()
        #执行合并测试
        cmd = 'svn merge --dry-run %s %s %s' % (tag,trunk,wcopy)
        GL.LOG.debug('合并测试，执行命令 (%s)' % cmd)
        localCmd(cmd)
        #合并
        out = ask('查看合并测试结果后，请确认是否执行实际的合并操作？', 'yes,no', 'no')
        if out == 'yes':
            cmd = 'svn merge %s %s %s' % (tag,trunk,wcopy)
            GL.LOG.info('执行实际的合并操作 (%s)' % cmd)
            localCmd(cmd)
    elif opt == 'ci':
        wcopy = mod.workcopy_cnf()
        instr = raw_input('确认提交请输入提交日志，否则请直接回车: ')
        if instr != '':
            cmd = 'svn ci %s -m "%s"' % (wcopy, instr)
            GL.LOG.info('执行提交操作 (%s)' % cmd)
            localCmd(cmd)

def svn(mod, opt, path=None):
    if opt!='info' and opt!='up' and opt!='merge' and opt!='ci' and opt!='switch' and opt!='cp' and opt!='del' and opt!='ls':
        print '不支持的操作 %s' % opt
        return
    if (opt=='info' or opt=='up') and mod.form()=='node':
        if path == None:
            dest = mod.appdir()
        else:
            dest = '%s/%s' % (mod.appdir(),path)
        cmd = 'svn %s %s' % (opt,dest)
        for ip in mod.deploy():
            if opt == 'up':
                out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
                if out == 'yes':
                    remoteCmd(ip, cmd)
            else:
                remoteCmd(ip, cmd)
    elif opt == 'merge':
        #先更新本地拷贝
        cmd = 'svn up %s' % mod.workcopy()
        GL.LOG.info('更新本地的工作拷贝，执行命令 (%s)' % cmd)
        localCmd(cmd)
        #svn路径信息
        if path == None:
            tag = mod.tag()
            trunk = mod.trunk()
            wcopy = mod.workcopy()
        else:
            tag = '%s/%s' % (mod.tag(),path)
            trunk = '%s/%s' % (mod.trunk(),path)
            wcopy = '%s/%s' % (mod.workcopy(),path)
        #执行合并测试
        cmd = 'svn merge --dry-run %s %s %s' % (tag,trunk,wcopy)
        GL.LOG.debug('合并测试，执行命令 (%s)' % cmd)
        localCmd(cmd)
        #合并
        out = ask('查看合并测试结果后，请确认是否执行实际的合并操作？', 'yes,no', 'no')
        if out == 'yes':
            cmd = 'svn merge %s %s %s' % (tag,trunk,wcopy)
            GL.LOG.info('执行实际的合并操作 (%s)' % cmd)
            localCmd(cmd)
    elif opt == 'ci':
        if path == None:
            wcopy = mod.workcopy()
        else:
            wcopy = '%s/%s' % (mod.workcopy(),path)
        instr = raw_input('确认提交请输入提交日志，否则请直接回车: ')
        if instr != '':
            cmd = 'svn ci %s -m "%s"' % (wcopy, instr)
            GL.LOG.info('执行提交操作 (%s)' % cmd)
            localCmd(cmd)
    elif opt == 'switch':
        dest = mod.appdir()
        if path==None or path.startswith('svn')==False:
            print 'switch的目标必须是svn形式的url'
        else:
            cmd = 'svn switch %s %s' % (path,dest)
            for ip in mod.deploy():
                out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
                if out == 'yes':
                    remoteCmd(ip, cmd)
    elif opt == 'ls':
        if path == None:
            tag = mod.tag()
            trunk = mod.trunk()
        else:
            tag = '%s/%s' % (mod.tag(),path)
            trunk = '%s/%s' % (mod.trunk(),path)
        cmd = 'svn ls %s' % trunk
        out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
        if out == 'yes':
            localCmd(cmd)
        cmd = 'svn ls %s' % tag
        out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
        if out == 'yes':
            localCmd(cmd)
    elif opt == 'del':
        instr = raw_input('确认提交请输入提交日志，否则请直接回车: ')
        if instr != '':
            if path == None:
                tag = mod.tag()
            else:
                tag = '%s/%s' % (mod.tag(),path)
            cmd = 'svn del %s -m "%s"' % (tag,instr)
            out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
            if out == 'yes':
                localCmd(cmd)
    elif opt == 'cp':
        instr = raw_input('确认提交请输入提交日志，否则请直接回车: ')
        if instr != '':
            if path == None:
                tag = mod.tag()
                trunk = mod.trunk()
            else:
                tag = '%s/%s' % (mod.tag(),path)
                trunk = '%s/%s' % (mod.trunk(),path)
            tag = tag[:tag.rfind('/')]  #拷贝的目的地应该是上层目录
            cmd = 'svn cp %s %s -m "%s"' % (trunk,tag,instr)
            out = ask('将在本地运行命令 (%s), 确认立刻执行吗？' % cmd, 'yes,no', 'no')
            if out == 'yes':
                localCmd(cmd)

def status(mod):
    for ip in mod.deploy():
        cmd = "ps -ef|grep java|grep %s|grep -v grep" % mod.pidname()
        remoteCmd(ip, cmd)

def bakgc(mod, ip):
    GL.LOG.info('在 (%s) 备份 (%s) 的gc日志' % (ip,mod.name()))
    gcdir = mod.gcdir()
    gcfile = 'gc.log'
    bakdir = mod.gcbakdir()
    bakname = '%s-%s.tar.gz' % (gcfile,getTimestamp())
    cmd = 'if [ -f "%s/%s" ];then mkdir -p %s; tar -zcf %s/%s -C %s %s ; echo "Backup gc file OK"; else echo "Not found gc file"; fi' % (gcdir,gcfile,bakdir,bakdir,bakname,gcdir,gcfile)
    remoteCmd(ip, cmd)

def savejstack(mod, ip):
    GL.LOG.info('在 (%s) 保存 (%s) 的jstack信息' % (ip,mod.name()))
    jsdir = mod.jstackdir()
    cmd = 'if [ ! -d "%s" ];then mkdir -p %s;fi' % (jsdir,jsdir)
    remoteCmd(ip, cmd)
    cmd = 'tmpid=`ps -ef|grep java|grep %s|grep -v grep|awk \'{print $2}\'`; [ -n "$tmpid" ] && jstack $tmpid > %s/jstack-$tmpid-%s.log' % (mod.pidname(), jsdir, getTimestamp())
    remoteCmd(ip, cmd)

def _stop(ip, mod, jstack=False):
    if mod.form()=='server' or mod.form()=='module':
        remoteCmd(ip, mod.tomcatshutdown())
        time.sleep(2)
    if mod.form()=='center' and jstack==True:
        savejstack(mod, ip)
    #cmd = "ps -ef|grep java|grep %s|awk '{print $2}'|xargs kill -9" % mod.pidname()
    cmd = 'tmpid=`ps -ef|grep java|grep %s|grep -v grep|awk \'{print $2}\'`; [ -n "$tmpid" ] && kill -9 $tmpid; echo killed' % mod.pidname()
    remoteCmd(ip, cmd)
    bakgc(mod, ip)

def _start(ip, mod):
    remoteCmd(ip, mod.pidexe(), False)

def start(mod):
    for ip in mod.deploy():
        out = ask('将在 (%s) 启动 (%s), 确认立刻执行吗？' % (ip,mod.name()), 'yes,no', 'no')
        if out != 'yes':
            continue
        _start(ip, mod)
        dubboAdmin(mod, ip, 'enable')

def stop(mod):
    for ip in mod.deploy():
        dubboAdmin(mod, ip, 'disable')
        out = ask('将在 (%s) 停止 (%s), 确认立刻执行吗？' % (ip,mod.name()), 'yes,no', 'no')
        if out != 'yes':
            continue
        _stop(ip, mod)

#theIP/asked/jstack用于提供的http请求, http.py
def restart(mod, theIP=None, asked=True, jstack=False):
    for ip in mod.deploy():
        if theIP!=None and theIP!=ip:   #指定ip的情况
            continue
        if asked:   #在无人值守的http模式下不用询问，也不需禁用dubbo
            dubboAdmin(mod, ip, 'disable')
            out = ask('将在 (%s) 重启 (%s), 确认立刻执行吗？' % (ip,mod.name()), 'yes,no', 'no')
            if out != 'yes':
                continue
        _stop(ip, mod, jstack)
        time.sleep(1)
        _start(ip, mod)
        if asked:
            dubboAdmin(mod, ip, 'enable')

def pm2(opt, mod=None):
    if opt=='l' or opt=='list':
        mod = getMod('cms')  #以cms来定位node所在的主机
        for ip in mod.deploy():
            remoteCmd(ip, 'pm2 l')
    elif opt=='reload' and mod!=None:
        cmd = 'pm2 reload %s' % mod.name()
        for ip in mod.deploy():
            out = ask('将在 (%s) 运行命令 (%s), 确认立刻执行吗？' % (ip,cmd), 'yes,no', 'no')
            if out == 'yes':
                remoteCmd(ip, cmd)

def getJobs(s):
    url = 'http://%s/ljob_controller/get_online_ljobs' % GL.monitor()
    r = s.post(url)
    jobs = parseJobs(r.text)
    return jobs

def getQueues(s):
    url = 'http://%s/lqueue_controller/get_online_lqueues.do' % GL.monitor()
    r = s.post(url)
    queues = parseQueues(r.text)
    return queues

def getMonitor(s, mod):
    jobs = getJobs(s)
    queues = getQueues(s)
    retJobs = []
    retQueues = []
    if jobs != None:
        for job in jobs:
            if job[1] == mod.name():
                retJobs.append(job)
    if queues != None:
        for q in queues:
            if q[1] == mod.name():
                retQueues.append(q)
    return (retJobs,retQueues)

def monitorJob(s, ip_id, ljobKey, start):
    url = 'http://%s/ljob_controller/send_ljob_status_request' % GL.monitor()
    if start == True:
        status = '1'
    else:
        status = '0'
    data = {'ljobKey':ljobKey,'ip':ip_id,'status':status}
    r = s.post(url, data=data)
    if r.status_code == 200:
        print 'OK'
    else:
        print '失败'

def monitorQueue(s, ip_id, lqueueKey, start):
    url = 'http://%s/lqueue_controller/send_lqueue_status_request.do' % GL.monitor()
    if start == True:
        status = '1'
    else:
        status = '0'
    data = {'lqueueKey':lqueueKey,'ip':ip_id,'status':status}
    r = s.post(url, data=data)
    if r.status_code == 200:
        print 'OK'
    else:
        print '失败'

def monitorSave():
    i = 1
    print '定时任务：'
    if GL.closeJobs() != None:
        for job in GL.closeJobs():
            print i,job[0],job[1],job[2]
            i += 1
    i = 1
    print '队列监控：'
    if GL.closeQueues() != None:
        for q in GL.closeQueues():
            print i,q[0],q[1],q[2]
            i += 1

def monitor(opt, mod):
    s = requests.session()
    url = 'http://%s/login_controller/do_login' % GL.monitor()
    r = s.post(url, data={'loginName':GL.muser(),'password':GL.mpwd()}, timeout=3)
    if '退出登录' not in r.text:
        GL.LOG.error('登录失败')
        return
    if opt == 'all':    #给监控discover.py用的
        jobs = getJobs(s)
        queues = getQueues(s)
        return (jobs,queues)
    if opt=='show' or opt=='save':
        (jobs,queues) = getMonitor(s, mod)
        tmp1 = []
        tmp2 = []
        i = 1
        print '定时任务：'
        for job in jobs:
            print i,job[0],job[1],job[2],job[6]
            i += 1
            tmp1.append(job)
        i = 1
        print '队列监控：'
        for q in queues:
            print i,q[0],q[1],q[2],q[4]
            i += 1
            tmp2.append(q)
        if opt == 'save':
            GL.setCloseJobs(tmp1)
            GL.setCloseQueues(tmp2)
    elif opt=='start' or opt=='close':
        jobs = GL.closeJobs()
        queues = GL.closeQueues()
        if opt == 'start':
            info = '开启'
            status = True
        else:
            info = '关闭'
            status = False
        i = 1
        print '定时任务：'
        for job in jobs:
            if job[1] == mod.name():
                ip_id = job[0]
                ljobKey = '%s_%s' % (job[1],job[2])
                print i,info,ip_id,ljobKey,
                i += 1
                monitorJob(s, ip_id, ljobKey, status)
        i = 1
        print '队列监控：'
        for q in queues:
            if q[1] == mod.name():
                ip_id = q[0]
                lqueueKey = '%s_%s' % (q[1],q[2])
                print i,info,ip_id,lqueueKey,
                i += 1
                monitorQueue(s, ip_id, lqueueKey, status)

#opt: enable/disable
def dubboAdmin(mod, ip, opt):
    if GL.env() != 'pro':   #非生产环境不需要处理dubboadmin
        return
    if mod.form() == 'center':
        if opt == 'enable':  #启用前等待服务注册到dubboadmin
            timekeeping(40)
        addr = '%s:%s' % (ip,mod.port())
        out = ask('%s DubboAdmin (%s), 确认立刻执行吗？' % (opt,addr), 'yes,no', 'no')
        if out == 'yes':
            url = 'http://%s/dubbo/control' % GL.monitor()
            params = {'name':GL.muser(),'passwd':GL.mpwd(),'status':opt, 'addr':addr}
            r = requests.post(url=url, params=params)
            GL.LOG.info('DubboAdmin %s %s : %s %s' % (opt,addr,r.status_code,r.text))
            if opt == 'disable':    #禁用后等待业务都执行完成
                timekeeping(20)

def zabbix_monitor():
    (jobs,queues) = monitor('all', None)
    zabbix_job = {}
    for job in jobs:
        tmp = {}
        name = '%s_%s' % (job[1],job[2])
        if name in zabbix_job:
            zabbix_job[name]['{#DEPLOY}'].append(job[0])
            if job[3] == '是':
                zabbix_job[name]['{#DISTRIBUTED}'].append(True)
            else:
                zabbix_job[name]['{#DISTRIBUTED}'].append(False)
            zabbix_job[name]['{#HEARTBEAT}'].append(job[5])
            if job[6] == '运行中':
                zabbix_job[name]['{#RUNNING}'].append(True)
            else:
                zabbix_job[name]['{#RUNNING}'].append(False)
        else:
            zabbix_job[name] = {}
            zabbix_job[name]['{#NAME}'] = name
            zabbix_job[name]['{#DEPLOY}'] = [job[0],]
            if job[3] == '是':
                zabbix_job[name]['{#DISTRIBUTED}'] = [True,]
            else:
                zabbix_job[name]['{#DISTRIBUTED}'] = [False,]
            #zabbix_job[name]['{#HEARTBEAT}'] = [time.strptime(job[5], '%Y-%m-%d %H:%M:%S'),]
            zabbix_job[name]['{#HEARTBEAT}'] = [job[5],]
            if job[6] == '运行中':
                zabbix_job[name]['{#RUNNING}'] = [True,]
            else:
                zabbix_job[name]['{#RUNNING}'] = [False,]
    zabbix_queue = {}
    for queue in queues:
        tmp = {}
        name = '%s_%s' % (queue[1],queue[2])
        if name in zabbix_queue:
            zabbix_queue[name]['{#DEPLOY}'].append(queue[0])
            zabbix_queue[name]['{#HEARTBEAT}'].append(queue[3])
            if queue[4] == '运行中':
                zabbix_queue[name]['{#RUNNING}'].append(True)
            else:
                zabbix_queue[name]['{#RUNNING}'].append(False)
        else:
            zabbix_queue[name] = {}
            zabbix_queue[name]['{#NAME}'] = name
            zabbix_queue[name]['{#DEPLOY}'] = [queue[0],]
            #zabbix_queue[name]['{#HEARTBEAT}'] = [time.strptime(queue[5], '%Y-%m-%d %H:%M:%S'),]
            zabbix_queue[name]['{#HEARTBEAT}'] = [queue[3],]
            if queue[4] == '运行中':
                zabbix_queue[name]['{#RUNNING}'] = [True,]
            else:
                zabbix_queue[name]['{#RUNNING}'] = [False,]
    return (zabbix_job,zabbix_queue)

def set(var, val=None):
    if var == 'show':
        print 'issue : %s' % GL.issue()
    elif var == 'issue':
        GL.setIssue(val)








