# 全文搜索实现(Whooshalchemyplus + jieba分词)

### 准备工作
由于Flask-WhooshAlchemy不支持中文分词搜索, 所以需要Flask-WhooshAlchemyPlus来替代之，然后再安装jieba分词。  
如果你暂时没有在虚拟环境上安装Flask-WhooshAlchemyPlus，请安装它。
<pre><code>
pip install Flask-WhooshAlchemy  
pip install jieba
</code></pre>
### 配置
配置 Flask-WhooshAlchemyPlus 也是相当简单。我们只需要告诉扩展全文搜索数据库的名称(文件config.py):
<pre><code>WHOOSH_BASE = os.path.join(basedir, 'search.db')
</code></pre>
### 模型修改
因为把 Flask-WhooshAlchemyPlus 整合进 Flask-SQLAlchemy，我们需要在模型的类中指明哪些数据需要建立搜索索引(文件 app/models.py):
<pre><code>
from jieba.analyse import ChineseAnalyzer

class Post(db.Model):
    __tablename__ = 'posts'
    __analyzer__ = ChineseAnalyzer()
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    #...
</code></pre>
模型有一个新的 __searchable__ 字段，这里面包含数据库中的所有能被搜索并且建立索引的字段。在我们的例子中，我们只要索引 blog 的 body 字段。  
因为这个改变并不影响到关系数据库的格式，因此不需要录制新的迁移脚本。  

### 初始化(app/__init__.py)
<pre><code>
import flask_whooshalchemyplus
from flask_whooshalchemyplus import index_all

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)                                                                                  
    login_manager.init_app(app)
    pagedown.init_app(app)
    flask_whooshalchemyplus.init_app(app)        #初始化
    with app.app_context():                      #手动索引 
        index_all(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    #...
</code></pre>
因为之前存储在数据库的 blog 是没有建立索引的。为了保持数据库和全文搜索引擎的同步，我们添加以下代码，由于这段代码运行加载很慢，所以建立索引后我就把它删了。
<pre><code>
from flask_whooshalchemyplus import index_all
    with app.app_context():
        index_all(app)
</code></pre>

### 搜索
现在假设我们在全文索引中有一些 blog，我们可以这样搜索:

```
>>> Post.query.whoosh_search('post').all()  
[<Post u'my second post'>, <Post u'my first post'>, <Post u'my third and last post'>]  
>>> Post.query.whoosh_search('second').all()  
[<Post u'my second post'>]  
>>> Post.query.whoosh_search('second OR last').all()  
[<Post u'my second post'>, <Post u'my third and last post'>]
```

在上面例子中你可以看到，查询并不限制于单个词。实际上，Whoosh 支持一个更加强大的搜索查询语言。

### 搜索表单
我们准备在导航栏中添加一个搜索表单。把表单放在导航栏中是有好处的，因为应用程序所有页都有搜索表单。

首先，我们添加一个搜索表单类(文件 app/main/forms.py):
<pre><code>
class SearchForm(Form):
    search = StringField('搜索', validators=[Required()])
</code></pre>
接着我们必须创建一个搜索表单对象并且使得它对所有模版中可用，因为我们将搜索表单放在导航栏中，导航栏是所有页面共有的。最容易的方式就是在 before_request 函数中创建这个表单对象，接着把它放在全局变量 g 中(文件 app/main/views.py):
<pre><code>
@main.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()
</code></pre>
我们接着添加表单到模板中(文件 app/templates/base.html):

```
<li><a href="{{ url_for('main.index') }}">首页</a></li>
{% if current_user.is_authenticated %}
<li><a href="{{ url_for('main.user', username=current_user.username) }}">个人资料</a></li>
    <form class="navbar-form navbar-left" style="display:inline;" action="{{ url_for('main.search') }}" method="post" name="search">
        {{ g.search_form.hidden_tag() }}{{ g.search_form.search(size=20) }}<input type="submit" value="搜索"></input>
    </form>
{% endif %}
```

注意，只有当用户登录后，我们才会显示搜索表单。before_request 函数仅仅当用户登录才会创建一个表单对象，因为我们的程序不会对非认证用户显示任何内容。

### 搜索视图函数
上面的模版中，我们在 action 字段中设置发送搜索请求到 search 视图函数。search 视图函数如下(文件 app/main/views.py):
<pre><code>
@main.route('/search', methods=['POST'])
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('main.index'))
	return redirect(url_for('main.search_results', query = g.search_form.search.data))
</code></pre>

