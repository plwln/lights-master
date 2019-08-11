# -*- coding: utf-8 -*-
import os, datetime
from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_from_directory,render_template_string
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from app.models import User, UserRoles, Role, Product, Component, Specification, ModalComponent, Document, Stock
from app.forms import ProductForm, ComponentForm, SpecificationForm, DocumentForm
from datetime import datetime, date, time



@app.route('/')
@login_required
def home_page():
    
    return render_template('index.html')

@app.route('/users_table')
@roles_required('Admin')
def users_table():
    users = User.query.filter(User.username != current_user.username)
    return render_template('table.html', users=users)

@app.route('/role/<user>')
@roles_required('Admin')
def roles_form(user):
    user = User.query.filter(User.username == user).first()
    roles = Role.query.all()
    return render_template('user_roles.html', user=user, roles=roles)

@app.route('/delete_role/<user>/<role>')
@roles_required('Admin')
def delete_role(user, role):
    db_user = User.query.filter(User.username == user).first()
    db_user.delete_role(role)
    return redirect(url_for('roles_form', user=user))

@app.route('/append_role/<user>/<role>')
@roles_required('Admin')
def append_role(user, role):
    db_user = User.query.filter(User.username == user).first()
    db_user.append_role(role)
    return redirect(url_for('roles_form', user=user))


@app.route('/product_table')
@login_required
def product_table():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('product_table.html', products=products)

@app.route('/create_product', methods = ['GET', 'POST'])
@app.route('/clone_product/<cloned_product>', methods = ['GET', 'POST'])
@login_required
def create_product(cloned_product=False):
    form = ProductForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Не заполнены необходимые поля или введены некорректные данные')
            return render_template('create_product.html', form = form)
        else:
            if Product.query.filter(Product.product_name == form.name.data).first() or Product.query.filter(Product.product_item == form.item.data).first():
                flash('Товар с таким именем или артикулом существует')
                return render_template('create_product.html', form = form)  
            else:
                product = Product(form.name.data, form.power.data, form.item.data, form.weight.data, form.materials.data)
                db.session.add(product)
                if cloned_product:
                    cloned_product = Product.query.filter(Product.id==cloned_product).first()
                    specifications = Specification.query.filter(Specification.product_id==cloned_product.id).all()
                    for specification in specifications:
                        cloned_specification = Specification(specification.component_type, product.id, specification.component_id, specification.count)
                        db.session.add(cloned_specification)
                db.session.commit()
                return redirect(url_for('product_specification', product = product.id, det = 'hollow'))
    return render_template('create_product.html', form=form)

@app.route('/product_specification/<product>/<det>', methods = ['GET', 'POST'])
@login_required
def product_specification(product, det):
    modal = ModalComponent.query.first()
    form = SpecificationForm()
    if det == 'hollow':
        component_name = det
    else:
        component_name = Component.query.filter(Component.id==det).first().component_name
    components = Component.query.order_by(Component.component_name).all()
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('product_specification', modal=modal, product=product,component_name=component_name, components=components, specifications=Specification.query.filter(Specification.product_id==product) ))
        # if Specification.query.filter(Specification.product_id == product and Specification.component_id == det).first().component_type == form.component_type.data:
        #     Specification.query.filter(Specification.product_id == product and Specification.component_id == det).first().count+=form.count.data
        #     db.session.commit()
        # else:
        specification = Specification(form.component_type.data, product, det, form.count.data)
        db.session.add(specification)
        db.session.commit()
        return redirect(url_for('product_specification', modal=modal, component_name=component_name, det='hollow', product=product,components=components, specifications=Specification.query.filter(Specification.product_id==product)))
    return render_template('product_specification.html', modal=modal, component_name=component_name,det='hollow', form=form, components=components, specifications=Specification.query.filter(Specification.product_id==product), product=product)

@app.route('/component_table')
@login_required
def component_table():
    modal_component = ModalComponent.query.first()
    components = Component.query.order_by(Component.component_name).all()
    return render_template('component_table.html', components=components, modal_component=modal_component)

@app.route('/create_component', methods = ['GET', 'POST'])
@login_required
def create_component():
    form = ComponentForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Не заполнены необходимые поля или введены некорректные данные')
            return render_template('create_component.html', form = form)
        else:
            if Component.query.filter(Component.component_name == form.name.data).first() or Component.query.filter(Component.component_item == form.item.data).first():
                flash('Товар с таким именем или артикулом существует')
                return render_template('create_component.html', form = form)  
            else:
                component = Component(form.name.data, form.unit.data, form.item.data)
                db.session.add(component)
                db.session.commit()
                return redirect(url_for('create_modal_component',  modal_component = component.id, det = 'hollow'))  
    return render_template('create_component.html', form=form)

@app.route('/product_info/<product>')
@login_required
def product_info(product):
    det = {}
    db_product = Product.query.filter(Product.id==product).first()
    specifications=Specification.query.filter(Specification.product_id==product).all()
    # item = specifications[1].get_children(specifications[1].get_component().id)[0]
    # print(item)
    # print(specifications[1].get_children(item.id))
    #report = get_details_report(specifications, det)
    modal = ModalComponent.query.first()
    return render_template('product_info.html', product=db_product, modal=modal, specifications=specifications)

