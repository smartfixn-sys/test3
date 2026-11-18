import os
import sqlite3
import uuid
import base64
from datetime import date
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

# إعداد الصفحة
st.set_page_config(page_title="أرشيف المؤمن عليهم", page_icon="📁", layout="wide")

# إنشاء مجلد لحفظ الصور المرفوعة
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# دالة لتحويل الصورة إلى Base64 لعرضها داخل صفحة الطباعة
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

# دالة لإنشاء كود طباعة آمن ومباشر داخل الإطار
def render_print_component(record_id, name, nat_id, phone, car_num, ins_type, s_date, e_date, status_text, client_images):
    images_html = ""
    for _, img_path in client_images:
        b64_img = get_image_base64(img_path)
        if b64_img:
            ext = os.path.splitext(img_path)[1].replace('.', '')
            if ext.lower() == 'jpg':
                ext = 'jpeg'
            images_html += f'<img src="data:image/{ext};base64,{b64_img}" style="max-width: 200px; max-height: 200px; margin: 10px; border: 1px solid #ccc; border-radius: 5px;" />'

    html_code = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; background-color: #fff; }}
            .header {{ text-align: center; border-bottom: 2px solid #0066cc; padding-bottom: 10px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; font-size: 14px; }}
            th {{ background-color: #f4f6f9; width: 30%; }}
            .images-section {{ text-align: center; margin-top: 20px; }}
            .print-btn {{
                background-color: #0066cc; color: white; padding: 10px 20px; border: none;
                border-radius: 5px; font-size: 16px; cursor: pointer; display: block; margin: 20px auto;
            }}
            .print-btn:hover {{ background-color: #004d99; }}
            @media print {{
                .print-btn {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>📁 بطاقة بيانات المؤمن عليه</h2>
            <p>تاريخ الاستخراج: {date.today()}</p>
        </div>
        <table>
            <tr><th>الاسم الكامل</th><td>{name}</td></tr>
            <tr><th>رقم الهوية / الإقامة</th><td>{nat_id}</td></tr>
            <tr><th>رقم الهاتف</th><td>{phone}</td></tr>
            <tr><th>رقم السيارة</th><td>{car_num}</td></tr>
            <tr><th>نوع التأمين</th><td>{ins_type}</td></tr>
            <tr><th>تاريخ البداية</th><td>{s_date}</td></tr>
            <tr><th>تاريخ النهاية</th><td>{e_date}</td></tr>
            <tr><th>حالة التأمين</th><td>{status_text}</td></tr>
        </table>
        <div class="images-section">
            <h3>المرفقات والوثائق:</h3>
            {images_html if images_html else "<p>لا توجد صور مرفقة</p>"}
        </div>
        <button class="print-btn" onclick="window.print()">🖨️ اضغط هنا للطباعة الآن</button>
    </body>
    </html>
    """
    return html_code

# إعداد قاعدة البيانات (جدول العملاء وجدول الصور المنفصل)
def init_db():
    with sqlite3.connect("archive.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                national_id TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                car_number TEXT NOT NULL,
                insurance_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS archive_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                image_path TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES archive (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

init_db()

st.title("📁 برنامج الأرشيف الإلكتروني للأسماء والتأمين")
st.markdown("إدارة سجلات العملاء، بيانات التأمين، وإرفاق عدة صور لنفس العميل بسهولة.")

# --- الشريط الجانبي للإضافة أو تحديث الصور ---
st.sidebar.header("➕ إضافة سجل أو صور جديدة")

existing_clients = []
with sqlite3.connect("archive.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, national_id FROM archive")
    existing_clients = cursor.fetchall()

client_mode = st.sidebar.radio("اختر العملية:", ["عميل جديد تماماً", "إضافة صور لعميل موجود"])

if client_mode == "إضافة صور لعميل موجود" and existing_clients:
    client_dict = {f"{c[1]} (هوية: {c[2]})": c[0] for c in existing_clients}
    selected_client_str = st.sidebar.selectbox("اختر العميل:", list(client_dict.keys()))
    selected_client_id = client_dict[selected_client_str]
    
    additional_file = st.sidebar.file_uploader("اختر صورة إضافية جديدة:", type=["jpg", "png", "jpeg"], key="add_more_img")
    
    if st.sidebar.button("إضافة الصورة للسجل", type="primary"):
        if additional_file:
            file_extension = os.path.splitext(additional_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            image_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            with open(image_path, "wb") as f:
                f.write(additional_file.getbuffer())
                
            with sqlite3.connect("archive.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO archive_images (client_id, image_path) VALUES (?, ?)", (selected_client_id, image_path))
                conn.commit()
                
            st.sidebar.success("تمت إضافة الصورة بنجاح! ✅")
            st.rerun()
        else:
            st.sidebar.error("الرجاء اختيار ملف صورة أولاً.")

else:
    name_input = st.sidebar.text_input("الاسم الكامل:")
    national_id_input = st.sidebar.text_input("رقم الهوية / الإقامة:")
    phone_input = st.sidebar.text_input("رقم الهاتف:")
    car_number_input = st.sidebar.text_input("رقم السيارة:")

    insurance_options = ["تأمين شامل", "تأمين ضد الغير", "تأمين طبي", "تأمين سفر", "أخرى"]
    insurance_type_input = st.sidebar.selectbox("نوع التأمين:", insurance_options)

    col_date1, col_date2 = st.sidebar.columns(2)
    with col_date1:
        start_date_input = st.sidebar.date_input("تاريخ البداية:", value=date.today())
    with col_date2:
        end_date_input = st.sidebar.date_input("تاريخ النهاية:", value=date.today())

    uploaded_file = st.sidebar.file_uploader("اختر صورة الوثيقة / الشخصية:", type=["jpg", "png", "jpeg"])

    if st.sidebar.button("حفظ في الأرشيف", type="primary"):
        if name_input and national_id_input and phone_input and car_number_input and uploaded_file:
            if end_date_input < start_date_input:
                st.sidebar.error("خطأ: تاريخ النهاية يجب أن يكون بعد تاريخ البداية!")
            else:
                try:
                    with sqlite3.connect("archive.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO archive (name, national_id, phone, car_number, insurance_type, start_date, end_date) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name_input, 
                            national_id_input, 
                            phone_input, 
                            car_number_input,
                            insurance_type_input, 
                            str(start_date_input), 
                            str(end_date_input)
                        ))
                        client_id = cursor.lastrowid
                        
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        unique_filename = f"{uuid.uuid4()}{file_extension}"
                        image_path = os.path.join(UPLOAD_DIR, unique_filename)
                        
                        with open(image_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        cursor.execute("INSERT INTO archive_images (client_id, image_path) VALUES (?, ?)", (client_id, image_path))
                        conn.commit()
                        
                    st.sidebar.success(f"تم حفظ سجل '{name_input}' بنجاح! ✅")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.sidebar.error("خطأ: رقم الهوية مسجل مسبقاً! يمكنك اختيار 'إضافة صور لعميل موجود' بدلاً من ذلك.")
        else:
            st.sidebar.error("الرجاء تعبئة جميع الحقول واختيار صورة.")

# --- قسم البحث والعرض ---
st.header("📋 الأرشيف الحالي")
search_query = st.text_input("🔍 ابحث بالاسم، رقم الهوية، أو رقم السيارة:", placeholder="اكتب للبحث...")

with sqlite3.connect("archive.db") as conn:
    cursor = conn.cursor()
    if search_query:
        cursor.execute("""
            SELECT id, name, national_id, phone, car_number, insurance_type, start_date, end_date 
            FROM archive 
            WHERE name LIKE ? OR national_id LIKE ? OR car_number LIKE ?
        """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute("""
            SELECT id, name, national_id, phone, car_number, insurance_type, start_date, end_date 
            FROM archive
        """)
    records = cursor.fetchall()

if not records:
    st.info("لا توجد نتائج مطابقة في الأرشيف.")
else:
    st.write(f"عدد السجلات المعروضة: **{len(records)}**")
    st.markdown("---")
    
    for record_id, name, nat_id, phone, car_num, ins_type, s_date, e_date in records:
        col1, col2, col3, col4 = st.columns([1.5, 2.5, 2.5, 1.2])
        
        with col1:
            with sqlite3.connect("archive.db") as conn_img:
                cur_img = conn_img.cursor()
                cur_img.execute("SELECT id, image_path FROM archive_images WHERE client_id = ?", (record_id,))
                client_images = cur_img.fetchall()
            
            if client_images:
                for img_id, img_path in client_images:
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            st.image(img, width=100)
                            if len(client_images) > 1:
                                if st.button("حذف هذه الصورة", key=f"del_img_{img_id}"):
                                    try:
                                        os.remove(img_path)
                                    except:
                                        pass
                                    with sqlite3.connect("archive.db") as del_conn:
                                        del_conn.cursor().execute("DELETE FROM archive_images WHERE id = ?", (img_id,))
                                        del_conn.commit()
                                    st.success("تم حذف الصورة")
                                    st.rerun()
                        except:
                            st.warning("صورة تالفة")
                    else:
                        st.warning("الصورة غير موجودة")
            else:
                st.warning("لا توجد صور")
                
        with col2:
            st.subheader(f"👤 {name}")
            st.write(f"**🆔 رقم الهوية:** {nat_id}")
            st.write(f"**📞 الهاتف:** {phone}")
            st.write(f"**🚗 رقم السيارة:** {car_num}")
            
        with col3:
            st.write("") 
            st.write(f"**🛡️ نوع التأمين:** {ins_type}")
            st.write(f"**📅 من:** {s_date}  |  **إلى:** {e_date}")
            
            is_expired = date.fromisoformat(e_date) < date.today()
            if is_expired:
                st.error("⚠️ التأمين منتهي الصلاحية")
                status_text = "منتهي الصلاحية ⚠️"
            else:
                st.success("✅ التأمين ساري المفعول")
                status_text = "ساري المفعول ✅"
            
        with col4:
            st.write("")
            # زر فتح خيارات الطباعة والمعاينة
            with st.expander("🖨️ طباعة السجل"):
                print_html_content = render_print_component(
                    record_id, name, nat_id, phone, car_num, ins_type, s_date, e_date, status_text, client_images
                )
                components.html(print_html_content, height=450, scrolling=True)

            # زر حذف السجل بالكامل
            if st.button("🗑️ حذف السجل بالكامل", key=f"del_rec_{record_id}", use_container_width=True):
                for img_id, img_path in client_images:
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except:
                            pass
                
                with sqlite3.connect("archive.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM archive_images WHERE client_id = ?", (record_id,))
                    cursor.execute("DELETE FROM archive WHERE id = ?", (record_id,))
                    conn.commit()
                
                st.success("تم حذف السجل وكل صوره!")
                st.rerun()
                
        st.markdown("---")