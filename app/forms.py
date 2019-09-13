from flask_wtf import Form
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,  SelectField, FloatField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from app.models import Component

from wtforms import validators, ValidationError
from wtforms.fields import DateField

class ProductForm(Form):
    name = TextField("Наименование изделия",[validators.Required("Введите наименование изделия")])
    item = IntegerField("Артикул",[validators.Optional()])
    power = IntegerField("Мощность", [validators.Required("Введите мощность изделия")])
    materials = SelectField('Материалы', choices = [('Стекло','Стекло'),  ('Пластик','Пластик')])
    unit = IntegerField("Единица измерения",[validators.Optional()])
    weight = FloatField('Вес', [validators.Required("Введите вес изделия")])
    submit = SubmitField("Добавить")

class ComponentForm(Form):
    name = TextField("Наименование комплектующего",[validators.Required("Введите наименование изделия")])
    unit = TextField("Единица измерения",[validators.Required("Введите единицу измерения")])
    item = IntegerField("Артикул",[validators.Optional()])
    submit = SubmitField("Добавить")

class DocumentForm(Form):
    text = TextAreaField('Комментарий', render_kw={'class': 'form-control', 'rows': 5})
    number = IntegerField("Артикул",[validators.Required('Введите номер заказа')])
    entrydate = DateField('Дата', [validators.Required('Введите дату')], format='%d-%m-%Y')
    submit = SubmitField("Добавить")
    hidden_type = HiddenField()

def choise_query():
    return Component.query.all()

class SubmitForm(Form):
    submit = SubmitField("Заказать")
    order = SubmitField('Резерв')

class SpecificationForm(Form):
    det = 'hollow'

    def make_det(self,det):
        self.det=det

    component_type = SelectField('Тип компонента', choices = [('Детали корпуса','Детали корпуса'),  ('Электротехнические детали','Электротехнические детали'),
    ('Герметики', 'Герметики'), ('Метизы', 'Метизы'), ('Упаковка', 'Упаковка'), ('Расходные материалы', 'Расходные материалы')])
    document_type = SelectField('Тип документа', choices = [('Приход', 'Приход'),('Расход', 'Расход'), ('Списание','Списание')])
    detail = TextField(det,[validators.Required("Введите наименование детали")])
    count = FloatField('Количество', [validators.Required("Введите количество деталей")])
    submit = SubmitField("Добавить")
    text = TextAreaField('Комментарий', render_kw={'class': 'form-control', 'rows': 5})
    id = HiddenField()

class NoteForm(Form):
    id = HiddenField()
    entrydate = DateField('Дата поступления', format='%d-%m-%Y')
    submit = SubmitField("Добавить")