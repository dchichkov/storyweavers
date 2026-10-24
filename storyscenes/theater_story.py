"""Three small theater problems, enacted before scene-sized prose is rendered.

The projection geometry and costume sizing are deliberately finite toy laws.
They are not a general optics engine or an autonomous dramatic planner.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import random

from .capabilities.api import registry as base_registry
from .capabilities.core import Action, CapabilityError, Entity, Query, Record, WorldSpec, execute, fingerprint, plain, replay
from .capabilities.physical import Container, Ownership, Parent, Route, accessible
from .capabilities.reading import Reader


@dataclass(frozen=True, kw_only=True)
class Performance(Record):
    purpose: str
    noisy: bool = False
    desired_size: int = 1
    performed: bool = False
    ending: str = ""


@dataclass(frozen=True, kw_only=True)
class Player(Record):
    line: str | None = None
    wearing: str | None = None
    mode: str = "spoken"


@dataclass(frozen=True, kw_only=True)
class Prop(Record):
    size: int = 1
    units: int = 0
    text: str | None = None


@dataclass(frozen=True, kw_only=True)
class Projection(Record):
    distance: int = 1
    size: int = 0
    event_id: str = ""


@dataclass(frozen=True, kw_only=True)
class Notice(Record):
    actor: str
    target: str
    kind: str
    value: str
    event_id: str


def notice(tx, id, target, kind, value):
    tx.require(tx.maybe("theater_notices", id) is None, "Notice already made")
    tx.put("theater_notices", Notice(id=id, actor=tx.action.actor, target=target, kind=kind, value=str(value), event_id=tx.event_id))


def project(tx, *, distance):
    tx.require(distance in (1, 3) and type(distance) is int, "Use one of the two marked distances")
    tx.require(all(accessible(tx, tx.action.actor, x) for x in ("figure", "lamp")), "Shadow apparatus out of reach")
    lamp = tx.get("theater_props", "lamp")
    tx.require(lamp.units > 0, "Lamp has no remaining charge")
    tx.put("theater_props", replace(lamp, units=lamp.units - 1))
    tx.put("theater_projections", Projection(id="screen", distance=distance, size=3 if distance == 1 else 1, event_id=tx.event_id))
    tx.emit(object="figure", distance=distance, size=3 if distance == 1 else 1)


def look(tx, *, target, reading):
    tx.require(accessible(tx, tx.action.actor, target), "Look from a place with access")
    if target == "screen":
        p = tx.get("theater_projections", target)
        tx.require(bool(p.event_id), "No shadow has been projected")
        tx.depend(p.event_id)
        value, kind = str(p.size), "shadow"
    else:
        tx.require(target == "figure", "Unknown inspection target")
        value, kind = "paper cutout", "source"
    notice(tx, reading, target, kind, value)
    tx.emit(target=target, kind=kind, value=value)


def read_line(tx):
    tx.require(accessible(tx, tx.action.actor, "book"), "Prompt book out of reach")
    line = tx.get("theater_props", "book").text
    player = tx.get("theater_players", tx.action.actor)
    tx.put("theater_players", replace(player, line=line))
    notice(tx, "read_" + tx.action.actor, "book", "line", line or "blank page")
    tx.emit(reader=tx.action.actor, line=line)


def whisper(tx):
    tx.require(tx.action.actor == "jo" and tx.get("parents", "jo").parent == "wings" and tx.get("parents", "mina").parent == "stage",
               "Cue is from the wings to the stage")
    line = tx.get("theater_players", "jo").line
    tx.require(bool(line), "Cannot prompt a line not read")
    heard = not tx.get("performances", "stage").noisy
    if heard:
        tx.put("theater_players", replace(tx.get("theater_players", "mina"), line=line))
    notice(tx, "cue", "mina", "audible", str(heard))
    tx.emit(speaker="jo", listener="mina", heard=heard)


def mime(tx):
    tx.require(tx.action.actor == "mina" and tx.get("parents", "mina").parent == "stage", "Mime starts on stage")
    seen = tx.get("theater_notices", "read_mina")
    tx.require(seen.actor == "mina" and seen.value == "blank page" and tx.get("theater_props", "book").text is None,
               "Mina must inspect the blank page before choosing a substitute")
    tx.depend(seen.event_id)
    tx.put("theater_players", replace(tx.get("theater_players", "mina"), mode="mime"))
    tx.emit(actor="mina", choice="wordless welcome")


def try_crown(tx, *, reading):
    tx.require(tx.action.actor == "mina" and accessible(tx, "mina", "crown"), "Crown fitting needs Mina and the crown")
    fit = tx.get("theater_props", "crown").size == 1
    tx.put("parents", Parent(id="crown", parent="mina" if fit else "tray"))
    tx.put("theater_players", replace(tx.get("theater_players", "mina"), wearing="crown" if fit else None))
    notice(tx, reading, "crown", "fit", str(fit))
    tx.emit(object="crown", fits=fit, destination="mina" if fit else "tray")


def resize(tx):
    tx.require(all(accessible(tx, tx.action.actor, x) for x in ("crown", "clip")), "Costume tools out of reach")
    crown, clip = tx.get("theater_props", "crown"), tx.get("theater_props", "clip")
    tx.require(crown.size == 2 and clip.units > 0, "Need large adjustable crown and spare clip")
    tx.put("theater_props", replace(crown, size=1))
    tx.put("theater_props", replace(clip, units=clip.units - 1))
    tx.emit(object="crown", size=1, tool="clip")


def perform(tx):
    scene, player = tx.get("performances", "stage"), tx.get("theater_players", "mina")
    tx.require(tx.action.actor == "mina" and tx.get("parents", "mina").parent == "stage" and not scene.performed,
               "Mina performs once, on stage")
    if scene.purpose == "shadow":
        seen = tx.get("theater_notices", "source")
        projection = tx.get("theater_projections", "screen")
        tx.require(seen.actor == "mina" and seen.target == "figure" and seen.kind == "source", "Mina must discover the actual source")
        tx.require(projection.size == scene.desired_size, "Use the intended shadow size")
        tx.depend(seen.event_id)
        tx.depend(projection.event_id)
        ending = "small_shadow" if projection.size == 1 else "giant_shadow"
    elif scene.purpose == "cue":
        tx.require(tx.get("containers", "door").open and tx.get("parents", "jo").parent == "stage", "Welcome must actually admit the visitor")
        tx.require(player.line is not None or player.mode == "mime", "Need a recovered line or an enacted wordless plan")
        ending = "wordless_welcome" if player.mode == "mime" else "spoken_welcome"
    else:
        tx.require(scene.purpose == "crown", "Unknown performance purpose")
        worn = player.wearing == "crown" and tx.get("parents", "crown").parent == "mina"
        displayed = tx.get("parents", "crown").parent == "chair"
        tx.require(worn or displayed, "Crown must be fitted or placed on the royal chair")
        ending = "worn_crown" if worn else "crown_on_chair"
    tx.put("performances", replace(scene, performed=True, ending=ending))
    tx.emit(actor="mina", ending=ending, line=player.line)


def validate(state):
    for row in state.tables["performances"].values():
        if (row.id != "stage" or row.purpose not in {"shadow", "cue", "crown"} or type(row.noisy) is not bool
                or row.desired_size not in (1, 3) or type(row.performed) is not bool or row.performed != bool(row.ending)):
            raise CapabilityError("Invalid theater performance")
    for row in state.tables["theater_players"].values():
        if state.get("entities", row.id).kind != "actor" or row.mode not in {"spoken", "mime"}:
            raise CapabilityError("Player needs a physical actor")
        if row.wearing and (row.wearing != "crown" or state.get("parents", row.wearing).parent != row.id or state.get("theater_props", "crown").size != 1):
            raise CapabilityError("Worn crown must fit and remain with its wearer")
    for row in state.tables["theater_props"].values():
        if state.get("entities", row.id) is None or type(row.units) is not int or row.units < 0 or type(row.size) is not int or row.size < 1:
            raise CapabilityError("Prop must be a physical finite resource")
    for row in state.tables["theater_projections"].values():
        if row.id != "screen" or row.distance not in (1, 3) or row.size not in (0, 1, 3) or (row.size != 0 and row.size != (3 if row.distance == 1 else 1)):
            raise CapabilityError("Shadow must follow the toy geometry")
    for row in state.tables["theater_notices"].values():
        if state.get("entities", row.actor).kind != "actor" or state.get("entities", row.target) is None or not row.event_id:
            raise CapabilityError("Notice needs grounded actor, object and event")


def initial(state):
    if state.tables["theater_notices"] or state.get("performances", "stage").performed or state.get("theater_projections", "screen").size:
        raise CapabilityError("Observations and performances must be enacted")


def registry():
    eng = base_registry()
    for table, record in (("performances", Performance), ("theater_players", Player), ("theater_props", Prop),
                          ("theater_projections", Projection), ("theater_notices", Notice)):
        eng.table(table, record)
    eng.validators.append(validate)
    eng.initial_validators.append(initial)
    physical = {"entities", "parents", "containers"}
    for name, fn, reads, writes in (
        ("project", project, {"theater_props", "theater_projections"}, {"theater_props", "theater_projections"}),
        ("look", look, {"theater_projections", "theater_notices"}, {"theater_notices"}),
        ("read", read_line, {"theater_props", "theater_players", "theater_notices"}, {"theater_players", "theater_notices"}),
        ("whisper", whisper, {"theater_players", "performances", "theater_notices"}, {"theater_players", "theater_notices"}),
        ("mime", mime, {"theater_props", "theater_players", "theater_notices"}, {"theater_players"}),
        ("try_crown", try_crown, {"theater_props", "theater_players", "theater_notices"}, {"theater_players", "theater_notices", "parents"}),
        ("resize", resize, {"theater_props"}, {"theater_props"}),
        ("perform", perform, {"performances", "theater_players", "theater_notices", "theater_projections"}, {"performances"}),
    ):
        eng.operation("theater_" + name, fn, reads=physical | reads, writes=writes)
    return eng


@dataclass(frozen=True, kw_only=True)
class Conditions:
    purpose: str = "shadow"
    giant_ending: bool = False
    noisy: bool = False
    written_line: bool = True
    large_crown: bool = True
    clip: bool = True

    def __post_init__(self):
        if self.purpose not in {"shadow", "cue", "crown"} or any(type(v) is not bool for k, v in asdict(self).items() if k != "purpose"):
            raise ValueError("Invalid theater conditions")


def conditions(seed):
    rng = random.Random(seed)
    return Conditions(purpose=("shadow", "cue", "crown")[seed % 3],
        **{k: rng.random() < .65 for k in ("giant_ending", "noisy", "written_line", "large_crown", "clip")})


def simulate(c):
    entities = tuple(Entity(id=i, name=n, kind=k, capacity=20) for i, n, k in (
        ("stage", "the stage", "place"), ("wings", "the wings", "place"),
        ("mina", "Mina", "actor"), ("jo", "Jo", "actor"), ("screen", "the paper screen", "object"),
        ("figure", "the paper cutout", "object"), ("lamp", "the lamp", "object"), ("book", "the prompt book", "object"),
        ("crown", "the crown", "object"), ("clip", "the fastening clip", "object"),
        ("tray", "the costume tray", "container"), ("chair", "the royal chair", "container"),
        ("stand", "the reading stand", "container"), ("door", "the stage door", "container")))
    locations = dict(mina="wings" if c.purpose == "crown" else "stage", jo="wings", screen="stage", figure="wings",
                     lamp="wings", book="wings", crown="tray", clip="tray", tray="wings", chair="stage", stand="stage", door="stage")
    records = dict(entities=entities, parents=tuple(Parent(id=i, parent=p) for i, p in locations.items()),
        ownership=(Ownership(id="crown", owner="jo"), Ownership(id="book", owner="jo")),
        containers=tuple(Container(id=i, open=i != "door") for i in ("tray", "chair", "stand", "door")),
        routes=(Route(id="front", source="wings", destination="stage"), Route(id="back", source="stage", destination="wings")),
        performances=(Performance(id="stage", purpose=c.purpose, noisy=c.noisy, desired_size=3 if c.giant_ending else 1),),
        theater_players=(Player(id="mina"), Player(id="jo")), theater_projections=(Projection(id="screen"),),
        theater_props=(Prop(id="lamp", units=3), Prop(id="book", text="The door is open. Come in." if c.written_line else None),
                       Prop(id="crown", size=2 if c.large_crown else 1), Prop(id="clip", units=int(c.clip))))
    actions = []

    def add(id, op, actor="mina", requires=(), **args):
        actions.append(Action(id=id, operation=op, actor=actor, args=args, requires=requires))

    add("large_shadow", "theater_project", "jo", distance=1)
    add("small_shadow", "theater_project", "jo", distance=3)
    add("restore_large", "theater_project", "jo", distance=1)
    add("see_large", "theater_look", target="screen", reading="first_shadow")
    add("see_small", "theater_look", target="screen", reading="second_shadow")
    add("inspect_source", "theater_look", target="figure", reading="source")
    add("backstage", "travel", route="back")
    add("onstage", "travel", route="front")
    add("read_jo", "theater_read", "jo")
    add("cue", "theater_whisper", "jo")
    add("take_book", "pickup", "jo", object="book", source="wings")
    add("show_book", "travel", "jo", route="front")
    add("place_book", "put", "jo", object="book", destination="stand")
    add("read_mina", "theater_read")
    add("jo_back", "travel", "jo", route="back")
    add("mime", "theater_mime")
    add("open_door", "set_container", container="door", open=True)
    add("enter", "travel", "jo", route="front", requires=(Query(table="containers", key="door", field="open", value=True),))
    add("try_crown", "theater_try_crown", reading="first_fit")
    add("resize", "theater_resize")
    add("retry_crown", "theater_try_crown", reading="second_fit")
    add("carry_crown", "pickup", object="crown", source="tray")
    add("display_crown", "put", object="crown", destination="chair")
    add("perform", "theater_perform")
    spec = WorldSpec(title="The little theater", records=records, actions=tuple(actions), max_steps=40,
                     goal=(Query(table="performances", key="stage", field="performed", value=True),))
    eng, choices = registry(), {a.id: a for a in actions}
    state = eng.initial(spec)

    def do(id):
        nonlocal state
        next_state = execute(eng, spec, state, choices[id])
        if next_state is None:
            raise ValueError(f"Theater policy rejected {id}")
        state = next_state

    if c.purpose == "shadow":
        for id in ("large_shadow", "see_large", "small_shadow", "see_small", "backstage", "inspect_source", "onstage"):
            do(id)
        if c.giant_ending:
            do("restore_large")
    elif c.purpose == "cue":
        do("read_jo")
        if state.get("theater_players", "jo").line is None:
            for id in ("take_book", "show_book", "place_book", "read_mina", "jo_back"):
                do(id)
            do("mime")
        else:
            do("cue")
            if state.get("theater_players", "mina").line is None:
                for id in ("take_book", "show_book", "place_book", "read_mina", "jo_back"):
                    do(id)
        do("open_door")
        do("enter")
    else:
        do("try_crown")
        if state.get("theater_players", "mina").wearing is None:
            if state.get("theater_props", "clip").units:
                do("resize")
                do("retry_crown")
            else:
                do("carry_crown")
        do("onstage")
        if state.get("theater_players", "mina").wearing is None:
            do("display_crown")
    do("perform")
    return spec, state


def generate(seed=0, *, prose_seed=None, config=None):
    from .theater_prose import render
    c = config or conditions(seed)
    spec, state = simulate(c)
    path = [e.action.id for e in state.events]
    if replay(registry(), spec, path) != state:
        raise ValueError("Theater replay changed")
    doc = render(spec, state, c, seed if prose_seed is None else prose_seed)
    plot = dict(purpose=c.purpose, outcome=state.get("performances", "stage").ending,
                method="mime" if "mime" in path else "read_visible" if "read_mina" in path else "whisper" if "cue" in path else
                       "resize" if "resize" in path else "display" if "display_crown" in path else "fit" if "try_crown" in path else "test_shadow")
    return dict(sample_id=f"theater:{seed}", world="theater", seed=seed, ok=True, conditions=asdict(c),
        story=doc.story, qa=plain(Reader(doc).questions()), story_sha256=fingerprint(doc.story), trace_sha256=fingerprint(state),
        path=path, plot=plot, words=len(doc.story.split())), spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    row, _, _, _ = generate(args.seed)
    print(row["story"])
    if args.qa:
        for q in row["qa"]:
            print(f"\nQ: {q['question']}\nA: {q['answer']}")


if __name__ == "__main__":
    main()
