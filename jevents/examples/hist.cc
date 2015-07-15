// STL based histogram
#include <stdint.h>
#include <stdio.h>
#include <map>
#include <queue>
#include "hist.h"

using namespace std;

extern "C" { 

typedef map<uint64_t, uint64_t> hist_type;

struct hist {
	hist_type hist;
	uint64_t total;
};

hist *init_hist()
{
	struct hist *h = new hist;
	h->total = 0;
	return h;
}

void hist_add(hist *h, uint64_t val)
{
	h->hist[val]++;
	h->total++;
}

void hist_print(hist *h, double min_percent) 
{
	unsigned long long below_thresh = 0;
	typedef pair<uint64_t, uint64_t> val_pair;
	priority_queue<val_pair> q;

	for (hist_type::iterator it = h->hist.begin(); it != h->hist.end(); it++) { 
		double percent = (double)(it->second) / (double)h->total;
		if (percent >= min_percent) {
			val_pair p(it->second, it->first);
			q.push(p);
		} else
			below_thresh += it->second;
	}
	printf("%11s %16s %16s\n", "PERCENT", "ADDR", "SAMPLES");
	while (!q.empty()) { 
		val_pair p = q.top();
		printf("%10.2f%% %16llx %16llu\n", 
				(p.first / (double)h->total) * 100.0,
				(unsigned long long)p.second,
				(unsigned long long)p.first);
		q.pop();
	}
	printf("%llu below threshold\n", below_thresh);
}

void free_hist(hist *h)
{
	delete h;
}

}
