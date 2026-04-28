from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('用户名已存在，请使用其他用户名。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('邮箱已被注册，请使用其他邮箱。')


class ProfileForm(FlaskForm):
    height = FloatField('身高 (cm)', validators=[Optional(), NumberRange(min=50, max=250)])
    weight = FloatField('体重 (kg)', validators=[Optional(), NumberRange(min=20, max=200)])
    age = IntegerField('年龄', validators=[Optional(), NumberRange(min=10, max=100)])
    gender = SelectField('性别', choices=[('未设置', '未设置'), ('男', '男'), ('女', '女')], default='未设置')
    body_shape = SelectField('体型', choices=[
        ('未设置', '未设置'),
        ('沙漏型', '沙漏型'),
        ('梨型', '梨型'),
        ('苹果型', '苹果型'),
        ('倒三角型', '倒三角型'),
        ('矩形', '矩形')
    ], default='未设置')
    skin_tone = SelectField('肤色', choices=[
        ('未设置', '未设置'),
        ('白皙', '白皙'),
        ('自然', '自然'),
        ('小麦色', '小麦色'),
        ('深色', '深色')
    ], default='未设置')
    submit = SubmitField('保存修改')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    submit = SubmitField('发送重置链接')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('重置密码')
