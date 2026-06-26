#!/usr/bin/env python3
"""
storyworlds/worlds/slack_rhyme_flashback_repetition_ghost_story.py
===================================================================

A tiny ghost-story world with:
- slack as the seed word and central cause of trouble
- rhyme, flashback, and repetition as narrative instruments
- a child-facing, eerie-but-gentle tone
- a state-driven premise, turn, and resolution

The world is designed as a small simulation rather than a frozen template:
a parent and child share an old room, a slack hanging thing causes a spooky
misread, a flashback explains the history, and repetition becomes the calming
spell that resolves the fear.

This file is standalone and follows the storyworld contract.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    shadowy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    unsettling: bool
    slack: bool = False
    location: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None


@dataclass
class Pattern:
    id: str
    verb: str
    gerund: str
    sound: str
    rhyme_word: str
    eerie_image: str
    history_image: str
    keyword: str = "slack"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.props: dict[str, Prop] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []
        self.events: list[str] = []

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_prop(self, prop: Prop) -> Prop:
        self.props[prop.id] = prop
        return prop

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)
        clone.props = dataclasses.deepcopy(self.props)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.history = list(self.history)
        clone.events = list(self.events)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_slack_sway(world: World) -> list[str]:
    out: list[str] = []
    for prop in world.props.values():
        if not prop.slack:
            continue
        sig = ("sway", prop.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The slack thing swayed in the dim room.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("fear", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fearful"] = hero.memes.get("fearful", 0.0) + 1
        out.append(f"{hero.id} held still and listened too hard.")
    return out


def _r_reassured(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("calm", 0.0) < THRESHOLD:
            continue
        sig = ("calm", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["fear"] = 0.0
        out.append(f"The room felt smaller, but safer now.")
    return out


CAUSAL_RULES = [
    Rule("slack_sway", _r_slack_sway),
    Rule("fear", _r_fear),
    Rule("reassured", _r_reassured),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "attic": Setting(place="the attic", shadowy=True, affords={"peek", "hear"}),
    "hallway": Setting(place="the hallway", shadowy=True, affords={"peek", "hear"}),
    "bedroom": Setting(place="the bedroom", shadowy=True, affords={"peek", "hear"}),
}

PATTERNS = {
    "curtain": Pattern(
        id="curtain",
        verb="peek behind the curtain",
        gerund="peeking behind the curtain",
        sound="flap",
        rhyme_word="moon",
        eerie_image="a curtain that moved like a quiet wave",
        history_image="the same curtain swaying in an old memory",
        tags={"ghost", "slack", "rhyme", "flashback", "repetition"},
    ),
    "rope": Pattern(
        id="rope",
        verb="look at the rope by the stairs",
        gerund="looking at the rope by the stairs",
        sound="creak",
        rhyme_word="light",
        eerie_image="a rope hanging slack like a sleeping snake",
        history_image="the rope that once held a little basket",
        tags={"ghost", "slack", "repetition"},
    ),
    "sheet": Pattern(
        id="sheet",
        verb="check the white sheet",
        gerund="checking the white sheet",
        sound="rustle",
        rhyme_word="night",
        eerie_image="a white sheet draped slack over a chair",
        history_image="the sheet folded neatly after laundry day",
        tags={"ghost", "slack", "flashback", "rhyme"},
    ),
}

CURATED = [
    ("attic", "curtain"),
    ("hallway", "rope"),
    ("bedroom", "sheet"),
]

GIRL_NAMES = ["Mina", "Lia", "Nora", "Elsie", "Pippa"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Jasper"]
TRAITS = ["curious", "brave", "gentle", "small", "sleepy"]


@dataclass
class StoryParams:
    place: str
    pattern: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world with slack, rhyme, flashback, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--pattern", choices=PATTERNS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    pattern = args.pattern or rng.choice(list(PATTERNS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, pattern=pattern, name=name, gender=gender, parent=parent, trait=trait)


def _do_flashback(world: World, hero: Entity, prop: Prop, pattern: Pattern) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1
    world.history.append(pattern.history_image)
    world.say(
        f"{hero.id} remembered it from yesterday, when the same slack thing had looked harmless in the light."
    )


def _do_repetition(world: World, hero: Entity, pattern: Pattern) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f'{hero.id} whispered, "{pattern.sound}, no scare; {pattern.sound}, no scare; {pattern.sound}, no scare."'
    )


def tell(setting: Setting, pattern: Pattern, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add_entity(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add_entity(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    prop = world.add_prop(
        Prop(
            id=pattern.id,
            label=pattern.id,
            phrase=pattern.eerie_image,
            unsettling=True,
            slack=True,
            location=setting.place,
            owner=hero.id,
            caretaker=parent.id,
        )
    )

    world.say(f"{hero.id} was a little {trait} {gender} who liked quiet rooms and soft beds.")
    world.say(f"{hero.id} and {parent.label} lived in {setting.place}, where shadows could stretch long and thin.")
    world.say(f"They noticed {prop.phrase}.")
    world.para()
    world.say(f"{hero.id} wanted to {pattern.verb}, even though the room felt hushed as a held breath.")
    hero.memes["fear"] = 1.0
    propagate(world)
    world.say(f"The slack {pattern.id} made a small {pattern.sound}, and that made the silence feel even bigger.")
    world.para()
    _do_flashback(world, hero, prop, pattern)
    world.say(
        f"In the flashback, the same thing had not been spooky at all; it had been ordinary, a thing that only looked ghostly in the dark."
    )
    world.say(
        f"That memory came back like a little lamp, and the room stopped feeling like a haunted house."
    )
    world.para()
    _do_repetition(world, hero, pattern)
    propagate(world)
    world.say(
        f'{hero.id} repeated the words until the scare got smaller and smaller. Then {hero.id} smiled and said, "No ghost here—just {prop.label}."'
    )
    world.say(
        f"At the end, the slack thing stayed where it was, but it no longer seemed like a shadow with a secret."
    )
    world.facts.update(hero=hero, parent=parent, prop=prop, pattern=pattern, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, pattern = f["hero"], f["parent"], f["pattern"]
    return [
        f'Write a short ghost story for a child that includes the word "slack" and ends calmly.',
        f"Tell a gentle spooky story where {hero.id} sees something slack in {world.setting.place} and then remembers what it really was.",
        f"Write a tiny story with rhyme, flashback, and repetition, where {hero.id} and {parent.label} solve a spooky misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, pattern = f["hero"], f["parent"], f["pattern"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.traits[-1]} child, and {parent.label}, who were together in {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the room seem spooky at first?",
            answer=f"The slack {pattern.id} looked eerie in the dim room, so it seemed like a ghostly thing for a moment.",
        ),
        QAItem(
            question=f"How did the story use a flashback?",
            answer=f"{hero.id} remembered yesterday, when the same thing looked normal, and that memory changed the scare into a harmless thought.",
        ),
        QAItem(
            question=f"How did repetition help?",
            answer=f"{hero.id} repeated a small calming rhyme: '{pattern.sound}, no scare; {pattern.sound}, no scare; {pattern.sound}, no scare,' and the fear got smaller.",
        ),
        QAItem(
            question=f"What was true at the end of the story?",
            answer=f"The slack {pattern.id} stayed in place, but it no longer felt haunted, and {hero.id} felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does slack mean?",
            answer="Slack means loose or hanging down without being pulled tight.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened before the present moment.",
        ),
        QAItem(
            question="Why can repeating words help a scared child?",
            answer="Repeating calm words can help a child feel steady, because the familiar rhythm makes the moment feel less frightening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)}")
    for p in world.props.values():
        lines.append(f"{p.id}: slack={p.slack} location={p.location}")
    lines.append(f"history={world.history}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(P) :- place(P).
pattern(X) :- pattern_id(X).
slack_item(X) :- prop(X), slack(X).
eerie(X) :- slack_item(X).
calm_story(P, X) :- setting(P), pattern(X), prop(X), slack(X).
#show calm_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PATTERNS:
        lines.append(asp.fact("pattern_id", pid))
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("slack", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show calm_story/2."))
    atoms = sorted(set(asp.atoms(model, "calm_story")))
    python_set = sorted((place, pid) for place in SETTINGS for pid in PATTERNS)
    if atoms == python_set:
        print(f"OK: ASP parity matches Python ({len(atoms)} calm_story facts).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", atoms)
    print("PY :", python_set)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PATTERNS[params.pattern], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show calm_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show calm_story/2."))
        print(asp.atoms(model, "calm_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, pattern in CURATED:
            params = StoryParams(
                place=place,
                pattern=pattern,
                name="Mina",
                gender="girl",
                parent="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
