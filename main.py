from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import math


with open('config.json', 'r') as f:
    param = json.load(f)['params']

local_server=True
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = param['gmail-user'],
    MAIL_PASSWORD = param['gmail-pass']
)

mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['prod_url']

db = SQLAlchemy(app)

class Contact(db.Model):
    ''' sno, name, email, phone_no, date, mes, '''
    snp = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    phone_num = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    mes = db.Column(db.String, nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    last_edit_date = db.Column(db.String, nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    img_file = db.Column(db.String(50), nullable=False)

@app.route('/')
def home():
    #pagination logic
    posts = Posts.query.filter_by().all()
    # [0:param['no_of_post']]
    last = math.ceil(len(posts)/int(param['no_of_post']))
    print(last)

    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1;
    page = int(page)

    posts = posts[(page-1)*int(param['no_of_post']):(page-1)*int(param['no_of_post'])+int(param['no_of_post'])]

    if(page==1 and page==last):
        prev='#'
        next='#'
    elif(page==1):
        prev = '#'
        next = '/?page='+str(page+1)
    elif(page==last):
        prev = '/?page='+str(page-1)
        next = '#'
    else:
        prev = '/?page='+str(page-1)
        next = '/?page='+str(page+1)

    return render_template('index.html', params=param, posts=posts, next=next, prev =prev)

@app.route('/dashboard', methods=['GET','POST'])
def dashbaord():
    if ('user' in session and session['user'] == param['admin_id']):
        posts = Posts.query.all()
        return render_template('adminpanel.html', params=param, posts= posts)

    if request.method=='POST':
        uname = request.form.get('uname')
        pswd = request.form.get('upass')
        if(uname==param['admin_id'] and pswd==param['admin_pass']):
            # set the session variable
            posts = Posts.query.all()
            session['user'] = uname
            return render_template('adminpanel.html', params=param, posts=posts)
    return render_template('dashboard.html', params=param)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/edit/<string:sno>/', methods=['GET','POST'])
def edit(sno):
    # post = Posts.query.filter_by(sno=sno).first()
    if ('user' in session and session['user'] == param['admin_id']):
        if request.method=='POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if sno=='0':
                addPost = Posts(title=title, slug=slug,content=content, img_file=img_file, date=datetime.now(), last_edit_date = datetime.now())
                db.session.add(addPost)
                db.session.commit()     
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.slug=slug
                post.content = content
                post.img_file = img_file
                post.last_edit_date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+sno)
        post=Posts.query.filter_by(sno=sno).first()    
        return render_template('edit.html', params=param, post=post)
    
    return redirect('/dashboard')

@app.route('/delete/<string:sno>', methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == param['admin_id']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/about')
def about():
    return render_template('about.html',  params=param)


@app.route('/blog')
def blog():
    return render_template('blog.html',  params=param)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        # Add entry to database table.
        name = request.form.get('name')
        email = request.form.get('email')
        phn = request.form.get('phone')
        msg = request.form.get('msg')
        values = Contact(name=name, email=email, phone_num=phn, date= datetime.now() ,mes=msg)
        db.session.add(values)
        db.session.commit()
        mail.send_message(
            name+" - A Message from Shubham Blog's",
            sender=email,
            recipients=[param['gmail-user']],
            body="\n"+msg +"\n\n"+ "Regards" +"\n"+name+"\n"+email+"\n"+phn
        )

    return render_template('contact.html',  params=param)


@app.route("/post/<string:postslug>", methods=['GET'])
def post_route(postslug):
    # slug2 = str(postslug)
    post = Posts.query.filter_by(slug = postslug).first()
    return render_template('post.html', params=param, post = post)

app.run()