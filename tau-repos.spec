# https://src.fedoraproject.org/rpms/fedora-repos/blob/f35/f/fedora-repos.spec. Lots of other things we could be doing but idc

%define dist_version 35

Summary:        tauOS Package Repositories
Name:           tau-repos
Version:        1
Release:        1
License:        GPLv3
URL:            https://tauos.co
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Provides:       tau-repos(%{version}) = %{release}

Requires:       system-release(%{dist_version})
# Obsoletes:      tau-repos < 1.0.0
Requires:       tau-gpg-keys = %{version}-%{release}

BuildRequires:  gnupg sed

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
%setup -q
%build

%install
# Link the primary/secondary keys to arch files, according to archmap.
# Ex: if there's a key named RPM-GPG-KEY-tauOS-1-primary, and archmap
#     says "tauOS-1-primary: i386 x86_64",
#     RPM-GPG-KEY-tauOS-1-{i386,x86_64} will be symlinked to that key.
for keyfile in RPM-GPG-KEY*; do
    # resolve symlinks, so that we don't need to keep duplicate entries in archmap
    real_keyfile=$(basename $(readlink -f $keyfile))
    key=${real_keyfile#RPM-GPG-KEY-} # e.g. 'tauOS-1-primary'
    if ! grep -q "^${key}:" archmap; then
        echo "ERROR: no archmap entry for $key"
        exit 1
    fi

    arches=$(sed -ne "s/^${key}://p" archmap)
    for arch in $arches; do
        # replace last part with $arch (tauOS-1-primary -> tauOS-1-$arch)
        ln -s $keyfile ${keyfile%%-*}-$arch # NOTE: RPM replaces %% with %
    done
done

# and add symlink for compat generic location
ln -s RPM-GPG-KEY-tauOS-%{version}-primary RPM-GPG-KEY-%{version}-tauOS

# Install the keys
install -d -m 755 %{buildroot}%{_sysconfdir}/pki/rpm-gpg
install -m 644 RPM-GPG-KEY* %{buildroot}%{_sysconfdir}/pki/rpm-gpg/

# Install repo files
install -d -m 755 %{buildroot}%{_sysconfdir}/yum.repos.d
for file in tauOS*repo ; do
  install -m 644 $file %{buildroot}%{_sysconfdir}/yum.repos.d
done

# Install ostree remote config
install -d -m 755 %{buildroot}%{_sysconfdir}/ostree/remotes.d/
install -m 644 tau.conf %{buildroot}%{_sysconfdir}/ostree/remotes.d/

# Create a Yum variable
mkdir -p %{buildroot}%{_sysconfdir}/yum/vars
echo "%{version}" > %{buildroot}%{_sysconfdir}/yum/vars/taurelease

%check
# Check arch keys exists on supported architectures
TMPRING=$(mktemp)
for VER in %{version}; do
  echo -n > "$TMPRING"
  for ARCH in $(sed -ne "s/^tauOS-${VER}-primary://p" archmap)
  do
    gpg --no-default-keyring --keyring="$TMPRING" \
      --import $RPM_BUILD_ROOT%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-tauOS-$VER-$ARCH
  done
  # Ensure some arch key was imported
  gpg --no-default-keyring --keyring="$TMPRING" --list-keys | grep -A 2 '^pub\s'
done
rm -f "$TMPRING"

%files
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
* Sat Feb 26 2022 Jamie Lee <hello@jamiethalacker.dev> - 1.0.0-1
- Initial Release
