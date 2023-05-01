import itchat
import time
from itchat.content import TEXT
import requests
from collections import defaultdict

#唤醒词是两个空格
openai_api_key = "api-sk"  #这里填充openai密钥
URL = "https://api.openai.com/v1/chat/completions"


#询问GPT
def askGPT(question):
	payload = {
		"model": "gpt-3.5-turbo",
		"temperature" : 1.0,
		"max_tokens" : 100,
		"n" : 1,
		"messages" : question
	}

	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {openai_api_key}"
	}

	print("上下文是：", question)

	response = requests.post(URL, headers=headers, json=payload)
	response = response.json()

	#print(response)
	return response['choices'][0]['message']['content']

# 生成微信登录二维码
def qrCallback(uuid, status, qrcode):
    # logger.debug("qrCallback: {} {}".format(uuid,status))
    if status == "0":
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(qrcode))
            _thread = threading.Thread(target=img.show, args=("QRCode",))
            _thread.setDaemon(True)
            _thread.start()
        except Exception as e:
            pass

        import qrcode

        url = f"https://login.weixin.qq.com/l/{uuid}"

        qr_api1 = "https://api.isoyu.com/qr/?m=1&e=L&p=20&url={}".format(url)
        qr_api2 = "https://api.qrserver.com/v1/create-qr-code/?size=400×400&data={}".format(url)
        qr_api3 = "https://api.pwmqr.com/qrcode/create/?url={}".format(url)
        qr_api4 = "https://my.tv.sohu.com/user/a/wvideo/getQRCode.do?text={}".format(url)
        print("You can also scan QRCode in any website below:")
        print(qr_api3)
        print(qr_api4)
        print(qr_api2)
        print(qr_api1)

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)


def after_login():
	print("登录后调用")

def after_logout():
	print("退出后调用")

# 不带具体对象注册，将注册为普通消息的回复方法；文本消息类型
@itchat.msg_register(TEXT)
def simple_reply(msg):
	print(msg)
	#当消息开头是两个空格时，启动机器人回复
	if msg['Content'].startswith('  '):	#修改唤醒词在这里，唤醒词修改后，82行也需同步修改
		FromUserName = msg['FromUserName'][1:] #消息发送者，截取掉第一个符号，@bf56f53b61dead6cb7a02b44775091d1b460a64e38ec5c5df9ab835cf75fd7f5
		Content = msg['Content'][2:] #消息内容，截取掉唤醒词
		
		print('received: %s from %s' % (Content,  FromUserName))

		#查找历史记录
		ddd = defaultdict(dict, **userSession)
		msgHistory = ddd[FromUserName] #数组
		print(len(msgHistory))
		if len(msgHistory) == 0:
			#第一次用，初始化一下
			msgHistory = []
			msgHistory.append({"role": "system", "content": ""})

		#把最新的询问加入到上下文元组
		tempDict1 = {"role": "user", "content": Content}
		msgHistory.append(tempDict1)
		#此处调用GPT
		resultGPT = ""
		try:
			resultGPT = askGPT(msgHistory)
		except Exception as e:
			resultGPT = "我出错了"

		print('GPT: %s' % resultGPT)
		#将GPT结果更新至上下文
		tempDict2 = {"role": "assistant", "content": resultGPT}
		msgHistory.append(tempDict2)
		#更新上下文存储
		userSession[FromUserName] = msgHistory

		print(userSession)
		return resultGPT #直接回复给发送者

#所有消息类型
@itchat.msg_register
def general_reply(msg):
	return 'I received a %s' % msg.type

def sendToGroup(groupName):
	chatrooms = itchat.search_chatrooms(name=groupName)	#返回搜索的群聊列表
	if chatrooms and len(chatrooms) > 0:
		print("群聊名字：" + chatrooms[0]['UserName'])
		itchat.send("欢迎大家", chatrooms[0]['UserName'])
	else:
		print('抱歉，不存在这个群聊：%s' % groupName) 

#一个发送者id对应一个chat的会话数组，初始化为空map
userSession = {
	# "user1":[ #历史对话记录
	# 			{"role": "system", "content": f"You are an assistant who tells any random and very short fun fact about this world."},
	# 			{"role": "user", "content": f"Write a fun fact about programmers."},
	# 			{"role": "assistant", "content": f"Programmers drink a lot of coffee!"},
	# 			{"role": "user", "content": f"Write one related to the Python programming language."}
	# 		],
	# "user2":[ #历史对话记录
	# 			{"role": "system", "content": f"You are an assistant who tells any random and very short fun fact about this world."},
	# 			{"role": "user", "content": f"Write a fun fact about programmers."},
	# 			{"role": "assistant", "content": f"Programmers drink a lot of coffee!"},
	# 			{"role": "user", "content": f"Write one related to the Python programming language."}
	# 		]
}

if __name__ == '__main__':
	itchat.auto_login(
		enableCmdQR=2,
		qrCallback=qrCallback,
		loginCallback=after_login, 
		exitCallback=after_logout
	)
	itchat.run()	#阻塞监听

	# # 获取自己的用户信息，返回自己的属性字典
	# itchat.search_friends()
	# friends = itchat.search_friends(nickName='Nanny')
	# #print(friends)
	# friend = friends[0]
	# itchat.send("祝您前程似锦", friend['UserName'])

	# sendToGroup("礼帽")

	#itchat.logout()  #推出微信