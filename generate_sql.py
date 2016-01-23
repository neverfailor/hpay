#!/usr/bin/env python
# -*- coding:UTF-8 -*-
__author__ = 'dchen'
__date__ = '2016/01/23'

import os
import sys
import random
import datetime

"""
    desc:
    自动生成账账通转秒秒通SQL脚本
"""


def create_file(file_name, file_content):
    '''
    创建文件
    :param file_name: 文件名
    :param file_content: 文件内容
    :return: none
    '''

    assert isinstance(file_name, basestring)
    assert isinstance(file_content, basestring)

    file = open(file_name, 'w')
    file.write(file_content)
    file.close()
    return


def generate_create_table_sql_file(table_name):
    '''
    生成创建数据库表脚本
    :param table_name: 表名
    :return: none
    '''

    assert isinstance(table_name, basestring)
    today = datetime.date.today().strftime("%m%d")
    sql = '''--### 用户: hpay
--### Ddl
--### 上线:1
create table ''' + table_name + '''
(
  security_code VARCHAR2(40)
)
tablespace HPAY
pctfree 10
pctused 40
initrans 1
maxtrans 255
storage
(
initial 64
next 8
minextents 1
maxextents unlimited
);
-- Add comments to the columns
comment on column ''' + table_name + '''.security_code
is '账账通转秒秒通设备临时表'''+ today  + '''';
-- Create/Recreate primary, unique and foreign key constraints
alter table ''' + table_name + '''
add constraint PK_SECURITY_CODE_''' + today + ''' unique (SECURITY_CODE)
using index
tablespace HPAY
pctfree 10
initrans 2
maxtrans 255
storage
(
initial 64K
next 1M
minextents 1
maxextents unlimited
);'''

    file_name = '01_hpay_ddl_create_table_' + table_name + '.sql'
    print 'create file: ' + file_name

    create_file(file_name, sql)
    return


def generate_insert_temp_table_sql_file(table_name, list_security_code):
    '''
    账账通转秒秒通设备临时表的脚本
    :param table_name: 表名
    :param list_security_code: 设备号
    :return: none
    '''

    assert isinstance(table_name, basestring);
    assert isinstance(list_security_code, list)

    sql = '''--### 用户: hpay
--### Dml
--### 上线:1\n'''

    for security_code in list_security_code:
        sql = sql + '''insert into hpay.''' + table_name + ''' (SECURITY_CODE) values (\'''' + security_code + '''');\n'''

    sql = sql + '''\n--###验证:''' + str(len(list_security_code)) + '''\nselect count(1) from hpay.''' + table_name + ''';'''

    # 创建SQL文件
    file_name = '02_hpay_dml_batch_insert_security_code.sql'
    print 'create file: ' + file_name
    create_file(file_name, sql)

    return

def generate_update_zzt_convert_mmt_sql_file(table_name):
    '''
    生成账账通转成秒秒通SQL脚本
    :param table_name: 表名
    :return: none
    '''
    assert isinstance(table_name, basestring);
    sql = '''--###用户:hpay
--###Dml
--###上线:1
update hpay.terminal_info t1
set t1.channel = 'FASTBILL',
t1.update_time = to_char(sysdate, 'yyyymmddhh24miss')
 where exists (select 1
         from hpay.unionpay_securitycode_info t2
         where t1.csn = t2.csn
           and exists
         (select 1
                  from hpay.''' + table_name + ''' t3
                 where t2.SECURITY_CODE = t3.SECURITY_CODE
                   and not exists (select 1
                          from hpay.t_merchant_csn t4
                         where t4.csn = t2.csn)));

--###验证:预发布执行结果填入这里
select count(1)
  from hpay.terminal_info t1
 where channel = 'FASTBILL'
   and exists
 (select 1
          from hpay.unionpay_securitycode_info t2
         where t1.csn = t2.csn
           and exists
         (select 1
                  from hpay.''' + table_name + ''' t3
                 where t2.SECURITY_CODE = t3.SECURITY_CODE));'''
    # 创建SQL文件
    file_name = '03_hpay_dml_update_terminal_info_channel_fastbill.sql'
    print 'create file: ' + file_name
    create_file(file_name, sql)

    return


def generate_security_code_list(start_security_code, count):
    '''
    生成设备号列表
    :param start_security_code: 字符串，起始设备号，
        Q8NL00449081
        1100201657050
    :param count: 字符串，生成数量
    :return: 设备号列表
    '''

    assert isinstance(start_security_code, basestring)
    assert isinstance(count, basestring)
    # 获取前缀
    prefix_end_index = len(start_security_code)
    for index in range(len(start_security_code)-len(count)):
        prefix_end_index = len(start_security_code) - len(count) - 1 - index
        if start_security_code[prefix_end_index:prefix_end_index+1] != '0':
            break;

    security_code_prefix = start_security_code[:prefix_end_index]
    print 'security_code_prefix: ' + security_code_prefix
    start = start_security_code[prefix_end_index:]

    int_start = int(start)
    int_count = int(count)
    print 'start: ',int_start, 'count: ', int_count

    list_security_code = []
    for i in range(int(start), int(start) + int(count)):
        list_security_code.append(security_code_prefix + str(i))

    return list_security_code


# 主流程
if len(sys.argv) > 3:
    print '参数不能超过3个'
    exit(0)

# 读取参数
start_security_code = sys.argv[1]
count = sys.argv[2]
table_name = 'TEMP_ZZT_FASTBILL_DEVICE_' + datetime.date.today().strftime("%m%d")
print 'table_name: ' + table_name

#创建目录
fold_name = 'sql'
if os.path.exists(fold_name) == False:
    os.mkdir(fold_name)
# 切换目录
os.chdir(fold_name);

# 步骤1
print 'generate create table sql file. Start'
generate_create_table_sql_file(table_name)
print 'generate create table sql file. Finished'

# 步骤2
print 'generate list of security code. Start'
list_security_code = generate_security_code_list(str(start_security_code), str(count))
print 'generate list of security code. Finished'

# 步骤3
print 'generate create insert sql file. Start'
generate_insert_temp_table_sql_file(table_name, list_security_code)
print 'generate create insert sql file. Finished'

# 步骤3
print 'generate create update sql file. Start'
generate_update_zzt_convert_mmt_sql_file(table_name)
print 'generate create update sql file. Finished'
