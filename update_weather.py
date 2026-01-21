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

# ---------------------------------------------------------
# FXJP106 (修正版: 更新日時確認ロジック)
# URL: https://www.data.jma.go.jp/airinfo/data/pict/nwp/fxjp106_HH.png
# ---------------------------------------------------------
from email.utils import parsedate_to_datetime # HTTPヘッダーの日付解析用

def download_fxjp106_checked():
    now_utc = datetime.now(timezone.utc)
    
    # 現在の時刻を基準に、直近の3時間ごとの時刻(00, 03...21)を計算
    # 例: 10時なら09時、02時なら00時
    base_hour = (now_utc.hour // 3) * 3
    
    # 最新候補から順に「過去へ」遡ってチェックする
    # 最大4回（12時間前まで）遡れば、必ず有効な最新図が見つかるはず
    for i in range(4):
        # 時間計算 (24時間表記の調整)
        target_h = (base_hour - (i * 3)) % 24
        h_str = f"{target_h:02d}"
        
        url = f"https://www.data.jma.go.jp/airinfo/data/pict/nwp/fxjp106_{h_str}.png"
        filename = f"FXJP106_temp_{h_str}.png"
        
        try:
            # HEADリクエストでヘッダー情報のみ取得（ファイル本体はまだ落とさない）
            head_req = requests.head(url, timeout=10)
            
            if head_req.status_code == 200:
                # Last-Modifiedヘッダー（更新日時）を取得
                last_modified_str = head_req.headers.get('Last-Modified')
                
                if last_modified_str:
                    # 文字列をdatetimeオブジェクトに変換
                    last_modified_dt = parsedate_to_datetime(last_modified_str)
                    
                    # サーバーの日時と現在時刻の差を計算
                    time_diff = now_utc - last_modified_dt
                    
                    # 【重要】判定ロジック
                    # もしファイルの更新時間が「12時間以上前」なら、それは「昨日のデータ」とみなしてスキップ
                    # (FXJP106は3時間ごとなので、正常なら数時間以内の古さのはず)
                    if time_diff > timedelta(hours=12):
                        print(f"スキップ: {url} はデータが古すぎます (更新: {last_modified_dt}, 経過: {time_diff})")
                        continue
                    
                    # データが新しい場合のみダウンロード実行
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        with open(filename, "wb") as f:
                            f.write(r.content)
                        print(f"FXJP106 をダウンロードしました (対象時刻: {h_str}UTC, 更新: {last_modified_dt})")
                        return filename
                else:
                    # Last-Modifiedがない場合は、危険なのでスキップするか、とりあえず落とす（今回はスキップ）
                    print(f"警告: Last-Modifiedヘッダーがありません ({url})")
                    continue
            else:
                # 404などの場合
                continue
                
        except Exception as e:
            print(f"FXJP106 チェックエラー ({h_str}UTC): {e}")
            continue

    print("FXJP106: 有効な（新しい）画像が見つかりませんでした")
    return None

# 実行とアップロード
fxjp106_png = download_fxjp106_checked()
if fxjp106_png:
    direct_png_upload(fxjp106_png, "FXJP106_Latest.png")

fbjp_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/fbjp/fbjp.png", "FBJP_Latest")
if fbjp_png: direct_png_upload(fbjp_png, "FBJP_Latest.png")

fpos39_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/low-level_sigwx/fbos39.png", "FBOS39_Latest")
if fpos39_png: direct_png_upload(fpos39_png, "FBOS39_Latest.png")

# --- QMCD / QMCJ 追加分 ---
qmcd_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/taf/QMCD98_RJFK.png", "QMCD_RJFK_Latest")
if qmcd_png: direct_png_upload(qmcd_png, "QMCD_RJFK_Latest.png")

qmcj_png = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/taf/QMCJ98_RJFK.png", "QMCJ_RJFK_Latest")
if qmcj_png: direct_png_upload(qmcj_png, "QMCJ_RJFK_Latest.png")

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
# 6. 全画像を1つのPDFにまとめる処理 (印刷品質重視・限界挑戦版)
# -----------------------------------
def create_combined_pdf(image_folder, output_pdf_name):
    target_images = [
        "ASAS_Prior.png", "ASAS_Latest.png", "FSAS_Latest.png",
        "AUPQ35_Latest.png", "AUPQ78_Latest.png",
        "FXFE502_Latest.png", "FXFE5782_Latest.png",
        "FBJP_Latest.png", "FBOS39_Latest.png",
        "FXJP106_Latest.png", "FXJP854_Latest.png",
        "QMCD_RJFK_Latest.png",
        "QMCJ_RJFK_Latest.png",
        "Sakurajima_Ashfall_Latest.png", "Kirishimayama_Ashfall_Latest.png"
    ]

    # A4 300DPI (印刷品質基準)
    A4_PORTRAIT_PX = (2480, 3508)
    A4_LANDSCAPE_PX = (3508, 2480)
    
    pdf_pages = []
    print("--- A4高画質PDF結合開始 (300DPI・高品質設定) ---")

    for img_name in target_images:
        img_path = os.path.join(image_folder, img_name)
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert("RGB")
                w, h = img.size
                page_size = A4_LANDSCAPE_PX if w >= h else A4_PORTRAIT_PX

                img_ratio = w / h
                page_ratio = page_size[0] / page_size[1]

                if img_ratio > page_ratio:
                    new_w = page_size[0]
                    new_h = int(new_w / img_ratio)
                else:
                    new_h = page_size[1]
                    new_w = int(new_h * img_ratio)

                resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", page_size, (255, 255, 255))
                offset = ((page_size[0] - new_w) // 2, (page_size[1] - new_h) // 2)
                canvas.paste(resized_img, offset)
                
                pdf_pages.append(canvas)
            except Exception as e:
                print(f"エラー: {img_name} -> {e}")

    if pdf_pages:
        output_path = os.path.join(image_folder, "all_weather_charts.pdf")
        # 保存設定をギリギリまで調整
        pdf_pages[0].save(
            output_path, 
            save_all=True, 
            append_images=pdf_pages[1:],
            resolution=300.0,
            quality=85,           # 85はサイズ効率が非常に高いです
            subsampling=0,        # 色のにじみを防止
            optimize=True         # 圧縮の最適化を有効化
        )
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"PDF作成完了: {output_path} (サイズ: {file_size_mb:.2f} MB)")
        
        # もしこれでも25MBを超えた場合の警告
        if file_size_mb > 25:
            print("【警告】ファイルサイズが25MBを超えています。Cloudflare Pagesでの公開に失敗する可能性があります。")
    else:
        print("作成対象の画像が見つかりませんでした。")

# 実行
create_combined_pdf(dest_folder_path, "all_weather_charts.pdf")
