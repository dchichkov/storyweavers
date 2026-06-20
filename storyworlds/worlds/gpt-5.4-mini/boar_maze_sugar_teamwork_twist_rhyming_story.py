#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boar_maze_sugar_teamwork_twist_rhyming_story.py
================================================================================

A standalone storyworld for a tiny rhyming tale about a boar, a maze, sugar,
teamwork, and a small twist. It models a child-friendly garden adventure where
two helpers try to reach a sweet prize, get turned around in the maze, and then
work together in an unexpected way to finish with a bright, satisfying ending.

The world is intentionally small:
- a maze with paths, hedges, a gate, and a little sugar stash
- one boar that can wander, get hungry, and become friendly when treated well
- two child characters who can team up
- state-driven beats: getting lost, sharing a plan, solving the twist, and
  ending with the sugar safely reached

The prose is kept rhythmic and lightly rhyming, but the story remains driven by
the simulated world state rather than by frozen paragraph templates.
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
BOAR_HUNGER_START = 2.0
TEAMWORK_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class MazeSetting:
    id: str
    place: str
    path_words: list[str]
    end_word: str
    twist_word: str
    rhythm_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    edible: bool = True
    sticky: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class BoarSpec:
    id: str
    label: str
    phrase: str
    snout_line: str
    helpful_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    boar = world.entities.get("boar")
    if boar and boar.meters["wandering"] >= THRESHOLD and boar.meters["hunger"] < 4:
        sig = ("hunger",)
        if sig not in world.fired:
            world.fired.add(sig)
            boar.meters["hunger"] += 1
            out.append("__hunger__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if "kid1" not in world.entities or "kid2" not in world.entities:
        return out
    a, b = world.get("kid1"), world.get("kid2")
    if a.memes["teamwork"] + b.memes["teamwork"] < TEAMWORK_MIN:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("maze").meters["hope"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("hunger", "physical", _r_hunger), Rule("teamwork", "social", _r_teamwork)]


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


def boar_is_hungry(world: World) -> bool:
    return world.get("boar").meters["hunger"] >= BOAR_HUNGER_START


def maze_twist_needed(world: World) -> bool:
    return world.get("maze").meters["twist"] >= THRESHOLD


def predict_twist(world: World) -> dict:
    sim = world.copy()
    _do_choice(sim, narrate=False)
    return {
        "boar_calm": sim.get("boar").memes["calm"] >= THRESHOLD,
        "sugar_reached": sim.get("sugar").meters["found"] >= THRESHOLD,
    }


def _do_choice(world: World, narrate: bool = True) -> None:
    boar = world.get("boar")
    sugar = world.get("sugar")
    maze = world.get("maze")
    a = world.get("kid1")
    b = world.get("kid2")
    boar.meters["wandering"] += 1
    propagate(world, narrate=narrate)
    if boar_is_hungry(world):
        world.say(f"The boar went snout-first through the maze, with a sniff and a snort.")
    if maze_twist_needed(world):
        world.say(f"The maze had a twisty gate, and the path grew tight as a curl.")
    if a.memes["teamwork"] + b.memes["teamwork"] >= TEAMWORK_MIN:
        maze.meters["opened"] += 1
        sugar.meters["found"] += 1
        boar.memes["calm"] += 1
        boar.meters["helped"] += 1


def setup(world: World, setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool) -> None:
    world.say(
        f"In a hedge-gate maze by the garden glade, two children went wandering, brave and not afraid."
    )
    world.say(
        f"{setting.rhythm_line} They hoped to reach {goal.phrase}, sweet as could be."
    )
    world.say(
        f"Near the turning green corners, they heard a soft snore; it was {boar.phrase}, a gentle boar."
    )


def search(world: World, setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool) -> None:
    a = world.get("kid1")
    b = world.get("kid2")
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f'They said, "We need a clue for this loop-de-loop queue, or we may circle forever in blue and green hue."'
    )
    world.say(f"The hedges went high; the sky looked small. The maze was a puzzle that puzzled them all.")


