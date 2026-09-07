# Feature packets to label

Each item below is ONE feature as it exists today.

### ITEM-01
**Name:** Authentication
**Type:** mixed
**Description:** Login, registration, password reset, logout, and access-denied flows. Core entry point for all authenticated member activity.

**User stories (5):**
- US020_RegisterAccount: Register a new account
- US021_Login: Log in with email and password
- US023_RequestPasswordReset: Request a password reset email
- US028_Logout: Log out of the current session
- US030_ViewAccessDenied: View access-denied page

**Screens (5):**
- SCR020_LoginPage: Login Page
- SCR021_SignupPage: Registration Page
- SCR025_PasswordResetRequest: Password Reset Request
- SCR028_AccessDenied: Access Denied
- SCR001_Homepage: Homepage (logout via topbar)

**Background logic (3):**
- BL027_SendWelcomeEmail: Send Welcome Email
- BL013_EmailConfirmation: Email Confirmation Sender
- BL006_CommunityJoined: Community Joined Handler

**Routes (5):**
- (POST) /people
- (POST) /sessions
- (DELETE) /sessions/:id
- (POST) /sessions/request_new_password
- (GET) /community_memberships/access_denied

**Data models (4):**
- MODEL001 — Community
- MODEL002 — Person
- CommunityMembership
- Email

---

### ITEM-02
**Name:** PayPal Transaction Flow
**Type:** mixed
**Description:** PayPal operation status polling, success, and cancel pages. PayPal permission and billing agreement request screens.

**User stories (5):**
- US068_ViewPayPalOpStatus: View PayPal operation polling status
- US069_ViewPayPalSuccess: View PayPal payment success page
- US070_ViewPayPalCancelled: View PayPal payment cancelled page
- US100_RequestPayPalOrderPermission: Request PayPal order permission
- US101_RequestPayPalBillingAgreement: Request PayPal billing agreement

**Screens (7):**
- SCR095_PayPalOpStatus: PayPal Operation Status
- SCR096_PayPalSuccess: PayPal Payment Success
- SCR097_PayPalCancel: PayPal Payment Cancelled
- SCR098_TransactionOpStatus: Transaction Operation Status
- SCR099_FinalizeProcessed: Finalize Processed Transaction
- SCR100_PayPalAskOrderPermission: PayPal Permissions Initiation
- SCR101_PayPalAskBillingAgreement: PayPal Billing Agreement Request

**Background logic (2):**
- BL056_PaypalServiceAPIPayments: PayPal Payments API Integration
- BL079_PaypalEvents: PayPal Transaction Event Handlers

**Routes (5):**
- (GET) /transactions/op_status/:process_token
- (GET) /paypal_service/checkout_orders/success
- (GET) /paypal_service/checkout_orders/cancel
- (GET) /:person_id/paypal_account/ask_order_permission
- (GET) /:person_id/paypal_account/ask_billing_agreement

**Data models (3):**
- PaypalPayment
- PaypalAccount
- Transaction

---

### ITEM-03
**Name:** Admin SEO & Social Media Settings
**Type:** ui
**Description:** Configure OG image tags, Twitter settings, sitemap/robots.txt, and per-page SEO meta tags. Social share button configuration.

**User stories (10):**
- US170_ConfigureSocialShareButtons: Configure social share button settings
- US171_ConfigureOGImageTags: Configure OG image and meta tag settings
- US172_ConfigureTwitterSettings: Configure Twitter/X sharing settings
- US173_ConfigureSitemapRobots: Configure sitemap and robots.txt settings
- US174_ConfigureGoogleSearchConsole: Configure Google Search Console verification
- US175_ConfigureLandingPageMeta: Configure landing page SEO meta tags
- US176_ConfigureSearchPageMeta: Configure search page SEO meta tags
- US177_ConfigureListingPageMeta: Configure listing page SEO meta tags
- US178_ConfigureCategoryPageMeta: Configure category page SEO meta tags
- US179_ConfigureProfilePageMeta: Configure profile page SEO meta tags

