#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distraction_barrette_flour_misunderstanding_pirate_tale.py
==========================================================================================

A standalone story world for a tiny pirate-tale misunderstanding:
a child pirate gets distracted by a shiny barrette, a flour mishap makes a
mess, and a calm grown-up clears up the misunderstanding and steers everyone
back to safe pretend play.

The story keeps a classical TinyStories shape:
premise -> distraction -> misunderstanding -> repair -> ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/distraction_barrette_flour_misunderstanding_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/distraction_barrette_flour_misunderstanding_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/distraction_barrette_flour_misunderstanding_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "confusion": 0.0, "relief": 0.0}

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
class Theme:
    id: str
    scene: str
    ship: str
    goal: str
    dark_spot: str
    send_off: str


@dataclass
class Item:
    id: str
    label: str
    kind: str
    risky: bool = False
    distracting: bool = False
    harmless: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    if world.get("table").meters["flour"] >= THRESHOLD and ("mess", "table") not in world.fired:
        world.fired.add(("mess", "table"))
        world.get("table").meters["mess"] += 1
        out.append("__mess__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("table").meters["mess"] >= THRESHOLD and ("worry", "parent") not in world.fired:
        world.fired.add(("worry", "parent"))
        world.get("Parent").memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("worry", "social", _r_worry)]


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


def predict_mess(world: World) -> bool:
    sim = world.copy()
    simulate_flour_spill(sim, narrate=False)
    return sim.get("table").meters["mess"] >= THRESHOLD


def simulate_flour_spill(world: World, narrate: bool = True) -> None:
    world.get("cup").meters["flour"] += 1
    world.get("table").meters["flour"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon, {hero.id} and {friend.id} turned the deck into "
        f"{theme.scene}. {theme.ship}"
    )
    world.say(
        f"{hero.id} shouted, 'We're brave pirates looking for {theme.goal}!'"
    )


def distraction(world: World, hero: Entity, barrette: Item) -> None:
    hero.memes["joy"] += 1
    hero.memes["focus"] -= 1
    world.say(
        f"Then a tiny {barrette.label} on the table gave {hero.id} a bright "
        f"distraction. {hero.id} reached for it because it glittered like treasure."
    )


def misunderstanding(world: World, friend: Entity, hero: Entity, flour: Item) -> None:
    friend.memes["confusion"] += 1
    world.say(
        f"{friend.id} peered at the bowl of {flour.label} and gasped. "
        f'"Did somebody spill the captain\'s storm powder?" {friend.id} asked.'
    )
    world.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head. "
        f'"No, it is only {flour.label} for pretend clouds," {hero.id} said, '
        f'but the two pirates had not noticed the mess yet.'
    )


def spill(world: World, hero: Entity, flour: Item) -> None:
    hero.memes["surprise"] += 1
    simulate_flour_spill(world)
    world.say(
        f"While everyone was looking at the {flour.label}, the cup tipped over."
    )
    world.say(
        f"White {flour.label} puffed across the table like sea foam, and the deck "
        f"turned dusty and silly."
    )


def repair(world: World, parent: Entity, hero: Entity, friend: Entity, barrette: Item, flour: Item) -> None:
    parent.memes["worry"] += 0.0
    world.say(
        f"{parent.label_word.capitalize()} came over right away and smiled. "
        f'"This is not a storm, and nobody is in trouble," {parent.id} said. '
        f'"It was just a misunderstanding."'
    )
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"Together they wiped the table clean, brushed the flour away, and put "
        f"the {barrette.label} back where it belonged."
    )
    world.say(
        f"{hero.id} learned to ask first before touching shiny things, and "
        f"{friend.id} learned to check before guessing about the mess."
    )


def ending(world: World, theme: Theme, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the end, the little pirates sailed on with clean hands, a tidy deck, "
        f"and a safe treasure map, ready for {theme.send_off}."
    )


