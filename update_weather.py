import requests
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
from pdf2image import convert_from_path
import shutil
import os
from PIL import Image

# --- 追加: PDF編集用ライブラリ ---
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# -----------------------------------
# 1. 保存先フォルダの定義
# -----------------------------------

# 保存先フォルダパス
dest_folder_path = "images"
os.makedirs(dest_folder_path, exist_ok=True)
print(f"Destination folder: {dest_folder_path}")

# ★追加: レイヤー画像のフォルダパス
layer_folder_path = "layer"

# -----------------------------------
# ★追加: PDFにレイヤー画像を合成する関数
# -----------------------------------
def overlay_japan_map(pdf_path, overlay_image_name):
    """
    pdf_path: 元のPDFファイルのパス
    overlay_image_name: layerフォルダ内のPNGファイル名
    戻り値: 合成後のPDFファイルパス（失敗時や画像がない場合は元のパスを返す）
    """
    overlay_png_path = os.path.join(layer_folder_path, overlay_image_name)

    # 元PDFやレイヤー画像が存在しない場合は何もしない
    if not os.path.exists(pdf_path):
        return pdf_path
    if not os.path.exists(overlay_png_path):
        print(f"警告: レイヤー画像なし ({overlay_png_path}) -> 合成スキップ")
        return pdf_path

    print(f"カラー合成処理開始: {pdf_path} + {overlay_image_name}")

    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # 全ページに対して処理
        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            # ReportLabで透明なPDFキャンバスを作成
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            
            # 画像をページサイズいっぱいに配置 (mask='auto'で透過)
            can.drawImage(ImageReader(overlay_png_path), 0, 0, width=width, height=height, mask="auto")
            can.save()
            packet.seek(0)
            
            # 元のページにオーバーレイPDFをマージ
            overlay_pdf = PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])
            writer.add_page(page)

        # 出力ファイル名を作成 (_COLOR を付与)
        output_file = pdf_path.replace(".pdf", "_COLOR.pdf")
        
        with open(output_file, "wb") as f:
            writer.write(f)
        
        print(f"レイヤー合成完了: {output_file}")
        return output_file

    except Exception as e:
        print(f"合成エラー: {e} -> 元ファイルを使用します")
        return pdf_path


# -----------------------------------
# 2. PDF/画像 ダウンロード関数群
# -----------------------------------
def download_asas_pdf(target_time):
    yyyymm = target_time.strftime("%Y%m")
    yyyymmddhhmm = target_time.strftime("%Y%m%d%H%M")
    url = f"https://www.data.jma.go.jp/yoho/data/wxchart/quick/{yyyymm}/ASAS_COLOR_{yyyymmddhhmm}.pdf"
    filename = f"ASAS_{yyyymmddhhmm}.pdf"
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    return None

def download_fsas_pdf():
    url = "https://www.data.jma.go.jp/yoho/data/wxchart/quick/FSAS24_COLOR_ASIA.pdf"
    filename = "FSAS24_COLOR_ASIA.pdf"
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    return None

def download_jma_nwpmap_pdf(chart_type, target_time):
    hh = target_time.strftime("%H")
    url = f"https://www.jma.go.jp/bosai/numericmap/data/nwpmap/{chart_type}_{hh}.pdf"
    filename = f"{chart_type.upper()}_{target_time.strftime('%Y%m%d%H%M')}.pdf"
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    return None

def download_jma_png(url, chart_type_name):
    local_filename = f"{chart_type_name}.png"
    r = requests.get(url)
    if r.status_code == 200:
        with open(local_filename, "wb") as f:
            f.write(r.content)
        print(f"{local_filename} をダウンロードしました")
        return local_filename
    return None

def download_jma_hourly_png(chart_type_base, target_time):
    hh = target_time.strftime("%H")
    url = f"https://www.data.jma.go.jp/airinfo/data/pict/nwp/{chart_type_base}_{hh}.png"
    filename = f"{chart_type_base.upper()}_{target_time.strftime('%Y%m%d%H%M')}.png"
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    return None

