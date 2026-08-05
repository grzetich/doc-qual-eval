# Cash Balance

A customer's `Cash balance` represents real funds. Customers can add funds to their cash balance by sending a bank transfer. These funds can be used for payment and can eventually be paid out to your bank account.

## Endpoints

### Update a cash balance's settings

- [POST /v1/customers/:id/cash_balance](https://docs.stripe.com/api/cash_balance/update.md)

### Retrieve a cash balance

- [GET /v1/customers/:id/cash_balance](https://docs.stripe.com/api/cash_balance/retrieve.md)

## Events

- `cash_balance.funds_available`
Occurs whenever there is a positive remaining cash balance after Stripe automatically reconciles new funds into the cash balance. If you enabled manual reconciliation, this webhook will fire whenever there are new funds into the cash balance.
