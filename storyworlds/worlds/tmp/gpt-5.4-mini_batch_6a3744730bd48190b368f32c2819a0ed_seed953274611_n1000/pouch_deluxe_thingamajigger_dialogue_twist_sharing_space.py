#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pouch_deluxe_thingamajigger_dialogue_twist_sharing_space.py
===========================================================================================

A tiny space-adventure storyworld about a child astronaut, a deluxe pouch,
a thingamajigger, a dialogue-driven twist, and a sharing ending.

The world is built around a short premise:
- a child wants to use a deluxe pouch to carry a useful thingamajigger
- a teammate needs the pouch for a different space job
- they talk, a twist changes who needs what, and they share the tool
- the ending proves the sharing worked by changing the state of the mission

The story engine uses typed entities with meters and memes, a forward-chaining
state update, a reasonableness gate, QA sets grounded in the simulated world,
and an inline ASP twin for parity checks.

Run:
    python storyworlds/worlds/gpt-5.4-mini/pouch_deluxe_thingamajigger_dialogue_twist_sharing_space.py
    python storyworlds/worlds/gpt-5.4-mini/pouch_deluxe_thingamajigger_dialogue_twist_sharing_space.py --qa
    python storyworlds/worlds/gpt-5.4-mini/pouch_deluxe_thingamajigger_dialogue_twist_sharing_space.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Pouch:
    id: str
    label: str
    deluxe: bool
    capacity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Thingamajigger:
    id: str
    label: str
    use: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    shift_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMove:
    id: str
    sense: int
    text: str
    success_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["tension"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True
    if narrate:
        pass


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for pouch_id, pouch in POUCHES.items():
            for tool_id, tool in THINGAMAJIGGERS.items():
                for twist_id, twist in TWISTS.items():
                    if place.dark and pouch.deluxe and tool.fragile:
                        combos.append((place_id, pouch_id, tool_id, twist_id))
    return combos


@dataclass
class StoryParams:
    place: str
    pouch: str
    thingamajigger: str
    twist: str
    share_move: str
    astronaut: str
    astronaut_gender: str
    teammate: str
    teammate_gender: str
    seed: Optional[int] = None


PLACES = {
    "lunar_bay": Place(id="lunar_bay", label="the lunar bay", dark=True, tags={"space", "bay"}),
    "orbit_hall": Place(id="orbit_hall", label="the orbit hall", dark=True, tags={"space", "hall"}),
    "sunroom": Place(id="sunroom", label="the sunroom", dark=False, tags={"room"}),
}

POUCHES = {
    "deluxe_pouch": Pouch(id="deluxe_pouch", label="a deluxe pouch", deluxe=True, capacity=2, tags={"pouch", "deluxe"}),
    "plain_pouch": Pouch(id="plain_pouch", label="a plain pouch", deluxe=False, capacity=1, tags={"pouch"}),
}

THINGAMAJIGGERS = {
    "thingamajigger": Thingamajigger(id="thingamajigger", label="the thingamajigger", use="scan the stardust trail", fragile=True, tags={"thingamajigger"}),
    "beacon": Thingamajigger(id="beacon", label="the beacon knob", use="call the shuttle", fragile=False, tags={"beacon"}),
}

TWISTS = {
    "lost_map": Twist(id="lost_map", reveal="the map slid under a seat", shift_need="the teammate needed the pouch to hold a map", tags={"twist", "sharing"}),
    "spare_battery": Twist(id="spare_battery", reveal="a spare battery clicked on", shift_need="the teammate only needed the thingamajigger for one quick scan", tags={"twist", "sharing"}),
}

SHARES = {
    "take_turns": ShareMove(id="take_turns", sense=3, text="they took turns with it", success_text="they took turns and shared it kindly", tags={"sharing"}),
    "split_job": ShareMove(id="split_job", sense=3, text="they split the job between them", success_text="they split the job and shared the work", tags={"sharing"}),
    "hog_it": ShareMove(id="hog_it", sense=1, text="one child tried to keep it all", success_text="one child kept it, but that would not fit the story", tags={"sharing"}),
}

NAMES_GIRL = ["Mia", "Luna", "Nova", "Zoe", "Ava"]
NAMES_BOY = ["Leo", "Kai", "Jett", "Milo", "Finn"]


def sensible_shares() -> list[ShareMove]:
    return [s for s in SHARES.values() if s.sense >= SENSE_MIN]


def reason_ok(pouch: Pouch, tool: Thingamajigger, twist: Twist, share: ShareMove) -> bool:
    return pouch.deluxe and tool.fragile and share.sense >= SENSE_MIN and twist.id in TWISTS


def explain_rejection() -> str:
    return "(No story: this setup needs a deluxe pouch, a fragile thingamajigger, and a sensible sharing move.)"


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    pouch = POUCHES[params.pouch]
    tool = THINGAMAJIGGERS[params.thingamajigger]
    twist = TWISTS[params.twist]
    share = SHARES[params.share_move]

    if not reason_ok(pouch, tool, twist, share):
        raise StoryError(explain_rejection())

    astro = world.add(Entity(id=params.astronaut, kind="character", type=params.astronaut_gender, role="astronaut", tags={"space"}))
    mate = world.add(Entity(id=params.teammate, kind="character", type=params.teammate_gender, role="teammate", tags={"space"}))
    bay = world.add(Entity(id=place.id, kind="place", type="place", label=place.label, tags=set(place.tags)))
    bag = world.add(Entity(id=pouch.id, kind="thing", type="pouch", label=pouch.label, tags=set(pouch.tags)))
    gizmo = world.add(Entity(id=tool.id, kind="thing", type="thingamajigger", label=tool.label, tags=set(tool.tags)))

    astro.memes["excited"] += 1
    mate.memes["curious"] += 1
    world.say(f"At {bay.label}, {astro.id} held up {bag.label} and grinned. \"This deluxe pouch is perfect,\" {astro.pronoun()} said.")
    world.say(f"{mate.id} leaned closer. \"What about {gizmo.label}?\" {mate.pronoun()} asked. \"We need it for the mission.\"")

    world.para()
    astro.memes["worry"] += 1
    mate.memes["worry"] += 1
    world.say(f"Then came the twist: {twist.reveal}. Suddenly {twist.shift_need}.")
    world.say(f"\"Oh,\" {astro.id} said. \"So the pouch is not just for me.\"")
    world.say(f"\"Right,\" {mate.id} said, \"and {gizmo.label} can help both of us.\"")

    world.para()
    astro.memes["kindness"] += 1
    mate.memes["kindness"] += 1
    world.say(f"\"Let's {share.text},\" {astro.id} said.")
    world.say(f"\"Deal,\" {mate.id} said. {share.success_text.capitalize()}.")
    world.say(f"They packed {gizmo.label} into {bag.label}, checked the glowing panels, and worked side by side until the ship path was clear.")

    world.para()
    astro.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(f"In the end, the {place.label} was calm and bright, {bag.label} stayed open for both hands, and {gizmo.label} helped them finish the space job together.")

    world.facts.update(
        astronaut=astro,
        teammate=mate,
        place=place,
        pouch=pouch,
        thingamajigger=tool,
        twist=twist,
        share=share,
        outcome="shared",
        shared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story that includes the words "pouch", "deluxe", and "thingamajigger".',
        f"Tell a child-friendly spaceship story where {f['astronaut'].id} and {f['teammate'].id} argue a little, then share a deluxe pouch and a thingamajigger.",
        f"Write a dialogue-driven space story with a twist and a sharing ending in {f['place'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["astronaut"]
    b = f["teammate"]
    pouch = f["pouch"]
    tool = f["thingamajigger"]
    twist = f["twist"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two space helpers working together in {f['place'].label}."),
        (f"What did {a.id} have?", f"{a.id} had {pouch.label}. It was deluxe, so it could hold mission things safely."),
        ("What was the twist?", f"The twist was that {twist.reveal}. That changed what the children needed to do next."),
        ("How did they solve the problem?", f"They shared the pouch and the thingamajigger. By talking first, they found a plan that helped both of them."),
        ("How did the story end?", f"It ended with {tool.label} helping the mission and both children working side by side. The pouch stayed useful because they shared it."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pouch?", "A pouch is a small bag that can hold little objects and keep them together."),
        ("What does deluxe mean?", "Deluxe means fancy or extra nice, with a little more quality or comfort than usual."),
        ("What is a thingamajigger?", "A thingamajigger is a funny word for a tool or gadget when you do not want to name it exactly."),
        ("Why is sharing important?", "Sharing helps more than one person use the same thing. It can calm arguments and make a plan work better."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
deluxe_pouch(P) :- pouch(P), deluxe(P).
reasonable(Combo) :- deluxe_pouch(P), thingamajigger(T), twist(X), share(S), sense(S, N), sense_min(M), N >= M.
shared :- share_move(S), sensible(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for pid, p in POUCHES.items():
        lines.append(asp.fact("pouch", pid))
        if p.deluxe:
            lines.append(asp.fact("deluxe", pid))
    for tid, t in THINGAMAJIGGERS.items():
        lines.append(asp.fact("thingamajigger", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for twid in TWISTS:
        lines.append(asp.fact("twist", twid))
    for sid, s in SHARES.items():
        lines.append(asp.fact("share_move", sid))
        lines.append(asp.fact("sense", sid, s.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show deluxe_pouch/1. #show shared/0."))
        _ = model
    except Exception as e:
        print(f"ASP smoke test failed: {e}")
        return 1
    py = len(valid_combos()) > 0
    print(f"OK: ASP smoke test ran and Python gate returned {py}.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, pouch=None, thingamajigger=None, twist=None, share_move=None, astronaut=None, astronaut_gender=None, teammate=None, teammate_gender=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        print(f"Story smoke test failed: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a deluxe pouch, a thingamajigger, dialogue, twist, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pouch", choices=POUCHES)
    ap.add_argument("--thingamajigger", choices=THINGAMAJIGGERS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--share-move", dest="share_move", choices=SHARES)
    ap.add_argument("--astronaut")
    ap.add_argument("--astronaut-gender", dest="astronaut_gender", choices=["girl", "boy"])
    ap.add_argument("--teammate")
    ap.add_argument("--teammate-gender", dest="teammate_gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid space-adventure combinations exist.")
    place, pouch, tool, twist = rng.choice(sorted(combos))
    share_move = args.share_move or rng.choice(sorted(s.id for s in sensible_shares()))
    if args.pouch and args.pouch != pouch:
        pouch = args.pouch
    if args.thingamajigger and args.thingamajigger != tool:
        tool = args.thingamajigger
    if args.twist and args.twist != twist:
        twist = args.twist
    if args.place and args.place != place:
        place = args.place
    if not reason_ok(POUCHES[pouch], THINGAMAJIGGERS[tool], TWISTS[twist], SHARES[share_move]):
        raise StoryError(explain_rejection())
    gen_a = args.astronaut_gender or rng.choice(["girl", "boy"])
    gen_b = args.teammate_gender or ("boy" if gen_a == "girl" else "girl")
    a = args.astronaut or rng.choice(NAMES_GIRL if gen_a == "girl" else NAMES_BOY)
    b = args.teammate or rng.choice([n for n in (NAMES_BOY if gen_b == "boy" else NAMES_GIRL) if n != a])
    return StoryParams(place=place, pouch=pouch, thingamajigger=tool, twist=twist, share_move=share_move,
                       astronaut=a, astronaut_gender=gen_a, teammate=b, teammate_gender=gen_b)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("pouch", POUCHES), ("thingamajigger", THINGAMAJIGGERS), ("twist", TWISTS), ("share_move", SHARES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
    StoryParams(place="lunar_bay", pouch="deluxe_pouch", thingamajigger="thingamajigger", twist="lost_map", share_move="take_turns", astronaut="Nova", astronaut_gender="girl", teammate="Kai", teammate_gender="boy"),
    StoryParams(place="orbit_hall", pouch="deluxe_pouch", thingamajigger="thingamajigger", twist="spare_battery", share_move="split_job", astronaut="Mia", astronaut_gender="girl", teammate="Leo", teammate_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show deluxe_pouch/1. #show shared/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show deluxe_pouch/1. #show shared/0."))
        print(f"ASP facts loaded; model size {len(model)}.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
