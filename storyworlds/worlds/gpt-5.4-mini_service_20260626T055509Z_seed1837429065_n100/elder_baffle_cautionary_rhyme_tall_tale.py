#!/usr/bin/env python3
"""
storyworlds/worlds/elder_baffle_cautionary_rhyme_tall_tale.py
==============================================================

A small tall-tale story world about an elder's cautionary rhyme and a baffle
that can confuse a wandering child.

Seed imagination:
- An elder knows a sung warning.
- A strange baffle can turn a short errand into a lost-and-found adventure.
- The child wants to push ahead anyway.
- A rhyme, a tool, and a wiser choice bring everyone home in one piece.

The world model tracks:
- physical meters: distance, mist, noise, lost, shine, dust
- emotional memes: wonder, defiance, caution, relief, trust, confusion

The story is designed to read like a complete child-facing tale, with a beginning,
a turn, and a resolved ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother", "elder_woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "elder_man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    meter: str
    effect: str
    confusion: str
    rhyme_key: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    safe_against: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.hazard: Hazard | None = None
        self.tool: Tool | None = None
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.hazard = self.hazard
        c.tool = self.tool
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "baffle_bend": Setting(
        place="Baffle Bend",
        detail="a windy bend in the road where echoes liked to play tricks",
        afford={"wander", "cross", "look"},
    ),
    "hayloft": Setting(
        place="the hayloft",
        detail="a high, dusty loft above the barn where shadows could shuffle",
        afford={"wander", "look"},
    ),
    "river_ford": Setting(
        place="the river ford",
        detail="a shallow crossing where water flashed and stones hid under the current",
        afford={"cross", "look"},
    ),
}

HAZARDS = {
    "echo_mist": Hazard(
        id="echo_mist",
        label="echo-mist",
        meter="confusion",
        effect="made the trail seem to split into two",
        confusion="baffled",
        rhyme_key="echo",
    ),
    "night_fog": Hazard(
        id="night_fog",
        label="night fog",
        meter="lost",
        effect="swallowed fence posts and footmarks",
        confusion="lost",
        rhyme_key="fog",
    ),
    "crooked_wind": Hazard(
        id="crooked_wind",
        label="crooked wind",
        meter="noise",
        effect="whistled so hard it rattled the gate latch",
        confusion="rattled",
        rhyme_key="wind",
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a brass lantern",
        phrase="a brass lantern with a bright, steady wick",
        helps={"look", "wander", "cross"},
        safe_against={"echo_mist", "night_fog"},
    ),
    "rope": Tool(
        id="rope",
        label="a red rope",
        phrase="a red rope long enough to trail from hand to hand",
        helps={"cross", "wander"},
        safe_against={"night_fog", "crooked_wind"},
    ),
    "bell": Tool(
        id="bell",
        label="a little bell",
        phrase="a little bell tied to a ribbon",
        helps={"look", "wander"},
        safe_against={"echo_mist", "crooked_wind"},
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Mina", "June", "Lula", "Nell"]
BOY_NAMES = ["Hank", "Jeb", "Milo", "Perry", "Finn", "Owen"]
ELDER_NAMES = ["Gran Ruth", "Old Sam", "Aunt Pru", "Grandpa Eli"]
TRAITS = ["curious", "stubborn", "bright-eyed", "lively"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    tool: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
hazard_present(H) :- hazard(H).
tool_help(T,H) :- tool(T), hazard(H), helps(T, H).
safe_choice(T,H) :- tool(T), hazard(H), safe_against(T, H), tool_help(T,H).

valid_story(P,H,T,G) :- setting(P), hazard(H), tool(T), tool_help(T,H), safe_choice(T,H), gender_ok(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("meter", h.meter))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
        for h in sorted(t.safe_against):
            lines.append(asp.fact("safe_against", tid, h))
    lines.append(asp.fact("gender_ok", "girl"))
    lines.append(asp.fact("gender_ok", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def _python_valid(params: StoryParams) -> bool:
    h = HAZARDS[params.hazard]
    t = TOOLS[params.tool]
    return params.hazard in HAZARDS and params.tool in TOOLS and params.place in SETTINGS and h.id in t.safe_against


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in clingo:", sorted(clingo_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hid, h in HAZARDS.items():
            for tid, t in TOOLS.items():
                if hid in t.safe_against:
                    combos.append((place, hid, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set((a, b, c) for a, b, c, _ in asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: an elder, a baffle, and a cautionary rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    if args.place and args.hazard and args.tool:
        if args.hazard not in TOOLS[args.tool].safe_against:
            raise StoryError(f"(No story: {TOOLS[args.tool].label} does not safely answer the {HAZARDS[args.hazard].label}.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hazard=hazard, tool=tool, name=name, gender=gender, elder=elder, trait=trait)


def _metered(e: Entity, key: str) -> bool:
    return e.meters.get(key, 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    world.hazard = hazard
    world.tool = tool

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder_woman" if "Gran" in params.elder or "Aunt" in params.elder else "elder_man"))

    hero.memes["wonder"] = 1.0
    elder.memes["caution"] = 1.0

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who lived near {world.setting.place}.")
    world.say(f"At {world.setting.place}, the world had a way of looking big as a barn and sly as a fox, especially in {world.setting.detail}.")
    world.say(f"{hero.id} wanted to go see the {hazard.label} because it sounded like the kind of baffle that could make a day into a legend.")
    world.para()
    world.say(f"But {elder.id} shook {elder.pronoun('possessive')} head and sang a cautionary rhyme: ")
    world.say(f"“When {hazard.label} rolls low and the old road sways, you do not dash through on your own brave ways.”")
    world.say(f"“Take {tool.label}, take care, and keep your feet where they ought to stay.”")
    hero.memes["defiance"] = 1.0

    # The turn: if the child pushes ahead, the hazard bites.
    world.para()
    hero.meters["distance"] = 1.0
    hero.meters[hazard.meter] = 1.0
    if hazard.id == "echo_mist":
        hero.memes["confusion"] = 1.0
    elif hazard.id == "night_fog":
        hero.meters["lost"] = 1.0
    else:
        hero.meters["noise"] = 1.0

    world.say(f"{hero.id} tried to hurry ahead anyway, and the {hazard.label} {hazard.effect}.")
    world.say(f"For a spell, the whole lane felt {hazard.confusion} and twice as wide.")
    world.say(f"{hero.id} stopped short, because even a stubborn sprite knows when the road is starting to baffle the boots off a person.")

    # Resolution: tool + elder rhyme restore safety.
    world.para()
    hero.memes["defiance"] = 0.0
    hero.memes["trust"] = 1.0
    hero.memes["relief"] = 1.0
    elder.memes["pride"] = 1.0
    world.say(f"{elder.id} came beside {hero.id} with {tool.phrase}, and together they followed the rhyme instead of the racket.")
    world.say(f"The {tool.label} fit the trouble just right, so the way ahead turned plain again.")
    world.say(f"{hero.id} walked home with {elder.id}, dry enough, clear-eyed, and smiling at the little baffle that had not gotten the better of them.")
    world.say(f"And that was the end of that tall-tale trail: one wise elder, one crooked warning, and one child who learned that a rhyme can be stronger than a boast.")

    world.facts.update(hero=hero, elder=elder, hazard=hazard, tool=tool, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    h = world.facts["hazard"]
    t = world.facts["tool"]
    return [
        f'Write a short tall tale for a child about an elder, a baffle, and a cautionary rhyme using the word "{h.rhyme_key}".',
        f"Tell a child-facing story where {p.name} ignores {p.elder}'s warning, then learns why {t.label} helps near the {h.label}.",
        f"Write a playful but cautionary yarn set at {world.setting.place} with a wise elder and a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hazard"]
    t = world.facts["tool"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    return [
        QAItem(
            question=f"Who was the story about, and where did {p.name} live?",
            answer=f"The story was about {p.name}, a little {p.gender} who lived near {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {elder.id} warn about when {p.name} wanted to go near the {h.label}?",
            answer=f"{elder.id} warned that the {h.label} could baffle a traveler, so it was safer to listen and go carefully.",
        ),
        QAItem(
            question=f"What did the elder sing that made the warning easy to remember?",
            answer=f"{elder.id} sang a cautionary rhyme that told {p.name} not to dash ahead through the trouble alone.",
        ),
        QAItem(
            question=f"How did {t.label} help in the end?",
            answer=f"{t.label.capitalize()} helped because it matched the problem and let {p.name} get home safely without getting caught by the hazard.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and trusting, because the scary part had passed and the elder had helped turn the baffle into a safe lesson.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cautionary rhyme?",
            answer="A cautionary rhyme is a short rhyme that warns someone about danger in a way that is easy to remember.",
        ),
        QAItem(
            question="What does it mean to baffle someone?",
            answer="To baffle someone means to confuse them so much that they are not sure what is happening.",
        ),
        QAItem(
            question="Why do elders often give warnings?",
            answer="Elders often give warnings because they have seen trouble before and want younger folks to stay safe.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  hazard: {world.hazard.id if world.hazard else ''}")
    lines.append(f"  tool: {world.tool.id if world.tool else ''}")
    return "\n".join(lines)


def explain_rejection(hazard: Hazard, tool: Tool) -> str:
    return f"(No story: {tool.label} does not safely fit the {hazard.label}; the elder's warning would not be honest.)"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    StoryParams(place="baffle_bend", hazard="echo_mist", tool="lantern", name="Mabel", gender="girl", elder="Gran Ruth", trait="curious"),
    StoryParams(place="river_ford", hazard="night_fog", tool="rope", name="Hank", gender="boy", elder="Old Sam", trait="stubborn"),
    StoryParams(place="hayloft", hazard="crooked_wind", tool="bell", name="Tilly", gender="girl", elder="Aunt Pru", trait="bright-eyed"),
]


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


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for place, hazard, tool, gender in combos:
            print(f"  {place:12} {hazard:12} {tool:8} {gender}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.hazard} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.tool and args.hazard not in TOOLS[args.tool].safe_against:
        raise StoryError(explain_rejection(HAZARDS[args.hazard], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hazard=hazard, tool=tool, name=name, gender=gender, elder=elder, trait=trait)


if __name__ == "__main__":
    main()
