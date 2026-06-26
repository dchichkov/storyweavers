#!/usr/bin/env python3
"""
storyworlds/worlds/capture_levis_curiosity_magic_cautionary_tall_tale.py
=========================================================================

A standalone storyworld for a curious, magical, cautionary tall tale about
trying to capture something marvelous without ruining a treasured pair of
levis.

The seed image behind this world is a child in the dusk, full of curiosity,
chasing a small bit of magic, while a careful grown-up warns about trouble.
The world keeps that premise, but lets the details vary within a tight set of
reasonable combinations.

Core idea:
- A child is curious about a magical thing they want to capture.
- The child wears prized levis.
- The chase can snag, stain, or otherwise ruin the levis.
- A cautious grown-up foresees the danger and offers a safer way.
- The story ends with the child still getting the wonder, but in a wiser way.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- imports results eagerly
- imports asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default generation, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"torn": 0.0, "muddy": 0.0, "dusty": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "caution": 0.0, "joy": 0.0, "worry": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ACTIVITIES = {
    "fireflies": Activity(
        id="fireflies",
        verb="capture the fireflies",
        gerund="capturing fireflies",
        rush="run after the fireflies",
        mess="torn",
        soil="snagged and torn",
        zone={"legs"},
        weather="dusky",
        keyword="fireflies",
        tags={"magic", "curiosity"},
    ),
    "moonmoths": Activity(
        id="moonmoths",
        verb="capture the moon-moths",
        gerund="capturing moon-moths",
        rush="dash after the moon-moths",
        mess="dusty",
        soil="dusty and snagged",
        zone={"legs"},
        weather="dusky",
        keyword="moon-moths",
        tags={"magic", "curiosity"},
    ),
    "willowlights": Activity(
        id="willowlights",
        verb="capture the willow lights",
        gerund="capturing willow lights",
        rush="reach up for the willow lights",
        mess="dusty",
        soil="dusty from the willow bark",
        zone={"legs", "torso"},
        weather="dusky",
        keyword="willow lights",
        tags={"magic", "curiosity"},
    ),
    "sparklefish": Activity(
        id="sparklefish",
        verb="capture the sparkle-fish",
        gerund="capturing sparkle-fish",
        rush="splash after the sparkle-fish",
        mess="muddy",
        soil="muddy from the creek bank",
        zone={"legs"},
        weather="evening",
        keyword="sparkle-fish",
        tags={"magic", "curiosity"},
    ),
}

SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"fireflies", "moonmoths", "willowlights"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"fireflies", "moonmoths", "willowlights"}),
    "creek": Setting(place="the creek bank", indoor=False, affords={"sparklefish"}),
    "lane": Setting(place="the lantern lane", indoor=False, affords={"fireflies", "moonmoths"}),
}

PRIZES = {
    "levis": Prize(
        label="levis",
        phrase="a favorite pair of levis",
        type="levis",
        region="legs",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="chaps",
        label="leather chaps",
        covers={"legs"},
        guards={"torn", "dusty", "muddy"},
        prep="pull on leather chaps first",
        tail="pulled on the leather chaps and tried again",
        plural=True,
    ),
    Gear(
        id="apron",
        label="a waxed apron",
        covers={"torso", "legs"},
        guards={"dusty"},
        prep="tie on a waxed apron first",
        tail="tied on the waxed apron and kept going",
    ),
    Gear(
        id="boots",
        label="tall boots",
        covers={"legs"},
        guards={"muddy"},
        prep="slip on tall boots first",
        tail="slipped on the tall boots and padded along",
        plural=True,
    ),
]

GIRL_NAMES = ["Luna", "Mabel", "Ivy", "June", "Rosie", "Hazel", "Nell", "Ruby"]
BOY_NAMES = ["Finn", "Otis", "Wes", "Hank", "Pip", "Toby", "Nate", "Gus"]
TRAITS = ["curious", "brave", "restless", "bright-eyed", "bouncy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class StoryWorld:
    pass


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a curious child, magical capture, and a cautious turn."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not truly threaten {prize.label}.)"
    return f"(No story: there is no sensible gear that protects {prize.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(id="levis", type="levis", label="levis", phrase="a favorite pair of levis", owner=hero.id, caretaker=parent.id, region="legs", plural=True))
    item.worn_by = hero.id

    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved wonder and wandering.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} levis like they were stitched from moonlight.")
    world.say(f"On a {activity.weather} evening at {setting.place}, {hero.id} heard about {activity.keyword} and wanted to {activity.verb}.")

    world.para()
    world.say(f"{hero.id}'s {params.parent} gave a cautionary look and said, \"Mind the brambles and the mud. Fancy levis do not like a rough chase.\"")
    hero.memes["caution"] += 0.5
    world.say(f"But curiosity can be a mighty horse, and {hero.id} was already trotting toward the glow.")

    world.zone = set(activity.zone)
    hero.meters[activity.mess] += 1
    if activity.mess in {"torn", "dusty", "muddy"}:
        item.meters[activity.mess] += 1
    if not world.covered(hero, "legs"):
        item.meters[activity.mess] += 1

    if item.meters[activity.mess] >= THRESHOLD:
        hero.memes["worry"] += 1
        world.say(f"The chase went wild as a goose in a hailstorm, and the levis came back {activity.soil}.")
        world.say(f"That meant extra work for the {params.parent}, who knew a clean patch is easier than a torn one.")
    gear = select_gear(activity, prize)
    if gear:
        world.para()
        world.say(f"Then the {params.parent} pointed to {gear.label} and said, \"Let's be clever, not reckless.\"")
        world.say(f"{hero.id} {gear.prep}, which kept the levis safe while the magic stayed lively.")
        world.say(f"Together they {gear.tail}, and at last {hero.id} managed to {activity.verb} without ruining {prize.label}.")
        hero.memes["resolve"] += 1
        hero.memes["joy"] += 1
        item.meters[activity.mess] = 0.0

    world.para()
    if gear:
        world.say(f"By bedtime, {hero.id} had one bright story, clean levis, and enough sense to grow another inch in spirit.")
    else:
        world.say(f"By bedtime, {hero.id} learned that a runaway wonder can be caught best with patience and a careful plan.")

    world.facts.update(hero=hero, parent=parent, prize=item, prize_cfg=prize, activity=activity, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short tall tale for a child who wants to {activity.verb} while wearing {prize.label}.',
        f"Tell a cautionary story about {hero.id}, {hero.pronoun('possessive')} levis, and a magical evening at {world.setting.place}.",
        f'Write a gentle, magical story that includes the word "capture" and ends with a wiser choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    prize = f["prize"]
    gear = f["gear"]
    out = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What was {hero.id} wearing that the grown-up wanted to protect?",
            answer=f"{hero.id} was wearing levis, and the {parent.type} wanted to keep them safe.",
        ),
        QAItem(
            question=f"Why was the {parent.type} cautious about the chase?",
            answer=f"The {parent.type} was cautious because the magical chase could leave the levis {activity.soil}.",
        ),
    ]
    if gear:
        out.append(QAItem(
            question=f"What helped {hero.id} capture the magical thing more safely?",
            answer=f"{gear.label} helped because it covered the right place and kept the levis from getting ruined.",
        ))
    return out


KNOWLEDGE = {
    "capture": [
        ("What does it mean to capture something?", "To capture something is to catch it or hold onto it so it does not get away."),
    ],
    "magic": [
        ("What is magic in a story?", "Magic is make-believe power that can do surprising things, like glow, float, or change shape."),
    ],
    "cautionary": [
        ("What does cautious mean?", "Cautious means careful and slow enough to avoid trouble."),
    ],
    "levis": [
        ("What are levis?", "Levis are a kind of denim pants, sturdy enough for hard play but still better kept clean."),
    ],
    "curiosity": [
        ("What is curiosity?", "Curiosity is the wish to find out how something works or what is hiding nearby."),
    ],
}

KNOWLEDGE_ORDER = ["capture", "magic", "cautionary", "curiosity", "levis"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("capture")
    tags.add("levis")
    tags.add("cautionary")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", activity="fireflies", prize="levis", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="orchard", activity="moonmoths", prize="levis", name="Gus", gender="boy", parent="grandfather", trait="bright-eyed"),
    StoryParams(place="creek", activity="sparklefish", prize="levis", name="Mabel", gender="girl", parent="father", trait="restless"),
    StoryParams(place="lane", activity="willowlights", prize="levis", name="Finn", gender="boy", parent="grandmother", trait="bouncy"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:14} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
