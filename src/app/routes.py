from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, Board, Column, Card, board_shares
from app.forms import RegistrationForm, LoginForm, BoardForm, ColumnForm, CardForm, SettingsForm, ShareBoardForm
from sqlalchemy import and_

# Define blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
kanban = Blueprint('kanban', __name__)

# Main blueprint for general routes

@main.route('/')
@main.route('/home')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('kanban.boards'))
    return render_template('index.html', title='Home')
# Auth blueprint for authentication routes

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        current_user.dark_mode = form.dark_mode.data
        db.session.commit()
        flash('Your settings have been updated!', 'success')
        return redirect(url_for('auth.settings'))
    elif request.method == 'GET':
        form.dark_mode.data = current_user.dark_mode
    return render_template('settings.html', title='User Settings', form=form)
# Kanban blueprint for kanban board routes

@kanban.route('/boards')
@login_required
def boards():
    # Get boards owned by the user
    owned_boards = Board.query.filter_by(user_id=current_user.id).all()
    
    # Get boards shared with the user
    shared_boards = current_user.shared_boards
    
    form = BoardForm()
    return render_template('boards.html', title='My Boards', 
                          owned_boards=owned_boards, 
                          shared_boards=shared_boards, 
                          form=form)

@kanban.route('/board/new', methods=['POST'])
@login_required
def new_board():
    form = BoardForm()
    if form.validate_on_submit():
        board = Board(title=form.title.data, user_id=current_user.id)
        db.session.add(board)
        db.session.commit()
        
        # Create default columns
        columns = [
            Column(title='To Do', position=0, board_id=board.id),
            Column(title='In Progress', position=1, board_id=board.id),
            Column(title='Done', position=2, board_id=board.id)
        ]
        db.session.add_all(columns)
        db.session.commit()
        
        flash('Your board has been created!', 'success')
    return redirect(url_for('kanban.boards'))

@kanban.route('/board/<int:board_id>')
@login_required
def board(board_id):
    board = db.session.get(Board, board_id)

    # Check if user is owner or has access
    if not (board.is_owner(current_user) or board.can_view(current_user)):
        abort(403)
    
    columns = Column.query.filter_by(board_id=board_id).order_by(Column.position).all()
    column_form = ColumnForm()
    card_form = CardForm()
    
    # Only show edit forms if user has edit permission
    can_edit = board.is_owner(current_user) or board.can_edit(current_user)
    
    return render_template('kanban.html', title=board.title, board=board, 
                           columns=columns, column_form=column_form, card_form=card_form,
                           can_edit=can_edit)

@kanban.route('/board/<int:board_id>/share', methods=['GET', 'POST'])
@login_required
def share_board(board_id):
    board = db.session.get(Board, board_id)
    
    # Only the owner can share the board
    if not board.is_owner(current_user):
        abort(403)
    
    form = ShareBoardForm()
    if form.validate_on_submit():
        user_to_share_with = User.query.filter_by(email=form.user_email.data).first()
        
        # Check if already shared
        existing_share = db.session.query(board_shares).filter_by(
            user_id=user_to_share_with.id,
            board_id=board.id
        ).first()
        
        if existing_share:
            flash(f'This board is already shared with {user_to_share_with.username}', 'warning')
        else:
            # Add to shared_with relationship
            can_edit = form.permission.data == 'edit'
            
            # Insert into the association table
            stmt = board_shares.insert().values(
                user_id=user_to_share_with.id,
                board_id=board.id,
                can_edit=can_edit
            )
            db.session.execute(stmt)
            db.session.commit()
            
            flash(f'Board shared with {user_to_share_with.username}!', 'success')
        
        return redirect(url_for('kanban.share_board', board_id=board.id))
    
    # Get all users this board is shared with
    shared_users = []
    shares = db.session.query(board_shares.c.user_id, board_shares.c.can_edit, User).\
        join(User, User.id == board_shares.c.user_id).\
        filter(board_shares.c.board_id == board.id).all()
    
    for user_id, can_edit, user in shares:
        shared_users.append({
            'user': user,
            'can_edit': can_edit
        })
    
    return render_template('share_board.html', title=f'Share {board.title}', 
                          board=board, form=form, shared_users=shared_users)

