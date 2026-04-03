"""
気象レポートPDF 降水量ハイライター - Webサーバー
"""

import os
import tempfile
from itertools import groupby
from flask import Flask, request, send_file, jsonify
import pdfplumber
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB上限


# ---------- PDF処理ロジック ----------

def extract_rainfall_groups(pdf_path):
    """pdfplumberでセル境界と降水量データを正確に取得してグループ化"""
    page_groups = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words()

            mmh_tops = [w['top'] for w in words if w['text'] == 'mm/h']
            if not mmh_tops:
                continue

            tset = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
            tables = page.find_tables(tset)
            if not tables:
                continue
            all_cells = tables[0].cells

            rainfall_boxes = []
            for w in words:
                in_row = any(abs(w['top'] - mt) <= 8 for mt in mmh_tops)
                if not in_row:
                    continue
                try:
                    val = float(w['text'])
                    if val <= 0:
                        continue
                    cx = (w['x0'] + w['x1']) / 2
                    cy = (w['top'] + w['bottom']) / 2
                    for cell in all_cells:
                        if cell[0] <= cx <= cell[2] and cell[1] <= cy <= cell[3]:
                            rainfall_boxes.append({
                                'value': val,
                                'x0': cell[0], 'top': cell[1],
                                'x1': cell[2], 'bottom': cell[3],
                                'row_top': round(cell[1], 1)
                            })
                            break
                except ValueError:
                    pass

            groups = []
            boxes_sorted = sorted(rainfall_boxes, key=lambda c: (c['row_top'], c['x0']))
            for _, row_boxes in groupby(boxes_sorted, key=lambda c: c['row_top']):
                row_boxes = list(row_boxes)
                current = [row_boxes[0]]
                for box in row_boxes[1:]:
                    if box['x0'] - current[-1]['x1'] <= 25:
                        current.append(box)
                    else:
                        groups.append(current)
                        current = [box]
                groups.append(current)

            page_groups.append({
                'page_num': page_num,
                'page_height': page.height,
                'groups': groups
            })

    return page_groups


def draw_highlights(input_path, output_path, page_groups):
    """pypdfium2でセル境界に合わせた水色の枠を描画"""
    doc = pdfium.PdfDocument(input_path)
    SKY_R, SKY_G, SKY_B = 0, 176, 240

    for pg in page_groups:
        page = doc[pg['page_num']]
        pdf_h = page.get_height()
        pl_h = pg['page_height']

        for group in pg['groups']:
            gx0 = min(c['x0'] for c in group)
            gx1 = max(c['x1'] for c in group)
            gtop = min(c['top'] for c in group)
            gbottom = max(c['bottom'] for c in group)

            pdf_x0 = gx0
            pdf_y0 = pdf_h - gbottom * (pdf_h / pl_h)
            pdf_y1 = pdf_h - gtop * (pdf_h / pl_h)

            rect = pdfium_c.FPDFPageObj_CreateNewRect(
                pdf_x0, pdf_y0, gx1 - gx0, pdf_y1 - pdf_y0
            )
            pdfium_c.FPDFPageObj_SetStrokeColor(rect, SKY_R, SKY_G, SKY_B, 255)
            pdfium_c.FPDFPageObj_SetStrokeWidth(rect, 1.5)
            pdfium_c.FPDFPath_SetDrawMode(rect, 0, 1)
            pdfium_c.FPDFPage_InsertObject(page.raw, rect)

        pdfium_c.FPDFPage_GenerateContent(page.raw)

    doc.save(output_path)


# ---------- ルーティング ----------

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/process', methods=['POST'])
def process():
    if 'pdf' not in request.files:
        return jsonify({'error': 'PDFファイルが見つかりません'}), 400

    file = request.files['pdf']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'PDFファイルのみ対応しています'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.pdf')
        output_path = os.path.join(tmpdir, 'output.pdf')

        file.save(input_path)

        page_groups = extract_rainfall_groups(input_path)

        total_cells = sum(len(g) for pg in page_groups for g in pg['groups'])
        total_groups = sum(len(pg['groups']) for pg in page_groups)

        if total_cells == 0:
            return jsonify({'error': '降水量データが見つかりませんでした。気象レポートのPDFか確認してください。'}), 400

        draw_highlights(input_path, output_path, page_groups)

        base_name = os.path.splitext(file.filename)[0]
        download_name = base_name + '_ハイライト済.pdf'

        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=download_name
        )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
