#!/usr/bin/env python3
"""
storyworlds/worlds/certify_misunderstanding_curiosity_mystery.py
=================================================================

A small mystery story world about a child, a misunderstanding, and a
curiosity that turns into a solved puzzle.

Premise:
- Someone wants a thing certified as real, safe, or complete.
- A misunderstanding makes the situation feel mysterious.
- Curiosity leads to checking clues, comparing facts, and finding the truth.
- The ending proves what changed in the world.

This world keeps the tone gentle, concrete, and child-facing while modeling
state with physical meters and emotional memes.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
    place: str = "the little town library"
    indoor: bool = True
    affordance: str = "checking clues"


@dataclass
class Mystery:
    id: str
    title: str
    clue_word: str
    verb: str
    investigation: str
    misunderstood: str
    resolve: str
    place_tag: str = "library"


@dataclass
class Seal:
    id: str
    label: str
    phrase: str
    what_it_proves: str
    belongs_to: str
    requires: str
    clue: str


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps_with: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _get_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _get_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _set_meme(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


@dataclass
class Rule:
    name: str
    apply: callable


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    if _get_meme(child, "misunderstanding") < THRESHOLD:
        return out
    sig = ("confusion", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meme(child, "worry", 1.0)
    out.append(f"{child.label} felt puzzled and looked at the clue again.")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    clue = world.facts["clue"]
    if _get_meme(child, "curiosity") < THRESHOLD:
        return out
    if _get_meter(clue, "seen") < THRESHOLD:
        return out
    sig = ("curious", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meter(clue, "examined", 1.0)
    out.append(f"{child.label} leaned closer, because curious eyes notice tiny things.")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    seal = world.facts["seal"]
    tool = world.facts["tool"]
    if _get_meter(tool, "used") < THRESHOLD:
        return out
    if _get_meter(seal, "found") < THRESHOLD:
        return out
    sig = ("truth", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_meme(child, "misunderstanding", 0.0)
    _add_meme(child, "relief", 1.0)
    out.append(f"The pieces finally fit together, and the mystery made sense.")
    return out


CAUSAL_RULES = [
    Rule("confusion", _r_confusion),
    Rule("curiosity", _r_curiosity),
    Rule("truth", _r_truth),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_is_important(mystery: Mystery, seal: Seal) -> bool:
    return mystery.clue_word == seal.clue


def valid_combo(mystery: Mystery, seal: Seal, tool: Tool) -> bool:
    return clue_is_important(mystery, seal) and tool.helps_with == seal.requires


SETTINGS = {
    "library": Setting(place="the little town library", indoor=True, affordance="checking clues"),
    "museum": Setting(place="the quiet museum hall", indoor=True, affordance="checking clues"),
    "garden": Setting(place="the moonlit garden shed", indoor=False, affordance="checking clues"),
}

MYSTERIES = {
    "stamp": Mystery(
        id="stamp",
        title="the missing stamp",
        clue_word="stamp",
        verb="certify the notice",
        investigation="look for the stamp on the desk and shelves",
        misunderstood="a missing stamp looked like a forbidden secret",
        resolve="the stamp was inside a book",
        place_tag="library",
    ),
    "key": Mystery(
        id="key",
        title="the lost key",
        clue_word="key",
        verb="certify the box",
        investigation="look under the bench and behind the curtain",
        misunderstood="a hidden key sounded like a mystery on purpose",
        resolve="the key was hanging on a ribbon",
        place_tag="museum",
    ),
    "note": Mystery(
        id="note",
        title="the unsigned note",
        clue_word="note",
        verb="certify the message",
        investigation="check the paper, the basket, and the window ledge",
        misunderstood="an unsigned note made everyone whisper",
        resolve="the note belonged to a friend",
        place_tag="garden",
    ),
}

SEALS = {
    "stamp": Seal(
        id="stamp",
        label="red stamp",
        phrase="a bright red stamp",
        what_it_proves="the notice was official",
        belongs_to="notice",
        requires="reading",
        clue="stamp",
    ),
    "key": Seal(
        id="key",
        label="small brass key",
        phrase="a small brass key",
        what_it_proves="the box could be opened the right way",
        belongs_to="box",
        requires="searching",
        clue="key",
    ),
    "note": Seal(
        id="note",
        label="signed note",
        phrase="a signed note",
        what_it_proves="the message came from a real friend",
        belongs_to="message",
        requires="reading",
        clue="note",
    ),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="magnifying glass", use="look closely", helps_with="reading"),
    "lantern": Tool(id="lantern", label="little lantern", use="see into dark corners", helps_with="searching"),
}

NAMES = ["Mina", "Leo", "Nora", "Owen", "Pia", "Tess", "Sam", "June"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "careful", "brave", "gentle"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    seal: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about certify, misunderstanding, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, myst in MYSTERIES.items():
            if myst.place_tag != sid:
                continue
            for seal_id, seal in SEALS.items():
                for tool_id, tool in TOOLS.items():
                    if valid_combo(myst, seal, tool):
                        out.append((sid, mid, seal_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.seal is None or c[2] == args.seal)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    setting, mystery, seal = rng.choice(sorted(combos))
    tool = "magnifier" if SEALS[seal].requires == "reading" else "lantern"
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, seal=seal, tool=tool,
                       name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, mystery: Mystery, seal: Seal, tool: Tool,
         name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    child.traits = ["little", trait]
    caretaker = world.add(Entity(id="parent", kind="character", type=parent, label=f"the {parent}"))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue_word, phrase=mystery.clue_word))
    seal_ent = world.add(Entity(id="seal", type="seal", label=seal.label, phrase=seal.phrase))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.label))
    world.facts.update(child=child, parent=caretaker, clue=clue, seal=seal_ent, tool=tool_ent,
                       mystery=mystery, setting=setting, seal_def=seal, tool_def=tool)

    world.say(f"{child.label} was a little {trait} {gender} who loved questions.")
    world.say(f"{child.pronoun('subject').capitalize()} kept thinking about {mystery.title}, because {mystery.misunderstood}.")
    world.say(f"One day, {child.label} and {child.pronoun('possessive')} {parent} went to {setting.place}.")
    world.para()
    world.say(f"They wanted to {mystery.verb}, but first they had to find {seal.phrase}.")
    _add_meme(child, "curiosity", 1.0)
    _add_meme(child, "misunderstanding", 1.0)
    _add_meter(clue, "seen", 1.0)
    _add_meter(seal_ent, "found", 0.0)
    propagate(world, narrate=True)
    world.say(f"{child.label} did not want the day to stay confusing, so {child.pronoun('subject')} started to {mystery.investigation}.")
    _add_meter(seal_ent, "found", 1.0)
    _add_meter(tool_ent, "used", 1.0)
    _add_meme(child, "curiosity", 1.0)
    world.para()
    propagate(world, narrate=True)
    world.say(f"At last, {mystery.resolve}, and that certified what everyone needed to know.")
    world.say(f"{child.label} smiled, because the mystery was solved and the answer was real.")
    world.facts["resolved"] = _get_meme(child, "misunderstanding") < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    myst = f["mystery"]
    return [
        f'Write a gentle mystery story for a young child where {child.label} learns to "certify" something after a misunderstanding.',
        f"Tell a short story about curiosity helping {child.label} solve {myst.title} at {world.setting.place}.",
        f"Write a child-friendly mystery that begins with confusion, follows clues, and ends with a clear certified answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    myst: Mystery = f["mystery"]
    seal: Seal = f["seal_def"]
    tool: Tool = f["tool_def"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.label}, a little child who loves curiosity and solving mysteries with {parent.label}.",
        ),
        QAItem(
            question=f"What made the first part of the story confusing?",
            answer=f"It was confusing because {myst.misunderstood}, so {child.label} had a real misunderstanding to sort out.",
        ),
        QAItem(
            question=f"What did {child.label} need in order to certify the answer?",
            answer=f"{child.label} needed {seal.phrase} and a {tool.label} to check the clues carefully.",
        ),
        QAItem(
            question=f"How did curiosity help in the middle of the story?",
            answer=f"Curiosity made {child.label} keep looking closely, so {child.pronoun('subject')} did not stop when the first idea was wrong.",
        ),
        QAItem(
            question=f"What finally proved the truth?",
            answer=f"The truth was proven when {myst.resolve}, and that certified what everyone needed to know.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "certify": [
        QAItem(
            question="What does it mean to certify something?",
            answer="To certify something means to say it is officially true, real, or approved after checking it carefully.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but the real meaning is different.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that you need clues to solve.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["certify"] + WORLD_KNOWLEDGE["curiosity"] + WORLD_KNOWLEDGE["misunderstanding"] + WORLD_KNOWLEDGE["mystery"]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
    for mid, myst in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("place_tag", mid, myst.place_tag))
        lines.append(asp.fact("clue_word", mid, myst.clue_word))
    for seal_id, seal in SEALS.items():
        lines.append(asp.fact("seal", seal_id))
        lines.append(asp.fact("seal_clue", seal_id, seal.clue))
        lines.append(asp.fact("requires", seal_id, seal.requires))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("helps_with", tool_id, tool.helps_with))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is compatible when the setting matches and the seal/tool pair fits.
compatible(S, M, Seal, Tool) :- mystery(M), setting(S), place_tag(M, S),
                                 seal(Seal), tool(Tool),
                                 clue_word(M, C), seal_clue(Seal, C),
                                 requires(Seal, R), helps_with(Tool, R).

#show compatible/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((s, m, seal) for s, m, seal in valid_combos())
    cl = set((s, m, seal) for s, m, seal, _tool in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SEALS[params.seal],
                 TOOLS[params.tool], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(setting="library", mystery="stamp", seal="stamp", tool="magnifier",
                name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="museum", mystery="key", seal="key", tool="lantern",
                name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="garden", mystery="note", seal="note", tool="magnifier",
                name="Nora", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        for s, m, seal, tool in rows:
            print(f"{s:8} {m:8} {seal:8} {tool:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
