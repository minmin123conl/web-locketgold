// Locket Filter Debugger — ghi log mọi request/response liên quan tới cấu hình
// Dùng 1 lần để tìm nơi Locket đọc danh sách filter/effect.
// Bật Shadowrocket Console/Log rồi mở app Locket -> phần filter.
var reqUrl = ($request && $request.url) ? $request.url : "";
var body = ($response && $response.body) ? $response.body : "";

// Chỉ quan tâm các host liên quan cấu hình/tính năng
var interesting = /locketcamera|revenuecat|rc-backup|firebaseremoteconfig|remoteconfig|firebaseio|locket-|firebaseauth|locket\.(app|camera)|appspot/i.test(reqUrl);

if (interesting) {
  // Tóm tắt body nếu có chứa từ khóa filter/effect
  var keywords = /filter|boomerang|lens|photobooth|effect|camera_effects|ai_filter|entitlement|subscription|feature/i.test(body);
  var preview = body;
  if (preview.length > 4000) preview = preview.substring(0, 4000) + "...[TRUNCATED]";
  console.log("===== LOCKET DEBUG =====");
  console.log("URL: " + reqUrl);
  console.log("HAS_FILTER_KEYWORDS: " + keywords);
  console.log("BODY: " + preview);
  console.log("===== END =====");
}

// Luôn trả về response gốc, không sửa đổi gì
if ($response) {
  $done({ body: body });
} else {
  // http-request: giữ nguyên
  $done({ body: body });
}