import datetime
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import sqlite3
from datetime import datetime

app = Flask(__name__) # __name__ 代表目前執行的模組
db_name = 'mydb.db'  # 資料庫預設名稱

def get_db_connection():
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")  # 主畫面
def index():
    #取得所有資料
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id,model,price FROM products ORDER by random() LIMIT 3")
    member = cursor.fetchall()
    cursor.close()
    conn.close()
    data = []
    for row in member:
        data.append({
            "product_id": str(row[0]),
            "name": row[1],
            "price": row[2],
        })
    #確認是否登入帳號
    account_number = request.cookies.get('account_number')
    return render_template('index.html', data=data, account_number=account_number)

@app.route('/exhibit', methods=['GET'])  # 展示商品
def exhibit():
    #取得資料
    category = request.args.get('category')
    brand = request.args.get('brand', '')

    # 取得資料
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    if category:
        if brand:
            cursor.execute("SELECT product_id, model, price FROM products WHERE category=? AND brand=?", (category, brand))
        else:
            cursor.execute("SELECT product_id, model, price FROM products WHERE category=?", (category,))
    else:
        cursor.execute("SELECT product_id,model,price FROM products ORDER by random() LIMIT 3")
    product = cursor.fetchall()
    cursor.close()
    conn.close()
    data = []
    for row in product:
        data.append({
            "product_id": str(row[0]),
            "model": row[1],
            "price": row[2],
        })
    return render_template('exhibit.html', data=data)


@app.route('/login', methods=['GET', 'POST'])  # 登入畫面
def login():
    if request.method == 'POST':
        account_number = request.form['account_number']  # 輸入帳號
        password = request.form['password']  # 輸入密碼

        # 連接資料庫
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE account_number=? AND password=?",(account_number, password))
        member = cursor.fetchall()
        cursor.close()
        conn.close()

        if member:
            response = make_response(redirect(url_for('index')))
            response.set_cookie('account_number', str(account_number))  # 儲存帳號
            return response  # 登入成功
        else:
            return render_template('login.html', error_message="請輸入正確的帳號密碼！")
    else:
        if request.cookies.get('account_number'):
            return redirect(url_for('index'))  # 已登入
        else:
            return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])  # 註冊帳號
