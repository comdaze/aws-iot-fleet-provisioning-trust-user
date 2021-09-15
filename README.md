# AWS IoT基于可信用户的设备队列预置
## 设备端WiFi配网
新设备开箱通电后，用手机搜索到新设备的SoftAP，然后在APP中填入无线路由器的SSID 和 wifi密码信息传入设备，确认后设备重启，连接无线路由器的wifi ssid，完成配网，流程示意图如下：

![wifi_smartconfig](/pics/wifi_smartconfig.png "wifi_smartconfig")

采用树莓派Raspberry Pi 3B+,下载RaspiWiFi程序，并且初始化安装
```
$ git clone https://github.com/comdaze/aws-iot-fleet-provisioning-trust-user.git

$ cd aws-iot-fleet-provisioning-trust-user/RaspiWiFi
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

![WiFi HotPoint](/pics/Hotpoint.jpeg "WiFi HotPoint")

查看热点路由器的IP地址：

![Router_IP](/pics/Router_IP.jpeg "Router_IP")

打开手机浏览器输入：http://10.0.0.1 ,可以看到WiFi Setup设置界面

![WiFI_Setup_1](/pics/WiFi_Setup_1.jpeg "WiFI_Setup_1")

选择可以连接Internet的WiFi热点：

![WiFI_Setup_2](/pics/WiFi_Setup_2.jpeg "WiFI_Setup_2")

输入密码，点击提交，此时已经给树莓派设置好了WiFi，树莓派会自动重启

![WiFI_Setup_3](/pics/WiFi_Setup_3.jpeg "WiFI_Setup_3")

此时看到树莓派已经连接了刚才设置好的可以连接internet的WiFi热点.

## 基于可信用户的IoT设备注册
AWS提供了几种不同的方式来配置设备并在上面安装证书。可以参看[白皮书](https://d1.awsstatic.com/whitepapers/device-manufacturing-provisioning.pdf)这篇中得到了详细描述。

本项目重点讨论 "由受信任的用户队列预置 "这一选项。当需要高度的安全性时，当制造供应链不被信任时，或者由于技术限制、成本或应用的具体限制，不可能在制造供应链中配置设备时，建议采用 "受信任用户的队列预置"的方式。使用这种方法，凭证永远不会暴露在制造供应链中。请阅读[这里](https://docs.aws.amazon.com/iot/latest/developerguide/provision-wo-cert.html)了解更多细节。
### 基本流程
安装者使用他编写和拥有的移动/Web应用，并与AWS进行认证。使用受信任的（认证的）用户API，安装者收到一个临时的X.509证书和私钥，有效期为5分钟。使用移动/网络应用，证书被传递给设备。设备连接到AWS IoT，并将临时凭证换成由AWS CA签署的唯一X.509证书和私钥。在这个工作流程中，AWS资源包括Thing名称、策略和证书都在AWS账户中设置。

![fp_by_trasted_user_flow](./pics/fp_by_trasted_user_flow.png "fp_by_trasted_user_flow")
### 用户认证系统部署
移动或者Web应用的用户认证可以采用Amazon Cognito User Pool或者其他认证服务，在这里我们采用开源用户认证系统[Keycloak](https://www.keycloak.org/),在AWS云上自动化部署请参考[Keycloak-on-AWS](https://github.com/aws-samples/keycloak-on-aws)。

移动/Web用户通过Keycloak认证登录后拿到Access Token，通过和Amazon Cognito Identity Pools集成，获得AWS的服务访问凭证Access Key和Securt Key，过程示意图如下：

![amazon-cognito-ext-auth-enhanced-flow](./pics/amazon-cognito-ext-auth-enhanced-flow.png "amazon-cognito-ext-auth-enhanced-flow")

Keycloak和Amazon Cognito Identity Pools集成配置请参见[部署向导](https://github.com/aws-samples/keycloak-on-aws/blob/master/doc/DEPLOYMENT_GUIDE.md)最后一部分。

### AWS IoT策略
IoT策略包括允许设备连接到AWS物联网核心消息代理，发送和接收MQTT消息，以及获取或更新设备的影子的操作。策略被附加到一个定义设备身份的证书上。当设备连接时，AWS IoT使用证书来查找附加的策略和它所持有的授权规则。

预置配置工作流程需要两套证书和对应的IoT策略。

第一个物联网策略由AWS物联网附加到临时证书上，用于启动配置工作流程,该策略系统内置，用户无需设定。

第二个策略是附加到设备中的永久证书上，我们需要手动创建第二个物联网策略，它将被附加到配置到设备的永久证书上。这个策略被配置模板引用，并在工作流过程中附加到永久证书上。下面的策略允许设备连接、发布和订阅MQTT消息。

创建新的物联网策略，将其命名为 "pubsub"，并为该策略设置以下内容。用你的账户ID替换'account'。
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws-cn:iot:cn-north-1:account:topic/test/topic*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws-cn:iot:cn-north-1:account:topicfilter/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": [
        "arn:aws-cn:iot:cn-north-1:account:client/test*"
      ]
    }
  ]
}
```
### AWS IoT队列的配置模板

预置模板是一个JSON文档，它使用参数来描述你的设备必须使用的资源，以与AWS IoT互动。在配置队列预置模板时，你可以选择预配置钩子（Pre Provisioning Hook）。Pre Provisioning Hook是一个Lambda函数，用于在允许设备被配置之前验证从设备传递的参数。为了简单起见，我们将不使用Pre Provisioning Hook。

