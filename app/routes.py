# -*- coding: utf-8 -*-
import os
import datetime
import json
from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_from_directory, render_template_string, jsonify
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from app.models import User, UserRoles, Role, Product, Component, Specification, ModalComponent, Document, Stock, Order, Note, Shop, ComponentShop
from app.forms import ProductForm, ComponentForm, SpecificationForm, DocumentForm, SubmitForm, NoteForm
from datetime import datetime, date, time
import datetime as dt
from jinja2 import Environment, BaseLoader, Template
import math
from asyncio import Queue
import asyncio
import threading
import time
from multiprocessing.dummy import Pool as ThreadPool


def delete_old_stocks(items):
    print(items)
    for item in items:
        for each in item:
            component_id = each.component_id
            Stock.query.filter(Stock.id == each.id).delete()
            each_stock = Stock.query.filter(
                component_id == Stock.component_id).first()
            if each_stock:
                each_stock.get_count()
        db.session.commit()


@app.route('/update_thread', methods=['POST'])
def update_thread():
    start_time = time.time()
    orders = Document.query.filter(Document.product_orders).filter(
        Document.order_item).all()[::-1]
    docs = [x.id for x in orders if x.order_status!='выполнен']
    cnt = 0
    print(len(docs))
    count = len(docs)//2
    if count == 1:
        count = 2
    if count == 0:
        count = 1
    if count > 5:
        count = 5
    pool = ThreadPool(count)
    pool.map(order_processor, docs)
    pool.close()
    pool.join()
    print("--- %s seconds ---" % (time.time() - start_time))
    return jsonify({'card': render_template('all_orders_in_process.html',  orders=orders, roles=[x.name for x in current_user.roles]),
                'table': render_template('all_table_order_in_process.html',  orders=orders, roles=[x.name for x in current_user.roles])})


@app.route('/get_count_all')
@login_required
def get_count_all():
    for stck in Stock.query.all():
        stck.get_count()

@app.route('/')
@login_required
def home_page():
    # for order in Order.query.all():
    #     Order.query.filter(Order.id==order.id).delete()
    #     db.session.commit()
    # for item in Stock.query.all():
    #     if item.component_id is None and item.id_product is None:
    # #         Stock.query.filter(Stock.id==stock.id).delete()
    # Stock.query.filter(Stock.component_id==' ').delete()
    # db.session.commit()
    # for note in Note.query.all():
    #     Note.query.delete()
    #     db.session.commit()
    # for doc in Document.query.all():
    #     if doc.document_type == 'Резерв':
    #         db.session.delete(doc)
    #         db.session.commit()
    # for name in ['Склад', 'Снабжение', 'Продажники', 'Производство', 'Технолог']:
    #     role = Role()
    #     db.session.add(role)
    #     db.session.commit()
    #     role.name = name
    #     db.session.commit()
    roles = [x.name for x in current_user.roles]
    docs = [Document.query.filter(Document.id == x.doc_id).first(
    ) for x in list(set(db.session.query(Order).filter(Order.doc_id).all()))]
    return render_template('index.html', orders=sorted(docs, key=lambda x: x.id)[::-1], roles=roles)


@app.route('/users_table')
@roles_required('Admin')
def users_table():
    # for c in Component.query.filter(Component.unfired is not None).all():
    #     c.unfired = 0
    #     db.session.commit()
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
    roles = [x.name for x in current_user.roles]
    products = Product.query.order_by(Product.product_name).all()
    return render_template('product_table.html', roles=roles, products=products)


@app.route('/create_product', methods=['GET', 'POST'])
@app.route('/clone_product/<cloned_product>', methods=['GET', 'POST'])
@login_required
def create_product(cloned_product=False):
    form = ProductForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Не заполнены необходимые поля или введены некорректные данные')
            return render_template('create_product.html', form=form)
        else:
            if Product.query.filter(Product.product_name == form.name.data).first() or Product.query.filter(Product.product_item == form.item.data).first():
                flash('Товар с таким именем или артикулом существует')
                return render_template('create_product.html', form=form)
            else:
                product = Product(form.name.data, form.power.data,
                                  form.item.data, form.weight.data, form.materials.data)
                db.session.add(product)
                if cloned_product:
                    cloned_product = Product.query.filter(
                        Product.id == cloned_product).first()
                    specifications = Specification.query.filter(
                        Specification.product_id == cloned_product.id).all()
                    for specification in specifications:
                        cloned_specification = Specification(
                            specification.component_type, product.id, specification.component_id, specification.count)
                        db.session.add(cloned_specification)
                db.session.commit()
                return redirect(url_for('product_specification', product=product.id, det='hollow'))
    return render_template('create_product.html', form=form)


@app.route('/product_specification/<product>/<det>', methods=['GET', 'POST'])
@login_required
def product_specification(product, det):
    modal = ModalComponent.query.first()
    form = SpecificationForm()
    if det == 'hollow':
        component_name = det
    else:
        component_name = Component.query.filter(
            Component.id == det).first().component_name
    components = Component.query.order_by(Component.component_name).all()
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('product_specification', modal=modal, product=product, component_name=component_name, components=components, specifications=Specification.query.filter(Specification.product_id == product)))
        # if Specification.query.filter(Specification.product_id == product and Specification.component_id == det).first().component_type == form.component_type.data:
        #     Specification.query.filter(Specification.product_id == product and Specification.component_id == det).first().count+=form.count.data
        #     db.session.commit()
        # else:
        specification = Specification(
            form.component_type.data, product, det, form.count.data)
        db.session.add(specification)
        db.session.commit()
        return redirect(url_for('product_specification', modal=modal, component_name=component_name, det='hollow', product=product, components=components, specifications=Specification.query.filter(Specification.product_id == product)))
    return render_template('product_specification.html', modal=modal, component_name=component_name, det='hollow', form=form, components=components, specifications=Specification.query.filter(Specification.product_id == product), product=product)


