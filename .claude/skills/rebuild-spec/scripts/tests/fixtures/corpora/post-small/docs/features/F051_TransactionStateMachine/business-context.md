# Business Context — F051_TransactionStateMachine

## Why It Matters

Every deal on the marketplace — from a buyer's first request to the seller receiving payment — follows a strict sequence of steps. This feature is the engine that enforces those steps: it ensures money is never released too early, payments are never left hanging indefinitely, and both parties are notified at the right moment. Without it, transactions could get stuck, funds could be held illegally, or sellers could never get paid.

## Who Uses It

- **Buyers** — their payment authorization is held and released correctly based on the deal outcome; they receive timely reminders to confirm receipt before the deadline passes
- **Sellers** — they are notified when a buyer requests a deal, when payment is captured, and when funds are released to them after confirmation
- **Marketplace administrators** — optionally notified by email when a new transaction starts in their community
- **The system itself** — schedules automatic fallbacks (auto-reject expired holds, auto-confirm after delivery windows) so no transaction is left unresolved

## What They Do

1. A buyer initiates a transaction — the system moves the deal to an "in progress" state and places a payment hold with the payment provider
2. If additional payment verification is required (for example, a bank security step), the system waits for completion; if the buyer does not complete it in time, the hold is automatically cancelled and the transaction is marked as not proceeding
3. Once payment is authorized, the seller receives a notification to accept or decline; the system starts a countdown — if the seller does not respond within the allowed window, the payment authorization is automatically released
4. When the seller accepts and payment is captured, the system starts a delivery countdown: for date-based bookings, the deadline is two days after the last booking date; for other transactions, the marketplace's configured confirmation window applies
5. If the buyer confirms receipt within the window, payment is released to the seller immediately
6. If the buyer does not confirm, the system automatically confirms and releases payment on their behalf — the seller always gets paid within the window
7. At any point where a problem occurs — payment failure, dispute, refund — the system routes the transaction to the correct outcome and notifies all relevant parties

## Unresolved Questions

- **Automatic confirmation window**: The exact number of days the marketplace administrator can configure for non-booking transactions was not confirmed from business documentation; behaviour depends on community settings.
- **Seller payout timing**: Whether payment is transferred to the seller immediately on confirmation or batched is handled by Stripe/PayPal payout jobs — not directly controlled by this feature's logic.
