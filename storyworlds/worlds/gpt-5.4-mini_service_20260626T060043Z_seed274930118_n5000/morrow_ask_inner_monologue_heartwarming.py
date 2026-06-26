#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/morrow_ask_inner_monologue_heartwarming.py
===============================================================================================================

A tiny heartwarming storyworld about a child, a gentle ask, and the promise of
the morrow. The story is driven by simulated state: a character carries a wish,
quietly thinks through it, asks someone kind, and either receives help or finds
a small brave way forward.

Seed words: morrow, ask
Feature: inner monologue
Style: heartwarming
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        pronouns = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
            "person": {"subject": "they", "object": "them", "possessive": "their"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "neighbor": {"subject": "they", "object": "them", "possessive": "their"},
            "grandparent": {"subject": "they", "object": "them", "possessive": "their"},
            "friend": {"subject": "they", "object": "them", "possessive": "their"},
        }
        base = pronouns.get(self.type, pronouns["person"])
        return base[case]


@dataclass
class Place:
    name: str
    warmth: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    label: str
    phrase: str
    verb: str
    result: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    phrase: str
    action: str
    effect: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.help_used: Optional[str] = None
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.help_used = self.help_used
        w.fired = set(self.fired)
        return w


def inner_thought(hero: Entity, wish: Wish, object_label: str) -> str:
    return (
        f"{hero.pronoun().capitalize()} thought, "
        f'"If I can ask kindly, maybe the morrow will feel brighter."'
    )


def want_line(hero: Entity, wish: Wish) -> str:
    return f"{hero.id} wanted to {wish.verb}."


def ask_line(hero: Entity, helper: Entity, wish: Wish) -> str:
    return (
        f"At last, {hero.id} took a breath and asked {helper.id}, "
        f'"Could we {wish.verb} for the morrow?"'
    )


def resolve_line(hero: Entity, helper: Entity, wish: Wish, help_def: Optional[Help]) -> str:
    if help_def is None:
        return (
            f"{helper.id} smiled softly and said the morrow could wait. "
            f"So {hero.id} kept the wish safe and made a small plan for later."
        )
    return (
        f"{helper.id} said yes, and together they used {help_def.phrase}. "
        f"That made {wish.result}, and {hero.id} felt warm inside."
    )


def build_story(place: Place, wish: Wish, help_def: Optional[Help], hero_name: str, helper_name: str,
                hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        type=hero_type,
        label=hero_name,
        traits=[trait, "thoughtful"],
        meters={"hope": 1.0},
        memes={"hope": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        type=helper_type,
        label=helper_name,
        traits=["kind", "steady"],
        meters={"care": 1.0},
        memes={"care": 1.0},
    ))

    world.say(f"{hero.id} lived near {place.name}, where even quiet days felt gentle.")
    world.say(f"{hero.id} had a small wish to {wish.verb}, and {wish.phrase} felt important.")
    world.say(inner_thought(hero, wish, wish.label))

    world.para()
    world.say(f"By evening, {hero.id} looked at {place.name} and imagined the morrow.")
    world.say(f"Would the morrow be ready for {wish.label}? {hero.id} hoped so.")
    world.say(ask_line(hero, helper, wish))
    world.say(f"{helper.id} listened with a kind face.")

    world.para()
    if help_def is not None and wish.id in help_def.helps:
        world.help_used = help_def.id
        hero.memes["relief"] = 1.0
        hero.meters["hope"] += 1.0
        world.say(
            f"{hero.id} felt brave enough to ask, because asking did not feel greedy; "
            f"it felt honest."
        )
        world.say(resolve_line(hero, helper, wish, help_def))
        world.say(
            f"In the end, {hero.id} went home smiling, carrying the thought that "
            f"the morrow could hold something lovely."
        )
    else:
        world.say(
            f"{helper.id} could not make that exact wish happen tonight, but {helper.id} did not laugh."
        )
        world.say(
            f"Instead, {helper.id} helped {hero.id} imagine a smaller step for tomorrow, "
            f"and that still counted as care."
        )
        world.say(
            f"{hero.id} tucked the wish into {hero.pronoun('possessive')} heart and felt comforted."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        wish=wish,
        help_def=help_def,
        place=place,
        trait=trait,
    )
    return world


PLACES = {
    "home": Place(name="home", warmth="cozy", affords={"read", "bake", "draw", "plan"}),
    "porch": Place(name="the porch", warmth="soft", affords={"watch", "wait", "talk"}),
    "garden": Place(name="the garden", warmth="bright", affords={"plant", "pick", "talk", "plan"}),
    "library": Place(name="the library", warmth="quiet", affords={"read", "plan", "draw"}),
}

