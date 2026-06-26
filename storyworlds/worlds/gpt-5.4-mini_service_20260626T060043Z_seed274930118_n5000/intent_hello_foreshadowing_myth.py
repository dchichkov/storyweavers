#!/usr/bin/env python3
"""
storyworlds/worlds/intent_hello_foreshadowing_myth.py
=====================================================

A small myth-like storyworld about a child-sized hero, an early greeting, and a
quiet intent that turns into a foretold blessing.

The seed image is simple:
- someone says hello to a sleeping sacred place,
- a sign hints that the day will matter,
- the hero makes an intent,
- the answer arrives as a mythic turn,
- the ending proves the world changed.

The world is simulated, not templated: meters track physical offerings and
distance, memes track courage, awe, and trust, and the story is narrated from
those state changes.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "gift": 0.0, "light": 0.0}
        if not self.memes:
            self.memes = {"awe": 0.0, "trust": 0.0, "intent": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen", "priestess"}
        male = {"boy", "man", "father", "brother", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    sacred_feature: str
    omen: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    hello: str
    intent: str
    sign: str
    turn: str
    offering: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    worth: str
    traits: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting

    def __post_init__(self):
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.omen_seen: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.omen_seen = self.omen_seen
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_omen(world: World) -> list[str]:
    out = []
    if not world.omen_seen:
        return out
    for hero in world.characters():
        if hero.memes["intent"] < THRESHOLD:
            continue
        sig = ("omen", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["awe"] += 1
        out.append("The sign listened, and the air grew deep with waiting.")
    return out


def _r_blessing(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters["gift"] < THRESHOLD:
            continue
        sig = ("blessing", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["trust"] += 1
        out.append("The place answered with a warm and shining hush.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_omen, _r_blessing):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "young")
    world.say(f"{hero.id} was a young {trait} {hero.type} who knew how to listen to old places.")


def hello(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["trust"] += 1
    world.say(f"At {setting.name}, {hero.id} lifted a hand and said hello to the {setting.sacred_feature}.")


def foreshadow(world: World, setting: Setting, rite: Rite) -> None:
    world.omen_seen = True
    world.say(
        f"Then the {setting.omen} moved once above the stones, as if it were warning "
        f"that something true was coming."
    )


def intent(world: World, hero: Entity, rite: Rite) -> None:
    hero.memes["intent"] += 1
    world.say(f"{hero.id} made a quiet intent to {rite.intent}, even if the path felt too small for such a promise.")


def journey(world: World, hero: Entity, rite: Rite, gift: Gift) -> None:
    hero.meters["distance"] += 1
    world.say(
        f"{hero.id} walked toward the old place with {gift.phrase} held close, "
        f"because {rite.sign} had made {hero.pronoun('possessive')} heart steady."
    )


def turn(world: World, hero: Entity, rite: Rite, gift: Gift) -> None:
    hero.meters["gift"] += 1
    world.say(
        f"When {hero.id} gave the {gift.label}, the air turned the way {rite.turn}, "
        f"and the waiting became kind."
    )
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, rite: Rite, gift: Gift) -> None:
    world.say(
        f"In the end, {hero.id} went home with {rite.result}; {gift.phrase} was gone, "
        f"but {hero.pronoun('possessive')} courage stayed bright."
    )


def tell(setting: Setting, rite: Rite, hero_name: str, hero_type: str, gift: Gift) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["young", "brave"],
    ))
    world.add(Entity(
        id=gift.id,
        type="thing",
        label=gift.label,
        phrase=gift.phrase,
        owner=hero.id,
    ))

    intro(world, hero)
    hello(world, hero, setting)
    world.para()
    foreshadow(world, setting, rite)
    intent(world, hero, rite)
    world.para()
    journey(world, hero, rite, gift)
    turn(world, hero, rite, gift)
    world.para()
    ending(world, hero, rite, gift)

    world.facts.update(hero=hero, setting=setting, rite=rite, gift=gift)
    return world


SETTINGS = {
    "hill_shrine": Setting(
        name="the hill shrine",
        sacred_feature="stone altar",
        omen="wind",
        affords={"hello", "intent", "gift"},
    ),
    "river_gate": Setting(
        name="the river gate",
        sacred_feature="water gate",
        omen="mist",
        affords={"hello", "intent", "gift"},
    ),
    "moon_tree": Setting(
        name="the moon tree",
        sacred_feature="silver roots",
        omen="owl-shadow",
        affords={"hello", "intent", "gift"},
    ),
}

RITES = {
    "first_hello": Rite(
        id="first_hello",
        hello="say hello to the old place",
        intent="speak kindly to the shrine",
        sign="the birds went silent",
        turn="a door in the air remembered them",
        offering="a bowl of clean water",
        result="a small blessing and a clear way home",
        tags={"hello", "foreshadowing", "myth"},
    ),
    "river_vow": Rite(
        id="river_vow",
        hello="say hello to the river spirit",
        intent="return the lost charm",
        sign="the reeds bent together",
        turn="the water opened like a curtain",
        offering="a silver comb",
        result="a calm heart and the river's thanks",
        tags={"hello", "foreshadowing", "myth"},
    ),
    "moon_asking": Rite(
        id="moon_asking",
        hello="say hello to the moon tree",
        intent="ask for a night-lighting favor",
        sign="the moon hid behind clouds",
        turn="a single leaf glowed at the right time",
        offering="a lantern seed",
        result="a new song for the dark road",
        tags={"hello", "foreshadowing", "myth"},
    ),
}

GIFTS = {
    "water_bowl": Gift("water_bowl", "bowl of water", "a bowl of clean water", "simple"),
    "silver_comb": Gift("silver_comb", "silver comb", "a silver comb wrapped in cloth", "small"),
    "lantern_seed": Gift("lantern_seed", "lantern seed", "a lantern seed in a little pouch", "rare"),
}

HERO_NAMES = ["Mira", "Niko", "Ari", "Lena", "Tavi", "Sera"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["gentle", "curious", "steadfast", "small", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, r, g) for s in SETTINGS for r in RITES for g in GIFTS]


@dataclass
class StoryParams:
    setting: str
    rite: str
    gift: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that begins with hello and ends in a blessing at {f["setting"].name}.',
        f"Tell a gentle legend where {f['hero'].id} makes an intent to {f['rite'].intent}, "
        f"after a small sign warns that the day matters.",
        f'Write a story that uses the words "hello" and "intent" and includes a foreshadowing sign before a gift is given.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rite: Rite = f["rite"]
    gift: Gift = f["gift"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} say hello?",
            answer=f"{hero.id} said hello at {setting.name}, beside the {setting.sacred_feature}.",
        ),
        QAItem(
            question=f"What intent did {hero.id} make after the sign appeared?",
            answer=f"{hero.id} made a quiet intent to {rite.intent}.",
        ),
        QAItem(
            question=f"What gift did {hero.id} carry to the sacred place?",
            answer=f"{hero.id} carried {gift.phrase}.",
        ),
        QAItem(
            question=f"What hinted that something important was coming?",
            answer=f"The story used foreshadowing: {rite.sign} and the omen over {setting.name}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with {hero.id} leaving with {rite.result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hello used for?",
            answer="Hello is a greeting people use to begin speaking kindly to someone or something.",
        ),
        QAItem(
            question="What does intent mean?",
            answer="Intent is a strong purpose in your heart about what you mean to do.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives an early sign that something important will happen later.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains a place, a spirit, or a special event in a grand way.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill_shrine", "first_hello", "water_bowl", "Mira", "girl", "gentle"),
    StoryParams("river_gate", "river_vow", "silver_comb", "Niko", "boy", "steadfast"),
    StoryParams("moon_tree", "moon_asking", "lantern_seed", "Sera", "girl", "curious"),
]


def explain_invalid(setting: str, rite: str, gift: str) -> str:
    return f"(No story: {setting}, {rite}, and {gift} do not fit the mythic greeting-and-gift pattern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world about hello, intent, and foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.setting and args.rite and args.gift:
        if (args.setting, args.rite, args.gift) not in valid_combos():
            raise StoryError(explain_invalid(args.setting, args.rite, args.gift))
    setting = args.setting or rng.choice(list(SETTINGS))
    rite = args.rite or rng.choice(list(RITES))
    gift = args.gift or rng.choice(list(GIFTS))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, rite=rite, gift=gift, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RITES[params.rite], params.name, params.gender, GIFTS[params.gift])
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
valid_story(S,R,G) :- setting(S), rite(R), gift(G).
hello_first(S,R) :- valid_story(S,R,_).
foreshadowed(S,R) :- valid_story(S,R,_), omen(S), sign_of(R).
has_intent(S,R) :- valid_story(S,R,_), intent_of(R).
ending_blessed(S,R) :- valid_story(S,R,_), blessing_of(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("omen", sid))
        lines.append(asp.fact("sacred", sid, s.sacred_feature))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("sign_of", rid))
        lines.append(asp.fact("intent_of", rid))
        lines.append(asp.fact("blessing_of", rid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} compatible stories:\n")
        for s, r, g in model:
            print(f"  {s:12} {r:12} {g:12}")
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
            header = f"### {p.name}: {p.rite} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
