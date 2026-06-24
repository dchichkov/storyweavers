#!/usr/bin/env python3
"""
storyworlds/worlds/limp_acquire_conflict_bedtime_story.py
=========================================================

A small bedtime story world about a child who limps, wants to acquire one more
comfort, and meets a gentle conflict before sleep.

The world is intentionally tiny and self-contained:
- a child with a sore foot and growing sleepiness
- a cozy bedtime setting
- one cherished bedtime object to acquire
- a parent who notices the conflict and helps resolve it kindly

The story logic is state-driven: the child's ache, desire, and sleepiness shape
the narration; the ending proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectWish:
    id: str
    label: str
    phrase: str
    type: str
    requires: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    wish: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", cozy=True, affords={"book", "bear", "water"}),
    "nursery": Setting(place="the nursery", cozy=True, affords={"bear", "book"}),
    "hallway": Setting(place="the hallway", cozy=True, affords={"water", "book"}),
}

WISHES = {
    "book": ObjectWish(
        id="book",
        label="storybook",
        phrase="one more storybook",
        type="book",
        requires={"bedtime"},
    ),
    "bear": ObjectWish(
        id="bear",
        label="teddy bear",
        phrase="the soft teddy bear",
        type="bear",
        requires={"bedtime"},
    ),
    "water": ObjectWish(
        id="water",
        label="cup of water",
        phrase="a small cup of water",
        type="water",
        requires={"bedtime"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ella", "Maya", "Zoe", "Ivy"]
BOY_NAMES = ["Theo", "Noah", "Eli", "Finn", "Leo", "Max", "Sam"]
TRAITS = ["sleepy", "gentle", "curious", "quiet", "brave", "small"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_tire(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("ache", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("sleepiness", 0.0) < THRESHOLD:
            continue
        sig = ("tire", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["frustration"] = actor.memes.get("frustration", 0.0) + 1
        out.append(f"{actor.id} felt extra tired from the sore foot.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("desire", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("rest_want", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        out.append("__conflict__")
    return out


def _r_settle(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("conflict", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("comfort", 0.0) < THRESHOLD:
            continue
        sig = ("settle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = 0.0
        actor.memes["peace"] = actor.memes.get("peace", 0.0) + 1
        out.append(f"{actor.id} settled down a little.")
    return out


RULES = [Rule("tire", _r_tire), Rule("conflict", _r_conflict), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_wish(setting: Setting, wish: ObjectWish) -> bool:
    return wish.id in setting.affords


def predict(world: World, actor: Entity, wish: ObjectWish) -> dict:
    sim = world.copy()
    _request(sim, sim.get(actor.id), wish, narrate=False)
    return {
        "conflict": any(e.memes.get("conflict", 0.0) >= THRESHOLD for e in sim.characters()),
        "got": sim.facts.get("got_wish", False),
    }


def _request(world: World, child: Entity, wish: ObjectWish, narrate: bool = True) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    child.memes["rest_want"] = child.memes.get("rest_want", 0.0) + 1
    if narrate:
        world.say(f"{child.id} wanted to acquire {wish.phrase} before sleep.")
    propagate(world, narrate=narrate)


def tell(setting: Setting, wish: ObjectWish, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["sleepy", "gentle"]),
        meters={"ache": 1.0, "steps": 1.0},
        memes={"sleepiness": 1.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    treasure = world.add(Entity(
        id=wish.id,
        type=wish.type,
        label=wish.label,
        phrase=wish.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    hero.meters["ache"] += 1
    hero.memes["sleepiness"] += 1

    world.say(f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'gentle')} {hero.type} with a sore foot.")
    world.say(f"At bedtime, {hero.id} loved the cozy room and wanted to acquire {treasure.phrase}.")
    world.say(f"{hero.id}'s {parent_type if parent_type in {'mother', 'father'} else 'parent'} had already tucked the blankets in soft and warm.")

    world.para()
    world.say(f"One quiet evening, {hero.id} began to limp toward {setting.place}.")
    _request(world, hero, wish)
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1

    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        hero.memes["conflict"] = 1.0
        parent.memes["worry"] += 1
    world.say(f"{hero.id} still wanted {wish.phrase}, but {hero.pronoun('possessive')} {parent_type if parent_type in {'mother', 'father'} else 'parent'} worried that staying up would make the sore foot feel worse.")

    world.para()
    world.say(f"{hero.id} pouted on the edge of the bed.")
    world.say(f'Then {hero.pronoun("possessive")} {parent_type if parent_type in {"mother", "father"} else "parent"} smiled and said, "Let me help."')
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1
    world.say(f"{parent_type.capitalize()} reached for the {treasure.label} and placed {treasure.it()} right beside {hero.id}'s pillow.")
    world.say(f"That way, {hero.id} could keep {treasure.it()} close without getting up again.")
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.facts.update(hero=hero, parent=parent, wish=wish, treasure=treasure, resolved=True, place=setting.place)

    world.para()
    world.say(f"{hero.id} lay down at last, the limp gone from {hero.pronoun('possessive')} steps because {hero.pronoun('subject')} was already in bed.")
    world.say(f"The room grew still, and {hero.id} fell asleep with {wish.label} tucked close and {parent_type if parent_type in {'mother', 'father'} else 'the parent'} nearby.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, wish = f["hero"], f["wish"]
    return [
        f'Write a gentle bedtime story for a young child named {hero.id} who limps and wants to acquire {wish.phrase}.',
        f'Tell a cozy story where a {hero.type} named {hero.id} has a conflict at bedtime, but a parent helps {hero.pronoun("object")} rest.',
        f'Write a short bedtime story that includes the words "limp" and "acquire" and ends with a peaceful sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, wish = f["hero"], f["parent"], f["wish"]
    return [
        QAItem(
            question=f"Why was {hero.id} moving slowly in the story?",
            answer=f"{hero.id} was limping because {hero.pronoun('possessive')} foot was sore.",
        ),
        QAItem(
            question=f"What did {hero.id} want to acquire before sleep?",
            answer=f"{hero.id} wanted to acquire {wish.phrase} before bedtime.",
        ),
        QAItem(
            question=f"How did {hero.id}'s {parent.type} help with the conflict?",
            answer=f"{parent.type.capitalize()} helped by putting {wish.label} beside the pillow so {hero.id} could rest and keep it close.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {hero.id} was in bed, feeling peaceful, with the bedtime object close by and no more conflict.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does limp mean?",
            answer="To limp means to walk unevenly because something hurts or feels weak.",
        ),
        QAItem(
            question="What does acquire mean?",
            answer="To acquire something means to get it or come to have it.",
        ),
        QAItem(
            question="Why do people feel sleepy at bedtime?",
            answer="People feel sleepy at bedtime because their bodies are ready to rest after a long day.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", wish="book", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="nursery", wish="bear", name="Theo", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="hallway", wish="water", name="Lily", gender="girl", parent="mother", trait="curious"),
]


ASP_RULES = r"""
% A wish is valid in a setting when the room affords it.
valid(Place, Wish) :- affords(Place, Wish).

% A bedtime conflict exists when the child wants the wish and is tired enough.
conflict(Place, Wish) :- valid(Place, Wish), bedtime(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.cozy:
            lines.append(asp.fact("bedtime", sid))
        for w in sorted(s.affords):
            lines.append(asp.fact("affords", sid, w))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    python_set = {(place, wid) for place, s in SETTINGS.items() for wid in s.affords}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid combos ({len(clingo_set)}).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime story world with a limp and a gentle conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (place, wish)
        for place, setting in SETTINGS.items()
        for wish in setting.affords
        if (args.place is None or args.place == place)
        and (args.wish is None or args.wish == wish)
    ]
    if not combos:
        raise StoryError("(No valid bedtime combination matches the given options.)")
    place, wish = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in WISHES[wish].genders:
        raise StoryError("(That wish does not fit the chosen gender here.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, wish=wish, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], WISHES[params.wish], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible bedtime combos:\n")
        for place, wish in triples:
            print(f"  {place:8} {wish}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.wish} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
