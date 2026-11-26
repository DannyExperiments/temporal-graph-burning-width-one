# Proof at a glance

In Hand’s model, spread happens first in each round, then the strategy ignites one vertex that remains unburnt. After the final ignition the strategy gets one extra spread. The question asks for a successful strategy with at most $h$ ignitions.

Use one vertex per input set and element and one relay per incidence. The first $k+1$ rounds have no contact. Then schedule all set-to-relay edges, all relay-to-element edges, and finally hub cleanup edges. The private leaf’s only contact with the hub comes first in cleanup. Each edge appears at a different time so the width is one.

Let $h$ be the last cleanup timestep. Add $h-k-1$ late leaves with first contacts after $h+1$. They each need a dedicated ignition, and the hub or private leaf needs another. So at most $k$ ignitions can account for elements. During the first contact phase an ignition can spread within just one set star, and the second phase separates the elements. The set charged to any ignition therefore covers each element attributable to it. Conversely a cover lets the initial ignitions choose the hub and at most $k$ sets, with the rest igniting the late leaves. The full proof also checks legal padding and the NP certificate.

[Manuscript](../paper/manuscript.pdf) · [Exact replay](../verification/src/replay.py)
