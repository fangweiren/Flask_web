#coding:utf-8
from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash, request, current_app,\
	make_response, g
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, SearchForm
from .. import db
from ..models import Permission, User, Role, Post, Comment
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET','POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(body=form.body.data, author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	show_followed = False
	if current_user.is_authenticated:
		show_followed = bool(request.cookies.get('show_followed', ''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
	posts = pagination.items
	return render_template('index.html', form=form, posts=posts, show_followed=show_followed,\
		pagination=pagination)


@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	page = request.args.get('page', 1, type=int)
	pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
	posts = pagination.items
	return render_template('user.html', user=user, posts=posts, pagination=pagination)



@main.route('/edit-profile', methods=['GET','POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		avatar = request.files['avatar']
		fname = avatar.filename
		UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
		ALLOWED_EXTENSIONS = ['png', 'gif', 'jpeg', 'jpg']
		flag = '.' in fname and fname.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
		if not flag:
			flash('类型错误,图片格式错误')
			return redirect(url_for('.user', username= current_user.username))
		avatar.save('{}{}_{}'.format(UPLOAD_FOLDER, current_user.username, fname))
		current_user.avatar = '/static/avatar/{}_{}'.format(current_user.username, fname)
		db.session.add(current_user)
		flash('个人资料已更新')
		return redirect(url_for('.user', username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('The profile has been updated')
		return redirect(url_for('.user', username=user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
		db.session.add(comment)
		flash('您的评论已发布.')
		return redirect(url_for('.post', id=post.id, page=-1))
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	comments = pagination.items
	return render_template('post.html', posts=[post], form=form, comments=comments,
		pagination=pagination)


@main.route('/sort_by_time/<int:id>', methods=['GET', 'POST'])
@login_required
def sort_by_time(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
		db.session.add(comment)
		flash('您的评论已发布.')
		return redirect(url_for('.sort_by_time', id=post.id, page=-1))
	mark = False
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	comments = pagination.items
	return render_template('post.html', posts=[post], form=form, comments=comments, mark=mark,
		pagination=pagination)


@main.route('/sort_by_likes/<int:id>', methods=['GET', 'POST'])
@login_required
def sort_by_likes(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object    ())
		db.session.add(comment)
		flash('您的评论已发布.')
		return redirect(url_for('.sort_by_likes', id=post.id, page=-1))
	mark = True
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.likes.desc()).paginate(
		page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	comments = pagination.items
	return render_template('post.html', posts=[post], form=form, comments=comments, mark=mark,
		pagination=pagination)


@main.route('/delete/<int:id>')
@login_required
def delete_post(id):
	post = Post.query.get_or_404(id)
	db.session.delete(post)
	flash('文章已删除')
	return redirect(url_for('.index'))


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('微博修改成功.')
		return redirect(url_for('.post', id=post.id))
	form.body.data = post.body
	return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash('YOu are already following this user.')
		return redirect(url_for('.user', username=username))
	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		flash('You are not following this user.')
		return redirect(url_for('.user', username=username))
	current_user.unfollow(user)
	flash('You are not following %s anymore' % username)
	return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
	follows = [{ 'user': item.follower, 'timestamp': item.timestamp}
				for item in pagination.items]
	return render_template('followers.html', user=user,title="Followers of", endpoint='.followers',
							pagination=pagination, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'], error_out=False)
	follows = [{ 'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
	return render_template('followers.html', user=user, title="Followed by", endpoint='.followed_by',
							pagination=pagination, follows=follows)


@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '', max_age=30*24*60*60)
	return resp


@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
	return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,
		per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	comments = pagination.items
	return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/collection/<username>')
@login_required
def show_collection(username):
	user = User.query.filter_by(username=username).first()
	page = request.args.get('page', 1, type=int)
	pagination = user.posts_collect.order_by(Post.timestamp.desc()).paginate(page, 
		per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	collection = pagination.items
	return render_template('collection.html', username=username, posts=collection, pagination=pagination)


@main.route('/collect/<int:id>')
@login_required
def collect_toggle(id):
	page = request.args.get('page', 1, type=int)
	post = Post.query.get_or_404(id)
	current_user.collect_toggle(post)
	return redirect(url_for('.index', id=id, page=page))


@main.route('/like/<username>')
@login_required
def show_like(username):
	user = User.query.filter_by(username=username).first()
	page = request.args.get('page', 1, type=int)
	pagination = user.like_post.order_by(Post.timestamp.desc()).paginate(page,
		per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	likes = pagination.items
	return render_template('like.html', username=username, posts=likes, pagination=pagination)


@main.route('/like/<int:id>')
@login_required
def like_toggle(id):
	page = request.args.get('page', 1, type=int)
	post = Post.query.get_or_404(id)
	current_user.like_toggle(post)
	return redirect(url_for('.index', id=id, page=page))


@main.route('/like-comment/<int:id>')
@login_required
def like_comment_toggle(id):
	page = request.args.get('page', 1, type=int)
	comment = Comment.query.get_or_404(id)
	current_user.dianzan_comment(comment)
	return redirect(url_for('.post', id=comment.post_id, page=page))


@main.route('/shield/<username>')
@login_required
def show_shield(username):
	user = User.query.filter_by(username=username).first()
	page = request.args.get('page', 1, type=int)
	pagination = user.shield_post.paginate(page,
		per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
	shields = pagination.items
	return render_template('shield.html', username=username, posts=shields, pagination=pagination)


@main.route('/shield/<int:id>')
@login_required
def shield_post(id):
	post = Post.query.get_or_404(id)
	current_user.add_shield(post)
	flash('该微博已屏蔽') 
	return redirect(url_for('.index'))

@main.route('/unblock/<int:id>')
@login_required
def unblock_post(id):
	post = Post.query.get_or_404(id)
	current_user.shield_post.remove(post)
	flash('该微博屏蔽已解除')
	return redirect(url_for('.show_shield', username=current_user.username))


@main.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated:
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()


@main.route('/search', methods=['POST'])
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('main.index'))
	return redirect(url_for('main.search_results', query = g.search_form.search.data))


@main.route('/search_results/<query>')
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query).all()
	return render_template('search.html', query=query, posts=results)
