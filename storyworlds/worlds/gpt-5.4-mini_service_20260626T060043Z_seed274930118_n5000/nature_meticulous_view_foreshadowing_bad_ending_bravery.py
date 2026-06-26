#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nature_meticulous_view_foreshadowing_bad_ending_bravery.py
==========================================================================================================

A small fable-style storyworld about nature, a meticulous watcher, a wide view,
foreshadowing, bravery, and a bad ending.

Seed image used to build the world:
---
A careful little animal loved the high view from the hill above the nature path.
It checked every stone, straightened every twig, and always noticed the sky first.
One day the clouds darkened, the birds went quiet, and the wind turned sharp.
The little watcher chose courage, even after the warnings, and hurried out to
help a friend before the storm arrived.
The help was brave, but the ending went badly: the path broke, the rain won,
and the wide view vanished behind gray water.

World logic:
---
    meticulous attention -> actor.memes["care"] += 1 ; actor.meters["order"] += 1
    foreshadowing signs  -> storm threat grows in the world state
    bravery under warning -> actor.memes["bravery"] += 1 ; actor.meters["risk"] += 1
    bad ending           -> if the storm arrives before shelter, the view is lost,
                            the path turns slick, and the hero ends sad but wiser

This file follows the Storyweavers contract: it is self-contained, uses the
shared results containers, includes an inline ASP twin, and can generate story,
QA, JSON, traces, and verification output.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        animalish = {"fox", "rabbit", "badger", "deer", "owl", "mouse", "hedgehog", "bird"}
        if self.type in animalish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    view: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk: str
    plural: bool = False


