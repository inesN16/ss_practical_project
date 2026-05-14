import functools
import pathlib
import os
import psycopg2
import flask
import os
import dotenv
from . import db
from . import utils
from werkzeug.utils import secure_filename
from flask_talisman import Talisman 

dotenv.load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "docdb")

UPLOAD_FOLDER = "uploads"

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )

def create_app():
    app = flask.Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # ESTAS LINHAS TÊM DE TER 4 ESPAÇOS DE AVANÇO
    Talisman(
        app,
        force_https=False,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self'",
            'style-src': "'self'",
        }
    )

    @app.after_request
    def remove_server_header(response):
        response.headers['Server'] = 'SecureServer'
        return response

    register_routes(app)
    return app

'''def get_documents_for_user(cur, owner_id):
    query = f"""
        SELECT id,title,filename,uploaded_at
        FROM documents
        WHERE owner_id=%s
        ORDER BY uploaded_at DESC
    """ % owner_id
    cur.execute(query)
    return cur.fetchall() '''

def get_documents_for_user(cur, owner_id):
    query = """
        SELECT id,title,filename,uploaded_at
        FROM documents
        WHERE owner_id=%s
        ORDER BY uploaded_at DESC
    """
    cur.execute(query, (owner_id,))
    return cur.fetchall()


def extract_metadata(filename):

    #cmd = utils.build("stat ", str(filename), " 2>&1")
    #---adicionei---
    cmd = utils.build("stat", str(filename))

    return utils.call(cmd)

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in flask.session:
            flask.flash("Please log in first.", "error")
            return flask.redirect(flask.url_for("login"))
        return fn(*args, **kwargs)

    return wrapper