**Screens (12):**
- SCR227_Admin2SocialShareButtons: Social Share Button Settings
- SCR228_Admin2ImageTags: OG Image & Meta Tag Settings
- SCR229_Admin2Twitter: Twitter / X Settings
- SCR230_Admin2SitemapRobots: Sitemap & Robots Settings
- SCR231_Admin2GoogleConsole: Google Search Console Settings
- SCR232_Admin2LandingPageMeta: Landing Page Meta Tags
- SCR233_Admin2SearchPageMeta: Search Page Meta Tags
- SCR234_Admin2ListingPageMeta: Listing Page Meta Tags
- SCR235_Admin2CategoryPageMeta: Category Page Meta Tags
- SCR236_Admin2ProfilePageMeta: Profile Page Meta Tags
- SCR174_AdminOldSEO: SEO Settings (legacy)
- SCR157_AdminOldSocialMedia: Social Media Settings (legacy)

**Background logic (1):**
- BL051_RobotsGenerator: Dynamic Robots.txt Generator

**Routes (10):**
- (GET) /admin/social-media/social-share-buttons
- (GET) /admin/social-media/image-and-tags
- (GET) /admin/social-media/twitter
- (GET) /admin/seo/sitemap-and-robots
- (GET) /admin/seo/google-search-console
- (GET) /admin/seo/landing-page-meta-tags
- (GET) /admin/seo/search-page-meta-tags
- (GET) /admin/seo/listing-pages-meta-tags
- (GET) /admin/seo/category-pages-meta-tags
- (GET) /admin/seo/profile-pages-meta-tags

**Data models (2):**
- MODEL001 — Community
- CommunityCustomization

---

### ITEM-04
**Name:** Terms Consent
**Type:** ui
**Description:** Terms-of-service acceptance gate for members with pending_consent status. Blocks access until accepted.

**User stories (1):**
- US025_AcceptTermsConsent: Accept terms of service consent

**Screens (2):**
- SCR008_TermsAccept: Terms Accept Form
- SCR027_PendingConsent: Terms Consent Pending

**Background logic (1):**
- (none)

**Routes (2):**
- (GET) /terms
- (POST) /terms

**Data models (1):**
- CommunityMembership

---

### ITEM-05
**Name:** Admin Essential & Privacy Settings
**Type:** ui
**Description:** Edit marketplace name, currency, locale, privacy mode, invite-only, domain, static content, and admin notification settings.

**User stories (5):**
- US117_EditEssentialSettings: Edit essential marketplace settings
- US118_EditPrivacySettings: Edit marketplace privacy settings
- US119_EditDomainSettings: Edit or configure custom domain
- US120_EditStaticContent: Edit static content pages
- US147_ViewAdminNotificationSettings: View and update admin notification settings

**Screens (8):**
- SCR182_Admin2Essentials: Essential Settings
- SCR183_Admin2AdminNotifications: Admin Notification Settings
- SCR184_Admin2StaticContent: Static Content Settings
- SCR185_Admin2Privacy: Privacy Settings
- SCR186_Admin2Domains: Domain Management
- SCR148_AdminOldCommunityDetails: Edit Community Details (legacy)
- SCR152_AdminOldSettings: Admin Settings (legacy)
- SCR173_AdminOldDomain: Domain Settings (legacy)

**Background logic (1):**
- BL017_IdentChanged: Ident Changed Handler

**Routes (10):**
- (GET) /admin/general/essentials
- (PUT) /admin/general/essentials
- (GET) /admin/general/privacy
- (PUT) /admin/general/privacy
- (GET) /admin/general/domain
- (PUT) /admin/general/domain
- (GET) /admin/general/static-content
- (PUT) /admin/general/static-content
- (GET) /admin/general/admin-notifications
- (PUT) /admin/general/admin-notifications

**Data models (3):**
- MODEL001 — Community
- CommunityCustomization
- DomainSetup

---

### ITEM-06
**Name:** Maintenance & Operational Tasks
**Type:** background
**Description:** Rake tasks for DB maintenance, GDPR data deletion, Stripe capabilities updates, data exports, deployment, and test tooling.

**User stories (1):**
- (none — operational)