这个函数实际做的事情不多，它只是从查询表单这能够获取查询的内容，并把它作为参数重定向另外一页。搜索工作不在这里直接做的原因还是担心用户无意中触发了刷新，这样会导致表单数据被重复提交。

### 搜索结果页
一旦查询的关键字被接收到，search_results 函数就会开始工作(文件 app/main/views.py):
<pre><code>
@main.route('/search_results/<query>')
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query).all()
	return render_template('search.html', query=query, posts=results)
</code></pre>


最后一部分就是搜索结果的模版(文件 app/templates/search.html):

```
{% extends "base.html" %}
{% import "_macros.html" as macros %}

{% block title %}Flasky - search{% endblock %}

{% block page_content %}
<div class="page-header">
	<h1>搜索关键词： "{{query}}"</h1>
</div>
{% include "_posts.html" %}
{% endblock %}
```

### 参考文章
[全文搜索](http://www.pythondoc.com/flask-mega-tutorial/textsearch.html#id8)  
[请教使用Flask-WhooshAlchemy做全文搜索时中文的模糊搜索问题](http://cocode.cc/t/flask-whooshalchemy/1529/6)  
[Welcome to Flask-WhooshAlchemyPlus!](https://github.com/Revolution1/Flask-WhooshAlchemyPlus)

# -------------------------------------------------------------------
# 阿里云服务器部署 nginx + gunicorn + supervisor + flask

## 前言：  
本文记录在阿|里云 ECS 服务器上搭建Flask Web应用程序的过程。对照着网上的各种教程跟着部署，不得不说有些教程根本就没有说完整个部署过程，这对于第一次部署的小白来说，这是致命的(包括我/(ㄒoㄒ)/~~ )好在经过两天的努力终于部署成功了，期间部署了N次，重新格式化磁盘N次。那么阿里云ECS服务器配置好了环境为什么公网IP不能访问？[请点这里，知道真相的我眼泪掉下来。](http://fangweiren843.blog.163.com/blog/static/241929142201764104057496/)

## 服务器配置：
  CPU：1核  
  内 存：2G  
  操作系统：Ubuntu 16.04 64位
  
## 连接到云服务器
Vmware虚拟机Ubuntu系统可以通过ssh远程连接到云服务器，在 Windows 系统上，可以使用PuTTY这款软件进行SSH 访问。
PuTTY是一个Telnet、SSH、rlogin、纯TCP以及串行接口连接软件。PuTTY为一开放源代码软件，主要由Simon Tatham维护，使用MIT licence授权。随着Linux在服务器端应用的普及，Linux系统管理越来越依赖于远程。在各种远程登录工具中，Putty是出色的工具之一。Putty是一个绿色免费的、Windows x86平台下的Telnet、SSH和rlogin客户端，但是功能丝毫不逊色于商业的Telnet类工具。PuTTY下载地址：http://www.putty.org/  
1>Vmware虚拟机Ubuntu系统可以通过ssh远程连接到云服务器
<pre><code>
root@fang-virtual-machine:~# ssh root@39.108.62.130                    #回车之后输入密码即可登录云服务器
root@39.108.62.131's password:                                         #此处输入密码，但密码不会显示
Welcome to Ubuntu 16.04.2 LTS (GNU/Linux 4.4.0-82-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

Welcome to Alibaba Cloud Elastic Compute Service !

Last login: Wed Jul  5 14:27:32 2017 from 101.69.71.175
root@iZwz9f34wv2yw5cv8v3a8pZ:~# 
</code></pre>

  @左边的root表示用户名  
  39.108.62.131代表公网IP
  
![](http://img2.ph.126.net/ITV6X0FBBvO2uzHIhOjPgQ==/6632309114328158855.jpg)

2>利用putty登陆SSH主机方法  
打开putty软件，输入公网ip--->登录协议--->会话名称--->Save--->open  
![](http://img0.ph.126.net/1f5CerFrLOQp0qFAUDJ8Vg==/6632475140583953763.jpg)
![](http://img0.ph.126.net/AACILq7DGscmv5yj3KIxfQ==/6632566400049065931.jpg)

## 新建用户  
首次登录到云服务器中，只有一个 root 用户，而使用 root 用户来管理应用的话，是存在风险的(误删系统文件等)，一般是建议使用子用户来管理应用，因此首先需要添加用户。

1.添加一个新用户（假定为nancy）
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:~# useradd -d /home/www -s /bin/bash -m nancy</code></pre>
上面命令中，参数d指定用户的主目录，参数s指定用户的shell，参数m表示如果该目录不存在，则创建该目录。

2.设置新用户的密码。
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:~# passwd nancy
Enter new UNIX password:
Retype new UNIX password:
passwd: password updated successfully
root@iZwz9f34wv2yw5cv8v3a8pZ:~#</code></pre>

3.为新用户设定sudo权限
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:~# visudo</code></pre>
visudo命令会打开sudo设置文件/etc/sudoers，然后按下图位置添加一行。
![](http://img0.ph.126.net/M3YIp6htXEohcl6S1L6qRA==/6632298119211889401.jpg)

  字段说明：
  root ：能使用sudo命令的用户  
  后面第一个ALL，允许使用sudo的主机  
  第二个括号里的ALL为使用sudo后以什么身份来执行命令（目的用户身份）  
  第三个字：ALL为以sudo命令允许执行的命令  
  NOPASSWD表示，切换sudo的时候，不需要输入密码，我喜欢这样比较省事。如果出于安全考虑，也可以强制要求输入密码。

最后，先退出root用户的登录，再用nancy的身份登录，检查到这一步为止，是否一切正常。

## 配置开发环境
服务器的初步配置流程就是这样，接下来配置开发环境。  
我的部署方案是：  
* Flask：Python中的一个轻量级Web开发框架，简单易用，功能强大，关于它的使用可以参考《Flask Web开发:基于Python的Web应用开发实战》这本书  
* Supervisor：监控服务进程的工具；  
* Gunicorn：一个Python WSGI UNIX的HTTP服务器  
* Nginx ：高性能Web服务器+负责反向代|理

项目目录：/home/www

### 创建虚拟环境
用pip安装virtualenv
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# pip install virtualenv</code></pre>

在项目目录/home/www下创建虚拟环境venv
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# virtualenv venv</code></pre>

激活虚拟环境
<pre><code>root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# ls
venv
root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# source venv/bin/activate    #激活虚拟环境
(venv) root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# deactivate           #退出虚拟环境
root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www#</code></pre>

### 安装Flask
首先确保已经进入虚拟环境开发目录
<pre><code>(venv) root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# pip install flask</code></pre>
![](http://img1.ph.126.net/jBkj4tpE07k0nnUmDyyltA==/6632463045956058898.jpg)

现在flask安装完成，使用flask写一个简单的 web 服务。
<pre><code>(venv) root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# vi hello.py</code></pre>

<pre><code>
#hello.py

from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'hello world'

if __name__ == '__main__':
    app.debug = True
    app.run()
</code></pre>

### Gunicorn 的配置
安装gunicorn
<pre><code>(venv) root@iZwz9f34wv2yw5cv8v3a8pZ:/home/www# pip install gunicorn</code></pre>

当我们安装好Gunicorn之后，需要用gunicorn启动flask，注意flask里面的name里面的代码启动了app.run(),这个含义是用flask自带的服务器启动app。这里我们使用了gunicorn，hello.py就等同于一个库文件，被gunicorn调用。
<pre><code>gunicorn -w 4 -b 0.0.0.0:8000 hello:app</code></pre>

此时，我们需要用 8000 的端口进行访问。其中 gunicorn 的部署中，-w 表示开启多少个进程(worker)，-b表示gunicorn开发的访问地址。  
想要结束gunicorn只需执行pkill gunicorn，有时候还的 ps 找到 pid 进程号才能 kill。可是这对于一个开发来说，太过于繁琐，因此出现了另外一个神器---supervisor，一个专门用来管理进程的工具，还可以管理系统的工具进程。

### Supervisor配置
安装supervisor，在项目目录添加supervisor的配置文件，在本例中是/home/www
<pre><code>
(venv) root@:/home/www# pip install supervisor                    #安装supervisor
(venv) root@:/home/www# echo_supervisord_conf > supervisor.conf   #生成supervisor默认配置文件
(venv) root@:/home/www# vi supervisor.conf                        #修改supervisor配置文件，添加gunicorn 进程管理
</code></pre>
在supervisor.conf配置文件底部添加以下内容
<pre><code>[program:hello]
command=/home/www/venv/bin/gunicorn -w 4 -b localhost:8000 hello:app          #supervisor启动命令
directory=/home/www                                                           #项目的文件夹路径

user=nancy   #设置一个非root用户，当我们以root用户启动supervisord之后。nancy也可以对supervisord进行管理
autostart=true                                                                #是否自动启动
autorestart=true                                                              #是否自动重启
stdout_logfile=/home/www/log/gunicorn.log                                     #log日志路径
stderr_logfile=/home/www/log/gunicorn.err                                     #错误日志路径
</code></pre>
supervisor的基本使用命令
<pre><code>
supervisord -c supervisor.conf                             #通过配置文件启动supervisor
supervisorctl -c supervisor.conf status                    #察看supervisor的状态
supervisorctl -c supervisor.conf reload                    #重新载入 配置文件
supervisorctl -c supervisor.conf start [all]|[appname]     #启动指定/所有 supervisor管理的程序进程
supervisorctl -c supervisor.conf stop [all]|[appname]      #关闭指定/所有 supervisor管理的程序进程
</code></pre>

### 配置 Nginx
安装Nginx
<pre><code>root@:/home/www# apt-get install nginx</code></pre>

Nginx的配置文件在/etc/nginx/sites-available/目录下，有一个default文件，只需要新建一个default文件替换掉原有的：
<pre><code>
(venv) root@:/home/www# cd /etc/nginx/sites-available/         #切换到目录sites-available
(venv) root@:/etc/nginx/sites-available# rm default            #删除default
(venv) root@:/etc/nginx/sites-available# vi default            #新建并编辑default
</code></pre>
编辑内容如下：
#设定虚拟主机配置
<pre><code>
server {
    listen       80;                  #侦听80端口
    server_name  39.108.62.131;       #server_name就是你的域名或者公网IP

    #默认请求
    location / {
        proxy_pass http://localhost:8000;   #设置被代|理服务器的端口或套接字，以及URL
        proxy_redirect off;
        proxy_set_header Host $host;        #以下三行，目的是将代|理服务器收到的用户的信息传到真实服务器上
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

}
</code></pre>
测试运行
<pre><code>
(venv) root@:/etc/nginx/sites-available# cd /home/www/             #回到项目目录
(venv) root@:/home/www# service nginx start                        #启动nginx和supervisor
(venv) root@:/home/www# supervisord -c supervisor.conf
</code></pre>
到此部署已经全部完成，接下来就可以用域名或公网IP访问了。

## 参考文章
[阿里云部署 Flask + WSGI + Nginx 详解](http://www.cnblogs.com/Ray-liang/p/4173923.html?utm_source=tuicool&utm_medium=referral)  
[GitHub - HortonHu/HO: 基于Flask的博客网站](https://github.com/HortonHu/HO)  
[Flask 搭建 Web 应用 | classTC的博客](http://classtc.com/2016/07/12/160711/)  
[GitHub - Junctionzc/flask-blog: 《Flask Web开发》的个人部署版本，包含学习笔记。](https://github.com/Junctionzc/flask-blog)  
[Flask Gunicorn Supervisor Nginx 项目部署小总结 · GitHub](https://gist.github.com/binderclip/f6b6f5ed4d71fa64c7c5)  
[python web 部署：nginx + gunicorn + supervisor + flask 部署笔记](http://www.jianshu.com/p/be9dd421fb8d)  
[flask几种部署方式实践 · 搬砖工的日常](https://eclipsesv.com/2016/12/12/flask%E9%83%A8%E7%BD%B2%E6%96%B9%E5%BC%8F%E5%AE%9E%E8%B7%B5/)  
[centos下通过gunicorn+nginx+supervisor部署Flask项目](https://zhuanlan.zhihu.com/p/21262280)  
[Ubuntu 下 WSGI + Nginx + Supervisor 部署 Flask](http://jinke.me/2015/12/09/flask-linux.html)  
[Linux服务器的初步配置流程](http://www.ruanyifeng.com/blog/2014/03/server_setup.html)

# -------------------------------------------------------------------
# MTV模式  

Django的MTV模式本质上和MVC是一样的，也是为了各组件间保持松耦合关系，只是定义上有些许不同  
Django的MTV分别是值：

  * M 代表模型（Model）：负责业务对象和数据库的关系映射(ORM)。  
  * T 代表模板 (Template)：负责如何把页面展示给用户(html)。  
  * V 代表视图（View）：负责业务逻辑，并在适当时候调用Model和Template。
  
除了以上三层之外，还需要一个URL分发器，它的作用是将一个个URL的页面请求分发给不同的View处理，View再调用相应的Model和Template，MTV的响应模式如下所示：

    1.Web服务器（中间件）收到一个http请求  
    2.Django在URLconf里查找对应的视图(View)函数来处理http请求  
    3.视图函数调用相应的数据模型来存取数据、调用相应的模板向用户展示页面  
    4.视图函数处理结束后返回一个http的响应给Web服务器  
    5.Web服务器将响应发送给客户端
    
![](https://github.com/fangweiren/leetcode/blob/master/screenshots/MVT.png?raw=true)
