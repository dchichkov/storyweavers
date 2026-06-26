#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/liqueur_prohibit_foreshadowing_mystery_to_solve_adventure.py
===============================================================================================================================================

A standalone story world for a tiny adventure about a hidden liqueur, a mysterious
prohibition, and a child who solves the puzzle through careful observation and
brave action.

Seed story:
---
In the village of Willowdale, there was a rule: NO ONE may taste the golden liqueur
kept in the old oak barrel behind the mayor's house. The barrel had sat there for
years, locked with a heavy iron clasp, and the key hung on a hook inside the
mayor's study. Every child knew the rule, but no one knew WHY the liqueur was
forbidden. Some whispered it was cursed. Others said it was poison. The mayor
refused to explain.

One day, a girl named Elara noticed something: a tiny vine had crept through the
crack in the barrel's wood, and on that vine grew three small purple berries.
The berries smelled like honey and spice. Elara remembered her grandmother saying,
"when the barrel vine blooms, the truth will show its face." She decided to
investigate. She looked at the key, counted the steps from the barrel to the well,
and drew a map of the shadows at noon. She found that the barrel's lock had a
small panel with three symbols: a leaf, a drop, and a star. The berries matched
the leaf. She pressed one against the leaf symbol and heard a soft click. The key
turned easily. Inside, instead of dark liquid, she found a rolled parchment with
a poem: "The liqueur is not for drinking but for seeing — pour one drop on any
truth and watch it glow." Elara poured a drop on the map, and the hidden tunnel
beneath the well glowed blue. She smiled and knew what to do next.

Causal constraints:
---
- investigate(actor, clue)          -> actor.knowledge += 1, clue.found = True
- match(berry, symbol)               -> lock opens if berry.kind matches symbol.kind
- open_barrel(actor)                 -> actor.reveals += 1, liqueur.revealed = True
- apply_liqueur(actor, target)       -> truth appears, actor.success = True
- telling_an_adult(actor)            -> mayor.knowledge += 1, reward given

Domain objects:
---
Clues: vine, berries, grandmother's saying, shadow map, symbols
Items: key, barrel, liqueur, parchment, berry
Locations: barrel, study, well
Actors: Elara, Mayor, Grandmother (memory)
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

CLUE_KINDS = {"vine", "saying", "shadow_map", "symbols"}
LOCATIONS = {"barrel_location", "study", "well"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    is_clue: bool = False
    is_symbol: bool = False
    symbol_kind: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    state: dict[str, bool] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mayor_f"}
        male = {"boy", "man", "mayor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    found_text: str
    tags: set[str] = field(default_factory=set)
    requires: list[str] = field(default_factory=list)


@dataclass
class Symbol:
    id: str
    kind: str
    match_with: str


CLUES: list[Clue] = [
    Clue(id="vine", label="vine", phrase="a tiny green vine creeping from the barrel crack",
         kind="vine", location="barrel_location",
         found_text="A tiny vine had squeezed through the crack in the barrel's wood, "
                    "and on it grew three small purple berries that smelled like honey and spice.",
         tags={"vine", "barrel", "crack"}),
    Clue(id="saying", label="grandmother's saying", phrase="her grandmother's old saying",
         kind="saying", location="study",
         found_text="Elara remembered her grandmother saying, 'when the barrel vine blooms, "
                    "the truth will show its face.'",
         tags={"saying", "grandmother", "truth"}),
    Clue(id="shadow_map", label="shadow map", phrase="a map she drew of the noon shadows",
         kind="shadow_map", location="well",
         found_text="She counted steps from the barrel to the well and drew the shadow "
                    "positions at noon. The map showed a pattern.",
         requires=["vine"],
         tags={"map", "shadow", "well"}),
    Clue(id="symbols", label="symbols on the lock", phrase="three symbols: a leaf, a drop, and a star",
         kind="symbols", location="barrel_location",
         found_text="The barrel's lock had a small panel with three symbols: a leaf, a drop, and a star.",
         requires=["shadow_map"],
         tags={"symbol", "lock", "leaf", "drop", "star"}),
]

SYMBOLS: list[Symbol] = [
    Symbol(id="leaf", kind="leaf", match_with="berry"),
    Symbol(id="drop", kind="drop", match_with="water"),
    Symbol(id="star", kind="star", match_with="light"),
]

BERRIES = ["purple", "blue", "red", "gold"]
BERRY_KINDS = {"purple": "leaf", "blue": "drop", "red": "star", "gold": "star"}


@dataclass
class StoryParams:
    hero_name: str
    hero_gender: str
    mayor_gender: str
    puzzle_difficulty: str
    berry_color: str
    seed: Optional[int] = None


class World:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.found_clues: set[str] = set()
        self.barrel_open: bool = False
        self.liqueur_used: bool = False
        self.success: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.found_clues = set(self.found_clues)
        clone.barrel_open = self.barrel_open
        clone.liqueur_used = self.liqueur_used
        clone.success = self.success
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_foreshadow(world: World) -> list[str]:
    """Vine and grandmother saying foreshadow the truth."""
    out = []
    if "vine" in world.found_clues and "saying" not in world.found_clues:
        sig = ("foreshadow", "vine")
        if sig not in world.fired:
            world.fired.add(sig)
            vine = world.get("vine_clue")
            vine.memes["foreboding"] += 1
            out.append("The vine seemed to whisper a secret only the brave could hear.")
    return out


def _r_reveal(world: World) -> list[str]:
    """Using liqueur reveals truth."""
    if world.liqueur_used and not world.success:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.success = True
            out.append("The hidden tunnel beneath the well glowed a brilliant blue.")
            return out
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="foreshadow", tag="narrative", apply=_r_foreshadow),
    Rule(name="reveal", tag="climax", apply=_r_reveal),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In a little village called Willowdale, a {hero.type} named {hero.id} "
              f"lived with a curious heart and brave feet.")
    world.say(f"Everyone knew the rule: No one may taste the golden liqueur in the old oak barrel "
              f"behind the mayor's house.")


