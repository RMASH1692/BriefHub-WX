import requests
from datetime import datetime, timedelta, timezone
UTC = timezone.utc # Add timezone import
from pdf2image import convert_from_path
import shutil
import os
from PIL import Image

# -----------------------------------
# 1. 保存先フォルダの定義
# -----------------------------------

# 保存先フォルダパス (My Drive内のパスをGitHubリポジトリのローカルパスに変更)
dest_folder_path = "images"

# 保存先フォルダが存在しない場合は作成
os.makedirs(dest_folder_path, exist_ok=True)
print(f"Destination folder: {dest_folder_path}")


# --- 取得したフォルダIDを変数に保存 --- (Removed Google Drive specific folder ID logic)
# print(f"Destination folder ID: {dest_folder_id}")


# -----------------------------------
# 2. PDFをダウンロードする関数 (ASAS用)
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
    else:
        print(f"{filename} はまだ公開されていません")
        return None

# -----------------------------------
# 2.1. PDFをダウンロードする関数 (FSAS用)
# -----------------------------------
def download_fsas_pdf():
    url = "https://www.data.jma.go.jp/yoho/data/wxchart/quick/FSAS24_COLOR_ASIA.pdf"
    filename = "FSAS24_COLOR_ASIA.pdf" # ローカルでの一時ファイル名

    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    else:
        print(f"FSAS24_COLOR_ASIA.pdf のダウンロードに失敗しました (Status Code: {r.status_code})")
        return None

# -----------------------------------
# 2.2. PDFをダウンロードする関数 (JMA Numeric Map共通用)
# -----------------------------------
def download_jma_nwpmap_pdf(chart_type, target_time):
    hh = target_time.strftime("%H")
    url = f"https://www.jma.go.jp/bosai/numericmap/data/nwpmap/{chart_type}_{hh}.pdf"
    filename = f"{chart_type.upper()}_{target_time.strftime('%Y%m%d%H%M')}.pdf" # ローカルファイル名

    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    else:
        print(f"{filename} (URL: {url}) はまだ公開されていないか、ダウンロードに失敗しました (Status Code: {r.status_code})")
        return None

# -----------------------------------
# 2.3. PNGをダウンロードする関数 (FBJP, FBOS用)
# -----------------------------------
def download_jma_png(url, chart_type_name):
    # ファイル名をURLから推測または指定
    local_filename = f"{chart_type_name}.png" # ローカルでの一時ファイル名

    r = requests.get(url)
    if r.status_code == 200:
        with open(local_filename, "wb") as f:
            f.write(r.content)
        print(f"{local_filename} をダウンロードしました")
        return local_filename
    else:
        print(f"{local_filename} (URL: {url}) のダウンロードに失敗しました (Status Code: {r.status_code})")
        return None

# -----------------------------------
# 2.4. JMA Hourly PNGをダウンロードする関数 (FXJP106用)
# -----------------------------------
def download_jma_hourly_png(chart_type_base, target_time):
    hh = target_time.strftime("%H")
    # Base URL for JMA hourly PNGs like FXJP106
    url = f"https://www.data.jma.go.jp/airinfo/data/pict/nwp/{chart_type_base}_{hh}.png"
    filename = f"{chart_type_base.upper()}_{target_time.strftime('%Y%m%d%H%M')}.png" # ローカルファイル名

    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{filename} をダウンロードしました")
        return filename
    else:
        print(f"PNGファイル {filename} (URL: {url}) はまだ公開されていないか、ダウンロードに失敗しました (Status Code: {r.status_code})")
        return None

