import webview

# window = webview.create_window('Nós Sociall', 'http://127.0.0.1:5000/')
# webview.start()

import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app
import mysql.connector
import random
import string
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Verifique se a pasta de uploads existe, caso contrário, crie-a
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    return mysql.connector.connect(
        host='nos-social.cb6uawesoga1.sa-east-1.rds.amazonaws.com',
        user='admin',
        password='e9Pd4ixme48JRv',
        database='nos_social'
    )

@app.route('/')
def root():
    return render_template('homepage.html')

@app.route('/registerUser', methods=['GET', 'POST'])
def registerUser():
    if request.method == 'POST':
        data = request.json
        fullName = data.get('fullName')
        userName = data.get('userName')
        emailUser = data.get('emailUser')
        phoneNumberUser = data.get('phoneNumberUser')
        passwordUser = data.get('passwordUser')
        confirmPassword = data.get('confirmPassword')
        userImg = data.get('userImg')

        if passwordUser != confirmPassword:
            return jsonify({"error": "As senhas não coincidem."}), 400

        db = get_db_connection()
        mycursor = db.cursor()
        try:
            query = "INSERT INTO user (fullName, userName, emailUser, phoneNumberUser, passwordUser, userImg) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (fullName, userName, emailUser, phoneNumberUser, passwordUser, userImg)
            mycursor.execute(query, values)
            db.commit()
            return jsonify({"redirect": url_for('loginUser')})
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500
        finally:
            mycursor.close()
            db.close()

    return render_template('registerUser.html')

def verificar_credenciais_usuario(emailUser, passwordUser):
    db = get_db_connection()
    mycursor = db.cursor()
    query = "SELECT id FROM user WHERE emailUser = %s AND passwordUser = %s"
    mycursor.execute(query, (emailUser, passwordUser))
    resultado = mycursor.fetchone()
    mycursor.close()
    db.close()
    return resultado

@app.route('/loginUser', methods=['GET', 'POST'])
def loginUser():
    if request.method == 'GET':
        return render_template('loginUser.html')
    elif request.method == 'POST':
        emailUser = request.form['emailUser']
        passwordUser = request.form['passwordUser']

        resultado = verificar_credenciais_usuario(emailUser, passwordUser)

        if resultado:
            user_id = resultado[0]
            return redirect(url_for('feed_user', id=user_id))
        else:
            return redirect(url_for('loginUser', error='Email ou senha inválidos'))
        
@app.route('/feedUser/<int:id>')
def feed_user(id):
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT id, fullName, userName, emailUser, phoneNumberUser, userImg FROM user WHERE id = %s", (id,))
    user = cursor.fetchone()

    cursor.execute("SELECT id, pageName, imageNgo FROM ngo WHERE registeringUser = %s", (user[2],))
    ngo = cursor.fetchone()
    user_has_ngo = ngo is not None

    cursor.execute("""
        SELECT post.id, post.description, post.image, post.createdPost, ngo.imageNgo, ngo.pageName,
               (SELECT COUNT(*) FROM `enjoy` WHERE `enjoy`.`postId` = post.id) AS like_count,
               (SELECT COUNT(*) FROM `enjoy` WHERE `enjoy`.`postId` = post.id AND `enjoy`.`userId` = %s) AS user_liked
        FROM post
        INNER JOIN ngo ON post.author = ngo.pageName
    """, (id,))
    posts = cursor.fetchall()

    comments = {}
    for post in posts:
        cursor.execute("SELECT id, textComment, userName, userImg, createdComment FROM comment WHERE postid = %s", (post[0],))
        comments[post[0]] = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('feedUser.html', user=user, posts=posts, user_has_ngo=user_has_ngo, ngo=ngo, comments=comments)

