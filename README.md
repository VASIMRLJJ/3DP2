# 3DP2
3d打印云盒项目

1.软件运行平台
==============

本软件为3d打印机云盒配套软件，一般运行在装有linux系统的卡片式ARM计算机上，例如树莓派，本软件运行需要配置环境

2.环境的配置
============

2.1 更改软件源
--------------

国内linux官方源速度很慢，建议改用清华或中科大软件源，网址如下

清华镜像源：<https://mirrors.tuna.tsinghua.edu.cn/>

中科大镜像源：<http://mirrors.ustc.edu.cn/>

网站上均有配置指南

2.2 安装Python3
---------------

命令行输入python3，没有交互式编程环境出现则需要自行编译安装：

菜鸟教程：<https://www.runoob.com/python3/python3-install.html>

然后安装pip3，运行以下命令：

sudo apt-get update

sudo apt-get install python3-pip

然后更改pypi源：

清华镜像源教程：<https://mirrors.tuna.tsinghua.edu.cn/help/pypi/>

2.3 配置python第三方包
----------------------

运行以下命令：

pip3 install flask

pip3 install pyserial

pip3 install requests

2.4 安装wiringpi用于控制LED
---------------------------

Wiringpi网址（树莓派）：*https://github.com/WiringPi/WiringPi*

Wiringop-zero网址（香橙派0）：*https://github.com/xpertsavenue/WiringOP-Zero*

安装教程就在readme里面

2.5 配置自启动服务
------------------

在/etc/systemd文件夹下创建自启动服务，具体是创建3dp.service服务

然后运行以下命令激活服务：

sudo systemctl daemon-reload

systemctl enable 3dp

2.6 配置网络接口等
------------------

| 2019.08.31 | Kevin Lee |
|------------|-----------|

