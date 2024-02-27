from flask import Flask, render_template, url_for, request, flash, redirect, session
from init_db import get_connection

app = Flask(__name__)
app.config['SECRET_KEY'] = '****'
DATABASE_NAME = '****'


def get_post(post_id, user_id):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, category, name, priority, texts FROM todo_list WHERE id = %s AND user_id = %s""",
                (post_id, user_id)
            )
            post = cursor.fetchone()

    if post:
        return {
            'id': post[0],
            'category': post[1],
            'name': post[2],
            'priority': post[3],
            'texts': post[4]
        }
    else:
        return None


def get_user_id(user_id):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                return None


def register_user(username, password):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE user_name = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return False

            cursor.execute("INSERT INTO users (user_name, password) VALUES (%s, %s) RETURNING id", (username, password))
            user_id = cursor.fetchone()[0]
            conn.commit()

            session['user_id'] = user_id
            return True


def authenticate_user(username, password):
    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE user_name = %s AND password = %s", (username, password))
            user = cursor.fetchone()

            if user:
                session['user_id'] = user[0]
                return True
            else:
                return False


def before_request():
    if request.endpoint not in ['register', 'login'] and 'user_id' not in session:
        return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required')
        else:
            result = register_user(username, password)
            if result:
                flash('Registration successful. You can now log in.')
                return redirect(url_for('login'))
            else:
                flash('Username already exists. Please choose a different username.')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required')
        else:
            result = authenticate_user(username, password)
            if result:
                flash(f'Welcome back, {username}!')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')

    return render_template('login.html')


@app.route('/posts/<int:post_id>/<int:user_id>')
def post(post_id, user_id):
    user_id = session.get('user_id')
    if user_id:
        post = get_post(post_id, user_id)
        if post:
            return render_template('post.html', post=post)
        else:
            flash('Post not found')
            return redirect(url_for('index'))
    else:
        flash('User not authenticated')
        return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    priority = request.form.get('priority') if request.method == 'POST' else None
    category = request.form.get('category') if request.method == 'POST' else None
    user_id = session.get('user_id')

    if user_id is None:
        flash('User not authenticated')
        return redirect(url_for('login'))

    user_id = get_user_id(user_id)

    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT category FROM todo_list WHERE user_id = %s",
                (user_id,)
            )
            categories = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT DISTINCT priority FROM todo_list WHERE user_id = %s",
                (user_id,)
            )
            priorities = [row[0] for row in cursor.fetchall()]

            condition = " AND user_id = %s"
            params = [user_id]

            if category and category != 'All categories':
                condition += " AND LOWER(category) = %s"
                params.append(category.lower())

            if priority and priority != 'All priority':
                condition += " AND LOWER(priority) = %s"
                params.append(priority.lower())

            cursor.execute("""
                SELECT todo_list.id, todo_list.user_id, todo_list.name, todo_list.category, 
                todo_list.priority, todo_list.texts FROM todo_list JOIN users ON todo_list.user_id = users.id
                WHERE 1 = 1""" + condition, params
                           )
            posts = cursor.fetchall()

            posts_data = []
            for post in posts:
                posts_data.append(
                    {
                        'id': post[0],
                        'user_id': post[1],
                        'name': post[2],
                        'category': post[3],
                        'priority': post[4],
                        'texts': post[5],
                    }
                )

            cursor.execute(
                "SELECT id, user_name FROM users"
            )
            users = cursor.fetchall()

    return render_template('index.html', posts=posts_data, categories=categories,
                           selected_category=category, priorities=priorities, selected_priority=priority,
                           user_id=user_id, users=users)


@app.route('/create-post', methods=['GET', 'POST'])
def create():
    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        priority = request.form['priority']
        texts = request.form['texts']
        user_id = get_user_id(session.get('user_id'))

        if not name or not category or not priority or not texts:
            flash('Name, category, priority, and texts are required')
        elif not user_id:
            flash('User not authenticated')
        else:
            with get_connection(DATABASE_NAME) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO todo_list (user_id, category, name, priority, texts) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, category, name, priority, texts)
                    )
                    conn.commit()

            flash('Task created successfully')
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    user_id = get_user_id(session.get('user_id'))
    post = get_post(post_id, user_id)
    if not post:
        flash('Post not found')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        priority = request.form['priority']
        texts = request.form['texts']

        if not name or not category or not priority or not texts:
            flash('Name, category, priority, and texts are required')
        else:
            with get_connection(DATABASE_NAME) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE todo_list
                        SET name = %s,
                        category = %s,
                        priority = %s,
                        texts = %s
                        WHERE id = %s AND user_id = %s
                        """,
                        (name, category, priority, texts, post_id, user_id)
                    )
                    conn.commit()
                flash('Post updated successfully')
                return redirect(url_for('index'))

    return render_template('edit.html', post=post)


@app.route('/<int:post_id>/delete', methods=['POST'])
def delete(post_id):
    user_id = get_user_id(session.get('user_id'))
    post = get_post(post_id, user_id)
    if not post:
        flash('Post not found')
        return redirect(url_for('index'))

    with get_connection(DATABASE_NAME) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM todo_list WHERE id = %s AND user_id = %s",
                (post_id, user_id)
            )
            conn.commit()

    flash('Post deleted successfully')
    return redirect(url_for('index'))


app.run(debug=True)
