from django.db import models

from datetime import datetime

# Create your models here.


class user(models.Model):
    """
    用户信息表
    login => 用户登录账号
    password => 用户登录密码
    nickname => 用户姓名
    role => 用户所属角色(9：普通用户，10：管理员，11：超级管理员)
    enable => 用户信息是否被可用(1：可用，0：禁用)
    deleted => 用户信息是否被删除(1：已经被删除，0：未被删除)
    register => 用户信息添加的时间
    """
    login = models.CharField(max_length=64, unique=True, null=False)
    password = models.CharField(max_length=128, null=False)
    nickname = models.CharField(max_length=64, null=False)
    role = models.PositiveSmallIntegerField(null=False, default=9)
    enable = models.PositiveSmallIntegerField(null=False, default=1)
    deleted = models.PositiveSmallIntegerField(null=False, default=0)
    register = models.DateTimeField(auto_now_add=True)