@kanban.route('/board/<int:board_id>/user/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_share(board_id, user_id):
    board = db.session.get(Board, board_id)
    
    # Only the owner can remove shares
    if not board.is_owner(current_user):
        abort(403)
    
    # Delete the share
    stmt = board_shares.delete().where(
        and_(
            board_shares.c.board_id == board_id,
            board_shares.c.user_id == user_id
        )
    )
    db.session.execute(stmt)
    db.session.commit()
    
    flash('User access has been removed!', 'success')
    return redirect(url_for('kanban.share_board', board_id=board.id))

@kanban.route('/board/<int:board_id>/user/<int:user_id>/permission', methods=['POST'])
@login_required
def update_share_permission(board_id, user_id):
    board = db.session.get(Board, board_id)
    
    # Only the owner can update permissions
    if not board.is_owner(current_user):
        abort(403)
    
    permission = request.form.get('permission')
    can_edit = permission == 'edit'
    
    # Update the permission
    stmt = board_shares.update().where(
        and_(
            board_shares.c.board_id == board_id,
            board_shares.c.user_id == user_id
        )
    ).values(can_edit=can_edit)
    
    db.session.execute(stmt)
    db.session.commit()
    
    flash('Permission updated!', 'success')
    return redirect(url_for('kanban.share_board', board_id=board.id))

@kanban.route('/board/<int:board_id>/column/new', methods=['POST'])
@login_required
def new_column(board_id):
    board = db.session.get(Board, board_id)
    
    # Check if user has edit permission
    if not (board.is_owner(current_user) or board.can_edit(current_user)):
        abort(403)
    
    form = ColumnForm()
    if form.validate_on_submit():
        # Get the highest position and add 1
        max_position = db.session.query(db.func.max(Column.position)).filter_by(board_id=board_id).scalar() or -1
        column = Column(title=form.title.data, position=max_position + 1, board_id=board_id)
        db.session.add(column)
        db.session.commit()
        flash('Column added!', 'success')
    return redirect(url_for('kanban.board', board_id=board_id))

@kanban.route('/column/<int:column_id>/card/new', methods=['POST'])
@login_required
def new_card(column_id):
    column = db.session.get(Column, column_id)
    board = column.board
    
    # Check if user has edit permission
    if not (board.is_owner(current_user) or board.can_edit(current_user)):
        abort(403)
    
    form = CardForm()
    if form.validate_on_submit():
        # Get the highest position and add 1
        max_position = db.session.query(db.func.max(Card.position)).filter_by(column_id=column_id).scalar() or -1
        card = Card(
            title=form.title.data,
            description=form.description.data,
            position=max_position + 1,
            column_id=column_id
        )
        db.session.add(card)
        db.session.commit()
        flash('Card added!', 'success')
    return redirect(url_for('kanban.board', board_id=column.board_id))

@kanban.route('/card/<int:card_id>/move', methods=['POST'])
@login_required
def move_card(card_id):
    card = db.session.get(Card, card_id)
    board = card.column.board
    
    # Check if user has edit permission
    if not (board.is_owner(current_user) or board.can_edit(current_user)):
        abort(403)
    
    data = request.get_json()
    target_column_id = data.get('columnId')
    target_position = data.get('position')
    
    if target_column_id and target_position is not None:
        # Update positions in the source column
        source_column_id = card.column_id
        source_position = card.position
        
        if int(target_column_id) == source_column_id:
            # Moving within the same column
            if target_position < source_position:
                # Moving up
                Card.query.filter(
                    Card.column_id == source_column_id,
                    Card.position >= target_position,
                    Card.position < source_position
                ).update({Card.position: Card.position + 1}, synchronize_session=False)
            else:
                # Moving down
                Card.query.filter(
                    Card.column_id == source_column_id,
                    Card.position > source_position,
                    Card.position <= target_position
                ).update({Card.position: Card.position - 1}, synchronize_session=False)
        else:
            # Moving to a different column
            # Update positions in source column
            Card.query.filter(
                Card.column_id == source_column_id,
                Card.position > source_position
            ).update({Card.position: Card.position - 1}, synchronize_session=False)
            
            # Update positions in target column
            Card.query.filter(
                Card.column_id == target_column_id,
                Card.position >= target_position
            ).update({Card.position: Card.position + 1}, synchronize_session=False)
            
            # Update the card's column
            card.column_id = target_column_id
        
        # Update the card's position
        card.position = target_position
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 400

@kanban.route('/board/<int:board_id>/delete', methods=['POST'])
@login_required
def delete_board(board_id):
    board = db.session.get(Board, board_id)
    
    # Only the owner can delete the board
    if not board.is_owner(current_user):
        abort(403)
    
    db.session.delete(board)
    db.session.commit()
    flash('Your board has been deleted!', 'success')
    return redirect(url_for('kanban.boards'))

@kanban.route('/column/<int:column_id>/delete', methods=['POST'])
@login_required
def delete_column(column_id):
    column = db.session.get(Column, column_id)
    board = column.board
    
    # Check if user has edit permission
    if not (board.is_owner(current_user) or board.can_edit(current_user)):
        abort(403)
    
    board_id = column.board_id
    db.session.delete(column)
    db.session.commit()
    flash('Column has been deleted!', 'success')
    return redirect(url_for('kanban.board', board_id=board_id))

@kanban.route('/card/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    card = db.session.get(Card, card_id)
    board = card.column.board
    
    # Check if user has edit permission
    if not (board.is_owner(current_user) or board.can_edit(current_user)):
        abort(403)
    
    board_id = card.column.board_id
    db.session.delete(card)
    db.session.commit()
    flash('Card has been deleted!', 'success')
    return redirect(url_for('kanban.board', board_id=board_id))
