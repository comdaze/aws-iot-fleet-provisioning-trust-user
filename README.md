# aws-iot-fleet-provisioning-trust-user
## WiFi 配网
```
$ cd RaspiWiFi
$ sudo python3 initial_setup.py


###################################
##### RaspiWiFi Intial Setup  #####
###################################


Would you like to specify an SSID you'd like to use 
for Host/Configuration mode? [default: RaspiWiFi Setup]: 


Would you like WPA encryption enabled on the hotspot 
while in Configuration Mode? [y/N]:y

What password would you like to for WPA hotspot 
access (if enabled above, 
Must be at least 8 characters) [default: NO PASSWORD]:0123456789

Would you like to enable 
auto-reconfiguration mode [y/N]?: y

How long of a delay would you like without an active connection 
before auto-reconfiguration triggers (seconds)? [default: 300]: 

Which port would you like to use for the Configuration Page? [default: 80]: 

Would you like to enable SSL during configuration mode 
(NOTICE: you will get a certificate ID error 
when connecting, but traffic will be encrypted) [y/N]?: N


Are you ready to commit changes to the system? [y/N]: y

Hit:1 http://archive.raspberrypi.org/debian buster InRelease
Hit:2 http://raspbian.raspberrypi.org/raspbian buster InRelease
Reading package lists... Done
Building dependency tree       
Reading state information... 0%

Installing Flask web server...

#####################################
##### RaspiWiFi Setup Complete  #####
#####################################


Initial setup is complete. A reboot is required to start in WiFi configuration mode...
Would you like to do that now? [y/N]: y

```
此时机器自动重启

打开手机无线局域网设置，可以看到“RaspiWiFi Setup”热点：
![WiFi HotPoint](/pics/hotpoint.jpg "WiFi HotPoint")
查看热点路由器的IP地址：
![Router_IP](/pics/Router_IP.jpg "Router_IP")
打开手机浏览器输入：http://10.0.0.1 ,可以看到WiFi Setup设置界面
![WiFI_Setup_1](/pics/WiFI_Setup_1.png "WiFI_Setup_1")
选择可以连接Internet的WiFi热点：
![WiFI_Setup_2](/pics/WiFI_Setup_2.png "WiFI_Setup_2")
输入密码，点击提交，此时已经给树莓派设置好了WiFi，树莓派会自动重启
![WiFI_Setup_3](/pics/WiFI_Setup_3.png "WiFI_Setup_3")
此时看到树莓派已经连接了刚才设置好的可以连接internet的WiFi热点

## 基于可信用户的IoT设备注册