**Screens (1):**
- (none — CLI only)

**Background logic (15):**
- BL081_MarketplaceRake: Marketplace Main Rake Tasks
- BL082_MarketplaceDBRake: Marketplace DB Maintenance Rake Tasks
- BL083_MarketplaceDataDeletionRake: GDPR Data Deletion Rake Tasks
- BL084_MarketplaceStripeRake: Stripe Management Rake Tasks
- BL085_ExportRake: Data Export Rake Tasks
- BL086_DeployRake: Deployment Rake Tasks
- BL087_HerokuRake: Heroku Deploy Rake Tasks
- BL088_DBRake: Custom DB Rake Tasks
- BL089_AssetsRake: Asset Pipeline Rake Tasks
- BL090_MigrateClpImagesRake: CLP Image Migration Rake Task
- BL091_CsExtractRake: Customer Support Data Extract
- BL092_TestSeedRake: Test Data Seed Rake Task
- BL093_AutoAnnotateModelsRake: Model Auto-Annotation Rake Task
- BL094_CucumberRake: Cucumber Test Runner Rake Config
- BL011_DelayedAirbrakeNotification: Delayed Airbrake Notification

**Routes (1):**
- (none — rake tasks)

**Data models (3):**
- MODEL001 — Community
- MODEL002 — Person
- StripeAccount

---

### ITEM-07
**Name:** Transaction Initiation
**Type:** mixed
**Description:** Initiate a transaction: free contact form for sellers and preauthorized payment checkout. Post-creation confirmation screen.

**User stories (4):**
- US060_InitiateFreeContact: Contact a seller via free contact form
- US061_InitiatePreauthorizeCheckout: Initiate a preauthorized payment checkout
- US062_ViewTransactionConfirmation: View post-creation transaction confirmation
- US063_ViewTransactionDetail: View own transaction detail

**Screens (5):**
- SCR094_FreeContactForm: Contact Seller Form
- SCR091_PreauthorizeCheckout: Preauthorize Checkout
- SCR090_TransactionNew: New Transaction Form
- SCR092_TransactionCreated: Post-Creation Confirmation
- SCR093_TransactionShow: Transaction Detail

**Background logic (3):**
- BL025_SendNewTransactionEmail: Send New Transaction Email
- BL038_TransactionPreauthorized: Transaction Preauthorized Handler
- BL080_TransactionProcessStateMachine: Transaction Process State Machine

**Routes (6):**
- (GET) /listings/:listing_id/contact
- (POST) /listings/:listing_id/contact
- (GET) /listings/:listing_id/initiate
- (POST) /transactions
- (GET) /transactions/created/:transaction_id
- (GET) /:person_id/transactions/:id

**Data models (6):**
- Transaction
- Conversation
- Message
- Booking
- StripePayment
- PaypalPayment

---

### ITEM-08
**Name:** Admin Email & Newsletter Management
**Type:** mixed
**Description:** Compose and send bulk emails, configure welcome email, newsletter, outgoing email address with SES verification.

**User stories (5):**
- US165_ComposeBulkEmail: Compose and send a bulk email to members
- US166_ConfigureWelcomeEmail: Configure welcome email content
- US167_ConfigureNewsletter: Configure automatic newsletter settings
- US168_ConfigureOutgoingEmail: Configure custom outgoing email address
- US169_EditOutgoingEmailAddress: Edit an existing outgoing email address

**Screens (6):**
- SCR220_Admin2ComposeEmail: Compose Bulk Email
- SCR221_Admin2OutgoingAddress: Custom Outgoing Email Address
- SCR222_Admin2OutgoingAddressEdit: Edit Outgoing Address
- SCR223_Admin2WelcomeEmail: Welcome Email Settings
- SCR224_Admin2Newsletter: Newsletter / Auto-Email Settings
- SCR156_AdminOldWelcomeEmail: Edit Welcome Email (legacy)

**Background logic (5):**
- BL009_CreateMemberEmailBatch: Create Member Email Batch
- BL007_CommunityMemberEmailSent: Community Member Email Sent
- BL043_CommunityMailer: Community Mailer
- BL067_EmailServiceSESClient: SES Email Client
- BL072_EmailServiceJobsRequestVerification: Email Service Request Verification

