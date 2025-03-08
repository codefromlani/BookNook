from app import create_app, db
from app.models import User, Book, Order, OrderItem, Review

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Book': Book,
        'Order': Order,
        'OrderItem': OrderItem,
        'Review': Review
    } 