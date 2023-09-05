# https://src.fedoraproject.org/rpms/fedora-repos/blob/f35/f/fedora-repos.spec. Lots of other things we could be doing but idc

%define dist_version 39

Summary:        tauOS Package Repositories
Name:           tau-repos
Version:        1
Release:        5%{?dist}
License:        GPLv3
URL:            https://tau.fyralabs.com
Source0:        README.md
Source1:        LICENSE
Source3:        tau.conf
Source4:        archmap
Source5:        tauOS.repo
Source6:        terra.repo

Source10:       RPM-GPG-KEY-tauOS-1-primary
Source11:       RPM-GPG-KEY-Terra-39-primary

BuildRequires:  gnupg
BuildRequires:  sed

BuildArch:      noarch
Provides:       tau-repos(%{version}) = %{release}

Requires:       system-release(%{dist_version})
# Obsoletes:      tau-repos < 1.0.0
Requires:       tau-gpg-keys = %{version}-%{release}

%description
tauOS package repository files for yum and dnf along with GPG public keys.

%package -n tau-gpg-keys
Summary:        tauOS RPM keys

%description -n tau-gpg-keys
This package provides the RPM signature keys.

%package ostree
Summary:        OSTree specific files

%description ostree
This package provides ostree specfic files like remote config from
where client's system will pull OSTree updates.

%prep

%build

%install
# Install the keys
install -d -m 755 %{buildroot}/etc/pki/rpm-gpg
install -m 644 %{_sourcedir}/RPM-GPG-KEY* %{buildroot}/etc/pki/rpm-gpg/

# Link the primary/secondary keys to arch files, according to archmap.
# Ex: if there's a key named RPM-GPG-KEY-tauOS-1-primary, and archmap
#     says "tauOS-1-primary: i386 x86_64",
#     RPM-GPG-KEY-tauOS-1-{i386,x86_64} will be symlinked to that key.
pushd %{buildroot}/etc/pki/rpm-gpg/

for keyfile in RPM-GPG-KEY*; do
    # resolve symlinks, so that we don't need to keep duplicate entries in archmap
    real_keyfile=$(basename $(readlink -f $keyfile))
    key=${real_keyfile#RPM-GPG-KEY-} # e.g. 'tauOS-1-primary'
    if ! grep -q "^${key}:" %{_sourcedir}/archmap; then
        echo "ERROR: no archmap entry for $key"
        exit 1
    fi

    arches=$(sed -ne "s/^${key}://p" %{_sourcedir}/archmap)
    for arch in $arches; do
        # replace last part with $arch (tauOS-1-primary -> tauOS-1-$arch)
        ln -s $keyfile ${keyfile%%-*}-$arch # NOTE: RPM replaces %% with %
    done
done

# and add symlink for compat generic location
ln -s RPM-GPG-KEY-tauOS-%{version}-primary RPM-GPG-KEY-%{version}-tauOS
popd

# Install repo files
install -d -m 755 %{buildroot}%{_sysconfdir}/yum.repos.d
install -m 644 %{_sourcedir}/tauOS*repo %{buildroot}%{_sysconfdir}/yum.repos.d

pushd %{buildroot}%{_sysconfdir}/yum.repos.d

for file in tauOS*repo; do
  sed -i "s/\$taurelease/%{version}/g" $file
done

popd

# Install ostree remote config
install -d -m 755 %{buildroot}%{_sysconfdir}/ostree/remotes.d/
install -m 644 %SOURCE3 %{buildroot}%{_sysconfdir}/ostree/remotes.d/

# Create a Yum variable
mkdir -p %{buildroot}%{_sysconfdir}/yum/vars
echo "%{version}" > %{buildroot}%{_sysconfdir}/yum/vars/taurelease

%check
# Check arch keys exists on supported architectures
TMPRING=$(mktemp)
for VER in %{version}; do
  echo -n > "$TMPRING"
  for ARCH in $(sed -ne "s/^tauOS-${VER}-primary://p" %{_sourcedir}/archmap)
  do
    gpg --no-default-keyring --keyring="$TMPRING" \
      --import %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-tauOS-$VER-$ARCH
  done
  # Ensure some arch key was imported
  gpg --no-default-keyring --keyring="$TMPRING" --list-keys | grep -A 2 '^pub\s'
done
rm -f "$TMPRING"

# Install licenses and documentation
mkdir -p licenses
install -pm 0644 %SOURCE1 licenses/LICENSE
install -pm 0644 %SOURCE0 README.md

%files
%doc README.md
%license licenses/LICENSE
%dir %{_sysconfdir}/yum.repos.d
%config(noreplace) %{_sysconfdir}/yum.repos.d/tauOS.repo
%{_sysconfdir}/yum/vars/taurelease

%files -n tau-gpg-keys
%dir %{_sysconfdir}/pki/rpm-gpg
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-*

%files ostree
%dir %{_sysconfdir}/ostree/remotes.d/
%config(noreplace) %{_sysconfdir}/ostree/remotes.d/tau.conf

%changelog
* Mon Sep 4 2023 Lleyton Gray <lleyton@fyralabs.com> - 1-5
- Bump for F39

* Fri Jul 21 2023 Lleyton Gray <lleyton@fyralabs.com> - 1-4
- Bump for F38

* Mon Oct 3 2022 Jaiden Riordan <jade@fyralabs.com> - 1.1-3
- Bump for F37

* Sat Apr 23 2022 Jamie Murphy <jamie@fyralabs.com> - 1.1-1
- Update for CI

* Wed Mar 23 2022 Jamie Lee <jamie@innatical.com> - 1.1-0
- Update for Fedora 36

* Sat Feb 26 2022 Jamie Lee <hello@jamiethalacker.dev> - 1.0.0-1
- Initial Release
