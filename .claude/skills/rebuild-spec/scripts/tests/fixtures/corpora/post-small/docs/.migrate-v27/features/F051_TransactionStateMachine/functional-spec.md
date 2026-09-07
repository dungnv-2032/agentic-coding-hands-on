---
authored_by: rebuild-spec
---
# F051_TransactionStateMachine

**Priority**: P2
**Type**: background
**Generated**: migrated

**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source citations, pseudocode, key entities, and DB writes for a Dev/QA/SA audience.

## 1. Overview

**Problem:** Every deal on the marketplace — from a buyer's first request to the seller receiving payment — follows a strict sequence of steps. This feature is the engine that enforces those steps: it ensures money is never released too early, payments are never left hanging indefinitely, and both parties are notified at the right moment. Without it, transactions could get stuck, funds could be held illegally, or sellers could never get paid.

**Solution:** `TransactionProcessStateMachine` is the authoritative Statesman-based state machine that orchestrates all lifecycle transitions for Transaction records. It is triggered by controllers, payment service callbacks, and delayed_job workers; it fires after_transition hooks that enqueue side-effect jobs (email, payment void, auto-confirmation scheduling). No direct HTTP surface — purely internal.

**Users:**

- **Buyers** — their payment authorization is held and released correctly based on the deal outcome; they receive timely reminders to confirm receipt before the deadline passes
- **Sellers** — they are notified when a buyer requests a deal, when payment is captured, and when funds are released to them after confirmation
- **Marketplace administrators** — optionally notified by email when a new transaction starts in their community
- **The system itself** — schedules automatic fallbacks (auto-reject expired holds, auto-confirm after delivery windows) so no transaction is left unresolved

**Goals:**

1. A buyer initiates a transaction — the system moves the deal to an "in progress" state and places a payment hold with the payment provider
2. If additional payment verification is required (for example, a bank security step), the system waits for completion; if the buyer does not complete it in time, the hold is automatically cancelled and the transaction is marked as not proceeding
3. Once payment is authorized, the seller receives a notification to accept or decline; the system starts a countdown — if the seller does not respond within the allowed window, the payment authorization is automatically released
4. When the seller accepts and payment is captured, the system starts a delivery countdown: for date-based bookings, the deadline is two days after the last booking date; for other transactions, the marketplace's configured confirmation window applies
5. If the buyer confirms receipt within the window, payment is released to the seller immediately
6. If the buyer does not confirm, the system automatically confirms and releases payment on their behalf — the seller always gets paid within the window
7. At any point where a problem occurs — payment failure, dispute, refund — the system routes the transaction to the correct outcome and notifies all relevant parties

**Non-Goals:** None called out.

## 2. Open Decisions

None — no unresolved domain confirmations.

## 3. Requirements

### Foundation (0xx)

- **FR-001** State machine enforces valid transitions only via Statesman guards
- **FR-002** after_transition(after_commit:true) hooks enqueue side-effect jobs atomically with DB commit
- **FR-003** `current_state` and `last_transition_at` updated in every after_transition callback
- **FR-004** validate_before_preauthorized row-locks listing to prevent concurrent booking conflicts
- **FR-005** void_payment called on preauthorized transition failure
- **FR-006** AutomaticConfirmationJob checks `can_transition_to?(:confirmed)` before calling `transition_to`
- **FR-007** AutomaticBookingConfirmationJob sends `booking_transaction_automatically_confirmed` email via PersonMailer

## 4. Business Rules

- Listing row-locked; transaction and booking (if present) must be valid. Failure raises Statesman::TransitionFailedError. (BR-001)
- AutomaticallyRejectPreauthorizedTransactionJob scheduled at gateway expiration minus 10 minutes. PayPal and Stripe each have distinct expiration periods. Not scheduled in test environment. (BR-002)
- If booking present, auto-confirm at `booking.final_end + 2 days`. Otherwise uses community-configured automatic_confirmation period. (BR-003)
- New transaction email only sent if `community.email_admins_about_new_transactions` is truthy. (BR-004)
- Gateway adapter's `reject_payment` called to void the payment authorization. Errors logged but not re-raised (silent on payment void failure). (BR-005)
- Tracks the transaction lifecycle state machine (states: not_started, initiated, payment_intent_requires_action, preauthorized, pending_ext, paid, confirmed, canceled, rejected, errored, dismissed, disputed, refunded, free, payment_intent_failed, payment_intent_action_expired, pending (deprecated), accepted (deprecated)) (SM-001)
- Both jobs check `TransactionService::StateMachine.can_transition_to?(transaction.id, :confirmed)` before executing transition. If false, job silently exits (idempotent on double-run). (BR-006)
- If `PlanService::API::API.plans.get_current(community_id:).data[:expired]` is truthy, job returns without sending reminder — prevents notifications for expired marketplace plans. (BR-007)

