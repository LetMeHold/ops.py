#!/usr/bin/python  
# -*- coding: UTF-8 -*-

from gl import *
from fabric import network
from fabric.api import env,local,cd,run,execute
from fabric.contrib.project import rsync_project

#class Remote:
    #
    #def __init__(self, ip):
        #self.__ip = ip
        #self.__user = 'root'
        #self.__ssh = sshLogin(ip, self.__user, GL.pwd(), GL.rsa())
        #GL.LOG.info('(%s) 远程登录 (%s) 成功' % (self.__user,ip))
    #
    #def ip(self):
        #return self.__ip
    #
    #def execute(self, cmd):
        #GL.LOG.info('远程 (%s) 执行命令 (%s) 开始' % (self.__ip,cmd))
        #stdout = sshExecute(self.__ssh, cmd)
        #info = stdout[stdout.find('\n'):]   #第一行不是输出,只是发送的命令
        #GL.LOG.info('远程 (%s) 执行命令 (%s) 输出\n%s' % (self.__ip,cmd,info))
        #GL.LOG.info('远程 (%s) 执行命令 (%s) 结束' % (self.__ip,cmd))
    #
    #def logout(self):
        #sshLogout(self.__ssh)
        #GL.LOG.info('(%s) 已从远程 (%s) 注销' % (self.__user,self.__ip))

#验证密码是否正确
#def verifyPwd(pwd):
    #ip = GL.deploy()[GL.env()]['deploy'].keys()[0]
    #try:
        #ssh = sshLogin(ip, 'root', pwd, GL.rsa())
        #ssh.logout()
        #return True
    #except Exception as e:
        #print e
        #return False

#获取远程ssh连接实例
#def remoteInstance(ip):
    #if GL.remote.has_key(ip):
        #return GL.remote[ip]
    #else:
        #remote = Remote(ip)
        #GL.remote[ip] = remote
        #return remote

#远程执行指定的命令
#def remoteCmd(ip, cmd):
    #remote = remoteInstance(ip)
    #remote.execute(cmd)

def localCmd(cmd):
    GL.LOG.debug('本地执行命令 (%s) 开始' % cmd)
    execute(local, cmd)
    GL.LOG.debug('本地执行命令 (%s) 结束' % cmd)

def remoteCmd(ip, cmd, _pty=True):
    GL.LOG.debug('远程 (%s) 执行命令 (%s) 开始' % (ip,cmd))
    ip = GL.getRealIP(ip)
    execute(run, cmd, host=ip, pty=_pty)
    GL.LOG.debug('远程 (%s) 执行命令 (%s) 结束' % (ip,cmd))

#def remoteCmds(ips, cmd, _pty=True):
    #GL.LOG.debug('远程 (%s) 执行命令 (%s) 开始' % (ips,cmd))
    #execute(run, cmd, '-P', hosts=ips, pty=_pty)
    #GL.LOG.debug('远程 (%s) 执行命令 (%s) 结束' % (ips,cmd))

def parseJobs(page):
    pt1 = re.compile(r'(?isu)<tr.*?>(.*?)</tr>')
    pt2 = re.compile(r'(?isu)<td.*?>(.*?)</td>')
    pt3 = re.compile(r'(?isu)<span.*?>(.*?)</span>')
    pt4 = re.compile(r'(?isu)^(.*?)<br />.*?onclick="(.*?)"')
    pt5 = re.compile(r'(?isu)^(.*?)<br />.*?onclick="(.*?)"')
    jobs = []
    for td in pt1.findall(page):
        tds = []
        for item in pt2.findall(td):
            tds.append(item)
        if len(tds) >= 8:
            jobs.append(tds)

    for job in jobs:
        jobname = pt3.findall(job[2])
        if len(jobname) > 0:
            job[2] = jobname[0]
        status = pt4.findall(job[6])
        if len(status) > 0:
            job[6] = status[0][0].strip()
            job.append(status[0][1])
        isrun = pt5.findall(job[7])
        if len(isrun) > 0:
            job[7] = isrun[0][0].strip()
            job.append(isrun[0][1])
    return jobs

def parseQueues(page):
    pt1 = re.compile(r'(?isu)<tr.*?>(.*?)</tr>')
    pt2 = re.compile(r'(?isu)<td.*?>(.*?)</td>')
    pt3 = re.compile(r'(?isu)<span.*?>(.*?)</span>')
    pt4 = re.compile(r'(?isu)^(.*?)<br/>.*?onclick="(.*?)"')
    queues = []
    for td in pt1.findall(page):
        tds = []
        for item in pt2.findall(td):
            tds.append(item)
        if len(tds) >= 6:
            queues.append(tds)

    for q in queues:
        qname = pt3.findall(q[2])
        if len(qname) > 0:
            q[2] = qname[0]
        status = pt4.findall(q[5])
        if len(status) > 0:
            q[5] = status[0][0].strip()
            q.append(status[0][1])
    return queues

def parseCenterSrv(page):
    pt1 = re.compile(r'(?isu)<tr.*?>(.*?)</tr>')
    pt2 = re.compile(r'(?isu)<td.*?>(.*?)</td>')
    pt3 = re.compile(r'(?isu)(^.*?)<input.*?$')
    srvs = []
    for td in pt1.findall(page):
        tds = []
        for item in pt2.findall(td):
            tds.append(item)
        if len(tds) == 3:
            srvs.append(tds)
    for srv in srvs:
        tmp = pt3.findall(srv[2])
        if len(tmp) > 0:
            srv[2] = tmp[0].strip()
    return srvs

def timekeeping(sec):
    for i in range(sec):
        p = '\r%s' % str(i+1)
        print p,
        time.sleep(1)
        sys.stdout.flush()
    print



