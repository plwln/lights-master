from app import db
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from sqlalchemy import Table, MetaData, exists
from sqlalchemy.sql import text
from flask import flash
from sqlalchemy.orm import validates

class Obs(db.Model):
    __tablename__ = 'obs'
    id = db.Column(db.Integer(), primary_key=True)
    update_date = db.Column(db.String())
    status = db.Column(db.String())
    doc = db.Column(db.Integer())

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')
    added = db.relationship('Stock', secondary='user_stock')
    order = db.relationship('Product', secondary='user_product')
    
    # Define the Role data-model
    def delete_role(self, del_role):
        self.roles.remove(Role.query.filter(Role.name==del_role).first())
        db.session.commit()
    def append_role(self, del_role):
        self.roles.append(Role.query.filter(Role.name==del_role).first())
        db.session.commit()

    def append_stock(self, del_stock):
        self.added.append(Stock.query.filter(Stock.id==del_stock).first())
        db.session.commit()
    def delete_added(self,delete='False'):
        for item in self.added:
            self.added.remove(Stock.query.filter(Stock.id==item.id).first())
            db.session.commit()

    def delete_stock(self, id):
        stock = Stock.query.filter(Stock.id==id).first()
        self.added.remove(stock)
        db.session.commit()
        db.session.delete(stock)
        db.session.commit()
    def get_added(self):
        added=[]
        for item in self.added:
            added.append(item)
        return added
    
    def append_order(self, del_stock):
        self.order.append(del_stock)
        db.session.commit()
    def get_order(self):
        order=[]
        for item in self.added:
            order.append(item)
        return order
            

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Shop(db.Model):
    __tablename__='shop'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

class ComponentShop(db.Model):
    __tablename__ = 'component_shop'
    id = db.Column(db.Integer(), primary_key=True)
    com_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    shop_id = db.Column(db.Integer(), db.ForeignKey('shop.id', ondelete='CASCADE'))

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class UserStock(db.Model):
    __tablename__ = 'user_stock'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    stock_id = db.Column(db.Integer(), db.ForeignKey('stock.id', ondelete='CASCADE'))

class UserProduct(db.Model):
    __tablename__ = 'user_product'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id', ondelete='CASCADE'))

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer(), primary_key=True)
    product_name = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    product_power = db.Column(db.Integer(), nullable=False)
    product_item = db.Column(db.Integer(), unique=True)
    product_weight = db.Column(db.Integer(), nullable=False)
    product_material = db.Column(db.String(255, collation='NOCASE'))
    pstock_count = db.Column(db.Float())
    p_unfired = db.Column(db.Float())
    def __init__(self, product_name, product_power, product_item, product_weight, product_material):
        self.product_name = product_name
        self.product_power = product_power
        self.product_item = product_item
        self.product_weight = product_weight
        self.product_material = product_material


    def delete_product(id):
        specification = Specification.query.filter(Specification.product_id==id).first()
        while specification:
            Specification.query.filter(Specification.product_id==id).delete()
            specification = Specification.query.filter(Specification.product_id==id).first()
        Product.query.filter(Product.id==id).delete()
        db.session.commit()

    def get_name(self):
        liters = [' ', '"',".","(",")","/","\\","*", "_","-",",", ":", ";"]
        name = self.product_name
        for liter in liters:
            name = name.replace(liter, '')
        return name
    
    def get_det(self):
        det = {}
        specifications=Specification.query.filter(Specification.product_id==self.id).all()
        report = Product.get_details_report(specifications, det)
        return report
    
    def old_get_det(self):
        det = {}
        specifications=Specification.query.filter(Specification.product_id==self.id).all()
        report = Product.old_get_details_report(specifications, det)
        return report

    @staticmethod
    def get_details_report(spec,det, count=1):
        component_name = ''
    
        for item in spec:
            if type(item)==Specification: 
                item_id = item.component_id
            else: item_id = item.child_id
            if item.get_children(item_id):
                component_name = Component.query.filter(Component.id==item_id).first().component_name
                det[component_name] = dict()
                det[component_name]['count'] = item.count
                Product.get_details_report(ModalComponent.query.filter(ModalComponent.parrent_id==item_id).all(), det[component_name], count)
                
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
    @staticmethod
    def old_get_details_report(spec,det, count=1):
        component_name = ''
    
        for item in spec:
            if type(item)==Specification: 
                item_id = item.component_id
            else: item_id = item.child_id
            if item.get_children(item_id):
                count *= item.count
                Product.old_get_details_report(ModalComponent.query.filter(ModalComponent.parrent_id==item_id).all(),det, count)
                
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



