# Edge Cases — F051_TransactionStateMachine

| Scenario | What Happens | User-Facing Message |
|----------|--------------|---------------------|
| Auto-reject job fires but transaction was already manually accepted (now in `paid` state) | Job checks `current_state == 'preauthorized'`; condition false; job exits silently with no transition | None — silent no-op |
| Auto-confirm job fires on transaction already in `confirmed` state (double-enqueue) | `can_transition_to?(:confirmed)` returns false; job exits without error or duplicate transition | None — silent no-op |
| Buyer does not complete 3DS bank verification before the cancel job fires | `payment_intent_requires_action → payment_intent_action_expired` transition occurs; `reject_transaction` soft-deletes the record; payment authorization voided | Buyer sees transaction marked as not completed; no further action possible |
| Preauthorization guard fails due to double-booking (another transaction locks the listing row first) | `Statesman::TransitionFailedError` raised inside guard; `void_payment` called to release the authorization; transaction remains in prior state | Buyer's payment hold released; they may retry the booking |
| Unknown/unsupported payment gateway passed to `handle_preauthorized` | `ArgumentError` raised; no auto-reject job scheduled; transaction stuck in `preauthorized` indefinitely | No immediate user notification; requires manual operator intervention |
| Commission charge fails after `pending_ext → paid` transition (PayPal eCheck) | `charge_commission_and_retry` attempts retry; if permanently failed, `TransactionRetryChargeCommission` job enqueued | No direct buyer/seller message; internal operator alert via Airbrake |
| `void_payment` call fails during preauthorized transition failure | Error logged via MarketplaceLogger; failure silently swallowed; payment authorization may remain active at the gateway | No user-facing message; authorization eventually expires at gateway timeout |
| Marketplace plan expired when ConfirmReminderJob fires | Job checks plan status and returns early without sending email | None — reminder silently suppressed |