def download_jma_ashfall_pdf(chart_id, target_time_jst):
    target_time_utc = target_time_jst.astimezone(UTC)
    yyyymmddhhmm = target_time_utc.strftime("%Y%m%d%H%M")
    url = f"https://www.jma.go.jp/bosai/volcano/data/ashfall/pdf/Z__C_RJTD_{yyyymmddhhmm}00_EQV_CHT_JCIashfallr_{chart_id}_N1_image.pdf"
    filename = f"ASHFALL_{chart_id}_{yyyymmddhhmm}.pdf"
    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        if os.path.getsize(filename) < 10240:
            os.remove(filename)
            return None
        return filename
    return None

# -----------------------------------
# 3. 取得ロジック関数群
# -----------------------------------
def get_latest_two_pdfs():
    now_utc = datetime.now(UTC)
    hours = [0, 6, 12, 18]
    for i in range(2):
        day = now_utc - timedelta(days=i)
        candidate_hours = hours[::-1]
        for h in candidate_hours:
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            latest_pdf = download_asas_pdf(target_time)
            if latest_pdf:
                idx = candidate_hours.index(h)
                if idx + 1 < len(candidate_hours):
                    prev_time = day.replace(hour=candidate_hours[idx + 1], minute=0, second=0, microsecond=0)
                else:
                    prev_day = day - timedelta(days=1)
                    prev_time = prev_day.replace(hour=18, minute=0, second=0, microsecond=0)
                prev_pdf = download_asas_pdf(prev_time)
                return latest_pdf, prev_pdf
    return None, None

def get_latest_jma_nwpmap_pdf(chart_type):
    now_utc = datetime.now(UTC)
    hours_nwpmap = [0, 12]
    for i in range(2):
        day = now_utc - timedelta(days=i)
        for h in sorted(hours_nwpmap, key=lambda x: abs(now_utc.hour - x)):
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            if target_time > now_utc: continue
            pdf_file = download_jma_nwpmap_pdf(chart_type, target_time)
            if pdf_file: return pdf_file
    return None

def get_latest_jma_hourly_png(chart_type_base, hours_list):
    now_utc = datetime.now(UTC)
    for i in range(2):
        day = now_utc - timedelta(days=i)
        candidate_hours = sorted(hours_list, key=lambda x: abs(now_utc.hour - x) if day.date() == now_utc.date() else x, reverse=True)
        for h in candidate_hours:
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            if target_time > now_utc: continue
            png_file = download_jma_hourly_png(chart_type_base, target_time)
            if png_file: return png_file
    return None

def get_latest_jma_ashfall_pdf_stable(volcano_name, volcano_code):
    ash_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    now_utc = datetime.now(timezone.utc)
    candidates = [h for h in ash_hours if h <= now_utc.hour]
    if candidates:
        base_hour = max(candidates)
        base_day = now_utc
    else:
        base_hour = ash_hours[-1]
        base_day = now_utc - timedelta(days=1)
    idx = ash_hours.index(base_hour)
    candidate_hours = [ash_hours[(idx - i) % len(ash_hours)] for i in range(len(ash_hours))]
    for i in range(2):
        day = base_day - timedelta(days=i)
        for hh in candidate_hours:
            ash_time = day.replace(hour=hh, minute=0, second=0, microsecond=0)
            ts = ash_time.strftime("%Y%m%d%H%M%S")
            url = f"https://www.jma.go.jp/bosai/volcano/data/ashfall/pdf/Z__C_RJTD_{ts}_EQV_CHT_JCIashfallr_{volcano_code}_N1_image.pdf"
            filename = f"ASHFALL_{volcano_name}_{ts}.pdf"
            r = requests.get(url)
            if r.status_code == 200 and len(r.content) > 10240:
                with open(filename, "wb") as f:
                    f.write(r.content)
                return filename
    return None

# -----------------------------------
# 4. 保存・アップロード用関数
# -----------------------------------
def pdf_to_png_and_upload(pdf_file, final_drive_name):
    if pdf_file and os.path.exists(pdf_file):
        png_filename_local = pdf_file.replace(".pdf", ".png")
        # カラー化されたPDFの場合は高解像度で変換
        pages = convert_from_path(pdf_file, dpi=200)
        pages[0].save(png_filename_local, "PNG")

        shutil.copy(png_filename_local, os.path.join(dest_folder_path, final_drive_name))
        print(f"Copied {png_filename_local} to {os.path.join(dest_folder_path, final_drive_name)}")
        os.remove(png_filename_local)
        return True
    return False