class Component(db.Model):
    __tablename__ = 'component'
    id = db.Column(db.Integer(), primary_key=True)
    component_name = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    component_unit = db.Column(db.String(255, collation='NOCASE'))
    component_item = db.Column(db.Integer(), unique=True)
    unfired = db.Column(db.Float())
    stock_count = db.Column(db.Float())
    note_count = db.Column(db.Float())
    shop = db.relationship('Shop', secondary='component_shop')
    def __init__(self, component_name, component_unit, component_item):
        self.component_name = component_name
        self.component_unit = component_unit
        self.component_item = component_item
    def shop_name(self):
        if self.shop !=[]:
            return self.shop[0].name
        else:
            return None
    def delete_component(id):
        specification = Specification.query.filter(Specification.component_id==id).first()
        child = ModalComponent.query.filter(ModalComponent.child_id==id).first()
        parrent = ModalComponent.query.filter(ModalComponent.parrent_id==id).first()
        stock = Stock.query.filter(Stock.component_id==id).first()
        while specification:
            Specification.query.filter(Specification.component_id==id).delete()
            specification = Specification.query.filter(Specification.component_id==id).first()
        while child:
            ModalComponent.query.filter(ModalComponent.child_id==id).delete()
            child = ModalComponent.query.filter(ModalComponent.child_id==id).first()
        while parrent:
            ModalComponent.query.filter(ModalComponent.parrent_id==id).delete()
            parrent = ModalComponent.query.filter(ModalComponent.parrent_id==id).first()
        while stock:
            Stock.query.filter(Stock.component_id==id).delete()
            stock = Stock.query.filter(Stock.component_id==id).first()
        Component.query.filter(Component.id==id).delete()
        db.session.commit()  
    
    def get_children(self, id):
        return False

    def get_type(self):
        return 'com'

    def get_note_count(self):
        self.note_count=0
        for note in Note.query.filter(Note.na_component==self.id):
            self.note_count+=note.n_count
        db.session.commit()

    def get_count(self, parent_id):
        count = ModalComponent.query.filter(ModalComponent.parrent_id==parent_id, ModalComponent.child_id==self.id).first().count
        return count
    def get_name(self):
        liters = [' ', '"',".","(",")","/","\\","*", "_","-",",", ":", ";"]
        name = self.component_name
        for liter in liters:
            name = name.replace(liter, '')
        name = name.lstrip().strip()
        return name

class Specification(db.Model):
    __tablename__ = 'specification'
    id = db.Column(db.Integer(), primary_key=True)
    component_type = db.Column(db.String(255, collation='NOCASE'))
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id', ondelete='CASCADE'))
    component_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    count =  db.Column(db.Float())
    residue = db.Column(db.Float())
    def __init__(self, component_type, product_id, component_id, count):
        self.component_type = component_type
        self.product_id = product_id
        self.component_id = component_id
        self.count = count
    
    def get_type(self):
        return 'spec'

    def get_component(self):
        return Component.query.filter(Component.id == self.component_id).first()
    
    def get_product(self):
        return Product.query.filter(Product.id == self.product_id).first()

    def get_children(self, id):
        children = ModalComponent.get_children(self.component_id)
        specs = [Specification.query.filter(Specification.product_id==self.product_id and Specification.component_id==x.id).first() for x in children]
        return children
class ModalComponent(db.Model):
    __tablename__ = 'modalcomponent'
    id = db.Column(db.Integer(), primary_key=True)
    parrent_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    child_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    count =  db.Column(db.Float())

    def __init__(self, parrent_id, child_id, count):
        self.parrent_id = parrent_id
        self.child_id = child_id
        self.count = count

    @staticmethod
    def get_children(id):
        children = []
        if ModalComponent.query.filter(ModalComponent.parrent_id==id).first():
            for parrent in ModalComponent.query.filter(ModalComponent.parrent_id==id).all():
                children.append(Component.query.filter(Component.id == parrent.child_id).first())
            return children
        return children

    @staticmethod
    def get_parents(id):
        parents = []
        if ModalComponent.query.filter(ModalComponent.child_id==id).first():
            for child in ModalComponent.query.filter(ModalComponent.child_id==id).all():
                parents.append(Component.query.filter(Component.id == child.parrent_id).first())
            return parents
        return parents

    def get_component(self):
        return Component.query.filter(Component.id == self.child_id).first()

