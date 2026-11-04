const purchaseDate = "2024-05-18T08:30:00Z";
const expiresDate = "2099-12-31T23:59:59Z";
var ua = $request && $request.headers ? $request.headers["User-Agent"] || $request.headers["user-agent"] || "" : "";
var obj = {};
try {
  obj = JSON.parse($response.body);
} catch (a0_0x380b30) {
  obj = {};
}
obj.Attention = "Locket Gold VIP - Kích hoạt thành công bởi Minh Quân!";
// ===== Subscription "mẹ": locket_1600_1y (Gold) =====
var a0_0x18eb4b = {
  auto_resume_date: null,
  display_name: "locket_1600_1y",
  is_sandbox: false,
  ownership_type: "PURCHASED",
  billing_issues_detected_at: null,
  management_url: "https://apps.apple.com/account/subscriptions",
  period_type: "normal",
  price: {
    amount: 399000,
    currency: "VND"
  },
  expires_date: expiresDate,
  grace_period_expires_date: null,
  refunded_at: null,
  unsubscribe_detected_at: null,
  original_purchase_date: purchaseDate,
  purchase_date: purchaseDate,
  store: "app_store",
  store_transaction_id: "2000001108724193"
};
var locketGold = {
  grace_period_expires_date: null,
  purchase_date: purchaseDate,
  original_purchase_date: purchaseDate,
  product_identifier: "locket_1600_1y",
  expires_date: expiresDate,
  ownership_type: "PURCHASED",
  store: "app_store"
};

// ===== Hàm tạo entitlement phụ (cùng product/expiry) để app không bắt "nâng gói" =====
function makeEntitlement(productId) {
  return {
    grace_period_expires_date: null,
    purchase_date: purchaseDate,
    original_purchase_date: purchaseDate,
    product_identifier: productId,
    expires_date: expiresDate,
    ownership_type: "PURCHASED",
    store: "app_store"
  };
}
function makeSubscription(productId, displayName) {
  return {
    auto_resume_date: null,
    display_name: displayName || productId,
    is_sandbox: false,
    ownership_type: "PURCHASED",
    billing_issues_detected_at: null,
    management_url: "https://apps.apple.com/account/subscriptions",
    period_type: "normal",
    price: { amount: 399000, currency: "VND" },
    expires_date: expiresDate,
    grace_period_expires_date: null,
    refunded_at: null,
    unsubscribe_detected_at: null,
    original_purchase_date: purchaseDate,
    purchase_date: purchaseDate,
    store: "app_store",
    store_transaction_id: "2000001108724193"
  };
}

// ===== Danh sách entitlement mà Locket traversal để gate filter/photobooth/ai =====
var entitlementIds = [
  "Gold", "pro", "vip", "gold", "plus", "plus_gold", "premium", "mega",
  "unlimited", "unlimited_gold", "boost", "boosted", "locket_gold",
  "photos_booth", "photo_booth", "photobooth", "ai_filters", "ai_filter",
  "filters", "filters_v2", "camera_effects", "camera_effects_v2",
  "ar_filters", "face_filters", "lenses", "boomerang", "burst",
  "all_features", "full_access", "locket_plus", "locket_premium",
  "camera_roll", "live_photos", "widget_customization", "no_ads"
];
var productIds = [
  "locket_1600_1y",
  "locket_plus_1y",
  "locket_premium_1y",
  "locket_unlimited_1y",
  "locket_photos_booth_1y",
  "locket_ai_filters_1y",
  "locket_camera_effects_1y",
  "locket_boost_1y"
];

// ===== subscriber =====
obj.subscriber = obj.subscriber || {};
obj.subscriber.first_seen = purchaseDate;
obj.subscriber.original_purchase_date = purchaseDate;
obj.subscriber.management_url = "https://apps.apple.com/account/subscriptions";
obj.subscriber.subscriptions = obj.subscriber.subscriptions || {};
obj.subscriber.entitlements = obj.subscriber.entitlements || {};
obj.subscriber.non_subscriptions = obj.subscriber.non_subscriptions || {};

// product chính
obj.subscriber.subscriptions.locket_1600_1y = a0_0x18eb4b;

