#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A small nursery-rhyme story world about a child, a misunderstanding, a barricade,
and a happy ending.

Premise seed:
- A little child is happily doing a mark-gerund activity.
- Someone sees the mess, mistakes it for trouble, and builds a barricade.
- The misunderstanding is cleared up with a gentle explanation.
- The ending is warm, tidy, and safe.

The world is intentionally small and constraint-checked. Every generated story is
driven by world state: meters (physical changes) and memes (emotional changes).
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    gerund: str
    verb: str
    mark_gerund: str
    mess: str
    zone: set[str]
    keyword: str


@dataclass
class Barricade:
    id: str
    label: str
    phrase: str
    uses: str
    clears: str
    blocks: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_mess(world: World) -> list[str]:
    out = []
    child = world.get("child")
    mark = world.get("mark")
    if child.meters["mess"] < THRESHOLD or mark.meters["cleaned"] >= THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mark.meters["smudged"] += 1
    out.append(f"The {mark.label} got a little {child.attrs.get('mess_word', 'messy')}.")
    return out


def _r_barricade(world: World) -> list[str]:
    out = []
    if world.get("observer").memes["worry"] < THRESHOLD:
        return out
    if world.get("barricade").meters["built"] >= THRESHOLD:
        return out
    sig = ("barricade",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("barricade").meters["built"] += 1
    out.append(f"A little barricade stood up by the door.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("barricade", _r_barricade)]


def check_reasonable(activity: Activity, barricade: Barricade) -> bool:
    return activity.keyword in barricade.blocks


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            if check_reasonable(ACTIVITIES[a], BARRICADES["straw_fence"]):
                combos.append((s, a))
    return combos


@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    observer: str
    barricade: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"drawing", "sticking"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"drawing", "sticking"}),
}

ACTIVITIES = {
    "drawing": Activity(
        id="drawing",
        gerund="drawing little circles",
        verb="draw little circles",
        mark_gerund="marking the paper as they drew",
        mess="ink",
        zone={"hands", "paper"},
        keyword="drawing",
    ),
    "sticking": Activity(
        id="sticking",
        gerund="sticking bright stars",
        verb="stick bright stars",
        mark_gerund="marking the page with stars",
        mess="glue",
        zone={"hands", "paper"},
        keyword="sticking",
    ),
}

BARRICADES = {
    "straw_fence": Barricade(
        id="straw_fence",
        label="straw fence",
        phrase="a little straw fence",
        uses="to keep the crayons in",
        clears="the floor",
        blocks={"drawing", "sticking"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ada", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Tom"]
OBSERVERS = ["mother", "father"]


def tell(setting: Setting, activity: Activity, child_name: str, observer_type: str, barricade: Barricade) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl" if child_name in GIRL_NAMES else "boy", label=child_name))
    observer = world.add(Entity(id="observer", kind="character", type=observer_type, label=f"the {observer_type}", role="observer"))
    mark = world.add(Entity(id="mark", label="page"))
    bc = world.add(Entity(id="barricade", label=barricade.label))
    child.attrs["mess_word"] = activity.mess
    child.attrs["activity"] = activity.id
    observer.attrs["barrier"] = barricade.id
    mark.meters["cleaned"] = 0.0
    bc.meters["built"] = 0.0
    bc.meters["opened"] = 0.0
    observer.memes["worry"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["confusion"] = 0.0

    world.say(f"{child.name} sat in {setting.place} and loved {activity.gerund}.")
    world.say(f"{child.name} was {activity.mark_gerund}, and the page seemed to sing.")
    world.para()
    observer.memes["worry"] += 1
    child.memes["confusion"] += 1
    world.say(f"The {observer_type} peeped in and thought the marks meant trouble.")
    world.say(f"So the {observer_type} brought out {barricade.phrase} {barricade.uses}.")
    propagate(world)
    world.para()
    child.memes["confusion"] += 1
    world.say(f"{child.name} blinked and pointed at the page.")
    world.say(f'"These are only {activity.keyword} marks," {child.name} said softly.')
    world.say(f'"I was {activity.gerund}, not making a mess on purpose."')
    observer.memes["worry"] = 0.0
    observer.memes["relief"] = 1.0
    world.get("barricade").meters["opened"] = 1.0
    mark.meters["cleaned"] = 1.0
    child.memes["joy"] += 1
    world.say(f"The {observer_type} smiled, opened the little barricade, and looked again.")
    world.say(f"Together they tidied the page, and the nursery felt calm and bright.")
    world.say(f"{child.name} kept {activity.gerund}, and the day ended with a happy ending.")

    world.facts.update(
        child=child,
        observer=observer,
        activity=activity,
        barricade=barricade,
        setting=setting,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "drawing": [("What does it mean to draw?", "To draw is to make shapes or lines on paper with a crayon, pencil, or marker.")],
    "sticking": [("What does it mean to stick something on a page?", "To stick something on a page means to use glue or paste so it stays there.")],
    "glue": [("What is glue for?", "Glue helps things stay together after you put them in the right place.")],
    "ink": [("What is ink?", "Ink is a colored liquid used for writing or drawing, and it can leave marks on paper.")],
    "barricade": [("What is a barricade?", "A barricade is something set up to block a way or keep a place safe.")],
}

KNOWLEDGE_ORDER = ["drawing", "sticking", "glue", "ink", "barricade"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about {f["child"].name}, who was {f["activity"].gerund}, and a grown-up who misunderstood the marks.',
        f'Tell a gentle story where a little one is {f["activity"].gerund}, a barricade gets built in worry, and the misunderstanding is cleared up kindly.',
        f'Write a short happy-ending story for small children that includes the word "{f["activity"].keyword}" and a little barricade.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, observer, activity = f["child"], f["observer"], f["activity"]
    return [
        QAItem(
            question=f"What was {child.name} doing in the nursery?",
            answer=f"{child.name} was {activity.gerund}, and the marks on the page were from that game.",
        ),
        QAItem(
            question=f"Why did the {observer.type} build a barricade?",
            answer=f"The {observer.type} thought the marks meant trouble, so {observer.pronoun('subject')} built a little barricade by the door before looking more closely.",
        ),
        QAItem(
            question=f"What did {child.name} say to clear up the misunderstanding?",
            answer=f"{child.name} explained that the marks were only from {activity.gerund}, not from being naughty.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the page tidied, the worry gone, and everyone feeling calm and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["activity"].keyword, world.facts["barricade"].id}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", activity="drawing", name="Mia", observer="mother", barricade="straw_fence"),
    StoryParams(setting="playroom", activity="sticking", name="Leo", observer="father", barricade="straw_fence"),
]


def explain_rejection(activity: Activity) -> str:
    return f"(No story: the world only supports a nursery-rhyme barricade story for {activity.keyword}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a mark-gerund misunderstanding and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--observer", choices=OBSERVERS)
    ap.add_argument("--barricade", choices=BARRICADES)
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
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("(Unknown activity.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        if args.activity:
            raise StoryError(explain_rejection(ACTIVITIES[args.activity]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    observer = args.observer or rng.choice(OBSERVERS)
    barricade = args.barricade or "straw_fence"
    return StoryParams(setting=setting, activity=activity, name=child_name, observer=observer, barricade=barricade)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.barricade not in BARRICADES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], params.name, params.observer, BARRICADES[params.barricade])
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


ASP_RULES = r"""
valid(S,A) :- setting(S), activity(A), blocks(barricade,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("blocks", "barricade", a.keyword))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate_story_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