# -----------------------------------
# 2.5. PDFをダウンロードする関数 (JMA Ashfall 共通用)
# -----------------------------------
def download_jma_ashfall_pdf(chart_id, target_time_jst): # Renamed parameter for clarity
    # target_time_jst should be a datetime object in JST
    target_time_utc = target_time_jst.astimezone(UTC) # Convert to UTC for URL construction
    yyyymmddhhmm = target_time_utc.strftime("%Y%m%d%H%M")
    # URL例: https://www.jma.go.jp/bosai/volcano/data/ashfall/pdf/Z__C_RJTD_20260117080000_EQV_CHT_JCIashfallr_JR506X_N1_image.pdf
    url = f"https://www.jma.go.jp/bosai/volcano/data/ashfall/pdf/Z__C_RJTD_{yyyymmddhhmm}00_EQV_CHT_JCIashfallr_{chart_id}_N1_image.pdf"
    filename = f"ASHFALL_{chart_id}_{yyyymmddhhmm}.pdf" # ローカルファイル名

    print(f"試行URL: {url}") # Add debug print

    r = requests.get(url)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)

        # ファイルサイズチェック: 10KB未満のPDFはひな形の可能性あり
        file_size = os.path.getsize(filename)
        if file_size < 10240: # 10KB (10240 bytes) を閾値として設定
            print(f"警告: ダウンロードした {filename} はサイズが小さすぎます ({file_size} bytes)。ひな形の可能性があります。スキップします。")
            os.remove(filename) # 疑わしいファイルを削除
            return None

        print(f"{filename} をダウンロードしました")
        return filename
    else:
        print(f"{filename} (URL: {url}) はまだ公開されていないか、ダウンロードに失敗しました (Status Code: {r.status_code})")
        return None


# -----------------------------------
# 3. 最新とその1つ前のPDFを取得する関数 (ASAS用)
# -----------------------------------
def get_latest_two_pdfs():
    now_utc = datetime.now(UTC)
    hours = [0, 6, 12, 18]

    # 最新のPDFを見つける
    for i in range(2):  # 直近2日まで遡る
        day = now_utc - timedelta(days=i)
        candidate_hours = hours[::-1]  # 18→12→6→0の順でチェック
        for h in candidate_hours:
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            latest_pdf = download_asas_pdf(target_time)
            if latest_pdf:
                # 最新が見つかったら、その1つ前も取得
                idx = candidate_hours.index(h)
                if idx + 1 < len(candidate_hours):
                    prev_time = day.replace(hour=candidate_hours[idx + 1], minute=0, second=0, microsecond=0)
                else:
                    # 前の日の最後の時間（18UTC）にさかのぼる
                    prev_day = day - timedelta(days=1)
                    prev_time = prev_day.replace(hour=18, minute=0, second=0, microsecond=0)
                prev_pdf = download_asas_pdf(prev_time)
                return latest_pdf, prev_pdf
    print("直近2日以内のASAS PDFが見つかりませんでした")
    return None, None

# -----------------------------------
# 3.1. 最新のJMA Numeric Map PDFを取得する関数 (AUPQ, FXFE, FXJP用)
# -----------------------------------
def get_latest_jma_nwpmap_pdf(chart_type):
    now_utc = datetime.now(UTC)
    hours_nwpmap = [0, 12] # AUPQ, FXFE, FXJPは00UTCと12UTC

    # 直近2日間のデータを確認
    for i in range(2):
        day = now_utc - timedelta(days=i)
        # 現在時刻に近い方からチェック (例: 現在15UTCなら12UTCを先に、次に00UTC)
        # sorted(..., key=lambda x: abs(now_utc.hour - x)) は現在の時刻に近い時間から順に試す
        for h in sorted(hours_nwpmap, key=lambda x: abs(now_utc.hour - x)):
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            # 未来の時刻はダウンロードしない
            if target_time > now_utc:
                continue

            pdf_file = download_jma_nwpmap_pdf(chart_type, target_time)
            if pdf_file:
                return pdf_file
    print(f"直近2日以内の {chart_type.upper()} PDFが見つかりませんでした")
    return None

# -----------------------------------
# 3.2. 最新のJMA Hourly PNGを取得する関数 (FXJP106用)
# -----------------------------------
def get_latest_jma_hourly_png(chart_type_base, hours_list):
    now_utc = datetime.now(UTC)

    for i in range(2): # Check for current and previous day
        day = now_utc - timedelta(days=i)
        # Try hours in reverse order of closeness to now for current day, or reverse order for past days
        # This prioritizes latest available.
        candidate_hours = sorted(hours_list, key=lambda x: abs(now_utc.hour - x) if day.date() == now_utc.date() else x, reverse=True)
        for h in candidate_hours:
            target_time = day.replace(hour=h, minute=0, second=0, microsecond=0)
            if target_time > now_utc: # Don't try to download future charts
                continue

            png_file = download_jma_hourly_png(chart_type_base, target_time)
            if png_file:
                return png_file
    print(f"直近2日以内の {chart_type_base.upper()} PNGが見つかりませんでした")
    return None

