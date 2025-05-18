from flask import Flask, request, render_template, redirect
import oracledb

oracledb.init_oracle_client(lib_dir=r"C:\\Program Files\\Oracle\\instantclient_23_7")
app = Flask(__name__)

conn = oracledb.connect(
    user="hr",
    password="hr",
    dsn="DESKTOP-60PQE0I:1521/XE"
)

# ─────────────────────────────────────────────
@app.route('/')
def index():
    with conn.cursor() as cur:
        # kitap listesi
        cur.execute("""
            SELECT b.bookID, b.title,
                   a.authorName||' '||a.authorSurname,
                   b.price, b.genre, b.stock, b.yearofpublish,
                   w.workerName
            FROM   books b
            JOIN   authors  a ON b.authorID = a.authorID
            LEFT  JOIN workers w ON b.workerID = w.workerID
            ORDER  BY b.bookID
        """)
        books = cur.fetchall()

        cur.execute("SELECT * FROM authors")
        authors = cur.fetchall()

        cur.execute("SELECT * FROM workers")
        workers = cur.fetchall()

        # 🔸 TÜM siparişler  (INNER yerine LEFT JOIN, filtre yok)
        cur.execute("""
            SELECT o.orderID,
                   c.customerName||' '||c.customerSurname,
                   TO_CHAR(o.orderDate,'YYYY-MM-DD'),
                   o.totalPrice,
                   w.workerName            -- NULL ise atanmamış
            FROM   orders   o
            JOIN   customers c ON o.custID = c.customerID
            LEFT  JOIN workers  w ON o.workID = w.workerID
            ORDER  BY o.orderID
        """)
        orders = cur.fetchall()

        # sipariş-kitap detayları
        order_details = {}
        for ord in orders:
            cur.execute("""
                SELECT b.title, ob.quantity
                FROM   order_books ob
                JOIN   books b ON ob.bookID = b.bookID
                WHERE  ob.orderID = :1
            """, (ord[0],))
            order_details[ord[0]] = cur.fetchall()

    return render_template(
        'index.html',
        books=books,
        authors=authors,
        workers=workers,
        orders=orders,
        order_details=order_details
    )

# ---------- kitap / yazar / çalışan ekleme ve worker assign ----------
@app.route('/add', methods=['POST'])
def add_book():
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO books (bookID, title, authorID, price, genre, stock, workerID, yearofpublish)
            VALUES (books_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7)
        """, (request.form['title'],
              request.form['authorID'],
              request.form['price'],
              request.form['genre'],
              request.form['stock'],
              request.form['workerID'],
              request.form['yearofpublish']))
    conn.commit()
    return redirect('/')

@app.route('/add_worker', methods=['POST'])
def add_worker():
    with conn.cursor() as cur:
        cur.execute("SELECT NVL(MAX(workerID),0)+1 FROM workers")
        new_id = cur.fetchone()[0]
        cur.execute("INSERT INTO workers VALUES (:1,:2,:3)",
                    (new_id, request.form['workerName'], request.form['position']))
    conn.commit()
    return redirect('/')

@app.route('/unassign_worker/<int:orderID>', methods=['POST'])
def unassign_worker(orderID):
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET workID = NULL WHERE orderID = :1", (orderID,))
    conn.commit()
    return redirect('/')

@app.route('/add_author', methods=['POST'])
def add_author():
    with conn.cursor() as cur:
        cur.execute("SELECT NVL(MAX(authorID),0)+1 FROM authors")
        new_id = cur.fetchone()[0]
        cur.execute("INSERT INTO authors VALUES (:1,:2,:3)",
                    (new_id, request.form['authorName'], request.form['authorSurname']))
    conn.commit()
    return redirect('/')

@app.route('/assign_worker/<int:orderID>', methods=['POST'])
def assign_worker(orderID):
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET workID=:1 WHERE orderID=:2",
                    (request.form['workerID'], orderID))
    conn.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
