import gradio as gr
import pandas as pd
from datetime import datetime
import os

# --- 1. إعدادات النظام الموحد ---
DATA_FILE = "Asyut_Maintenance_Official_Report.xlsx"
IMG_FOLDER = "maintenance_photos"
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

# الأعمدة الموحدة (12 عمود)
COLS = ["م", "التاريخ", "الهندسة", "بند الصيانه", "المستهدف", "المنفذ", "المغذي", "المحول", "الموزع", "النسبة %", "GPS", "المسار"]

districts = ["شرق", "غرب", "البدارى", "الخزان", "مبارك", "مركز شمال", "مركز جنوب", "ساحل سليم", "الغنايم", "صدفا", "ابوتيج مدينة", "ابوتيج قرى"]

# القائمة الكاملة (42 بند صيانة - بدون أي نقص)
maintenance_items = [
    "صيانة عامود جهد منخفض", "صيانة عامود جهد متوسط", "بناء قاعده كشك محول", "عمل محاره لقاعدة كشك محول", 
    "زرع عامود جهد متوسط", "زرع عامود جهد منخفض", "صيانة محول معلق", "صيانة محول كشك", "صيانة محول حجره", 
    "صيانة لوحة ربط حلقى RMU جهد متوسط", "صيانة لوحة جهد منخفض", "صيانة صندوق توزيع جهد منخفض", 
    "خلع وتركيب عامود جهد منخفض", "خلع وتركيب عامود جهد متوسط", "شد وتحريب موصلات لو هوائيه جهد متوسط", 
    "شد موصلات معزولة جهد منخفض", "تغيير شداد لو ٣ مسمار", "تغيير شداد لو ٤ مسمار", "تغيير عازل قرص", 
    "تغيير عازل مسمار", "عمل ركاب", "عمل سرفيل لو جهد متوسط", "عمل كوسه لو جهد متوسط", 
    "صيانة موصلات هوائيه جهد متوسط ب كم", "صيانة موزع جهد متوسط", "صيانة جهاز ريكلوزر جهد متوسط", 
    "صيانة منظم جهد متوسط", "صيانة موصلات هوائيه معزولة جهد منخفض ب كم", "تغيير كابل جهد متوسط ب كم", 
    "تغيير كابل جهد منخفض ب كم", "ردم كرب كابلات جهد متوسط ب كم", "ردم كرب كابلات جهد منخفض ب كم", 
    "عمل علبه نهاية خارجية", "عمل علبه نهاية داخليه", "عمل علبه اتصال", "دهان عامود جهد متوسط", 
    "دهان عامود جهد منخفض", "دهان كشك محول", "دهان لوحة جهد متوسط", "عمل فورمه خرسانية جهد متوسط", 
    "عمل فورمه خرسانية جهد منخفض", "تغيير عازل صيني جهد منخفض ١٤ سم"
]

# --- 2. الوظائف البرمجية ---
def toggle_fields(item):
    f_v, t_v, d_v = False, False, False
    if any(x in item for x in ["موصلات", "كابل", "ريكلوزر"]): f_v = True
    if "محول" in item: t_v = True
    if "موزع" in item: d_v = True
    return gr.update(visible=f_v), gr.update(visible=t_v), gr.update(visible=d_v)

def process_save(dist, item, target_val, done, feeder, trans, dist_n, gps, img):
    try:
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M")
        ratio = (done / target_val) * 100 if target_val > 0 else 0
        
        img_path = "لا يوجد"
        if img is not None:
            # معالجة حفظ الصورة بشكل صحيح
            img_name = f"{dist}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            img_full_path = os.path.join(IMG_FOLDER, img_name)
            import PIL.Image as Image
            if isinstance(img, Image.Image):
                img.save(img_full_path)
            else:
                from shutil import copyfile
                copyfile(img, img_full_path)
            img_path = img_name

        # تحميل أو إنشاء الشيت
        if os.path.exists(DATA_FILE):
            df = pd.read_excel(DATA_FILE)
            # إذا كانت الأعمدة قديمة أو ناقصة (كما ظهر في صور الخطأ)، نعيد تهيئة الأعمدة
            if len(df.columns) != len(COLS):
                df = pd.DataFrame(columns=COLS)
        else:
            df = pd.DataFrame(columns=COLS)
        
        new_entry = [len(df)+1, current_time, dist, item, target_val, done, feeder, trans, dist_n, f"{ratio:.1f}%", gps, img_path]
        df.loc[len(df)] = new_entry
        df.to_excel(DATA_FILE, index=False)
        return "✅ تم الحفظ بنجاح تحت إشراف م./ أسامة صادق إبراهيم"
    except Exception as e:
        return f"❌ خطأ فني: {str(e)}"

