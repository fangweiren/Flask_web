# MTV模式  

Django的MTV模式本质上和MVC是一样的，也是为了各组件间保持松耦合关系，只是定义上有些许不同  
Django的MTV分别是值：

  *M 代表模型（Model）：负责业务对象和数据库的关系映射(ORM)。  
  *T 代表模板 (Template)：负责如何把页面展示给用户(html)。  
  *V 代表视图（View）：负责业务逻辑，并在适当时候调用Model和Template。
  
除了以上三层之外，还需要一个URL分发器，它的作用是将一个个URL的页面请求分发给不同的View处理，View再调用相应的Model和Template，MTV的响应模式如下所示：

    1.Web服务器（中间件）收到一个http请求  
    2.Django在URLconf里查找对应的视图(View)函数来处理http请求  
    3.视图函数调用相应的数据模型来存取数据、调用相应的模板向用户展示页面  
    4.视图函数处理结束后返回一个http的响应给Web服务器  
    5.Web服务器将响应发送给客户端
    
![](https://github.com/fangweiren/leetcode/blob/master/screenshots/MVT.png?raw=true)
