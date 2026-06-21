#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py
====================================================================

A tiny fable-like storyworld about an apple, a bit of magic, and a rhyme that
teaches a gentle lesson. The domain is small and classical: a child, a parent,
an orchard, a single apple, a spell, and a speaking lesson. State changes drive
the story, and the ending proves what changed.

The seed prompt asks for: apple + Magic + Rhyme + Dialogue + Fable style.
This world rebuilds that premise as a reasoned simulation: a character wants a
special apple, magic makes the apple act strangely, a rhyme reveals the problem,
dialogue guides the fix, and the fable ends with a lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py
    python storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/apple_magic_rhyme_dialogue_fable.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Orchard:
    id: str
    name: str
    trees: int
    blossoms: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Apple:
    id: str
    label: str
    phrase: str
    ripe: bool = True
    magical: bool = False
    spoken: bool = False
    glowing: bool = False
    shared: bool = False
    eaten: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Spell:
    id: str
    name: str
    effect: str
    power: int
    safe: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rhyme:
    id: str
    couplet: str
    lesson: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.apple: Optional[Apple] = None
        self.orchard: Optional[Orchard] = None
        self.spell: Optional[Spell] = None
        self.rhyme: Optional[Rhyme] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.apple = copy.deepcopy(self.apple)
        c.orchard = copy.deepcopy(self.orchard)
        c.spell = copy.deepcopy(self.spell)
        c.rhyme = copy.deepcopy(self.rhyme)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_glow(world: World) -> list[str]:
    out = []
    if world.apple and world.apple.meters["magic"] >= THRESHOLD and ("glow",) not in world.fired:
        world.fired.add(("glow",))
        world.apple.glowing = True
        world.apple.meters["glow"] += 1
        out.append("The apple began to glow like a tiny lantern.")
    return out


def _r_speak(world: World) -> list[str]:
    out = []
    if world.apple and world.apple.glowing and not world.apple.spoken and ("speak",) not in world.fired:
        world.fired.add(("speak",))
        world.apple.spoken = True
        world.apple.memes["voice"] += 1
        out.append("It seemed to ask for words as bright as its shine.")
    return out


def _r_shared(world: World) -> list[str]:
    out = []
    if world.apple and world.apple.spoken and not world.apple.shared and ("share",) not in world.fired:
        world.fired.add(("share",))
        world.apple.shared = True
        out.append("The child felt it was kinder to share the apple than to hide it.")
    return out


CAUSAL_RULES = [Rule("glow", _r_glow), Rule("speak", _r_speak), Rule("share", _r_shared)]


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


def predict_magic(world: World) -> dict:
    sim = world.copy()
    if sim.apple:
        sim.apple.meters["magic"] += 1
    propagate(sim, narrate=False)
    return {"glowing": bool(sim.apple and sim.apple.glowing), "shared": bool(sim.apple and sim.apple.shared)}


def setup(world: World, child: Entity, elder: Entity, orchard: Orchard, apple: Apple) -> None:
    child.memes["curiosity"] += 1
    elder.memes["patience"] += 1
    world.say(
        f"In a small orchard with {orchard.trees} apple trees, {child.id} found a single apple "
        f"resting beneath the leaves."
    )
    world.say(
        f'{child.id} smiled. "{apple.phrase}," {child.pronoun()} said, and {elder.id} answered, '
        f'"A kind heart keeps a fable sweet."'
    )


def cast_magic(world: World, child: Entity, spell: Spell, apple: Apple) -> None:
    child.memes["wonder"] += 1
    apple.meters["magic"] += 1
    world.say(
        f'{child.id} whispered the spell {spell.name}. At once, the apple felt warm with {spell.effect}.'
    )
    propagate(world, narrate=True)


def rhyme_warning(world: World, elder: Entity, rhyme: Rhyme, apple: Apple) -> None:
    elder.memes["warning"] += 1
    world.say(
        f'{elder.id} said a rhyme: "{rhyme.couplet}"'
    )
    world.say(f'Then {elder.id} added, "{rhyme.lesson}"')


def choose_kindness(world: World, child: Entity, elder: Entity, apple: Apple) -> None:
    child.memes["kindness"] += 1
    apple.shared = True
    world.say(
        f'{child.id} listened, and {child.pronoun()} nodded. "We can share it," {child.pronoun()} said.'
    )
    world.say(
        f"{child.id} placed the apple in the center of the table so both of them could enjoy it."
    )


def ending(world: World, child: Entity, elder: Entity, apple: Apple) -> None:
    child.memes["peace"] += 1
    elder.memes["peace"] += 1
    if apple.glowing:
        world.say(
            f"The apple still shone softly, but now it shone between them, not in one small hand."
        )
    if apple.shared:
        world.say(
            f"In the end, {child.id} and {elder.id} laughed together, and the little orchard felt wiser."
        )
    else:
        world.say(
            f"In the end, the apple stayed still, and both learned that wonder is best when it is shared."
        )