def direct_png_upload(local_png_file, final_drive_name):
    if local_png_file and os.path.exists(local_png_file):
        shutil.copy(local_png_file, os.path.join(dest_folder_path, final_drive_name))
        print(f"Copied {local_png_file} to {os.path.join(dest_folder_path, final_drive_name)}")
        os.remove(local_png_file)
        return True
    return False

# -----------------------------------
# 5. メイン実行ブロック
# -----------------------------------

# --- ASASチャート (合成不要) ---
latest_asas_pdf_local, prev_asas_pdf_local = get_latest_two_pdfs()
pdf_to_png_and_upload(latest_asas_pdf_local, "ASAS_Latest.png")
pdf_to_png_and_upload(prev_asas_pdf_local, "ASAS_Prior.png")
if latest_asas_pdf_local and os.path.exists(latest_asas_pdf_local): os.remove(latest_asas_pdf_local)
if prev_asas_pdf_local and os.path.exists(prev_asas_pdf_local): os.remove(prev_asas_pdf_local)

# --- FSASチャート (合成不要) ---
fsas_pdf_local = download_fsas_pdf()
if fsas_pdf_local:
    pdf_to_png_and_upload(fsas_pdf_local, "FSAS_Latest.png")
    if os.path.exists(fsas_pdf_local): os.remove(fsas_pdf_local)

# --- AUPQチャート (★合成対象★) ---
# AUPQ35
aupq35_pdf = get_latest_jma_nwpmap_pdf('aupq35')
if aupq35_pdf:
    # 1. カラー合成 (戻り値は合成後のファイル名)
    aupq35_color = overlay_japan_map(aupq35_pdf, "japan_overlay_aupq.png")
    # 2. 合成後のPDFをPNG化して保存
    pdf_to_png_and_upload(aupq35_color, "AUPQ35_Latest.png")
    # 3. 不要な一時ファイルの削除
    if os.path.exists(aupq35_pdf): os.remove(aupq35_pdf)
    if aupq35_color != aupq35_pdf and os.path.exists(aupq35_color): os.remove(aupq35_color)

# AUPQ78
aupq78_pdf = get_latest_jma_nwpmap_pdf('aupq78')
if aupq78_pdf:
    aupq78_color = overlay_japan_map(aupq78_pdf, "japan_overlay_aupq.png")
    pdf_to_png_and_upload(aupq78_color, "AUPQ78_Latest.png")
    if os.path.exists(aupq78_pdf): os.remove(aupq78_pdf)
    if aupq78_color != aupq78_pdf and os.path.exists(aupq78_color): os.remove(aupq78_color)

# --- FXFEチャート (★合成対象★) ---
# FXFE502
fxfe502_pdf = get_latest_jma_nwpmap_pdf('fxfe502')
if fxfe502_pdf:
    fxfe502_color = overlay_japan_map(fxfe502_pdf, "japan_overlay_fxfe.png")
    pdf_to_png_and_upload(fxfe502_color, "FXFE502_Latest.png")
    if os.path.exists(fxfe502_pdf): os.remove(fxfe502_pdf)
    if fxfe502_color != fxfe502_pdf and os.path.exists(fxfe502_color): os.remove(fxfe502_color)

# FXFE5782
fxfe5782_pdf = get_latest_jma_nwpmap_pdf('fxfe5782')
if fxfe5782_pdf:
    fxfe5782_color = overlay_japan_map(fxfe5782_pdf, "japan_overlay_fxfe.png")
    pdf_to_png_and_upload(fxfe5782_color, "FXFE5782_Latest.png")
    if os.path.exists(fxfe5782_pdf): os.remove(fxfe5782_pdf)
    if fxfe5782_color != fxfe5782_pdf and os.path.exists(fxfe5782_color): os.remove(fxfe5782_color)

# --- FXJPチャート (★合成対象★) ---
# FXJP854
fxjp854_pdf = get_latest_jma_nwpmap_pdf('fxjp854')
if fxjp854_pdf:
    fxjp854_color = overlay_japan_map(fxjp854_pdf, "japan_overlay_fxjp.png")
    pdf_to_png_and_upload(fxjp854_color, "FXJP854_Latest.png")
    if os.path.exists(fxjp854_pdf): os.remove(fxjp854_pdf)
    if fxjp854_color != fxjp854_pdf and os.path.exists(fxjp854_color): os.remove(fxjp854_color)