# -----------------------------------
# 3.3. 最新のJMA Ashfall PDFを取得する関数 (桜島、霧島山用)
# -----------------------------------
def get_latest_jma_ashfall_pdf(chart_id, chart_name):
    JST = timezone(timedelta(hours=9)) # Define JST
    now_jst = datetime.now(JST) # Get current time in JST
    issuance_hours_jst = [2, 5, 8, 11, 14, 17, 20, 23] # Specific JST issuance hours

    # Iterate backwards through days (current day, then previous day)
    for i in range(2):
        day_to_check_jst = now_jst - timedelta(days=i)

        # Generate candidate datetimes for this day, in JST, in descending order
        candidate_datetimes_jst = []
        for h in issuance_hours_jst:
            candidate_time_jst = day_to_check_jst.replace(hour=h, minute=0, second=0, microsecond=0)
            if candidate_time_jst <= now_jst: # Only consider past or current hours
                candidate_datetimes_jst.append(candidate_time_jst)

        candidate_datetimes_jst.sort(reverse=True) # Sort to try latest first

        for target_time_jst in candidate_datetimes_jst:
            print(f"試行時刻 (JST): {target_time_jst.strftime('%Y%m%d%H%M')}") # Debug print for candidate time
            pdf_file = download_jma_ashfall_pdf(chart_id, target_time_jst) # Pass JST time
            if pdf_file:
                return pdf_file

    print(f"直近2日以内の {chart_name} (チャートID: {chart_id}) PDFが見つかりませんでした")
    return None

# -----------------------------------
# 3.4. 降灰予想図（UTC基準・バックアップ付き・安定版）3.3更新不具合に伴い追加
# -----------------------------------
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

    for i in range(2):  # 当日＋前日
        day = base_day - timedelta(days=i)

        for hh in candidate_hours:
            ash_time = day.replace(hour=hh, minute=0, second=0, microsecond=0)
            ts = ash_time.strftime("%Y%m%d%H%M%S")

            url = (
                "https://www.jma.go.jp/bosai/volcano/data/ashfall/pdf/"
                f"Z__C_RJTD_{ts}_EQV_CHT_JCIashfallr_{volcano_code}_N1_image.pdf"
            )

            filename = f"ASHFALL_{volcano_name}_{ts}.pdf"
            r = requests.get(url)

            if r.status_code == 200 and len(r.content) > 10240:
                with open(filename, "wb") as f:
                    f.write(r.content)
                print(f"取得成功（降灰予想）: {filename}")
                return filename
            else:
                print(f"未発行: {volcano_name} {ts}")

    print(f"取得失敗（全候補）: {volcano_name}")
    return None



# -----------------------------------
# 4. PDFをPNGに変換してDriveに保存
#    この関数はローカルにPNGを生成し、ローカルのGitHubリポジトリにコピーします
# -----------------------------------
def pdf_to_png_and_upload(pdf_file, final_drive_name):
    if pdf_file:
        png_filename_local = pdf_file.replace(".pdf", ".png") # ローカルでの一時ファイル名
        pages = convert_from_path(pdf_file, dpi=200)
        pages[0].save(png_filename_local, "PNG")

        # ローカルのGitHubリポジトリにコピー
        shutil.copy(png_filename_local, os.path.join(dest_folder_path, final_drive_name))
        print(f"Copied {png_filename_local} to {os.path.join(dest_folder_path, final_drive_name)}")

        # ローカルのPNGファイルを削除
        os.remove(png_filename_local)

        return True # 成功したことを示す
    else:
        print("PDFファイルがないためPNG化できません")
        return False

