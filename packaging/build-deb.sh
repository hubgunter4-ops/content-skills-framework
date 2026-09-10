#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=${VERSION:-0.3.1}
PKG="$ROOT/build/deb/content-skills-framework_${VERSION}_all"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/content-skills-framework" "$PKG/usr/bin" "$PKG/usr/share/applications"
find "$ROOT/toolkit" "$ROOT/desktop" -type d -name __pycache__ -prune -exec rm -rf {} +
cp -a "$ROOT/toolkit" "$ROOT/desktop" "$PKG/opt/content-skills-framework/"
cat > "$PKG/DEBIAN/control" <<EOF
Package: content-skills-framework
Version: ${VERSION}
Section: devel
Priority: optional
Architecture: all
Maintainer: Content Skills Framework
Description: GUI local para Content Skills Framework
 Ejecuta el router y los workers locales con cuotas, circuit breakers y sandbox.
Depends: python3 (>= 3.10)
EOF
cat > "$PKG/usr/bin/content-skills-framework" <<'EOF'
#!/usr/bin/env bash
exec python3 /opt/content-skills-framework/desktop/server.py "$@"
EOF
chmod 0755 "$PKG/usr/bin/content-skills-framework"
cat > "$PKG/usr/share/applications/content-skills-framework.desktop" <<'EOF'
[Desktop Entry]
Name=Content Skills Framework
Comment=GUI local para enrutar y ejecutar herramientas
Exec=content-skills-framework
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Development;Utility;
EOF
mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$PKG" "$ROOT/dist/content-skills-framework_${VERSION}_all.deb"
sha256sum "$ROOT/dist/content-skills-framework_${VERSION}_all.deb" >> "$ROOT/dist/SHA256SUMS"
echo "$ROOT/dist/content-skills-framework_${VERSION}_all.deb"
