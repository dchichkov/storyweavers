#!/usr/bin/env python3
"""
A small fable-like story world about a flexible choice, a warning, and a kind
reconciliation.

Premise:
A young heron wants to cross a river to reach ripe berries on the far bank.
A badger friend warns that the usual straight log bridge is slippery after rain.
The heron first insists, then learns to bend with the moment and chooses a
flexible path: a swaying reed crossing guided by a shared rope.

The storyworld keeps the causal state in a tiny simulation:
- actors have meters and memes
- the river, bridge, reeds, and rope change physical state
- dialogue and foreshadowing are driven by world state
- reconciliation clears the social tension

The tone is a simple fable: concrete, gentle, and lesson-shaped.
"""

from __future__ import annotations

import argparse
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
    wears: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "bird": {"subject": "she", "object": "her", "possessive": "her"},
            "heron": {"subject": "she", "object": "her", "possessive": "her"},
            "badger": {"subject": "he", "object": "him", "possessive": "his"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    near: str
    far: str
    affords: set[str] = field(default_factory=set)
    slippery: bool = False


@dataclass
class Crossing:
    id: str
    label: str
    kind: str
    flexible: bool
    safe_when_wet: bool
    spans: str
    requires: Optional[str] = None
    dialog_offer: str = ""
    dialog_warning: str = ""
    dialog_accept: str = ""


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def fable_moral() -> str:
    return "A flexible heart finds a safe path when a rigid one would slip."


def _apply_slip(world: World) -> list[str]:
    out: list[str] = []
    river = world.get("river")
    if river.meters.get("wet", 0) < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.wears == "bridge" and not world.facts.get("bridge_safe_when_wet", False):
            sig = ("slip", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["fear"] = ent.memes.get("fear", 0) + 1
            out.append(f"The crossing shivered under the wet air.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _apply_slip(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Lila"
    helper: str = "Bram"
    hero_type: str = "heron"
    helper_type: str = "badger"
    place: str = "riverbank"
    crossing: str = "reed_path"


PLACES = {
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        near="the near bank",
        far="the berry thicket",
        affords={"crossing"},
        slippery=True,
    ),
}

CROSSINGS = {
    "reed_path": Crossing(
        id="reed_path",
        label="the reed path",
        kind="reeds",
        flexible=True,
        safe_when_wet=True,
        spans="across the water",
        requires="rope",
        dialog_offer="We can tie a rope to the reeds and bend with the wind.",
        dialog_warning="That old log is slick after rain, and it may roll.",
        dialog_accept="Then let us use the flexible path and keep our feet light.",
    ),
    "log_bridge": Crossing(
        id="log_bridge",
        label="the old log bridge",
        kind="log",
        flexible=False,
        safe_when_wet=False,
        spans="across the water",
        requires=None,
        dialog_offer="We could cross fast on the log.",
        dialog_warning="That log is slippery after rain.",
        dialog_accept="Let us not trust the slick log today.",
    ),
}

BERRIES = {
    "berries": "sweet berries",
}

HERO_NAMES = ["Lila", "Mina", "Taro", "Suri", "Niko"]
HELPER_NAMES = ["Bram", "Moss", "June", "Orin", "Pax"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about flexible choices.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    place = args.place or "riverbank"
    crossing = args.crossing or rng.choice(list(CROSSINGS))
    return StoryParams(
        seed=args.seed,
        name=name,
        helper=helper,
        place=place,
        crossing=crossing,
    )


def _tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    crossing = CROSSINGS[params.crossing]
    world = World(place)

    hero = world.add(Entity(id="hero", kind="character", type="heron", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="badger", label=params.helper))
    river = world.add(Entity(id="river", kind="thing", type="river", label="the river"))
    rope = world.add(Entity(id="rope", kind="thing", type="rope", label="a rope", plural=False))
    bridge = world.add(Entity(id="bridge", kind="thing", type=crossing.kind, label=crossing.label))
    berries = world.add(Entity(id="berries", kind="thing", type="berries", label=BERRIES["berries"]))
    bridge.wears = "bridge"
    world.facts["bridge_safe_when_wet"] = crossing.safe_when_wet
    world.facts["flexible"] = crossing.flexible
    world.facts["crossing"] = crossing
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["river"] = river
    world.facts["rope"] = rope
    world.facts["berries"] = berries

    world.say(f"{hero.label} was a little heron who loved the far bank where the sweet berries grew.")
    world.say(f"{helper.label} was a patient badger who watched the weather and listened before he leaped.")
    world.say(f"One morning, after rain, the river shone silver and the berry thicket looked very tempting.")
    world.say(f"{hero.label} wanted to go at once, and the old log bridge looked like the quickest way.")
    world.para()
    world.say(f'"We can cross now," said {hero.label}.')
    world.say(f'"{crossing.dialog_warning}" said {helper.label}.')
    if crossing.flexible:
        world.say(f'"{crossing.dialog_offer}"')
    else:
        world.say(f'"{crossing.dialog_offer}"')

    river.meters["wet"] = 1
    propagate(world, narrate=True)
    world.para()
    if crossing.flexible:
        hero.memes["stubborn"] = 1
        world.say(f"{hero.label} hesitated, because the log looked familiar and the reeds looked bendy and strange.")
        world.say(f'"I only know the old way," {hero.label} said.')
        world.say(f'"Then learn the flexible way," said {helper.label}, and he tied the rope to the reeds.')
        hero.memes["curious"] = 1
        bridge.wears = "reed_path"
        world.say(f"{hero.label} tested the reed path. It swayed, but it held, because it could flex without breaking.")
        world.say(f'"{crossing.dialog_accept}" said {hero.label}, and {helper.label} nodded.')
        hero.memes["joy"] = 1
        helper.memes["joy"] = 1
        hero.memes["conflict"] = 0
        world.say(f"Together they crossed slowly, and the reeds bent like a bow instead of snapping like a stick.")
        world.say(f"On the far bank, the berries were still sweet, and both friends laughed softly at their wise choice.")
    else:
        hero.memes["stubborn"] = 1
        world.say(f"{hero.label} tried the old log bridge, but the wet wood slid under small feet.")
        world.say(f"{helper.label} called out, and {hero.label} turned back before the river could take a tumble into trouble.")
        world.say(f'Then they found a safer way, because even proud feet must sometimes listen.')
        hero.memes["conflict"] = 1
        helper.memes["concern"] = 1
        hero.memes["joy"] = 1
        helper.memes["joy"] = 1
        world.say(f"They did not argue long. A wiser path made the day kinder.")
    world.para()
    world.say(f"In the end, {hero.label} learned that being flexible is not weakness; it is a way to keep moving.")
    world.say(f"{fable_moral()}")
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = _tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    crossing = f["crossing"]
    return [
        "Write a gentle fable about a flexible choice, a warning, and a safe crossing.",
        f"Tell a story about {hero.label} the heron and {helper.label} the badger, where a crossing choice matters after rain.",
        f"Write a short animal tale that uses the word flexible and ends with reconciliation across a river.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    crossing = world.facts["crossing"]
    qas = [
        QAItem(
            question=f"Who wanted to cross the river for the berries?",
            answer=f"{hero.label}, the little heron, wanted to cross the river to reach the berries on the far bank.",
        ),
        QAItem(
            question=f"What did {helper.label} warn about?",
            answer=f"{helper.label} warned that the old log bridge was slippery after rain and might be a bad choice.",
        ),
        QAItem(
            question="What flexible thing helped them cross safely?",
            answer="A flexible reed path tied with a rope helped them cross safely because it could bend without breaking.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The friends reconciled, crossed together, and reached the far bank safely with a wiser heart.",
        ),
    ]
    if crossing.flexible:
        qas.append(QAItem(
            question="Why was the reed path a better choice than the old log bridge?",
            answer="The reed path was better because it was flexible, and the rope made it steady enough to cross after rain.",
        ))
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flexible mean?",
            answer="Flexible means something can bend, change, or move with a new situation instead of breaking or staying stiff.",
        ),
        QAItem(
            question="Why can wet wood be slippery?",
            answer="Wet wood can be slippery because water makes the surface smoother, so feet can slide more easily.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and come back together kindly after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.wears:
            bits.append(f"wears={e.wears}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Flexible crossings are those that can bend, and safe crossings are the ones
% that remain safe after rain.
flexible(C) :- crossing(C), flex(C).
safe(C) :- crossing(C), safe_when_wet(C).
recommended(C) :- flexible(C), safe(C).
resolved :- recommended(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        if c.flexible:
            lines.append(asp.fact("flex", cid))
        if c.safe_when_wet:
            lines.append(asp.fact("safe_when_wet", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("riverbank", cid) for cid, c in CROSSINGS.items() if c.flexible and c.safe_when_wet]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show recommended/1."))
    return sorted(set(asp.atoms(model, "recommended")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: ASP matches Python ({len(py)} recommended crossings).")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(clingo_set))
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        place=args.place or "riverbank",
        crossing=args.crossing or rng.choice(list(CROSSINGS)),
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
    StoryParams(name="Lila", helper="Bram", place="riverbank", crossing="reed_path"),
]


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show recommended/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show recommended/1."))
        print(sorted(set(asp.atoms(model, "recommended"))))
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
