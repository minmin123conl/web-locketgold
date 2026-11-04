function setHeaderValue(_0x22f21f, _0x459459, _0x37d84e) {
    var _0xda408a = _0x459459.toLowerCase();
    if (_0xda408a in _0x22f21f) {
      _0x22f21f[_0xda408a] = _0x37d84e;
    } else {
      _0x22f21f[_0x459459] = _0x37d84e;
    }
  }
  var modifiedHeaders = $request && $request.headers ? $request.headers : {};
  setHeaderValue(modifiedHeaders, "X-RevenueCat-ETag", "");
  setHeaderValue(modifiedHeaders, "x-revenuecat-etag", "");
  setHeaderValue(modifiedHeaders, "If-None-Match", "");
  setHeaderValue(modifiedHeaders, "if-none-match", "");
  delete modifiedHeaders["X-RevenueCat-ETag"];
  delete modifiedHeaders["x-revenuecat-etag"];
  delete modifiedHeaders["If-None-Match"];
  delete modifiedHeaders["if-none-match"];
  var a0_0x30282c = {
    headers: modifiedHeaders
  };
  $done(a0_0x30282c);