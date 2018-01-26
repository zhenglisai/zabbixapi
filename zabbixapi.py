#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import time
import requests
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# zabbix认证信息
zabbix_url = "http://52.80.127.55/zabbix/api_jsonrpc.php"
zabbix_username = "Admin"
zabbix_password = "zabbix"
#全局变量定义
local_path = os.path.split(os.path.realpath(__file__))[0]
log_file = local_path + os.path.sep + "log_zabbixapi.log"
headers = {"Content-Type": "application/json"}
#记录日志模块
def log(data):
    file = open(log_file, 'a+')
    date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    try:
        file.write("%s %s" %(date,data)+'\n')
    finally:
        file.close()
#zabbix登陆
def zabbix_login():
    try:
        data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
            "user": zabbix_username,
            "password": zabbix_password
        },
        "id": 0
        })
        request_data = requests.post(zabbix_url, data=data, headers=headers)
        return json.loads(request_data.text)['result']
    except BaseException,e:
        log("zabbix_login: %s" %e)
        return "error"
#zabbix退出
def zabbix_logout(token):
    try:
        data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "user.logout",
            "params": [],
            "id": 0,
            "auth": token
        })
        request_data = requests.post(zabbix_url, data=data, headers=headers)
        result = json.loads(request_data.text)['result']
        if result:
            return "ok"
        else:
            log("登出失败，原因：%s" %e)
            return "error"
    except BaseException,e:
        log("zabbix_logout: %s" %e)
        return "error"
#获取主机组id
def get_group_id(group_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "name": [
                            group_name
                        ]
                    }
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        group_id = json.loads(request.text)['result']
        if len(group_id) == 0:
            return "null"
        else:
            return group_id[0]['groupid']
    except BaseException,e:
        log("get_group_id: %s" %e)
        return "error"
    finally:
        zabbix_logout(token)
#创建服务器组
def create_group(group_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.create",
                "params": {
                    "name": group_name
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        group_id = json.loads(request.text)['result']['groupids'][0]
        return group_id
    except BaseException,e:
        log("create_group: %s" %e)
        return "error"
    finally:
        zabbix_logout(token)
#获取模板id
def get_template_id(template_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "template.get",
                "params": {
                    "output": "extend",
                    "filter": {
                        "host": [
                            template_name
                        ]
                    }
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        template_id = json.loads(request.text)['result'][0]['templateid']
        return template_id
    except BaseException,e:
        log('get_template_id: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#创建主机
def create_host(host_name,group_name,host_ip,host_port,template_name):
    try:
        token = zabbix_login()
        template_id = get_template_id(template_name)
        if template_id == "error":
            return "error"
        group_id = get_group_id(group_name)
        if group_id == "error":
            return "error"
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.create",
                "params": {
                    "host": host_name,
                    "interfaces": [
                        {
                            "type": 1,
                            "main": 1,
                            "useip": 1,
                            "ip": host_ip,
                            "dns": "",
                            "port": host_port
                        }
                    ],
                    "groups": [
                        {
                            "groupid": group_id
                        }
                    ],
                    "templates": [
                        {
                            "templateid": template_id
                        }
                    ],
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        host_id = json.loads(request.text)['result']['hostids'][0]
        return host_id
    except BaseException,e:
        log('create_host: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#删除主机
def delete_host(host_id):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.delete",
                "params": [
                    host_id
                ],
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        host_id_deleted = json.loads(request.text)['result']['hostids'][0]
        if host_id_deleted == host_id:
            return "ok"
        else:
            log('delete_host: failed %s' %request.text)
            return "failed"
    except BaseException,e:
        log('delete_host: %s' %e)
        return "error"
#获取主机状态（监控状态是否正常）
def get_host_status(hostid):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["available"],
                    "hostids": hostid
                },
                "id": 0,
                "auth": token
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        host_status = json.loads(request.text)['result'][0]['available']
        if host_status == '1':
            return "available"
        else:
            return "unavailable"
    except BaseException,e:
        log('get_host_status: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#根据监控名获取监控项最新值
def get_item_value_name(host_id, item_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "item.get",
                "params": {
                    "output": "extend",
                    "hostids": host_id,
                    "search": {
                        "name": item_name
                    },
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        last_value = json.loads(request.text)['result'][0]['lastvalue']
        return last_value
    except BaseException,e:
        log('get_item_value_name: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#根据监控项键值获取监控项最新值
def get_item_value_key(host_id, item_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "item.get",
                "params": {
                    "output": "extend",
                    "hostids": host_id,
                    "search": {
                        "key_": item_name
                    },
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        last_value = json.loads(request.text)['result'][0]['lastvalue']
        return last_value
    except BaseException,e:
        log('get_item_value_key: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#获取某个主机组下所有主机id
def get_group_hosts_id(group_name):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                    "selectHosts": "hostid",
                    "filter": {
                        "name": [
                            group_name
                        ]
                    }
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        hosts = json.loads(request.text)['result'][0]['hosts']
        host_id_list = []
        for host_id in hosts:
            host_id_list.append(host_id)
        return host_id_list
    except BaseException,e:
        log('get_group_hosts_id %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#获取主机的监控项数
def get_host_item_num(host_id):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "item.get",
                "params": {
                    "hostids": host_id,
                    "countOutput": "true",
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        item_num = json.loads(request.text)['result']
        return item_num
    except BaseException,e:
        log('get_item_num: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#获取主机的自发现规则id列表
def get_LLD_ids(host_id):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "discoveryrule.get",
                "params": {
                    "output": "extend",
                    "hostids": host_id
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        item_ids = json.loads(request.text)['result']
        lld_id_list = []
        for item_id in item_ids:
            lld_id_list.append(item_id['itemid'])
        return lld_id_list
    except BaseException,e:
        log('get_LLD_ids: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#开启某个主机的自发现规则
def LLD_on(item_id, host_id):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "discoveryrule.update",
                "params": {
                    "itemid": item_id,
                    "hostids": host_id,
                    "status": 0
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        item_result = json.loads(request.text)['result']['itemids']
        if len(item_result) != 0:
            return "ok"
        else:
            return "failed"
    except BaseException,e:
        log('LLD_on: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
#关闭某个主机的自发现规则
def LLD_off(item_id, host_id):
    try:
        token = zabbix_login()
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "discoveryrule.update",
                "params": {
                    "itemid": item_id,
                    "hostids": host_id,
                    "status": 1
                },
                "auth": token,
                "id": 0
            })
        request = requests.post(zabbix_url, data=data, headers=headers)
        lld_result = json.loads(request.text)['result']['itemids']
        if len(lld_result) != 0:
            return "ok"
        else:
            return "failed"
    except BaseException,e:
        log('LLD_off: %s' %e)
        return "error"
    finally:
        zabbix_logout(token)
