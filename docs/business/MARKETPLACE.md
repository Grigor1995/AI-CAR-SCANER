# Marketplace

2026-10-29 · Existing AI-CAR-SCANER · baseline 082b71d.

PARTIALLY IMPLEMENTED overall. Merchant registration creates an unverified
shop and MARKET portal entitlement. Suspending the merchant owner also hides listings and blocks quotes. Merchants create/update own products, price
in minor units, supported currency, stock, HTTPS image reference and declared
fitment. An HTTPS URL is not an image-upload storage service. Images are not
fetched by the backend. Products are hidden until seller verified, active,
listing enabled and admin moderation approved. Updates reset moderation.

Offers: PUBLIC/CUSTOMER/CENTER audiences, quantity threshold, aware validity
interval and optional exact coupon. Professional price requires active staff in
a verified active center; discount never follows a client-supplied mode alone.
Apply highest eligible basis points; no stacking; floor discount to minor unit.
Quote checks stock but reserves nothing. Fitment may be SELLER_CLAIM_UNVERIFIED,
NO_MATCHING_CLAIM or UNKNOWN; never CONFIRMED.

Pending: upload storage, inventory audit/versioning, native merchant editors,
verified manufacturer/OEM fitment feeds and abuse workflows. Payments/checkout
UNSUPPORTED intentionally; future architectural seam only, no credentials stored.