# -----------------------------------
# 4.1. PNGを直接Driveに保存
#      この関数はローカルにダウンロードされたPNGを、ローカルのGitHubリポジトリにコピーします
# -----------------------------------
def direct_png_upload(local_png_file, final_drive_name):
    if local_png_file:
        # ローカルのGitHubリポジトリにコピー
        shutil.copy(local_png_file, os.path.join(dest_folder_path, final_drive_name))
        print(f"Copied {local_png_file} to {os.path.join(dest_folder_path, final_drive_name)}")

        # ローカルのPNGファイルを削除
        os.remove(local_png_file)

        return True
    else:
        print("PNGファイルがないためアップロードできません")
        return False


# -----------------------------------
# 5. 実行
# -----------------------------------

# --- ASASチャートの処理 ---
latest_asas_pdf_local, prev_asas_pdf_local = get_latest_two_pdfs()

# 最新ASAS PDFをPNGに変換し、ASAS_Latest.pngとしてDriveにアップロード
pdf_to_png_and_upload(latest_asas_pdf_local, "ASAS_Latest.png")

# 一つ前のASAS PDFをPNGに変換し、ASAS_Prior.pngとしてDriveにアップロード
pdf_to_png_and_upload(prev_asas_pdf_local, "ASAS_Prior.png")

# ローカルのASAS PDFファイルを削除
if latest_asas_pdf_local and os.path.exists(latest_asas_pdf_local):
    os.remove(latest_asas_pdf_local)
    print(f"ローカルのPDFファイル {latest_asas_pdf_local} を削除しました。")
if prev_asas_pdf_local and os.path.exists(prev_asas_pdf_local):
    os.remove(prev_asas_pdf_local)
    print(f"ローカルのPDFファイル {prev_asas_pdf_local} を削除しました。")


# --- FSASチャートの処理 ---
fsas_pdf_local = download_fsas_pdf()

if fsas_pdf_local:
    # FSAS PDFをPNGに変換し、FSAS_Latest.pngとしてDriveにアップロード
    pdf_to_png_and_upload(fsas_pdf_local, "FSAS_Latest.png")

    # ローカルのFSAS PDFファイルを削除
    if os.path.exists(fsas_pdf_local):
        os.remove(fsas_pdf_local)
        print(f"ローカルのPDFファイル {fsas_pdf_local} を削除しました。")


# --- AUPQチャートの処理 ---
# AUPQ35
aupq35_pdf_local = get_latest_jma_nwpmap_pdf('aupq35')
if aupq35_pdf_local:
    pdf_to_png_and_upload(aupq35_pdf_local, "AUPQ35_Latest.png")
    if os.path.exists(aupq35_pdf_local):
        os.remove(aupq35_pdf_local)
        print(f"ローカルのPDFファイル {aupq35_pdf_local} を削除しました。")

# AUPQ78
aupq78_pdf_local = get_latest_jma_nwpmap_pdf('aupq78')
if aupq78_pdf_local:
    pdf_to_png_and_upload(aupq78_pdf_local, "AUPQ78_Latest.png")
    if os.path.exists(aupq78_pdf_local):
        os.remove(aupq78_pdf_local)
        print(f"ローカルのPDFファイル {aupq78_pdf_local} を削除しました。")


# --- FXFEチャートの処理 ---
# FXFE502
fxfe502_pdf_local = get_latest_jma_nwpmap_pdf('fxfe502')
if fxfe502_pdf_local:
    pdf_to_png_and_upload(fxfe502_pdf_local, "FXFE502_Latest.png")
    if os.path.exists(fxfe502_pdf_local):
        os.remove(fxfe502_pdf_local)
        print(f"ローカルのPDFファイル {fxfe502_pdf_local} を削除しました。")

# FXFE5782
fxfe5782_pdf_local = get_latest_jma_nwpmap_pdf('fxfe5782')
if fxfe5782_pdf_local:
    pdf_to_png_and_upload(fxfe5782_pdf_local, "FXFE5782_Latest.png")
    if os.path.exists(fxfe5782_pdf_local):
        os.remove(fxfe5782_pdf_local)
        print(f"ローカルのPDFファイル {fxfe5782_pdf_local} を削除しました。")