class Document(db.Model):
    __tablename__ = 'document'
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.String())
    maker_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    document_type = db.Column(db.String())
    comment = db.Column(db.String())
    product_orders = db.relationship('Order', secondary='document_order')
    order_status = db.Column(db.String())
    order_item = db.Column(db.Integer(), unique=True)
    endtime = db.Column(db.String())
    def remove(self, order):
        self.product_orders.remove(order)
        db.session.commit()
    def __init__(self, date, maker_id, document_type, comment):
        self.date = date
        self.maker_id = maker_id
        self.document_type = document_type
        self.comment = comment

    def get_maker(self):
        return User.query.filter(User.id==self.maker_id).first()
    def get_name(self):
        return 'Document{}'.format(self.id)
    
    def append_doc_order(self, del_stock):
        self.product_orders.append(Order.query.filter(Order.id==del_stock).first())
        db.session.commit()
    

    @staticmethod
    def delete(id):
        print()
        orders = Order.query.filter(Order.doc_id==id).all()
        stock = Stock.query.filter(Stock.document_id==id).first()
        update = []
        for stck in Stock.query.filter(Stock.document_id==id).all():
            if stck.component_id:
                update.append([Stock.query.filter(Stock.component_id == stck.component_id and Stock.document_id!=id).first().id, current_user.username])
            else:
                update.append([Stock.query.filter(Stock.id_product == stck.id_product and Stock.document_id!=id).first().id, current_user.username])
        for order in orders:
            for note in Note.query.filter(Note.order_id==order.id).all():
                Note.query.filter(Note.id==note.id).delete()
            Order.query.filter(Order.id==order.id).delete()
        while stock:
            if stck.component_id:
                Stock.query.filter(Stock.component_id==stock.component_id).first().get_count()
            else:
                Stock.query.filter(Stock.id_product==stock.id_product).first().get_count()

            Stock.query.filter(Stock.document_id==id).delete()
            stock = Stock.query.filter(Stock.document_id==id).first()
        
        for item in update:
            stock = Stock.query.filter(Stock.id==item[0]).first()
            if stock and current_user.username==item[1]:
                stock.get_count()
        Document.query.filter(Document.id==id).delete()
        db.session.commit()  

class DocumentOrder(db.Model):
    __tablename__ = 'document_order'
    id = db.Column(db.Integer(), primary_key=True)
    document_id = db.Column(db.Integer(), db.ForeignKey('document.id', ondelete='CASCADE'))
    order_id = db.Column(db.Integer(), db.ForeignKey('product_order.id', ondelete='CASCADE'))

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer(), primary_key=True)
    document_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    component_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    id_product = db.Column(db.Integer(), db.ForeignKey('product.id', ondelete='CASCADE'))
    count =  db.Column(db.Float())
    workflow_count = db.Column(db.Float())
    def __init__(self, document_id, id_product, component_id, count):
        self.document_id = document_id
        self.component_id = component_id
        self.count = count
        self.id_product = id_product
    def get_name(self):
        if self.id_product:
            name = Product.query.filter(Product.id==self.id_product).first().product_name
        if self.component_id:
            name = Component.query.filter(Component.id==self.component_id).first().component_name
        
        return name
    def get_unit(self):
        unit = Component.query.filter(Component.id==self.component_id).first().component_unit
        return unit

    def get_old_count(self):
        count=0
        reserved = 0
        stock_count = 0
        if self.id_product:
            stocks = Stock.query.filter(Stock.id_product==self.id_product).all()
            stock_count = Product.query.filter(Product.id==self.id_product).first().pstock_count 
        if self.component_id:
            stocks = Stock.query.filter(Stock.component_id==self.component_id).all()
            stock_count = Component.query.filter(Component.id==self.component_id).first().stock_count
        for item in stocks:
            if item.get_document() and item.get_document().document_type=='Приход':
                count+=item.count
            elif item.get_document() and item.get_document().document_type=='Расход':
                count-=item.count
            elif item.get_document().document_type=='Резерв' or  item.get_document().document_type=='Заказ':
                count -= item.count
                if reserved is None:
                    reserved = item.count
                else:
                    reserved += item.count
            elif item.get_document():
                count=0
        if self.id_product:
            Product.query.filter(Product.id==self.id_product).first().p_unfired = reserved
            db.session.commit()
            Product.query.filter(Product.id==self.id_product).first().pstock_count=count
            db.session.commit()
        else: 
            Component.query.filter(Component.id==self.component_id).first().unfired = reserved
            db.session.commit()
            Component.query.filter(Component.id==self.component_id).first().stock_count = count
            db.session.commit()

    def get_count(self):
        count=0
        reserved = 0
        stock_count = 0
        if self.id_product:
            stocks = Stock.query.filter(Stock.id_product==self.id_product).all()
            stocks = db.session.query(Stock, Document).filter(Stock.id_product==self.id_product).join(Document, Stock.document_id==Document.id).all()
            stock_count = Product.query.filter(Product.id==self.id_product).first()
            if stock_count:
                stock_count = stock_count.pstock_count 
        if self.component_id:
            stocks = db.session.query(Stock, Document).filter(Stock.component_id==self.component_id).join(Document, Stock.document_id==Document.id).all()
            stock_count = Component.query.filter(Component.id==self.component_id).first().stock_count
        
        for item in stocks:
            if item[1].document_type=='Приход':
                count+=item[0].count
            elif item[1].document_type=='Расход':
                count-=item[0].count
            elif item[1].document_type == 'Резерв':
                count-=item[0].count
                reserved += item[0].count
            elif item[1].document_type=='Списание':
                count=0
            
        if self.id_product:
            if stock_count is not None:
                Product.query.filter(Product.id==self.id_product).first().p_unfired = reserved
                db.session.commit()
                Product.query.filter(Product.id==self.id_product).first().pstock_count=count
                db.session.commit()
        else:
            Component.query.filter(Component.id==self.component_id).first().unfired = reserved
            db.session.commit()
            Component.query.filter(Component.id==self.component_id).first().stock_count = count
            db.session.commit()


    def get_component(self):
        return Component.query.filter(Component.id==self.component_id).first()
    
    def get_product(self):
        return Product.query.filter(Product.id==self.id_product).first()

    def get_document(self):
        return Document.query.filter(Document.id==self.document_id).first()

