"""Exact finite checks for the width-one Temporal Graph Burning reduction."""

from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class Instance:
    names: tuple[str, ...]
    contacts: dict[int, tuple[int, int]]
    h: int
    hub: int
    leaf: int
    late: tuple[int, ...]


def construct(sets, n, k, *, reverse_order=False):
    m = len(sets)
    incidences = [(i, e) for i, s in enumerate(sets) for e in sorted(s)]
    if reverse_order:
        incidences.reverse()
    relays = {(i, e): m + n + j for j, (i, e) in enumerate(incidences)}
    hub = m + n + len(relays)
    leaf = hub + 1
    names = [f"S{i+1}" for i in range(m)] + [chr(97+e) for e in range(n)]
    names += [f"R{i+1}{chr(97+e)}" for i, e in relays]
    names += ["C", "P"]

    prefix = [(i, r) for (i, _), r in relays.items()]
    prefix += [(r, m + e) for (_, e), r in relays.items()]
    cleanup = [*range(m), *relays.values()]
    if reverse_order:
        cleanup.reverse()
    prefix += [(hub, leaf)] + [(hub, node) for node in cleanup]

    h = k + 1 + len(prefix)
    late = tuple(range(leaf + 1, leaf + 1 + h - k - 1))
    contacts = dict(enumerate(prefix, k + 2))
    contacts.update((h + 2 + j, (hub, node)) for j, node in enumerate(late))
    names += [f"T{i+1}" for i in range(len(late))]
    return Instance(tuple(names), contacts, h, hub, leaf, late)


def spread(burning, edges):
    result = burning
    for u, v in edges:
        endpoints = (1 << u) | (1 << v)
        if burning & endpoints:
            result |= endpoints
    return result


def spread_step(burning, contacts, time):
    edge = contacts.get(time)
    return spread(burning, (edge,)) if edge is not None else burning


def trace(contacts, ignitions):
    burning = 0
    for time, v in enumerate((*ignitions, None), 1):
        before = burning
        burning = spread_step(before, contacts, time)
        spread_mask = burning ^ before
        if v is not None:
            assert not burning & (1 << v), f"already burning at round {time}"
            burning |= 1 << v
        yield time, spread_mask, v, burning


def validate_structure(instance, k):
    expected_vertices = set(range(len(instance.names)))
    marked = {instance.hub}
    neighbors = {node: [] for node in expected_vertices}
    unique = set()
    times = instance.contacts
    assert set(times) == set(range(k + 2, instance.h + 1)) | set(range(instance.h + 2, instance.h + 2 + len(instance.late)))
    assert len(instance.late) == instance.h - k - 1
    late_set = set(instance.late)
    for time, (u, v) in times.items():
        edge = frozenset((u, v))
        assert len(edge) == 2 and edge <= expected_vertices and edge not in unique
        unique.add(edge)
        neighbors[u].append(v)
        neighbors[v].append(u)
        assert bool(edge & late_set) == (time > instance.h + 1)
    pending = [instance.hub]
    while pending:
        for v in neighbors[pending.pop()]:
            if v not in marked:
                marked.add(v)
                pending.append(v)
    assert marked == expected_vertices
    # In this singleton-label encoding each distinct edge occupies exactly its own timestamp.
    assert times and len(unique) == len(times)


def exact_tiny_decision(instance, h):
    """Enumerate legal ignitions and all possible stopping times through h + 1."""
    core = (1 << (instance.leaf + 1)) - 1
    late = len(instance.late)
    assert all(not (set(instance.late) & set(edge)) for t, edge in instance.contacts.items() if t <= h + 1)
    # These late leaves are interchangeable throughout this horizon, so count
    # how many have been ignited while considering a late-leaf move at every step.
    current = {(0, 0)}
    for t in range(1, h + 2):
        upcoming = set()
        for burned, late_burned in current:
            burned = spread_step(burned, instance.contacts, t)
            if burned == core and late_burned == late:
                return True
            if t > h:
                continue
            if late_burned < late and late - (late_burned + 1) <= h - t:
                upcoming.add((burned, late_burned + 1))
            if late - late_burned <= h - t:
                unburned = core ^ burned
                while unburned:
                    first = unburned & -unburned
                    upcoming.add((burned | first, late_burned))
                    unburned ^= first
        current = upcoming
    return False