@app.route('/profileUser/<int:id>')
def profileUser(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, fullName, userName, emailUser, phoneNumberUser, userImg FROM user WHERE id = %s", (id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('profileUser.html', user=user)

@app.route('/updateProfileUser', methods=['POST'])
def updateProfileUser():
    data = request.form
    user_id = data.get('id')
    fullName = data.get('fullName')
    userName = data.get('userName')
    emailUser = data.get('emailUser')
    phoneNumberUser = data.get('phoneNumberUser')
    userImg = data.get('userImg')

    db = get_db_connection()
    cursor = db.cursor()
    query = "UPDATE user SET fullName = %s, userName = %s, emailUser = %s, phoneNumberUser = %s, userImg = %s WHERE id = %s"
    values = (fullName, userName, emailUser, phoneNumberUser, userImg, user_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('profileUser', id=user_id))

@app.route('/profileNgo/<int:id>')
def profileNgo(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, cnpj, stateRegistration, corporateReason, emailNgo, phoneNumberNgo, physicalAddress, objectiveOfTheNgo, pageName, imageNgo, bgImageNgo FROM ngo WHERE id = %s", (id,))
    ngo = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('profileNgo.html', ngo=ngo)

@app.route('/updateProfileNgo', methods=['POST'])
def updateProfileNgo():
    data = request.form
    ngo_id = data.get('id')
    cnpj = data.get('cnpj')
    stateRegistration = data.get('stateRegistration')
    corporateReason = data.get('corporateReason')
    emailNgo = data.get('emailNgo')
    phoneNumberNgo = data.get('phoneNumberNgo')
    physicalAddress = data.get('physicalAddress')
    objectiveOfTheNgo = data.get('objectiveOfTheNgo')
    pageName = data.get('pageName')
    imageNgo = data.get('imageNgo')
    bgImageNgo = data.get('bgImageNgo')

    db = get_db_connection()
    cursor = db.cursor()
    query = """
        UPDATE ngo SET cnpj = %s, stateRegistration = %s, corporateReason = %s, emailNgo = %s, phoneNumberNgo = %s,
        physicalAddress = %s, objectiveOfTheNgo = %s, pageName = %s, imageNgo = %s, bgImageNgo = %s WHERE id = %s
    """
    values = (cnpj, stateRegistration, corporateReason, emailNgo, phoneNumberNgo, physicalAddress, objectiveOfTheNgo, pageName, imageNgo, bgImageNgo, ngo_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('feedNgo', ngo_id=ngo_id))

@app.route('/excluir-ngo/<int:id>', methods=['POST'])
def excluir_ngo(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM ngo WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('root'))

@app.route('/excluir-usuario/<int:id>', methods=['POST'])
def excluir_usuario(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM user WHERE id = %s", (id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('root'))

@app.route('/atualizar-usuario/<int:id>', methods=['GET'])
def atualizar_usuario(id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, fullName, userName, emailUser, phoneNumberUser, userImg FROM user WHERE id = %s", (id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template('atualizacao-usuario.html', user=user)

@app.route('/salvar-alteracao-usuario', methods=['POST'])
def salvar_alteracao_usuario():
    id = request.form['id']
    fullName = request.form['fullName']
    userName = request.form['userName']
    emailUser = request.form['emailUser']
    phoneNumberUser = request.form['phoneNumberUser']
    userImg = request.form['userImg']

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE user SET fullName = %s, userName = %s, emailUser = %s, phoneNumberUser = %s, userImg = %s
        WHERE id = %s
    """, (fullName, userName, emailUser, phoneNumberUser, userImg, id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('feed_user', id=id))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, fullName, userName, userImg FROM user WHERE fullName LIKE %s OR userName LIKE %s", ('%' + query + '%', '%' + query + '%'))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('searchResults.html', results=results)

@app.route('/registerNgo', methods=['GET', 'POST'])
def registerNgo():
    if request.method == 'POST':
        data = request.form
        cnpj = data.get('cnpj')
        stateRegistration = data.get('stateRegistration')
        corporateReason = data.get('corporateReason')
        emailNgo = data.get('emailNgo')
        phoneNumberNgo = data.get('phoneNumberNgo')
        physicalAddress = data.get('physicalAddress')
        objectiveOfTheNgo = data.get('objectiveOfTheNgo')
        pageName = data.get('pageName')
        imageNgo = data.get('imageNgo')
        bgImageNgo = data.get('bgImageNgo')
        registeringUser = data.get('registeringUser')

        print("registeringUser:", registeringUser)  # Debug: Imprimir o valor de registeringUser

        # Verificar se o registeringUser existe na tabela user
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT userName FROM user WHERE userName = %s", (registeringUser,))
        user = cursor.fetchone()

        if user is None:
            cursor.close()
            db.close()
            print("Usuário registrador não encontrado.")  # Debug: Imprimir mensagem de erro
            return jsonify({"error": "Usuário registrador não encontrado."}), 400

        try:
            query = """
            INSERT INTO ngo (cnpj, stateRegistration, corporateReason, emailNgo, phoneNumberNgo, physicalAddress, objectiveOfTheNgo, pageName, imageNgo, bgImageNgo, registeringUser)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (cnpj, stateRegistration, corporateReason, emailNgo, phoneNumberNgo, physicalAddress, objectiveOfTheNgo, pageName, imageNgo, bgImageNgo, registeringUser)
            cursor.execute(query, values)
            db.commit()
            
            # Recuperar o ID da ONG recém-criada
            ngo_id = cursor.lastrowid
            
            cursor.close()
            db.close()
            
            # Redirecionar para feedNgo com o id da ONG recém-criada
            return redirect(url_for('feedNgo', ngo_id=ngo_id))
        except mysql.connector.Error as err:
            cursor.close()
            db.close()
            print("Erro do MySQL:", str(err))  # Debug: Imprimir o erro do MySQL
            return jsonify({"error": str(err)}), 500
    
    return render_template('registerNgo.html')

@app.route('/success')
def success():
    return "ONG registrada com sucesso!"

@app.route('/feedNgo/<int:ngo_id>')
def feedNgo(ngo_id):
    db = get_db_connection()
    cursor = db.cursor()

    # Obter informações da ONG
    cursor.execute("SELECT id, pageName, imageNgo FROM ngo WHERE id = %s", (ngo_id,))
    ngo = cursor.fetchone()

    if ngo is None:
        cursor.close()
        db.close()
        return "ONG não encontrada", 404

    print("ONG encontrada:", ngo)  # Debug: Imprimir dados da ONG

    # Obter posts da ONG
    cursor.execute("""
        SELECT post.id, post.profilePicture, post.author, post.description, post.image, post.createdPost 
        FROM post 
        WHERE post.author = %s
    """, (ngo[1],))  # Comparando o campo author com pageName

    posts = cursor.fetchall()
    print("Posts encontrados:", posts)  # Debug: Imprimir os posts encontrados

    for i in range(len(posts)):
        post = list(posts[i])
        post[5] = datetime.strptime(post[5], '%Y-%m-%d %H:%M:%S')
        posts[i] = post

    cursor.close()
    db.close()
    return render_template('feedNgo.html', ngo=ngo, posts=posts)
    
def time_ago(value):
    now = datetime.now()
    diff = now - value

    seconds = diff.total_seconds()
    periods = [
        (seconds // 31536000, "ano", "anos"),
        (seconds // 2592000, "mês", "meses"),
        (seconds // 604800, "semana", "semanas"),
        (seconds // 86400, "dia", "dias"),
        (seconds // 3600, "hora", "horas"),
        (seconds // 60, "minuto", "minutos"),
        (seconds, "segundo", "segundos"),
    ]

    for period, singular, plural in periods:
        if period > 0:
            return f"{int(period)} {singular if period == 1 else plural} atrás"
    return "agora mesmo"

app.jinja_env.filters['time_ago'] = time_ago

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/createPost', methods=['POST'])
def create_post():
    data = request.json
    profilePicture = data.get('profilePicture')
    author = data.get('author')
    description = data.get('description')
    image = data.get('image')
    post_id = data.get('id')
    createdPost = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not (profilePicture and author and description and image):
        return jsonify({"msg": "Todos os campos são obrigatórios"}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"msg": "Erro ao conectar ao banco de dados"}), 500

    cursor = db.cursor()
    query = """
    INSERT INTO post (profilePicture, author, description, image, createdPost, id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (profilePicture, author, description, image, createdPost, post_id)
    try:
        cursor.execute(query, values)
        db.commit()
        return jsonify({"msg": "Post criado com sucesso"}), 200
    except mysql.connector.Error as err:
        return jsonify({"msg": f"Erro ao criar post: {err}"}), 500
    finally:
        cursor.close()
        db.close()

import os
from flask import current_app

@app.route('/uploadImage', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"msg": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "Nenhum arquivo selecionado"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        try:
            file.save(file_path)
            print(f"Arquivo salvo em: {file_path}")  # Log de debug
            return jsonify({"msg": "Imagem carregada com sucesso", "filename": filename, "file_path": file_path}), 200
        except Exception as e:
            print(f"Erro ao salvar imagem: {str(e)}")  # Log de erro
            return jsonify({"msg": f"Erro ao salvar imagem: {str(e)}"}), 500
    return jsonify({"msg": "Formato de arquivo não permitido"}), 400

@app.route('/editPost/<int:post_id>', methods=['GET', 'POST'])
def editPost(post_id):
    db = get_db_connection()
    cursor = db.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT id, description, image, author FROM post WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        cursor.close()
        db.close()
        if post:
            # Vamos buscar o ngo_id baseado no autor
            ngo_id = get_ngo_id_by_author(post[3])
            return render_template('editPost.html', post=post, ngo_id=ngo_id)
        else:
            return "Post não encontrado", 404

    elif request.method == 'POST':
        description = request.form['description']
        image = request.form.get('image', None)
        ngo_id = request.form['ngo_id']

        if not description:
            return jsonify({"msg": "Descrição é obrigatória"}), 400

        query = "UPDATE post SET description = %s"
        values = [description]

        if image:
            query += ", image = %s"
            values.append(image)

        query += " WHERE id = %s"
        values.append(post_id)

        try:
            cursor.execute(query, tuple(values))
            db.commit()
            return redirect(url_for('feedNgo', ngo_id=ngo_id))
        except mysql.connector.Error as err:
            return jsonify({"msg": f"Erro ao editar post: {err}"}), 500
        finally:
            cursor.close()
            db.close()

def get_ngo_id_by_author(author):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM ngo WHERE pageName = %s", (author,))
    ngo_id = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return ngo_id

@app.route('/deletePost/<int:post_id>', methods=['POST'])
def deletePost(post_id):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM post WHERE id = %s", (post_id,))
        db.commit()
        return redirect(url_for('feedNgo', ngo_id=request.form['ngo_id']))
    except mysql.connector.Error as err:
        return jsonify({"msg": f"Erro ao excluir post: {err}"}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/toggleLike', methods=['POST'])
def toggle_like():
    data = request.json
    post_id = data.get('post_id')
    user_id = data.get('user_id')
    
    db = get_db_connection()
    cursor = db.cursor()

    try:
        # Verificar se o usuário já curtiu o post
        cursor.execute("SELECT * FROM `enjoy` WHERE postId = %s AND userId = %s", (post_id, user_id))
        like = cursor.fetchone()

        if like:
            # Se já curtiu, remover curtida
            cursor.execute("DELETE FROM `enjoy` WHERE postId = %s AND userId = %s", (post_id, user_id))
            db.commit()
            liked = False
        else:
            # Se não curtiu, adicionar curtida
            cursor.execute("INSERT INTO `enjoy` (id, postId, userId) VALUES (%s, %s, %s)", (str(uuid.uuid4()), post_id, user_id))
            db.commit()
            liked = True

        # Contar número de curtidas do post
        cursor.execute("SELECT COUNT(*) FROM `enjoy` WHERE postId = %s", (post_id,))
        like_count = cursor.fetchone()[0]
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()
    
    return jsonify({'liked': liked, 'like_count': like_count})
        
@app.route('/createComment', methods=['POST'])
def create_comment():
    data = request.form
    textComment = data.get('textComment')
    userName = data.get('userName')
    userImg = data.get('userImg')
    postid = data.get('postid')
    createdComment = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not (textComment and userName and postid):
        return jsonify({"msg": "Todos os campos são obrigatórios"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    query = """
    INSERT INTO comment (textComment, userName, userImg, postid, createdComment)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (textComment, userName, userImg, postid, createdComment)
    try:
        cursor.execute(query, values)
        db.commit()
        return jsonify({"msg": "Comentário criado com sucesso"})
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"msg": f"Erro ao criar comentário: {err}"}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/editComment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    db = get_db_connection()
    if not db:
        return "Erro ao conectar ao banco de dados", 500
    
    cursor = db.cursor()

    if request.method == 'GET':
        try:
            cursor.execute("SELECT id, textComment, userName FROM comment WHERE id = %s", (comment_id,))
            comment = cursor.fetchone()
            if comment:
                # Obter o userId baseado no userName
                cursor.execute("SELECT id FROM user WHERE userName = %s", (comment[2],))
                user = cursor.fetchone()
                if user:
                    return render_template('editComment.html', comment=comment, user=user)
                else:
                    return "Usuário não encontrado", 404
            else:
                return "Comentário não encontrado", 404
        except mysql.connector.Error as err:
            return f"Erro ao executar a consulta: {err}", 500
        finally:
            cursor.close()
            db.close()

    elif request.method == 'POST':
        textComment = request.form['textComment']
        userName = request.form['userName']
        userId = request.form['userId']  # Capture userId from the form

        if not textComment:
            return jsonify({"msg": "O texto do comentário é obrigatório"}), 400

        query = "UPDATE comment SET textComment = %s WHERE id = %s AND userName = %s"
        values = (textComment, comment_id, userName)

        try:
            cursor.execute(query, values)
            db.commit()
            return redirect(url_for('feed_user', id=userId))  # Redirect to the user's feed
        except mysql.connector.Error as err:
            return jsonify({"msg": f"Erro ao editar comentário: {err}"}), 500
        finally:
            cursor.close()
            db.close()

@app.route('/deleteComment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM comment WHERE id = %s", (comment_id,))
        db.commit()
        return jsonify({"msg": "Comentário excluído com sucesso"}), 200
    except mysql.connector.Error as err:
        return jsonify({"msg": f"Erro ao excluir comentário: {err}"}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/accountNgo/<int:user_id>/<int:ngo_id>')
def accountNgo(user_id, ngo_id):
    db = get_db_connection()
    cursor = db.cursor()

    # Obter informações da ONG
    cursor.execute("SELECT id, pageName, imageNgo FROM ngo WHERE id = %s", (ngo_id,))
    ngo = cursor.fetchone()

    if ngo is None:
        cursor.close()
        db.close()
        return "ONG não encontrada", 404

    print("ONG encontrada:", ngo)  # Debug: Imprimir dados da ONG

    # Obter posts da ONG
    cursor.execute("""
        SELECT post.id, post.profilePicture, post.author, post.description, post.image, post.createdPost,
               (SELECT COUNT(*) FROM `enjoy` WHERE `enjoy`.`postId` = post.id) AS like_count
        FROM post 
        WHERE post.author = %s
    """, (ngo[1],))  # Comparando o campo author com pageName

    posts = cursor.fetchall()
    print("Posts encontrados:", posts)  # Debug: Imprimir os posts encontrados

    comments = {}
    for post in posts:
        cursor.execute("SELECT id, textComment, userName FROM comment WHERE postid = %s", (post[0],))
        comments[post[0]] = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('accountNgo.html', user_id=user_id, ngo=ngo, posts=posts, comments=comments)

@app.route('/accountNgoEnjoy/<int:user_id>', methods=['POST'])
def accountNgoEnjoy(user_id):
    data = request.get_json()
    post_id = data.get('post_id')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM enjoy WHERE postId = %s AND userId = %s", (post_id, user_id))
    enjoy_exists = cursor.fetchone()[0]

    if enjoy_exists:
        cursor.execute("DELETE FROM enjoy WHERE postId = %s AND userId = %s", (post_id, user_id))
        action = 'unliked'
    else:
        cursor.execute("INSERT INTO enjoy (postId, userId) VALUES (%s, %s)", (post_id, user_id))
        action = 'liked'

    db.commit()

    cursor.execute("SELECT COUNT(*) FROM enjoy WHERE postId = %s", (post_id,))
    like_count = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return jsonify(success=True, action=action, like_count=like_count)

@app.route('/accountNgoCreateComment', methods=['POST'])
def accountNgoCreateComment():
    post_id = request.form['postid']
    user_id = request.form['user_id']
    text_comment = request.form['textComment']
    created_comment = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("INSERT INTO comment (postId, textComment, createdComment) VALUES (%s, %s, %s)",
                   (post_id, text_comment, created_comment))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('accountNgo', user_id=user_id, ngo_id=post_id))

if __name__ == '__main__':
    app.run(debug=True)