# --- FXJPチャートの処理 ---
# FXJP854
fxjp854_pdf_local = get_latest_jma_nwpmap_pdf('fxjp854')
if fxjp854_pdf_local:
    pdf_to_png_and_upload(fxjp854_pdf_local, "FXJP854_Latest.png")
    if os.path.exists(fxjp854_pdf_local):
        os.remove(fxjp854_pdf_local)
        print(f"ローカルのPDFファイル {fxjp854_pdf_local} を削除しました。")

# FXJP106
fxjp106_hours = [0, 3, 6, 9, 12, 15, 18, 21] # JMAの一般的な3時間ごとの更新を想定
fxjp106_png_local = get_latest_jma_hourly_png('fxjp106', fxjp106_hours)
if fxjp106_png_local:
    direct_png_upload(fxjp106_png_local, "FXJP106_Latest.png")


# --- FBJPチャートの処理 ---
fbjp_png_local = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/fbjp/fbjp.png", "FBJP_Latest")
if fbjp_png_local:
    direct_png_upload(fbjp_png_local, "FBJP_Latest.png")

# --- FBOS39チャートの処理 ---
fpos39_png_local = download_jma_png("https://www.data.jma.go.jp/airinfo/data/pict/low-level_sigwx/fbos39.png", "FBOS39_Latest")
if fpos39_png_local:
    direct_png_upload(fpos39_png_local, "FBOS39_Latest.png")


# --- 桜島・霧島山 降灰予報図の処理 ---
# --- 桜島 降灰予想図 ---
sakurajima_pdf_local = get_latest_jma_ashfall_pdf_stable("Sakurajima", "JR506X")
if sakurajima_pdf_local:
    pdf_to_png_and_upload(sakurajima_pdf_local, "Sakurajima_Ashfall_Latest.png")
    os.remove(sakurajima_pdf_local)

# --- 霧島山（新燃岳）降灰予想図 ---
kirishima_pdf_local = get_latest_jma_ashfall_pdf_stable("Kirishimayama", "JR551X")
if kirishima_pdf_local:
    pdf_to_png_and_upload(kirishima_pdf_local, "Kirishimayama_Ashfall_Latest.png")
    os.remove(kirishima_pdf_local)

# -----------------------------------
# 6. 全画像を1つのPDFにまとめる処理 (追加機能)
# -----------------------------------
def create_combined_pdf(image_folder, output_pdf_name):
    # PDFに含めたい画像のファイル名リスト（HTMLの並び順と同じにする）
    target_images = [
        "ASAS_Prior.png",
        "ASAS_Latest.png",
        "FSAS_Latest.png",
        "AUPQ35_Latest.png",
        "AUPQ78_Latest.png",
        "FXFE502_Latest.png",
        "FXFE5782_Latest.png",
        "FBJP_Latest.png",
        "FBOS39_Latest.png",
        "FXJP106_Latest.png",
        "FXJP854_Latest.png",
        "Sakurajima_Ashfall_Latest.png",
        "Kirishimayama_Ashfall_Latest.png"
    ]

    pdf_pages = []

    print("--- PDF結合処理開始 ---")
    
    for img_name in target_images:
        img_path = os.path.join(image_folder, img_name)
        
        if os.path.exists(img_path):
            try:
                # 画像を開く
                img = Image.open(img_path)
                
                # PDFにするためにRGBモードに変換（PNGはRGBAの場合があるため必須）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                pdf_pages.append(img)
                print(f"追加: {img_name}")
            except Exception as e:
                print(f"エラー（スキップ）: {img_name} -> {e}")
        else:
            print(f"未存在（スキップ）: {img_name}")

    if pdf_pages:
        output_path = os.path.join(image_folder, output_pdf_name)
        # 最初の画像をベースに、残りの画像をappendして保存
        pdf_pages[0].save(
            output_path, 
            save_all=True, 
            append_images=pdf_pages[1:]
        )
        print(f"PDF作成完了: {output_path}")
    else:
        print("結合する画像がありませんでした。")

# 実行
create_combined_pdf(dest_folder_path, "all_weather_charts.pdf")
