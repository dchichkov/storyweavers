#!/usr/bin/env python3
"""
storyworlds/worlds/salute_pierce_foreshadowing_cautionary_rhyme_whodunit.py
============================================================================

A standalone storyworld for a tiny whodunit-ish mystery with foreshadowing,
a cautionary turn, and a rhyming ending image.

Premise:
- A child detective notices a small clue in a quiet place.
- A sealed object looks tempting to open with something sharp.
- A cautious helper warns that a pin or nail would pierce the seal and ruin the clue.
- The detective chooses the safer tool, solves the mystery, and ends with a salute.

The world is intentionally small, state-driven, and child-facing.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    clue: str = ""
    sharp: bool = False
    fragile: bool = False
    holds: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    key: str
    place: str
    scent: str
    with_chest: bool = False
    with_cabinet: bool = False


@dataclass
class Mystery:
    key: str
    question: str
    clue_word: str
    opening_word: str
    reveal: str
    rhyme_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    key: str
    label: str
    phrase: str
    risky_verb: str
    safe_verb: str
    sharp: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    key: str
    label: str
    phrase: str
    fragile: bool = False
    holds: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    prize: str
    name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "library": Setting("library", "the quiet library", "dust and paper", with_cabinet=True),
    "attic": Setting("attic", "the dusty attic", "old wood and rain", with_chest=True),
    "workshop": Setting("workshop", "the little workshop", "soap and sawdust", with_cabinet=True),
}

MYSTERIES = {
    "badge": Mystery(
        key="badge",
        question="Who left the tiny badge?",
        clue_word="badge",
        opening_word="seal",
        reveal="the badge belonged to the lost helper",
        rhyme_end="glow and know",
        tags={"badge", "clue", "metal"},
    ),
    "note": Mystery(
        key="note",
        question="Who wrote the little note?",
        clue_word="note",
        opening_word="wax seal",
        reveal="the note named the missing toy owner",
        rhyme_end="show and know",
        tags={"note", "paper", "clue"},
    ),
    "keycard": Mystery(
        key="keycard",
        question="Who dropped the keycard?",
        clue_word="keycard",
        opening_word="sticky wrap",
        reveal="the keycard opened the locked drawer",
        rhyme_end="glow and go",
        tags={"card", "clue", "paper"},
    ),
}

TOOLS = {
    "pin": Tool("pin", "a pin", "a small pin", "poke", "lift", sharp=True, tags={"sharp", "pin"}),
    "nail": Tool("nail", "a nail", "a thin nail", "poke", "slide", sharp=True, tags={"sharp", "nail"}),
    "scissors": Tool("scissors", "scissors", "small scissors", "snip", "open", sharp=True, tags={"sharp", "scissors"}),
    "key": Tool("key", "a key", "a little brass key", "turn", "turn", sharp=False, tags={"key"}),
}

PRIZES = {
    "box": Prize("box", "the clue box", "a little clue box", fragile=True, holds="the clue", tags={"box", "fragile"}),
    "envelope": Prize("envelope", "the sealed envelope", "a sealed envelope", fragile=True, holds="the clue", tags={"envelope", "fragile"}),
    "drawer": Prize("drawer", "the locked drawer", "a locked drawer", fragile=False, holds="the clue", tags={"drawer"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Eli", "Theo"]
TRAITS = ["curious", "careful", "bright", "patient", "quiet"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t in TOOLS:
                for p in PRIZES:
                    if reasonable(TOOLS[t], PRIZES[p]):
                        combos.append((s, m, t, p))
    return combos


def reasonable(tool: Tool, prize: Prize) -> bool:
    return (tool.sharp and prize.fragile) or (not tool.sharp and not prize.fragile)


def explain_rejection(tool: Tool, prize: Prize) -> str:
    return f"(No story: {tool.label} does not fit {prize.label} in a sensible whodunit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a quiet whodunit with a cautionary turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "uncle", "aunt"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)
              and (args.prize is None or c[3] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool, prize = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "uncle", "aunt"])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, prize=prize,
                       name=name, child_type=child_type,
                       helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    prize = PRIZES[params.prize]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type, role="detective", meters={}, memes={}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper", meters={}, memes={}))
    object_ent = world.add(Entity(id="object", kind="thing", type="thing", label=prize.label, phrase=prize.phrase, fragile=prize.fragile, holds=mystery.clue_word, meters={"sealed": 1.0}, memes={}, clue=mystery.reveal))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label=mystery.clue_word, phrase=f"the {mystery.clue_word}", meters={"seen": 0.0}, memes={}, clue=mystery.reveal))
    world.facts.update(setting=setting, mystery=mystery, tool=tool, prize=prize, child=child, helper=helper, object=object_ent, clue=clue, opened=False, pierced=False, solved=False)

    child.memes["curiosity"] = 1.0
    helper.memes["caution"] = 1.0

    world.say(f"In {setting.place}, {child.id} was a little {params.child_type} who liked to look for clues. {setting.scent} drifted through the room, and one small thing foreshadowed the case: a {mystery.clue_word} half-hidden near {prize.label}.")
    world.say(f"{child.id} wanted to solve the mystery: {mystery.question}.")

    world.para()
    child.memes["desire"] = 1.0
    world.say(f"{child.id} picked up {tool.label} and looked at {prize.label}.")
    if tool.sharp and prize.fragile:
        world.say(f'"Careful," {helper.id} said. "That {tool.label} could pierce the {mystery.opening_word} and ruin the clue."')
    else:
        world.say(f'"Careful," {helper.id} said. "That plan would not help the case."')

    if tool.sharp and prize.fragile:
        world.say(f"{child.id} paused, then chose to salute {helper.id} with a grin.")
        world.say(f'Instead of a poke, {child.id} used the safe way and turned the key. The {prize.label} opened cleanly.')
        child.memes["joy"] = 1.0
        world.facts["opened"] = True
        world.facts["solved"] = True
        world.say(f"Inside was the clue: {mystery.reveal}. That was the answer all along.")
        world.para()
        world.say(f'The case was closed, and {child.id} gave a neat salute. "No need to pierce what a patient turn can reveal," {helper.id} said, and the little room felt bright.')
        world.say(f"{mystery.rhyme_end}.")
    else:
        world.say(f"{child.id} used the safe tool, and the case stayed tidy.")
        world.facts["opened"] = True
        world.facts["solved"] = True
        world.say(f"The clue was plain to see: {mystery.reveal}.")
        world.para()
        world.say(f"{child.id} and {helper.id} shared a salute, and the quiet room ended with {mystery.rhyme_end}.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child in {f["setting"].place} that includes the words "salute" and "pierce".',
        f"Tell a cautious mystery story where {f['child'].id} almost uses something sharp on {f['prize'].label}, but {f['helper'].id} warns against it and the clue is solved safely.",
        f'Write a rhyming mystery with foreshadowing, a warning, and a salute at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    mystery = f["mystery"]
    prize = f["prize"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {child.id} trying to solve?",
            answer=f"{child.id} was trying to solve the mystery of {mystery.question.lower()} in the quiet room. The clue was already foreshadowed by the little {mystery.clue_word} near {prize.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id} about {tool.label}?",
            answer=f"{helper.id} warned {child.id} because that sharp tool could pierce the {mystery.opening_word} and ruin the clue. A careful choice kept the case from getting damaged.",
        ),
        QAItem(
            question=f"What did {child.id} do instead of poking at {prize.label}?",
            answer=f"{child.id} used the safe way, opened the {prize.label} cleanly, and then gave a salute. That let the clue stay whole and the mystery be solved.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the answer found, the room calm, and {mystery.rhyme_end}. The last image shows {child.id} and {helper.id} saluting after the clue was read.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a salute?", "A salute is a quick, neat way to show respect or say hello. People sometimes salute with a hand at the brow."),
        QAItem("What does pierce mean?", "To pierce means to make a hole or push through something. A sharp thing can pierce thin paper or cloth."),
        QAItem("What is foreshadowing?", "Foreshadowing is a small hint that helps you guess what may happen later in a story."),
        QAItem("What makes a story cautionary?", "A cautionary story shows a mistake or danger so the listener can learn to be careful."),
        QAItem("What is a whodunit?", "A whodunit is a mystery story where you try to figure out who did something or what happened."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} clue={e.clue!r} fragile={e.fragile} sharp={e.sharp}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.tool not in TOOLS or params.prize not in PRIZES:
        raise StoryError("Invalid params.")
    if not reasonable(TOOLS[params.tool], PRIZES[params.prize]):
        raise StoryError(explain_rejection(TOOLS[params.tool], PRIZES[params.prize]))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
puzzle_opened :- sharp(T), fragile(P), chosen(T), chosen(P).
safe_opened :- not puzzle_opened.
solved :- opened.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for k in MYSTERIES:
        lines.append(asp.fact("mystery", k))
    for k, t in TOOLS.items():
        lines.append(asp.fact("tool", k))
        if t.sharp:
            lines.append(asp.fact("sharp", k))
    for k, p in PRIZES.items():
        lines.append(asp.fact("prize", k))
        if p.fragile:
            lines.append(asp.fact("fragile", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    combos = set(valid_combos())
    if combos and len(combos) >= 4:
        pass
    # smoke test generation
    try:
        sample = generate(StoryParams(setting="library", mystery="note", tool="pin", prize="box",
                                     name="Lily", child_type="girl", helper_name="Aunt May", helper_type="aunt"))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    print("OK: generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()


def main() -> None:
    ap = argparse.ArgumentParser(description="Story world sketch.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "uncle", "aunt"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    args = ap.parse_args()

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(setting="library", mystery="note", tool="pin", prize="box", name="Lily", child_type="girl", helper_name="Aunt May", helper_type="aunt"),
            StoryParams(setting="attic", mystery="badge", tool="nail", prize="envelope", name="Leo", child_type="boy", helper_name="Dad", helper_type="father"),
            StoryParams(setting="workshop", mystery="keycard", tool="scissors", prize="drawer", name="Mia", child_type="girl", helper_name="Uncle Ben", helper_type="uncle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