def register():
    if request.method == 'POST':
        member = {
            'account_number': request.form['account_number'],
            'password': request.form['password'],
            'email': request.form['email'],
            'username': request.form['username'],
            'phone_number': request.form['phone_number'],
            'address': request.form['address'],
            'date_of_birth': request.form['date_of_birth'],
            'administrator': 'false'
        }

        # 連接資料庫
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 檢查帳號是否已存在
        cursor.execute("SELECT * FROM members WHERE account_number = ?", (member['account_number'],))
        existing_account = cursor.fetchone()

        # 檢查電子郵件是否已存在
        cursor.execute("SELECT * FROM members WHERE email = ?", (member['email'],))
        existing_email = cursor.fetchone()

        if existing_account:
            error_message = "帳號已存在，請使用其他帳號"
        elif existing_email:
            error_message = "電子郵件已存在，請使用其他電子郵件"
        else:
            # 如果帳號和電子郵件都不存在，則插入新會員資料
            cursor.execute("INSERT INTO members VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(member.values()))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        cursor.close()
        conn.close()
        return render_template('register.html', error_message=error_message, form_data=member)
    else:
        if request.cookies.get('account_number'):
            return redirect(url_for('index'))  # 已登入
        else:
            return render_template('register.html', form_data={})

@app.route('/member', methods=['GET'])  # 會員中心
def member():
    if request.cookies.get('account_number'):  # 檢查是否登入
        # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT account_number,administrator FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchall()[0]
        data = {
            "account_number": str(member[0]),
            "administrator": member[1]
        }
        cursor.close()
        conn.close()
        return render_template('member.html',administrator=(lambda x: x if x == 'true' else None)(data['administrator']))
    else:
        return render_template('login.html')  # 跳轉到登入畫面

@app.route('/member_info')  # 顯示會員資料
def member_info():
    if request.cookies.get('account_number'):  # 檢查是否登入
    # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchall()[0]
        data = {
            "account_number": str(member[0]),
            "email": member[2],
            "username": member[3],
            "phone_number": member[4],
            "address": member[5],
            "date_of_birth": member[6],
            "administrator": member[7],
        }
        cursor.close()
        conn.close()
        return render_template('member_info.html', member=data)
    else:
        return render_template('login.html')  # 跳轉到登入畫面

@app.route('/member_edit', methods=['GET', 'POST'])  # 變更會員資料
def member_edit():
    if request.cookies.get('account_number'):  # 檢查是否登入
        success=''
        if request.method == 'POST':
            password = request.form['password']
            username = request.form['username']
            email = request.form['email']
            phone_number = request.form['phone_number']
            address = request.form['address']
            date_of_birth = request.form['date_of_birth']

            # 連接資料庫，更新資料
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("UPDATE members SET password=?,email=?,username=?,phone_number=?,address=?,date_of_birth=? WHERE account_number=?", (password, email, username, phone_number, address, date_of_birth, request.cookies.get('account_number')))
            conn.commit()
            cursor.close()
            conn.close()
            success = '變更資料成功！'

        # 連接資料庫
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchall()[0]
        data = {
            "account_number": member[0],
            "password": member[1],
            "email": member[2],
            "username": member[3],
            "phone_number": member[4],
            "address": member[5],
            "date_of_birth": member[6],
        }
        cursor.close()
        conn.close()
        return render_template('member_edit.html', member=data, success=success)
    else:
        return render_template('login.html')  # 跳轉到登入畫面

@app.route('/order', methods=['GET', 'POST'])  # 訂單查詢
def order():
    if request.cookies.get('account_number'):
        # 連接資料庫
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 基本查詢語句
        query = "SELECT * FROM orders WHERE customer_id=?"
        params = [request.cookies.get('account_number')]

        # 檢查查詢條件並添加到查詢語句中
        if request.method == 'POST':
            order_number = request.form.get('orderNumber')
            order_date = request.form.get('orderDate')

            if order_number:
                query += " AND order_id=?"
                params.append(order_number)
            if order_date:
                query += " AND order_date=?"
                params.append(order_date)

        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('order.html', data=data)
    else:
        return render_template('login.html')  # 跳轉到登入畫面


@app.route("/cart", methods=['GET', 'POST'])  # 購物車
def cart():
    message = request.args.get('message', '')
    if request.method == 'POST':

        cart = request.cookies.get('cart')
        if cart:
            cart = json.loads(cart)
            products = [{"name": item['model'], "price": item['price'], "quantity": item['quantity'], "total": item['total_amount'], "product_id": product_id} for product_id, item in cart.items()]
            id = request.cookies.get('account_number')  # 會員帳號
            order_date = datetime.now().strftime('%Y-%m-%d')  # 取得目前日期時間
            address = request.form['shipping_address']  # 輸入地址

            # 構造 product_str 和 count_str
            product_ids = [str(product['product_id']) for product in products]
            counts = [str(product['quantity']) for product in products]

            product_str = ','.join(product_ids)
            count_str = ','.join(counts)

            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("INSERT INTO orders (customer_id, order_date, product, count, status, address) VALUES (?, ?, ?, ?, ?, ?)", (id, order_date, product_str, count_str, '已下單', address))
            conn.commit()
            conn.close()

            # 清空購物車
            response = make_response(redirect(url_for('cart', message="訂購成功!")))
            response.set_cookie('cart', '', expires=0)  # 刪除購物車
            return response
        else:
            products = []
        return redirect(url_for('cart'))  # After processing POST request, redirect to GET request to avoid form resubmission.

    else:  # GET request
        cart = request.cookies.get('cart')
        if cart:
            cart = json.loads(cart)
            products = [{"name": item['model'], "price": item['price'], "quantity": item['quantity'], "total": item['total_amount'], "product_id": product_id} for product_id, item in cart.items()]
            total_amount = sum(item['total_amount'] for item in cart.values())
        else:
            products = []
            total_amount = 0
        return render_template('cart.html', products=products, total_amount=total_amount, account_number=request.cookies.get('account_number'), message=message)

@app.route("/administrator")  # 管理員介面
def administrator():
    if request.cookies.get('account_number'):
        # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT account_number,administrator FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchall()
        cursor.close()
        conn.close()
        if (member[0][1] == 'true'):
            return render_template('administrator.html')
        else:
            return render_template('index.html')
    return render_template('login.html')  # 跳轉到登入畫面

@app.route("/all_member")  # 管理員介面 - 所有會員資料
def all_member():
    if request.cookies.get('account_number'):
        # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT account_number,administrator FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchone()  # 只需要取一条记录
        cursor.execute("SELECT * FROM members")
        all_member = cursor.fetchall()
        cursor.close()
        conn.close()
        if member and member[1] == 'true':
            return render_template('all_member.html', all_member=all_member)
        else:
            return render_template('index.html')
    return render_template('login.html')  # 跳轉到登入畫面

@app.route("/all_product")  # 管理員介面 - 商品管理
def all_product():
    if request.cookies.get('account_number'):
        # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT account_number,administrator FROM members WHERE account_number=?",(request.cookies.get('account_number'),))
        member = cursor.fetchone()  # 只需要取一条记录
        cursor.execute("SELECT * FROM products")
        all_product = cursor.fetchall()
        cursor.close()
        conn.close()
        if member and member[1] == 'true':
            return render_template('all_product.html', all_products=all_product)
        else:
            return render_template('index.html')
    return render_template('login.html')  # 跳轉到登入畫面

@app.route("/all_order", methods=['GET', 'POST'])  # 管理員介面 - 所有訂單
def all_order():
    if request.cookies.get('account_number'):
        # 連接資料庫,查詢權限
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT account_number, administrator FROM members WHERE account_number=?", (request.cookies.get('account_number'),))
        member = cursor.fetchone()  # 只需要取一条记录
        if member and member[1] == 'true':
            # 基本查詢語句
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            # 檢查查詢條件並添加到查詢語句中
            if request.method == 'POST':
                order_number = request.form.get('orderNumber')
                order_date = request.form.get('orderDate')
                member = request.form.get('member')
                if order_number:
                    query += " AND order_id=?"
                    params.append(order_number)
                if order_date:
                    query += " AND order_date=?"
                    params.append(order_date)
                if member:
                    query += " AND customer_id=?"
                    params.append(member)

            print(query)
            cursor.execute(query, params)
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('order.html', data=data, admin_mode=True)
        else:
            return render_template('index.html')
    return render_template('login.html')  # 跳轉到登入畫面

@app.route("/product", methods=['GET'])  # 商品頁面
def product():
    category = request.args.get('category')
    brand = request.args.get('brand', '')
    # 確認是否登入帳號
    account_number = request.cookies.get('account_number')
    return render_template('product.html',category=category, brand=brand, account_number=account_number)


@app.route("/product/<int:product_id>", methods=['GET', 'POST'])
def product_details(product_id):
    if request.method == 'POST':
        quantity = request.form.get('quantity')
        if not quantity or int(quantity) <= 0:
            return "Invalid quantity", 400

        # Retrieve product details from database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
        product = cursor.fetchone()

        if product:
            # Extract necessary details
            product_id = str(product[0])
            model = product[3]
            price = float(product[4])  # Assuming price is stored as a float in the database

            # Calculate total amount
            total_amount = float(quantity) * price

            # Retrieve current cart from cookies
            cart = request.cookies.get('cart')
            if cart:
                cart = json.loads(cart)
            else:
                cart = {}

            # Update cart with the new product
            cart_item = {
                'model': model,
                'price': price,
                'quantity': int(quantity),
                'total_amount': total_amount
            }

            cart[str(product_id)] = cart_item

            # Close database connection
            cursor.close()
            conn.close()

            # Create response with updated cart cookie
            resp = make_response(redirect(url_for('product_details', product_id=product_id, _external=True)))
            resp.set_cookie('cart', json.dumps(cart), max_age=60*60*24*30)  # Expires in 30 days

            # Pass the success message
            resp.set_cookie('message', '加入購物車成功!', max_age=1)

            return resp
        else:
            return "Product not found", 404
    else:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
        product = cursor.fetchone()

        if product:
            data = {
                "product_id": str(product[0]),
                "category": product[1],
                "brand": product[2],
                "model": product[3],
                "price": product[4],
                "stock_quantity": product[5],
                "description": product[6],
                "specifications": product[7],
            }

            # Check for the success message
            message = request.cookies.get('message', '')

            return render_template('product_details.html', product=data, message=message)
        else:
            return "Product not found", 404


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('account_number', '', expires=0)  # 刪除帳號
    response.set_cookie('cart', '', expires=0)  # 刪除購物車
    return response

if __name__ == '__main__':
    app.run(debug=True)
