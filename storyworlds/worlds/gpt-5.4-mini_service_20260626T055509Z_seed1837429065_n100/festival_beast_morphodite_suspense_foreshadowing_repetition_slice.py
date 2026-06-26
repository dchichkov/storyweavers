#!/usr/bin/env python3
"""
storyworlds/worlds/festival_beast_morphodite_suspense_foreshadowing_repetition_slice.py
======================================================================================

A small slice-of-life story world for a festival day with a beast, a morphodite,
and a gentle suspense turn that resolves through practical care.

The seed image is simple:
- a town festival is being set up,
- someone notices signs of a beast,
- a morphodite helper keeps changing shape to help,
- and the worry turns out smaller, kinder, and more ordinary than it first seemed.

The story uses:
- suspense: a small unknown presence near the festival grounds,
- foreshadowing: clues that point to the truth before it is named,
- repetition: a few repeated phrases and actions that make the scene feel lived-in,
- slice of life: ordinary preparations, small social reactions, and a calm ending.

The world is intentionally compact and constraint-checked.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    keyword: str
    suspense_clue: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    protects: set[str] = field(default_factory=set)


@dataclass
class MorphoditeForm:
    id: str
    label: str
    purpose: str
    phrase: str


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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _deepcopy_entities(entities: dict[str, Entity]) -> dict[str, Entity]:
    return {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes), props=dict(v.props))
            for k, v in entities.items()}


dataclasses.deepcopy = _deepcopy_entities  # type: ignore[attr-defined]


@dataclass
class StoryParams:
    place: str
    event: str
    prop: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "town_square": Setting(
        place="the town square",
        detail="The square smelled like sweet buns and fresh straw, and banners fluttered above the booths.",
        affords={"festival"},
    ),
    "fair_green": Setting(
        place="the fair green",
        detail="The fair green was wide and soft, with a ribbon arch and a small stage at one end.",
        affords={"festival"},
    ),
    "market_lane": Setting(
        place="the market lane",
        detail="The market lane was lined with tables, baskets, and bright cloth canopies.",
        affords={"festival"},
    ),
}

EVENTS = {
    "festival": Event(
        id="festival",
        verb="help at the festival",
        gerund="helping at the festival",
        keyword="festival",
        suspense_clue="a soft thump near the lantern tent",
        sound="a low rustle",
        tags={"festival", "lantern", "crowd"},
    ),
}

PROPS = {
    "lantern": Prop(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with blue stars",
        region="hands",
        genders={"girl", "boy"},
    ),
    "tray": Prop(
        id="tray",
        label="tray of buns",
        phrase="a tray of warm buns",
        region="arms",
        plural=False,
    ),
    "banner": Prop(
        id="banner",
        label="festival banner",
        phrase="a long striped banner",
        region="hands",
        plural=True,
    ),
}

MORPHODITE_FORMS = {
    "cart": MorphoditeForm(
        id="cart",
        label="cart shape",
        purpose="carry supplies without wobbling",
        phrase="a little cart shape with neat wooden sides",
    ),
    "lamp": MorphoditeForm(
        id="lamp",
        label="lamp shape",
        purpose="shine light near dark corners",
        phrase="a bright lamp shape that glowed softly",
    ),
    "bird": MorphoditeForm(
        id="bird",
        label="bird shape",
        purpose="peek over stalls and spot small things",
        phrase="a quick bird shape with alert eyes",
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Tia", "Nora", "Pia", "Sana"],
    "boy": ["Eli", "Oren", "Milo", "Theo", "Rafi", "Jonah"],
}

TRAITS = ["careful", "curious", "patient", "cheerful", "steady", "quiet"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("Something moved behind the lantern tent.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("focus", 0) < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("Again and again, the little bell on the stall rang as helpers passed by.")
    return out


RULES = [Rule("suspense", _r_suspense), Rule("repetition", _r_repetition)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event_id in setting.affords:
            for prop_id in PROPS:
                combos.append((place, event_id, prop_id))
    return combos


def _reasonableness_gate(place: str, event: str, prop: str) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if event not in EVENTS:
        raise StoryError("Unknown event.")
    if prop not in PROPS:
        raise StoryError("Unknown prop.")
    if event not in SETTINGS[place].affords:
        raise StoryError("That event does not fit this setting.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    event = EVENTS[params.event]
    prop_cfg = PROPS[params.prop]
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"calm": 1.0},
        memes={"focus": 0.0, "worry": 0.0, "warmth": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="morphodite",
        label="the morphodite",
        role="helper",
        memes={"pride": 0.0, "helpfulness": 1.0},
    ))
    beast = world.add(Entity(
        id="beast",
        kind="character",
        type="beast",
        label="the beast",
        role="gentle mystery",
        meters={"size": 1.0},
        memes={"shyness": 1.0, "hunger": 1.0, "calm": 0.0},
    ))
    prop = world.add(Entity(
        id="prop",
        type=prop_cfg.id,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        plural=prop_cfg.plural,
        owner=hero.id,
        props={"region": prop_cfg.region},
    ))

    world.facts.update(hero=hero, companion=companion, beast=beast, prop=prop, event=event, setting=setting)
    return world


def introduce(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    setting = world.setting
    world.say(
        f"{hero.label} was a {world.facts['trait']} little {hero.type} who loved the festival at {setting.place}."
    )
    world.say(
        f"{companion.label} was a morphodite, which meant it could change shape to help with almost any job."
    )


def setup(world: World) -> None:
    hero = world.get("hero")
    prop = world.get("prop")
    event = world.facts["event"]
    hero.memes["focus"] += 1
    world.say(
        f"That morning, {hero.label} carried {prop.phrase} to the festival stalls and counted the steps from one booth to the next."
    )
    world.say(
        f"{hero.label} liked the little routines: tie the ribbon, check the bun tray, smile at the neighbors, tie the ribbon again."
    )
    world.say(
        f"{event.suspense_clue} was the first odd thing {hero.label} noticed."
    )
    world.say(
        f"The clue stayed small, but it made the air feel quiet for a moment."
    )


def suspense_turn(world: World) -> None:
    hero = world.get("hero")
    beast = world.get("beast")
    companion = world.get("companion")
    event = world.facts["event"]
    hero.memes["worry"] += 1
    world.say(
        f"{hero.label} paused. There was {event.sound}, then another soft thump, and then silence."
    )
    world.say(
        f"Again and again, {hero.label} looked toward the lantern tent, and again and again the path looked empty."
    )
    propagate(world)
    beast.memes["shyness"] += 1
    world.say(
        f"{companion.label} slipped into a bird shape to peek over the booths."
    )
    world.say(
        f"It saw a beast crouched beside the straw bales, trying very hard not to bump the hanging bells."
    )


def reveal(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    beast = world.get("beast")
    prop = world.get("prop")
    hero.memes["worry"] = 0.0
    hero.memes["warmth"] += 1
    beast.memes["calm"] += 1
    world.say(
        f"The beast was not there to scare anyone. It had wandered in for the smell of the warm buns."
    )
    world.say(
        f"It was only a big festival beast from the parade practice, dusty with straw and a little lost."
    )
    world.say(
        f"{companion.label} changed into a cart shape so it could carry the prop and make room beside the stall."
    )
    world.say(
        f"{hero.label} set down {prop.phrase}, and the small worry turned into a useful one: the beast was hungry."
    )


def resolution(world: World) -> None:
    hero = world.get("hero")
    beast = world.get("beast")
    companion = world.get("companion")
    world.say(
        f"{hero.label} brought the beast a bun, then another. The beast took them carefully, one by one."
    )
    world.say(
        f"The morphodite stayed in cart shape for the baskets, then lamp shape for the dim corner near the stage."
    )
    world.say(
        f"By noon, the bells were ringing, the banners were straight, and the beast was sitting politely by the fence with crumbs on its whiskers."
    )
    world.say(
        f"{hero.label} laughed at how the same small sound had seemed spooky in the morning and ordinary by lunch."
    )


def tell_story(world: World) -> World:
    introduce(world)
    world.para()
    setup(world)
    world.para()
    suspense_turn(world)
    world.para()
    reveal(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    return [
        f"Write a gentle slice-of-life story set at {f['setting'].place} with a festival, a beast, and a morphodite helper.",
        f"Tell a suspenseful but calm story where {hero.label} notices a clue during a {event.keyword} and later learns the beast is harmless.",
        "Write a short child-friendly story that uses repetition, foreshadowing, and a soft reveal at a festival.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    beast = world.facts["beast"]
    companion = world.facts["companion"]
    prop = world.facts["prop"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question=f"Who was the story mainly about at {setting.place}?",
            answer=f"The story was mainly about {hero.label}, who helped at the festival in {setting.place}.",
        ),
        QAItem(
            question=f"What made {hero.label} worried before the beast was found?",
            answer=f"{hero.label} heard a soft thump near the lantern tent and saw a clue that seemed mysterious for a moment.",
        ),
        QAItem(
            question=f"How did the morphodite help with the festival?",
            answer=f"The morphodite changed shapes to carry supplies, peek over the stalls, and bring light to the darker corners.",
        ),
        QAItem(
            question=f"What was the beast actually doing near the festival booths?",
            answer=f"The beast was wandering near the festival because it was hungry and wanted the smell of the warm buns.",
        ),
        QAItem(
            question=f"What happened to {prop.label} by the end?",
            answer=f"{prop.label.capitalize()} was set down safely, and the festival kept going with the prop in place and the beast sitting nearby.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt calm and amused after learning the beast was harmless and just a little lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a festival?",
            answer="A festival is a happy public event where people gather for food, music, games, and friendly activities.",
        ),
        QAItem(
            question="What is a beast?",
            answer="A beast is a large animal or creature, and in stories it can seem scary at first before you learn more about it.",
        ),
        QAItem(
            question="What is a morphodite?",
            answer="A morphodite is a made-up helper creature that can change shape, like a cart or a lamp, to do different jobs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.props:
            bits.append(f"props={ent.props}")
        lines.append(f"{ent.id}: {ent.type} {ent.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Event, Prop) :- setting(Place), affords(Place, Event), prop(Prop).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for ev in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, ev))
    for eid in EVENTS:
        lines.append(asp.fact("event", eid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Festival beast morphodite story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["morphodite"])
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
    combos = valid_combos()
    if args.place or args.event or args.prop:
        combos = [c for c in combos
                  if (args.place is None or c[0] == args.place)
                  and (args.event is None or c[1] == args.event)
                  and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, event, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or "morphodite"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prop=prop, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params.place, params.event, params.prop)
    world = build_world(params)
    world.facts["trait"] = params.trait
    tell_story(world)
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
    StoryParams(place="town_square", event="festival", prop="lantern", name="Mina", gender="girl", companion="morphodite", trait="careful"),
    StoryParams(place="fair_green", event="festival", prop="tray", name="Eli", gender="boy", companion="morphodite", trait="curious"),
    StoryParams(place="market_lane", event="festival", prop="banner", name="Tia", gender="girl", companion="morphodite", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
