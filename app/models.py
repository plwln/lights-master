from app import db
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from sqlalchemy import Table, MetaData
from sqlalchemy.sql import text
from flask import flash

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
        for role in self.roles:
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
    def delete_order(self):
        for item in self.order:
            self.order.remove(Product.query.filter(Product.id==item.id).first())
            db.session.commit()
            

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

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

    @staticmethod
    def get_details_report(spec,det, count=1):
        component_name = ''
    
        for item in spec:
            if type(item)==Specification: 
                item_id = item.component_id
            else: item_id = item.child_id
            if item.get_children(item_id):
                count *= item.count
                Product.get_details_report(ModalComponent.query.filter(ModalComponent.parrent_id==item_id).all(),det, count)
                
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
    def __init__(self, component_name, component_unit, component_item):
        self.component_name = component_name
        self.component_unit = component_unit
        self.component_item = component_item
    
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
    
    def get_count(self, parent_id):
        count = ModalComponent.query.filter(ModalComponent.parrent_id==parent_id, ModalComponent.child_id==self.id).first().count
        return count
    
    def get_name(self):
        liters = [' ', '"',".","(",")","/","\\","*", "_","-",",", ":", ";"]
        name = self.component_name
        for liter in liters:
            name = name.replace(liter, '')
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
    
    def get_component(self):
        return Component.query.filter(Component.id == self.component_id).first()
    
    def get_product(self):
        return Product.query.filter(Product.id == self.product_id).first()

    def get_children(self, id):
        children = ModalComponent.get_children(self.component_id)
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

    def __init__(self, date, maker_id, document_type, comment):
        self.date = date
        self.maker_id = maker_id
        self.document_type = document_type
        self.comment = comment
    
    def get_maker(self):
        return User.query.filter(User.id==self.maker_id).first()
    def get_name(self):
        return 'Document{}'.format(self.id)

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer(), primary_key=True)
    document_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    component_id = db.Column(db.Integer(), db.ForeignKey('component.id', ondelete='CASCADE'))
    count =  db.Column(db.Float())

    def __init__(self, document_id, component_id, count):
        self.document_id = document_id
        self.component_id = component_id
        self.count = count

    def get_name(self):
        name = Component.query.filter(Component.id==self.component_id).first().component_name
        return name
    def get_unit(self):
        unit = Component.query.filter(Component.id==self.component_id).first().component_unit
        return unit

    def get_count(self):
        count=0
        for item in Stock.query.filter(Stock.component_id==self.component_id).all():
            if item.get_document().document_type=='Приход':
                count+=item.count
            elif item.get_document().document_type=='Расход':
                if count>=item.count:
                    count-=item.count
                else:
                    db.session.delete(item)
                    db.session.commit()

            else:
                count=0

        Component.query.filter(Component.id==self.component_id).first().stock_count=count
        db.session.commit()

    def get_component(self):
        return Component.query.filter(Component.id==self.component_id).first()
    
    def get_document(self):
        return Document.query.filter(Document.id==self.document_id).first()