**Routes (10):**
- (GET) /admin/emails/compose-email
- (POST) /admin/emails/compose-email
- (GET) /admin/emails/welcome-email
- (PUT) /admin/emails/welcome-email
- (GET) /admin/emails/automatic-newsletter
- (PUT) /admin/emails/automatic-newsletter
- (GET) /admin/emails/custom-outgoing-address
- (POST) /admin/emails/custom-outgoing-address
- (GET) /admin/emails/custom-outgoing-address/:id/edit
- (PUT) /admin/emails/custom-outgoing-address/:id

**Data models (3):**
- MODEL001 — Community
- MODEL002 — Person
- Email

---

### ITEM-09
**Name:** Email Confirmation
**Type:** mixed
**Description:** Email verification flow after registration or email change. Token-based confirmation with resend capability.

**User stories (1):**
- US024_ConfirmEmail: Confirm email address via link

**Screens (2):**
- SCR022_EmailConfirmation: Email Confirmation Landing
- SCR023_ConfirmationPending: Awaiting Confirmation Notice

**Background logic (1):**
- BL013_EmailConfirmation: Email Confirmation Sender

**Routes (1):**
- (GET) /people/confirmation?confirmation_token=...

**Data models (3):**
- Email
- CommunityMembership
- MODEL002 — Person

---

### ITEM-10
**Name:** Admin Branding & Design
**Type:** ui
**Description:** Configure marketplace logos, colors, cover photos, topbar, footer, and listing layout arrangement.

**User stories (5):**
- US113_EditBranding: Edit marketplace logos and colors
- US114_EditCoverPhotos: Upload cover photos
- US115_EditTopbar: Edit topbar navigation links
- US116_EditFooter: Edit footer links and content
- US121_EditLayoutArrangement: Configure listing display arrangement

**Screens (8):**
- SCR192_Admin2LogosColor: Logos & Color Settings
- SCR193_Admin2CoverPhotos: Cover Photos Settings
- SCR189_Admin2Topbar: Topbar Settings
- SCR190_Admin2Footer: Footer Settings
- SCR191_Admin2Arrangement: Layout / Arrangement Settings
- SCR147_AdminOldLookAndFeel: Edit Branding / Colors
- SCR149_AdminOldTopbarEdit: Edit Topbar Menu
- SCR150_AdminOldFooterEdit: Edit Footer

**Background logic (1):**
- BL010_CreateSquareImages: Create Square Image Thumbnails

**Routes (10):**
- (GET) /admin/design/logos-and-color
- (PUT) /admin/design/logos-and-color
- (GET) /admin/design/cover-photos
- (PUT) /admin/design/cover-photos
- (GET) /admin/design/top-bar
- (PUT) /admin/design/top-bar
- (GET) /admin/design/footer
- (PUT) /admin/design/footer
- (GET) /admin/design/arrangement
- (PUT) /admin/design/arrangement

**Data models (2):**
- CommunityCustomization
- MarketplaceConfigurations

---

### ITEM-11
**Name:** Stripe Payment Integration
**Type:** background
**Description:** Stripe Connect payment operations, account management, capabilities update, and reporting.

**User stories (1):**
- (none — underlying payment service)

**Screens (1):**
- (none — service layer)

**Background logic (8):**
- BL062_StripeServiceAPIPayments: Stripe Payments API Integration
- BL063_StripeServiceAPIAccounts: Stripe Accounts API Integration
- BL064_StripeServiceAPIWrapper: Stripe API Wrapper
- BL065_StripeServiceCapabilitiesUpdate: Stripe Capabilities Update
- BL066_StripeServiceReport: Stripe Report
- BL029_StripePayoutJob: Stripe Payout
- BL037_TransactionPaymentIntentCancel: Transaction Payment Intent Cancel
- BL041_TransactionRetryChargeCommission: Transaction Retry Charge Commission

**Routes (1):**
- (none — internal service calls)

**Data models (3):**
- StripePayment
- StripeAccount
- Transaction