@app.route('/component_table')
@login_required
def component_table():
    roles = [x.name for x in current_user.roles]
    modal_component = ModalComponent.query.first()
    components = Component.query.order_by(Component.component_name).all()
    return render_template('component_table.html', roles=roles, components=components, modal_component=modal_component)


@app.route('/create_component', methods=['GET', 'POST'])
@app.route('/create_component/<cloned_component>', methods=['GET', 'POST'])
@login_required
def create_component(cloned_component=False):
    form = ComponentForm()
    if request.method == 'POST':
        if form.validate() == False:
            flash('Не заполнены необходимые поля или введены некорректные данные')
            return render_template('create_component.html', form=form)
        else:
            if Component.query.filter(Component.component_name == form.name.data).first() or Component.query.filter(Component.component_item == form.item.data).first():
                flash('Товар с таким именем или артикулом существует')
                return render_template('create_component.html', form=form)
            else:
                component = Component(
                    form.name.data, form.unit.data, form.item.data)
                db.session.add(component)
                db.session.commit()
                if cloned_component:
                    cloned_component = Component.query.filter(
                        Component.id == cloned_component).first()
                    modal_components = ModalComponent.query.filter(
                        ModalComponent.parrent_id == cloned_component.id).all()
                    for modal_component in modal_components:
                        cloned_modal = ModalComponent(
                            component.id, modal_component.child_id, modal_component.count)
                        db.session.add(cloned_modal)
                    db.session.commit()
                return redirect(url_for('create_modal_component',  modal_component=component.id, det='hollow'))
    return render_template('create_component.html', form=form)


@app.route('/product_info/<product>')
@login_required
def product_info(product):
    roles = [x.name for x in current_user.roles]
    db_product = Product.query.filter(Product.id == product).first()
    specifications = Specification.query.filter(
        Specification.product_id == product).all()
    spec_dict = [[], [], [], [], [], []]

    def rec(specifications, c_type, ret_dict, count=1, parrent=None, tab='--'):
        for specification in specifications:
            if type(specification) == Specification:
                if specification.component_type == c_type:
                    ret_dict.append(f''' <tr>
                    <td scope="row">{specification.get_component().component_name}</td>
                    <td>{specification.get_component().component_unit}</td>
                    <td>{specification.count}</td>
                    </tr>''')
                    if specification.get_children(specification.get_component().id):
                        rec(specification.get_children(specification.get_component(
                        ).id), c_type, ret_dict, specification.count, specification.get_component().id, tab)
            else:
                ret_dict.append(f'''<tr>
                                    <td scope="row">{tab}{specification.component_name}</td>
                                    <td>{specification.component_unit}</td>
                                    <td>{specification.get_count(parrent)*count}</td>
                                    </tr>''')
                if ModalComponent.get_children(specification.id):
                    minus = tab+tab
                    rec(ModalComponent.get_children(specification.id), c_type, ret_dict,
                        specification.get_count(parrent)*count, specification.id, minus)
    i = 0
    tmps = []
    for det_type in ('Детали корпуса', 'Электротехнические детали', 'Герметики', 'Метизы', 'Упаковка', 'Расходные материалы'):
        rec(specifications, det_type, spec_dict[i])
        tmp_string = ''
        tmp_string = ' '.join(spec_dict[i])
        rtemplate = Template(tmp_string).render()
        tmps.append(rtemplate)
        i += 1
    modal = ModalComponent.query.first()
    return render_template('product_info.html', spec_dict=tmps, roles=roles, product=db_product, modal=modal, specifications=specifications)


@app.route('/delete_component/<id>')
@login_required
def delete_component(id):
    Component.delete_component(id)
    return redirect(url_for('component_table'))


@app.route('/delete_specification/<id>')
@login_required
def delete_specification(id):
    product = Specification.query.filter(
        Specification.id == id).first().product_id
    Specification.query.filter(Specification.id == id).delete()
    db.session.commit()
    return redirect(url_for('product_specification', product=product, det='hollow'))


@app.route('/delete_product/<id>')
@login_required
def delete_product(id):
    Product.delete_product(id)
    return redirect(url_for('product_table'))


@app.route('/create_modal_component/<modal_component>/<det>', methods=['GET', 'POST'])
@login_required
def create_modal_component(modal_component, det):
    form = SpecificationForm()
    component_name = ''
    if det == 'hollow':
        component_name = det
    else:
        component_name = Component.query.filter(
            Component.id == det).first().component_name
    modals = [x.id for x in ModalComponent.get_children(modal_component)]
    components = Component.query.filter(
        Component.id != modal_component).order_by(Component.component_name).all()
    parents = ModalComponent.get_parents(modal_component)
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('create_modal_component', parents=parents, modals=modals,  modal_component=modal_component, component_name=component_name, components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id == modal_component)))
        specification = ModalComponent(modal_component, det, form.count.data)
        db.session.add(specification)
        db.session.commit()
        return redirect(url_for('create_modal_component', parents=parents, modals=modals, modal_component=modal_component, det='hollow', component_name=component_name, components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id == modal_component)))
    return render_template('create_modal_component.html', parents=parents, modals=modals, modal_component=modal_component, det='hollow', component_name=component_name, form=form, components=components, specifications=ModalComponent.query.filter(ModalComponent.parrent_id == modal_component))


@app.route('/delete_modal_component/<id>')
@login_required
def delete_modal_component(id):
    modal_component = ModalComponent.query.filter(
        ModalComponent.id == id).first().parrent_id
    ModalComponent.query.filter(ModalComponent.id == id).delete()
    db.session.commit()
    return redirect(url_for('create_modal_component', modal_component=modal_component, det='hollow'))