def covered_sets(sets, n, k):
    target = set(range(n))
    for choice in combinations(range(len(sets)), k):
        if set().union(*(sets[i] for i in choice)) == target:
            return choice
    return None


def check_instances():
    outcomes = {True: 0, False: 0}
    for n in (1, 2, 3):
        universe = set(range(n))
        subsets = [{v for v in universe if encoded & (1 << v)} for encoded in range(1, 1 << n)]
        for m in range(1, min(3, len(subsets)) + 1):
            for sets in combinations(subsets, m):
                if set.union(*sets) != universe or sum(map(len, sets)) > 6:
                    continue
                for k in range(1, m + 1):
                    choice = covered_sets(sets, n, k)
                    yes = choice is not None
                    for reverse_order in (False, True):
                        instance = construct(sets, n, k, reverse_order=reverse_order)
                        validate_structure(instance, k)
                        assert exact_tiny_decision(instance, instance.h) == yes, (sets, k, reverse_order)
                        if yes:
                            schedule = (instance.hub, *choice, *instance.late)
                            assert len(schedule) == instance.h
                            states = list(trace(instance.contacts, schedule))
                            assert states[-1][-1] == (1 << len(instance.names)) - 1
                        outcomes[yes] += 1
    return outcomes


def worked_example():
    sets = ({0, 1}, {1})
    instance = construct(sets, 2, 1)
    schedule = (instance.hub, 0, *instance.late)
    states = list(trace(instance.contacts, schedule))
    full = (1 << len(instance.names)) - 1
    assert instance.h == 14 and len(instance.late) == 12 and len(instance.names) == 21
    assert states[-2][-1] == states[-1][-1] == full
    phases = ["Start", "Choose", "Choose", "Relays", "Relays", "Relays",
              "Elements", "Elements", "Elements"] + ["Cleanup"] * 6 + ["Final spread"]
    rounds = [{"time": 0, "phase": phases[0], "edge": None, "new": [], "ignition": None, "burned": []}]
    for t, moved, ignited, burning in states:
        edge = instance.contacts.get(t)
        rounds.append({
            "time": t, "phase": phases[t],
            "edge": [instance.names[i] for i in edge] if edge is not None else None,
            "new": [name for i, name in enumerate(instance.names) if moved & (1 << i)],
            "ignition": instance.names[ignited] if ignited is not None else None,
            "burned": [name for i, name in enumerate(instance.names) if burning & (1 << i)],
        })
    return instance, rounds


def main():
    # The first ignition cannot spread in its own round. The final spread can finish.
    assert list(trace({1: (0, 1)}, [0]))[-1][-1] == 0b01
    assert list(trace({2: (0, 1)}, [0]))[-1][-1] == 0b11
    # Simultaneous spread uses the previously burning endpoints.
    assert spread(0b001, ((0, 1), (1, 2))) == 0b011
    outcomes = check_instances()
    example, rows = worked_example()
    assert rows[3]["new"] == ["R1a"] and rows[6]["new"] == ["a"] and rows[7]["new"] == ["b"]
    assert rows[14]["ignition"] == "T12" and not rows[15]["edge"]
    assert min(t for t, edge in example.contacts.items() if set(example.late) & set(edge)) == 16
    yes, no = outcomes[True], outcomes[False]
    print(f"Set Cover equivalence, connectivity and width one: {yes + no} scheduled instances ({yes} yes, {no} no).")
    print("Simulation checks: legal ignitions and all stopping times, including success on the final spread.")
    print("Worked example: 21 vertices, h = 14, all burning at t = 14, final check t = 15, first late contact t = 16.")


if __name__ == "__main__":
    main()
