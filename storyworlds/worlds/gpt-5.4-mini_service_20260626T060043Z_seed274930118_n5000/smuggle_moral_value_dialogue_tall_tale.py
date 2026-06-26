#!/usr/bin/env python3
"""
storyworlds/worlds/smuggle_moral_value_dialogue_tall_tale.py
============================================================

A compact story world about a tall-tale-sized smuggle, a moral value at stake,
and plenty of dialogue.

Premise:
- A small, folksy hero needs to smuggle a humble but important object past a
  nosy gatekeeper.
- The hero's choice is never just about speed; it also tests honesty, kindness,
  and whether a clever trick helps someone harmless or hurts someone needy.

The world models:
- typed entities with physical meters and emotional memes
- a moral-value axis that can shift from selfishness toward generosity
- dialogue beats that move the story forward
- tall-tale exaggeration in the narration voice, while staying child-facing

This script is standalone and follows the Storyweavers world contract.
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
# Core story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["distance", "risk", "hidden", "blocked", "reputation"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "pride", "kindness", "greed", "relief", "shame", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the creek road"
    boundary: str = "the bridge"
    end_point: str = "the market"
    has_gate: bool = True


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    value: str
    moral_weight: str
    risk_word: str
    hidden_verb: str
    public_verb: str


@dataclass
class Guard:
    id: str
    label: str
    type: str
    phrase: str
    duty: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "creekroad": Setting(place="the creek road", boundary="the rattling bridge", end_point="the market"),
    "fairground": Setting(place="the fairground lane", boundary="the striped gate", end_point="the pie tent"),
    "docktrail": Setting(place="the dock trail", boundary="the rope dock", end_point="the lighthouse shed"),
}

CARGOS = {
    "medicine": Cargo(
        id="medicine",
        label="medicine bottle",
        phrase="a little medicine bottle",
        value="helping someone sick",
        moral_weight="care",
        risk_word="break",
        hidden_verb="tuck the medicine bottle under a coat",
        public_verb="carry the medicine bottle in plain sight",
    ),
    "pie": Cargo(
        id="pie",
        label="pie",
        phrase="a warm blueberry pie",
        value="sharing food",
        moral_weight="generosity",
        risk_word="cool",
        hidden_verb="hide the pie in a basket",
        public_verb="carry the pie where everyone could smell it",
    ),
    "letter": Cargo(
        id="letter",
        label="letter",
        phrase="a folded letter with a wax seal",
        value="keeping a promise",
        moral_weight="truth",
        risk_word="wrinkle",
        hidden_verb="slip the letter into a pocket",
        public_verb="wave the letter around like a flag",
    ),
}

GUARDS = {
    "keeper": Guard(
        id="keeper",
        label="the gatekeeper",
        type="man",
        phrase="a square-shouldered gatekeeper",
        duty="stops travelers and asks questions",
    ),
    "aunt": Guard(
        id="aunt",
        label="Aunt Belle",
        type="woman",
        phrase="a no-nonsense aunt",
        duty="wants the truth told plainly",
    ),
}

HEROES = {
    "boy": ["Ned", "Tom", "Ike", "Zeb", "Milo"],
    "girl": ["June", "Mabel", "Tess", "Dora", "Kit"],
}

TRAITS = ["brave", "bright", "stubborn", "cheerful", "lively", "quick-witted"]


@dataclass
class StoryParams:
    place: str
    cargo: str
    guard: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for cargo in CARGOS:
            for guard in GUARDS:
                combos.append((place, cargo, guard))
    return combos


def reasonableness_gate(place: str, cargo: Cargo, guard: Guard) -> bool:
    if place == "fairground" and cargo.id == "medicine":
        return True
    if place == "creekroad" and cargo.id in {"medicine", "letter"}:
        return True
    if place == "docktrail" and cargo.id in {"pie", "letter"}:
        return True
    return True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    cargo = CARGOS[params.cargo]
    guard = GUARDS[params.guard]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "small-town"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="woman",
        label="Mama June",
        traits=["wise", "kind"],
    ))
    g = world.add(Entity(
        id=guard.id,
        kind="character",
        type=guard.type,
        label=guard.label,
        phrase=guard.phrase,
    ))
    item = world.add(Entity(
        id=cargo.id,
        type="thing",
        label=cargo.label,
        phrase=cargo.phrase,
        owner=hero.id,
        carrier=hero.id,
    ))

    # Act 1: tall-tale setup.
    hero.memes["pride"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} was a {params.trait} little {params.gender} from {setting.place}, "
        f"small as a button and quick as a cricket."
    )
    world.say(
        f"{hero.id} had to get {item.phrase} across {setting.boundary} and on to {setting.end_point}, "
        f"because its {cargo.value} mattered more than a shiny coin in a thunderstorm."
    )
    world.say(
        f"The trouble was {guard.phrase}, who {guard.duty} and could sniff a secret like a hound sniffs supper."
    )

    # Act 2: choice, dialogue, risk.
    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} whispered, 'If I carry it in the open, {g.label.lower()} will stop me.'"
    )
    world.say(
        f"But {hero.id} also said, 'If I hide it, maybe nobody will know I helped.'"
    )
    if cargo.id == "medicine":
        world.say(
            f"{helper.label} said, 'Child, if that bottle reaches the sick house, you'll have done a fine and honest kind of trick.'"
        )
    elif cargo.id == "pie":
        world.say(
            f"{helper.label} said, 'A pie can travel under a towel, but it should still be shared fair and square.'"
        )
    else:
        world.say(
            f"{helper.label} said, 'A letter can be secret without being a lie, if it keeps a promise instead of breaking one.'"
        )

    # The actual smuggle: hidden, but morally directed.
    item.meters["hidden"] = 1
    item.carrier = hero.id
    hero.memes["greed"] += 0.0
    hero.memes["trust"] += 1

    if cargo.id == "medicine":
        world.say(
            f"{hero.id} tucked the bottle under a flapping coat and walked so gently even the dust stayed quiet."
        )
    elif cargo.id == "pie":
        world.say(
            f"{hero.id} hid the pie in a basket under a clean cloth and balanced it like a moon on a fence post."
        )
    else:
        world.say(
            f"{hero.id} slipped the letter inside a boot and marched along as careful as a cat on church steps."
        )

    # Guard interaction.
    world.para()
    guard_blocked = True
    if cargo.id == "medicine":
        world.say(f"{g.label} barked, 'What have you got there?'")
        world.say(f"{hero.id} said, 'Just a little errand and a big hurry.'")
        world.say(f"{g.label} peered hard, but {helper.label} stepped in and said, 'The bottle is for someone in need.'")
        world.say(f"{g.label} scratched {g.label.lower()}'s head and let them through.")
        guard_blocked = False
    elif cargo.id == "pie":
        world.say(f"{g.label} asked, 'What smells so sweet?'")
        world.say(f"{hero.id} answered, 'A pie headed to a hungry table.'")
        world.say(f"{g.label} laughed like a barn door in a windstorm and waved them on.")
        guard_blocked = False
    else:
        world.say(f"{g.label} said, 'Why all the sneaking?'")
        world.say(f"{hero.id} replied, 'Because promises travel better when kept close.'")
        world.say(f"{g.label} softened and said, 'Then keep it close and keep it true.'")
        guard_blocked = False

    # Act 3: moral resolution.
    world.para()
    if not guard_blocked:
        hero.memes["relief"] += 1
        hero.memes["shame"] += 0.0
        world.say(
            f"By the time the sun blinked over {setting.end_point}, {hero.id} had delivered {item.phrase} and learned a tall lesson."
        )
        world.say(
            f"Smuggling can be wrong when it hides a hurtful thing, but it can be right when it shelters kindness, care, or a promise that ought to be kept."
        )
        world.say(
            f"{hero.id} stood taller than a fence post and smiled, because the secret had become a good deed in the daylight."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        guard=g,
        cargo=item,
        cargo_def=cargo,
        guard_def=guard,
        params=params,
        delivered=not guard_blocked,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
cargo(medicine;pie;letter).
place(creekroad;fairground;docktrail).
guard(keeper;aunt).

valid(Place,Cargo,Guard) :- place(Place), cargo(Cargo), guard(Guard).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CARGOS:
        lines.append(asp.fact("cargo", c))
    for g in GUARDS:
        lines.append(asp.fact("guard", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_def"]
    hero = f["hero"]
    guard = f["guard"]
    return [
        f'Write a tall-tale style story about a child who must smuggle {cargo.phrase} past {guard.label}.',
        f"Tell a dialogue-heavy story where {hero.id} makes a sneaky but good-hearted choice to move {cargo.phrase} across town.",
        f'Write a short moral tale that uses the word "smuggle" and ends with a helpful lesson about {cargo.moral_weight}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo_def"]
    guard = f["guard_def"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} need to smuggle?",
            answer=f"{hero.id} needed to smuggle {cargo.phrase} because it mattered for {cargo.value}.",
        ),
        QAItem(
            question=f"Who worried about the secret cargo?",
            answer=f"{guard.label} worried and asked questions, but {helper.label} helped explain why the cargo should get through.",
        ),
        QAItem(
            question=f"How did {hero.id} carry the cargo?",
            answer=f"{hero.id} carried it hidden at first, then used a careful excuse and honest words to finish the trip safely.",
        ),
        QAItem(
            question=f"What lesson did the story give about smuggling?",
            answer=(
                f"The story said smuggling can be wrong when it hides something hurtful, "
                f"but it can be good when it protects care, truth, or a promise."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    cargo = f["cargo_def"]
    out = [
        QAItem(
            question="What does it mean to smuggle something?",
            answer="To smuggle something means to move it secretly past a place or person who would stop it.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind of good choice, like honesty, kindness, fairness, or courage.",
        ),
    ]
    if cargo.id == "medicine":
        out.append(QAItem(
            question="Why can medicine be important?",
            answer="Medicine can help a sick person feel better or heal.",
        ))
    elif cargo.id == "pie":
        out.append(QAItem(
            question="Why is sharing food kind?",
            answer="Sharing food is kind because it helps others get something warm and tasty to eat.",
        ))
    else:
        out.append(QAItem(
            question="Why are letters important?",
            answer="Letters can carry news, promises, and feelings from one person to another.",
        ))
    return out


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.kind:8}/{e.type:8}) meters={{{', '.join(f'{k}: {round(v, 2)}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {round(v, 2)}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    cargo: str
    guard: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about smuggling, dialogue, and moral values.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--guard", choices=sorted(GUARDS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.cargo is None or c[1] == args.cargo)
        and (args.guard is None or c[2] == args.guard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cargo, guard = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, cargo=cargo, guard=guard, name=name, gender=gender, trait=trait)


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
    StoryParams(place="creekroad", cargo="medicine", guard="keeper", name="Ned", gender="boy", trait="brave"),
    StoryParams(place="fairground", cargo="pie", guard="keeper", name="June", gender="girl", trait="cheerful"),
    StoryParams(place="docktrail", cargo="letter", guard="aunt", name="Mabel", gender="girl", trait="quick-witted"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, guard) combos:\n")
        for c in combos:
            print(f"  {c[0]:10} {c[1]:10} {c[2]:10}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
            header = f"### {p.name}: {p.cargo} on {p.place} with {p.guard}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