@app.route('/component_info/<component>')
@login_required
def component_info(component):
    roles = [x.name for x in current_user.roles]
    db_component = Component.query.filter(Component.id == component).first()
    specifications = ModalComponent.query.filter(
        ModalComponent.parrent_id == component)
    return render_template('component_info.html', roles=roles, component=db_component, specifications=specifications)


@app.route('/stock', methods=['GET', 'POST'])
@login_required
def stock():
    roles = [x.name for x in current_user.roles]
    current_user.added = []
    for item in current_user.get_added():
        db.session.delete(item)
        current_user.added.remove(item)
        db.session.commit()
    stock_db = list(set(db.session.query(Stock.component_id).all()))
    stock = []
    for item in stock_db:
        if item[0] is not None:
            stock.append(Stock.query.filter(
                Stock.component_id == item[0]).first())
    for item in stock:
        if item.get_component() is not None and item.get_component().stock_count is None:
            item.get_count()
    form = SpecificationForm()
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('stock', form=form, stock=stock))
        document = Document(datetime.today().strftime(
            "%Y/%m/%d %H:%M"), current_user.id, form.document_type.data, form.text.data)
        db.session.add(document)
        db.session.commit()
        stock = Stock(document.id, None, form.id.data, form.count.data)
        db.session.add(stock)
        db.session.commit()
        compon = Component.query.filter(
            Component.id == stock.component_id).first()
        last_count = compon.stock_count
        stock.get_count()
        if form.document_type.data == 'Приход':
            stck = db.session.query(Stock, Document).filter(Stock.document_id==Document.id).filter(Stock.component_id==form.id.data)
            stck = stck.filter(Document.order_status is not None).all()
            for s in stck:
                if s[0].workflow_count:
                    if s[0].workflow_count<s[0].count:
                        s[0].workflow_count+=1
                        db.session.commit()
                        break
                    else:
                        continue
                else:
                    s[0].workflow_count=1
                    db.session.commit()


            note = Note.query.filter(
                Note.na_component == stock.component_id).first()
            if note:
                n_count = note.n_count
                stck_count = stock.get_component().stock_count
                count = n_count-stck_count
                if count <= 0:
                    Note.query.filter(Note.na_component ==
                                      stock.component_id).delete()
                    db.session.commit()
                else:
                    note.n_stock = count
                    db.session.commit
            flash('Приход {} на склад'.format(stock.get_name()), 'message')
        elif document.document_type == 'Расход':
                stck = db.session.query(Stock, Document).filter(Stock.document_id==Document.id).filter(Stock.component_id==form.id.data)
                stck = stck.filter(Document.order_status is not None).all()
                cmpnt = stock.get_component()
                docs = set([x[1].id for x in stck])
                print(docs)
                d_count = cmpnt.stock_count-stock.count
                if cmpnt.unfired>=d_count:
                    count = len(docs)//2
                    if count == 1:
                        count = 2
                    if count == 0:
                        count = 1
                    if count > 5:
                        count = 5
                    pool = ThreadPool(count)
                    pool.map(order_processor, docs)
                    pool.close()
                    pool.join()
                if compon.stock_count != 0 and compon.stock_count == last_count:
                    flash('Расход детали {} со склада невозможен. Недостаточно деталей'.format(
                        stock.get_name()), 'message')
                else:
                    flash('Расход детали {} со склада'.format(
                        stock.get_name()), 'message')
        else:
            flash('Деталь {} списана'.format(stock.get_name()), 'message')
        return redirect(url_for('stock', form=form, stock=stock, roles=roles))
    return render_template('stock.html', form=form, stock=stock, roles=roles)


@app.route('/stock_adding/<doc_type>/<doc>', methods=['GET', 'POST'])
@login_required
def stock_adding(doc_type, doc):
    today = datetime.today()
    form = SpecificationForm()
    form1 = DocumentForm()
    modal_component = ModalComponent.query.first()
    last_stocked = Stock.query.first()
    added = current_user.added
    components = Component.query.order_by(Component.component_name).all()
    document = Document(' ', current_user.id, doc_type, ' ')
    if doc != 'False':
        document = Document.query.filter(Document.id == doc).first()
    db.session.add(document)
    db.session.commit()
    stock_db = list(set(db.session.query(Stock.component_id).all()))
    stock = []
    for item in stock_db:
        stock.append(Stock.query.filter(Stock.component_id == item[0]).first())

    if request.method == 'POST':
        if form.id.data == 'comment':
            for item in current_user.get_added():
                item.get_document().date = today.strftime("%Y/%m/%d %H:%M")
                item.get_document().comment = form1.text.data
                db.session.commit()
                current_user.added.remove(item)
                item.get_count()
                db.session.commit()
            flash('Склад обновлён', 'message')
        else:
            if form.count.data is None:
                flash('Используйте "." вместо ","')
                return redirect(url_for('stock_adding', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added=added, last_stocked=last_stocked, form=form, component=components, modal_component=modal_component))
            stock = Stock(document.id, None, form.id.data, form.count.data)
            db.session.add(stock)
            db.session.commit()
            current_user.append_stock(stock.id)
            stock.get_count()
            if document.document_type == 'Расход':
                stck = db.session.query(Stock, Document).filter(Stock.document_id==Document.id).filter(Stock.component_id==form.id.data)
                stck = stck.filter(Document.order_status is not None).all()
                cmpnt = stock.get_component()
                docs = set([x[1].id for x in stck])
                print(docs)
                d_count = cmpnt.stock_count-stock.count
                if cmpnt.unfired>=d_count:
                    print('tut')
                    count = len(docs)//2
                    if count == 1:
                        count = 2
                    if count == 0:
                        count = 1
                    if count > 5:
                        count = 5
                    pool = ThreadPool(count)
                    pool.map(order_processor, docs)
                    pool.close()
                    pool.join()
            flash('Деталь {} добавлена в список'.format(
                stock.get_name()), 'message')
        return redirect(url_for('stock_adding', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added=added, form=form, last_stocked=last_stocked,  component=components, modal_component=modal_component))

    return render_template('stock_adding.html', doc=doc, doc_type=doc_type, stock=stock, form1=form1, added=added, form=form, last_stocked=last_stocked,  components=components, modal_component=modal_component)