def twist(world: World, setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool) -> None:
    a = world.get("kid1")
    b = world.get("kid2")
    boar = world.get("boar")
    pred = predict_twist(world)
    world.facts["pred"] = pred
    world.say(
        f"Then came the twist: the boar loved the tryst of sweet sugar pieces tucked under the mist."
    )
    world.say(
        f"{boar.snout_line} It nosed at the corner, then paused to adore {goal.phrase} with a hopeful snore."
    )
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f'{a.id} and {b.id} shared one plan: "{tool.phrase} can lure him; then all of us can."'
    )


def cooperate(world: World, setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool) -> None:
    a = world.get("kid1")
    b = world.get("kid2")
    maze = world.get("maze")
    boar = world.get("boar")
    sugar = world.get("sugar")
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    maze.meters["twist"] = 0.0
    boar.memes["friendly"] += 1
    sugar.meters["found"] += 1
    world.say(
        f"They worked as a team: one held the gate, one held the trail, and the boar took the path that would not fail."
    )
    world.say(
        f"{tool.use_line} Soon the boar snuffled the sugar, and the maze lost its frown."
    )


def ending(world: World, setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool) -> None:
    a = world.get("kid1")
    b = world.get("kid2")
    sugar = world.get("sugar")
    boar = world.get("boar")
    world.say(
        f"At last they reached {goal.phrase}, with sugar in sight and the boar acting bright."
    )
    world.say(
        f"They shared the sweet treasure, and the boar got a small treat too; teamwork made the whole day new."
    )
    world.say(
        f"In the maze by the garden glade, they found the way and the twirling stayed."
    )