def tell(orchard: Orchard, spell: Spell, rhyme: Rhyme, child_name: str = "Milo",
         child_type: str = "boy", elder_name: str = "Mira", elder_type: str = "girl") -> World:
    world = World()
    child = world.add(Entity(child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder"))
    apple = Apple("apple", "apple", "a shining apple")
    world.apple = apple
    world.orchard = orchard
    world.spell = spell
    world.rhyme = rhyme

    setup(world, child, elder, orchard, apple)
    world.para()
    cast_magic(world, child, spell, apple)
    rhyme_warning(world, elder, rhyme, apple)
    if predict_magic(world)["glowing"]:
        choose_kindness(world, child, elder, apple)
    world.para()
    ending(world, child, elder, apple)

    world.facts.update(
        child=child,
        elder=elder,
        orchard=orchard,
        spell=spell,
        rhyme=rhyme,
        apple=apple,
        glowing=apple.glowing,
        shared=apple.shared,
    )
    return world


ORCHARDS = {
    "green_hill": Orchard("green_hill", "the green hill orchard", 7, blossoms=True),
    "red_lane": Orchard("red_lane", "the red lane orchard", 5, blossoms=False),
}

SPELLS = {
    "spark": Spell("spark", "Sparkbright", "a warm sparkle", 1, safe=True),
    "glimmer": Spell("glimmer", "Glimmerglow", "a gentle glimmer", 2, safe=True),
}

RHYMES = {
    "share": Rhyme("share", "One apple bright, two hearts at ease;", "A good thing grows when people share."),
    "kind": Rhyme("kind", "A sweet surprise can start a smile;", "The kindest magic travels far."),
}

GIRL_NAMES = ["Mira", "Luna", "Nora", "Ava", "Ivy"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Eli", "Noah"]
TRAITS = ["curious", "gentle", "thoughtful", "patient"]


@dataclass
@dataclass
class StoryParams:
    orchard: str
    spell: str
    rhyme: str
    child: str
    child_type: str
    elder: str
    elder_type: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(o, s, r) for o in ORCHARDS for s in SPELLS for r in RHYMES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about an apple, magic, rhyme, and dialogue.")
    ap.add_argument("--orchard", choices=ORCHARDS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["boy", "girl"])
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
    combos = [c for c in valid_combos()
              if (args.orchard is None or c[0] == args.orchard)
              and (args.spell is None or c[1] == args.spell)
              and (args.rhyme is None or c[2] == args.rhyme)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    orchard, spell, rhyme = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["boy", "girl"])
    elder_type = args.elder_type or ("girl" if child_type == "boy" else "boy")
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(GIRL_NAMES if elder_type == "girl" else BOY_NAMES)
    if elder == child:
        elder = (GIRL_NAMES if elder_type == "girl" else BOY_NAMES)[0]
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(orchard, spell, rhyme, child, child_type, elder, elder_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a young child that includes the word "apple" and a little magic.',
        f"Tell a story where {f['child'].id} and {f['elder'].id} talk about a magical apple in {f['orchard'].name}.",
        f'Write a gentle rhyming fable where "{f["rhyme"].couplet}" appears as dialogue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    apple = f["apple"]
    child = f["child"]
    elder = f["elder"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question="What happened when the child used the spell?",
            answer=f"The apple began to glow with a warm magic light. That made the child slow down and listen when the elder spoke."
        ),
        QAItem(
            question="Why did the elder tell a rhyme?",
            answer=f"The rhyme was a warning and a lesson. It helped the child understand that the apple should be shared kindly instead of kept selfishly."
        ),
        QAItem(
            question="What did the child do at the end?",
            answer=f"{child.id} shared the apple and put it where both children could enjoy it. That choice matched the lesson in the rhyme and made the ending peaceful."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an orchard?", "An orchard is a place where people grow fruit trees, like apple trees."),
        QAItem("What is a fable?", "A fable is a short story that teaches a lesson, often with a simple choice between selfishness and kindness."),
        QAItem("Why can rhyme help a story?", "Rhyme makes a line easier to remember, so a lesson can sound lively and stick in the mind."),
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
    if world.orchard:
        lines.append(f"  orchard  : {world.orchard}")
    if world.spell:
        lines.append(f"  spell    : {world.spell}")
    if world.rhyme:
        lines.append(f"  rhyme    : {world.rhyme}")
    if world.apple:
        lines.append(f"  apple    : glowing={world.apple.glowing} shared={world.apple.shared} spoken={world.apple.spoken}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("green_hill", "spark", "share", "Milo", "boy", "Mira", "girl", "curious"),
    StoryParams("red_lane", "glimmer", "kind", "Ava", "girl", "Theo", "boy", "thoughtful"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for o in ORCHARDS:
        lines.append(asp.fact("orchard", o))
    for s in SPELLS:
        lines.append(asp.fact("spell", s))
    for r in RHYMES:
        lines.append(asp.fact("rhyme", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(O,S,R) :- orchard(O), spell(S), rhyme(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: default generation failed.")
    else:
        print("OK: normal generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ORCHARDS[params.orchard], SPELLS[params.spell], RHYMES[params.rhyme],
        params.child, params.child_type, params.elder, params.elder_type
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for o, s, r in asp_valid_combos():
            print(f"  {o:10} {s:8} {r}")
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
            if sample.story not in seen:
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
            header = f"### {p.child} and {p.elder}: apple, magic, and a fable lesson"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
