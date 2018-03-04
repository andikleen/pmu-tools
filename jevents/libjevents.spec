Name:		libjevents
Version:	1
Release:	1%{?dist}
Summary:	libjevents shared library from pmu-tools

License:	BSD
URL:		https://github.com/andikleen/pmu-tools/jevents
# git clone https://github.com/andikleen/pmu-tools.git pmu-tools
# cd pmu-tools && tar czf jevents.tar.gz jevents/
Source0:	jevents.tar.gz

%description
jevents library from pmu-tools.

%prep
%setup -q -n jevents


%build
%make_build PREFIX=%{buildroot}/usr

%install
%make_install PREFIX=%{buildroot}/usr

%files
/usr/bin/event-rmap
/usr/bin/listevents
/usr/bin/showevent
/usr/include/*
/usr/lib64/libjevents.a

%changelog

* Sat Mar 3 2018 Pablo Llopis <pablo.llopis@gmail.com> 1-1
- Initial specfile version