@app.route('/delete_component/<id>')
@login_required
def delete_component(id):
    Component.delete_component(id)
    return redirect(url_for('component_table'))  

@app.route('/delete_specification/<id>')
@login_required
def delete_specification(id):
    product = Specification.query.filter(Specification.id == id).first().product_id
    Specification.query.filter(Specification.id == id).delete()
    db.session.commit()
    return redirect(url_for('product_specification', product=product, det='hollow'))  

@app.route('/delete_product/<id>')
@login_required
def delete_product(id):
    Product.delete_product(id)
    return redirect(url_for('product_table'))  


@app.route('/create_modal_component/<modal_component>/<det>', methods = ['GET', 'POST'])
@login_required
def create_modal_component(modal_component, det):
    form = SpecificationForm()
    component_name = ''
    if det == 'hollow':
        component_name = det
    else:
        component_name = Component.query.filter(Component.id==det).first().component_name
    modals = [x.id for x in ModalComponent.get_children(modal_component)]
    components = Component.query.filter(Component.id!=modal_component).order_by(Component.component_name).all()
    parents = ModalComponent.get_parents(modal_component)
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('create_modal_component', parents=parents, modals=modals,  modal_component=modal_component,component_name=component_name, components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id==modal_component) ))
        specification = ModalComponent( modal_component, det, form.count.data)
        db.session.add(specification)
        db.session.commit()
        return redirect(url_for('create_modal_component', parents=parents, modals=modals, modal_component=modal_component, det='hollow', component_name=component_name,components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id==modal_component)))
    return render_template('create_modal_component.html', parents=parents, modals=modals, modal_component=modal_component,det='hollow',component_name=component_name, form=form, components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id==modal_component))

@app.route('/delete_modal_component/<id>')
@login_required
def delete_modal_component(id):
    modal_component = ModalComponent.query.filter(ModalComponent.id == id).first().parrent_id
    ModalComponent.query.filter(ModalComponent.id == id).delete()
    db.session.commit()
    return redirect(url_for('create_modal_component', modal_component=modal_component, det='hollow')) 

@app.route('/component_info/<component>')
@login_required
def component_info(component):
    db_component = Component.query.filter(Component.id==component).first()
    specifications=ModalComponent.query.filter(ModalComponent.parrent_id==component)
    return render_template('component_info.html', component=db_component, specifications=specifications)

@app.route('/stock', methods = ['GET', 'POST'])
@login_required
def stock():
    for item in current_user.get_added():
        db.session.delete(item)
        current_user.added.remove(item)
        db.session.commit()
    stock_db = list(set(db.session.query(Stock.component_id).all()))
    stock = []
    print(stock_db)
    for item in stock_db:
        stock.append(Stock.query.filter(Stock.component_id==item[0]).first())
<<<<<<< HEAD
    for item in stock:
        if item.get_component().stock_count is None:
            item.get_count()
=======
    print(stock)
>>>>>>> 080e86274ffcd7ae21113dba7614d5639d6c245b
    form = SpecificationForm()
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('stock', form=form, stock=stock))
        document = Document(datetime.today().strftime("%Y/%m/%d %H:%M"), current_user.id, form.document_type.data, form.text.data)
        db.session.add(document)
        db.session.commit()
<<<<<<< HEAD
        stock = Stock(document.id, form.id.data, form.count.data)
        db.session.add(stock)
        db.session.commit()
        stock.get_count()
=======
        last_count = Stock.query.filter(Stock.component_id==form.id.data).first().get_count()
        stock = Stock(document.id, form.id.data, form.count.data)
        db.session.add(stock)
        db.session.commit()
>>>>>>> 080e86274ffcd7ae21113dba7614d5639d6c245b
        if form.document_type.data=='Приход':
            flash('Приход {} на склад'.format(stock.get_name()), 'message')
        elif form.document_type.data=='Расход':
            if stock.get_count()!=0 and stock.get_count()==last_count:
                flash('Расход детали {} со склада невозможен. Недостаточно деталей'.format(stock.get_name()), 'message')
            else:
                flash('Расход детали {} со склада'.format(stock.get_name()), 'message')
        else:
            flash('Деталь {} списана'.format(stock.get_name()), 'message')
        return redirect(url_for('stock', form=form, stock=stock))
    return render_template('stock.html', form=form, stock=stock)

@app.route('/stock_adding/<doc_type>/<doc>', methods = ['GET', 'POST'])
@login_required
def stock_adding(doc_type, doc):
<<<<<<< HEAD
=======
    all_stock=Stock.query.all()
