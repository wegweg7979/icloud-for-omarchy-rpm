# icloud-for-omarchy.spec — iCloud as native apps on the Hurunagus desktop,
# sharing one Apple sign-in.
#
# Upstream (github.com/ferdousbhai/icloud-for-omarchy, MIT) ships an Arch
# PKGBUILD and a signed pacman repo, nothing Fedora-shaped. This spec is the
# Fedora port. Phase 1 carries the three components that compile on Fedora 45
# with no source changes at all — verified with upstream's own invocation
# (bin/build): `cargo build --release --locked --bins -p icloud-sessiond
# -p icloud-drive -p icloud-photos` finished in 104s, producing
# icloud-sessiond, icloud-session-signin, icloud-drive, icloud-photos and
# icloud-photos-app.
#
# Notes the port needed (all measured, none of them code patches):
#   * the session package's crate is named *sessiond*, hence -p icloud-sessiond;
#   * rusqlite builds from its BUNDLED SQLite amalgamation, so gcc is a build
#     dependency and sqlite-devel is not (Arch's PKGBUILD lists 'sqlite'
#     because Arch's rusqlite links the system library);
#   * upstream's runtime requirement `org.freedesktop.secrets` is a *capability*
#     that no Fedora package Provides — gnome-keyring is the implementation on
#     this image;
#   * libshumate is only needed by icloud-findmy, which this spec does not
#     build yet.
#
# COPR-safe by house precedent: `cargo build` fetches crates from crates.io, so
# the COPR project MUST have network access enabled (`enable_net: true`), the
# same as huru-calendar's golang build. The offline fallback is vendoring —
# `cargo vendor --locked` measured 244 crates / 311 MB in 12s — if that policy
# ever changes.
#
# Rust release builds carry no debug info here, so there is none to extract and
# an empty debuginfo subpackage would fail the build (same choice as
# airgraph.spec and huru-calendar.spec).

%global debug_package %{nil}

Name:           icloud-for-omarchy
Version:        0.12.1
Release:        1%{?dist}
Summary:        iCloud Drive, Photos and the shared iCloud sign-in for the Hurunagus desktop

License:        MIT
URL:            https://github.com/ferdousbhai/icloud-for-omarchy
# The tag archive unpacks to icloud-for-omarchy-%{version}/.
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz

# Compiled for x86_64 — the only arch the hurunagus images target.
ExclusiveArch:  x86_64

# This package is a metapackage: it installs everything the spec builds.
Requires:       icloud-session = %{version}-%{release}
Requires:       icloud-drive = %{version}-%{release}
Requires:       icloud-photos = %{version}-%{release}

BuildRequires:  cargo
BuildRequires:  rust
# The bundled SQLite amalgamation is C.
BuildRequires:  gcc
# The gtk-rs crates discover their libraries through pkg-config.
BuildRequires:  pkgconf-pkg-config
BuildRequires:  gtk4-devel
BuildRequires:  libadwaita-devel
# webkitgtk6.0 is the web view the sign-in window is built on.
BuildRequires:  webkitgtk6.0-devel
BuildRequires:  desktop-file-utils
# %{_userunitdir} for icloud-drive's user unit.
BuildRequires:  systemd-rpm-macros

%description
The iCloud suite for Linux desktops, packaged for Fedora: iCloud Drive as a
local folder kept in sync both ways, iCloud Photos in a GTK4 window, and the
shared Apple sign-in every component uses.

Signing in is the one manual step — `icloud-session sign-in` opens Apple's own
page (password and two-factor code included), and the resulting session is kept
in the system keyring, never the password. Every window action is also
available from the command line with JSON output.

Installing this metapackage pulls in the components packaged so far. Upstream
also provides Notes, Reminders, Contacts and Find My; those become separate
packages once these three are proven.

# ---------------------------------------------------------------------------
# The shared sign-in: a D-Bus service, a sign-in window and the CLI that the
# other components link against.
# ---------------------------------------------------------------------------
%package        -n icloud-session
Summary:        Shared iCloud sign-in: D-Bus service, sign-in window and CLI

Requires:       gtk4
Requires:       webkitgtk6.0
Requires:       gstreamer1-plugins-good
Requires:       glib2
# Upstream requires the `org.freedesktop.secrets` capability, which no Fedora
# package Provides. gnome-keyring owns that D-Bus name here — without it there
# is nowhere to keep the session cookies.
Requires:       gnome-keyring

%description -n icloud-session
Owns one iCloud web sign-in for every app on the machine — a D-Bus-activated
daemon, Apple's sign-in page in a window, and the `icloud-session` command.
Session cookies live in the system keyring; the Apple ID password is never
stored unless you ask for it (Find My needs it periodically).

The daemon has no systemd unit by design: the bus starts it on the first call
and it exits when idle.

%files -n icloud-session
%{_bindir}/icloud-sessiond
%{_bindir}/icloud-session-signin
%{_bindir}/icloud-session
%{_datadir}/dbus-1/services/io.github.ferdousbhai.ICloudSession.service
%{_datadir}/applications/io.github.ferdousbhai.ICloudSession.desktop
%doc session/README.md
%license LICENSE NOTICE

# ---------------------------------------------------------------------------
# iCloud Drive as a synced folder.
# ---------------------------------------------------------------------------
%package        -n icloud-drive
Summary:        iCloud Drive as ~/iCloud Drive, synced both ways

