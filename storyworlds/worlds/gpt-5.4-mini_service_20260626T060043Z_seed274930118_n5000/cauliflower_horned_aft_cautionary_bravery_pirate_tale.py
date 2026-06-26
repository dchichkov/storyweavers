#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cauliflower_horned_aft_cautionary_bravery_pirate_tale.py
==================================================================================================

A small pirate-tale story world with cautionary warnings and brave choices.

Seed tale:
---
A tiny pirate crew sailed aft of a stormy reef. Their captain loved bravery,
but the lookout kept a cautionary eye on the sea. One day they found a strange
cauliflower-shaped cloud over a horned island. The captain wanted treasure,
but a smart warning about the reef changed the plan. The crew chose a braver,
safer route and still found their way home.

This script turns that premise into a simulated world with physical meters
and emotional memes, plus a declarative ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"safe": 0.0, "risk": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "caution": 0.0, "worry": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "matey"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the sea"
    note: str = ""
    aft: bool = False
    danger: str = ""


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    risk: str
    caution: str
    bravery: str
    location: str


@dataclass
class StoryParams:
    setting: str
    object: str
    hero_name: str
    hero_type: str
    first_mate_name: str
    first_mate_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = dataclasses.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _copy_entity(e: Entity) -> Entity:
    return Entity(**dataclasses.asdict(e))


def _deepcopy_entities(entities: dict[str, Entity]) -> dict[str, Entity]:
    return {k: _copy_entity(v) for k, v in entities.items()}


def _world_copy(self: World) -> World:
    w = World(self.setting)
    w.entities = _deepcopy_entities(self.entities)
    w.fired = set(self.fired)
    w.paragraphs = [[]]
    w.facts = dict(self.facts)
    return w


World.copy = _world_copy  # type: ignore[attr-defined]


SETTINGS = {
    "harbor": Setting(place="the harbor", note="The harbor water rocked the boats gently.", aft=True, danger="reef"),
    "reef": Setting(place="the reef line", note="The reef line hid sharp stones under the waves.", aft=True, danger="reef"),
    "island": Setting(place="the horned island", note="The horned island rose dark and odd from the sea.", aft=False, danger="storm"),
    "cove": Setting(place="the cove", note="The cove stayed quiet, but the rocks could still scratch a hull.", aft=True, danger="rocks"),
}

OBJECTS = {
    "cauliflower": ObjectSpec(
        id="cauliflower",
        label="cauliflower",
        phrase="a cauliflower-white lantern wrapped in sailcloth",
        risk="slip into the foam",
        caution="watch the aft side of the boat",
        bravery="hold course with brave hearts",
        location="aft",
    ),
    "horn": ObjectSpec(
        id="horn",
        label="horn",
        phrase="a horned figurehead carved from driftwood",
        risk="snag the rigging",
        caution="keep the aft ropes clear",
        bravery="face the reef without fear",
        location="aft",
    ),
    "map": ObjectSpec(
        id="map",
        label="map",
        phrase="an old sea map with a crooked red line",
        risk="send them the wrong way",
        caution="read the cautionary marks",
        bravery="choose the safer route anyway",
        location="aft",
    ),
}