@app.route('/stock_product', methods=['GET', 'POST'])
@login_required
def stock_product():
    roles = [x.name for x in current_user.roles]
    for item in current_user.get_added():
        current_user.added.remove(item)
        db.session.delete(item)
        db.session.commit()
    stock_db = list(set(db.session.query(Stock.id_product).all()))
    stock = []
    for item in stock_db:
        if item[0] is not None:
            stock.append(Stock.query.filter(
                Stock.id_product == item[0]).first())

    for item in stock:
        if item.get_product() is not None and item.get_product().pstock_count is None:
            item.get_count()
    form = SpecificationForm()
    if request.method == 'POST':
        if form.count.data is None:
            flash('Используйте "." вместо ","')
            return redirect(url_for('stock', form=form, stock=stock))
        document = Document(datetime.today().strftime(
            "%Y/%m/%d %H:%M"), current_user.id, form.document_type.data, form.text.data)
        db.session.add(document)
        db.session.commit()
        stock = Stock(document.id, form.id.data, None, form.count.data)
        db.session.add(stock)
        db.session.commit()
        prod = Product.query.filter(Product.id == stock.id_product).first()
        last_count = prod.pstock_count
        stock.get_count()
        if form.document_type.data == 'Приход':
            flash('Приход {} на склад'.format(stock.get_name()), 'message')
            note = Note.query.filter(
                Note.na_product == stock.id_product).first()
            if note:
                count = Note.n_count-stock.get_product().pstock_count
                if count <= 0:
                    Note.query.filter(Note.na_product ==
                                      stock.id_product).delete()
                    db.session.commit()
                else:
                    note.n_stock = count
                    db.session.commit
        elif form.document_type.data == 'Расход':
            if prod.pstock_count != 0 and prod.pstock_count == last_count:
                flash('Расход детали {} со склада невозможен. Недостаточно деталей'.format(
                    stock.get_name()), 'message')
            else:
                flash('Расход детали {} со склада'.format(
                    stock.get_name()), 'message')
        else:
            flash('Деталь {} списана'.format(stock.get_name()), 'message')
        return redirect(url_for('stock_product', form=form, stock=stock, roles=roles))
    return render_template('product_stock.html', form=form, stock=stock, roles=roles)


@app.route('/pstock_adding/<doc_type>/<doc>', methods=['GET', 'POST'])
@login_required
def pstock_adding(doc_type, doc):
    today = datetime.today()
    form = SpecificationForm()
    form1 = DocumentForm()
    products = Product.query.order_by(Product.product_name).all()
    document = Document(' ', current_user.id, doc_type, ' ')
    if doc != 'False':
        document = Document.query.filter(Document.id == doc).first()
    db.session.add(document)
    db.session.commit()
    stock_db = list(set(db.session.query(Stock.id_product).all()))
    stock = []
    for item in stock_db:
        if item[0] is not None:
            stock.append(Stock.query.filter(
                Stock.id_product == item[0]).first())

    if request.method == 'POST':
        if form.id.data == 'comment':
            for item in current_user.get_added():
                item.get_document().date = today.strftime("%Y/%m/%d %H:%M")
                item.get_document().comment = form1.text.data
                db.session.commit()
                current_user.added.remove(item)
                item.get_count()
                db.session.commit()
            flash('Склад обновлён', 'message')
        else:
            if form.count.data is None:
                flash('Используйте "." вместо ","')
            stock = Stock(document.id, form.id.data, None, form.count.data)

            db.session.add(stock)
            db.session.commit()
            current_user.append_stock(stock.id)
            flash('Товар {} добавлен в список'.format(
                stock.get_name()), 'message')
        return redirect(url_for('pstock_adding', doc=doc, doc_type=doc_type, stock=stock, form1=form1, form=form, products=products))

    return render_template('pstock_adding.html', doc=doc, doc_type=doc_type, stock=stock, form1=form1, form=form, products=products)


@app.route('/document/<component_id>')
@login_required
def document(component_id):
    form = SpecificationForm()
    stocks = Stock.query.filter(Stock.component_id == component_id).all()
    print(stocks)
    documents = [Document.query.filter(
        Document.id == stock.document_id).first() for stock in stocks]
    print(documents)
    return render_template('document.html', form=form, stocks=stocks, documents=documents, product='0')


@app.route('/pdocument/<product_id>')
@login_required
def pdocument(product_id):
    form = SpecificationForm()
    stocks = Stock.query.filter(Stock.id_product == product_id).all()
    documents = [Document.query.filter(
        Document.id == stock.document_id).first() for stock in stocks]
    return render_template('document.html', form=form, stocks=stocks, documents=documents, product='1')


@app.route('/delete_document/<s_id>')
@login_required
def delete_document(s_id):
    stock = Stock.query.filter(Stock.id == s_id)
    component_id = stock.first().component_id
    product_id = stock.first().id_product
    stock.delete()
    db.session.commit()
    stck = ''
    if component_id:
        stck = Stock.query.filter(Stock.component_id == component_id).first()
    else:
        stck = Stock.query.filter(Stock.id_product == product_id).first()
    if stck:
        stck.get_count()
    else:
        if component_id:
            Component.query.filter(
                Component.id == component_id).first().stock_count = 0
            db.session.commit()
        else:
            Product.query.filter(
                Product.id == product_id).first().pstock_count = 0
            db.session.commit()
    if component_id:
        return redirect(url_for('document', component_id=component_id))
    return redirect(url_for('pdocument', product_id=product_id))


