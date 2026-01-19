# Known Error Patterns

<!-- Add entries as you encounter and resolve errors -->

## Template

### [Error Name]
- **Sentry Error:** `ErrorClassName` or error message pattern
- **Root Cause:** What actually happened
- **User Impact:** What the user experienced
- **Resolution:** How to fix / what to tell customer
- **Customer Response:** Copy-paste response for CS

---

## Example Entry

### Payment Token Expired
- **Sentry Error:** `PaymentTokenExpiredError` or "token expired"
- **Root Cause:** User took longer than 10 minutes on payment page
- **User Impact:** "Payment failed" error on checkout
- **Resolution:** User needs to restart checkout
- **Customer Response:** "Hi! It looks like your payment session timed out - this happens if the checkout page is open for more than 10 minutes. Please try checking out again, and let me know if you run into any issues!"

---

<!-- Add new errors below as they're resolved -->
