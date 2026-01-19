# Expected User Flows

## Checkout Flow
1. User adds items to cart
2. User clicks "Checkout"
3. User enters shipping information
4. User enters payment information
5. User clicks "Place Order"
6. Order confirmation displayed
7. Confirmation email sent

### Expected Behaviors
- Session timeout: 15 minutes of inactivity
- Cart persists for 24 hours
- Payment tokens valid for 10 minutes

## Login Flow
1. User enters email
2. User enters password
3. System validates credentials
4. Session created (24 hour expiry)
5. User redirected to dashboard

### Expected Behaviors
- Max 5 login attempts before lockout
- Lockout duration: 15 minutes
- Password reset link valid for 1 hour

## [Add more flows as needed]