@app.route('/order/<doc>', methods=['GET', 'POST'])
@login_required
def order(doc):
    today = datetime.today()
    form = SpecificationForm()
    form1 = DocumentForm()
    added = current_user.order
    product = Product.query.order_by(Product.product_name).all()
    document = ''
    if doc == 'False':
        document = Document(today.strftime("%Y/%m/%d %H:%M"),
                            current_user.id, 'Резерв', ' ')
        db.session.add(document)
        db.session.commit()
    else:
        document = Document.query.filter(Document.id == doc).first()
    orders = document.product_orders
    if request.method == 'POST':
        if form.id.data == 'comment':

            # startdate = document.date.split(' ')[0].split('/')
            # year, month, day = int(startdate[0]), int(
            #     startdate[1]), int(startdate[2])
            document.endtime = form1.entrydate.data
            db.session.commit()
            current_user.order = []
            db.session.commit()
            orders = []
            db.session.commit()
            document.comment = form1.text.data
            db.session.commit()
            document.order_item = form1.number.data
            db.session.commit()

            flash('Заказ произведён', 'message')
            return redirect(url_for('order', doc='False', form1=form1, added=added, form=form, products=product))
        else:
            if form.count.data is None:
                flash('Используйте "." вместо ","')
                return redirect(url_for('order', doc=document.id,  form1=form1, added=added, form=form, products=product))
            order = Order(document.id, form.id.data, form.count.data)
            db.session.add(order)
            db.session.commit()
            document.append_doc_order(order.id)
            return redirect(url_for('check_order', order=order.id))
    return render_template('order.html', doc='False', form1=form1, added=added, form=form, products=product, orders=orders)


@app.route('/check_order/<order>', methods=['GET', 'POST'])
@login_required
def check_order(order):
    doc_type = 'Заказ'
    order = Order.query.filter(Order.id == order).first()
    product = Product.query.filter(Product.id == order.prod_id).first()
    def pstock(x): return x if x and x > 0 else 0
    order_status = 'Обработка'
    form = SubmitForm()
    new_md = dict()
    if request.method == 'POST':
        details = dict()
        with open(str(product.id)+'.json', 'r', encoding='utf-8') as fh:  # открываем файл на чтение
            details = json.load(fh)
        current_user.append_order(product)
        db.session.commit()
        if product.pstock_count is None or product.pstock_count < order.count:
            for key in details.keys():
                cmpnnt = Component.query.filter(
                    Component.component_name == key).first()
                db.session.add(Stock(order.doc_id, None, cmpnnt.id, math.ceil(details[key]*(order.count-pstock(product.pstock_count)))))
                db.session.commit()
                Stock.query.filter(
                    cmpnnt.id == Stock.component_id).first().get_count()
        else:
            p_stock = Stock.query.filter(
                Stock.id_product == product.id).first()
            db.session.add(Stock(order.doc_id, product.id,
                                 None, product.pstock_count))
            db.session.commit()
            p_stock.get_count()

        flash('Товар {} добавлен в список'.format(
            product.product_name), 'message')
        return redirect(url_for('order', doc=order.doc_id))
    if request.method == 'GET':
        details = product.get_det()
        details_new = details.copy()
        stock = []
        mod_stock = []
        if product.pstock_count is not None and product.pstock_count > 0:
            p_stock = Stock.query.filter(
                Stock.id_product == product.id).first()
            stock.append([product, p_stock])
        if product.pstock_count is None or product.pstock_count < (order.count):
            get_mods_rec(details_new, new_md, product, pstock, order)
            for name in details_new.keys():
                component = Component.query.filter(
                    Component.component_name == name).first()
                item = Stock.query.filter(
                    Stock.component_id == component.id).first()
                if item is None or component.stock_count < (details_new[name]*(order.count-pstock(product.pstock_count))):
                    def check(x): return 'Резерв' if x == 'Заказ' else x
                    doc_type = check(doc_type)
                    unfired = lambda x: x if x else 0
                    if component.stock_count:
                        note = Note(component.id, product.id, order.id, math.fabs(
                            (component.stock_count+unfired(component.unfired))-(details_new[name]*(order.count-pstock(product.pstock_count)))), '')
                    else:
                        note = Note(component.id, product.id, order.id, math.fabs((details_new[name]*(order.count-pstock(product.pstock_count)))), '')
                    db.session.add(note)
                    db.session.commit()
                    order_status = None
                    component.get_note_count()
                    stock.append([component, item])
                else:
                    stock.append([component, item])
            for name in new_md:
                component = Component.query.filter(
                    Component.component_name == name).first()
                item = Stock.query.filter(
                    Stock.component_id == component.id).first()
                mod_stock.append([component, item])
        order.status = doc_type
        order.get_document().document_type = 'Резерв'
        db.session.commit()
        order.get_document().order_status = order_status
        db.session.commit()

    with open(str(product.id)+'.json', 'w', encoding='utf-8') as fh:  # открываем файл на запись
        dets = dict()
        dets.update(details_new)
        dets.update(new_md)
        print(dets)
        fh.write(json.dumps(dets, ensure_ascii=False))
    return render_template('check_order.html', form=form, order=order, pstock=pstock(product.pstock_count), product=product, modules=new_md, details=details_new, stock=stock, mod_stock=mod_stock, doc_type=doc_type)


@app.route('/update_status', methods=['POST', 'GET'])
def update_status():
    doc = Document.query.filter(Document.id == request.form['id']).first()
    if doc.order_status == 'Обработка':
        doc.order_status = 'в производстве'
        db.session.commit()
    elif doc.order_status == 'в производстве':
        doc.order_status = 'отгружен'
        db.session.commit()
    elif doc.order_status == 'отгружен':
        doc.order_status = 'выполнен'
        db.session.commit()
    else:
        doc.order_status = 'Завершен'
        db.session.commit()
    return jsonify({'cards': render_template('orders_in_process.html',  order=doc),
                    'table': render_template('table_order_in_process.html',  order=doc, roles=[x.name for x in current_user.roles])})