Requires:       icloud-session = %{version}-%{release}

%description -n icloud-drive
Keeps ~/iCloud Drive in sync with iCloud Drive, both ways, over the shared
sign-in. There is no window: it is a folder, so the file manager, an editor or
an agent reads and writes it like any other.

Conflicts are never clobbered — the local version is kept as a
`name (conflicted copy …)` and uploaded. A local delete goes to iCloud's
Recently Deleted (30 days) and an iCloud delete goes to the desktop trash, so
nothing is removed for good. More than 20 removals at once (and more than a
quarter of what is in sync) pauses the sync until `icloud-drive sync --yes`, and
a missing folder is never read as everything having been deleted.

The user unit ships DISABLED on purpose: a first sync downloads the whole
Drive, which a package must not start by itself. `icloud-drive start` turns it
on, now and at every login.

%files -n icloud-drive
%{_bindir}/icloud-drive
%{_userunitdir}/icloud-drive.service
%doc drive/README.md
%license LICENSE NOTICE

# ---------------------------------------------------------------------------
# The Photos app.
# ---------------------------------------------------------------------------
%package        -n icloud-photos
Summary:        iCloud Photos: browse by month and album, download, upload, delete

Requires:       icloud-session = %{version}-%{release}
Requires:       libadwaita
Requires:       hicolor-icon-theme
# `icloud-photos copy` puts an image on the clipboard; `icloud-photos open`
# hands a file to the desktop's default app.
Recommends:     wl-clipboard
Recommends:     xdg-utils

%description -n icloud-photos
iCloud Photos in GTK4/libadwaita: browse the library by month and by album,
download originals, upload photos and videos, and move them to Recently
Deleted with an undo. Thumbnails are iCloud's own small previews, fetched as
you scroll — nothing is decoded or resized locally, which is what makes
browsing a large library over a network bearable.

Originals are saved under ~/Pictures/<year>/<month>/. The window is also a
command line: `icloud-photos --help`.

%files -n icloud-photos
%{_bindir}/icloud-photos
%{_bindir}/icloud-photos-app
%{_datadir}/applications/com.ferdousbhai.IcloudPhotos.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.ferdousbhai.IcloudPhotos.svg
%doc photos/README.md
%license LICENSE NOTICE

# The metapackage's own files. It must carry at least one file or the empty
# %files is a build error.
%files
%doc README.md
%license LICENSE NOTICE

# ---------------------------------------------------------------------------
%prep
%autosetup -n %{name}-%{version}

%build
# Upstream's own invocation, from bin/build: the session package builds the
# *sessiond* crate, and icloud-photos' default "ui" feature pulls gtk and
# libadwaita. --locked honours the committed Cargo.lock.
cargo build --release --locked --bins -p icloud-sessiond -p icloud-drive -p icloud-photos

%check
# The desktop entries, validated in the source tree (%check runs before
# %install). cargo's own test suites are deliberately NOT run yet: they pull
# dev-dependencies and drive fixture-heavy fake servers, and they have not been
# vetted on Fedora — add them once the first build is green and they are known
# to pass in a network-enabled buildroot.
desktop-file-validate sessiond/data/io.github.ferdousbhai.ICloudSession.desktop
desktop-file-validate photos/data/com.ferdousbhai.IcloudPhotos.desktop

%install
# icloud-session: two binaries, one symlink, D-Bus activation, a launcher.
install -Dpm755 target/release/icloud-sessiond %{buildroot}%{_bindir}/icloud-sessiond
install -Dpm755 target/release/icloud-session-signin %{buildroot}%{_bindir}/icloud-session-signin
# Run as `icloud-session` this same executable is the CLI (upstream ships the
# symlink too).
ln -s icloud-sessiond %{buildroot}%{_bindir}/icloud-session
install -Dpm644 sessiond/data/io.github.ferdousbhai.ICloudSession.service %{buildroot}%{_datadir}/dbus-1/services/io.github.ferdousbhai.ICloudSession.service
install -Dpm644 sessiond/data/io.github.ferdousbhai.ICloudSession.desktop %{buildroot}%{_datadir}/applications/io.github.ferdousbhai.ICloudSession.desktop

# icloud-drive: the binary and its user unit (left disabled, see the header).
install -Dpm755 target/release/icloud-drive %{buildroot}%{_bindir}/icloud-drive
install -Dpm644 drive/data/icloud-drive.service %{buildroot}%{_userunitdir}/icloud-drive.service

# icloud-photos: the CLI and the window, launcher and icon.
install -Dpm755 target/release/icloud-photos %{buildroot}%{_bindir}/icloud-photos
install -Dpm755 target/release/icloud-photos-app %{buildroot}%{_bindir}/icloud-photos-app
install -Dpm644 photos/data/com.ferdousbhai.IcloudPhotos.desktop %{buildroot}%{_datadir}/applications/com.ferdousbhai.IcloudPhotos.desktop
install -Dpm644 photos/data/com.ferdousbhai.IcloudPhotos.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.ferdousbhai.IcloudPhotos.svg

%changelog
* Sat Nov 15 2026 Dan <dan@localhost> - 0.12.1-1
- Initial Fedora packaging: icloud-session, icloud-drive, icloud-photos.
