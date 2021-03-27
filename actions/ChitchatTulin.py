import requests
import json

def get_response(msg):

    apiurl = "http://openapi.tuling123.com/openapi/api/v2"

    # 构造请求参数实体
    params = {"reqType": 0,
              "perception": {
                  "inputText": {
                      "text": msg
                  }
              },
              "userInfo": {
                  "apiKey": "f82bc2ba75a140e88e879593dd5342a2",
                  "userId": "704592"
              }}
    # 将表单转换为json格式
    content = json.dumps(params)

    # 发起post请求
    r = requests.post(url=apiurl, data=content, verify=False).json()
    print("r = " + str(r))

    code = r['intent']['code']
    if code == 10004 or code == 10008:
        message = r['results'][0]['values']['text']
        return message
    return None