@app.route('/update_all', methods=['POST', 'GET'])
def update_all():
    docs = Document.query.filter(Document.product_orders).filter(
        Document.order_item).all()
    print(docs)
    for doc in docs:
        if doc.order_status not in ['Обработка', 'в производстве', 'отгружен', 'выполнен', 'Завершен']:
            print(doc.order_status)
            order_processor(doc.id)
    return jsonify({'card': render_template('all_orders_in_process.html',  orders=docs, roles=[x.name for x in current_user.roles]),
                    'table': render_template('all_table_order_in_process.html',  orders=docs, roles=[x.name for x in current_user.roles])})


@app.route('/update', methods=['POST', 'GET'])
def get_report_order():
    doc = Document.query.filter(Document.id == request.form['id']).first()
    start_time = time.time()
    order_processor(request.form['id'])
    print("--- %s seconds ---" % (time.time() - start_time))
    return jsonify({'card': render_template('orders_in_process.html',  order=doc, roles=[x.name for x in current_user.roles]),
                    'table': render_template('table_order_in_process.html',  order=doc, roles=[x.name for x in current_user.roles])})


def order_processor(doc):
    doc = Document.query.filter(Document.id == doc).first()
    print(doc)
    doc_type = 'Заказ'
    if doc.order_status is None:
        order_status = 'Обработка'
    else:
        order_status = doc.order_status
    for order in doc.product_orders:
        items = []
        product = order.get_product()
        details = {}
        def pstock(x): return x if x and x > 0 else 0
        details_new = product.get_det()
        stock = []
        mod_stock = []
        new_md = dict()
        start_time = time.time()
        try:
            with open(str(product.id)+'.json', 'r', encoding='utf-8') as fh:  # открываем файл на чтение
                details = json.load(fh)
        except:
            details = details_new.copy()
        print("--- %s seconds ---" % (time.time() - start_time))
        start_time = time.time()
        stocks = Stock.query.filter(Stock.document_id == doc.id)
        for stck in stocks.all():
            Stock.query.filter(Stock.id == stck.id).delete()
        db.session.commit()
        print("--- %s seconds ---" % (time.time() - start_time))
        pstck = Stock.query.filter(Stock.id_product == product.id).filter(
            Stock.document_id == doc.id)
        for p in pstck.all():
            items.append(p)
        for note in Note.query.filter(Note.order_id == order.id).all():
            Note.query.filter(Note.id == note.id).delete()
        db.session.commit()
        start_time = time.time()
        # print([(x.get_component().component_name, x.get_document().document_type, x) for x in items])
        if product.pstock_count is not None and product.pstock_count > 0:
            stock.append([product, Stock.query.filter(
                Stock.id_product == product.id).first()])
        if product.pstock_count is None or product.pstock_count < (order.count):
            get_mods_rec(details_new, new_md, product, pstock, order)
            for name in details_new.keys():
                query = db.session.query(Component, Stock).filter(
                    Component.component_name == name).filter(Stock.component_id == Component.id).first()
                if query is None:
                    query = [(Component.query.filter(
                    Component.component_name == name).first()), None]
                if query[1]:
                    query[1].get_count()
                if query[1] is None or query[0].stock_count < (details_new[name]*(order.count-pstock(product.pstock_count))):
                    doc_type = 'Резерв'
                    note = Note(query[0].id, product.id, order.id, math.fabs(
                        (query[0].stock_count+query[0].unfired)-(details_new[name]*(order.count-pstock(product.pstock_count)))), '')
                    db.session.add(note)
                    db.session.commit()
                    order_status = None
                    query[0].get_note_count()
            for name in new_md:
                query2 = db.session.query(Component, Stock).filter(
                    Component.component_name == name).filter(Stock.component_id == Component.id).first()
                query2[1].get_count()
        order.status = doc_type
        db.session.commit()
        order.get_document().order_status = order_status
        db.session.commit()
        print("--- %s seconds ---" % (time.time() - start_time))

        start_time = time.time()
        with open(str(product.id)+'.json', 'w', encoding='utf-8') as fh:  # открываем файл на запись
            dets = dict()
            dets.update(details_new)
            dets.update(new_md)
            fh.write(json.dumps(dets, ensure_ascii=False))

        with open(str(product.id)+'.json', 'r', encoding='utf-8') as fh:  # открываем файл на чтение
            details = json.load(fh)
        print("--- %s seconds ---" % (time.time() - start_time))
        start_time = time.time()
        if product.pstock_count is None or product.pstock_count < order.count:
            for key in details.keys():
                cmpnnt = Component.query.filter(Component.component_name == key).first().id
                stck = Stock.query.filter(Stock.document_id==order.doc_id).filter(Stock.component_id==cmpnnt).first()
                if stck:
                    stck.count = math.ceil(dets[key]*(order.count-pstock(product.pstock_count)))
                    db.session.commit()
                    stck.get_count()
                else:
                    new_stck = Stock(order.doc_id, None, cmpnnt,
                                        math.ceil(dets[key]*(order.count-pstock(product.pstock_count))))
                    db.session.add(new_stck)
                    db.session.commit()
                    new_stck.get_count()

        else:
            p_stock = db.session.query(Product.id).filter(
                Stock.id_product == product.id).first()
            p_stck = Stock(order.doc_id, p_stock[0], None, product.pstock_count)
            db.session.add(p_stck
                )
            db.session.commit()
            p_stck.get_count()
            
        print("--- %s seconds ---" % (time.time() - start_time))


