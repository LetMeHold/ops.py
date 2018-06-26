#!/usr/bin/python  
# -*- coding: UTF-8 -*-

import os
import sys

if len(sys.argv)==4 and (sys.argv[1]=='qb' or sys.argv[1]=='kt' or sys.argv[1]=='yh' or sys.argv[1]=='hp') and (sys.argv[2]=='job' or sys.argv[2]=='queue') and sys.argv[3]=='--discover':
    pass
elif len(sys.argv)==3 and (sys.argv[1]=='qb' or sys.argv[1]=='kt' or sys.argv[1]=='yh' or sys.argv[1]=='hp') and sys.argv[2]=='--up':
    pass
else:
    print '''usage:
    monitor.py <qb/hp/kt/yh> <job/queue> --discover
    monitor.py <qb/hp/kt/yh> --up
    '''
    exit()

if sys.argv[1] == 'qb':
    os.environ['ops_project'] = 'qb'
    host = 'shanpai.monitor'
elif sys.argv[1] == 'kt':
    os.environ['ops_project'] = 'kt'
    host = 'kt.monitor'
elif sys.argv[1] == 'yh':
    os.environ['ops_project'] = 'yh'
    host = 'yh.monitor'
elif sys.argv[1] == 'hp':
    os.environ['ops_project'] = 'hp'
    host = 'hp.monitor'
os.environ['ops_key'] = 'maintenance'

from gl import *
from wrap import *

env = 'pro'
GL.setEnv(env)
GL.LOG = getLogger('TheLogger', 'ops-toolkit-monitor.log')

def job_up_data(data, fname):
    lines = []
    line = '%s monitor_jobs_count %d\n' % (host, len(data['data']))
    lines.append(line)
    for tt in data['data']:
        line = '%s monitor.job[%s.deploy] %s\n' % (host, tt['{#NAME}'], seq.join(tt['{#DEPLOY}']))
        lines.append(line)
        line = '%s monitor.job[%s.distributed] %s\n' % (host, tt['{#NAME}'], tt['{#DISTRIBUTED}'])
        lines.append(line)
        line = '%s monitor.job[%s.heartbeat] %s\n' % (host, tt['{#NAME}'], seq.join(tt['{#HEARTBEAT}']))
        lines.append(line)
        line = '%s monitor.job[%s.running] %s\n' % (host, tt['{#NAME}'], tt['{#RUNNING}'])
        lines.append(line)
        if True not in tt['{#RUNNING}']:
            problem = '没有运行中的定时任务: %s' % tt['{#RUNNING}']
        elif len(tt['{#DISTRIBUTED}'])>1 and False in tt['{#DISTRIBUTED}'] and tt['{#RUNNING}'].count(True)>1:
            problem = '非分布式定时任务启动了不止一个 分布式(%s) 运行状态(%s)' % (tt['{#DISTRIBUTED}'],tt['{#RUNNING}'])
        #elif len(tt['{#DISTRIBUTED}'])>1 and True in tt['{#DISTRIBUTED}'] and tt['{#RUNNING}'].count(True)!=len(tt['{#DISTRIBUTED}']):
            #problem = '分布式定时任务未全部启动 分布式(%s) 运行状态(%s)' % (tt['{#DISTRIBUTED}'],tt['{#RUNNING}'])
        #elif tt['{#NAME}'] == 'qb-data-process_flowMigrateJob':
            #problem = '测试问题触发...........'
        else:
            problem = 'None'
        line = '%s monitor.job[%s.problem] %s\n' % (host, tt['{#NAME}'], problem)
        lines.append(line)
    fname = '/tmp/job.txt'
    f = open(fname, 'w')
    f.writelines(lines)
    f.close()

def queue_up_data(data, fname):
    lines = []
    line = '%s monitor_queues_count %d\n' % (host, len(data['data']))
    lines.append(line)
    for tt in data['data']:
        line = '%s monitor.queue[%s.deploy] %s\n' % (host, tt['{#NAME}'], seq.join(tt['{#DEPLOY}']))
        lines.append(line)
        line = '%s monitor.queue[%s.heartbeat] %s\n' % (host, tt['{#NAME}'], seq.join(tt['{#HEARTBEAT}']))
        lines.append(line)
        line = '%s monitor.queue[%s.running] %s\n' % (host, tt['{#NAME}'], tt['{#RUNNING}'])
        lines.append(line)
        if True not in tt['{#RUNNING}']:
            problem = '没有运行中的队列监控: %s' % tt['{#RUNNING}']
        else:
            problem = 'None'
        line = '%s monitor.queue[%s.problem] %s\n' % (host, tt['{#NAME}'], problem)
        lines.append(line)
    fname = '/tmp/queue.txt'
    f = open(fname, 'w')
    f.writelines(lines)

(zabbix_job,zabbix_queue) = zabbix_monitor()
job_data = {"data": zabbix_job.values()}
que_data = {"data": zabbix_queue.values()}
seq = ','

if sys.argv[2] == '--up':
    job_txt = '/tmp/job.txt'
    job_up_data(job_data, job_txt)
    output = commands.getoutput('zabbix_sender -z 127.0.0.1 -i %s' % job_txt)
    GL.LOG.info('上传定时任务zabbix采集数据：\n' + output)
    que_txt = '/tmp/queue.txt'
    queue_up_data(que_data, que_txt)
    output = commands.getoutput('zabbix_sender -z 127.0.0.1 -i %s' % que_txt)
    GL.LOG.info('上传队列监控zabbix采集数据：\n' + output)
elif sys.argv[2]=='job' and sys.argv[3] == '--discover':
    print json.dumps(job_data, sort_keys=True, indent=4)
elif sys.argv[2]=='queue' and sys.argv[3] == '--discover':
    print json.dumps(que_data, sort_keys=True, indent=4)
else:
    pass


