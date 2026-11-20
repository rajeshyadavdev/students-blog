from datetime import UTC, datetime

from blog.extensions import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    date_posted = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(UTC),
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
