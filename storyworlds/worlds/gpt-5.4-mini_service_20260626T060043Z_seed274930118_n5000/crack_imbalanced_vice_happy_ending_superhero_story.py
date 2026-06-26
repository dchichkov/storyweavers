#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/crack_imbalanced_vice_happy_ending_superhero_story.py
==========================================================================================================

A small superhero story world with a happy ending.

Seed words: crack, imbalanced, vice
Style: Superhero Story
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cracked": 0.0, "imbalanced": 0.0, "safe": 0.0, "repaired": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    danger: str
    issue: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.type in {"hero", "girl", "boy"}]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))


def act_makes_worse(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.heroes():
        for ch in CHALLENGES.values():
            if hero.meters[ch.id] < THRESHOLD:
                continue
            if ch.id not in world.setting.affords:
                continue
            for item in world.worn_items(hero):
                if item.protective:
                    continue
                if item.owner != hero.id:
                    continue
                if item.meters["repaired"] >= THRESHOLD:
                    continue
                if item.id == "city_arch":
                    continue
                if item.meters["cracked"] >= THRESHOLD or item.meters["imbalanced"] >= THRESHOLD:
                    continue
                if item.kind != "object":
                    continue
                sig = ("worsen", hero.id, item.id, ch.id)
                if sig in world.fired:
                    continue
                if not (world.zone & ch.zone):
                    continue
                world.fired.add(sig)
                item.meters["cracked"] += 1
                item.meters["imbalanced"] += 1
                hero.memes["fear"] += 1
                out.append(f"{hero.pronoun('possessive').capitalize()} {item.label_word} wobbled and took a crack.")
    return out


def act_repair(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["cracked"] < THRESHOLD and ent.meters["imbalanced"] < THRESHOLD:
            continue
        sig = ("repair", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["cracked"] = 0.0
        ent.meters["imbalanced"] = 0.0
        ent.meters["repaired"] += 1
        ent.meters["safe"] += 1
        out.append(f"It was steady again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for func in (act_makes_worse, act_repair):
            got = func(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def can_fix(ch: Challenge, gear: Gear, item: Entity) -> bool:
    return ch.id in gear.guards and bool(ch.zone & gear.covers) and item.kind == "object"


def predict(world: World, hero: Entity, ch: Challenge, item_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[ch.id] += 1
    sim.zone = set(ch.zone)
    propagate(sim, narrate=False)
    item = sim.entities[item_id]
    return {
        "cracked": item.meters["cracked"] >= THRESHOLD,
        "imbalanced": item.meters["imbalanced"] >= THRESHOLD,
    }


SETTINGS = {
    "tower": Setting("the clock tower", {"crack"}),
    "bridge": Setting("the sky bridge", {"imbalance", "crack"}),
    "hangar": Setting("the rescue hangar", {"vice"}),
}

CHALLENGES = {
    "crack": Challenge(
        id="crack",
        verb="cross the crack",
        gerund="crossing the crack",
        danger="the crack could spread",
        issue="a crack in the path",
        zone={"feet"},
        keyword="crack",
        tags={"crack"},
    ),
    "imbalance": Challenge(
        id="imbalance",
        verb="step onto the wobbly span",
        gerund="balancing on the wobbly span",
        danger="the whole span could tip",
        issue="an imbalanced beam",
        zone={"feet", "torso"},
        keyword="imbalanced",
        tags={"imbalanced"},
    ),
    "vice": Challenge(
        id="vice",
        verb="pry the broken clamp loose",
        gerund="working with the vice clamp",
        danger="the clamp could pinch the wrong way",
        issue="a stubborn vice at the door",
        zone={"hands"},
        keyword="vice",
        tags={"vice"},
    ),
}

GEAR = [
    Gear("brace", "a steel brace", {"crack"}, {"feet", "torso"}, "bring a steel brace", "brought the steel brace"),
    Gear("stabilizer", "a stabilizer belt", {"imbalance"}, {"feet", "torso"}, "put on a stabilizer belt", "put on the stabilizer belt"),
    Gear("gloves", "strong gloves", {"vice"}, {"hands"}, "wear strong gloves", "wore the strong gloves"),
]

ITEMS = {
    "beam": ("beam", "a long city beam", "object"),
    "bridge": ("bridge", "the bridge", "object"),
    "clamp": ("clamp", "the rescue vice clamp", "object"),
}

HERO_NAMES = ["Nova", "Spark", "Mira", "Jax", "Ruby", "Leo"]
HELPER_NAMES = ["Pip", "Ivy", "Kai", "Bea"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    item: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            for item in ITEMS:
                combos.append((place, ch_id, item))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about crack, imbalanced, and vice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (args.challenge is None or c[1] == args.challenge)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, challenge, item = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, challenge=challenge, item=item, hero_name=hero_name, helper_name=helper_name)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type="hero", label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="hero", label=params.helper_name))
    item_id, item_label, kind = ITEMS[params.item]
    item = world.add(Entity(id=item_id, kind=kind, type="object", label=item_label, owner=hero.id))
    item.worn_by = hero.id
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.facts.update(hero=hero, helper=helper, item=item, challenge=CHALLENGES[params.challenge], setting=SETTINGS[params.place])
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    ch: Challenge = f["challenge"]
    place: Setting = f["setting"]

    world.say(f"{hero.label_word} was a brave superhero who watched over {place.place}.")
    world.say(f"One day, {hero.label_word} saw {item.phrase} near {place.place}.")

    world.para()
    world.say(f"The trouble was a {ch.issue}.")
    world.say(f"{hero.label_word} wanted to {ch.verb}, but {ch.danger}.")
    hero.meters[ch.id] += 1
    world.zone = set(ch.zone)

    if ch.id == "vice":
        world.say(f"A sneaky vice had pinched the clamp too tight.")
    elif ch.id == "crack":
        world.say(f"The crack made the path look thin and nervous.")
    else:
        world.say(f"The bridge leaned to one side and felt imbalanced.")
    propagate(world)

    world.para()
    gear = next(g for g in GEAR if can_fix(ch, g, item))
    if predict(world, hero, ch, item.id)["cracked"] or predict(world, hero, ch, item.id)["imbalanced"]:
        world.say(f"{helper.label_word} hurried over and held out {gear.label}.")
        world.say(f'"Let\'s {gear.prep}," {helper.label_word} said.')
        item.meters["cracked"] = 0.0
        item.meters["imbalanced"] = 0.0
        item.meters["safe"] = 1.0
        hero.memes["fear"] += 1
        hero.memes["relief"] += 1
        world.say(f"{hero.label_word} nodded, took a breath, and tried again.')
        world.say(f"This time, {hero.label_word} could move safely, and the city stayed calm.")
        world.say(f"At the end, {item.label_word} was steady, and the superhero team smiled at the bright sky.")
    else:
        world.say(f"{hero.label_word} found a safer way before any harm could spread.")
        world.say(f"That kept {item.label_word} safe, and the day stayed bright.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story about {f['hero'].label_word} and the {f['challenge'].keyword} problem.",
        f"Tell a happy-ending story where {f['hero'].label_word} fixes {f['item'].label_word} with help from a friend.",
        f"Write a child-friendly story that includes the words crack, imbalanced, and vice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    ch: Challenge = f["challenge"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.label_word}.",
        ),
        QAItem(
            question=f"What problem did {hero.label_word} face?",
            answer=f"{hero.label_word} faced {ch.issue}.",
        ),
        QAItem(
            question=f"Who helped {hero.label_word} in the end?",
            answer=f"{helper.label_word} helped by bringing the right gear.",
        ),
        QAItem(
            question=f"What happened to {item.label_word} by the end?",
            answer=f"{item.label_word} was steady and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a brace do?",
            answer="A brace helps hold something steady so it does not crack or bend as easily.",
        ),
        QAItem(
            question="What do strong gloves do?",
            answer="Strong gloves protect hands and help someone grip a tool safely.",
        ),
        QAItem(
            question="What does imbalanced mean?",
            answer="Imbalanced means not steady or not even, so something may lean or tip.",
        ),
        QAItem(
            question="What is a vice?",
            answer="A vice is a tool that can hold something tightly in place while it is fixed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(tower).
setting(bridge).
setting(hangar).

challenge(crack).
challenge(imbalance).
challenge(vice).

item(beam).
item(bridge).
item(clamp).

affords(tower, crack).
affords(bridge, crack).
affords(bridge, imbalance).
affords(hangar, vice).

gear(brace).
gear(stabilizer).
gear(gloves).

guards(brace, crack).
guards(stabilizer, imbalance).
guards(gloves, vice).

covers(brace, feet).
covers(brace, torso).
covers(stabilizer, feet).
covers(stabilizer, torso).
covers(gloves, hands).

valid(P, C, I) :- affords(P, C), challenge(C), item(I), gear(G), guards(G, C), covers(G, R), worn_on(I, R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for i, (_, _, _) in ITEMS.items():
        lines.append(asp.fact("item", i))
    for p, s in SETTINGS.items():
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", p, c))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    for i, (_, _, _) in ITEMS.items():
        lines.append(asp.fact("worn_on", i, "torso"))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def valid_story_set() -> set[tuple]:
    return set(valid_combos())


def asp_valid_story_set() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = valid_story_set()
    asp_set = asp_valid_story_set()
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams("bridge", "imbalance", "bridge", "Nova", "Pip"),
    StoryParams("tower", "crack", "beam", "Spark", "Ivy"),
    StoryParams("hangar", "vice", "clamp", "Mira", "Kai"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
