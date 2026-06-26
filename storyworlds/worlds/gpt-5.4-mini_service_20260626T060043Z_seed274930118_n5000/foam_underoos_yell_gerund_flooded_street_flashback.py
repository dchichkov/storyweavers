#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/foam_underoos_yell_gerund_flooded_street_flashback.py
======================================================================================================

A tiny heartwarming storyworld about a child in a flooded street, a soggy
warning, and a safer way to play after a flashback teaches everyone to be kind.

Premise seed:
- foam
- underoos
- yell-gerund
- flooded street
- Flashback
- Cautionary
- Heartwarming

The world models:
- a child who loves the foam
- a parent who remembers a past scare in a flashback
- a flooded street that is tempting but risky
- a cautionary warning, then a warm compromise that keeps the play going
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "fear": 0.0, "joy": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "care": 0.0, "warning": 0.0, "flashback": 0.0}

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
    place: str = "the flooded street"
    indoor: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Finn", "Ava", "Theo"]
TRAITS = ["careful", "curious", "gentle", "brave", "playful", "thoughtful"]


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    child_type = params.gender
    parent_type = params.parent

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        traits=["little", params.trait],
        meters={"wet": 0.0, "fear": 0.0, "joy": 0.0, "work": 0.0},
        memes={"joy": 0.0, "fear": 0.0, "care": 0.0, "warning": 0.0, "flashback": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={"wet": 0.0, "fear": 0.0, "joy": 0.0, "work": 0.0},
        memes={"joy": 0.0, "fear": 0.0, "care": 0.0, "warning": 0.0, "flashback": 0.0},
    ))
    foam = world.add(Entity(
        id="foam",
        type="toy",
        label="foam float",
        phrase="a bright foam float",
        owner=hero.id,
        caretaker=parent.id,
    ))
    underoos = world.add(Entity(
        id="underoos",
        type="clothes",
        label="underoos",
        phrase="clean underoos",
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        region="torso",
    ))
    raincoat = world.add(Entity(
        id="raincoat",
        type="gear",
        label="raincoat",
        phrase="a yellow raincoat",
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        region="torso",
        protective=True,
        covers={"torso"},
    ))
    world.facts.update(hero=hero, parent=parent, foam=foam, underoos=underoos, raincoat=raincoat)
    return world


def flashback(world: World) -> None:
    parent = world.get("Parent")
    parent.memes["flashback"] += 1
    world.say(
        "The parent had a flashback to one rainy afternoon, when a sudden splash had "
        "made everyone run and search with worried faces."
    )
    world.say(
        "That old scare had ended safely, but it taught the parent to speak softly "
        "when water was deep and streets were slippery."
    )


def introduce(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    parent = world.get("Parent")
    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} "
        f"who loved {world.facts['foam'].label} and bright puddles."
    )
    world.say(
        f"{hero.id} also wore {world.facts['underoos'].label} under a raincoat, because the day "
        f"had come with a flooded street and shiny little waves."
    )
    parent.memes["care"] += 1


def caution(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    parent = world.get("Parent")
    hero.memes["joy"] += 1
    world.say(
        f"On the flooded street, {hero.id} wanted to yell-gerund with delight and dash straight "
        f"into the water."
    )
    world.say(
        f"But {parent.label} held up a gentle hand and said, \"Careful, {hero.id}. "
        f"Deep water can hide holes and bumps.\""
    )
    hero.memes["warning"] += 1
    hero.meters["fear"] += 1


def child_reacts(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    parent = world.get("Parent")
    hero.memes["fear"] += 0.5
    world.say(
        f"{hero.id} frowned for a moment, then listened. {hero.pronoun().capitalize()} did not want "
        f"to get hurt, and {hero.pronoun('possessive')} heart wanted to stay close."
    )
    world.say(
        f"{parent.pronoun().capitalize()} remembered the flashback too, and that made the warning "
        f"kind instead of sharp."
    )


def safe_play(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    parent = world.get("Parent")
    foam = world.get("foam")
    hero.meters["wet"] += 0.2
    hero.memes["joy"] += 1.5
    parent.memes["joy"] += 1
    world.say(
        f"Then the parent found a safer game: they set the foam on a flat crate and let it bob "
        f"in the water like a tiny boat."
    )
    world.say(
        f"{hero.id} grinned, reached for the foam, and splashed only with the toes of "
        f"{hero.pronoun('possessive')} boots."
    )
    world.say(
        f"Soon {hero.id} was laughing instead of yelling, and the underoos stayed dry under the "
        f"raincoat."
    )
    foam.meters["wet"] += 0.1


def ending(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    parent = world.get("Parent")
    world.say(
        f"By the end, the flooded street still glittered, but now it felt like a place for "
        f"careful play, not a place to rush."
    )
    world.say(
        f"{hero.id} carried the foam home, warm and happy, while {parent.label} walked beside "
        f"{hero.pronoun('object')} with a relieved smile."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    flashback(world)
    caution(world)
    child_reacts(world)
    world.para()
    safe_play(world)
    ending(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child should not be urged into deep flooded water without caution.
risky(street) :- flooded(street).
needs_warning(child) :- risky(street), child_near(street).
heartwarming(child) :- needs_warning(child), safe_compromise(child).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("flooded", "street"),
        asp.fact("child_near", "street"),
        asp.fact("has", "hero", "foam"),
        asp.fact("worn", "hero", "underoos"),
        asp.fact("worn", "hero", "raincoat"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.gender not in {"girl", "boy"}:
        raise StoryError("This world only supports a girl or boy protagonist.")
    if params.parent not in {"mother", "father"}:
        raise StoryError("This world only supports a mother or father caregiver.")


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    py = True
    try:
        reasonableness_gate(StoryParams(name="Mia", gender="girl", parent="mother", trait="careful"))
    except StoryError:
        py = False
    model = asp.one_model(asp_program("#show risky/1."))
    clingo = bool(asp.atoms(model, "risky"))
    if py and clingo:
        print("OK: ASP and Python gates agree for the flooded street world.")
        return 0
    print("MISMATCH: Python and ASP reasonableness differ.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        'Write a heartwarming story about foam, a flooded street, and a careful parent.',
        f"Tell a cautionary story where {hero.id} wants to play in the flooded street, but the parent remembers a flashback and finds a safer way.",
        "Write a short child-friendly story that includes underoos, a raincoat, and a gentle compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the flooded street?",
            answer=(
                f"{parent.label} warned {hero.id} because the water could hide holes and bumps, "
                f"and the street was too deep for rushing. The warning was gentle because the parent "
                f"remembered a flashback to an old scare."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the foam at first?",
            answer=(
                f"{hero.id} wanted to dash into the flooded street and play with the foam right away, "
                f"because the water looked exciting."
            ),
        ),
        QAItem(
            question=f"What safer choice did they make in the end?",
            answer=(
                f"They set the foam on a flat crate so it could bob like a tiny boat, and {hero.id} "
                f"played carefully instead of rushing into the deep water."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foam?",
            answer="Foam is light and bubbly, so it can float and bob on water.",
        ),
        QAItem(
            question="What are underoos?",
            answer="Underoos are underclothes worn under outer clothes, so they stay hidden and help keep a child comfortable.",
        ),
        QAItem(
            question="Why should people be careful around flooded streets?",
            answer="Flooded streets can hide holes, trash, and strong water, so careful steps are safer than rushing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:10} type={e.type:10} "
            f"meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming flooded-street storyworld.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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
    StoryParams(name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risky/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show risky/1."))
        print("risky atoms:", asp.atoms(model, "risky"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