def get_mods_rec(details_new, new_md, product, pstock, order):
    names = []
    for name in details_new.keys():
        if type(details_new[name]) == dict:
            names.append(name)
    if names == []:
        return
    for name in names:
        for det in details_new[name]:

            if type(details_new[name][det]) == dict and details_new[name]['count'] > 1:
                details_new[name][det]['count'] *= details_new[name]['count']
        component = Component.query.filter(
            Component.component_name == name).first()
        item = Stock.query.filter(Stock.component_id == component.id).first()
        if item:
            item.get_count()
        if item and component.stock_count > 0:
            new_md.update({name: details_new[name]['count']})
            if component.stock_count < (details_new[name]['count']*(order.count-pstock(product.pstock_count))):
                count = details_new[name].pop('count')
                for det in details_new[name].keys():
                    if type(details_new[name][det]) != dict:
                        details_new[name][det] *= (
                            (count*order.count-component.stock_count)/(order.count))
                    else:
                        details_new[name][det]['count'] *= (
                            (count*order.count-component.stock_count)/(order.count))
                details_new.update(details_new[name])
            details_new.pop(name)
        else:
            if item:
                item.get_count()
            if 'count' in details_new[name]:
                count = details_new[name].pop('count')
                for det in details_new[name].keys():
                    if type(details_new[name][det]) != dict:
                        details_new[name][det] *= count
                    else:
                        details_new[name][det]['count'] *= count
            details_new.update(details_new[name])
        if name in details_new.keys():
            details_new.pop(name)
    get_mods_rec(details_new, new_md, product, pstock, order)
    return


@app.route('/delete_and_back/<id>')
@login_required
def delete_and_back(id):
    doc = Order.query.filter(Order.id == id).first().doc_id
    order = Order.query.filter(Order.id == id).first()
    stck = list(db.session.query(Stock.component_id).filter(Stock.document_id==doc).all())
    stocks = [x[0] for x in stck]
    stck_p = list(db.session.query(Stock.id_product).filter(Stock.document_id==doc).filter(Stock.id_product).all())
    stocks_p = [x[0] for x in stck_p]
    order.delete()
    if stocks:
        for stock in stocks:
            s = Stock.query.filter(Stock.component_id==stock).first()
            if s:
                s.get_count()
    if stocks_p:
        for stock_p in stocks_p:
            s_p = Stock.query.filter(Stock.id_product==stock_p).first()
            if s_p:
                s_p.get_count()
    
    return redirect(url_for('order', doc=doc))


@app.route('/delete_order/<id>')
@login_required
def delete_order(id):
    Document.delete(id)
    return redirect(url_for('home_page'))


@app.route('/fork/<doc_type>')
@login_required
def fork(doc_type):
    for item in current_user.get_added():
        db.session.delete(item)
        current_user.added.remove(item)
        db.session.commit()
    return redirect(url_for('stock_adding', doc_type=doc_type, doc='False'))


@app.route('/prod_fork/<doc_type>')
@login_required
def prod_fork(doc_type):
    for item in current_user.get_added():
        db.session.delete(item)
        current_user.added.remove(item)
        db.session.commit()
    return redirect(url_for('pstock_adding', doc_type=doc_type, doc='False'))


@app.route('/delete_stock/<stock_id>/<doc_id>')
@login_required
def delete_stock(stock_id, doc_id):
    current_user.delete_stock(stock_id)
    doc = Document.query.filter(Document.id == doc_id).first()
    return redirect(url_for('stock_adding', doc_type=doc.document_type, doc=doc.id))


@app.route('/delete_pstock/<stock_id>/<doc_id>')
@login_required
def delete_pstock(stock_id, doc_id):
    current_user.delete_stock(stock_id)
    doc = Document.query.filter(Document.id == doc_id).first()
    return redirect(url_for('pstock_adding', doc_type=doc.document_type, doc=doc.id))


@app.route('/remove_stock/<component_id>')
@login_required
def remove_stock(component_id, comment):
    document = Document(datetime.utcnow(), current_user.id,
                        'Cписание', comment)
    db.session.add(document)
    db.session.commit()
    stock = Stock(document.id, None, component_id, 0)
    db.session.add(stock)
    db.session.commit()
    return redirect(url_for('stock'))


@app.route('/storekeeper_page', methods=['GET', 'POST'])
@login_required
def storekeeper_page():
    roles = [x.name for x in current_user.roles]
    notes = [Note.query.filter(Note.na_component == x[0]).first(
    ) for x in set(db.session.query(Note.na_component).all())]
    print(notes)
    form = NoteForm()
    if request.method == 'POST':
        Note.query.filter(Note.id == form.id.data).first(
        ).arrival_date = form.entrydate.data
        db.session.commit()
        return redirect(url_for('storekeeper_page'))
    return render_template('store_keeper_page.html', notes=notes, form=form, roles=roles)


@app.route('/untouched_details', methods=['POST'])
@login_required
def untouched_details():
    order = request.form['order']
    product = request.form['product']
    roles = [x.name for x in current_user.roles]
    notes = Note.query.filter(Note.order_id == order).filter(
        Note.na_product == product).all()
    return render_template('untouched_details.html', notes=notes)


@app.route('/workshops', methods=['GET', 'POST'])
def workshops():
    workshops = Shop.query.all()

    return render_template('workshops.html', workshops=workshops)


@app.route('/make_shop', methods=['POST'])
def make_shop():
    new_shop = Shop()
    new_shop.name = request.form['name']
    db.session.add(new_shop)
    db.session.commit()
    workshops = Shop.query.all()
    return render_template('shop_tabs.html', workshops=workshops)


@app.route('/product_list', methods=['POST'])
def product_list():
    products = Product.query.all()
    print(products)
    return render_template('workshop_details.html', products=products, type=request.form['type'])

@app.route('/component_list', methods=['POST'])
def component_list():
    details = Component.query.all()
    products = Product.query.all()
    return render_template('workshop_details.html', details=details, products=products, type=request.form['type'])


