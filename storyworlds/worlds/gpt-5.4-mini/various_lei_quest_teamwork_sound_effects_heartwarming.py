#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py
==========================================================================================

A standalone storyworld for a small heartwarming quest about children making a
lei together. The domain is built around:

- a quest to find "various" flowers and ribbons,
- teamwork between two children and a grown-up helper,
- playful sound effects during the search and crafting,
- a warm ending where the finished lei becomes a gift.

The world is intentionally small and classical: physical meters track gathered
materials, finished craft, and fatigue; emotional memes track hope, teamwork,
joy, and pride. Stories are driven by state changes rather than a frozen text
template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4-mini/various_lei_quest_teamwork_sound_effects_heartwarming.py --verify
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
TEAMWORK_GAIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    sounds: list[str]
    flowers: list[str]
    has_path: bool = True
    has_table: bool = True


@dataclass
class Item:
    id: str
    label: str
    kind: str
    scent: str
    sound: str
    color: str
    meter_gain: float = 1.0


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.place: Optional[Place] = None

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
        clone.place = copy.deepcopy(self.place)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters["helped"] >= THRESHOLD and e.meters["shared"] >= THRESHOLD:
            sig = ("teamwork", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["teamwork"] += TEAMWORK_GAIN
            out.append("__teamwork__")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("basket_full") and world.facts.get("strung"):
        sig = ("finish",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["joy"] += 1
            out.append("__finish__")
    return out


CAUSAL_RULES = [Rule("teamwork", "social", _r_teamwork), Rule("finish", "social", _r_finish)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_path(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} began a small quest in {place.label}. "
        f"They wanted to make a lei for someone they loved."
    )
    world.say(
        f"The garden answered with small sounds all around them: {', '.join(place.sounds[:2])}. "
        f"The air felt sweet, and the search could begin."
    )


def split_tasks(world: World, hero: Entity, helper: Entity) -> None:
    hero.meters["hope"] += 1
    helper.meters["hope"] += 1
    hero.meters["helped"] += 1
    helper.meters["shared"] += 1
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f'{hero.id} held up a little basket. "{helper.id}, you find the bright flowers, and I will hold the string," '
        f"{hero.id} said."
    )
    world.say(
        f'"Deal," {helper.id} said, and together they went from patch to patch, listening for every tiny clue.'
    )
    propagate(world, narrate=False)


def gather(world: World, picker: Entity, item: Item) -> None:
    picker.meters["basket"] += item.meter_gain
    picker.meters["helped"] += 0.5
    picker.memes["pride"] += 0.5
    item_meter = f"{item.color} {item.kind}"
    world.say(
        f"{picker.id} found a {item_meter} with a soft {item.sound} sound. "
        f'"{item.label}!" {picker.id} cheered.'
    )


def various_find(world: World, hero: Entity, helper: Entity, items: list[Item]) -> None:
    world.say(
        f"They needed various pieces for the lei, not just one kind. A few petals, a ribbon, and one shiny shell would make it feel special."
    )
    gather(world, hero, items[0])
    world.say("Swish, swish, went the leaves as they looked under the bushes.")
    gather(world, helper, items[1])
    world.say("Tap-tap, went their shoes on the path as they hurried back together.")
    gather(world, hero, items[2])
    world.facts["basket_full"] = hero.meters["basket"] + helper.meters["basket"] >= 3
    hero.meters["shared"] += 1
    helper.meters["helped"] += 1


def craft(world: World, hero: Entity, helper: Entity, parent: Entity, lei: Item) -> None:
    world.facts["strung"] = True
    hero.meters["finished"] += 1
    helper.meters["finished"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'Back at the table, {parent.label_word} helped them thread the pieces one by one. '
        f'Slip, slide, slip went the string as the lei grew longer.'
    )
    world.say(
        f'At last, the {lei.label} sat in a bright circle, smelling like flowers and sunshine.'
    )


def gift(world: World, hero: Entity, helper: Entity, parent: Entity, lei: Item) -> None:
    for e in (hero, helper, parent):
        if e.kind == "character":
            e.memes["love"] += 1
    world.say(
        f"They carried the lei to {parent.id}'s side and placed it gently around {parent.pronoun("object")}'s neck."
    )
    world.say(
        f'"Oh," {parent.id} whispered, smiling wide. "You made this together?"'
    )
    world.say(
        f'"Yes!" {hero.id} and {helper.id} said at once. The flowers gave off a soft sweet smell, and everyone felt warm inside.'
    )
    world.say(
        f"The little lei was more than a gift now. It was proof that two friends, a patient grown-up, and many tiny hands could make something beautiful together."
    )


def tell(place: Place, items: list[Item], hero_name: str = "Mina", helper_name: str = "Noah",
         hero_gender: str = "girl", helper_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    world.place = place
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="quester"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity("Mom", kind="character", type=parent_type, role="guide", label="their grown-up"))
    lei = world.add(Entity("lei", type="thing", label="lei", attrs={"kind": "gift"}))

    quest_path(world, hero, helper, place)
    world.para()
    split_tasks(world, hero, helper)
    various_find(world, hero, helper, items)
    world.para()
    craft(world, hero, helper, parent, lei)
    world.para()
    gift(world, hero, helper, parent, lei)

    world.facts.update(hero=hero, helper=helper, parent=parent, place=place, items=items, lei=lei)
    return world


PLACES = {
    "garden": Place("garden", "the garden", ["rustle", "hum", "tap"], ["plumeria", "jasmine", "hibiscus"]),
    "backyard": Place("backyard", "the backyard", ["chirp", "swish", "ding"], ["daisy", "mint", "small fern"]),
    "market": Place("market", "the little market stall", ["clink", "brrr", "whoosh"], ["orchid", "marigold", "rose"]),
}

ITEMS = {
    "flowers": Item("flowers", "fresh flowers", "flowers", "sweet", "rustle", "pink", 1.0),
    "ribbon": Item("ribbon", "a ribbon", "ribbon", "clean fabric", "swish", "yellow", 1.0),
    "shell": Item("shell", "a shiny shell", "shell", "salt air", "clink", "white", 1.0),
    "leaf": Item("leaf", "a bright leaf", "leaf", "green stem", "rustle", "green", 1.0),
    "bead": Item("bead", "a blue bead", "bead", "smooth glass", "click", "blue", 1.0),
}

CURATED = [
    ("garden", ["flowers", "ribbon", "shell"]),
    ("backyard", ["leaf", "flowers", "bead"]),
    ("market", ["flowers", "shell", "ribbon"]),
]

GIRL_NAMES = ["Mina", "Lani", "Lea", "Mia", "Noa", "Ava"]
BOY_NAMES = ["Noah", "Kai", "Leo", "Eli", "Owen", "Ben"]
TRAITS = ["gentle", "patient", "brave", "kind", "careful", "cheerful"]


@dataclass
class StoryParams:
    place: str
    item1: str
    item2: str
    item3: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, b, c) for p in PLACES for a, b, c in [(x[0], x[1], x[2]) for x in CURATED if x[0] == p] or []]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming quest world about making a lei together.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item1", choices=ITEMS)
    ap.add_argument("--item2", choices=ITEMS)
    ap.add_argument("--item3", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    choices = CURATED[0][1]
    item_ids = [args.item1 or choices[0], args.item2 or choices[1], args.item3 or choices[2]]
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, *item_ids, hero, hero_gender, helper, helper_gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    return [
        f'Write a heartwarming quest story that uses the word "various" and includes a lei being made in {place}.',
        f"Tell a story where {f['hero'].id} and {f['helper'].id} work together to find various pieces for a lei and give it as a gift.",
        f'Write a gentle teamwork story with sound effects like "swish" and "tap" that ends with a lei.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent, place = f["hero"], f["helper"], f["parent"], f["place"]
    return [
        ("What were the children trying to make?",
         f"They were trying to make a lei together. They wanted it to be pretty enough to give as a loving gift."),
        ("Why did they need various pieces?",
         f"They did not want just one flower. They needed various pieces so the lei would look full, colorful, and special."),
        (f"Who helped them finish the lei?",
         f"{parent.id} helped them thread the pieces at the table. That teamwork helped turn the gathered parts into one finished circle."),
        ("How did the story end?",
         f"It ended with the finished lei being placed around {parent.id}'s neck. Everyone felt warm, happy, and proud of making something together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a lei?",
         "A lei is a necklace made from flowers, leaves, or other pretty pieces. People often give it as a welcoming or loving gift."),
        ("Why do stories use sound effects?",
         "Sound effects make a story feel lively and fun. They help you imagine what the characters hear while they act."),
        ("What does teamwork mean?",
         "Teamwork means people help each other and share the work. When a team works well, they can finish something together more easily."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
teamwork(E) :- helped(E), shared(E).
finished :- basket_full, strung.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    items = [ITEMS[params.item1], ITEMS[params.item2], ITEMS[params.item3]]
    world = tell(PLACES[params.place], items, params.hero, params.helper, params.hero_gender, params.helper_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show teamwork/1.\n#show finished/0."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for place, ids in CURATED:
            params = StoryParams(place, *ids, "Mina", "girl", "Noah", "boy", "mother", "kind")
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