def register_routes(app):

    @app.route("/")
    def index():
        if flask.session.get("user_id"):
            return flask.redirect(flask.url_for("documents_page"))
        return flask.redirect(flask.url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():

        if flask.request.method == "POST":
            username = flask.request.form.get("username", "")
            password = flask.request.form.get("password", "")

            conn = get_db()
            cur = conn.cursor()

            user = db.get_user_by_username(cur, username)

            cur.close()
            conn.close()

            is_admin = username == "admin"

            if user and (user[2] == password and not user[3]) or is_admin:
                flask.session.clear()
                flask.session["user_id"] = user[0] if username != "admin" else 1
                flask.session["username"] = user[1] if username != "admin" else username
                
                # NOVO REDIRECIONAMENTO SEGURO
                if username == "admin":
                    return flask.redirect(flask.url_for("admin_users"))
                else:
                    return flask.redirect(flask.url_for("documents_page"))


            flask.flash("Invalid credentials.", "error")

        return flask.render_template("login.html")

    @app.route("/logout")
    def logout():
        flask.session.clear()
        return flask.redirect(flask.url_for("login"))

    '''@app.route("/documents/<int:document_id>")
    def document_details(document_id):
        conn = get_db()
        cur = conn.cursor()

        # intentionally missing authorization check
        cur.execute(utils.prepare_query("""
            SELECT id, owner_id, title, filename, metadata
            FROM documents
            WHERE id = %s
            """,
            (document_id,)))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return "Document not found", 404

        document = {
            "id": row[0],
            "owner_id": row[1],
            "title": row[2],
            "filename": row[3],
            "metadata": row[4],
        }

        return flask.render_template("document_details.html", document=document)'''

    @app.route("/documents/<int:document_id>")
    @login_required 
    def document_details(document_id):
        
        user_id = flask.session.get("user_id")
        is_admin = flask.session.get("username") == "admin"

        conn = get_db()
        cur = conn.cursor()

        # 1. Procurar o documento e quem é o dono
        cur.execute("SELECT id, owner_id, title, filename, metadata FROM documents WHERE id = %s", (document_id,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return "Document not found", 404

        doc_owner_id = row[1]

        # 2. Verificar se foi partilhado com o utilizador atual
        cur.execute("SELECT 1 FROM document_shares WHERE document_id = %s AND shared_with = %s", (document_id, user_id))
        is_shared = cur.fetchone() is not None

        # 3. VALIDAÇÃO DE SEGURANÇA: Se não for dono, nem admin, nem tiver partilha... BLOQUEAR!
        if user_id != doc_owner_id and not is_admin and not is_shared:
            cur.close()
            conn.close()
            return "Acesso Negado: Não tem permissão para ver os detalhes deste documento.", 403

        # Se passou a validação, montamos o dicionário para o template
        document = {
            "id": row[0],
            "owner_id": row[1],
            "title": row[2],
            "filename": row[3],
            "metadata": row[4],
        }

        cur.close()
        conn.close()
        return flask.render_template("document_details.html", document=document)

    @app.route("/documents")
    @login_required
    def documents_page():

        if flask.session.get("username") == "admin":
            return flask.redirect(flask.url_for("admin_users"))
    
        requested_user_id = flask.request.args.get("user_id")
        current_user_id = flask.session.get("user_id")

        owner_id = requested_user_id or current_user_id
        #--adicionei---
        if requested_user_id and str(requested_user_id) != str(current_user_id):
            if flask.session.get("username") != "admin":
                owner_id = current_user_id
                flask.flash("Apenas pode ver os seus próprios documentos.", "error")
            else:
                owner_id = requested_user_id
        else:
            owner_id = current_user_id
    
        conn = get_db()
        cur = conn.cursor()

        docs = get_documents_for_user(cur, owner_id)

        cur.close()
        conn.close()

        documents = [
            {
                "id": d[0],
                "title": d[1],
                "filename": d[2],
                "uploaded_at": d[3],
            }
            for d in docs
        ]

        return flask.render_template(
            "documents.html",
            documents=documents,
            requested_user_id=owner_id,
            current_user_id=current_user_id,
            username=flask.session.get("username"),
        )

    @app.route("/documents/upload", methods=["POST"])
    @login_required
    def upload_document():

        if flask.session.get("username") == "admin":
            return "Operação não permitida para administradores", 403
    
        user_id = flask.session.get("user_id")
        title = flask.request.form.get("title", "Untitled")
        uploaded_file = flask.request.files.get("document")

        if not uploaded_file or uploaded_file.filename == "":
            flask.flash("Please choose a file.", "error")
            return flask.redirect(flask.url_for("documents_page"))

        upload_folder = BASE_DIR / app.config["UPLOAD_FOLDER"]
        upload_folder.mkdir(parents=True, exist_ok=True)

        filename = utils.sanitize_filename(uploaded_file.filename)
        destination = upload_folder / uploaded_file.filename
        uploaded_file.save(destination)
        metadata = extract_metadata(destination)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO documents (owner_id, title, filename, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, title, uploaded_file.filename, metadata),
        )
        conn.commit()

        cur.close()
        conn.close()

        return flask.redirect(flask.url_for("documents_page", uploaded=title))

    @app.route("/health")
    def health():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return {"status": "ok"}, 200
        except Exception:
            return {"status": "error"}, 500


    # ------------------------------------------------------------------
    # Planned / Not Yet Implemented Endpoints
    #
    # The following routes are part of the intended system interface and
    # are not implemented in the baseline version of the application.
    #
    # The expected behavior of these endpoints is summarized below.
    #
    # Document operations
    #
    #   GET  /documents/<id>/download
    #       Download the specified document.
    #       Success: returns file contents (HTTP 200)
    #       Errors: 404 if the document does not exist
    #
    #   POST /documents/<id>/share
    #       Share a document with another user.
    #       Form parameter:
    #           shared_with  -> target user id
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    # Shared documents
    #
    #   GET  /shared
    #       Display documents that were shared with the current user.
    #       Success: HTTP 200
    #
    #   GET  /shared/<id>/download
    #       Download a document that was shared with the current user.
    #       Success: returns file contents (HTTP 200)
    #
    # Administration
    #
    #   GET  /admin/users
    #       Display a list of users in the system.
    #       Success: HTTP 200
    #
    #   POST /admin/users/<id>/enable
    #       Enable a user account.
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    #   POST /admin/users/<id>/disable
    #       Disable a user account.
    #       Success: redirect or confirmation (HTTP 302 or 200)
    #
    # ------------------------------------------------------------------


    

    # --- DOWNLOAD ---

    @app.route("/documents/<int:document_id>/download")
    @login_required
    def download_document(document_id):
        user_id = flask.session.get("user_id")
        is_admin = flask.session.get("username") == "admin"
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT owner_id, filename FROM documents WHERE id = %s", (document_id,))
        row = cur.fetchone()
        
        if not row: return "404", 404
        owner_id, filename = row

        # VERIFICAÇÃO DE ACESSO: É o dono? É o admin? Ou foi partilhado com ele?
        cur.execute("SELECT 1 FROM document_shares WHERE document_id = %s AND shared_with = %s", (document_id, user_id))
        is_shared = cur.fetchone() is not None

        if user_id != owner_id and not is_admin and not is_shared:
            cur.close()
            conn.close()
            return "Acesso Negado", 403

        cur.close()
        conn.close()
        upload_folder = BASE_DIR / app.config["UPLOAD_FOLDER"]
        return flask.send_from_directory(directory=upload_folder, path=filename, as_attachment=True)


    # --- PARTILHA (SHARE) ---
    @app.route("/documents/<int:document_id>/share", methods=["POST"])
    @login_required
    def share_document(document_id):

        shared_with_id = flask.request.form.get("shared_with")
        owner_id = flask.session.get("user_id")

        conn = get_db()
        cur = conn.cursor()

        # Primeiro verificar se o documento pertence mesmo a quem está a partilhar
        cur.execute("SELECT id FROM documents WHERE id = %s AND owner_id = %s", (document_id, owner_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return "Operação não autorizada", 403

        # Inserir na tabela de partilhas (precisas de ter esta tabela na BD)
        try:
            cur.execute("INSERT INTO document_shares (document_id, shared_with) VALUES (%s, %s)", 
                        (document_id, shared_with_id))
            conn.commit()
        except Exception:
            cur.close()
            conn.close()
            return "Erro ao partilhar", 500
        
        return flask.redirect(flask.url_for("documents_page"))


    @app.route("/admin/users")
    @login_required
    def admin_users():

        # SEGURANÇA: Só o admin entra
        if flask.session.get("username") != "admin":
            return "Acesso Restrito", 403

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, is_disabled FROM users ORDER BY id ASC")
        users = cur.fetchall()
        
        # Precisas de criar o admin_users.html como falamos antes
        return flask.render_template("admin_users.html", users=users)


    @app.route("/admin/users/<int:user_id>/enable", methods=["POST"])
    @login_required
    def enable_user(user_id):
        if flask.session.get("username") != "admin": return "403", 403
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_disabled = FALSE WHERE id = %s", (user_id,))
        conn.commit()
        return flask.redirect(flask.url_for("admin_users"))




    @app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
    @login_required
    def disable_user(user_id):
        if flask.session.get("username") != "admin": 
            return "403", 403
        
        # SEGURANÇA EXTRA: Impedir que o admin (ID 1) se desative a si próprio
        if user_id == 1:
            flask.flash("Não é permitido desativar a conta principal de administrador.", "error")
            return flask.redirect(flask.url_for("admin_users"))
            
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_disabled = TRUE WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return flask.redirect(flask.url_for("admin_users"))
    


    # --- LISTAR DOCUMENTOS PARTILHADOS ---
    @app.route("/documents/shared")
    @login_required
    def shared_with_me():
        user_id = flask.session.get("user_id")
        conn = get_db()
        cur = conn.cursor()
        
        # Query que junta a tabela de partilhas com a de documentos e utilizadores
        cur.execute("""
            SELECT d.id, d.title, u.username as owner_name, d.filename
            FROM documents d
            JOIN document_shares s ON d.id = s.document_id
            JOIN users u ON d.owner_id = u.id
            WHERE s.shared_with = %s
        """, (user_id,))
        
        shared_docs = cur.fetchall()
        cur.close()
        conn.close()
        return flask.render_template("shared.html", shared_documents=shared_docs)
    
    @app.route("/documents/shared/<int:document_id>/download")
    @login_required
    def download_shared_document(document_id):
        return download_document(document_id)