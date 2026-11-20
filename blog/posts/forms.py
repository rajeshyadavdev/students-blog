from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class PostForm(FlaskForm):
    title = StringField(
        label="Title",
        validators=[DataRequired(), Length(min=3, max=100)],
    )
    content = TextAreaField(
        label="Content",
        validators=[DataRequired(), Length(min=10)],
    )
    submit = SubmitField(label="Post")


# Alias so existing imports of PostCreateForm continue working without changes
PostCreateForm = PostForm
