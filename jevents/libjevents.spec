Name:		libjevents
Version:	1
Release:	1%{?dist}
Summary:	libjevents shared library from pmu-tools

License:	GPL
URL:		https://github.com/andikleen/pmu-tools/jevents
# git clone https://github.com/andikleen/pmu-tools.git pmu-tools
# cd pmu-tools && tar czf jevents.tar.gz jevents/
Source0:	jevents.tar.gz

%description
jevents library from pmu-tools.

%prep
%setup -q -n jevents


%build
%make_build

%install
%make_install 

%files
/usr/local/bin/event-rmap
/usr/local/bin/listevents
/usr/local/bin/showevent
/usr/local/include/jevents.h
/usr/local/include/jsession.h
/usr/local/include/measure.h
/usr/local/include/perf-iter.h
/usr/local/include/rdpmc.h
/usr/local/lib64/libjevents.a

%changelog