## 5. Screens

N/A — background feature (no screens).

## 6. User Stories

### US190_SystemAutoConfirmTransaction — Auto-confirm transaction after timeout

When a transaction has been in `paid` state past the community's `automatic_confirmation_after_days` threshold (or past booking end + 2 days for booking transactions), the system transitions it to `confirmed`, releases payment to the seller, and notifies the requester.

**Acceptance Criteria:**
- [ ] state transitions to `confirmed` and TransactionAutomaticallyConfirmedJob enqueued
- [ ] state transitions to `confirmed` and booking confirmation email sent
- [ ] `can_transition_to?(:confirmed)` returns false, no duplicate transition

## 7. Scenarios

### US190_SystemAutoConfirmTransaction — Happy Path

**Given** a transaction in `paid` state older than community threshold, **When** AutomaticConfirmationJob runs, **Then** state transitions to `confirmed` and TransactionAutomaticallyConfirmedJob enqueued.

### US190_SystemAutoConfirmTransaction — Scenario 2

**Given** a booking transaction in `paid` state past `final_end + 2 days`, **When** AutomaticBookingConfirmationJob runs, **Then** state transitions to `confirmed` and booking confirmation email sent.

### US190_SystemAutoConfirmTransaction — Scenario 3

**Given** transaction already in `confirmed` state, **When** job runs, **Then** `can_transition_to?(:confirmed)` returns false, no duplicate transition.

## 8. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Auto-reject job fires but transaction was already manually accepted (now in `paid` state) | Job checks `current_state == 'preauthorized'`; condition false; job exits silently with no transition | None — silent no-op |
| Auto-confirm job fires on transaction already in `confirmed` state (double-enqueue) | `can_transition_to?(:confirmed)` returns false; job exits without error or duplicate transition | None — silent no-op |
| Buyer does not complete 3DS bank verification before the cancel job fires | `payment_intent_requires_action → payment_intent_action_expired` transition occurs; `reject_transaction` soft-deletes the record; payment authorization voided | Buyer sees transaction marked as not completed; no further action possible |
| Preauthorization guard fails due to double-booking (another transaction locks the listing row first) | `Statesman::TransitionFailedError` raised inside guard; `void_payment` called to release the authorization; transaction remains in prior state | Buyer's payment hold released; they may retry the booking |
| Unknown/unsupported payment gateway passed to `handle_preauthorized` | `ArgumentError` raised; no auto-reject job scheduled; transaction stuck in `preauthorized` indefinitely | No immediate user notification; requires manual operator intervention |
| Commission charge fails after `pending_ext → paid` transition (PayPal eCheck) | `charge_commission_and_retry` attempts retry; if permanently failed, `TransactionRetryChargeCommission` job enqueued | No direct buyer/seller message; internal operator alert via Airbrake |
| `void_payment` call fails during preauthorized transition failure | Error logged via MarketplaceLogger; failure silently swallowed; payment authorization may remain active at the gateway | No user-facing message; authorization eventually expires at gateway timeout |
| Marketplace plan expired when ConfirmReminderJob fires | Job checks plan status and returns early without sending email | None — reminder silently suppressed |

## 9. Edge Behaviours to Verify

- **FR-001** → — Transaction.current_state must equal the last TransactionTransition.to_state for any transaction
- **FR-006** → — AutomaticConfirmationJob exits cleanly when transaction not in `paid` state (idempotent)

## 10. Configuration

N/A — no user-facing configuration constants for this feature.