NAMES = ["Ava", "Nia", "Mara", "Finn", "Oren", "Beck", "Luna", "Rhett"]
TYPES = ["captain", "matey", "pirate", "lookout", "sailor"]


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        label=params.hero_name, meters={"safe": 0.0, "risk": 0.0, "found": 0.0},
        memes={"bravery": 0.0, "caution": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    mate = world.add(Entity(
        id=params.first_mate_name, kind="character", type=params.first_mate_type,
        label=params.first_mate_name, meters={"safe": 0.0, "risk": 0.0, "found": 0.0},
        memes={"bravery": 0.0, "caution": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    treasure = world.add(Entity(
        id=obj.id, type="thing", label=obj.label, phrase=obj.phrase,
        owner=hero.id, caretaker=mate.id, location=obj.location,
        meters={"safe": 0.0, "risk": 0.0, "found": 0.0},
    ))
    world.facts = {"hero": hero, "mate": mate, "treasure": treasure, "spec": obj}
    return world


def warning_rule(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    treasure = world.facts["treasure"]
    spec = world.facts["spec"]
    if hero.memes["bravery"] >= THRESHOLD and hero.memes["caution"] < THRESHOLD:
        sig = ("warn", treasure.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["warned"] = True
            world.say(
                f"{mate.id} gave a cautionary warning about the {world.setting.danger}: "
                f'"Keep an eye on the aft side, or the {treasure.label} might {spec.risk}."'
            )
            out.append("warned")
    return out


def danger_rule(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    treasure = world.facts["treasure"]
    spec = world.facts["spec"]
    if hero.memes["bravery"] >= THRESHOLD and not world.facts.get("safer_route"):
        sig = ("risk", treasure.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["risk"] += 1
            treasure.meters["risk"] += 1
            out.append(f"The {treasure.label} was in danger of trouble aft of the reef.")
            world.say(out[-1])
    return out


def safe_route_rule(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("warned") and not world.facts.get("safer_route"):
        world.facts["safer_route"] = True
        hero = world.facts["hero"]
        mate = world.facts["mate"]
        treasure = world.facts["treasure"]
        spec = world.facts["spec"]
        hero.memes["caution"] += 1
        hero.memes["relief"] += 1
        hero.meters["safe"] += 1
        treasure.meters["safe"] += 1
        world.say(
            f"{hero.id} listened, turned the helm, and chose a safer route aft of the reef."
        )
        world.say(
            f"That brave choice kept the {treasure.label} from trouble, and {mate.id} smiled beside the mast."
        )
        out.append("safe_route")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (warning_rule, danger_rule, safe_route_rule):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


def tell(world: World) -> World:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    treasure = world.facts["treasure"]
    spec = world.facts["spec"]

    world.say(
        f"On the aft deck, {hero.id} was a bold {hero.type} who loved {spec.bravery}."
    )
    world.say(
        f"{mate.id} was the {mate.type} who watched the sea with a cautionary eye."
    )
    world.say(
        f"Together they kept {treasure.phrase} near the lantern, where the wind could not easily steal it."
    )

    world.para()
    world.say(
        f"One gray day, the ship drifted near {world.setting.place}, where the air tasted like salt and storm."
    )
    world.say(
        f"{hero.id} wanted to claim the sight at once, even though the horned rocks looked sharp as teeth."
    )
    hero.memes["bravery"] += 1
    hero.memes["worry"] += 0.5
    propagate(world)

    world.para()
    if world.facts.get("warned"):
        world.say(
            f"{hero.id} paused, listened to the cautionary warning, and looked again at the aft ropes."
        )
        world.say(
            f"Then {hero.id} chose the braver thing: not rushing ahead, but steering safely so the whole crew could return."
        )
        propagate(world)

    world.para()
    if world.facts.get("safer_route"):
        world.say(
            f"At sunset, the ship slipped home with the {treasure.label} still safe, and the crew cheered for brave caution."
        )
    else:
        world.say(
            f"By dusk, the ship still had a hard path ahead, but the crew had learned to heed a warning before the sea grew mean."
        )
    return world


def build_story(params: StoryParams) -> StorySample:
    world = tell(make_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a young child that includes the words "cauliflower", "horned", and "aft".',
        f"Tell a cautionary-but-brave pirate story where {f['hero'].id} learns to listen to a warning about the {world.setting.danger}.",
        f"Write a small story about a ship near {world.setting.place} that ends with a safer route and a happy crew.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    treasure = world.facts["treasure"]
    spec = world.facts["spec"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a brave {hero.type}, and {mate.id}, who gave the cautionary warning.",
        ),
        QAItem(
            question=f"What did {mate.id} warn about?",
            answer=f"{mate.id} warned about the {world.setting.danger} near the aft side of the ship and about the {treasure.label} getting lost or hurt.",
        ),
        QAItem(
            question=f"Why was the warning useful?",
            answer=f"It was useful because it helped {hero.id} choose a safer route instead of pushing ahead into trouble.",
        ),
        QAItem(
            question=f"What stayed safe by the end?",
            answer=f"The {treasure.label} stayed safe, and the crew made it home with their brave choice intact.",
        ),
    ]
    if world.facts.get("safer_route"):
        qa.append(QAItem(
            question=f"How did {hero.id} show bravery without being careless?",
            answer=f"{hero.id} showed bravery by listening first, then steering the ship safely instead of rushing into the danger.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does aft mean on a ship?",
            answer="Aft means toward the back of the ship.",
        ),
        QAItem(
            question="Why can caution be helpful at sea?",
            answer="Caution is helpful at sea because the water, rocks, and storms can be dangerous, so a warning can keep everyone safe.",
        ),
        QAItem(
            question="What is cauliflower?",
            answer="Cauliflower is a white vegetable with a bumpy shape that can look like a little cloud.",
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means being willing to do a hard thing even when it feels scary, especially when you do it in a smart way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
mate(M) :- mate_name(M).
treasure(T) :- treasure_id(T).

brave(H) :- brave_name(H).
warned :- cautionary_warning.
safer_route :- warned.
safe_treasure(T) :- treasure(T), safer_route.

#show warned/0.
#show safer_route/0.
#show safe_treasure/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname in SETTINGS:
        lines.append(asp.fact("setting", sname))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("treasure_id", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_treasure/1.\n#show warned/0.\n#show safer_route/0."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    if ("safer_route", ()) in atoms and ("warned", ()) in atoms:
        print("OK: ASP twin produces the expected warning and safer-route markers.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected markers.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale story world with caution and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--first-mate-name")
    ap.add_argument("--first-mate-type", choices=TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    hero_type = args.hero_type or rng.choice(["captain", "pirate", "lookout"])
    mate_type = args.first_mate_type or rng.choice(["matey", "lookout", "pirate"])
    hero_name = args.hero_name or rng.choice(NAMES)
    mate_name = args.first_mate_name or rng.choice([n for n in NAMES if n != hero_name])
    if args.setting and args.object and args.setting == "island" and args.object == "cauliflower":
        pass
    return StoryParams(
        setting=setting,
        object=obj,
        hero_name=hero_name,
        hero_type=hero_type,
        first_mate_name=mate_name,
        first_mate_type=mate_type,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="harbor", object="cauliflower", hero_name="Iris", hero_type="captain", first_mate_name="Milo", first_mate_type="lookout"),
    StoryParams(setting="reef", object="horn", hero_name="Nora", hero_type="pirate", first_mate_name="Ben", first_mate_type="matey"),
    StoryParams(setting="cove", object="map", hero_name="Jace", hero_type="captain", first_mate_name="Luna", first_mate_type="lookout"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_treasure/1.\n#show warned/0.\n#show safer_route/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.setting} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
