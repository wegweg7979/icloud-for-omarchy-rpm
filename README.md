# icloud-for-omarchy — Fedora packaging

Fedora RPM packaging for [icloud-for-omarchy](https://github.com/ferdousbhai/icloud-for-omarchy):
iCloud Drive, iCloud Photos and the shared Apple sign-in as native apps, on an
Omarchy/Hyprland desktop. Upstream ships an Arch PKGBUILD and a signed pacman
repository; this repository carries only the spec that turns it into RPMs.

## Fedora package (COPR)

```sh
sudo dnf copr enable wegweg7979/icloud-for-omarchy
sudo dnf install icloud-for-omarchy
```

## What it builds

| Package | What it is |
|---|---|
| `icloud-session` | One iCloud sign-in for every app: D-Bus-activated daemon, sign-in window, CLI |
| `icloud-drive` | `~/iCloud Drive` kept in sync both ways — off until `icloud-drive start` |
| `icloud-photos` | iCloud Photos in GTK4: browse by month and album, download, upload, delete with undo |
| `icloud-for-omarchy` | Metapackage installing all of the above |

Upstream's Notes, Reminders, Contacts and Find My are not packaged yet.

## Building

`rpm/icloud-for-omarchy.spec` is the only file that matters;
`bin/spec-sources` re-pins the `Source0` sha256 after a version bump.

Upstream's Rust workspace builds with
`cargo build --release --locked --bins -p icloud-sessiond -p icloud-drive -p icloud-photos`
and fetches its crates from crates.io, so **the COPR project must have network
access enabled** — the same as the golang build in `huru-calendar`.

Verify a change without touching the host:

```sh
podman run --rm -v "$PWD":/work:z registry.fedoraproject.org/fedora:45 bash -c '
  dnf5 -y install rpm-build rpmdevtools desktop-file-utils cargo rust gcc pkgconf-pkg-config \
      gtk4-devel libadwaita-devel webkitgtk6.0-devel systemd-rpm-macros
  mkdir -p /rpmbuild/{SPECS,SOURCES,BUILD,RPMS}
  cp /work/rpm/icloud-for-omarchy.spec /rpmbuild/SPECS/
  rpmbuild -bb --define "_topdir /rpmbuild" /rpmbuild/SPECS/icloud-for-omarchy.spec'
```

## Signing in

Once installed, `icloud-session sign-in` opens Apple's own page (password and
two-factor code included); the session is kept in the system keyring. Nothing
syncs until you sign in, and iCloud Drive stays off until `icloud-drive start`.

## Licence

MIT for the packaging in this repository. Upstream is MIT; its `LICENSE` and
`NOTICE` (third-party credits) ship inside every built package.
