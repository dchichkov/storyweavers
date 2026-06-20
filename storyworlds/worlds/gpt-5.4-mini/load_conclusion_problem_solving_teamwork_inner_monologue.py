#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/load_conclusion_problem_solving_teamwork_inner_monologue.py
===========================================================================================

A standalone storyworld for a bedtime-story style tale about a child facing a
small but real burden, thinking through the problem, asking for help, and
finding a gentle teamwork solution.

Seed words: load, conclusion
Features: Problem Solving, Teamwork, Inner Monologue
Style: Bedtime Story

The world is intentionally small: a child wants to bring a bedtime "load"
(cozy things needed for a sleep routine) to a resting place, but the load is
too heavy or awkward to carry alone. The story turns on the child's inner
monologue, a sensible problem-solving beat, and a cooperative ending image
that proves the load was handled and the conclusion of the night is calm.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
- includes Python reasonableness gates and inline ASP twin
- emits 3 QA sets from world state
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
LOAD_MIN = 1
LOAD_MAX = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    scene: str
    resting_place: str
    ending_image: str
    supports_together: bool = True

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
class LoadItem:
    id: str
    label: str
    weight: int
    awkward: bool
    bedtime_use: str
    tags: set[str] = field(default_factory=set)

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
class HelpIdea:
    id: str
    label: str
    power: int
    teamwork_text: str
    conclusion_text: str
    tags: set[str] = field(default_factory=set)

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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return c


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


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["strain"] >= THRESHOLD and ("tired",) not in world.fired:
        world.fired.add(("tired",))
        child.memes["worry"] += 1
        out.append("__tired__")
    return out


CAUSAL_RULES = [Rule("tired", "social", _r_tired)]


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


def load_cost(load: LoadItem, carrying: int) -> int:
    return load.weight + carrying


def reasonableness(load: LoadItem, setting: Setting, helper: HelpIdea) -> bool:
    return setting.supports_together and helper.power >= load.weight and load.weight >= LOAD_MIN


def sensible_help() -> list[HelpIdea]:
    return [h for h in HELPS.values() if h.power >= 2]


def best_help() -> HelpIdea:
    return max(HELPS.values(), key=lambda h: h.power)


def predict(world: World, load: LoadItem, helper: HelpIdea) -> dict:
    sim = world.copy()
    _carry(sim, sim.get("child"), sim.get("parent"), load, helper, narrate=False)
    return {
        "finished": sim.get("load").meters["moved"] >= THRESHOLD,
        "strain": sim.get("child").meters["strain"],
    }


def _carry(world: World, child: Entity, parent: Entity, load: LoadItem, helper: HelpIdea, narrate: bool = True) -> None:
    child.meters["strain"] += load.weight
    child.meters["effort"] += 1
    if load.weight >= 3:
        child.memes["worry"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, load: LoadItem) -> None:
    child.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.label_word} stayed up a little longer in {setting.scene}. "
        f"A small {load.label} waited by the door, ready for the night."
    )
    world.say(
        f"{child.id} wanted to bring the {load.label} to {setting.resting_place} all by {child.pronoun('object')}self."
    )


def inner_voice(world: World, child: Entity, load: LoadItem) -> None:
    child.memes["thought"] += 1
    world.say(
        f'{child.id} looked at the {load.label} and thought, "It is a big load for my little arms. '
        f'If I rush, I might drop it."'
    )


def problem(world: World, child: Entity, load: LoadItem) -> None:
    child.memes["need"] += 1
    world.say(
        f"{child.id} tried to lift it, but the {load.label} wobbled in {child.pronoun('possessive')} hands. "
        f"The load felt heavier than it had looked."
    )


def teamwork_offer(world: World, parent: Entity, child: Entity, helpidea: HelpIdea) -> None:
    parent.memes["kindness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled softly. "{helpidea.teamwork_text}"'
    )


def accept_help(world: World, child: Entity, parent: Entity, helpidea: HelpIdea) -> None:
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} nodded, and the worry in {child.pronoun('possessive')} chest loosened. "
        f"{child.id} thought, 'I do not have to do every hard thing alone.'"
    )
    world.say(
        f"Together, they followed the plan and {helpidea.conclusion_text}."
    )


