Name:           zerosys
Version:        0.1.0
Release:        1%{?dist}
Summary:        Friendly server automation for beginner sysadmins
License:        Apache-2.0
URL:            https://github.com/0extra/0sys
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip
BuildRequires:  python3-wheel

Requires:       python3 >= 3.11
Requires:       python3-pyyaml
Requires:       python3-jinja2
Requires:       python3-pydantic
Recommends:     ansible-core
Recommends:     openssh-clients

%description
0sys helps people who are just starting their journey as system
administrators. Write a simple YAML configuration file and 0sys
picks the right tool and does the work for you.

Features:
- Interactive wizard for guided setup
- Ansible backend with reusable roles
- Cloud-init generator for VPS providers
- SSH and local connection support
- Audit log with secret redaction
- Built-in knowledge base with explanations and tips

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%files
%{_bindir}/0sys
%{_bindir}/zerosys
%{python3_sitelib}/zerosys/
%{python3_sitelib}/zerosys-%{version}*.dist-info/
%license LICENSE
%doc README.md CHANGELOG.md

%changelog
* Sat Jan 01 2026 0extra <zero.to.extra@gmail.com> - 0.1.0-1
- Initial release