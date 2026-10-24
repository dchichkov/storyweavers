"""A bounded, stylized greenhouse, not a horticultural prediction model.

Water, support and light treatments change physical-carrier records. Characters
inspect those records before treating a plant. Recovery is checked the following
morning, not asserted by the prose. No runtime model calls.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import random

from .capabilities.api import registry as base_registry
from .capabilities.core import Action, CapabilityError, Entity, Query, Record, WorldSpec, execute, fingerprint, plain, replay
from .capabilities.physical import Container, Ownership, Parent, Route, accessible
from .capabilities.epistemic import Fact, Proposition, Result
from .capabilities.reading import Document, Reader, Statement


@dataclass(frozen=True, kw_only=True)
class Plant(Record):
    moisture: int = 1
    supported: bool = False
    shelter_needed: bool = False
    light: int = 2
    height: int = 2
    recovered: bool = False
    support_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class Supply(Record):
    units: int
    leaking: bool = False


@dataclass(frozen=True, kw_only=True)
class Reading(Record):
    actor: str
    target: str
    kind: str
    value: int
    event_id: str


def inspect(tx, *, plant, reading):
    tx.require(accessible(tx, tx.action.actor, plant), "Plant must be reachable")
    row = tx.get("plants", plant)
    tx.require(tx.maybe("garden_readings", reading) is None, "Inspection identity already used")
    tx.put("garden_readings", Reading(id=reading, actor=tx.action.actor, target=plant,
        kind="moisture", value=row.moisture, event_id=tx.event_id))
    tx.emit(plant=plant, moisture=row.moisture, reading=reading)


def treat(tx, *, plant, reading, method, source="can"):
    row, seen = tx.get("plants", plant), tx.get("garden_readings", reading)
    tx.require(accessible(tx, tx.action.actor, plant), "Treatment out of reach")
    tx.require(seen.actor == tx.action.actor and seen.target == plant and seen.kind == "moisture" and seen.value == row.moisture,
               "Treatment requires a current inspection by this actor")
    tx.depend(seen.event_id)
    if method == "water":
        tx.require(source in {"can", "jug"}, "Use a declared watering vessel")
        can = tx.get("garden_supplies", source)
        tx.require(accessible(tx, tx.action.actor, source) and can.units > 0 and not can.leaking,
                   "Need reachable water in a sound can")
        tx.require(row.moisture == 0, "Do not water already wet soil")
        tx.put("garden_supplies", replace(can, units=can.units - 1))
    elif method == "drain":
        tx.require(row.moisture == 2, "Only waterlogged soil needs drainage")
        tx.require(accessible(tx, tx.action.actor, "drain_tray"), "Drainage tray out of reach")
        tray = tx.get("garden_supplies", "drain_tray")
        tx.put("garden_supplies", replace(tray, units=tray.units + 1))
    else:
        tx.require(False, "Unknown treatment")
    tx.put("plants", replace(row, moisture=1))
    tx.emit(plant=plant, method=method, before=row.moisture, after=1)


def fill(tx, *, source):
    tx.require(source in {"tap", "jug"}, "A non-water supply cannot fill the can")
    can, supply = tx.get("garden_supplies", "can"), tx.get("garden_supplies", source)
    tx.require(accessible(tx, tx.action.actor, "can") and accessible(tx, tx.action.actor, source), "Water source out of reach")
    tx.require(can.units == 0 and supply.units >= 1, "Need empty can and remaining source water")
    tx.put("garden_supplies", replace(supply, units=supply.units - 1))
    tx.put("garden_supplies", replace(can, units=1))
    tx.emit(source=source, recipient="can", units=1)


def leak(tx):
    can, puddle = tx.get("garden_supplies", "can"), tx.get("garden_supplies", "puddle")
    tx.require(can.leaking and can.units > 0 and accessible(tx, tx.action.actor, "can"), "No reachable leaking water")
    tx.put("garden_supplies", replace(puddle, units=puddle.units + can.units))
    tx.put("garden_supplies", replace(can, units=0))
    tx.emit(source="can", recipient="puddle", units=can.units)


def mend(tx):
    can, patch = tx.get("garden_supplies", "can"), tx.get("garden_supplies", "washer")
    tx.require(accessible(tx, tx.action.actor, "can") and accessible(tx, tx.action.actor, "washer"), "Repair out of reach")
    tx.require(can.leaking and patch.units == 1, "Need a leak and a spare washer")
    tx.put("garden_supplies", replace(can, leaking=False))
    tx.put("garden_supplies", replace(patch, units=0))
    tx.emit(object="can", repair="washer", leaking=False)


def measure_stake(tx, *, stake):
    tx.require(stake in {"short_stake", "tall_stake"}, "Measure a declared stake")
    tx.require(accessible(tx, tx.action.actor, stake), "Stake out of reach")
    tx.require(tx.maybe("garden_readings", "stake") is None, "Stake already measured")
    tx.put("garden_readings", Reading(id="stake", actor=tx.action.actor, target=stake,
        kind="length", value=tx.get("garden_supplies", stake).units, event_id=tx.event_id))
    tx.emit(stake=stake, kind="length")


def support(tx, *, plant, stake):
    tx.require(stake in {"short_stake", "tall_stake"}, "Support requires a declared stake")
    row, cord = tx.get("plants", plant), tx.get("garden_supplies", "cord")
    pole = tx.get("garden_supplies", stake)
    reading = tx.get("garden_readings", "stake")
    tx.require(reading.actor == tx.action.actor and reading.target == stake and reading.kind == "length" and reading.value == pole.units,
               "Use the stake actually measured by this actor")
    tx.depend(reading.event_id)
    tx.require(all(accessible(tx, tx.action.actor, x) for x in (plant, stake, "cord")), "Support out of reach")
    tx.require(pole.units >= row.height and cord.units > 0 and not row.supported, "Stake must reach the stem; need unused cord")
    tx.put("garden_supplies", replace(cord, units=cord.units - 1))
    tx.put("parents", Parent(id=stake, parent=plant))
    tx.put("plants", replace(row, supported=True, support_id=stake))
    tx.emit(plant=plant, stake=stake, cord="cord")


def give_light(tx, *, plant, hours, lamp=False):
    row = tx.get("plants", plant)
    tx.require(accessible(tx, tx.action.actor, plant), "Plant out of reach")
    tx.require(type(hours) is int and hours > 0, "Positive light interval required")
    if lamp:
        battery = tx.get("garden_supplies", "lamp")
        tx.require(accessible(tx, tx.action.actor, "lamp") and battery.units >= hours, "Lamp needs charge")
        tx.put("garden_supplies", replace(battery, units=battery.units - hours))
        tx.require(tx.tick + hours <= 8, "Light session must finish before the morning check")
    else:
        tx.require(tx.get("parents", plant).parent == "sill", "Only the plant on the sill gets this sun interval")
        tx.require(tx.tick + hours <= 4, "Daylight is over")
    from .capabilities.core import Clock
    tx.put("clock", Clock(id="clock", tick=tx.tick + hours))
    tx.put("plants", replace(row, light=row.light + hours))
    tx.emit(plant=plant, hours=hours, source="lamp" if lamp else "sun")


def morning(tx):
    tx.require(tx.tick >= 8, "Recovery is assessed the following morning")
    for row in tx.all("plants"):
        protected = row.supported or tx.get("parents", row.id).parent == "shelter" or not row.shelter_needed
        tx.put("plants", replace(row, recovered=row.moisture == 1 and row.light >= 2 and protected))
    tx.require(tx.maybe("garden_readings", "morning") is None, "Morning already assessed")
    tx.put("garden_readings", Reading(id="morning", actor=tx.action.actor, target="fern",
        kind="morning", value=tx.get("plants", "fern").moisture, event_id=tx.event_id))
    tx.emit(kind="morning_check")


def validate(state):
    for row in state.tables["plants"].values():
        entity = state.get("entities", row.id)
        if (entity is None or entity.kind != "container" or type(row.moisture) is not int or row.moisture not in (0, 1, 2)
                or type(row.light) is not int or row.light < 0 or type(row.height) is not int or row.height < 1):
            raise CapabilityError("Invalid physical plant state")
        if any(type(v) is not bool for v in (row.supported, row.shelter_needed, row.recovered)):
            raise CapabilityError("Plant switches must be booleans")
        if bool(row.support_id) != row.supported:
            raise CapabilityError("Plant support identity must agree with support state")
        if row.supported and (not row.support_id or state.get("parents", row.support_id) != Parent(id=row.support_id, parent=row.id)):
            raise CapabilityError("A supporting stake must remain attached to its plant")
    for row in state.tables["garden_supplies"].values():
        if state.get("entities", row.id) is None or type(row.units) is not int or row.units < 0 or type(row.leaking) is not bool:
            raise CapabilityError("Supply must have a physical carrier and finite nonnegative units")
    for row in state.tables["garden_readings"].values():
        actor = state.get("entities", row.actor)
        if (actor is None or actor.kind != "actor" or state.get("entities", row.target) is None
                or row.kind not in {"moisture", "length", "morning"} or type(row.value) is not int or row.value < 0 or not row.event_id):
            raise CapabilityError("Invalid grounded garden reading")


def initial(state):
    if state.tables["garden_readings"]:
        raise CapabilityError("Inspections must be enacted")


def registry():
    engine = base_registry()
    engine.table("plants", Plant)
    engine.table("garden_supplies", Supply)
    engine.table("garden_readings", Reading)
    engine.validators.append(validate)
    engine.initial_validators.append(initial)
    physical = {"entities", "parents", "containers"}
    for name, handler, reads, writes in (
        ("garden_inspect", inspect, {"plants", "garden_readings"}, {"garden_readings"}),
        ("garden_treat", treat, {"plants", "garden_readings", "garden_supplies"}, {"plants", "garden_supplies"}),
        ("garden_fill", fill, {"garden_supplies"}, {"garden_supplies"}),
        ("garden_leak", leak, {"garden_supplies"}, {"garden_supplies"}),
        ("garden_mend", mend, {"garden_supplies"}, {"garden_supplies"}),
        ("garden_measure", measure_stake, {"garden_supplies", "garden_readings"}, {"garden_readings"}),
        ("garden_support", support, {"plants", "garden_supplies", "garden_readings"}, {"plants", "garden_supplies", "parents"}),
        ("garden_light", give_light, {"plants", "garden_supplies"}, {"plants", "garden_supplies", "clock"}),
        ("garden_morning", morning, {"plants", "garden_readings"}, {"plants", "garden_readings"}),
    ):
        engine.operation(name, handler, reads=physical | reads, writes=writes)
    return engine


@dataclass(frozen=True, kw_only=True)
class Conditions:
    purpose: str = "water"
    wet: bool = False
    full_can: bool = True
    tall_stake: bool = True
    cord: bool = True
    late_friend: bool = False
    charged_lamp: bool = True
    washer: bool = True

    def __post_init__(self):
        if self.purpose not in {"water", "support", "light", "leak"}:
            raise ValueError("Unknown greenhouse purpose")
        if any(type(v) is not bool for k, v in asdict(self).items() if k != "purpose"):
            raise ValueError("Greenhouse switches must be booleans")


def conditions(seed):
    rng = random.Random(seed)
    return Conditions(purpose=("water", "support", "light", "leak")[seed % 4],
        **{k: rng.random() < .6 for k in ("wet", "full_can", "tall_stake", "cord", "late_friend", "charged_lamp", "washer")})


def simulate(c):
    plants = (Plant(id="fern", moisture=(2 if c.wet else 0) if c.purpose == "water" else 0 if c.purpose == "leak" else 1,
                    shelter_needed=c.purpose == "support", light=0 if c.purpose == "light" else 2),
              Plant(id="ivy", light=0 if c.purpose == "light" else 2))
    ids = ("fern", "ivy", "can", "tap", "jug", "drain_tray", "puddle", "washer", "short_stake", "tall_stake", "cord", "lamp")
    entities = [Entity(id="house", name="the greenhouse", kind="place"), Entity(id="porch", name="the porch", kind="place"),
                Entity(id="rae", name="Rae", kind="actor", capacity=20), Entity(id="ivo", name="Ivo", kind="actor", capacity=20)]
    entities += [Entity(id=i, name=n, kind="container", capacity=cap) for i, n, cap in (
        ("bench", "the workbench", 20), ("sill", "the sunny sill", 1), ("shelter", "the sheltered corner", 20))]
    entities += [Entity(id=i, name="spare stake" if i == "tall_stake" else i.replace("_", " "),
                        kind="container" if i in {"fern", "ivy"} else "object", capacity=5) for i in ids]
    parents = tuple(Parent(id=i, parent="porch" if i == "ivo" and c.late_friend and c.purpose == "light" else "house") for i in ("rae", "ivo", "bench", "sill", "shelter")) + tuple(
        Parent(id=i, parent="ivo" if i == "ivy" and c.late_friend and c.purpose == "light" else "bench") for i in ids)
    records = dict(entities=tuple(entities), parents=parents, plants=plants,
        ownership=(Ownership(id="fern", owner="rae"), Ownership(id="ivy", owner="ivo")),
        containers=tuple(Container(id=i) for i in ("bench", "sill", "shelter", "fern", "ivy")),
        routes=(Route(id="inside", source="porch", destination="house"),),
        propositions=(Proposition(id="goal", subject="rae", predicate="desire", scope="authored_premise",
            result=Result(kind="exact", value={"water": "help the drooping plant recover", "support": "protect the tall plant from the night's draft",
                "light": "give both plants enough light", "leak": "find why the watering can loses its water"}[c.purpose]), reference_start=0, reference_end=0),),
        facts=(Fact(id="goal", carrier="rae", proposition="goal"),),
        garden_supplies=tuple(Supply(id=i, units=n, leaking=i == "can" and c.purpose == "leak") for i, n in (
            ("can", 1 if c.full_can and c.purpose != "leak" else 0), ("tap", 3), ("jug", 2),
            ("drain_tray", 0), ("puddle", 0), ("washer", int(c.washer)),
            ("short_stake", 1), ("tall_stake", 3 if c.tall_stake else 1), ("cord", int(c.cord)),
            ("lamp", 2 if c.charged_lamp else 0))))
    actions = []

    def add(id, op, actor="rae", **args):
        actions.append(Action(id=id, operation=op, actor=actor, args=args))

    for plant in ("fern", "ivy"):
        add("inspect_" + plant, "garden_inspect", plant=plant, reading=plant)
        for source in ("bench", "sill", "shelter"):
            add(f"lift_{plant}_{source}", "pickup", object=plant, source=source)
        for target in ("bench", "sill", "shelter"):
            add(f"put_{plant}_{target}", "put", object=plant, destination=target)
        add("sun_" + plant, "garden_light", plant=plant, hours=2)
        add("lamp_" + plant, "garden_light", plant=plant, hours=2, lamp=True)
    add("arrive_ivy", "put", "ivo", object="ivy", destination="bench")
    add("arrive_ivo", "travel", "ivo", route="inside")
    add("water", "garden_treat", plant="fern", reading="fern", method="water")
    add("jug_water", "garden_treat", plant="fern", reading="fern", method="water", source="jug")
    add("drain", "garden_treat", plant="fern", reading="fern", method="drain")
    add("fill", "garden_fill", source="tap")
    add("refill", "garden_fill", source="tap")
    add("leak", "garden_leak")
    add("mend", "garden_mend")
    add("support", "garden_support", plant="fern", stake="tall_stake")
    add("measure_stake", "garden_measure", stake="tall_stake")
    add("try_short", "garden_support", plant="fern", stake="short_stake")
    add("wait_friend", "advance_time", to_tick=3)
    add("night", "advance_time", to_tick=8)
    add("morning", "garden_morning")
    spec = WorldSpec(title="Under the greenhouse glass", records=records, actions=tuple(actions), max_steps=60,
        goal=(Query(table="garden_readings", key="morning", field="kind", value="morning"),
              Query(table="clock", key="clock", field="tick", value=8)))
    engine = registry()
    state = engine.initial(spec)
    available = {a.id: a for a in actions}

    def do(id):
        nonlocal state
        after = execute(engine, spec, state, available[id])
        if after is None:
            raise ValueError(f"Greenhouse policy rejected {id}")
        state = after

    if c.purpose == "water":
        do("inspect_fern")
        if state.get("garden_readings", "fern").value == 2:
            do("drain")
        else:
            if not state.get("garden_supplies", "can").units:
                do("fill")
            do("water")
    elif c.purpose == "support":
        do("measure_stake")
        if state.get("garden_readings", "stake").value >= state.get("plants", "fern").height and state.get("garden_supplies", "cord").units:
            do("support")
        else:
            do("lift_fern_bench")
            do("put_fern_shelter")
    elif c.purpose == "light":
        do("lift_fern_bench")
        do("put_fern_sill")
        do("sun_fern")
        do("lift_fern_sill")
        do("put_fern_bench")
        if c.late_friend:
            do("wait_friend")
            do("arrive_ivo")
            do("arrive_ivy")
        do("lift_ivy_bench")
        do("put_ivy_sill")
        if not c.late_friend:
            do("sun_ivy")
        elif c.charged_lamp:
            do("lamp_ivy")
    elif c.purpose == "leak":
        do("fill")
        do("leak")
        if c.washer:
            do("mend")
            do("refill")
            do("inspect_fern")
            do("water")
        else:
            do("inspect_fern")
            do("jug_water")
    else:
        raise ValueError("Unknown greenhouse purpose")
    do("night")
    do("morning")
    path = [e.action.id for e in state.events]
    if replay(engine, spec, path) != state:
        raise ValueError("Greenhouse replay changed")
    return spec, state


def generate(seed=0, *, prose_seed=None, config=None):
    from .greenhouse_prose import render
    c = config or conditions(seed)
    spec, state = simulate(c)
    doc = render(spec, state, c, seed if prose_seed is None else prose_seed)
    path = [e.action.id for e in state.events]
    plot = dict(purpose=c.purpose, outcome="both_ready" if all(p.recovered for p in state.tables["plants"].values()) else "one_waits",
                method="drain" if "drain" in path else "jug" if "jug_water" in path else "water" if "water" in path else "shelter" if "put_fern_shelter" in path else
                       "stake" if "support" in path else "lamp" if "lamp_ivy" in path else "sun_turns" if "sun_ivy" in path else "wait")
    return dict(sample_id=f"greenhouse:{seed}", world="greenhouse", seed=seed, ok=True, conditions=asdict(c),
        story=doc.story, qa=plain(Reader(doc).questions()), story_sha256=fingerprint(doc.story),
        trace_sha256=fingerprint(state), path=path, plot=plot, words=len(doc.story.split())), spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    row, _, _, _ = generate(args.seed)
    print(row["story"])
    if args.qa:
        for qa in row["qa"]:
            print(f"\nQ: {qa['question']}\nA: {qa['answer']}")


if __name__ == "__main__":
    main()
