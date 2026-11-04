const url = $request ? $request.url : "";
function injectBadge(_0x1ec50e) {
  if (!_0x1ec50e || typeof _0x1ec50e !== "object") {
    return;
  }
  if ("badge" in _0x1ec50e || "uid" in _0x1ec50e || "username" in _0x1ec50e || "first_name" in _0x1ec50e || "phone_number" in _0x1ec50e) {
    _0x1ec50e.badge = "locket_gold";
    _0x1ec50e.badge_tier = "gold";
    _0x1ec50e.is_gold = true;
    _0x1ec50e.show_badge = true;
  }
  for (let _0x2e27fe in _0x1ec50e) {
    if (_0x1ec50e.hasOwnProperty(_0x2e27fe) && typeof _0x1ec50e[_0x2e27fe] === "object" && _0x1ec50e[_0x2e27fe] !== null) {
      injectBadge(_0x1ec50e[_0x2e27fe]);
    }
  }
}
if (url.includes("changeProfileInfo")) {
  $done({
    response: {
      status: 200,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*"
      },
      body: JSON.stringify({
        data: {
          badge: "locket_gold",
          badge_tier: "gold",
          is_gold: true,
          success: true
        },
        result: {
          badge: "locket_gold",
          badge_tier: "gold",
          is_gold: true,
          success: true
        }
      })
    }
  });
} else {
  let body = $response ? $response.body : null;
  if (body) {
    try {
      let obj = JSON.parse(body);
      injectBadge(obj);
      body = JSON.stringify(obj);
    } catch (a0_0x2f3ba8) {}
  }
  const a0_0x3b006b = {
    body: body
  };
  $done(a0_0x3b006b);
}