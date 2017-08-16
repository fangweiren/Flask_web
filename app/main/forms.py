#-*- coding=utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(FlaskForm):
	name = StringField('有什么新鲜事想告诉大家?', validators=[Required()])
	submit = SubmitField('发布')

class EditProfileForm(FlaskForm):
	avatar = FileField('自定义头像')
	name = StringField('真实姓名', validators=[Length(0, 64)])
	location = StringField('所在地', validators=[Length(0, 64)])
	about_me = TextAreaField('自我介绍')
	submit = SubmitField('提交')


class EditProfileAdminForm(FlaskForm):
	email = StringField('电子邮箱', validators=[Required(), Length(1,64), Email()])
	username = StringField('用户名', validators=[Required(), Length(1,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, '用户名必须只有字母、数字、点或下划线')])
	confirmed = BooleanField('邮箱验证')
	role = SelectField('用户组', coerce=int)
	name = StringField('真实姓名', validators=[Length(0, 64)])
	location = StringField('所在地', validators=[Length(0, 64)])
	about_me = TextAreaField('自我介绍')
	submit = SubmitField('提交')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_email(self, field):
		if field.data !=self.user.email and User.query.filter_by(email=field.data).first():
			raise ValidationError('该邮箱已被注册。')

	def validate_username(self,field):
		if field.data != self.user.username and User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已被使用')

class PostForm(FlaskForm):
	body = PageDownField("有什么新鲜事想告诉大家?", validators=[Required()])
	submit = SubmitField('发布')


class CommentForm(FlaskForm):
	body = StringField('请输入你的评论', validators=[Required()])
	submit = SubmitField('评论')


class SearchForm(FlaskForm):
	search = StringField('搜索', validators=[Required()])