class Order(db.Model):
    __tablename__ = 'product_order'
    id = db.Column(db.Integer(), primary_key=True)
    doc_id = db.Column(db.Integer(), db.ForeignKey('document.id', ondelete='CASCADE'))
    prod_id = db.Column(db.Integer(), db.ForeignKey('product.id', ondelete='CASCADE'))
    count =  db.Column(db.Float())
    status = db.Column(db.String())
    pshop_id = db.Column(db.Float())
    pworkflow_count = db.Column(db.Float())
    def __init__(self, doc_id, prod_id, count):
        self.doc_id = doc_id
        self.prod_id = prod_id
        self.count = count
    
    def get_product(self):
        return Product.query.filter(Product.id==self.prod_id).first()
    
    def get_document(self):
        return Document.query.filter(Document.id==self.doc_id).first()
    
    def delete(self):
        note = Note.query.filter(Note.order_id==self.id).first()
        stock = Stock.query.filter(Stock.document_id==self.doc_id).first()
        update = []
        for stck in Stock.query.filter(Stock.document_id==self.doc_id).all():
            if stck.component_id:
                update.append([Stock.query.filter(Stock.component_id == stck.component_id and Stock.get_document().id!=self.doc_id).first().id, current_user.username])
            else:
                update.append([Stock.query.filter(Stock.id_product == stck.id_product and Stock.get_document().id!=self.doc_id).first().id, current_user.username])
        while note:
                Note.query.filter(Note.order_id==self.id).delete()
                note = Note.query.filter(Note.order_id==self.id).first()
        while stock:
            if stck.component_id:
                Stock.query.filter(Stock.component_id==stock.component_id).first().get_count()
            else:
                Stock.query.filter(Stock.id_product==stock.id_product).first().get_count()

            Stock.query.filter(Stock.document_id==self.doc_id).delete()
            stock = Stock.query.filter(Stock.document_id==self.doc_id).first()
        
        for item in update:
            stock = Stock.query.filter(Stock.id==item[0]).first()
            if stock and current_user.username==item[1]:
                stock.get_count()
        Document.query.filter(Document.id==self.doc_id).first().remove(Order.query.filter(Order.id==self.id).first())
        Order.query.filter(Order.doc_id==self.id).delete()
        db.session.commit()  


class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer(), primary_key=True)
    na_component = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    na_product = db.Column(db.Integer(), db.ForeignKey('product.id', ondelete='CASCADE'))
    order_id = db.Column(db.Integer(), db.ForeignKey('product_order.id', ondelete='CASCADE'))
    arrival_date = db.Column(db.String())
    n_count = db.Column(db.Float())
    def __init__(self, na_component, na_product, order_id, n_count, arrival_date):
        self.na_component = na_component
        self.na_product = na_product
        self.order_id = order_id
        self.arrival_date = arrival_date
        self.n_count = n_count
    def get_name(self):
        retstr = 'note{}{}{}'.format(self.na_component, self.na_product, str(self.n_count).replace('.', ''))
        return retstr
    def get_component(self):
        return Component.query.filter(Component.id==self.na_component).first()



