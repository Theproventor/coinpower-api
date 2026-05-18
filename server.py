from flask import Flask, request, jsonify
from flask_cors import CORS
import pg8000.native
import os
import json
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app, origins="*")

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "JanusUrbanus@e1097")

def get_db():
    u = urlparse(DATABASE_URL)
    return pg8000.native.Connection(
        host=u.hostname,
        port=u.port or 5432,
        user=u.username,
        password=u.password,
        database=u.path.lstrip("/"),
        ssl_context=True,
    )

def init_db():
    conn = get_db()
    conn.run("CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, title TEXT NOT NULL, cat TEXT DEFAULT 'MARKT', excerpt TEXT, content TEXT, img TEXT, date TEXT, created_at TIMESTAMP DEFAULT NOW())")
    conn.run("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT NOT NULL, description TEXT, price NUMERIC(10,2), img TEXT, cat TEXT, created_at TIMESTAMP DEFAULT NOW())")
    conn.run("CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, name TEXT, email TEXT, coin TEXT, items JSONB, total NUMERIC(10,2), status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())")
    conn.run("CREATE TABLE IF NOT EXISTS signal (id SERIAL PRIMARY KEY, signal TEXT DEFAULT 'BULLISH', description TEXT, updated_at TIMESTAMP DEFAULT NOW())")
    conn.close()

@app.route('/')
def health():
    return jsonify({'status': 'ok'})

def rows_as_dicts(conn, results):
    """Convert pg8000 row tuples to dicts using column metadata."""
    cols = [c["name"] for c in conn.columns]
    return [dict(zip(cols, row)) for row in results]

@app.route('/articles', methods=['GET'])
def get_articles():
    try:
        limit = int(request.args.get('limit', 50))
        conn = get_db()
        results = conn.run("SELECT * FROM articles ORDER BY created_at DESC LIMIT :limit", limit=limit)
        rows = rows_as_dicts(conn, results)
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles/<int:aid>', methods=['GET'])
def get_article(aid):
    try:
        conn = get_db()
        results = conn.run("SELECT * FROM articles WHERE id=:aid", aid=aid)
        rows = rows_as_dicts(conn, results)
        conn.close()
        return jsonify(rows[0]) if rows else (jsonify({'error': 'not found'}), 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles', methods=['POST'])
def create_article():
    try:
        d = request.json
        conn = get_db()
        results = conn.run(
            "INSERT INTO articles (title,cat,excerpt,content,img,date) VALUES (:title,:cat,:excerpt,:content,:img,:date) RETURNING *",
            title=d.get('title'), cat=d.get('cat', 'MARKT'), excerpt=d.get('excerpt'),
            content=d.get('content'), img=d.get('img'), date=d.get('date')
        )
        row = rows_as_dicts(conn, results)[0]
        conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles/<int:aid>', methods=['DELETE'])
def delete_article(aid):
    try:
        conn = get_db()
        conn.run("DELETE FROM articles WHERE id=:aid", aid=aid)
        conn.close()
        return jsonify({'deleted': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['GET'])
def get_products():
    try:
        conn = get_db()
        results = conn.run("SELECT * FROM products ORDER BY created_at DESC")
        rows = rows_as_dicts(conn, results)
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    try:
        d = request.json
        conn = get_db()
        results = conn.run(
            "INSERT INTO products (name,description,price,img,cat) VALUES (:name,:description,:price,:img,:cat) RETURNING *",
            name=d.get('name'), description=d.get('description'), price=d.get('price'),
            img=d.get('img'), cat=d.get('cat')
        )
        row = rows_as_dicts(conn, results)[0]
        conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    try:
        conn = get_db()
        conn.run("DELETE FROM products WHERE id=:pid", pid=pid)
        conn.close()
        return jsonify({'deleted': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        conn = get_db()
        results = conn.run("SELECT * FROM orders ORDER BY created_at DESC")
        rows = rows_as_dicts(conn, results)
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        d = request.json
        conn = get_db()
        results = conn.run(
            "INSERT INTO orders (name,email,coin,items,total) VALUES (:name,:email,:coin,:items,:total) RETURNING *",
            name=d.get('name'), email=d.get('email'), coin=d.get('coin'),
            items=json.dumps(d.get('items', [])), total=d.get('total')
        )
        row = rows_as_dicts(conn, results)[0]
        conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/signal', methods=['GET'])
def get_signal():
    try:
        conn = get_db()
        results = conn.run("SELECT * FROM signal ORDER BY updated_at DESC LIMIT 1")
        rows = rows_as_dicts(conn, results)
        conn.close()
        return jsonify(rows[0]) if rows else jsonify({'signal': 'BULLISH', 'description': ''})
    except:
        return jsonify({'signal': 'BULLISH', 'description': ''})

@app.route('/signal', methods=['POST'])
def update_signal():
    try:
        d = request.json
        conn = get_db()
        conn.run("DELETE FROM signal")
        results = conn.run(
            "INSERT INTO signal (signal,description) VALUES (:signal,:description) RETURNING *",
            signal=d.get('signal', 'BULLISH'), description=d.get('description', '')
        )
        row = rows_as_dicts(conn, results)[0]
        conn.close()
        return jsonify(row)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/login', methods=['POST'])
def admin_login():
    d = request.json
    if d.get('password') == ADMIN_PASSWORD:
        return jsonify({'token':'admin-token-2026','role':'admin'})
    return jsonify({'error':'Wrong password'}), 401

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
