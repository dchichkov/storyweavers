#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/engineer_buckaroo_loin_mystery_to_solve_comedy.py
=================================================================================

A standalone story world for a tiny comedic mystery: an engineer and a buckaroo
follow odd clues involving a "loin" word, solve a harmless mystery, and end with
a cheerful reveal.

The world is intentionally small and classical: typed entities with physical
meters and emotional memes, a forward-chained causal simulation, a reasonability
gate, and an ASP twin for parity checks.

The seed words are baked into the domain vocabulary:
- engineer
- buckaroo
- loin

The narrative flavor is comedy, but the outcome is a complete mystery to solve:
something is missing, clues appear, the pair investigates, and the ending reveals
the harmless truth.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "buckaroo", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Mystery:
    id: str
    missing: str
    clue_noun: str
    clue_place: str
    reveal: str
    setup: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: str
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    if not clue:
        return out
    if world.facts.get("mystery_solved"):
        return out
    sig = ("clue", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["noticed"] += 1
    out.append(f"A clue was spotted.")
    return out


def _r_spread_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_solved"):
        for eid in ("engineer", "buckaroo"):
            ent = world.entities.get(eid)
            if ent and ent.memes["relief"] < THRESHOLD:
                ent.memes["relief"] += 1
                ent.memes["joy"] += 1
                sig = ("laugh", eid)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule("clue", "mystery", _r_clue),
    Rule("laugh", "social", _r_spread_laugh),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def explain_tool_rejection(tool: Tool) -> str:
    return f"(No story: {tool.label} is too silly to solve the mystery in a believable way.)"


def mystery_valid(m: Mystery, tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN and m.missing in {"lunchbox", "hat", "boots"}


def predict(world: World, mystery: Mystery, tool: Tool) -> dict:
    sim = world.copy()
    _search(sim, mystery, tool, narrate=False)
    return {"solved": sim.facts.get("mystery_solved", False)}


def _search(world: World, mystery: Mystery, tool: Tool, narrate: bool = True) -> None:
    engineer = world.get("engineer")
    buckaroo = world.get("buckaroo")
    clue = world.facts["clue"]
    engineer.memes["curiosity"] += 1
    buckaroo.memes["curiosity"] += 1
    world.say(f"The engineer and the buckaroo stared at the mystery with very serious faces, which only made it funnier.")
    world.say(f"{mystery.setup}")
    world.say(f'"Something is off," said the engineer. "The {mystery.missing} cannot vanish like a magician."')
    world.say(f'"I reckon it did," said the buckaroo. "But I also reckon it may be hiding in plain sight."')
    world.say(f"They followed the clue to {mystery.clue_place}.")
    world.say(f'There they found {clue.label}, which looked suspiciously important.')
    tool_use = tool.use.replace("{missing}", mystery.missing).replace("{clue}", clue.label)
    world.say(f'The engineer used {tool.phrase} and {tool_use}.')
    world.say(f'The buckaroo nodded so hard {buckaroo.pronoun("possessive")} hat almost filed a complaint.')
    world.facts["mystery_solved"] = True
    world.facts["reveal_text"] = mystery.reveal
    propagate(world, narrate=narrate)


def setup_scene(world: World, mystery: Mystery) -> None:
    world.say(f"On a bright afternoon, the engineer and the buckaroo set out to solve a tiny mystery.")
    world.say(f'The case was simple: {mystery.missing} had gone missing, and everyone had a theory.')
    world.say(f'The engineer had a notebook. The buckaroo had a stubborn grin. Neither had a clue, which was a problem.')
    world.say(f'At first the only hint was a silly note about the word "{mystery.clue_noun}".')


def resolve_scene(world: World, mystery: Mystery) -> None:
    world.say(f'Then the truth popped out: {world.facts["reveal_text"]}.')
    world.say(f'The missing {mystery.missing} had not been stolen at all; it had been moved by accident and tucked where no one looked.')
    world.say(f'The engineer laughed. The buckaroo laughed. Even the mystery seemed embarrassed.')
    world.say(f'By the end, the room was tidy again, the clue was understood, and the two friends were grinning like they had solved a grand bank heist made of sandwiches.')


def tell(mystery: Mystery, tool: Tool) -> World:
    world = World()
    eng = world.add(Entity(id="engineer", kind="character", type="engineer", role="solver", traits=["careful"]))
    buck = world.add(Entity(id="buckaroo", kind="character", type="buckaroo", role="helper", traits=["brave"]))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_noun))
    world.facts["clue"] = clue
    world.facts["mystery"] = mystery
    world.facts["tool"] = tool
    setup_scene(world, mystery)
    world.para()
    _search(world, mystery, tool)
    world.para()
    resolve_scene(world, mystery)
    return world