def finish(world: World, setting: Setting, child: Entity, load: LoadItem) -> None:
    child.meters["strain"] = 0.0
    load_ent = world.get("load")
    load_ent.meters["moved"] = 1.0
    world.say(
        f"At last, the {load.label} was in {setting.resting_place}, and the room felt peaceful again."
    )
    world.say(
        f"{setting.ending_image} {child.id} yawned, smiled, and let the conclusion of the night settle in like a warm blanket."
    )


def tell(setting: Setting, load: LoadItem, helpidea: HelpIdea,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    load_ent = world.add(Entity(id="load", type="load", label=load.label))
    world.facts["setting"] = setting
    world.facts["load_cfg"] = load
    world.facts["help"] = helpidea

    setup(world, child, parent, setting, load)
    world.para()
    inner_voice(world, child, load)
    problem(world, child, load)
    teamwork_offer(world, parent, child, helpidea)

    can_solve = reasonableness(load, setting, helpidea)
    world.para()
    if can_solve:
        accept_help(world, child, parent, helpidea)
        finish(world, setting, child, load)
        outcome = "solved"
    else:
        world.say(
            f"{child.id} tried anyway, but the plan did not fit the load."
        )
        world.say(
            f"In the end, they had to stop and think of a safer way before the night could go on."
        )
        outcome = "stalled"

    world.facts.update(
        child=child, parent=parent, load=load_ent, outcome=outcome,
        solved=(outcome == "solved"),
        finished=load_ent.meters["moved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "the reading nook", "A moonbeam touched the blanket fort, and the pillow stack stayed neat."),
    "hallway": Setting("hallway", "the hallway", "the bedside shelf", "A tiny lamp glowed near the wall, and the hallway looked cozy and still."),
    "playroom": Setting("playroom", "the playroom", "the toy basket corner", "The teddy bear sat watch while the blankets made a soft little hill."),
}

LOADS = {
    "blankets": LoadItem("blankets", "bundle of blankets", 3, False, "make the bed extra cozy", {"cozy"}),
    "books": LoadItem("books", "stack of storybooks", 2, False, "build a bedtime pile", {"reading"}),
    "pillows": LoadItem("pillows", "armful of pillows", 4, True, "make a sleepy nest", {"sleep"}),
    "laundry": LoadItem("laundry", "basket of folded laundry", 5, True, "finish the room before sleep", {"work"}),
}

HELPS = {
    "split": HelpIdea("split", "split the load", 3, "Let's carry it together, one piece at a time.", "divided the load into smaller pieces and moved them one by one", {"teamwork"}),
    "cart": HelpIdea("cart", "roll a little cart", 4, "We can use the little cart so the load does not wobble.", "set the load on a little cart and rolled it along gently", {"teamwork"}),
    "two_hands": HelpIdea("two_hands", "use two hands and slow steps", 2, "Hold it with two hands and take slow steps with me.", "held the load with two hands and walked slowly, together", {"teamwork"}),
}

CHILD_NAMES = ["Mia", "Luna", "Noah", "Theo", "Ivy", "Ava", "Eli", "Rose"]
CURATED = [
    StoryParams("nursery", "blankets", "split", "Mia", "girl", "mother"),
    StoryParams("hallway", "books", "two_hands", "Noah", "boy", "father"),
    StoryParams("playroom", "pillows", "cart", "Ivy", "girl", "mother"),
]


@dataclass
class StoryParams:
    setting: str
    load: str
    helpidea: str
    child_name: str
    child_gender: str
    parent: str
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
    combos = []
    for s_id, s in SETTINGS.items():
        for l_id, l in LOADS.items():
            for h_id, h in HELPS.items():
                if reasonableness(l, s, h):
                    combos.append((s_id, l_id, h_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about a load, teamwork, and a gentle conclusion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--helpidea", choices=HELPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.load and args.helpidea:
        if not reasonableness(LOADS[args.load], SETTINGS[args.setting], HELPS[args.helpidea]):
            raise StoryError("That help idea does not really solve that load in that setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.load is None or c[1] == args.load)
              and (args.helpidea is None or c[2] == args.helpidea)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, load, helpidea = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, load, helpidea, name, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    load = f["load_cfg"]
    helpidea = f["help"]
    setting = f["setting"]
    return [
        f'Write a bedtime story that includes the words "load" and "conclusion" and shows a child asking for help with a {load.label}.',
        f"Tell a gentle story where {child.id} feels a big load, listens to an inner thought, and works together with a grown-up to reach a calm conclusion.",
        f"Write a small, cozy story in a bedtime tone about teamwork and problem solving in {setting.scene}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent = f["child"], f["parent"]
    load, setting, helpidea = f["load_cfg"], f["setting"], f["help"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {child.pronoun('possessive')} {parent.label_word}, who were trying to handle a {load.label}."),
        ("What problem did they face?",
         f"The {load.label} was a big load for one child to carry alone, so {child.id} had to stop and think. That is what made the story turn into a problem-solving moment."),
        ("What did {0} think to {1}?".format(child.id, child.pronoun('possessive')),
         f"{child.id} thought that the load was too much for little arms and that asking for help would be smarter than rushing. The inner voice helped {child.id} stay calm."),
    ]
    if f.get("solved"):
        qa.append((
            "How did they solve the problem?",
            f"They used {helpidea.label} together, so the load could move without wobbling. Teamwork made the hard job small enough to finish."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the load safely in {setting.resting_place} and a quiet, cozy conclusion. The room looked peaceful, and the bedtime feeling returned."
        ))
    else:
        qa.append((
            "Why did the plan fail?",
            f"The idea was not strong enough for that load, so they had to pause and find a better way. The story stayed gentle, but the problem was not solved yet."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["load_cfg"].tags)
    if world.facts.get("solved"):
        tags |= world.facts["help"].tags
    knowledge = {
        "cozy": [("What does cozy mean?", "Cozy means warm, soft, and comfortable, like a blanket tucked around you at bedtime.")],
        "reading": [("Why are storybooks nice at bedtime?", "Storybooks help calm your mind, and reading together can feel quiet and safe before sleep.")],
        "sleep": [("Why are pillows useful?", "Pillows help make a bed soft and comfy so it is easier to rest.")],
        "work": [("What is folding laundry?", "Folding laundry means putting clean clothes into neat stacks so they are easy to carry and store.")],
        "teamwork": [("What is teamwork?", "Teamwork means people help each other and do a job together, so the job feels easier.")],
    }
    order = ["cozy", "reading", "sleep", "work", "teamwork"]
    out: list[tuple[str, str]] = []
    for tag in order:
        if tag in tags:
            out.extend(knowledge[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(H) :- help(H), power(H, P), load(L), weight(L, W), P >= W.
solvable(S, L, H) :- setting(S), load(L), help(H), sensible(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        if s.supports_together:
            lines.append(asp.fact("supports_together", s_id))
    for l_id, l in LOADS.items():
        lines.append(asp.fact("load", l_id))
        lines.append(asp.fact("weight", l_id, l.weight))
    for h_id, h in HELPS.items():
        lines.append(asp.fact("help", h_id))
        lines.append(asp.fact("power", h_id, h.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) != {h for h, v in HELPS.items() if v.power >= 2}:
        rc = 1
        print("MISMATCH in sensible helps.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: verify passed and smoke generation succeeded.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], LOADS[params.load], HELPS[params.helpidea],
                 params.child_name, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} solvable combos:")
        for s, l, h in asp_valid_combos():
            print(f"  {s:8} {l:10} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("nursery", "blankets", "split", "Mia", "girl", "mother"),
    StoryParams("hallway", "books", "two_hands", "Noah", "boy", "father"),
    StoryParams("playroom", "pillows", "cart", "Ivy", "girl", "mother"),
]
if __name__ == "__main__":
    main()
