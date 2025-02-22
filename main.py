from flask import Flask, abort, render_template, redirect, url_for, flash, request,session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from sqlalchemy import Integer, String, Float,ForeignKey
from flask_bootstrap import Bootstrap5
from forms import contactForm, registerForm, loginForm, addForm
from email_class import mail
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import stripe
from dotenv import load_dotenv
import os


# CONFIG -------------------
load_dotenv()
app = Flask(__name__)
Bootstrap5(app)
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')


ckeditor = CKEditor(app)


stripe.api_key = os.getenv('api_key')
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# DB Tables
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    sales = relationship("infoSales", back_populates="own_person")

class Product(db.Model):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float())
    name: Mapped[str] = mapped_column(String(1000), unique=True)
    img: Mapped[str] = mapped_column(String(1000), unique=True)
    content: Mapped[str] = mapped_column(String(10000), unique=True)

class infoSales(db.Model):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    own_person = relationship("User", back_populates="sales")
    products = mapped_column(String(1000))



with app.app_context():
    db.create_all()  



# ROUTING -------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')
@app.route('/about-us')
def about_us():
    return render_template('about_us.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    contact_form = contactForm()
    if contact_form.validate_on_submit():
        mail_user = contact_form.email.data
        name_user = contact_form.name.data
        body_user = contact_form.body.data
        subject_user = contact_form.subject.data
        email = mail()
        email.send_message(mail_user, subject_user, body_user, name_user)
        flash('The message was successfully sent')
    return render_template('contact.html', form=contact_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = loginForm()
    if form_login.validate_on_submit():
        email = form_login.email.data
        password = form_login.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            flash('Email doesn\'t exist, please try again.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form_login, current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = registerForm()
    if register_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == register_form.email.data)).scalar()
        if not user:
            hash_and_salted = generate_password_hash(register_form.password.data, method="pbkdf2:sha256", salt_length=8)
            new_user = User(email=register_form.email.data, name=register_form.username.data, password=hash_and_salted)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
    return render_template('register.html', form=register_form)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower().strip()
    dic = {'rat': 'rat-poison', 'cockroaches': 'Cockroaches'}

    if query not in dic:
        flash('Not Found, try to write it correctly.')
        return redirect(url_for('home')) 
    return redirect(url_for('products', category=dic[query]))

@app.route('/products/<string:category>')
def products(category):
    items = db.session.execute(db.select(Product).where(Product.category == category)).scalars()
    return render_template('products.html', data=items)

@app.route('/skip/<int:id>')
def skip(id):
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('products')) 
    
    product = db.get_or_404(Product, id)
    
    new_cart = []
    for item in session['cart']:
        if item.get('id') == id:
            if item.get('quantity', 1) > 1:
                item['quantity'] -= 1
                new_cart.append(item)
        else:
            new_cart.append(item) 

    session['cart'] = new_cart
    session['total_price'] = sum(item['price'] * item['quantity'] for item in new_cart) if new_cart else 0.0
    session.modified = True

    return redirect(url_for('products', category=product.category))

@app.route('/description/<int:id>')
def description(id):
    product = db.get_or_404(Product, id)
    return render_template('description.html',item=product)

@app.route('/purchase/<int:id>')
def purchase(id):

    product = db.get_or_404(Product, id)
    if "cart" not in session:
        session['cart'] = []
    cart = session['cart']
    for item in cart:
        if item['id'] == product.id:
            item['quantity'] += 1
            break
    else:
        cart.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': 1
        })
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    session['total_price'] = total_price
    return redirect(url_for("products", category=product.category)) 

# ADMIN POWERS
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/add', methods=['GET', 'POST'])
@admin_only
def add():
    form_add = addForm()
    if form_add.validate_on_submit():
        new_publi = Product(category=form_add.category.data,
                            price=form_add.price.data,
                            name=form_add.name.data,
                            img=form_add.img.data,
                            content=form_add.description.data)
        existing_product = db.session.execute(db.select(Product).where(Product.name == new_publi.name)).scalar()
        if not existing_product:
            db.session.add(new_publi)
            db.session.commit()
            flash("The publication was successfully created.")
            return redirect(url_for('products', category=form_add.category.data))
        else:
            flash("The product already exists.")
    return render_template('add.html', form=form_add)

@app.route('/delete/<int:id>', methods=['POST'])
@admin_only
def delete(id):
    if request.method == "POST":
        publi = db.session.execute(db.select(Product).where(Product.id == id)).scalar()
        category = publi.category
        db.session.delete(publi)
        db.session.commit()
        return redirect(url_for('products', category=category))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_only
def edit(id):
    product = db.get_or_404(Product, id)
    edit_product = addForm(
        category=product.category,
        price=product.price,
        name=product.name,
        img=product.img,
        description=product.content
    )
    if edit_product.validate_on_submit():
        product.name = edit_product.name.data
        product.category = edit_product.category.data
        product.img = edit_product.img.data
        product.price = edit_product.price.data
        db.session.commit()
        return redirect(url_for('products', category=product.category))
    return render_template('add.html', form=edit_product)

# PAYMENT PROCCESSING
YOUR_DOMAIN = "http://127.0.0.1:4242"

@app.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == 'paid':
        products_in_cart = str(session.get('cart', []))  
        new_sale = infoSales(person_id=current_user.id, products=products_in_cart)
        db.session.add(new_sale)
        db.session.commit()
        total_price=0
        for item in session['cart']:
            total_price += item['price'] * item['quantity']
        send_confirmation_email(current_user.email, session['cart'], total_price)

        session.pop('cart', None)
        session.pop('total_price', None)

        return render_template('success.html')
    else:
        return redirect(url_for('cancel'))

@app.route('/cancel')
@login_required
def cancel():
    flash("Payment canceled. Please try again.")
    return render_template('cancel.html')

@csrf.exempt
@login_required
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    if 'cart' not in session or not session['cart']:
        flash("Tu carrito está vacío.")
        return redirect(url_for("home"))
    
    try:
        total_price = 0
        line_items = []
        for item in session['cart']:
            line_items.append({
                'price_data': {
                    'currency': 'ars',
                    'product_data': {
                        'name': item['name'],
                    },
                    'unit_amount': int(item['price'] * 100),
                },
                'quantity': item['quantity'],
            })
            total_price += item['price'] * item['quantity']
        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )        
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e), 500

# server mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

def send_confirmation_email(user_email, cart, total_price):
    subject = "Confirmation of your products"
    body = f"Hello,\n\nThank you for your purchase. Here are the details of your order:\n\n"
    
    for item in cart:
        body += f"- {item['name']} x {item['quantity']} - ${item['price'] * item['quantity']}\n"

    body += f"\nTotal: ${total_price}\n\nThank you for shopping with us!"
    msg = Message(subject, recipients=[user_email])
    msg.body = body
    mail.send(msg)

if __name__ == "__main__":
    app.run(debug=True,port=4242)
