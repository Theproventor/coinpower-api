from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import json

app = Flask(__name__)
CORS(app, origins="*")

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "JanusUrbanus@e1097")

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, title TEXT NOT NULL, cat TEXT DEFAULT 'MARKT', excerpt TEXT, content TEXT, img TEXT, date TEXT, created_at TIMESTAMP DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT NOT NULL, description TEXT, price NUMERIC(10,2), img TEXT, cat TEXT, created_at TIMESTAMP DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, name TEXT, email TEXT, coin TEXT, items JSONB, total NUMERIC(10,2), status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS signal (id SERIAL PRIMARY KEY, signal TEXT DEFAULT 'BULLISH', description TEXT, updated_at TIMESTAMP DEFAULT NOW())")
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def health():
    return jsonify({'status': 'ok'})

@app.route('/articles', methods=['GET'])
def get_articles():
    try:
        limit = request.args.get('limit', 50)
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT %s", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles/<int:aid>', methods=['GET'])
def get_article(aid):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM articles WHERE id=%s", (aid,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return jsonify(dict(row)) if row else (jsonify({'error':'not found'}), 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles', methods=['POST'])
def create_article():
    try:
        d = request.json
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO articles (title,cat,excerpt,content,img,date) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
            (d.get('title'),d.get('cat','MARKT'),d.get('excerpt'),d.get('content'),d.get('img'),d.get('date')))
        row = dict(cur.fetchone())
        conn.commit(); cur.close(); conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/articles/<int:aid>', methods=['DELETE'])
def delete_article(aid):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM articles WHERE id=%s", (aid,))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'deleted': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['GET'])
def get_products():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM products ORDER BY created_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    try:
        d = request.json
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO products (name,description,price,img,cat) VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (d.get('name'),d.get('description'),d.get('price'),d.get('img'),d.get('cat')))
        row = dict(cur.fetchone())
        conn.commit(); cur.close(); conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id=%s", (pid,))
        conn.commit(); cur.close(); conn.close()
        return jsonify({'deleted': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        d = request.json
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("INSERT INTO orders (name,email,coin,items,total) VALUES (%s,%s,%s,%s,%s) RETURNING *",
            (d.get('name'),d.get('email'),d.get('coin'),json.dumps(d.get('items',[])),d.get('total')))
        row = dict(cur.fetchone())
        conn.commit(); cur.close(); conn.close()
        return jsonify(row), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/signal', methods=['GET'])
def get_signal():
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM signal ORDER BY updated_at DESC LIMIT 1")
        row = cur.fetchone()
        cur.close(); conn.close()
        return jsonify(dict(row)) if row else jsonify({'signal':'BULLISH','description':''})
    except:
        return jsonify({'signal':'BULLISH','description':''})

@app.route('/signal', methods=['POST'])
def update_signal():
    try:
        d = request.json
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("DELETE FROM signal")
        cur.execute("INSERT INTO signal (signal,description) VALUES (%s,%s) RETURNING *",
            (d.get('signal','BULLISH'),d.get('description','')))
        row = dict(cur.fetchone())
        conn.commit(); cur.close(); conn.close()
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