def filter_data(start_date, end_date):
    if not os.path.exists(DATA_FILE): return None, "لا توجد بيانات"
    df = pd.read_excel(DATA_FILE)
    df['dt'] = pd.to_datetime(df['التاريخ'], errors='coerce')
    s_d = datetime.strptime(start_date, "%Y-%m-%d").date()
    e_d = datetime.strptime(end_date, "%Y-%m-%d").date()
    mask = (df['dt'].dt.date >= s_d) & (df['dt'].dt.date <= e_d)
    filtered_df = df.loc[mask].drop(columns=['dt'])
    if filtered_df.empty: return None, "لا توجد بيانات لهذه الفترة"
    path = f"Summary_{start_date}_to_{end_date}.xlsx"
    filtered_df.to_excel(path, index=False)
    return filtered_df, path

# --- 3. الواجهة الرسمية ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
    gr.Markdown(f"""
    # ⚡ منظومة صيانة قطاع أسيوط جنوب 
    ### تحت إشراف مهندس: أسامة صادق إبراهيم ساويرس
    **مدير إدارة الصيانة بقطاع أسيوط جنوب**
    """)
    
    with gr.Tab("📝 إدخال البيانات الميدانية"):
        with gr.Row():
            sel_dist = gr.Dropdown(districts, label="1. اختر الهندسة")
            sel_item = gr.Dropdown(maintenance_items, label="2. اختر بند الصيانة")
        
        with gr.Row():
            num_target = gr.Number(label="الكمية المستهدفة", value=1)
            num_done = gr.Number(label="الكمية المنفذة فعلياً", value=0)
            txt_gps = gr.Textbox(label="إحداثيات الموقع (GPS)")
            
        with gr.Row():
            txt_feeder = gr.Textbox(label="اسم المغذي", visible=False)
            txt_trans = gr.Textbox(label="اسم المحول", visible=False)
            txt_distrib = gr.Textbox(label="اسم الموزع", visible=False)

        sel_item.change(toggle_fields, inputs=[sel_item], outputs=[txt_feeder, txt_trans, txt_distrib])
        
        # تصحيح إعدادات الصورة لتجنب ValueError و AttributeError
        input_img = gr.Image(label="صورة تنفيذ العمل", type="pil")
        
        btn_submit = gr.Button("اعتماد وإرسال التقرير النهائي 🚀", variant="primary")
        msg_out = gr.Textbox(label="حالة العملية")

        btn_submit.click(process_save, 
                         inputs=[sel_dist, sel_item, num_target, num_done, txt_feeder, txt_trans, txt_distrib, txt_gps, input_img], 
                         outputs=[msg_out])

    with gr.Tab("📊 لوحة المراقبة والتجميع الزمني"):
        with gr.Row():
            date_s = gr.Textbox(label="من تاريخ", value=datetime.now().strftime("%Y-%m-%d"))
            date_e = gr.Textbox(label="إلى تاريخ", value=datetime.now().strftime("%Y-%m-%d"))
        
        btn_filter = gr.Button("تجميع التقارير للفترة المحددة 🔍")
        table_out = gr.DataFrame(label="السجل الموحد")
        file_summary = gr.File(label="تحميل ملف التجميع (Excel)")

        btn_filter.click(filter_data, inputs=[date_s, date_e], outputs=[table_out, file_summary])

app.launch(share=True)