在AWS IoT控制台，导航到 "Onboard"，"Fleet provisioning templates"。
点击'创建模板',点击'开始':

![create_provising_template_start](./pics/create_provising_template_start.png "create_provising_template_start")

模板名称：TrustedUserProvisioningTemplate
在'供应角色'下点击'创建角色'，并命名为'IoTFleetProvisioningRole',勾选‘使用Amazon IoT注册表来管理您的设备队列’,

![create_provising_template_step1](./pics/create_provising_template_step1.png "create_provising_template_step1")

点击'下一步'。
选择'使用现有的AWS IoT策略'并选择之前创建的'pubsub'。
点击'创建模板'。

![create_provising_template_step2](./pics/create_provising_template_step2.png "create_provising_template_step2")

填写物品名称前缀：‘mything_’, 可选选择物品类型以及组，点击‘创建模版’，

![create_provising_template_step3](./pics/create_provising_template_step3.png "create_provising_template_step3")

保持此页面默认设置，

![create_provising_template_step4](./pics/create_provising_template_step4.png "create_provising_template_step4")

点击页面底部的'启用模板'，

![create_provising_template_step5](./pics/create_provising_template_step4.png "create_provising_template_step5")

导航到‘队列预置模版’，选择创建的模板‘TrustedUserProvisioningTemplate’，可以看到模版JSON的内容，可以根据需求点击'Edit JSON'，修改模版。

![create_provising_template_end](./pics/create_provising_template_end.png "create_provising_template_end")

如果用命令行执行如下：
```
aws iot create-provisioning-template \
        --template-name TrustedUserProvisioningTemplate \
        --provisioning-role-arn arn:aws-cn:iam::account:role/service-role/IoTFleetProvisioningRole \
        --template-body file://template.json \
        --enabled 
```
### 移动端应用获得临时预置Claim证书
使用受信任的用户，如终端用户或拥有已知账户的安装人员，可以简化设备制造过程。设备没有唯一的客户证书，而是有一个临时证书，使设备能够连接到AWS IoT，时间只有5分钟。在这5分钟的窗口期间，受信任的用户获得一个具有较长寿命的唯一客户证书，并将其安装在设备上。Claim证书的有限寿命最大限度地减少了证书受损的风险。欲了解更多信息，请参阅由受信任用户提供。
确保创建的Amazon Cognito Identity Pool的‘经过身份验证的角色’，附加了如下策略：
```
{
    "Effect": "Allow",
    "Action": [
        "iot:CreateProvisioningClaim",
    ],
    "Resource": [
        "arn:aws:us-east-1:account:provisioningtemplate/TrustedUserProvisioningTemplate"
    ]
}
```
安装python依赖模块
```
$ pip install requests==2.25.1 
$ pip installurllib3==1.26.5 
$ pip install python-keycloak
```
获取临时证书，保存在手机上
```
python mobile_claim.py
```
证书保存在./certs目录下，将私有密钥和证书发送到设备端。
### 设备端执行  
```     
$ python3 fleetprovisioning.py \
        --endpoint a2jtec7plm36gl.ats.iot.cn-north-1.amazonaws.com.cn \
        --root-ca ./certs/root.ca.pem \
        --cert ./certs/provision.cert.pem \
        --key ./certs/provision.private.key \
        --templateName TrustedUserProvisioningTemplate \
        --templateParameters "{\"SerialNumber\":\"1\",\"DeviceLocation\":\"Seattle\"}"

$ python3 pubsub.py --endpoint a2jtec7plm36gl.ats.iot.cn-north-1.amazonaws.com.cn --root-ca ./certs/root.ca.pem --key  ./certs/long-term.private.key --cert ./certs/long-term.cert.pem --topic test/topic

Connecting to a2jtec7plm36gl.ats.iot.cn-north-1.amazonaws.com.cn with client ID 'test-43340e64-4ddf-4331-a09b-37fe844353c7'...
Connected!
Subscribing to topic 'test/topic'...
Subscribed with QoS.AT_LEAST_ONCE
Sending 10 message(s)
Publishing message to topic 'test/topic': Hello World! [1]
Received message from topic 'test/topic': b'"Hello World! [1]"'
Publishing message to topic 'test/topic': Hello World! [2]
Received message from topic 'test/topic': b'"Hello World! [2]"'
Publishing message to topic 'test/topic': Hello World! [3]
Received message from topic 'test/topic': b'"Hello World! [3]"'
Publishing message to topic 'test/topic': Hello World! [4]
Received message from topic 'test/topic': b'"Hello World! [4]"'
Publishing message to topic 'test/topic': Hello World! [5]
Received message from topic 'test/topic': b'"Hello World! [5]"'
Publishing message to topic 'test/topic': Hello World! [6]
Received message from topic 'test/topic': b'"Hello World! [6]"'
Publishing message to topic 'test/topic': Hello World! [7]
Received message from topic 'test/topic': b'"Hello World! [7]"'
Publishing message to topic 'test/topic': Hello World! [8]
Received message from topic 'test/topic': b'"Hello World! [8]"'
Publishing message to topic 'test/topic': Hello World! [9]
Received message from topic 'test/topic': b'"Hello World! [9]"'
Publishing message to topic 'test/topic': Hello World! [10]
Received message from topic 'test/topic': b'"Hello World! [10]"'
10 message(s) received.
Disconnecting...
Disconnected!

```

程序详细运行流程可以参考[notebook](/notebook/fleet_provisioning.ipynb)。