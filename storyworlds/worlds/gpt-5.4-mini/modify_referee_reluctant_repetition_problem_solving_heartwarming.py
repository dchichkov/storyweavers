#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/modify_referee_reluctant_repetition_problem_solving_heartwarming.py
===================================================================================================

A standalone storyworld about a small, heartwarming problem-solving game:
a child reluctantly modifies a toy game, a referee notices repeated mistakes,
and everyone cooperates to make the game fair and fun again.

The seed words are woven into the world model and prose:
- modify
- referee
- reluctant

The domain emphasizes:
- Repetition: the same mistake happens more than once before the fix
- Problem solving: the child and referee work out a better rule together
- Heartwarming tone: the ending is kind, encouraging, and warm

This script follows the Storyweavers contract and can be run directly.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "progress": 0.0, "repetition": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "reluctance": 0.0, "trust": 0.0}

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
class Setting:
    id: str
    place: str
    game: str
    noise: str
    warmth: str
    repeated_mistake: str
    fixed_move: str

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
class Tool:
    id: str
    label: str
    use: str
    helps_with: str
    kind: str = "tool"

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
    apply: Callable[["World"], list[str]]

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turns: list[str] = []

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
        clone.turns = list(self.turns)
        return clone


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["mess"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["repetition"] += 1
    world.get("referee").memes["worry"] += 1
    out.append("__repeat__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["progress"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    world.get("referee").memes["joy"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("repetition", "social", _r_repetition),
    Rule("relief", "social", _r_relief),
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


def predict_repetition(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["mess"] += 1
    propagate(sim, narrate=False)
    return {
        "repeat": sim.get("child").meters["repetition"] >= THRESHOLD,
        "worry": sim.get("referee").memes["worry"],
    }


def calm_setup(world: World, setting: Setting, child: Entity, referee: Entity) -> None:
    child.memes["trust"] += 1
    referee.memes["trust"] += 1
    world.say(
        f"At {setting.place}, the children gathered around {setting.game}. "
        f"{setting.noise} made the room feel lively, and everyone smiled."
    )
    world.say(
        f"{child.id} wanted to play, but {child.pronoun('subject')} was a little "
        f"reluctant about the new rules."
    )


def start_problem(world: World, child: Entity, setting: Setting) -> None:
    child.meters["mess"] += 1
    child.memes["worry"] += 1
    world.turns.append("mistake")
    world.say(
        f"The first try went wrong. {setting.repeated_mistake}, and the game felt "
        f"stuck for a moment."
    )


def repeat_problem(world: World, child: Entity, setting: Setting) -> None:
    child.meters["mess"] += 1
    child.memes["worry"] += 1
    child.meters["repetition"] += 1
    world.turns.append("mistake")
    world.say(
        f"They tried again, but {setting.repeated_mistake} happened once more. "
        f"The same problem kept showing up."
    )


def referee_warns(world: World, child: Entity, referee: Entity, setting: Setting) -> None:
    pred = predict_repetition(world)
    world.facts["predicted_repeat"] = pred["repeat"]
    world.facts["predicted_worry"] = pred["worry"]
    referee.memes["worry"] += 1
    world.say(
        f'{referee.id} the referee knelt beside {child.id}. "{child.id}, we can '
        f"fix this gently,\" {referee.pronoun()} said. \"If we keep doing the same "
        f"thing, {setting.repeated_mistake.lower()} will keep happening.\""
    )


def modify_game(world: World, child: Entity, referee: Entity, setting: Setting, tool: Tool) -> None:
    child.memes["reluctance"] += 1
    world.say(
        f"{child.id} looked reluctant at first, but {referee.id} suggested they "
        f"modify the game with {tool.label}."
    )
    world.say(
        f"{tool.label.capitalize()} would {tool.use}, so the same mistake would not "
        f"keep returning."
    )


def solve(world: World, child: Entity, referee: Entity, setting: Setting, tool: Tool) -> None:
    child.meters["progress"] += 1
    child.memes["joy"] += 1
    referee.memes["joy"] += 1
    world.say(
        f"Together they made the change. {child.id} used {tool.label}, and the "
        f"new rule {tool.helps_with}."
    )
    world.say(
        f"This time, the game moved forward instead of looping back to the same "
        f"trouble."
    )


def heartwarming_end(world: World, child: Entity, referee: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} grinned, no longer reluctant, and {referee.id} gave a warm "
        f"nod. The room felt lighter."
    )
    world.say(
        f"At the end, they played {setting.game} together with easy laughter, "
        f"and the repeated mistake was finally gone."
    )


def tell(setting: Setting, tool: Tool, child_name: str, child_type: str,
         referee_name: str, referee_type: str, helper_name: str = "Parent") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    referee = world.add(Entity(id=referee_name, kind="character", type=referee_type, role="referee"))
    helper = world.add(Entity(id=helper_name, kind="character", type="parent", role="helper"))
    world.add(Entity(id="game", kind="thing", type="game", label=setting.game))
    world.facts["setting"] = setting
    world.facts["tool"] = tool
    world.facts["child"] = child
    world.facts["referee"] = referee
    world.facts["helper"] = helper

    calm_setup(world, setting, child, referee)
    world.para()
    start_problem(world, child, setting)
    repeat_problem(world, child, setting)
    world.para()
    referee_warns(world, child, referee, setting)
    modify_game(world, child, referee, setting, tool)
    world.para()
    solve(world, child, referee, setting, tool)
    heartwarming_end(world, child, referee, setting)

    world.facts.update(
        outcome="solved",
        repeated=child.meters["repetition"] >= THRESHOLD,
        modified=child.meters["progress"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "schoolhall": Setting(
        id="schoolhall",
        place="the school hall",
        game="beanbag toss",
        noise="Soft applause from the practice corner",
        warmth="warm",
        repeated_mistake="the beanbag kept landing in the wrong basket",
        fixed_move="adjust the basket height",
    ),
    "clubroom": Setting(
        id="clubroom",
        place="the club room",
        game="card sorting",
        noise="The clock ticked softly beside the table",
        warmth="cozy",
        repeated_mistake="the cards kept slipping out of order",
        fixed_move="add a color guide",
    ),
    "library": Setting(
        id="library",
        place="the quiet library nook",
        game="tower building",
        noise="A little lamp glowed on the shelf",
        warmth="gentle",
        repeated_mistake="the blocks kept wobbling and falling",
        fixed_move="widen the base",
    ),
}

TOOLS = {
    "tape": Tool("tape", "a strip of tape", "hold the edge in place", "kept the basket from sliding"),
    "guide": Tool("guide", "a color guide card", "show the next step", "made the cards stay in the right order"),
    "base": Tool("base", "a wider base piece", "steady the bottom", "kept the tower from wobbling"),
}

NAMES = ["Mia", "Noah", "Lina", "Owen", "Zoe", "Eli", "Nora", "Ivy", "Sam", "Theo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    tool: str
    child: str
    child_type: str
    referee: str
    referee_type: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TOOLS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about modification, a referee, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--referee")
    ap.add_argument("--referee-type", choices=["girl", "boy", "woman", "man"])
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
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    referee_type = args.referee_type or rng.choice(["girl", "boy", "woman", "man"])
    child = args.child or rng.choice(NAMES)
    referee = args.referee or rng.choice([n for n in NAMES if n != child])
    return StoryParams(setting, tool, child, child_type, referee, referee_type)


def generation_prompts(world: World) -> list[str]:
    s = world.facts["setting"]
    t = world.facts["tool"]
    return [
        f'Write a heartwarming story that includes the words "modify", "referee", and "reluctant" while children solve a repeated game problem.',
        f"Tell a gentle story where a reluctant child and a referee have to modify {s.game} with {t.label}.",
        f"Write a child-friendly story about repetition and problem solving that ends with everyone smiling after they modify a game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    s: Setting = world.facts["setting"]
    t: Tool = world.facts["tool"]
    child: Entity = world.facts["child"]
    referee: Entity = world.facts["referee"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {referee.id}, who meet in {s.place} to fix a game together. The referee helps guide the problem solving in a kind way."
        ),
        QAItem(
            question=f"Why was {child.id} reluctant?",
            answer=f"{child.id} was reluctant because the game kept going wrong and the child did not want to change the rules. The repeated mistake made the child unsure at first."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They modified the game with {t.label} so {t.helps_with}. That stopped the same mistake from coming back again."
        ),
    ]
    if world.facts.get("repeated"):
        qa.append(
            QAItem(
                question=f"What happened after the same mistake happened twice?",
                answer=f"The referee noticed the repetition and asked them to try a better plan. That made room for a solution instead of another failed turn."
            )
        )
    if world.facts.get("modified"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended warmly, with everyone smiling and the game finally working. The child felt braver after helping solve the problem."
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem("What is a referee?", "A referee is a person who watches a game, makes sure the rules are fair, and helps settle problems kindly."),
    QAItem("What does modify mean?", "Modify means to change something a little so it works better for the problem you have."),
    QAItem("What is repetition?", "Repetition means something happens again and again, like the same mistake repeating in a game."),
    QAItem("What is problem solving?", "Problem solving means thinking carefully, trying ideas, and working together until the problem is fixed."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("schoolhall", "tape", "Mia", "girl", "Mr. Reed", "man"),
    StoryParams("clubroom", "guide", "Noah", "boy", "Aunt June", "woman"),
    StoryParams("library", "base", "Lina", "girl", "Coach Ben", "man"),
]


ASP_RULES = r"""
repetition :- child_mess(M), M >= 1, not solved_yet.
problem_solving :- modified_game.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show tool/1."))
    settings = sorted(set(asp.atoms(model, "setting")))
    tools = sorted(set(asp.atoms(model, "tool")))
    return [(s, t) for (s,) in settings for (t,) in tools]


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, tool=None, child=None, child_type=None, referee=None, referee_type=None), random.Random(777)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], params.child, params.child_type, params.referee, params.referee_type)
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
        print(asp_program("", "#show setting/1.\n#show tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{s} {t}" for s, t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