WISHES = {
    "story": Wish(
        id="story",
        label="a story",
        phrase="a story would make the evening feel snug",
        verb="hear a story",
        result="the room felt snug and sleepy",
        requires={"read"},
        tags={"story", "book"},
    ),
    "cookie": Wish(
        id="cookie",
        label="a cookie",
        phrase="a cookie would make the morrow start sweetly",
        verb="bake a cookie",
        result="the kitchen smelled sweet and bright",
        requires={"bake"},
        tags={"cookie", "sweet"},
    ),
    "drawing": Wish(
        id="drawing",
        label="a drawing",
        phrase="a drawing would help the child remember the day",
        verb="make a drawing",
        result="the paper held a tiny happy picture",
        requires={"draw"},
        tags={"draw", "art"},
    ),
    "garden": Wish(
        id="garden",
        label="a garden visit",
        phrase="a short garden visit would make the morrow feel hopeful",
        verb="visit the garden",
        result="the little path felt full of promise",
        requires={"plan", "talk"},
        tags={"garden", "plant"},
    ),
}

HELPS = {
    "readbook": Help(
        id="readbook",
        label="a storybook",
        phrase="a storybook and a cozy lamp",
        action="read a story",
        effect="the room glowed with soft comfort",
        helps={"story"},
    ),
    "mixbatter": Help(
        id="mixbatter",
        label="a mixing bowl",
        phrase="a bowl, a spoon, and gentle help",
        action="bake a cookie",
        effect="the cookies became warm little moons",
        helps={"cookie"},
    ),
    "coloredpencil": Help(
        id="coloredpencil",
        label="colored pencils",
        phrase="colored pencils and a fresh page",
        action="make a drawing",
        effect="the page turned into a tiny treasure",
        helps={"drawing"},
    ),
    "seedpack": Help(
        id="seedpack",
        label="seed packets",
        phrase="seed packets and a little watering can",
        action="visit the garden",
        effect="the garden promise felt easy to keep",
        helps={"garden"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Eva", "June"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Sage"]
HELPER_NAMES = ["Mira", "Pip", "Aunt Jo", "Grandma", "Noah", "Mr. Lee"]
TRAITS = ["brave", "gentle", "patient", "curious", "shy", "careful"]


@dataclass
class StoryParams:
    place: str
    wish: str
    help: str
    name: str
    gender: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, pl in PLACES.items():
        for wish_id, wish in WISHES.items():
            if not wish.requires.issubset(pl.affords):
                continue
            for help_id, hp in HELPS.items():
                if wish_id in hp.helps:
                    combos.append((place, wish_id, help_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld about asking gently for the morrow."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--help", dest="help_item", choices=HELPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["friend", "mother", "father", "grandparent", "neighbor"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.wish is None or c[1] == args.wish)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, wish, help_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["friend", "mother", "father", "grandparent", "neighbor"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, wish=wish, help=help_id, name=name, gender=gender,
                       helper_name=helper_name, helper_type=helper_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming short story with the words "morrow" and "ask" about {f["hero"].id}.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['wish'].verb} and asks {f['helper'].id} for help.",
        f"Write an inner-monologue story about a child thinking about the morrow before making a kind ask.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    wish: Wish = f["wish"]
    help_def: Optional[Help] = f["help_def"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {wish.verb}.",
        ),
        QAItem(
            question=f"Who did {hero.id} ask for help?",
            answer=f"{hero.id} asked {helper.id} kindly.",
        ),
        QAItem(
            question=f"What word did {hero.id} think about when hoping for something good later?",
            answer="The child thought about the morrow, which means the next day.",
        ),
    ]
    if help_def is not None:
        qa.append(
            QAItem(
                question=f"How did {help_def.label} help the wish come true?",
                answer=f"{help_def.phrase} helped make it possible to {wish.verb}, and {wish.result}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'morrow' mean?",
            answer="Morrow is a gentle old word for the next day.",
        ),
        QAItem(
            question="Why can asking kindly help?",
            answer="Asking kindly helps because it shows respect, and people are often more willing to help when they feel respected.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private talk a character has in their own head.",
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


ASP_RULES = r"""
valid_combo(Place,Wish,Help) :- place(Place), wish(Wish), help(Help),
                                affords(Place,Need), needs(Wish,Need),
                                helps(Help,Wish).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
        for n in sorted(w.requires):
            lines.append(asp.fact("needs", wid, n))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        for w in sorted(h.helps):
            lines.append(asp.fact("helps", hid, w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    wish = WISHES[params.wish]
    help_def = HELPS[params.help]
    world = build_story(
        place=place,
        wish=wish,
        help_def=help_def,
        hero_name=params.name,
        helper_name=params.helper_name,
        hero_type=params.gender,
        helper_type=params.helper_type,
        trait=params.trait,
    )
    return world


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} type={e.type:10} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  place={world.place.name}")
    lines.append(f"  help_used={world.help_used}")
    return "\n".join(lines)


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
    StoryParams(place="home", wish="story", help="readbook", name="Mina", gender="girl",
                helper_name="Grandma", helper_type="grandparent", trait="gentle"),
    StoryParams(place="home", wish="cookie", help="mixbatter", name="Owen", gender="boy",
                helper_name="Mira", helper_type="mother", trait="curious"),
    StoryParams(place="library", wish="drawing", help="coloredpencil", name="Lila", gender="girl",
                helper_name="Pip", helper_type="friend", trait="shy"),
    StoryParams(place="garden", wish="garden", help="seedpack", name="Theo", gender="boy",
                helper_name="Mr. Lee", helper_type="neighbor", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