def show_mystery(world: World, hero: Entity, mayor: Entity) -> None:
    world.say(f"The barrel was locked with a heavy iron clasp, and the key hung on a hook "
              f"in the mayor's study.")
    world.say(f"Every child knew the rule, but no one knew WHY the liqueur was forbidden.")
    world.say(f"{mayor.pronoun('possessive').capitalize()} lips were sealed tighter than the barrel.")


def discover_clue(world: World, hero: Entity, clue: Clue) -> None:
    if clue.id in world.found_clues:
        return
    world.found_clues.add(clue.id)
    clue_obj = world.add(Entity(
        id=f"{clue.id}_clue",
        kind="clue",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        location=clue.location,
        is_clue=True,
    ))
    world.say(clue.found_text)
    hero.memes["knowledge"] += 1
    clue_obj.state["found"] = True
    if clue.kind == "symbols":
        # Lock panel described
        world.say(f"{hero.id} studied the symbols with growing excitement.")
        propagate(world)


def match_berry(world: World, hero: Entity, berry_color: str) -> None:
    symbol_kind = BERRY_KINDS.get(berry_color, "leaf")
    world.say(f"{hero.id} picked one of the {berry_color} berries and held it against "
              f"the leaf symbol on the lock.")
    world.say(f"It fit perfectly. A soft click echoed in the quiet yard.")
    world.barrel_open = True
    hero.memes["success"] += 1


def open_barrel(world: World, hero: Entity, mayor: Entity) -> None:
    world.say(f"The iron clasp lifted easily. {hero.id} opened the barrel lid.")
    world.say(f"Instead of dark liquid, inside lay a rolled parchment with a poem:")
    world.say('"The liqueur is not for drinking but for seeing — pour one drop '
              'on any truth and watch it glow."')
    world.facts["parchment_found"] = True
    hero.memes["revelation"] += 1


def apply_liqueur(world: World, hero: Entity, target: str = "map") -> None:
    world.liqueur_used = True
    world.say(f"{hero.id} took a small drop of the golden liqueur and let it fall "
              f"on the {target}.")
    world.say(f"The liquid shimmered and began to glow. A hidden tunnel beneath the well "
              f"appeared on the map, outlined in blue light.")
    propagate(world)
    hero.memes["success"] += 1


def tell_mayor(world: World, hero: Entity, mayor: Entity) -> None:
    world.say(f"{hero.id} ran to the mayor's study and showed the glowing map.")
    world.say(f"{mayor.pronoun('possessive').capitalize()} eyes widened. 'You solved it,' "
              f"{mayor.pronoun()} whispered. 'The liqueur was never a drink — it was a key "
              f"to the village's oldest secret.'")
    world.say(f"She awarded {hero.id} a small silver badge shaped like a leaf.")
    world.facts["reward"] = True
    hero.memes["joy"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    hero_type = params.hero_gender or "girl"
    mayor_type = f"mayor_{params.mayor_gender[0]}" if params.mayor_gender else "mayor_f"
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_type,
        label=params.hero_name,
        traits=["curious", "brave"],
    ))
    mayor = world.add(Entity(
        id="Mayor",
        kind="character",
        type=mayor_type,
        label="the mayor",
    ))
    world.facts["hero"] = hero
    world.facts["mayor"] = mayor

    # Act 1: setup
    introduce(world, hero)
    show_mystery(world, hero, mayor)
    world.para()

    # Act 2: investigation - clues revealed sequentially
    world.say(f"One afternoon, {hero.id} noticed something near the barrel.")
    discover_clue(world, hero, CLUES[0])  # vine
    world.para()
    world.say(f"{hero.id} hurried to the study to think.")
    discover_clue(world, hero, CLUES[1])  # saying
    world.para()
    world.say(f"At the well, {hero.id} measured the shadows.")
    discover_clue(world, hero, CLUES[2])  # shadow map
    world.para()
    world.say(f"Back at the barrel, {hero.id} saw the symbols.")
    discover_clue(world, hero, CLUES[3])  # symbols
    world.para()

    # Act 3: puzzle solving
    world.say(f"The {params.berry_color} berries on the vine matched the leaf symbol.")
    match_berry(world, hero, params.berry_color)
    world.para()
    open_barrel(world, hero, mayor)
    world.para()
    apply_liqueur(world, hero, target="map")
    world.para()
    tell_mayor(world, hero, mayor)
    world.say(f"That is how {hero.id} discovered that some secrets are not meant to be drunk — "
              f"only to be seen.")
    return world


