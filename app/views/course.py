from flask import Blueprint,render_template,abort,redirect,url_for,request,abort,jsonify
from flask.ext.login import login_required
from app.models import *
from app.forms import ReviewForm
from app import db

course = Blueprint('course',__name__)
QUERY_ORDER = [Course.term.desc(),
        Course.kcid,
        ]

@course.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    term = request.args.get('term',None,type=str)
    course_name = request.args.get('course',None,type=str)
    course_type = request.args.get('type',None,type=str)
    department = request.args.get('dept',None,type=str)
    course_query = Course.query
    if term:
        '''学期'''
        course_query = course_query.filter(Course.term==term)
    if course_name:
        '''课程名'''
        course_query = course_query.filter(Course.name==course_name)
    if course_type:
        '''课程类型'''
        course_query = course_query.filter(Course.course_type==course_type)
    if department:
        '''开课院系'''
        course_query = course_query.filter(Course.dept==department)

    courses_page = course_query.order_by(*QUERY_ORDER).paginate(page,per_page=per_page)
    return render_template('course-index.html',pagination=courses_page)

@course.route('/<int:course_id>/')
def view_course(course_id,course_name=None):
    course = Course.query.get(course_id)
    if not course:
        abort(404)

    related_courses = Course.query.filter_by(name=course_name).all()
    teacher = course.teacher
    reviews = course.reviews.all()
    if teacher:
        same_teacher_courses = teacher.courses
    else:
        same_teacher_courses = None
    return render_template('course.html',
            course=course,
            course_rate = course.course_rate,
            reviews=reviews,
            related_courses=related_courses,
            teacher=teacher,
            same_teacher_courses=same_teacher_courses)

@course.route('/<int:course_id>/upvote/', methods=['POST'])
@login_required
def upvote(course_id):
    course = Course.query.get(course_id)
    if not course or course.upvoted:
        return jsonify(ok=False)
    if course.downvoted:
        course.un_downvote()
    ok = course.upvote()
    return jsonify(ok=ok, count=course.upvote_count)

@course.route('/<int:course_id>/undo-upvote/', methods=['POST'])
@login_required
def undo_upvote(course_id):
    course = Course.query.get(course_id)
    if not course or not course.upvoted:
        return jsonify(ok=False)
    ok = course.un_upvote()
    return jsonify(ok=ok, count=course.upvote_count)

@course.route('/<int:course_id>/downvote/', methods=['POST'])
@login_required
def downvote(course_id):
    course = Course.query.get(course_id)
    if not course or course.downvoted:
        return jsonify(ok=False)
    if course.upvoted:
        course.un_upvote()
    ok = course.downvote()
    return jsonify(ok=ok, count=course.downvote_count)

@course.route('/<int:course_id>/undo-downvote/', methods=['POST'])
@login_required
def undo_downvote(course_id):
    course = Course.query.get(course_id)
    if not course or not course.downvoted:
        return jsonify(ok=False)
    ok = course.un_downvote()
    return jsonify(ok=ok, count=course.downvote_count)

@course.route('/<int:course_id>/follow/', methods=['POST'])
@login_required
def follow(course_id):
    course = Course.query.get(course_id)
    if not course or course.following:
        return jsonify(ok=False)
    ok = course.follow()
    return jsonify(ok=ok, count=course.follow_count)

@course.route('/<int:course_id>/unfollow/', methods=['POST'])
@login_required
def unfollow(course_id):
    course = Course.query.get(course_id)
    if not course or not course.following:
        return jsonify(ok=False)
    ok = course.unfollow()
    return jsonify(ok=ok, count=course.follow_count)

@course.route('/<int:course_id>/join/', methods=['POST'])
@login_required
def join(course_id):
    course = Course.query.get(course_id)
    if not course or course.joined:
        return jsonify(ok=False)
    ok = course.join()
    return jsonify(ok=ok, count=course.join_count)

@course.route('/<int:course_id>/quit/',
methods=['POST'])
@login_required
def quit(course_id):
    course = Course.query.get(course_id)
    if not course or not course.joined:
        return jsonify(ok=False)
    ok = course.quit()
    return jsonify(ok=ok, count=course.join_count)

@course.route('/<int:course_id>/reviews/')
def reviews(course_id, course_name=None):
    course = Course.query.get(course_id)
    if not course:
        abort(404)
    #if course_name != course.name:
    #    return redirect(url_for('.review',course_id=course_id,course_name=course.name))

    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1

    reviews = course.reviews.paginate(page=page, per_page=10)
    if reviews.total:
        str = ''
        for item in reviews.items:
            str += item.content + '<a href=' + url_for('review.edit_review', review_id=item.id) +'>Edit</a><br>'
        return str
    else:
        return 'No reviews'




@course.route('/new/',methods=['GET','POST'])
@course.route('/<int:course_id>/edit/',methods=['GET','POSt'])
def edit_course(course_id=None):
    if course_id:
        course = Course.query.get(course_id)
    else:
        course = Course()
    if not course:
        abort(404)
    course_form = CourseForm(request.form, course)
    if course_form.validate_on_submit():
        course_form.populate_obj(course)
        course = course.save()
        flash('course saved')
        return redirect('.view_course', course_id=course.id, course_name=course.name)
    return render_template('edit-course.html', form=course_form)
