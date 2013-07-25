extra_derived = {
# CBO
     "CBO.LLC_PCIE_MEM_WRITE_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from PCIe to memory written",
          "Desc": "LLC Miss Data from PCIe to memory written",
          "Equation": "TOR_INSERTS.OPCODE with:Cn_MSR_PMON_BOX_FILTER.opc=0x19e * 64",
     },
     "CBO.LLC_PCIE_MEM_READ_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from PCIe read from memory",
          "Desc": "LLC Miss Data from PCIe read from memory",
          "Equation": "TOR_INSERTS.OPCODE with:Cn_MSR_PMON_BOX_FILTER.opc=0x19c * 64",
     },
     "CBO.LLC_PCIE_MEM_TOTAL_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from PCIe read from memory",
          "Desc": "LLC Miss Data from PCIe read from memory",
          "Equation": "LLC_PCIE_MEM_READ_BYTES + LLC_PCIE_MEM_WRITE_BYTES"
     },
     "CBO.LLC_DDIO_MEM_WRITE_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from DDIO to memory written",
          "Desc": "LLC Miss Data from DDIO to memory written",
          "Equation": "TOR_INSERTS.MISS_OPCODE with:Cn_MSR_PMON_BOX_FILTER.opc=0x19e * 64",
     },
     "CBO.LLC_DDIO_MEM_READ_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from PCIe read from memory",
          "Desc": "LLC Miss Data from PCIe read from memory",
          "Equation": "TOR_INSERTS.MISS_OPCODE with:Cn_MSR_PMON_BOX_FILTER.opc=0x19c * 64",
     },
     "CBO.LLC_DDIO_MEM_TOTAL_BYTES": {
          "Box": "CBO",
          "Category": "CBO TOR Events",
          "Defn": "LLC Miss Data from DDIO read from memory",
          "Desc": "LLC Miss Data from DDIO read from memory",
          "Equation": "LLC_DDIO_MEM_READ_BYTES + LLC_DDIO_MEM_WRITE_BYTES"
     },
      "CBO.AVG_LLC_DATA_READ_MISS_LATENCY": {
          "Box": "CBO",
          "Category": "CBO CACHE Events",
          "Defn": "Average LLC data read (demand+prefetch) miss latency (core clocks)",
          "Desc": "Average LLC data read (demand+prefetch) miss latency (core clocks)",
          "Equation": "(TOR_OCCUPANCY.MISS_OPCODE / TOR_INSERTS.MISS_OPCODE) with:Cn_MSR_PMON_BOX_FILTER.opc=0x182"
     },
     
# PCU
    "PCU.PCT_FREQ_BAND0": {
        "Box": "PCU",
          "Category": "PCU FREQ_RESIDENCY Events",
          "Defn": "Counts the percent that the uncore was running at a frequency greater than or equal to the frequency that is configured in the filter.  One can use all four counters with this event, so it is possible to track up to 4 configurable bands.  One can use edge detect in conjunction with this event to track the number of times that we transitioned into a frequency greater than or equal to the configurable frequency. One can also use inversion to track cycles when we were less than the configured frequency.",
          "Desc": "Frequency Residency",
          "Notes": "The PMON control registers in the PCU only update on a frequency transition.   Changing the measuring threshold during a sample interval may introduce errors in the counts.   This is especially true when running at a constant frequency for an extended period of time.  There is a corner case here: we set this code on the GV transition.  So, if we never GV we will never call this code.  This event does not include transition times.  It is handled on fast path.",
          "Equation": "FREQ_BAND0_CYCLES / CLOCKTICKS"
     },
     "PCU.PCT_FREQ_BAND1": {
          "Box": "PCU",
          "Category": "PCU FREQ_RESIDENCY Events",
          "Defn": "Counts the percent that the uncore was running at a frequency greater than or equal to the frequency that is configured in the filter.  One can use all four counters with this event, so it is possible to track up to 4 configurable bands.  One can use edge detect in conjunction with this event to track the number of times that we transitioned into a frequency greater than or equal to the configurable frequency. One can also use inversion to track cycles when we were less than the configured frequency.",
          "Desc": "Frequency Residency",
          "Notes": "The PMON control registers in the PCU only update on a frequency transition.   Changing the measuring threshold during a sample interval may introduce errors in the counts.   This is especially true when running at a constant frequency for an extended period of time.  There is a corner case here: we set this code on the GV transition.  So, if we never GV we will never call this code.  This event does not include transition times.  It is handled on fast path.",
          "Equation": "FREQ_BAND1_CYCLES / CLOCKTICKS"
     },
     "PCU.PCT_FREQ_BAND2": {
          "Box": "PCU",
          "Category": "PCU FREQ_RESIDENCY Events",
          "Defn": "Counts the percent that the uncore was running at a frequency greater than or equal to the frequency that is configured in the filter.  One can use all four counters with this event, so it is possible to track up to 4 configurable bands.  One can use edge detect in conjunction with this event to track the number of times that we transitioned into a frequency greater than or equal to the configurable frequency. One can also use inversion to track cycles when we were less than the configured frequency.",
          "Desc": "Frequency Residency",
          "Notes": "The PMON control registers in the PCU only update on a frequency transition.   Changing the measuring threshold during a sample interval may introduce errors in the counts.   This is especially true when running at a constant frequency for an extended period of time.  There is a corner case here: we set this code on the GV transition.  So, if we never GV we will never call this code.  This event does not include transition times.  It is handled on fast path.",
          "Equation": "FREQ_BAND2_CYCLES / CLOCKTICKS"
     },
     "PCU.PCT_FREQ_BAND3": {
          "Box": "PCU",
          "Category": "PCU FREQ_RESIDENCY Events",
          "Defn": "Counts the percent that the uncore was running at a frequency greater than or equal to the frequency that is configured in the filter.  One can use all four counters with this event, so it is possible to track up to 4 configurable bands.  One can use edge detect in conjunction with this event to track the number of times that we transitioned into a frequency greater than or equal to the configurable frequency. One can also use inversion to track cycles when we were less than the configured frequency.",
          "Desc": "Frequency Residency",
          "Notes": "The PMON control registers in the PCU only update on a frequency transition.   Changing the measuring threshold during a sample interval may introduce errors in the counts.   This is especially true when running at a constant frequency for an extended period of time.  There is a corner case here: we set this code on the GV transition.  So, if we never GV we will never call this code.  This event does not include transition times.  It is handled on fast path.",
          "Equation": "FREQ_BAND3_CYCLES / CLOCKTICKS"
     },
     "QPI_LL.QPI_SPEED": {
          "Box": "QPI_LL",
          "Category": "QPI_LL CFCLK Events",
          "Counters": "0-3",
          "Defn": "QPI speed - GT/s",
          "Desc": "QPI speed - GT/s",
          "Equation": "CLOCKTICKS/NUM_R3QPI*8/1000000000",
     },
     "iMC.DIMM_SPEED": {
          "Box": "iMC",
          "Category": "iMC CAS Events",
          "Defn": "DIMM Speed",
          "Desc": "DIMM Speed",
          "Equation": "MC_Chy_PCI_PMON_CTR_FIXED / 2",
          "Obscure": 1,
     },


}