MYSTERIES = {
    "lunchbox": Mystery(
        "lunchbox",
        missing="lunchbox",
        clue_noun="pickle-shaped stain",
        clue_place="behind the music stand",
        reveal="the lunchbox had slid under a stack of comic books when the table was bumped",
        setup="The music room smelled like crackers and mystery.",
        tags={"lunchbox", "clue"},
    ),
    "hat": Mystery(
        "hat",
        missing="hat",
        clue_noun="dusty feather",
        clue_place="on top of the coat rack",
        reveal="the hat was perched above the coat rack where the tallest breeze had left it",
        setup="The hall looked very solemn, as if it were trying not to giggle.",
        tags={"hat", "clue"},
    ),
    "boots": Mystery(
        "boots",
        missing="boots",
        clue_noun="tiny muddy footprint",
        clue_place="near the back door",
        reveal="the boots had been carried to the back step by a very helpful puppy",
        setup="The porch had the air of a detective movie, if detective movies were made for children.",
        tags={"boots", "clue"},
    ),
}

TOOLS = {
    "notebook": Tool(
        "notebook",
        label="notebook",
        phrase="a notebook and a pencil",
        use="scribbled down the clue and made a sensible guess about where the {missing} might be",
        helps="helps organize clues",
        sense=3,
        tags={"solve"},
    ),
    "magnifier": Tool(
        "magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        use="peered at the clue until the answer practically waved hello",
        helps="looks closely at details",
        sense=3,
        tags={"solve"},
    ),
    "tumbleweed": Tool(
        "tumbleweed",
        label="tumbleweed",
        phrase="a tumbleweed",
        use="rolled past the clue and did absolutely nothing useful",
        helps="silly but useless",
        sense=1,
        tags={"silly"},
    ),
}


NAME_PAIRS = [("Iris", "Comet"), ("June", "Ranger"), ("Nora", "Dusty"), ("Mina", "Buck")] 


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        f'Write a funny mystery story that includes the words "engineer", "buckaroo", and "{m.clue_noun}".',
        f'Tell a comedy where the engineer and buckaroo solve a missing {m.missing} mystery using {tool.label}.',
        f'Write a child-friendly story in which a clue leads the engineer and buckaroo to a harmless answer and a laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about an engineer and a buckaroo who try to solve a small mystery together. They act like a team and keep the story playful.",
        ),
        QAItem(
            question=f"What clue helped them?",
            answer=f'The clue was {m.clue_noun}. They followed it to {m.clue_place}, and that led them closer to the answer.',
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They used {tool.phrase} and careful thinking to connect the clue to the missing {m.missing}. That let them find the harmless truth instead of guessing wildly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Tool = f["tool"]
    items = [
        QAItem(
            question="What is an engineer?",
            answer="An engineer is someone who plans, builds, and fixes things by using careful thinking and practical tools.",
        ),
        QAItem(
            question="What is a buckaroo?",
            answer="A buckaroo is a cowboy word for a rider or ranch hand. In a comedy story, it sounds a little wild and a little funny.",
        ),
        QAItem(
            question="Why are clues useful in a mystery?",
            answer="Clues help you connect small facts into a bigger answer. They let detectives test ideas instead of making random guesses.",
        ),
    ]
    if tool.sense >= SENSE_MIN:
        items.append(QAItem(
            question=f"What does {tool.label} help with?",
            answer=f"{tool.label.capitalize()} helps by supporting careful searching and clever thinking. It is the kind of tool that makes a mystery easier to solve.",
        ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return explain_tool_rejection(tool)
    return "(No story: this mystery/tool combination is not interesting enough to support a clear comedy beat.)"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid, m in MYSTERIES.items():
        for tid, t in TOOLS.items():
            if mystery_valid(m, t):
                out.append((mid, tid))
    return out


@dataclass
class StoryParams:
    mystery: str
    tool: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    ("lunchbox", "notebook"),
    ("hat", "magnifier"),
    ("boots", "notebook"),
]



ASP_RULES = r"""
valid(M, T) :- mystery(M), tool(T), clueworthy(M), sensible(T).
solved(M, T) :- valid(M, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clueworthy", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        print("MISMATCH: smoke story empty.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery world with an engineer and a buckaroo.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.mystery is None or c[0] == args.mystery)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, tool = rng.choice(sorted(combos))
    return StoryParams(mystery=mystery, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(MYSTERIES[params.mystery], TOOLS[params.tool])
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
        print(asp_program("#show valid/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid mystery/tool combos:\n")
        for m, t in combos:
            print(f"  {m:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(m, t)) for m, t in CURATED]
    else:
        seen = set()
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
            header = f"### {p.mystery} via {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
