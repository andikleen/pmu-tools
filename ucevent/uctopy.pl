#!/usr/bin/perl
# generate python data files from perl input
# uctopl.pl CPU-ACRONYM events.pl derived.pl >cpu_uc.py
use File::Basename;

$cpu = $ARGV[0];
shift(@ARGV);
foreach (@ARGV) {
	do $_;
}

$code = <<END;
\$aliases = \\%CPU_UCFilterAliases;
\$events = \\%CPU_UCEventList;
\$derived = \\%CPU_UCDerivedList;
END
$code =~ s/CPU/$cpu/g;
eval($code);

print "# $cpu ";
foreach $j (@ARGV) { 
	$f = basename($j);
	$f =~ s/\.pl//;
	print "$f ";
}
print "\n\n";

%categories = {};
@catlit = ();
%global = {};

$indent = "     ";
$quote = "\"";
$nquote = "\"\"\"";

sub addquote($) {
	my($data) = (@_);
	return $nquote . $data . $nquote if ($data =~ /\n/);
	return $quote . $data . $quote;
}

print "# aliases\n";
print "aliases = {\n";
foreach $i (keys(%{ $aliases } )) {
	print $indent,$quote,$i,$quote,": ",addquote($aliases->{$i}),",\n";
}
print "}\n\n";

sub format_data($) {
	my($data) = (@_);
	return $data if ($data =~ /^[0-9]+$/ || $data =~ /^0x[0-9a-fA-F]+$/);
	$data =~ s/"/\\"/g;
	return addquote($data);
}

sub to_list($) {
	my($l) = (@_);
	return $l;
	($a, $b) = $l =~ /(\d+)-(\d+)/;
	$o = "";
	for (; $a <= $b; $a++) {
		$o += "$a,";
	}
	return $o;
}

sub print_event($$) { 
	my($name, $ev) = (@_);

	#return if $ev->{'Public'} ne "Y";

	push(@catlist, $ev->{"Category"});

	print $indent,$quote,$name,$quote,": {\n";
	foreach $w (sort(keys(%{$ev}))) {
		next if $w =~ /Sub[cC]at/;
		next if $w eq "Subevents";
		next if $ev->{$w} eq "" && $w ne "Category";
		next if $w eq "OrigName";
		next if $w =~ /([A-Z]+)Status/;
		next if $w eq "RTLSignal";
		next if $w eq "Public";
		if ($w eq "Internal") { 
			$w = "ExtSel";
		}

		$val = $ev->{$w};
		next if $w eq "MaxIncCyc" && ($val == "1" || $val == "0");
		next if $w eq "SubCtr" && $val == "0";

		$val = to_list($val) if $w eq "Counters" && $val =~ /-/;

		print $indent,$indent,
		      addquote($w),": ",format_data($val),",\n";
	}
	print $indent,"},\n";
}

sub print_sub($$$) {
	my($box, $j, $sub) = (@_);
	foreach $k (keys(%{$sub})) {
		$subev = $sub->{$k};
		# put all the fields from the parent 
		# into the sub event to normalize
		foreach $o (keys(%{$ev})) {
			next if defined($sub->{$o});
			$subev->{$o} = $ev->{$o};
		}
		print_event("$box.$j.$k", $subev);
	}
}

sub print_list($$) {
	my($name, $evl) = (@_);
	print "$name = {\n";
	foreach $box (keys(%{$evl})) {
		$evlist = $evl->{$box};
		$box =~ s/ Box Events//;
		$box =~ s/ /_/g;
		print $indent,"\n# $box:\n";

		foreach $j (sort(keys(%{$evlist}))) {
			$ev = $evlist->{$j};
			$ev->{"Box"} = $box;
			$ev->{"Category"} = $box . " " . $ev->{"Category"};
			print_event("$box.$j", $ev);
			print_sub($box, $j, $ev->{"Subcat"});
			print_sub($box, $j, $ev->{"SubCat"});
			print_sub($box, $j, $ev->{"Subevents"});
		}
	}
	print "}\n";
}

print_list("events", $events);
print_list("derived", $derived);

print "categories = (\n";
$prev = "";
foreach $i (sort @catlist) {
	next if $i eq $prev;
	$prev = $i;
	print $indent,addquote($i),",\n";
}
print ");\n";