def tell(theme: Theme, barrette: Item, flour: Item, hero_name: str, friend_name: str,
         hero_gender: str, friend_gender: str, parent_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    world.add(Entity(id="table", label="table"))
    world.add(Entity(id="cup", label="cup"))
    world.add(Entity(id="barrette", label=barrette.label, attrs={"kind": barrette.kind}))
    world.add(Entity(id="flour", label=flour.label, attrs={"kind": flour.kind}))

    setup(world, hero, friend, theme)
    world.para()
    distraction(world, hero, barrette)
    misunderstanding(world, friend, hero, flour)
    world.para()
    spill(world, hero, flour)
    repair(world, parent, hero, friend, barrette, flour)
    world.para()
    ending(world, theme, hero, friend)

    world.facts.update(
        hero=hero, friend=friend, parent=parent, theme=theme,
        barrette=barrette, flour=flour, spilled=True,
        misunderstanding=True, resolved=True,
    )
    return world


THEMES = {
    "pirate_tale": Theme(
        "pirate_tale",
        "a pretend pirate deck",
        "The sofa was the captain's ship, a spoon became a telescope, and a paper map led to the hidden cove.",
        "the hidden cove",
        "the bright corner by the lantern",
        "set sail into the cove",
    ),
}

ITEMS = {
    "barrette": Item("barrette", "barrette", "shiny", risky=False, distracting=True, tags={"barrette", "distraction"}),
    "flour": Item("flour", "flour", "kitchen", risky=False, harmless=True, tags={"flour"}),
    "powder": Item("powder", "flour", "kitchen", risky=False, harmless=True, tags={"flour"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn"]


@dataclass
class StoryParams:
    theme: str
    barrette: str
    flour: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("pirate_tale", "barrette", "flour")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale misunderstanding with a barrette and flour.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--barrette", choices=["barrette"])
    ap.add_argument("--flour", choices=["flour"])
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
    if args.theme and args.theme not in THEMES:
        raise StoryError("Unknown theme.")
    theme = args.theme or "pirate_tale"
    barrette = args.barrette or "barrette"
    flour = args.flour or "flour"
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero])
    parent_gender = rng.choice(["mother", "father"])
    return StoryParams(theme, barrette, flour, hero, hero_gender, friend, friend_gender, parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-tale story for a small child that includes the words "distraction", "barrette", and "flour".',
        f"Tell a gentle story where {f['hero'].id} gets distracted by a shiny barrette, there is a misunderstanding about flour, and a grown-up helps everyone laugh it off.",
        "Write a short misunderstanding story on a pretend pirate deck that ends with the mess cleaned up and the friends sailing on.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What distracted {hero.id}?",
            answer=f"A shiny barrette distracted {hero.id}. It glittered like treasure, so {hero.id} reached for it instead of watching the flour."
        ),
        QAItem(
            question="What was misunderstood?",
            answer=f"{friend.id} thought the flour might be storm powder, but it was only flour for pretend play. The grown-up cleared up the misunderstanding."
        ),
        QAItem(
            question="How did the story end?",
            answer="The flour was cleaned up, the barrette was put back, and the pirate game continued with everyone calm and happy."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barrette?",
            answer="A barrette is a small hair clip that holds hair back or decorates a hairstyle."
        ),
        QAItem(
            question="What is flour?",
            answer="Flour is a powder made from ground grains. People use it to bake bread, cakes, and other food."
        ),
        QAItem(
            question="What should you do if you are confused about a mess?",
            answer="You should ask a grown-up or ask before guessing. That helps clear up misunderstandings and keeps play safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
item(barrette).
item(flour).
theme(pirate_tale).
valid(theme, barrette, flour).
misunderstanding_happens :- item(barrette), item(flour).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("item", "barrette"),
        asp.fact("item", "flour"),
        asp.fact("theme", "pirate_tale"),
        asp.fact("valid", "theme", "barrette", "flour"),
    ])


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python valid-combos match.")
    else:
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], ITEMS[params.barrette], ITEMS[params.flour],
                 params.hero, params.friend, params.hero_gender, params.friend_gender,
                 params.parent_gender)
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


CURATED = [StoryParams("pirate_tale", "barrette", "flour", "Lily", "girl", "Tom", "boy", "mother")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:", asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