---

### ITEM-12
**Name:** Listing Discovery & Search
**Type:** mixed
**Description:** Homepage search, category/price filters, keyword search, and map-based geo browsing. Sphinx full-text search.

**User stories (5):**
- US001_BrowseListings: Browse listing search results
- US002_FilterListings: Filter listings by category/price/location
- US013_SearchByKeyword: Search listings by keyword
- US014_ViewMapPins: View listing locations on map
- US027_ViewInlineSignIn: View inline sign-in panel on homepage

**Screens (6):**
- SCR001_Homepage: Homepage / Search
- SCR001_Homepage/REG001: SearchResults region
- SCR001_Homepage/REG002: MapViewport region
- SCR060_ListingsBrowse: Browse / Search All Listings
- SCR026_HomepageSignIn: Inline Sign-In Panel
- SCR001_Homepage/REG003: SignInBanner region

**Background logic (1):**
- BL077_DiscoveryClient: Discovery Client

**Routes (5):**
- (GET) /
- (GET) /listings
- (GET) /:locale/more_listings
- (GET) /listings/locations_json
- (GET) /homepage/sign_in

**Data models (3):**
- Listing
- Category
- MODEL001 — Community

---

### ITEM-13
**Name:** Admin Listing Moderation
**Type:** mixed
**Description:** View all community listings, approve/reject pending listings, move to top of search, configure listing approval and comments settings. CSV export.

**User stories (8):**
- US135_ConfigureListingApproval: Configure listing approval settings
- US136_ConfigureListingComments: Configure listing comments on/off
- US148_ViewAllListingsAdmin: View all community listings in admin panel
- US149_ApproveListingAdmin: Approve a pending listing
- US150_RejectListingAdmin: Reject a pending listing
- US151_MoveListingToTop: Move a listing to top of search results
- US155_ExportListingsCSV: Export community listings as CSV
- US196_SystemExportListingsJob: Run async listings CSV export job

**Screens (4):**
- SCR206_Admin2ManageListings: Manage All Listings
- SCR207_Admin2ListingApproval: Listing Approval Settings
- SCR208_Admin2ListingComments: Listing Comments Settings
- SCR159_AdminOldCommunityListings: Manage Community Listings (legacy)

**Background logic (2):**
- BL014_ExportListings: Export Listings to CSV
- BL005_CommentCreated: Comment Created Notification

**Routes (7):**
- (GET) /admin/listings/manage-listings
- (PUT) /admin/listings/manage-listings/:id
- (PUT) /listings/:id/move_to_top
- (GET) /admin/listings/listing-approval
- (PUT) /admin/listings/listing-approval
- (GET) /admin/listings/listing-comments
- (PUT) /admin/listings/listing-comments

**Data models (2):**
- Listing
- MODEL001 — Community

---

### ITEM-14
**Name:** OAuth Login
**Type:** mixed
**Description:** OAuth-based login and account creation via Google, Facebook, and LinkedIn providers. Handles callback, account linking, and consent gate.

**User stories (1):**
- US022_LoginOAuth: Log in via OAuth provider

**Screens (2):**
- SCR024_OAuthCallback: OAuth Callback Handler
- SCR020_LoginPage: Login Page (OAuth buttons)

**Background logic (1):**
- BL006_CommunityJoined: Community Joined Handler

**Routes (2):**
- (GET) /people/auth/:provider/callback
- (POST) /people/auth/:provider/callback

**Data models (2):**
- MODEL002 — Person
- CommunityMembership

---

### ITEM-15
**Name:** Static & Info Pages
**Type:** ui
**Description:** Static information pages: About, How To Use, Terms, Privacy, News. Also error pages and system screens.

**User stories (6):**
- US007_ViewCustomLandingPage: View custom landing page
- US008_ViewAboutPage: View About page
- US009_ViewTermsPage: View Terms of Service
- US010_ViewPrivacyPage: View Privacy Policy
- US011_ViewHowToUsePage: View How To Use page
- US012_ViewNewsPage: View News/Blog page

