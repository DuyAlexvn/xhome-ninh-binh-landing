const SHEET_NAME = 'Leads';
const SECRET_TOKEN = 'CHANGE_THIS_TO_A_LONG_RANDOM_SECRET';

const HEADERS = [
  'Thời gian gửi',
  'Họ tên',
  'Khu vực xây dựng',
  'Diện tích dự kiến',
  'Số tầng dự kiến',
  'Hạng mục quan tâm',
  'Thời gian triển khai',
  'Ngân sách dự kiến',
  'Số điện thoại/Zalo'
];

function doPost(e) {
  try {
    const rawBody = e && e.postData && e.postData.contents
      ? e.postData.contents
      : '{}';

    const payload = JSON.parse(rawBody);

    if (payload.token !== SECRET_TOKEN) {
      return jsonResponse({
        ok: false,
        error: 'Unauthorized'
      });
    }

    const lead = payload.lead || {};
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
    }

    ensureHeaders(sheet);

    const row = HEADERS.map(function(header) {
      return sanitizeCell(lead[header] || '');
    });

    sheet.appendRow(row);

    return jsonResponse({
      ok: true
    });
  } catch (err) {
    return jsonResponse({
      ok: false,
      error: String(err)
    });
  }
}

function doGet() {
  return jsonResponse({
    ok: true,
    message: 'Lead endpoint is running'
  });
}

function ensureHeaders(sheet) {
  const firstRow = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const hasHeader = firstRow.some(function(value) {
    return String(value || '').trim() !== '';
  });

  if (!hasHeader) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    return;
  }

  const currentHeaders = firstRow.map(function(value) {
    return String(value || '').trim();
  });

  const isSame = HEADERS.every(function(header, index) {
    return currentHeaders[index] === header;
  });

  if (!isSame) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
}

function sanitizeCell(value) {
  let text = String(value || '').trim();
  text = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
  text = text.replace(/\s+/g, ' ');
  text = text.slice(0, 300);

  if (/^[=+\-@\t\r]/.test(text)) {
    return "'" + text;
  }

  return text;
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