@app.route('/add_component', methods=['POST'])
def add_component():
    component = Component.query.filter(
        Component.id == request.form['component_id']).first()
    shop = Shop.query.filter(Shop.id == request.form['workshop_id']).first()
    component.shop.append(shop)
    db.session.commit()
    details = db.session.query(Component).join(ComponentShop).filter(
        Component.id == ComponentShop.com_id).filter(shop.id == ComponentShop.shop_id).all()
    if len(details) <= 1:
        print('tut')
        return render_template('workshop_details.html', details=details, type='list')
    return render_template('component_row.html', det=component)

@app.route('/add_product', methods=['POST'])
def add_product():
    product = Order.query.filter(
        Order.prod_id == request.form['product_id']).first()
    if product is None:
        product = Order(None ,request.form['product_id'], None)
        db.session.add(product)
        db.session.commit()
    product.pshop_id = request.form['workshop_id']
    db.session.commit()
    products = db.session.query(Product).join(Order).filter(
        Product.id == Order.prod_id).filter(request.form['workshop_id'] == Order.pshop_id).all()
    if len(products) <= 1:
        return render_template('workshop_details.html', products=products, type='list')
    return render_template('product_row.html', prod=product)

@app.route('/show_workshop', methods=['POST'])
def show_workshop():
    details = db.session.query(Component).join(ComponentShop).filter(
        Component.id == ComponentShop.com_id).filter(request.form['workshop'] == ComponentShop.shop_id).all()
    products = db.session.query(Product).join(Order).filter(
        Product.id == Order.prod_id).filter(request.form['workshop'] == Order.pshop_id).all()
    
    return render_template('workshop_details.html', details=details, products = products,  type='list')


@app.route('/pworkshop_orders/<shop>', methods=['GET', 'POST'])
def pworkshop_orders(shop):
    prods = db.session.query(Order, Document, Product).filter(
        Order.doc_id == Document.id).filter(Order.prod_id==Product.id).all()
    print(prods)
    products = {}
    for prod in prods:
        print(prod)
        if prod[0]:
            print(prod[0].pshop_id)
            if prod[0].pshop_id==int(shop):
                print('tut')
                if prod[1].endtime:
                    endtime = datetime.strptime(prod[1].endtime,"%Y-%m-%d")
                    if endtime not in products:
                        products[prod[1].endtime] = prod
                    else:
                        products[prod[1].endtime].append(prod)
    print(products)
    times=sorted(products, key=lambda x: x)
    return render_template('pworkflow_table.html', times = times, components = products)

@app.route('/workshop_orders', methods=['GET', 'POST'])
def workshop_orders():
    print(request.form['shop'])
    query = Document.query.filter(
        Document.order_status == 'в производстве').all()
    dets = db.session.query(Stock, Document, Component).filter(
        Stock.document_id == Document.id).filter(Stock.component_id==Component.id).all()
    components = {}
    for det in dets:
        if det[2].shop :
            if det[2].shop[0].id==int(request.form['shop']):
                if det[1].endtime:
                    endtime = datetime.strptime(det[1].endtime,"%Y-%m-%d")
                    if endtime not in components:
                        components[det[1].endtime] = det
                    else:
                        components[det[1].endtime].append(det)
    if components == {}:
        return redirect(url_for('pworkshop_orders', shop = request.form['shop']))
    times=sorted(components, key=lambda x: x)
    return render_template('workflow_table.html', docs = query, times = times, components = components)

@app.route('/delete_component_shop', methods=['GET', 'POST'])
def delete_component_shop():
    Component.query.filter(Component.id==request.form['id']).first().shop=[]
    db.session.commit()
    return '', 204

@app.route('/delete_product_shop', methods=['GET', 'POST'])
def delete_product_shop():
    Order.query.filter(Order.prod_id==request.form['id']).filter(Order.pshop_id is not None).first().pshop_id=None
    db.session.commit()
    return '', 204

@app.route('/workflow', methods=['GET', 'POST'])
def workflow():
    workshops = Shop.query.all()
    roles = [x.name for x in current_user.roles]
    return render_template('workflow.html', roles=roles, workshops=workshops)

@app.route('/workflow_count', methods=['GET', 'POST'])
def workflow_count():
    stock = Stock.query.filter(Stock.id == request.form['stock']).first()
    new_doc = Document(datetime.today().strftime("%Y/%m/%d %H:%M"), current_user.id, 'Приход', '')
    db.session.add(new_doc)
    db.session.commit()
    new_stck = Stock(new_doc.id, None, stock.get_component().id, int(request.form['workflow_count']))
    db.session.add(new_stck)
    db.session.commit()
    new_stck.get_count()
    if stock.workflow_count:
        stock.workflow_count+=int(request.form['workflow_count'])
        db.session.commit()
        print(stock.workflow_count)
    else:
        stock.workflow_count=int(request.form['workflow_count'])
        db.session.commit()
        print(stock.workflow_count)
    
    return render_template('workflow_row.html', stock = stock)

@app.route('/pworkflow_count', methods=['GET', 'POST'])
def pworkflow_count():
    order = Order.query.filter(Order.id == request.form['order']).first()
    if order.pworkflow_count:
        order.pworkflow_count+=int(request.form['pworkflow_count'])
        db.session.commit()
        print(order.pworkflow_count)
    else:
        order.pworkflow_count=int(request.form['pworkflow_count'])
        db.session.commit()
        print(order.pworkflow_count)
    
    return render_template('pworkflow_row.html', order = order)

@app.route('/executed_orders', methods=['GET', 'POST'])
def executed_orders():
    executed_orders = Document.query.filter(Document.order_status=='выполнен').all()
    roles = [x.name for x in current_user.roles]
    return render_template('executed_orders.html', orders=sorted(executed_orders, key=lambda x: x.id)[::-1], roles=roles)

