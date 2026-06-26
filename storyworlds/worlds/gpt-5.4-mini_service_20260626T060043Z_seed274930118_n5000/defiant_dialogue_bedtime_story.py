#!/usr/bin/env python3
"""
storyworlds/worlds/defiant_dialogue_bedtime_story.py
=====================================================

A small storyworld about bedtime, a defiant child, and a gentle dialogue that
turns resistance into rest.
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
# World model
# ---------------------------------------------------------------------------

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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"tired": 0.0, "mess": 0.0, "sleepy": 0.0}
        if not self.memes:
            self.memes = {"defiance": 0.0, "comfort": 0.0, "love": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    soothing: bool = False
    doubles_as: str = ""  # bedtime helper type


@dataclass
class Choice:
    id: str
    name: str
    prompt: str
    effect: str
    helps_sleep: bool
    makes_defiance_worse: bool = False


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    choice: Optional[Choice] = None
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            items=copy.deepcopy(self.items),
            choice=copy.deepcopy(self.choice),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": "the bedroom",
    "nursery": "the nursery",
    "cabin": "the little cabin",
}

ITEMS = {
    "blanket": Item(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        kind="comfort",
        soothing=True,
        doubles_as="cover",
    ),
    "night_light": Item(
        id="night_light",
        label="night light",
        phrase="a small moon-shaped night light",
        kind="light",
        soothing=True,
        doubles_as="glow",
    ),
    "stuffed_bear": Item(
        id="stuffed_bear",
        label="stuffed bear",
        phrase="a cuddly stuffed bear",
        kind="friend",
        soothing=True,
        doubles_as="hug",
    ),
    "water_cup": Item(
        id="water_cup",
        label="water cup",
        phrase="a little cup of water",
        kind="need",
        soothing=True,
        doubles_as="sip",
    ),
}

CHOICES = {
    "one_more_song": Choice(
        id="one_more_song",
        name="one more song",
        prompt="Sing one more song",
        effect="softened the sharp edges of the evening",
        helps_sleep=True,
    ),
    "one_more_hug": Choice(
        id="one_more_hug",
        name="one more hug",
        prompt="Ask for one more hug",
        effect="made the room feel safe again",
        helps_sleep=True,
    ),
    "stay_up_too_long": Choice(
        id="stay_up_too_long",
        name="stay up too long",
        prompt="Keep arguing and stay up too long",
        effect="made bedtime harder",
        helps_sleep=False,
        makes_defiance_worse=True,
    ),
}

NAMES = ["Mila", "Theo", "Nina", "Finn", "Luna", "Ben", "Ivy", "Eli"]
PARENTS = [("mother", "mom"), ("father", "dad")]
TRAITS = ["curious", "sleepy", "bright-eyed", "stubborn", "gentle", "playful"]


# ---------------------------------------------------------------------------
# Story structure
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    child_trait: str
    parent_type: str
    comfort_item: str
    choice: str
    seed: Optional[int] = None


def _article(name: str) -> str:
    return "an" if name[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_gender,
            memes={"defiance": 0.0, "comfort": 0.0, "love": 0.0, "calm": 0.0},
            meters={"tired": 0.0, "mess": 0.0, "sleepy": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent_type,
            label=PARENTS[0][1] if params.parent_type == "mother" else PARENTS[1][1],
            memes={"defiance": 0.0, "comfort": 0.0, "love": 0.0, "calm": 0.0},
            meters={"tired": 0.0, "mess": 0.0, "sleepy": 0.0},
        )
    )
    comfort = world.items[params.comfort_item]
    choice = CHOICES[params.choice]
    world.choice = choice
    world.facts.update(
        child=child,
        parent=parent,
        comfort=comfort,
        choice=choice,
        params=params,
    )

    # Beginning
    world.say(
        f"{child.id} was {_article(params.child_trait)} {params.child_trait} little {params.child_gender} "
        f"who loved the last bit of each day."
    )
    world.say(
        f"At {world.setting}, {child.id}'s favorite bedtime thing was {comfort.phrase}."
    )
    world.say(
        f"{child.id} liked to listen when {parent.label} tucked {child.pronoun('object')} in and spoke softly."
    )

    # Middle tension
    world.para()
    child.meters["tired"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"One night, {parent.label} said, \"It is bedtime now, {child.id}.\""
    )
    world.say(
        f"{child.id} crossed {child.pronoun('possessive')} arms and said, \"No, I am not sleepy.\""
    )
    world.say(
        f"{parent.label} smiled and answered, \"Your eyes look heavy, and your voice sounds small.\""
    )
    if choice.makes_defiance_worse:
        child.memes["defiance"] += 1
        world.say(
            f"But {child.id} only shook {child.pronoun('possessive')} head and kept arguing."
        )
    else:
        child.memes["comfort"] += 1
        world.say(
            f"{child.id} still wanted one more little thing before sleep."
        )

    # Turn
    world.para()
    if choice.helps_sleep:
        world.say(f"{parent.label} said, \"How about {choice.prompt.lower()}?\"")
        world.say(f"{child.id} looked at {parent.label} and whispered, \"Okay.\"")
        child.memes["calm"] += 1
        child.memes["defiance"] = max(0.0, child.memes["defiance"] - 1.0)
        child.meters["sleepy"] += 1
        world.say(
            f"That {choice.effect}, and {comfort.phrase} waited close by on the pillow."
        )
    else:
        world.say(f"{parent.label} said, \"We can talk kindly, but we cannot stay up forever.\"")
        world.say(
            f"{child.id} paused, listened, and let the room grow quiet."
        )
        child.memes["calm"] += 1
        child.meters["sleepy"] += 1

    # Resolution
    world.para()
    child.meters["tired"] += 1
    child.memes["love"] += 1
    world.say(
        f"At last, {child.id} curled under the {comfort.label} and closed {child.pronoun('possessive')} eyes."
    )
    world.say(
        f"{parent.label} tucked the blanket in and whispered, \"Good night, my dear.\""
    )
    world.say(
        f"The room stayed still and warm, and soon {child.id} was breathing in slow, sleepy breaths."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    comfort = f["comfort"]
    choice = f["choice"]
    return [
        f'Write a bedtime story for a young child named {child.id} that includes the word "defiant" and gentle dialogue.',
        f"Tell a bedtime story where {child.id} is defiant at {world.setting} but {parent.label} helps {child.pronoun('object')} settle with {comfort.label}.",
        f"Write a soft story about a child who resists sleep, talks with a parent, and ends under {comfort.phrase}.",
        f"Make a bedtime tale with dialogue where {choice.name} leads from fussing to rest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    comfort = f["comfort"]
    choice = f["choice"]
    return [
        QAItem(
            question=f"Why was {child.id} defiant at bedtime?",
            answer=(
                f"{child.id} wanted to keep the evening going and did not want to stop playing yet. "
                f"At first, {child.id} crossed {child.pronoun('possessive')} arms and said no."
            ),
        ),
        QAItem(
            question=f"What did {parent.label} say to help {child.id} settle down?",
            answer=(
                f"{parent.label} spoke gently and offered {choice.prompt.lower()}. "
                f"That made the room feel kinder and gave {child.id} a way to agree."
            ),
        ),
        QAItem(
            question=f"What helped {child.id} fall asleep at the end?",
            answer=(
                f"{comfort.phrase} and {parent.label}'s soft tuck-in helped {child.id} get cozy. "
                f"By the end, {child.id} was breathing in slow, sleepy breaths."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when a child gets ready to rest, often by washing up, listening to a story, and climbing into bed.",
        ),
        QAItem(
            question="Why do people use a night light?",
            answer="People use a night light to make a room feel less dark and more comfortable at night.",
        ),
        QAItem(
            question="What does a blanket do?",
            answer="A blanket helps keep someone warm and cozy while they sleep.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child(C) :- child_name(C).
parent(P) :- parent_type(P).
comfort(I) :- comfort_item(I).

defiant(C) :- story_defiant(C).
settles(C) :- story_settles(C).

valid(S, I, C) :- setting(S), item(I), child_name(C), bedtime_story(S, I).
valid_story(S, I, C, D) :- valid(S, I, C), child_gender(C, D).

bedtime_story(S, I) :- setting(S), item(I), helps_sleep(I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.soothing:
            lines.append(asp.fact("helps_sleep", iid))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if choice.helps_sleep:
            lines.append(asp.fact("helps_sleep_choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for item_id, item in ITEMS.items():
            for child in NAMES:
                if item.soothing:
                    combos.append((setting, item_id, child))
    return combos


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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} type={e.type:7} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    if world.choice:
        lines.append(f"  choice={world.choice.id}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    child_trait: str
    parent_type: str
    comfort_item: str
    choice: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld with a defiant child and gentle dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--comfort", choices=ITEMS)
    ap.add_argument("--choice", choices=CHOICES)
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
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES)
    child_trait = args.trait or rng.choice(TRAITS)
    parent_type = args.parent or rng.choice(["mother", "father"])
    comfort_item = args.comfort or rng.choice([k for k, v in ITEMS.items() if v.soothing])
    choice = args.choice or rng.choice(list(CHOICES))

    if args.choice and not CHOICES[args.choice].helps_sleep:
        raise StoryError("This world needs a kind bedtime turn, so the chosen dialogue must help the child settle.")

    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=child_trait,
        parent_type=parent_type,
        comfort_item=comfort_item,
        choice=choice,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, item, child) combos ({len(stories)} with gender):\n")
        for setting, item, child in triples:
            genders = sorted(g for (s, i, c, g) in stories if (s, i, c) == (setting, item, child))
            print(f"  {setting:8} {item:12} {child:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bedroom", "Mila", "girl", "stubborn", "mother", "blanket", "one_more_song"),
            StoryParams("nursery", "Theo", "boy", "sleepy", "father", "stuffed_bear", "one_more_hug"),
            StoryParams("cabin", "Luna", "girl", "playful", "mother", "night_light", "one_more_song"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
