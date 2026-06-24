#!/usr/bin/env python3
"""
Fairy-tale story world: a small mystery about a magical muss, a little humor,
and a tidy ending.

A seed tale:
---
In a tiny kingdom, a careful baker named Pippa kept a silver spoon, a warm loaf,
and a little storybook of funny rhymes. One morning, the spoon began to vanish
from the table, and a trail of floury footprints led all through the kitchen.
Pippa worried the queen would think a mouse had made a mess.

But the “mouse” was no mouse at all. It was a shy little kitchen sprite who had
used a giggling spell on the spoon. Every time someone looked straight at it,
the spoon hid behind a teapot or slipped into a basket of buns. Pippa followed
the clues, laughed at the sprite’s silly sneezes, and solved the mystery. Then
she asked the sprite to help tidy the muss, and the kitchen sparkled again.
---

World model:
- Physical meters: flour, crumbs, sticky, tidiness, hiddenness
- Emotional memes: worry, humor, wonder, relief, trust
- The story is driven by state changes: clues appear, magic hides the object,
  humor softens fear, the mystery is solved, and the muss gets cleaned.
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
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "woman", "witch", "princess", "baker"}
        male = {"boy", "king", "man", "wizard", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class ObjectOfSearch:
    id: str
    label: str
    phrase: str
    mess_kind: str
    clue_kind: str
    room: str
    can_hide: bool = True


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    object: str
    seed: Optional[int] = None


SETTINGS = {
    "castle_kitchen": Setting(place="the castle kitchen", indoors=True),
    "moon_library": Setting(place="the moonlit library", indoors=True),
    "rose_garden": Setting(place="the rose garden", indoors=False),
}

OBJECTS = {
    "spoon": ObjectOfSearch(
        id="spoon",
        label="silver spoon",
        phrase="a silver spoon",
        mess_kind="flour",
        clue_kind="footprints",
        room="table",
    ),
    "crown": ObjectOfSearch(
        id="crown",
        label="tiny crown",
        phrase="a tiny crown",
        mess_kind="crumbs",
        clue_kind="sparkles",
        room="bench",
    ),
    "book": ObjectOfSearch(
        id="book",
        label="storybook",
        phrase="a little storybook",
        mess_kind="sticky",
        clue_kind="whispers",
        room="shelf",
    ),
}

HEROES = {
    "Pippa": "girl",
    "Milo": "boy",
    "Nell": "girl",
    "Tobin": "boy",
}

HELPERS = {
    "sprite": "sprite",
    "bunny": "bunny",
    "owl": "owl",
    "cat": "cat",
}

TALES = [
    "Once upon a time",
    "Long ago",
    "In a tiny kingdom",
]

TRAITS = ["careful", "cheerful", "curious", "gentle", "brave"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _clue_reveal(world: World) -> list[str]:
    out = []
    obj = world.get("object")
    if obj.hidden:
        if world.facts.get("clue_seen", 0) >= THRESHOLD:
            sig = "reveal"
            if sig not in world.fired:
                world.fired.add(sig)
                obj.hidden = False
                world.facts["found"] = True
                out.append(f"The clue at the {world.facts['clue_place']} pointed right to the {obj.label}.")
    return out


def _tidy_muss(world: World) -> list[str]:
    out = []
    obj = world.get("object")
    helper = world.get("helper")
    hero = world.get("hero")
    if world.facts.get("found") and world.facts.get("shared_laugh", 0) >= THRESHOLD:
        sig = "tidy"
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["muss"] = False
            hero.memes["relief"] = hero.memes.get("relief", 0) + 1
            helper.memes["trust"] = helper.memes.get("trust", 0) + 1
            out.append(f"Together they brushed the muss away, and the {obj.label} shone again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_clue_reveal, _tidy_muss):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World) -> bool:
    sim = world.copy()
    simulate_magic(sim, narrate=False)
    return sim.facts.get("found", False)


def simulate_magic(world: World, narrate: bool = True) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    obj = world.get("object")
    helper.memes["humor"] = helper.memes.get("humor", 0) + 1
    world.facts["muss"] = True
    obj.hidden = True
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts["clue_seen"] = 1
    world.facts["clue_place"] = {
        "spoon": "a teapot",
        "crown": "the window seat",
        "book": "the old ladder",
    }[obj.id]
    if narrate:
        world.say(
            f"Then a shy little {helper.type} twinkled in with a giggling spell, "
            f"and at once the {obj.label} vanished from sight."
        )
        world.say(
            f"{hero.id} followed the clue trail with a puzzled face, until even the silly spell began to seem funny."
        )
    propagate(world, narrate=narrate)
    world.facts["shared_laugh"] = 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    helper.memes["humor"] = helper.memes.get("humor", 0) + 1


def introduce(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    obj = world.get("object")
    world.say(
        f"{random.choice(TALES)}, {hero.id} was a little {hero.type} with a {hero.traits[0]} heart "
        f"who loved stories, riddles, and neat shelves."
    )
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {obj.phrase} in {world.setting.place}, "
        f"and {helper.id} liked to make {hero.pronoun('object')} laugh with funny hiccups."
    )
    world.say(
        f"One morning, the {obj.label} was missing, and a muss of {obj.mess_kind} had appeared near the {obj.room}."
    )


def mystery_turn(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    obj = world.get("object")
    world.para()
    world.say(
        f"{hero.id} gasped, because the missing {obj.label} made the whole room feel puzzly."
    )
    if predict(world):
        world.say(
            f"{helper.id} whispered, 'Follow the clue and keep your grin on.'"
        )
    simulate_magic(world, narrate=True)
    world.say(
        f"{hero.id} laughed at the helper's sneeze, and the laugh made the spell feel smaller."
    )


def ending(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    obj = world.get("object")
    world.para()
    if not world.facts.get("muss"):
        world.say(
            f"At last the {obj.label} sat in {world.facts['clue_place']}, the muss was gone, "
            f"and the little kingdom looked bright again."
        )
        world.say(
            f"{hero.id} thanked {helper.id}, and both of them smiled at the tidy room and the solved mystery."
        )
    else:
        raise StoryError("The story must end with the muss cleaned and the mystery solved.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    obj_cfg = OBJECTS[params.object]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=[random.choice(TRAITS)]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, traits=["sly", "kind"]))
    obj = world.add(Entity(id="object", kind="thing", type=obj_cfg.label, label=obj_cfg.label, phrase=obj_cfg.phrase))
    world.add(Entity(id="setting", kind="thing", type="place", label=setting.place))
    world.facts["object_cfg"] = obj_cfg
    introduce(world)
    mystery_turn(world)
    ending(world)
    world.facts.update(hero=hero, helper=helper, object=obj)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj_cfg = f["object_cfg"]
    return [
        f"Write a fairy tale about {hero.id}, a {hero.type}, and a missing {obj_cfg.label} that is found through a funny magical clue.",
        f"Tell a child-friendly mystery where {helper.id} uses a giggling spell, the room gets mussy, and {hero.id} solves the puzzle.",
        f"Write a short story with humor, magic, and a solved mystery in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj_cfg = f["object_cfg"]
    return [
        QAItem(
            question=f"What was missing from {world.setting.place}?",
            answer=f"The missing thing was {obj_cfg.phrase}.",
        ),
        QAItem(
            question=f"Who used the giggling spell?",
            answer=f"{helper.id} used the giggling spell.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery was solved, the muss was cleaned away, and the {obj_cfg.label} shone again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the spell turned silly?",
            answer=f"{hero.id} felt less worried and started to laugh, which helped solve the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you try to figure out by looking for clues.",
        ),
        QAItem(
            question="What does a spell do in a fairy tale?",
            answer="A spell is magic words or magic power that can change what happens in the story.",
        ),
        QAItem(
            question="Why can laughter help in a story?",
            answer="Laughter can help because it calms worry, brings people together, and makes a hard problem feel easier to solve.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
found :- clue_seen.
tidied :- found, shared_laugh.
#show found/0.
#show tidied/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue_seen"),
            asp.fact("shared_laugh"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found/0.\n#show tidied/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    if "found/0" in atoms and "tidied/0" in atoms:
        print("OK: ASP twin accepts the solved mystery.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with humor, magic, and a solved mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    obj = args.object or rng.choice(list(OBJECTS))
    hero_type = HEROES[hero]
    helper_type = HELPERS[helper]
    if args.hero and args.helper and hero == helper:
        raise StoryError("The hero and the helper must be different characters.")
    return StoryParams(setting=setting, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, object=obj)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="castle_kitchen", hero="Pippa", hero_type="girl", helper="sprite", helper_type="sprite", object="spoon"),
    StoryParams(setting="moon_library", hero="Milo", hero_type="boy", helper="owl", helper_type="owl", object="book"),
    StoryParams(setting="rose_garden", hero="Nell", hero_type="girl", helper="cat", helper_type="cat", object="crown"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show found/0.\n#show tidied/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show found/0.\n#show tidied/0."))
        print(sorted((sym.name, len(sym.arguments)) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
