#!/usr/bin/env python3
"""
storyworlds/worlds/week_meantime_rock_moral_value_inner_monologue.py
====================================================================

A small bedtime-story world about a child, a found rock, the meantime, and a
gentle moral value learned through inner monologue.

Premise:
A child finds a smooth rock during the week and wants to keep it. In the
meantime, a small delay and a kind thought lead the child from possessiveness
to generosity. The story ends with a quiet, concrete change: the rock is
shared, returned, or used in a way that proves the lesson.

This world uses:
- typed entities with meters and memes
- state-driven narration
- a reasonableness gate with an inline ASP twin
- child-facing bedtime-story prose
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the backyard"
    afford_week_find: bool = True
    afford_meantime_wait: bool = True


@dataclass
class Offer:
    id: str
    label: str
    action: str
    keepsake: bool = False
    helps_with: str = ""


@dataclass
class StoryParams:
    setting: str
    moral_value: str
    monologue_style: str
    child_name: str
    child_gender: str
    child_trait: str
    rock_label: str
    rock_origin: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard"),
    "garden": Setting(place="the garden"),
    "path": Setting(place="the little path by the fence"),
    "porch": Setting(place="the porch"),
}

MORAL_VALUES = {
    "kindness": {
        "name": "kindness",
        "lesson": "kindness means thinking about how another person feels",
        "turn": "share",
    },
    "honesty": {
        "name": "honesty",
        "lesson": "honesty means telling the truth even when it feels a little hard",
        "turn": "tell",
    },
    "patience": {
        "name": "patience",
        "lesson": "patience means waiting calmly while things settle",
        "turn": "wait",
    },
    "generosity": {
        "name": "generosity",
        "lesson": "generosity means giving without clinging too tight",
        "turn": "give",
    },
}

MONOLOGUES = {
    "gentle": [
        "Maybe I should think before I decide.",
        "I can keep the rock safe and still be kind.",
        "The meantime is not empty; it is where good choices grow.",
    ],
    "curious": [
        "I wonder why this little rock matters so much to me.",
        "Maybe the best thing is not always the thing I first wanted.",
        "A quiet pause can help a heart choose well.",
    ],
    "reflective": [
        "I feel the wish to keep it, but I also hear a kinder idea.",
        "I can choose what is right, even while I am waiting.",
        "A small rock can teach a big lesson when I listen closely.",
    ],
}

CHILD_NAMES_GIRL = ["Mia", "Lina", "Nora", "Ella", "Zoe", "Lily", "Ava"]
CHILD_NAMES_BOY = ["Noah", "Eli", "Leo", "Finn", "Theo", "Ben", "Max"]
CHILD_TRAITS = ["thoughtful", "quiet", "curious", "gentle", "sleepy", "careful"]


# ---------------------------------------------------------------------------
# World state and narration
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def nice_day(setting: Setting) -> str:
    if setting.place == "the porch":
        return "On a quiet evening"
    return "One soft week day"


def intro_line(child: Entity) -> str:
    trait = next((t for t in child.traits if t != "little"), "gentle")
    return f"{child.id} was a little {trait} {child.type} who noticed small things very carefully."


def rock_description(rock_label: str, rock_origin: str) -> str:
    return f"a smooth {rock_label} from {rock_origin}"


def monologue_for(style: str, moral_value: str) -> str:
    opts = MONOLOGUES[style]
    base = random.choice(opts)
    moral = MORAL_VALUES[moral_value]["lesson"]
    return f"{base} {moral.capitalize()}."


def offered_action(moral_value: str) -> str:
    return MORAL_VALUES[moral_value]["turn"]


def inner_thoughts(child: Entity, style: str, moral_value: str) -> str:
    thought = monologue_for(style, moral_value)
    return f"{child.id} thought, '{thought}'"


def check_reasonable(params: StoryParams) -> None:
    if params.moral_value not in MORAL_VALUES:
        raise StoryError("Unknown moral value.")
    if params.monologue_style not in MONOLOGUES:
        raise StoryError("Unknown inner monologue style.")
    if params.rock_label.strip() == "":
        raise StoryError("The rock must have a clear label.")


# ---------------------------------------------------------------------------
# Causal rule simulation
# ---------------------------------------------------------------------------
def propagate(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    rock = world.get("rock")

    sig = ("want_keep",)
    if child.memes.get("possessive", 0) >= 1 and sig not in world.fired:
        world.fired.add(sig)
        child.memes["tug"] = child.memes.get("tug", 0) + 1
        out.append(f"{child.id} held the rock a little tighter.")

    sig = ("kind_turn",)
    if child.memes.get("reflection", 0) >= 1 and sig not in world.fired:
        world.fired.add(sig)
        child.memes["kindness"] = child.memes.get("kindness", 0) + 1
        child.memes["tug"] = 0
        out.append(f"The tight feeling in {child.pronoun('possessive')} chest softened.")

    sig = ("shared",)
    if rock.owner != child.id and child.memes.get("kindness", 0) >= 1 and sig not in world.fired:
        world.fired.add(sig)
        rock.carried_by = rock.owner
        out.append(f"The rock was gently given back where it belonged.")
    return out


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def setup(world: World) -> None:
    child = world.get("child")
    rock = world.get("rock")
    world.say(intro_line(child))
    world.say(
        f"In the middle of the week, {child.id} found {rock_description(rock.label, rock.phrase)} "
        f"near {world.setting.place}."
    )
    world.say(f"{child.id} loved the way {rock.it()} fit in {child.pronoun('possessive')} palm.")
    child.memes["possessive"] = 1


def tension(world: World) -> None:
    child = world.get("child")
    rock = world.get("rock")
    world.para()
    world.say(nice_day(world.setting) + f", {child.id} carried the rock home in the meantime.")
    world.say(
        f"{child.id} wanted to keep {rock.it()} forever, because it felt like a secret treasure."
    )
    world.say(inner_thoughts(child, world.facts["monologue_style"], world.facts["moral_value"]))
    child.memes["reflection"] = 1
    propagate(world)


def turn(world: World) -> None:
    child = world.get("child")
    rock = world.get("rock")
    moral = world.facts["moral_value"]
    world.para()
    world.say(
        f"Then {child.id} remembered that {MORAL_VALUES[moral]['lesson']}."
    )
    if moral == "kindness":
        world.say(f"{child.id} thought about how another child might like to hold the rock, too.")
    elif moral == "honesty":
        world.say(f"{child.id} knew the grown-up should hear the truth about where the rock came from.")
    elif moral == "patience":
        world.say(f"{child.id} decided to wait until morning instead of grabbing a fast answer.")
    else:
        world.say(f"{child.id} decided that keeping the rock was less important than doing what was generous.")

    child.memes["kindness"] = 1
    propagate(world)

    if moral == "kindness":
        rock.owner = "neighbor"
        world.say(f"{child.id} walked the rock back and placed it in a waiting hand.")
    elif moral == "honesty":
        rock.owner = "neighbor"
        world.say(f"{child.id} told the truth, and the rock returned to the neighbor's windowsill.")
    elif moral == "patience":
        world.say(f"{child.id} set the rock on a shelf and waited until it was the right time to ask about it.")
    else:
        rock.owner = "neighbor"
        world.say(f"{child.id} chose generosity and gave the rock back with a small smile.")


def ending(world: World) -> None:
    child = world.get("child")
    rock = world.get("rock")
    world.para()
    if rock.owner == "neighbor":
        world.say(
            f"By bedtime, {child.id} felt warm inside, because {world.facts['moral_value']} had made the ending soft."
        )
        world.say(
            f"The little rock was not a secret treasure anymore; it was a shared, happy memory."
        )
    else:
        world.say(
            f"By bedtime, {child.id} placed the rock by the pillow and promised to ask about it tomorrow."
        )
        world.say(
            f"The meantime had turned into a calm, sleepy promise instead of a greedy one."
        )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    check_reasonable(params)
    setting = SETTINGS[params.setting]
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        traits=["little", params.child_trait],
        meters={"tired": 0},
        memes={"possessive": 0, "reflection": 0, "kindness": 0},
    ))
    rock = world.add(Entity(
        id="rock",
        kind="thing",
        type="rock",
        label=params.rock_label,
        phrase=params.rock_origin,
        owner="neighbor",
        carried_by=None,
        plural=False,
        meters={"smoothness": 1},
        memes={"specialness": 1},
    ))
    neighbor = world.add(Entity(
        id="neighbor",
        kind="character",
        type="adult",
        label="the neighbor",
        traits=["patient"],
        meters={},
        memes={},
    ))

    world.facts.update(
        setting=params.setting,
        moral_value=params.moral_value,
        monologue_style=params.monologue_style,
        child=child,
        rock=rock,
        neighbor=neighbor,
    )

    setup(world)
    tension(world)
    turn(world)
    ending(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child about a week, a {f["rock"].label}, and a kind thought in the meantime.',
        f"Tell a gentle story where {f['child'].id} finds a {f['rock'].label} and learns a moral value through inner monologue.",
        f'Write a short bedtime story that uses the words "week", "meantime", and "rock" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    rock = world.facts["rock"]
    moral = world.facts["moral_value"]
    return [
        QAItem(
            question=f"What did {child.id} find during the week?",
            answer=f"{child.id} found {rock_description(rock.label, rock.phrase)} near {world.setting.place}.",
        ),
        QAItem(
            question=f"What was {child.id} thinking about in the meantime?",
            answer=(
                f"In the meantime, {child.id} was thinking about whether to keep the rock or do what was right."
            ),
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"The story taught {moral}, because {MORAL_VALUES[moral]['lesson']}.",
        ),
        QAItem(
            question=f"How did the child change by the end?",
            answer=(
                f"By the end, {child.id} was kinder and less clingy, and the rock was no longer treated like a secret prize."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "week": [
        QAItem(
            question="What is a week?",
            answer="A week is a group of seven days.",
        )
    ],
    "meantime": [
        QAItem(
            question="What does meantime mean?",
            answer="Meantime means the time in between two moments or events.",
        )
    ],
    "rock": [
        QAItem(
            question="What is a rock?",
            answer="A rock is a hard piece of stone found on the ground.",
        )
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means caring about other people and trying to help them feel good.",
        )
    ],
    "honesty": [
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth.",
        )
    ],
    "patience": [
        QAItem(
            question="What is patience?",
            answer="Patience means waiting calmly without getting upset.",
        )
    ],
    "generosity": [
        QAItem(
            question="What is generosity?",
            answer="Generosity means giving or sharing willingly.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = ["week", "meantime", "rock", world.facts["moral_value"]]
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE[tag])
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
# Tracing
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_wants_keep(C) :- possessive(C).
child_reflects(C) :- reflection(C).
child_becomes_kind(C) :- child_reflects(C), lesson(M), moral_value(M).

resolved(C) :- child_becomes_kind(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in MORAL_VALUES:
        lines.append(asp.fact("moral_value", name))
        lines.append(asp.fact("lesson", name))
    for name in MONOLOGUES:
        lines.append(asp.fact("monologue_style", name))
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    lines.append(asp.fact("thing", "rock"))
    lines.append(asp.fact("keyword", "week"))
    lines.append(asp.fact("keyword", "meantime"))
    lines.append(asp.fact("keyword", "rock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = asp.atoms(model, "resolved")
    ok = ("resolved",) not in []  # keep structure simple
    if atoms == [("C",)]:
        pass
    # Parity check is structural: the ASP program should always produce at
    # least one resolved atom when given the fixed facts.
    if atoms:
        print("OK: ASP twin produces a resolved story state.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected resolved state.")
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about a rock, the meantime, and a moral value."
    )
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--moral-value", choices=MORAL_VALUES.keys())
    ap.add_argument("--monologue-style", choices=MONOLOGUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("--rock-label")
    ap.add_argument("--rock-origin")
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
    moral_value = args.moral_value or rng.choice(list(MORAL_VALUES))
    monologue_style = args.monologue_style or rng.choice(list(MONOLOGUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)
    trait = args.trait or rng.choice(CHILD_TRAITS)
    rock_label = args.rock_label or rng.choice(["little gray rock", "round pebble", "palm-sized stone"])
    rock_origin = args.rock_origin or rng.choice(["the garden path", "the edge of the porch", "the warm little lane"])
    params = StoryParams(
        setting=setting,
        moral_value=moral_value,
        monologue_style=monologue_style,
        child_name=name,
        child_gender=gender,
        child_trait=trait,
        rock_label=rock_label,
        rock_origin=rock_origin,
    )
    check_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="backyard",
        moral_value="kindness",
        monologue_style="gentle",
        child_name="Mia",
        child_gender="girl",
        child_trait="thoughtful",
        rock_label="smooth gray rock",
        rock_origin="the garden path",
    ),
    StoryParams(
        setting="garden",
        moral_value="honesty",
        monologue_style="curious",
        child_name="Leo",
        child_gender="boy",
        child_trait="curious",
        rock_label="round pebble",
        rock_origin="the warm little lane",
    ),
    StoryParams(
        setting="porch",
        moral_value="patience",
        monologue_style="reflective",
        child_name="Lily",
        child_gender="girl",
        child_trait="quiet",
        rock_label="small white stone",
        rock_origin="the porch step",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(asp.atoms(model, "resolved"))
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
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.child_name}: {p.moral_value} with a rock at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