def tell(setting: MazeSetting, boar: BoarSpec, goal: Goal, tool: Tool,
         kid1: str = "Mina", kid1_gender: str = "girl",
         kid2: str = "Owen", kid2_gender: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    world.add(Entity(id="kid1", kind="character", type=kid1_gender, role="helper", label=kid1))
    world.add(Entity(id="kid2", kind="character", type=kid2_gender, role="helper", label=kid2))
    world.add(Entity(id="boar", kind="character", type="boar", role="twist", label=boar.label))
    world.add(Entity(id="maze", kind="thing", type="maze", label="the maze"))
    world.add(Entity(id="sugar", kind="thing", type="goal", label="sugar", attrs={"sweet": True}))
    world.get("boar").meters["hunger"] = BOAR_HUNGER_START
    world.get("maze").meters["twist"] = 1.0
    setup(world, setting, boar, goal, tool)
    world.para()
    search(world, setting, boar, goal, tool)
    world.para()
    twist(world, setting, boar, goal, tool)
    world.para()
    cooperate(world, setting, boar, goal, tool)
    world.para()
    ending(world, setting, boar, goal, tool)
    world.facts.update(setting=setting, boar=boar, goal=goal, tool=tool,
                       kid1=world.get("kid1"), kid2=world.get("kid2"),
                       outcome="sweet", seed=None)
    return world


SETTINGS = {
    "garden": MazeSetting(
        "garden", "the garden maze",
        ["left", "right", "left", "around"],
        "the center gate",
        "twist",
        "The path was green and neat, with a turny beat and a shuffle of feet.",
        tags={"maze", "garden"},
    ),
    "orchard": MazeSetting(
        "orchard", "the orchard maze",
        ["apple", "peach", "pear", "plum"],
        "the stone arch",
        "twist",
        "The orchard glowed with blossom light, and the turns were merry in morning bright.",
        tags={"maze", "orchard"},
    ),
    "corn": MazeSetting(
        "corn", "the corn maze",
        ["stalk", "leaf", "bend", "sway"],
        "the round opening",
        "twist",
        "Tall corn stood proud, but the trails all curved like a ribbon in a happy crowd.",
        tags={"maze", "field"},
    ),
}

BOARS = {
    "boar": BoarSpec(
        "boar",
        "a young boar",
        "a young boar with a shiny snout",
        "The boar lifted its nose and gave one cheerful snore.",
        "The boar blinked, then came along and turned the trouble into song.",
        tags={"boar"},
    )
}

GOALS = {
    "sugar": Goal("sugar", "sugar", "the sugar stash", edible=True, sticky=False, tags={"sugar"}),
}

TOOLS = {
    "trail": Tool("trail", "crumb trail", "a trail of sugar crumbs", "They laid a crumb trail, bright and pale.", tags={"sugar", "teamwork"}),
}

@dataclass
class StoryParams:
    setting: str
    boar: str
    goal: str
    tool: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BOARS:
            for g in GOALS:
                combos.append((s, b, g))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    boar = f["boar"]
    return [
        f'Write a rhyming story for a young child about {boar.label} in a maze, with sugar and teamwork.',
        f"Tell a sweet twist story set in {setting.place} where two helpers and a boar find sugar together.",
        "Write a gentle rhyming adventure where teamwork helps everyone through a maze and ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: MazeSetting = f["setting"]
    boar: BoarSpec = f["boar"]
    goal: Goal = f["goal"]
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    a = kid1
    b = kid2
    answers = [
        QAItem("Who is the story about?", f"It is about {a.id} and {b.id}, plus {boar.label}. They were trying to find sugar in the maze."),
        QAItem("What problem did they have?", f"They got turned around in the maze, and the boar kept following the smell of sugar. The twist made the path tricky, so they had to work together."),
        QAItem("How did they solve it?", f"They made a plan and used teamwork. One child helped with the gate while the other helped guide the boar toward the sugar."),
        QAItem("How did the story end?", f"It ended happily with sugar found, the boar calm, and the maze no longer confusing. Everyone shared the sweet prize."),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a maze?", "A maze is a place with twisty paths that can be hard to follow. You may need to try more than one turn to find the way out."),
        QAItem("What does sugar taste like?", "Sugar tastes sweet. People often use it in treats and tiny snacks."),
        QAItem("Can teamwork help?", "Yes. Teamwork means helping each other, and it can make a hard job easier and faster."),
        QAItem("What is a boar?", "A boar is a wild pig with a strong nose. It can sniff smells very well."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,G) :- setting(S), boar(B), goal(G).
outcome(sweet) :- valid(_,_,_), teamwork(kid1), teamwork(kid2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BOARS:
        lines.append(asp.fact("boar", bid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, boar=None, goal=None, tool=None,
                                                            kid1=None, kid1_gender=None, kid2=None,
                                                            kid2_gender=None, parent=None),
                                          _random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming boar-maze-sugar teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boar", choices=BOARS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--kid1")
    ap.add_argument("--kid1-gender", choices=["girl", "boy"])
    ap.add_argument("--kid2")
    ap.add_argument("--kid2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    boar = args.boar or "boar"
    goal = args.goal or "sugar"
    tool = args.tool or "trail"
    kid1_gender = args.kid1_gender or rng.choice(["girl", "boy"])
    kid2_gender = args.kid2_gender or ("boy" if kid1_gender == "girl" else "girl")
    kid1 = args.kid1 or rng.choice(["Mina", "Tia", "Luca", "Nia", "Pip"])
    kid2 = args.kid2 or rng.choice([n for n in ["Owen", "Noah", "Eli", "Bo", "Finn"] if n != kid1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, boar, goal, tool, kid1, kid1_gender, kid2, kid2_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BOARS[params.boar], GOALS[params.goal], TOOLS[params.tool],
                 params.kid1, params.kid1_gender, params.kid2, params.kid2_gender, params.parent)
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
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, "boar", "sugar", "trail", "Mina", "girl", "Owen", "boy", "mother")) for s in SETTINGS]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
