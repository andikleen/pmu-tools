class Aux:
    limited_counters = { "r3qpi": 3, "ubox": 2 }
    filters = ("filter_nid", "mask", "match", "filter_opc", "filter_state")
    DEFAULT_COUNTERS = 4
    MAX_RANK = 8

    acronyms = {
        "TOR": "Table of Requests, pending transactions",
        "FLIT": "80-bit QPI packet",
        "RPQ": "Read Queue",
        "WPQ": "Write Queue",
        "CBO": "Last Level Cache Slice",
        "PCU": "Power Control Unit",
        "iMC": "Memory Controller",
        "HA": "Home Agent",
        "QPI_LL": "QPI Link Layer",
    }

    qual_alias = {
        "nid": "filter_nid",
        "opc": "filter_opc",
        "all_opc": "filter_all_op",
        "nm": "filter_nm",
        "not_nm": "filter_not_nm",
        "opc0": "filter_opc0",
        "opc1": "filter_opc1",
        "loc": "filter_loc",
        "rem": "filter_rem",
        "nc": "filter_nc",
        "Q_Py_PCI_PMON_PKT_MATCH0[12:00]": "match0",
        "Q_Py_PCI_PMON_PKT_MATCH1[19:16]": "match_rds",
        "Q_Py_PCI_PMON_PKT_MASK0[12:0]": "mask0",
        "Q_Py_PCI_PMON_PKT_MASK0[17:0]": "mask0",   # why both?
        "Q_Py_PCI_PMON_PKT_MASK1[19:16]": "mask_rds",
        "Q_Py_PCI_PMON_PKT_MATCH0": "match0",
        "Q_Py_PCI_PMON_PKT_z_MATCH0": "match0",
        "Q_Py_PCI_PMON_PKT_z_MASK0[12:0]": "mask0", # XXX correct?
        "Q_Py_PCI_PMON_PKT_z_MASK0[17:0]": "mask0", # XXX correct?
        "edge_det": "edge",
        "Cn_MSR_PMON_BOX_FILTER.opc": "filter_opc",
        "Cn_MSR_PMON_BOX_FILTER0.opc": "filter_opc",
        "Cn_MSR_PMON_BOX_FILTER1.opc": "filter_opc",
        "Cn_MSR_PMON_BOX_FILTER.state": "filter_state",
        "Cn_MSR_PMON_BOX_FILTER0.state": "filter_state",
        "Cn_MSR_PMON_BOX_FILTER0.tid": "filter_tid",
        "Cn_MSR_PMON_BOX_FILTER0.nc": "filter_nc",
        "Cn_MSR_PMON_BOX_FILTER0.nm": "filter_nm",
        "Cn_MSR_PMON_BOX_FILTER0.all_opc": "filter_all_op", # XXX
        "Cn_MSR_PMON_BOX_FILTER0.opc1": "filter_opc1",
        "Cn_MSR_PMON_BOX_FILTER0.opc0": "filter_opc0",
        "Cn_MSR_PMON_BOX_FILTER0.loc": "filter_loc",
        "Cn_MSR_PMON_BOX_FILTER0.not_nm": "filter_not_nm",
        "Cn_MSR_PMON_BOX_FILTER1.nm": "filter_nm",
        "Cn_MSR_PMON_BOX_FILTER1.all_opc": "filter_all_op", # XXX
        "Cn_MSR_PMON_BOX_FILTER1.opc1": "filter_opc1",
        "Cn_MSR_PMON_BOX_FILTER1.opc0": "filter_opc0",
        "Cn_MSR_PMON_BOX_FILTER1.loc": "filter_loc",
        "Cn_MSR_PMON_BOX_FILTER1.not_nm": "filter_not_nm",
        "Q_Py_PCI_PMON_PKT_MATCH0.dnid": "match_dnid",
        "Q_Py_PCI_PMON_PKT_z_MATCH0.dnid": "match_dnid", # XXX
        "Q_Py_PCI_PMON_PKT_z_MATCH1": "match1",
        "Q_Py_PCI_PMON_PKT_z_MASK1": "mask1",
        "PCUFilter[7:0]": "filter_band0",
        "PCUFilter[15:8]": "filter_band1",
        "PCUFilter[23:16]": "filter_band2",
        "PCUFilter[31:24]": "filter_band3",
        "CBoFilter[31:23]": "filter_opc",
        "CBoFilter[17:10]": "filter_nid",
        "QPIMatch0[17:0]": "match0",
        "QPIMask0[17:0]": "mask0",
        "QPIMatch0[12:0]": "match0",
        "QPIMask0[12:0]": "mask0",
        "QPIMask1[19:16]": "mask_rds",
        "QPIMatch1[19:16]": "match_rds",
        "CBoFilter[22:18]": "filter_state",
    }

    qual_display_alias = {
        "QPIMask0[12:0]": "mask_mc, match_opc, match_vnw",
        "QPIMatch0[12:0]": "match_mc, match_opc, match_vnw",
        "QPIMatch0[17:0]": "match_mc, match_opc, match_vnw, match_dnid",
    }

    alias_events = {
        "MC_Chy_PCI_PMON_CTR_FIXED": "uncore_imc_INDEX/clockticks/"
    }

    clockticks = (
        "uncore_(cbox|ha|pcu)_?\d*/event=0x0/",
        ".*/clockticks/", 
        "uncore_(r2pcie|r3qpi)_?\d*/event=0x1/",
        "uncore_qpi(_\d+)?/event=0x14/"
    )