# --- その他のPNGチャート (合成不要) ---
fxjp106_png = get_latest_jma_hourly_png('fxjp106', [0, 3, 6, 9, 12, 15, 18, 21])
if fxjp106_png: direct_png_upload(fxjp106_png, "FXJP106_Latest.png")

fbjp_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/fbjp/fbjp.png", "FBJP_Latest")
if fbjp_png: direct_png_upload(fbjp_png, "FBJP_Latest.png")

fpos39_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/low-level_sigwx/fbos39.png", "FBOS39_Latest")
if fpos39_png: direct_png_upload(fpos39_png, "FBOS39_Latest.png")

# --- 降灰予報図 (合成不要) ---
sakurajima_pdf = get_latest_jma_ashfall_pdf_stable("Sakurajima", "JR506X")
if sakurajima_pdf:
    pdf_to_png_and_upload(sakurajima_pdf, "Sakurajima_Ashfall_Latest.png")
    os.remove(sakurajima_pdf)

kirishima_pdf = get_latest_jma_ashfall_pdf_stable("Kirishimayama", "JR551X")
if kirishima_pdf:
    pdf_to_png_and_upload(kirishima_pdf, "Kirishimayama_Ashfall_Latest.png")
    os.remove(kirishima_pdf)

# -----------------------------------
# 6. 全画像を1つのPDFにまとめる処理 (A4高画質版)
# -----------------------------------
def create_combined_pdf(image_folder, output_pdf_name):
    # PDFに含める画像リスト
    target_images = [
        "ASAS_Prior.png", "ASAS_Latest.png", "FSAS_Latest.png",
        "AUPQ35_Latest.png", "AUPQ78_Latest.png",
        "FXFE502_Latest.png", "FXFE5782_Latest.png",
        "FBJP_Latest.png", "FBOS39_Latest.png",
        "FXJP106_Latest.png", "FXJP854_Latest.png",
        "Sakurajima_Ashfall_Latest.png", "Kirishimayama_Ashfall_Latest.png"
    ]

    # A4サイズ (300DPI) のピクセル数
    # 幅: 8.27インチ × 300 = 2481 px
    # 高さ: 11.69インチ × 300 = 3508 px
    A4_SIZE = (2481, 3508)
    
    pdf_pages = []
    print("--- A4高画質PDF結合処理開始 ---")

    for img_name in target_images:
        img_path = os.path.join(image_folder, img_name)
        
        if os.path.exists(img_path):
            try:
                # 画像を読み込み
                img = Image.open(img_path)
                
                # 1. 白色のA4ベースキャンバスを作成
                canvas = Image.new('RGB', A4_SIZE, (255, 255, 255))
                
                # 2. アスペクト比を維持したまま、A4枠内に収まる最大サイズを計算
                img.thumbnail(A4_SIZE, Image.Resampling.LANCZOS)
                
                # 3. 画像を中央に配置するための座標計算
                offset = (
                    (A4_SIZE[0] - img.width) // 2,
                    (A4_SIZE[1] - img.height) // 2
                )
                
                # 4. キャンバスに画像を貼り付け
                canvas.paste(img, offset)
                
                pdf_pages.append(canvas)
                print(f"追加 (A4最適化): {img_name}")
                
            except Exception as e:
                print(f"エラー（スキップ）: {img_name} -> {e}")
        else:
            print(f"未存在（スキップ）: {img_name}")

    if pdf_pages:
        output_path = os.path.join(image_folder, output_pdf_name)
        # 最初のページをベースに保存。resolution=300を指定して高画質設定を明示
        pdf_pages[0].save(
            output_path, 
            save_all=True, 
            append_images=pdf_pages[1:],
            resolution=300.0,
            quality=95
        )
        print(f"A4高画質PDF作成完了: {output_path}")
    else:
        print("結合する画像がありませんでした。")

# 実行
create_combined_pdf(dest_folder_path, "all_weather_charts.pdf")
