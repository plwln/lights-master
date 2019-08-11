from app import app, db
from app.models import User, UserRoles, Role, Product, Component, Specification, ModalComponent
from app.forms import ProductForm, ComponentForm, SpecificationForm
from sqlalchemy import orm

parent = orm.aliased(ModalComponent)
child = orm.aliased(ModalComponent)
top_q = (orm.query.Query([Component.id.label('id')]).join(ModalComponent, Component.id == ModalComponent.parrent_id).cte(recursive=True))
bottom_q = (orm.query.Query([child.parrent_id.label('id')]).join(parent, parent.parrent_id == child.parrent_id))

final_query = top_q.union_all(bottom_q)

print(orm.query.Query([final_query.c.id]).with_session(db.session).all())