>>>>>>> 080e86274ffcd7ae21113dba7614d5639d6c245b
    today = datetime.today()
    form = SpecificationForm()
    form1 = DocumentForm()
    modal_component = ModalComponent.query.first()
    last_stocked = Stock.query.first()
    added = current_user.added
    components = Component.query.order_by(Component.component_name).all()
    document = Document(' ', current_user.id, doc_type,' ')
    if doc!='False':
        document= Document.query.filter(Document.id==doc).first()
    db.session.add(document)
    db.session.commit()
    stock_db = list(set(db.session.query(Stock.component_id).all()))
    stock = []
    for item in stock_db:
        stock.append(Stock.query.filter(Stock.component_id==item[0]).first())

    if request.method == 'POST':
        if form.id.data=='comment':
            for item in current_user.get_added():
                item.get_document().date=today.strftime("%Y/%m/%d %H:%M")
                item.get_document().comment=form1.text.data
                db.session.commit()
                current_user.added.remove(item)
<<<<<<< HEAD
                item.get_count()
=======
>>>>>>> 080e86274ffcd7ae21113dba7614d5639d6c245b
                db.session.commit()
            flash('Склад обновлён', 'message')
        else:
            if form.count.data is None:
                flash('Используйте "." вместо ","')
                return redirect(url_for('stock_adding', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added = added, last_stocked = last_stocked, form = form, component = components, modal_component=modal_component ))
            print(document.id)
            stock = Stock(document.id, form.id.data, form.count.data)
            
            db.session.add(stock)
            db.session.commit()
            current_user.append_stock(stock.id)
            flash('Деталь {} добавлена в список'.format(stock.get_name()), 'message')
        return redirect(url_for('stock_adding', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added = added, form = form, last_stocked = last_stocked,  component = components, modal_component=modal_component))
    
    return render_template('stock_adding.html', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added = added, form = form, last_stocked = last_stocked,  components = components, modal_component=modal_component)


@app.route('/document/<component_id>')
@login_required
def document(component_id):
    form = SpecificationForm()
    stocks = Stock.query.filter(Stock.component_id==component_id).all()
    documents = [Document.query.filter(Document.id==stock.document_id).first() for stock in stocks]
    return render_template('document.html', form=form, stocks = stocks, documents = documents)

@app.route('/delete_document/<document_id>')
@login_required
<<<<<<< HEAD
def delete_document(document_id):
    stock = Stock.query.filter(Stock.document_id==document_id)
    component_id = stock.first().component_id
    stock.delete()
    db.session.commit()
    Stock.query.filter(Stock.component_id==component_id).first().get_count()
=======
def delete_document(id):
    document = Document.query.filter(Document.id==id).first()
    stock = Stock.query.filter(Stock.document_id==Document.id).first()
    component_id = stock.component_id
    document.delete()
    stock.delete()
    db.session.commit()
>>>>>>> 080e86274ffcd7ae21113dba7614d5639d6c245b
    return redirect(url_for('document', component_id = component_id))

@app.route('/fork/<doc_type>')
@login_required
def fork(doc_type):
    for item in current_user.get_added():
        db.session.delete(item)
        current_user.added.remove(item)
        db.session.commit()
    return redirect(url_for('stock_adding', doc_type=doc_type, doc='False'))

@app.route('/delete_stock/<stock_id>/<doc_id>')
@login_required
def delete_stock(stock_id, doc_id):
    current_user.delete_stock(stock_id)
    doc = Document.query.filter(Document.id==doc_id).first()
    return redirect(url_for('stock_adding', doc_type=doc.document_type, doc=doc.id))


@app.route('/remove_stock/<component_id>')
@login_required
def remove_stock(component_id, comment):
    document = Document(datetime.utcnow(), current_user.id, 'Cписание', comment)
    db.session.add(document)
    db.session.commit()
    stock = Stock(document.id, component_id, 0)
    db.session.add(stock)
    db.session.commit()
    return redirect(url_for('stock'))


def get_details_report(spec,det, count=1):
    component_name = ''

    for item in spec:
        if type(item)==Specification: 
            item_id = item.component_id
        else: item_id = item.child_id
        if item.get_children(item_id):
            count *= item.count
            get_details_report(ModalComponent.query.filter(ModalComponent.parrent_id==item_id).all(),det, count)
            
        else:
            if type(item)==Specification: 
                component_name = Component.query.filter(Component.id==item.component_id).first().component_name
                if component_name in det.keys():
                    det[component_name] += item.count
            else:
                component_name = Component.query.filter(Component.id==item.child_id).first().component_name
                if component_name in det.keys():
                    det[component_name] += item.count*count
            if component_name not in det.keys() and component_name!='':
                det[component_name] = item.count*count

        
        
    return det

# def rec_html(specification):
#     for item in specification.get_children(specification.get_component().id):
#         html = "<tr><td ><span style='margin-left: 10px;'>{{item.component_name}}</span></td><td ><span style='margin-left: 10px;'>{{item.component_unit}}</span></td><td ><span style='margin-left: 10px;'>{{item.get_count(specification.get_component().id)}}</span></td></tr>"
#         if specification.get_children(item.id)!=[]:
#             rec_html(specification.get_children(item.id))