@dataclass
class Danger:
    id: str
    sign: str
    arrival: str
    mess: str
    outcome: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.storm = 0.0
        self.view_clear = True

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.storm = self.storm
        c.view_clear = self.view_clear
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_meticulous(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("care", 0.0) < THRESHOLD:
            continue
        sig = ("meticulous", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["order"] = actor.meters.get("order", 0.0) + 1.0
        out.append(f"{actor.id} straightened the path stones and checked each leaf.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("foreshadowing", 0.0) < THRESHOLD:
            continue
        sig = ("foreshadow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.storm += 1.0
        out.append("The clouds grew heavier, and even the birds went quiet.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("brave", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["risk"] = actor.meters.get("risk", 0.0) + 1.0
        out.append(f"{actor.id} chose to go on anyway, with a steady little heart.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if world.storm < THRESHOLD or actor.meters.get("risk", 0.0) < THRESHOLD:
            continue
        sig = ("bad_end", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.view_clear = False
        actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1.0
        out.append("Then the rain came hard and hid the wide view behind gray water.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("meticulous", _r_meticulous),
    Rule("foreshadow", _r_foreshadow),
    Rule("bravery", _r_bravery),
    Rule("bad_ending", _r_bad_ending),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_end(world: World, actor: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["bravery"] = 1.0
    propagate(sim, narrate=False)
    return {"bad": not sim.view_clear, "storm": sim.storm}


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} lived in {world.setting.place}, where the view from the hill "
        f"showed trees, stones, and far-off birds."
    )
    world.say(
        f"{hero.id} was meticulous. It liked every twig in place, every pebble "
        f"lined up, and every trail kept neat."
    )


def love_nature(world: World, hero: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1.0
    hero.memes["foreshadowing"] = hero.memes.get("foreshadowing", 0.0) + 1.0
    world.say(
        f"{hero.id} loved nature, and it spent long mornings watching the view "
        f"change with the light."
    )
    world.say(
        "But the wind had a cold edge, and the clouds gathered like a warning."
    )


def arrives(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(
        f"One day {hero.id} met {friend.id} beside the path and wanted to "
        f"{activity.verb} before the weather turned."
    )
    world.say(
        f"{hero.id} could already see the dark sky over the trees. "
        f"That was the first foreshadowing."
    )


def warns(world: World, hero: Entity) -> None:
    world.say(
        f"The little watcher paused and looked again at the sky. "
        f"It knew the morning was becoming unsafe."
    )


def brave_choice(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"Still, {hero.id} was brave. It decided to {activity.rush} and help "
        f"its friend right away."
    )


def ending(world: World, hero: Entity) -> None:
    if world.view_clear:
        world.say(
            f"In the end, the hill stayed bright and the view remained clear."
        )
    else:
        world.say(
            f"In the end, the hill was only rain, and the view was gone. "
            f"{hero.id} stood in the wet grass, smaller but wiser."
        )


SETTINGS = {
    "hill": Setting(place="the hill above the nature path", view="wide view", affords={"help"}),
    "ridge": Setting(place="the ridge by the trees", view="far view", affords={"help"}),
    "glade": Setting(place="the glade near the stream", view="soft view", affords={"help"}),
}

ACTIVITIES = {
    "help": Activity(
        id="help",
        verb="help its friend reach the path",
        gerund="helping a friend",
        rush="hurry to help its friend",
        keyword="help",
        tags={"nature", "view", "foreshadowing", "bravery"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a small lantern for the trail",
        type="lantern",
        risk="water",
    ),
    "map": Prize(
        label="map",
        phrase="a folded trail map",
        type="map",
        risk="rain",
    ),
}

DANGERS = {
    "storm": Danger(
        id="storm",
        sign="clouds",
        arrival="rain",
        mess="mud",
        outcome="the view disappeared",
        tags={"foreshadowing", "bad ending"},
    )
}

HERO_NAMES = ["Robin", "Moss", "Pip", "Fern", "Toby", "Willow", "Nim", "Sage"]
FRIEND_NAMES = ["Bramble", "Daisy", "Clover", "Juniper", "Poppy", "Thorn"]
TRAITS = ["meticulous", "gentle", "patient", "careful", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable about nature, a meticulous watcher, and a wide {world.setting.view}.',
        f"Tell a short story where {f['hero'].id} is {f['trait']} and brave, but the sky foreshadows trouble.",
        f"Write a child-friendly fable that ends with a bad ending after a brave choice on {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=(
                f"It is about {hero.id}, a little {f['trait']} watcher of nature "
                f"who lived near {world.setting.place}."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} love about the hill?",
            answer=(
                f"{hero.id} loved the {world.setting.view} and spent time noticing "
                f"tiny details in the leaves, stones, and sky."
            ),
        ),
        QAItem(
            question=f"What warned {hero.id} that trouble was coming?",
            answer=(
                f"The dark clouds, the quiet birds, and the sharp wind were foreshadowing "
                f"that a storm was on its way."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} keep going anyway?",
            answer=(
                f"{hero.id} wanted to help {friend.id}, and bravery made it hurry out "
                f"even though the weather looked bad."
            ),
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=(
                f"The rain came hard, the path turned wet, and the wide view disappeared. "
                f"It was a bad ending, and {hero.id} stood in the grass with a sad heart."
            ),
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer=(
                "Foreshadowing is when small clues hint that something important may happen later."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery means doing something hard or scary even when you are afraid."
            ),
        ),
        QAItem(
            question="What does nature mean?",
            answer=(
                "Nature is the world of trees, birds, rain, rocks, rivers, and other living and wild things."
            ),
        ),
    ]


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
    lines.append(f"  setting: {world.setting.place} / {world.setting.view}")
    lines.append(f"  storm: {world.storm}")
    lines.append(f"  view_clear: {world.view_clear}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Robin", friend_name: str = "Bramble",
         trait: str = "meticulous") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type="bird", traits=["little", trait, "careful"]
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type="rabbit", traits=["small", "hopeful"]
    ))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))

    world.say(
        f"Once, in the quiet land of nature, {hero.id} lived by {setting.place}."
    )
    intro(world, hero)
    love_nature(world, hero)
    world.para()
    arrives(world, hero, friend, activity)
    warns(world, hero)
    brave_choice(world, hero, activity)
    propagate(world, narrate=True)

    # The prize is only symbolic here; the bad ending comes from the storm.
    if world.storm >= THRESHOLD:
        prize.meters["wet"] = 1.0
        world.facts["bad"] = True
        world.say(f"The trail map grew soggy in the rain, and the careful plan was lost.")
    else:
        world.facts["bad"] = False
    world.para()
    ending(world, hero)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        setting=setting,
        activity=activity,
        prize_cfg=prize_cfg,
        trait=trait,
    )
    return world


KNOWLEDGE_ORDER = ["nature", "view", "foreshadowing", "bravery", "bad ending"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risk", pid, p.risk))
    for did, d in DANGERS.items():
        lines.append(asp.fact("danger", did))
        for t in sorted(d.tags):
            lines.append(asp.fact("tagged_danger", did, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, A, P) :- affords(Place, A), setting(Place), activity(A), prize(P).
story(Place, A, P) :- valid(Place, A, P).
"""


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
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(place: str, activity: str, prize: str) -> str:
    return f"(No story: {place}, {activity}, and {prize} do not form a valid nature fable here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world of nature, meticulous care, foreshadowing, bravery, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or "meticulous"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.friend, params.trait)
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


CURATED = [
    StoryParams(place="hill", activity="help", prize="map", name="Robin", friend="Bramble", trait="meticulous"),
    StoryParams(place="ridge", activity="help", prize="lantern", name="Moss", friend="Clover", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for row in triples:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