**Screens (16):**
- SCR003_AboutPage: About Page
- SCR004_HowToUsePage: How To Use Page
- SCR005_TermsPage: Terms of Service
- SCR006_PrivacyPage: Privacy Policy
- SCR007_NewsPage: News / Blog
- SCR002_LandingPage: Custom Landing Page
- SCR009_ConsentPage: Consent Page
- SCR010_DesignPage: Style Guide
- SCR011_SitemapPage: Sitemap
- SCR012_ErrorNotFound: 404 Not Found
- SCR013_ErrorServer: 500 Server Error
- SCR014_ErrorNotAcceptable: 406 Not Acceptable
- SCR015_ErrorGone: 410 Gone
- SCR016_ErrorCommunityNotFound: Community Not Found
- SCR017_NotAvailable: Community Not Available
- SCR018_EmailDesign: Email Template Preview

**Background logic (1):**
- (none)

**Routes (6):**
- (GET) /infos/about
- (GET) /infos/how_to_use
- (GET) /infos/terms
- (GET) /infos/privacy
- (GET) /infos/news
- (GET) /:locale/

**Data models (3):**
- MODEL001 — Community
- CommunityCustomization
- LandingPageVersion

---

### ITEM-16
**Name:** Request Processing Middleware
**Type:** background
**Description:** Core Rack middleware stack: marketplace lookup (multi-tenancy), SSL enforcement, health check, cookie isolation, robots.txt generation, and session context.

**User stories (1):**
- (none — system only)

**Screens (1):**
- (none — middleware layer)

**Background logic (8):**
- BL046_MarketplaceLookup: Marketplace Lookup Middleware
- BL047_MarketplaceHostFromCustomHeader: Marketplace Host Header Override
- BL048_EnforceSsl: Enforce SSL Middleware
- BL049_HealthCheck: Health Check Middleware
- BL050_CustomCookieRenamer: Custom Cookie Renamer
- BL051_RobotsGenerator: Dynamic Robots.txt Generator
- BL052_SessionContextMiddleware: Session Context Middleware
- BL028_SessionContextSerializer: Session Context Serializer

**Routes (2):**
- (GET) /health
- (GET) /robots.txt

**Data models (2):**
- MODEL001 — Community
- MODEL002 — Person

---

### ITEM-17
**Name:** Public Profile & People
**Type:** ui
**Description:** Public user profile page, members list, followers, followed people, and public feedback list.

**User stories (5):**
- US004_ViewSellerProfile: View a seller's public profile
- US005_BrowseMembersList: Browse all community members
- US017_ViewFollowersList: View own followers list
- US018_ViewFollowedPeopleList: View people I follow
- US019_ViewFeedbackList: View public feedback list

**Screens (5):**
- SCR040_PublicProfile: Public User Profile
- SCR041_PeopleList: People / Members List
- SCR049_FollowersList: Followers List
- SCR050_FollowedPeopleList: Followed People List
- SCR058_UserFeedbackList: User Feedback List

**Background logic (1):**
- (none)

**Routes (5):**
- (GET) /:username
- (GET) /people
- (GET) /:person_id/followers
- (GET) /:person_id/followed_people
- (GET) /user_feedbacks

**Data models (4):**
- MODEL002 — Person
- CommunityMembership
- FollowerRelationship
- Testimonial

---

### ITEM-18
**Name:** Admin User Management
**Type:** ui
**Description:** View, ban/unban members, and manage listing posting permissions. Filter by status.

**User stories (5):**
- US141_ViewMembersList: View all community members
- US142_BanMember: Ban a community member
- US143_UnbanMember: Unban a previously banned member
- US144_GrantPostingPermission: Grant a member the listing posting flag
- US145_RevokePostingPermission: Revoke a member's listing posting flag

**Screens (2):**
- SCR195_Admin2ManageUsers: Manage Users List
- SCR162_AdminOldCommunityMembers: Manage Members (legacy)

**Background logic (1):**
- (none)

**Routes (2):**
- (GET) /admin/users/manage-users
- (PUT) /admin_old/communities/:community_id/community_memberships/:id

**Data models (2):**
- CommunityMembership
- MODEL002 — Person
