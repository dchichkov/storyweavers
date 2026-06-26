#!/usr/bin/env python3
"""
storyworlds/worlds/slim_suspense_animal_story.py
=================================================

A small animal story world with a suspenseful, child-facing premise:
a slim little animal must cross a dark place, hear a worrying sound,
and find a safe way through.

The world is intentionally small and constraint-checked. The story is not
a frozen paragraph with swapped nouns; it is driven by simulated state:
fear rises, a sound appears, a helper or tool changes the danger, and the
ending proves what changed.

Seed impression:
- A slim animal hears something scary in the dark.
- The animal wants to rescue or reach something important.
- A careful helper and a small tool turn suspense into relief.
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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

ANIMAL_NAMES = ["Milo", "Pip", "Nia", "Mira", "Toby", "Lulu", "Rook", "Suri"]
HELPER_NAMES = ["Moss", "Poppy", "Fern", "Bramble", "Wren"]
TRAITS = ["slim", "brave", "curious", "gentle", "quick", "tiny"]

SETTINGS = {
    "wood": "the quiet wood",
    "barn": "the old barn",
    "reedbank": "the reed bank",
    "hill": "the grassy hill",
}

DARK_PLACES = {
    "wood": True,
    "barn": True,
    "reedbank": True,
    "hill": False,
}

OBJECTS = {
    "lantern": {
        "label": "lantern",
        "phrase": "a little lantern with a warm glow",
        "light": 2.0,
    },
    "bell": {
        "label": "bell",
        "phrase": "a tiny silver bell",
        "light": 0.0,
    },
    "rope": {
        "label": "rope",
        "phrase": "a soft rope loop",
        "light": 0.0,
    },
    "leaf": {
        "label": "leaf",
        "phrase": "a broad green leaf",
        "light": 0.0,
    },
}

DANGERS = {
    "owl": {
        "name": "owl",
        "sound": "a soft hoot overhead",
        "shape": "shadow",
        "risk": 1.5,
    },
    "wind": {
        "name": "wind",
        "sound": "a long whistling sigh",
        "shape": "rustle",
        "risk": 1.0,
    },
    "creak": {
        "name": "creak",
        "sound": "a creaky pop from the boards",
        "shape": "noise",
        "risk": 1.2,
    },
}

VALID_PAIRINGS = {
    "wood": {"lantern", "rope"},
    "barn": {"lantern", "bell"},
    "reedbank": {"lantern", "leaf"},
    "hill": {"bell", "leaf"},
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "squirrel", "fox", "rat", "hedgehog", "mole"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting_key: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

        clone = World(self.setting_key)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    danger: str
    helper: str
    item: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_is_helpful(setting: str, item: str) -> bool:
    return item in VALID_PAIRINGS[setting]


def story_is_reasonable(setting: str, danger: str, item: str) -> bool:
    if setting not in SETTINGS or danger not in DANGERS or item not in OBJECTS:
        return False
    return item_is_helpful(setting, item)


def explain_rejection(setting: str, danger: str, item: str) -> str:
    place = SETTINGS.get(setting, setting)
    danger_name = DANGERS.get(danger, {"name": danger})["name"]
    obj = OBJECTS.get(item, {"label": item})["label"]
    return (
        f"(No story: {obj} does not make sense as a safe tool for {danger_name} at {place}. "
        f"Try a combination where the object actually helps in that place.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(S,D,I) :- setting(S), danger(D), item(I), helps(S,I).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for i in VALID_PAIRINGS[s]:
            lines.append(asp.fact("helps", s, i))
    for d in DANGERS:
        lines.append(asp.fact("danger", d))
    for i in OBJECTS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, d, i) for s in SETTINGS for d in DANGERS for i in OBJECTS if story_is_reasonable(s, d, i)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def dark_place(setting: str) -> bool:
    return DARK_PLACES[setting]


def predict_safety(world: World, hero: Entity, item: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] = 0.0
    sim.get(item.id).carried_by = hero.id
    safe = sim.facts.get("tool_light", 0.0) >= 1.0
    return {"safe": safe}


def tell(setting: str, danger: str, helper: str, item: str, hero_name: str, hero_type: str, trait: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type))
    pal = w.add(Entity(id=helper, kind="character", type="mouse"))
    tool = w.add(Entity(
        id=item,
        type=item,
        label=OBJECTS[item]["label"],
        phrase=OBJECTS[item]["phrase"],
        owner=hero.id,
        carried_by=hero.id,
    ))
    d = DANGERS[danger]

    w.facts.update(hero=hero, pal=pal, tool=tool, danger=d, setting=setting, item=item)

    place = SETTINGS[setting]
    w.say(f"{hero_name} was a {trait} little {hero_type} who loved quiet paths and soft grass.")
    w.say(f"{hero_name} carried {tool.phrase} because {hero_name.lower()} liked to feel ready for the dark.")

    w.para()
    if dark_place(setting):
        w.say(f"At {place}, the sky dimmed fast, and the path ahead looked narrow and strange.")
    else:
        w.say(f"At {place}, the evening stayed mild, but the shadows still made the corners look deep.")
    w.say(f"Then {hero_name} heard {d['sound']}.")
    hero.memes["fear"] += 1
    w.say(f"{hero_name} stopped so suddenly that {hero_name.lower()} almost dropped the {tool['label']}.")

    w.para()
    hero.memes["curiosity"] += 1
    w.say(f"{hero_name} wanted to keep going, but {hero_name.lower()} could not see the far side clearly.")
    w.say(f"{helper} came close and whispered that the noise might be something small, not something cruel.")
    w.say(f"Together they listened again, very still.")

    if danger == "owl":
        w.say("The shape above them bobbed once, and a sleepy owl blinked from a branch.")
    elif danger == "wind":
        w.say("The wind pushed the reeds and made the whole bank shiver like a living thing.")
    else:
        w.say("A board in the old path gave one deep creak, then held still again.")

    w.para()
    if item == "lantern":
        hero.memes["hope"] += 1
        w.say(f"{helper} lifted the lantern, and a warm circle of light spilled over the ground.")
        w.say(f"That light showed there was room to pass, because the scary shape was only {d['sound']} and a harmless little shadow.")
        w.say(f"{hero_name} breathed out, stepped forward, and crossed safely with {tool.label} glowing beside {hero_name.lower()}.")
    elif item == "rope":
        hero.memes["hope"] += 1
        w.say(f"{helper} tied the rope to a low post so {hero_name} could follow the line without stumbling.")
        w.say(f"The steady rope made the dark feel smaller, and the sound turned out to be only {d['sound']}.")
        w.say(f"{hero_name} went on, one careful step at a time, until the path opened wide again.")
    elif item == "bell":
        hero.memes["hope"] += 1
        w.say(f"{helper} gave the bell a tiny shake, and its bright ring cut through the hush.")
        w.say(f"The ringing let {hero_name} hear where the path turned, and the fear shrank to a little flutter.")
        w.say(f"{hero_name} followed the sound and reached the other side without a tumble.")
    else:
        hero.memes["hope"] += 1
        w.say(f"{helper} held the broad leaf over {hero_name_name if False else hero_name}'s head like a tiny shield.")
        w.say(f"It did not chase the dark away, but it helped {hero_name} feel brave enough to keep moving.")
        w.say(f"Before long, {hero_name} found the safe edge of the path and smiled at the calm end of the night.")

    w.facts["resolved"] = True
    w.facts["tool_light"] = OBJECTS[item]["light"]
    return w


# ---------------------------------------------------------------------------
# Registries and QA
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for d in DANGERS:
            for i in OBJECTS:
                if story_is_reasonable(s, d, i):
                    out.append((s, d, i))
    return sorted(out)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    d = f["danger"]["name"]
    item = f["tool"]["label"]
    place = SETTINGS[f["setting"]]
    return [
        f"Write a short suspenseful animal story about a slim little {hero.type} at {place} where something scary seems to move in the dark.",
        f"Tell a gentle suspense story for children in which {hero.id} hears {d['sound']} and uses a {item} to stay safe.",
        f"Write an animal story with a brief scare, a careful helper, and a calm ending at {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    tool = f["tool"]
    d = f["danger"]
    place = SETTINGS[f["setting"]]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a {hero.memes and 'slim'} little {hero.type} who goes through a scary moment and then feels safe again.",
        ),
        QAItem(
            question=f"What worried {hero.id} at {place}?",
            answer=f"{hero.id} heard {d['sound']} at {place}, and that made the path feel suspenseful until {pal.id} helped look again.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel brave near the end?",
            answer=f"{tool.phrase} helped, because it gave {hero.id} something useful to do while {pal.id} stayed beside {hero.id}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} crossing safely and learning that the scary sound was not a disaster after all.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives off light so you can see in dark places and feel safer walking there.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something seems scary or uncertain.",
        ),
        QAItem(
            question="Why might a slim animal fit through a narrow place more easily?",
            answer="A slim animal can slip through tight spaces more easily because there is less body to squeeze past the walls or reeds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="wood", danger="owl", helper="Moss", item="lantern", hero_name="Pip", hero_type="mouse", trait="slim"),
    StoryParams(setting="barn", danger="creak", helper="Poppy", item="bell", hero_name="Milo", hero_type="rabbit", trait="slim"),
    StoryParams(setting="reedbank", danger="wind", helper="Fern", item="rope", hero_name="Lulu", hero_type="squirrel", trait="slim"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slim suspenseful animal story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--item", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--type", dest="hero_type", choices=["mouse", "rabbit", "squirrel", "fox", "hedgehog", "mole"], default=None)
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
    if args.setting and args.danger and args.item and not story_is_reasonable(args.setting, args.danger, args.item):
        raise StoryError(explain_rejection(args.setting, args.danger, args.item))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.danger is None or c[1] == args.danger)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, danger, item = rng.choice(combos)
    helper = args.helper or rng.choice(HELPER_NAMES)
    hero_type = args.hero_type or rng.choice(["mouse", "rabbit", "squirrel", "hedgehog"])
    hero_name = args.name or rng.choice(ANIMAL_NAMES)
    trait = args.trait or "slim"
    return StoryParams(setting=setting, danger=danger, helper=helper, item=item, hero_name=hero_name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.danger, params.helper, params.item, params.hero_name, params.hero_type, params.trait)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, danger, item) combos:\n")
        for s, d, i in combos:
            print(f"  {s:9} {d:8} {i:8}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.setting} / {p.danger} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
