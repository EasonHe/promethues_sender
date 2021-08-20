#*_ encoding=utf-8 *
from  flask import  Flask,request
import  yaml,smtplib,requests,json
from email.mime.text import MIMEText
from gevent import monkey
from gevent import pywsgi

# msg = {'status': 'firing', 'externalURL': 'http://master:9093', 'groupLabels': {'alertname': 'node_up'}, 'version': '4',
#        'commonAnnotations': {}, 'receiver': 'hewei', 'groupKey': '{}:{alertname="node_up"}', 'alerts': [
#         {'status': 'firing',
#          'labels': {'instance': 'work2', 'job': 'styml', 'serveice': 'db', 'alertname': 'node_up', 'team': 'node'},
#          'endsAt': '0001-01-01T00:00:00Z',
#          'generatorURL': 'http://master:9090/graph?g0.expr=up+%3D%3D+0\\u0026g0.tab=1',
#          'startsAt': '2018-06-05T19:35:52.111745952+08:00',
#          'annotations': {'description': 'work2 of job styml has been down for more than 1 minutes.',
#                          'summary': 'Instance work2 down'}}, {'status': 'firing',
#                                                               'labels': {'instance': 'work1', 'job': 'styml',
#                                                                          'service': 'web', 'alertname': 'node_up',
#                                                                          'team': 'node'},
#                                                               'endsAt': '0001-01-01T00:00:00Z',
#                                                               'generatorURL': 'http://master:9090/graph?g0.expr=up+%3D%3D+0\\u0026g0.tab=1',
#                                                               'startsAt': '2018-06-05T19:38:52.114175492+08:00',
#                                                               'annotations': {
#                                                                   'description': 'work1 of job styml has been down for more than 1 minutes.',
#                                                                   'summary': 'Instance work1 down'}}],
#        'commonLabels': {'job': 'styml', 'alertname': 'node_up', 'team': 'node'}}
monkey.patch_all()
app =Flask(__name__)
def sender_mail(content=None,subject=None,receiver=None):
    try:
        f = open('conf/mail.yml')
        arg = yaml.load(f)
        f.close()
        for user_info in arg['send_to']:
            if user_info['name'] == receiver:
                print (receiver)
                tos = user_info['user_list']

        smtp_server = arg['mconf']['smtp_server']
        smtp_port = arg['mconf']['smtp_port']
        smtp_username = arg['mconf']['fromuser']
        smtp_password = arg['mconf']['password']
        fromuser= arg['mconf']['fromuser']
        print(content,subject,tos)
        body = "{},<br>".format(content)
        body += "<p> come from alertmanager.</p>"
        msg = MIMEText(body, "html",'utf-8')
        msg["Subject"] = subject
        msg["From"] = fromuser
        msg["To"] = ",".join(tos)
        msg["Accept-Language"] = "zh-CN"
        msg["Accept-Charset"] = "ISO-8859-1,utf-8"
        s = smtplib.SMTP_SSL(smtp_server,smtp_port);
        s.set_debuglevel(1)
        s.login(smtp_username, smtp_password)
        s.sendmail(smtp_username,tos, msg.as_string())

        return True
    except  ValueError as e:
        print(e)
        return  False
    #raise Exception('send fail')

@app.route('/',methods=['POST'])
def index():
    if request.method == "POST":
        msg= eval(request.get_data())
        receiver = msg['receiver']
        aler_num = len(msg['alerts'])
        aler_name = 'aler_name={}'.format( msg['groupLabels']['alertname'])
        title =  'alerts for  ' + aler_name
        print title
        list_status = '[{}]'.format(aler_num) + msg['status']
        print list_status
        title = title  + '--' + list_status
        content = ''
        for  alert in msg['alerts']:
            content = content + '<br><br><b>lables</b><br>'
            #add start time
            content =content + 'startsAt={}'.format(alert['startsAt'])
            for k,v in  alert['labels'].items():
                content = content + "<br>{} ={}".format(k,v)
            content = content + "<br><b>Annotations</b>"
            for k,v in  alert['annotations'].items():
                print k,v
                content = content + "<br>{}={} ".format(k,v)
        print content
        if sender_mail(content=content,receiver=receiver,subject=title) == True:
            return "success"
#钉钉告警接口,接收类型为json
@app.route('/dingding',methods=["POST"])
def ding_sender():
    if request.method == "POST":
        msg = eval(request.get_data())
        print  type(msg)
        headers = {'Content-Type': 'application/json'}
        r = requests.post('https://oapi.dingtalk.com/robot/send?access_token=3cea4a9aa4b6a21d4a71d67040816890a0672a4685a52d3ad43',headers=headers,json=msg)
        r.encoding = 'utf-8'
        content  = r.text
        print content
    return  "dingding return code status {}".format('eeee')

@app.route('/promethues_dd',methods=["POST"])
def promethues():
    if request.method == "POST":
        msg = eval(request.get_data())
        long_str = "## Prometheus生产环境告警\n"
        receiver = msg['receiver']
        aler_num = len(msg['alerts'])
        aler_name = 'aler_name={}'.format( msg['groupLabels']['alertname'])
        title =  'alerts for  ' + aler_name
        list_status = '[{}]'.format(aler_num) + msg['status']
        title = title  + ' ' + list_status
        print title
        long_str = long_str +  "### {}\n".format(title)
        for  alert in msg['alerts']:
            long_str = long_str  + '#### lables\n'
            #add start time
            long_str = long_str + '##### startsAt={}\n'.format(alert['startsAt'])
            for k,v in  alert['labels'].items():
                long_str = long_str + "##### {}={}\n".format(k,v)
            long_str = long_str + "#### Annotations\n"
            for k,v in  alert['annotations'].items():
                print k,v
                long_str = long_str + "##### {}={}\n".format(k,v)
        mydata = {"msgtype": "markdown", "markdown": {"title": title, "text": "temp"}}
        mydata["markdown"]["text"] = long_str
        #mydata = json.dumps(mydata, encoding='utf-8', ensure_ascii=False) 这里不需要处理数据了
        headers = {'Content-Type': 'application/json'}
        #mydata =eval(mydata)， 这里不需要处理数据了
        r = requests.post('https://oapi.dingtalk.com/robot/send?access_token=3cea4a9aa4b6a21d4a71d67040816890a0672a4685a52d3ad43f',headers=headers, json=mydata)
        r.encoding = 'utf-8'
        content = r.text
        print content
    return "dingding return code status {}".format('eeee')
if __name__ == '__main__':
    #sender_mail(receiver='yunwei')
    #app.run(host='0.0.0.0',debug=True)
    server = pywsgi.WSGIServer(('0.0.0.0',5000),app)
    server.serve_forever()



