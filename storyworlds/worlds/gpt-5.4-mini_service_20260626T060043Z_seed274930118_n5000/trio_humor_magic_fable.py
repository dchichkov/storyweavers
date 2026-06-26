#!/usr/bin/env python3
"""
A small fable-style story world about a magical trio whose funny mistakes teach
a simple lesson.

Premise:
- Three friends form a tiny trio.
- One of them finds a little magic.
- The magic is useful, but only when they share it wisely.
- Their comic mischief creates a problem.
- They learn that a quick joke is fun, but cooperation is better.

The world is intentionally small and constraint-checked: a story is only
generated when the trio, the magical object, and the resolution all make sense
together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared result containers importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------

@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "joy": 0.0, "worry": 0.0})
    holding: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Object:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    enchanted: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"glow": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"importance": 0.0})


@dataclass
class Setting:
    place: str = "the meadow"
    weather: str = "bright"
    affords: set[str] = field(default_factory=lambda: {"share_magic", "test_spell"})


@dataclass
class Magic:
    name: str
    effect: str
    joke: str
    risk: str
    lesson: str
    tag: str = "magic"


@dataclass
class StoryParams:
    setting: str
    magic: str
    trio1: str
    trio2: str
    trio3: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", weather="bright", affords={"share_magic", "test_spell"}),
    "orchard": Setting(place="the orchard", weather="warm", affords={"share_magic", "test_spell"}),
    "hill": Setting(place="the hill", weather="windy", affords={"share_magic", "test_spell"}),
}

MAGICS = {
    "giggleseed": Magic(
        name="a giggleseed",
        effect="made flowers sneeze into tiny blossoms",
        joke="everybody laughed when the seed hiccuped sparkles",
        risk="it can tangle a plan into a silly mess",
        lesson="a little laughter is best when everyone gets a turn",
    ),
    "moonbell": Magic(
        name="a moonbell",
        effect="rang soft silver light across the grass",
        joke="the bell gave a ding so tiny that even the ants looked surprised",
        risk="it can make friends chase the glow instead of the job",
        lesson="sharing the light keeps the group together",
    ),
    "frogwand": Magic(
        name="a frog wand",
        effect="made pebbles hop like cheerful frogs",
        joke="the pebbles leaped so oddly that the trio snorted with laughter",
        risk="it can send the wrong thing hopping away",
        lesson="careful hands keep a funny tool from becoming trouble",
    ),
}

ANIMALS = [
    ("fox", "fox"),
    ("hare", "hare"),
    ("badger", "badger"),
    ("mouse", "mouse"),
    ("squirrel", "squirrel"),
    ("mole", "mole"),
]

TRAITS = ["clever", "brave", "bouncy", "earnest", "quick", "gentle"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def trio_names() -> list[str]:
    return ["Pip", "Milo", "Tansy", "Nori", "Jun", "Wren", "Otto", "Lumi"]


def trio_combo_ok(setting: Setting, magic: Magic) -> bool:
    return "share_magic" in setting.affords and "test_spell" in setting.affords and bool(magic.name)


def select_setting_and_magic(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    settings = [args.setting] if getattr(args, "setting", None) else list(SETTINGS)
    magics = [args.magic] if getattr(args, "magic", None) else list(MAGICS)
    candidates = [(s, m) for s in settings for m in magics if trio_combo_ok(SETTINGS[s], MAGICS[m])]
    if not candidates:
        raise StoryError("No valid setting/magic combination matches the given options.")
    return rng.choice(candidates)


def choose_animals(rng: random.Random) -> tuple[str, str, str]:
    chosen = rng.sample(ANIMALS, 3)
    return chosen[0][0], chosen[1][0], chosen[2][0]


def choose_names(rng: random.Random) -> tuple[str, str, str]:
    return tuple(rng.sample(trio_names(), 3))  # type: ignore[return-value]


def name_for_animal(animal: str) -> str:
    return animal


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    magic = MAGICS[params.magic]
    a1 = world.add(Character(id=params.trio1, type=params.trio1, label=params.trio1, traits=["trio-leader"]))
    a2 = world.add(Character(id=params.trio2, type=params.trio2, label=params.trio2, traits=["trio-member"]))
    a3 = world.add(Character(id=params.trio3, type=params.trio3, label=params.trio3, traits=["trio-member"]))
    relic = world.add(Object(id="relic", type="magic-item", label=magic.name, owner=a1.id, enchanted=True))
    world.facts.update(chars=[a1, a2, a3], relic=relic, magic=magic, trio=[a1.id, a2.id, a3.id])
    return world


# ---------------------------------------------------------------------------
# Causal narration
# ---------------------------------------------------------------------------

def opening(world: World) -> None:
    a1, a2, a3 = world.facts["chars"]
    world.say(
        f"Once in {world.setting.place}, there lived a small trio: {a1.label}, {a2.label}, and {a3.label}."
    )
    world.say(
        f"They were quick to laugh, and each one thought the others were the cleverest part of the group."
    )


def discovery(world: World) -> None:
    a1, a2, a3 = world.facts["chars"]
    magic: Magic = world.facts["magic"]
    relic: Object = world.facts["relic"]
    a1.memes["joy"] += 1
    relic.meters["glow"] += 1
    world.say(
        f"One day, {a1.label} found {relic.label} tucked beneath a root, and it shimmered with soft magic."
    )
    world.say(
        f"When {a1.label} tapped it, {magic.effect}, and the whole trio blinked in surprise."
    )


def playful_problem(world: World) -> None:
    a1, a2, a3 = world.facts["chars"]
    magic: Magic = world.facts["magic"]
    relic: Object = world.facts["relic"]
    a2.memes["worry"] += 1
    relic.meters["mess"] += 1
    world.say(
        f"{a2.label} wanted to show off, so the trio tried the spell again and again for a joke."
    )
    world.say(
        f"Soon the magic got wobbly; {magic.risk}, and even the birds looked as if they were laughing at them."
    )
    world.say(
        f"A puff of sparkle blew the wrong way, and the three friends ended up with a very silly, tangled plan."
    )


def wise_turn(world: World) -> None:
    a1, a2, a3 = world.facts["chars"]
    magic: Magic = world.facts["magic"]
    a3.memes["pride"] += 1
    a3.memes["joy"] += 1
    world.say(
        f"Then {a3.label} paused and said, 'A trick is fun, but a trio is stronger when it shares.'"
    )
    world.say(
        f"They took turns holding {world.facts['relic'].label}, and the magic settled into a neat, bright glow."
    )
    world.say(
        f"At once, the spell behaved: {magic.joke}, and the three of them laughed in relief instead of trouble."
    )


def resolution(world: World) -> None:
    magic: Magic = world.facts["magic"]
    a1, a2, a3 = world.facts["chars"]
    world.say(
        f"By evening, {world.setting.place} was peaceful again, and the trio had finished their task together."
    )
    world.say(
        f"They learned that {magic.lesson}, and that a shared smile is safer than a selfish stunt."
    )
    world.say(
        f"So the little friends went home side by side, with one glowing treasure and three happier hearts."
    )


def build_story(world: World) -> None:
    opening(world)
    world.para()
    discovery(world)
    playful_problem(world)
    world.para()
    wise_turn(world)
    resolution(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    magic: Magic = world.facts["magic"]
    trio = world.facts["chars"]
    return [
        f"Write a short fable about a trio who finds {magic.name} and learns to share it wisely.",
        f"Tell a funny little story where {trio[0].label}, {trio[1].label}, and {trio[2].label} make a magical mistake, then fix it together.",
        f"Create a child-friendly fable with humor, magic, and a lesson about cooperation in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a1, a2, a3 = world.facts["chars"]
    magic: Magic = world.facts["magic"]
    return [
        QAItem(
            question=f"Who were the three friends in the story?",
            answer=f"The trio was {a1.label}, {a2.label}, and {a3.label}.",
        ),
        QAItem(
            question=f"What magical thing did they find?",
            answer=f"They found {magic.name}, which could make something funny and bright happen.",
        ),
        QAItem(
            question=f"What went wrong when they used the magic too much?",
            answer=f"The spell became wobbly and silly, so the plan turned messy instead of helpful.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They slowed down, took turns, and shared the magic so it behaved well again.",
        ),
        QAItem(
            question=f"What lesson did the trio learn?",
            answer=magic.lesson.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    magic: Magic = world.facts["magic"]
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses animals or simple characters to teach a lesson.",
        ),
        QAItem(
            question="Why can magic be funny in a story?",
            answer="Magic can be funny when it does something surprising, like making a tiny mistake or a silly surprise.",
        ),
        QAItem(
            question="Why is sharing important in a group?",
            answer="Sharing helps everyone help each other, so one friend does not have to do everything alone.",
        ),
        QAItem(
            question="What makes a trio?",
            answer="A trio is a group of three.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A trio is valid when there are exactly three characters and a valid magical item.
valid_story(S, M) :- setting(S), magic(M), trio_ok(S, M).

% This world is intentionally small: any listed setting and magic are allowed.
trio_ok(S, M) :- setting(S), magic(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MAGICS if trio_combo_ok(SETTINGS[s], MAGICS[m])}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny trio fable with humor and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting, magic = select_setting_and_magic(args, rng)
    trio = choose_names(rng)
    return StoryParams(setting=setting, magic=magic, trio1=trio[0], trio2=trio[1], trio3=trio[2])


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    build_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        if isinstance(ent, Character):
            lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes}")
        else:
            lines.append(f"{ent.id}: label={ent.label} meters={ent.meters} memes={ent.memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid setting/magic pairs:\n")
        for s, m in pairs:
            print(f"  {s:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for m in MAGICS:
                params = StoryParams(setting=s, magic=m, trio1="Pip", trio2="Milo", trio3="Tansy")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
