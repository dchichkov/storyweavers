#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nanny_quiz_moat_teamwork_quest_pirate_tale.py
==============================================================================

A standalone storyworld script for a tiny pirate-tale domain:

- A child-led pirate quest needs help crossing a moat.
- A nanny notices the risk, offers a teamwork plan, and turns the danger into a
  playful quiz.
- The story supports a few constraint-checked variants, all driven by world
  state: quest setup, moat tension, teamwork turn, and a safe ending image.

Seed words and features:
- nanny
- quiz
- moat
- Teamwork
- Quest
- Style: Pirate Tale
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
        female = {"girl", "mother", "mom", "woman", "nanny"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"nanny": "nanny"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    helper: str
    goal: str
    moat_name: str
    treasure_name: str
    ending: str

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
class Question:
    id: str
    label: str
    answer: str

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
class Response:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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
class Rule:
    name: str
    tag: str
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["splash"] < THRESHOLD:
            continue
        sig = ("wet", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["wet"] += 1
        out.append("__wet__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamed") and not world.facts.get("teamwork_fired"):
        world.facts["teamwork_fired"] = True
        for e in list(world.entities.values()):
            if e.role in {"child", "nanny"}:
                e.memes["hope"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("teamwork", "social", _r_teamwork)]


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


def hazard_at_risk(tool: str, target: str) -> bool:
    return tool == "planks" and target == "moat"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for tool in TOOLS:
            for target in TARGETS:
                if hazard_at_risk(tool, target):
                    combos.append((theme, tool, target))
    return combos


def reasonableness_gate(args: argparse.Namespace) -> None:
    if args.target and args.target != "moat":
        raise StoryError("(No story: this world needs a moat so the quest has a real crossing problem.)")
    if args.tool and args.target and not hazard_at_risk(args.tool, args.target):
        raise StoryError("(No story: that tool does not create a meaningful moat-crossing problem.)")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(No story: the chosen response is too flimsy for this quest.)")


def _do_hazard(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["splash"] += 1
    propagate(world, narrate=narrate)


def tell(theme: Theme, tool: str, target: str, response: Response,
         child_name: str = "Pip", child_gender: str = "boy",
         nanny_name: str = "Nanny June", nanny_gender: str = "nanny") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    nanny = world.add(Entity(id=nanny_name, kind="character", type=nanny_gender, role="nanny"))
    moat = world.add(Entity(id="moat", kind="thing", type="moat", label="the moat"))
    bridge = world.add(Entity(id="bridge", kind="thing", type="bridge", label="the rickety bridge"))
    child.memes["quest"] += 1
    child.memes["joy"] += 1

    world.say(
        f"On a bright pirate afternoon, {child.id} and {nanny.id} turned the deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"Captain {child.id}!" {child.id} cried. "The map says the treasure lies beyond {theme.moat_name}!"'
    )

    world.para()
    world.say(
        f"But the {theme.moat_name} was wide and shiny, and the wind made the ropes groan like old ship timbers. "
        f"{child.id} frowned at the crossing."
    )
    world.say(f'"We need a way over," {child.id} said. "Maybe {tool}?"')

    child.memes["bravery"] += 1
    if tool == "planks":
        world.say(
            f'{child.id} pointed at the loose planks. "We can make a bridge ourselves!"'
        )
    else:
        world.say(
            f'{nanny.id} shook {nanny.pronoun("possessive")} head. "{tool} will not help us cross safely."'
        )

    world.say(
        f"{nanny.id} peered at the water, then at the map, and gave a small smile. "
        f'"Let us solve it together," {nanny.pronoun()} said. "First, answer my quiz."'
    )
    world.facts["teamed"] = True

    world.para()
    world.say(f'"What keeps the ship steady?" {nanny.id} asked.')
    world.say(f'"Teamwork!" {child.id} shouted.')
    world.say(f'"What do pirates do before a quest across a moat?"')
    world.say(f'"Plan first!" {child.id} answered.')
    world.say(
        f"{nanny.id} nodded. Together they laid {theme.treasure_name} markers on the deck, tied a rope rail, "
        f"and used the quiz answers to make a safe crossing plan."
    )

    _do_hazard(world, moat, narrate=False)
    world.para()
    world.say(
        f"{child.id} and {nanny.id} crossed slowly, holding the rope with both hands. "
        f"The moat splashed below, but the plan held firm."
    )
    if response.id == "lighthouse":
        world.say(
            f"At the far side, {response.success.replace('{target}', theme.moat_name)}."
        )
    else:
        world.say(response.success.replace("{target}", theme.moat_name))

    world.para()
    world.say(
        f"At last they reached the treasure chest. The lid opened, and the gold blinked in the sun like a happy eye. "
        f"{theme.ending}"
    )

    world.facts.update(
        child=child,
        nanny=nanny,
        moat=moat,
        bridge=bridge,
        theme=theme,
        tool=tool,
        target=target,
        response=response,
        outcome="safe",
    )
    return world


THEMES = {
    "pirate_tale": Theme(
        "pirate_tale",
        "a deck full of maps and rope",
        "The sail was a blanket, a spoon became a spyglass, and a chalk mark on the boards showed the treasure route.",
        "Captain",
        "Mate",
        "the hidden island",
        "the moat",
        "the treasure chest",
        "They waved their hats and laughed as the gulls wheeled above the ship."
    ),
    "moon_pirates": Theme(
        "moon_pirates",
        "a silver ship on the moon",
        "The bench was their ship, a ribbon became a flag, and little shells stood in for moon rocks.",
        "Captain",
        "Scout",
        "the crater island",
        "the moat",
        "the treasure chest",
        "They bounced home with moon-dust shoes and big grins."
    ),
}

TOOLS = ["planks", "rope", "lantern"]
TARGETS = ["moat"]

RESPONSES = {
    "bridge": Response("bridge", 3, 3, "built a little bridge and crossed without a splash", "could not build a bridge in time", "built a little bridge"),
    "rope": Response("rope", 2, 2, "tied the rope rail tight and crossed carefully", "the rope slipped and the crossing wobbled", "tied the rope rail tight"),
    "lighthouse": Response("lighthouse", 3, 4, "set a lantern on the far side to guide the way", "the lantern was not enough to guide them", "set a lantern to guide the way"),
}


KNOWLEDGE = {
    "moat": [("What is a moat?", "A moat is a deep ditch or water channel around something, often a castle or fort.")],
    "nanny": [("What does a nanny do?", "A nanny helps care for children, keeps them safe, and often helps them learn and play.")],
    "quiz": [("What is a quiz?", "A quiz is a set of questions that helps someone remember or learn something.")],
    "teamwork": [("What is teamwork?", "Teamwork means people work together and help each other to reach a goal.")],
    "quest": [("What is a quest?", "A quest is an adventure with a goal, like finding treasure or solving a problem.")],
    "pirates": [("Who are pirates in stories?", "Pirates are adventure characters who sail, follow maps, and hunt for treasure.")],
}


@dataclass
@dataclass
class StoryParams:
    theme: str
    tool: str
    target: str
    response: str
    child_name: str
    child_gender: str
    nanny_name: str
    nanny_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "nanny", "quiz", and "moat".',
        f"Tell a teamwork quest story where {f['child'].id} and {f['nanny'].id} cross a moat by solving a quiz together.",
        f'Write a story in pirate style about a child, a nanny, and a moat, ending with a safe treasure win.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, nanny, theme = f["child"], f["nanny"], f["theme"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {nanny.id}, who go on a pirate quest together. The nanny helps turn the crossing into a teamwork game."
        ),
        QAItem(
            question="Why did they need the quiz?",
            answer=f"They needed the quiz to plan a safe way across the moat. The answers helped them work together instead of rushing in."
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"It ended safely at the treasure chest. {theme.ending} That ending proves the quest was solved with teamwork."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"moat", "nanny", "quiz", "teamwork", "quest", "pirates"}
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            for q, a in pairs:
                out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pirate_tale", "planks", "moat", "bridge", "Pip", "boy", "Nanny June", "nanny"),
    StoryParams("pirate_tale", "rope", "moat", "rope", "Mira", "girl", "Nanny June", "nanny"),
    StoryParams("moon_pirates", "lantern", "moat", "lighthouse", "Theo", "boy", "Nanny Rose", "nanny"),
]


def explain_rejection(tool: str) -> str:
    return f"(No story: {tool} does not create a good moat quest in this tiny world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate(args)
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.tool is None or c[1] == args.tool)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, tool, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(["Pip", "Mira", "Theo", "Lena", "Kai", "Zoe"])
    nanny_name = args.nanny_name or rng.choice(["Nanny June", "Nanny Rose", "Nanny Pearl"])
    return StoryParams(theme, tool, target, response, child_name, child_gender, nanny_name, "nanny")


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], params.tool, params.target, RESPONSES[params.response],
                 params.child_name, params.child_gender, params.nanny_name, params.nanny_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: nanny, quiz, moat, teamwork, quest, pirate tale.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--nanny-name")
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


ASP_RULES = r"""
hazard(Tool, Target) :- tool(Tool), target(Target), Tool = planks, Target = moat.
valid(Theme, Tool, Target) :- theme(Theme), hazard(Tool, Target).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for t in TARGETS:
        lines.append(asp.fact("target", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"MISMATCH: smoke test failed: {err}")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            header = f"### {p.child_name} and {p.nanny_name}: {p.theme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