// mapping entitlement -> product (bao phủ mọi thứ app thử)
var entitlementToProduct = {};
var i;
for (i = 0; i < productIds.length; i++) {
  entitlementToProduct[productIds[i]] = productIds[i];
}
entitlementToProduct["Gold"] = "locket_1600_1y";
entitlementToProduct["gold"] = "locket_1600_1y";
entitlementToProduct["pro"] = "locket_1600_1y";
entitlementToProduct["vip"] = "locket_1600_1y";
entitlementToProduct["plus"] = "locket_plus_1y";
entitlementToProduct["plus_gold"] = "locket_plus_1y";
entitlementToProduct["premium"] = "locket_premium_1y";
entitlementToProduct["locket_premium"] = "locket_premium_1y";
entitlementToProduct["unlimited"] = "locket_unlimited_1y";
entitlementToProduct["unlimited_gold"] = "locket_unlimited_1y";
entitlementToProduct["photos_booth"] = "locket_photos_booth_1y";
entitlementToProduct["photo_booth"] = "locket_photos_booth_1y";
entitlementToProduct["photobooth"] = "locket_photos_booth_1y";
entitlementToProduct["ai_filters"] = "locket_ai_filters_1y";
entitlementToProduct["ai_filter"] = "locket_ai_filters_1y";
entitlementToProduct["filters"] = "locket_ai_filters_1y";
entitlementToProduct["filters_v2"] = "locket_ai_filters_1y";
entitlementToProduct["camera_effects"] = "locket_camera_effects_1y";
entitlementToProduct["camera_effects_v2"] = "locket_camera_effects_1y";
entitlementToProduct["ar_filters"] = "locket_camera_effects_1y";
entitlementToProduct["face_filters"] = "locket_camera_effects_1y";
entitlementToProduct["lenses"] = "locket_camera_effects_1y";
entitlementToProduct["boost"] = "locket_boost_1y";
entitlementToProduct["boosted"] = "locket_boost_1y";
entitlementToProduct["mega"] = "locket_unlimited_1y";
entitlementToProduct["boomerang"] = "locket_photos_booth_1y";
entitlementToProduct["burst"] = "locket_photos_booth_1y";
entitlementToProduct["all_features"] = "locket_unlimited_1y";
entitlementToProduct["full_access"] = "locket_unlimited_1y";
entitlementToProduct["locket_plus"] = "locket_plus_1y";
entitlementToProduct["camera_roll"] = "locket_plus_1y";
entitlementToProduct["live_photos"] = "locket_plus_1y";
entitlementToProduct["widget_customization"] = "locket_plus_1y";
entitlementToProduct["no_ads"] = "locket_1600_1y";

// Ghi subscriptions cho từng product ngoài product chính
for (i = 0; i < productIds.length; i++) {
  if (!obj.subscriber.subscriptions[productIds[i]]) {
    obj.subscriber.subscriptions[productIds[i]] = makeSubscription(productIds[i], productIds[i]);
  }
}

// Ghi entitlements
for (i = 0; i < entitlementIds.length; i++) {
  var ent = entitlementToProduct[entitlementIds[i]] || "locket_1600_1y";
  if (!obj.subscriber.entitlements[entitlementIds[i]]) {
    obj.subscriber.entitlements[entitlementIds[i]] = makeEntitlement(ent);
  }
}

// ===== offerings: để app tìm thấy gói Gold trong store (tránh "không có gói") =====
obj.offerings = {
  current: {
    identifier: "locket_gold",
    server_description: "Locket Gold",
    metadata: {},
    availablePackages: [
      { identifier: "$rc_monthly", platform_product_identifier: "locket_1600_1y" },
      { identifier: "$rc_annual", platform_product_identifier: "locket_1600_1y" },
      { identifier: "$rc_six_month", platform_product_identifier: "locket_1600_1y" },
      { identifier: "$rc_three_month", platform_product_identifier: "locket_1600_1y" }
    ]
  },
  all: []
};
obj.products = [
  {
    identifier: "locket_1600_1y",
    description: "Locket Gold",
    title: "Locket Gold",
    price: 399000,
    price_string: "399000 VND",
    currency_code: "VND",
    intro_eligibility_status: "eligible",
    period: "P1Y",
    period_unit: "YEAR",
    period_number_of_units: 1
  }
];

$done({
  body: JSON.stringify(obj)
});