GIRL_NAMES = ["Elara", "Mira", "Lena", "Sofia", "Iris"]
BOY_NAMES = ["Eli", "Nico", "Theo", "Finn", "Kai"]
MAYOR_GENDERS = ["mother", "father"]
DIFFICULTIES = ["easy", "medium", "hard"]
COLORS = ["purple", "blue", "red", "gold"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(name, gender, mayor, color)
            for name in GIRL_NAMES + BOY_NAMES
            for gender in ["girl", "boy"]
            for mayor in MAYOR_GENDERS
            for color in COLORS
            if (gender == "girl" and name in GIRL_NAMES) or (gender == "boy" and name in BOY_NAMES)]


ASP_RULES = r"""
% Clues chain: each clue requires the previous one
clue_chain("vine", "saying").
clue_chain("saying", "shadow_map").
clue_chain("shadow_map", "symbols").

% Berry matches symbol based on color
berry_matches("purple", "leaf").
berry_matches("blue", "drop").
berry_matches("red", "star").
berry_matches("gold", "star").

% Valid story requires all clues found and matching berry
valid_story(Name, Gender, Mayor, Color) :-
    clue_chain(_, _),
    berry_matches(Color, _),
    hero_name(Name), hero_gender(Gender),
    mayor_gender(Mayor).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
        for r in c.requires:
            lines.append(asp.fact("requires", c.id, r))
    for s in SYMBOLS:
        lines.append(asp.fact("symbol", s.id, s.kind, s.match_with))
    for color, kind in BERRY_KINDS.items():
        lines.append(asp.fact("berry_matches", color, kind))
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("hero_gender", g))
    for m in MAYOR_GENDERS:
        lines.append(asp.fact("mayor_gender", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short adventure story for a child about solving a mystery involving a forbidden liqueur.",
        "Tell a tale where a curious child discovers the true purpose of a prohibited treasure through clues and bravery.",
        "Create a story where a locked barrel, a vine, and a grandmother's saying lead to a hidden truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts.get("hero")
    mayor = world.facts.get("mayor")
    if not hero:
        return []
    return [
        QAItem(
            question=f"What rule existed in Willowdale about the golden liqueur?",
            answer=f"The rule was that no one may taste the golden liqueur in the old oak barrel behind the mayor's house.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find first near the barrel?",
            answer=f"{hero.id} found a tiny green vine with three small purple berries creeping through a crack in the barrel.",
        ),
        QAItem(
            question=f"How did {hero.id} open the barrel?",
            answer=f"{hero.id} matched one of the berries to the leaf symbol on the lock, and the lock clicked open.",
        ),
        QAItem(
            question=f"What was inside the barrel instead of liqueur?",
            answer=f"Inside was a rolled parchment with a poem that said the liqueur was for seeing, not drinking.",
        ),
        QAItem(
            question=f"What happened when {hero.id} poured the liqueur on the map?",
            answer=f"The map glowed blue, revealing a hidden tunnel beneath the well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a liqueur?", answer="A liqueur is a sweet, flavored drink, but in this story it is a magical liquid that reveals truth."),
        QAItem(question="Why do people make rules?", answer="Rules can protect us or keep secrets safe. In the story, the rule hid a magical purpose."),
        QAItem(question="What does 'prohibit' mean?", answer="To prohibit means to forbid or say no to something. The liqueur was prohibited."),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a forbidden liqueur, a mystery, a brave child.")
    ap.add_argument("--hero-name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mayor-gender", choices=MAYOR_GENDERS)
    ap.add_argument("--color", choices=COLORS)
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
    name = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    if name in GIRL_NAMES and gender == "boy":
        raise StoryError(f"{name} is a girl's name.")
    if name in BOY_NAMES and gender == "girl":
        raise StoryError(f"{name} is a boy's name.")
    mayor = args.mayor_gender or rng.choice(MAYOR_GENDERS)
    color = args.color or rng.choice(COLORS)
    return StoryParams(
        hero_name=name,
        hero_gender=gender,
        mayor_gender=mayor,
        puzzle_difficulty="medium",
        berry_color=color,
    )


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
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.state:
                bits.append(f"state={e.state}")
            lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
        print("\n".join(lines))
    if qa:
        lines = []
        lines.append("== (1) Generation prompts ==")
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
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(f"  {s[0]:6} {s[1]:5} {s[2]:6} {s[3]:6}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []

    if args.all:
        combos = valid_combos()
        for name, gender, mayor, color in combos[:5]:
            p = StoryParams(hero_name=name, hero_gender=gender, mayor_gender=mayor,
                            puzzle_difficulty="medium", berry_color=color)
            samples.append(generate(p))
    else:
        seen = set()
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
        if args.all or len(samples) > 1:
            p = sample.params
            header = f"### {p.hero_name}: {p.berry_color} berries, {p.mayor_gender} mayor"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
