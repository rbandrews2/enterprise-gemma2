# Supplied WZOS identity - October 17, 2026

Ray supplied WZOS_ICON_L0GO_FAVICON.png as the authoritative app logo/favicon/shortcut.
Original319x355 RGBA file copied byte-for-byte to static/wzos-logo.png.
SHA256: de2d9bcd2828fff395a33878a0e659e57091be8af84b33d9a4c072ed5e521052.

Applied to shared sidebar, dashboard and sign-in/account setup panel, retaining
all existing module/card styling and the Time Tracker/Atlas artwork.
Browser ICO16/32/48/64/128/256 and PNG32; Apple180; Windows144; standard PWA192/512;
separate maskable192/512 with complete artwork inside safe center circle.
Variants contain the full supplied artwork, preserve aspect ratio and use existing
black theme as canvas. No cropping, redesign, model-generated replacement or new
runtime image library. Pillow used only at development time.

Manifest id/start_url/scope remain /. Cache-versioned icon links permit refresh
without changing installed app identity. Existing devices may refresh icons on
browser/OS schedule; do not clear storage or force reinstall pending offline drafts.

Validation: local HTTP confirmed exact source bytes, PNG sizes/MIME, ICO sizes,
manifest links and stable identity.39 focused Node checks passed (install, account,
dashboard and meeting lifecycle);13 earlier focused meeting/provider Python checks
passed. Brand preview desktop/mobile images loaded and had no horizontal overflow
(actual CSS viewport417px under temporary phone-size override); override reset.
Preview's pre-existing synthetic /api/dispatch/notifications404 was observed and
is not attributed to branding or production. New live artwork not yet deployed.

Combine with Daily frame repair only after its exact tenant media-origin approval;
no logo change requires extra credential access or IAM. Deployment must verify
favicon/Apple/maskable/master assets and the shared shell, plus existing role/
organization/edition and runtime configuration preservation.
