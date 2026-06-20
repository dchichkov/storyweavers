#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/four_bruise_boat_ramp_humor_teamwork_bedtime.py
================================================================================

A standalone story world for a tiny bedtime tale at a boat ramp.

Seeded premise:
- setting: boat ramp
- features: humor, teamwork
- style: bedtime story
- seed words: four, bruise

The world model is small and classical:
- a child wants to help with a boat at dusk
- the ramp is slippery and the boat is awkward
- a small bump leaves a bruise
- everybody uses teamwork and a little humor to finish safely
- the ending settles into a cozy bedtime image

This script follows the shared Storyweavers contract:
- StoryParams plus registries
- build_parser, resolve_params, generate, emit, main
- Python reasonableness gate and inline ASP twin
- three QA sets grounded in world state
- --verify smoke-tests normal generation and ASP parity
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
BRUISE_THRESHOLD = 1.0
TEAMWORK_THRESHOLD = 2.0
HUMOR_THRESHOLD = 1.0
RAMP_WET_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str
    ramp: str
    water: str
    bedtime_detail: str

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
class Action:
    id: str
    verb: str
    plan: str
    mishap: str
    joke: str
    teamwork_move: str
    ending_image: str

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
class ComfortItem:
    id: str
    label: str
    phrase: str

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


def _r_bruise(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    if not child:
        return out
    if child.meters["bumped"] < THRESHOLD:
        return out
    sig = ("bruise", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["bruise"] += 1
    child.memes["surprised"] += 1
    out.append("__bruise__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    boat = world.facts.get("boat")
    child = world.facts.get("child")
    helper = world.facts.get("helper")
    if not boat or not child or not helper:
        return out
    if child.memes["helped"] < TEAMWORK_THRESHOLD:
        return out
    sig = ("teamwork", boat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["steady"] += 1
    helper.memes["pride"] += 1
    out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule("bruise", "physical", _r_bruise),
    Rule("teamwork", "social", _r_teamwork),
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


def ramp_is_tricky(setting: Setting) -> bool:
    return True


def child_can_get_bruised(setting: Setting, action: Action) -> bool:
    return ramp_is_tricky(setting) and action.id == "carry_boat"


def teamwork_works(child_help: int, helper_help: int) -> bool:
    return child_help + helper_help >= TEAMWORK_THRESHOLD


def setup(world: World, child: Entity, helper: Entity, setting: Setting, action: Action) -> None:
    child.memes["curious"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At the {setting.place}, {child.id} and {helper.id} were getting ready "
        f"for a sleepy little night by the water. {setting.bedtime_detail}"
    )
    world.say(
        f"{child.id} wanted to {action.verb}. It sounded simple, until the ramp "
        f"looked slick as a fish."
    )


def humor(world: World, child: Entity, helper: Entity, action: Action) -> None:
    child.memes["humor"] += 1
    helper.memes["humor"] += 1
    world.say(
        f'{child.id} grinned. "{action.joke}" {helper.id} said, and that made '
        f"the serious job feel less heavy."
    )


def slip(world: World, child: Entity, setting: Setting) -> None:
    child.meters["bumped"] += 1
    child.memes["oops"] += 1
    world.say(
        f"As they moved, {child.id}'s shoe slid on the wet ramp. {child.id} "
        f"bumped a shin on the edge, and a tiny bruise bloomed like a blueberry."
    )


def teamwork(world: World, child: Entity, helper: Entity, action: Action, boat: Entity) -> None:
    child.memes["helped"] += 1
    child.memes["determined"] += 1
    helper.memes["helped"] += 1
    world.say(
        f"Then they tried again, one hand on the rope and one hand on the boat. "
        f"{action.teamwork_move}"
    )
    propagate(world, narrate=False)
    if boat.meters["steady"] >= THRESHOLD:
        world.say(
            f"The boat stopped wobbling and sat just where it should, as neat as "
            f"a toy in a bedtime book."
        )


def comfort(world: World, parent: Entity, child: Entity, helper: Entity, setting: Setting,
            action: Action, comfort_item: ComfortItem) -> None:
    child.memes["safe"] += 1
    child.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over with {comfort_item.phrase}. "
        f'{parent.pronoun().capitalize()} kissed the bruise and said, "Little '
        f"bumps happen at the water. Good teamwork keeps the whole family safe."
    )
    world.say(
        f"{helper.id} snickered, pretending to salute the ramp. "
        f'"Captain {child.id}, the boat is ready for bedtime docking!"'
    )
    world.say(
        f"That made {child.id} laugh through the sting. The moon went silver on "
        f"the water, and the ramp felt less tricky now."
    )


def ending(world: World, child: Entity, helper: Entity, parent: Entity, setting: Setting,
           action: Action, comfort_item: ComfortItem) -> None:
    world.say(
        f"After one last check, the boat rested safely by the dock, and everyone "
        f"walked home with slow, sleepy steps."
    )
    world.say(
        f"At bedtime, {child.id} curled up warm and tired, thinking of the little "
        f"bruise, the silly joke, and how four hands had made one hard job easy."
    )
    world.say(
        f"Outside, {setting.water} shone under the night sky. Inside, the house "
        f"was soft and quiet, and {comfort_item.label} stayed tucked beside the pillow."
    )


def tell(setting: Setting, action: Action, comfort_item: ComfortItem,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "father",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=5))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", age=9))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    boat = world.add(Entity(id="boat", type="boat", label="little boat"))
    world.add(Entity(id="ramp", type="place", label=setting.ramp))
    world.facts.update(child=child, helper=helper, parent=parent, boat=boat, setting=setting, action=action)

    setup(world, child, helper, setting, action)
    world.para()
    humor(world, child, helper, action)
    slip(world, child, setting)
    if child_can_get_bruised(setting, action):
        propagate(world, narrate=False)
    world.para()
    teamwork(world, child, helper, action, boat)
    world.para()
    comfort(world, parent, child, helper, setting, action, comfort_item)
    world.para()
    ending(world, child, helper, parent, setting, action, comfort_item)
    world.facts["outcome"] = "bruise"
    return world


SETTINGS = {
    "boat_ramp": Setting(
        id="boat_ramp",
        place="the boat ramp",
        ramp="the wet boat ramp",
        water="the lake",
        bedtime_detail="A small porch light blinked on, and the water made a soft hush-hush sound.",
    ),
    "dock": Setting(
        id="dock",
        place="the dock",
        ramp="the dock boards",
        water="the river",
        bedtime_detail="Lantern light made a cozy stripe across the boards.",
    ),
}

ACTIONS = {
    "carry_boat": Action(
        id="carry_boat",
        verb="carry the little boat to the water",
        plan="carry the little boat together",
        mishap="slid on the ramp",
        joke="The boat was so small it looked like it could hide in a lunchbox!",
        teamwork_move="They lifted with careful knees, marched like tiny penguins, and counted one, two, three.",
        ending_image="the boat resting by the dock",
    ),
    "guide_boat": Action(
        id="guide_boat",
        verb="guide the little boat to the water",
        plan="guide the little boat with a rope",
        mishap="bumped the edge",
        joke="Even the boat seemed to be trying not to giggle.",
        teamwork_move="One held the rope while the other steadied the bow, and together they moved slowly.",
        ending_image="the boat floating still and calm",
    ),
}

COMFORTS = {
    "blanket": ComfortItem("blanket", "a blanket", "a soft blanket"),
    "pillow": ComfortItem("pillow", "a pillow", "a fluffy pillow"),
    "teddy": ComfortItem("teddy", "a teddy bear", "a sleepy teddy bear"),
}

GIRL_NAMES = ["Mila", "Nora", "Lena", "Ivy", "Ruby", "Poppy", "Ada", "June"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Bennett", "Leo", "Milo", "Jack", "Ezra"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    comfort: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
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
    for sid in SETTINGS:
        for aid in ACTIONS:
            for cid in COMFORTS:
                combos.append((sid, aid, cid))
    return combos


def explain_rejection() -> str:
    return "(No story: this bedtime boat-ramp tale needs a boat, a slippery ramp, and a small bruise-worthy bump.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime boat-ramp story world with humor, teamwork, and a tiny bruise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES if helper_gender == "father" else GIRL_NAMES)
    parent_name = args.parent_name or rng.choice(GIRL_NAMES if parent_gender == "mother" else BOY_NAMES)
    return StoryParams(setting, action, comfort, child_name, child_gender, helper_name, helper_gender, parent_name, parent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    action = f["action"]
    return [
        f'Write a bedtime story set at {setting.place} where a child wants to {action.plan} and someone uses humor and teamwork.',
        f"Tell a gentle story with the words 'four' and 'bruise' about {f['child'].id} at the boat ramp, ending safely at bedtime.",
        f'Write a cozy story in which {f["child"].id} bumps a shin at the water, then the family laughs and works together to finish the job.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent = f["child"], f["helper"], f["parent"]
    setting, action = f["setting"], f["action"]
    qa = [
        ("Where does the story happen?",
         f"It happens at {setting.place}. The wet ramp and the water are the important parts of the place."),
        ("What did the child want to do?",
         f"{child.id} wanted to {action.verb}. It sounded like a simple bedtime errand, but the ramp was slippery."),
        ("What made the child laugh?",
         f"{helper.id}'s joke about the little boat made {child.id} laugh. Humor helped the hard job feel lighter."),
        ("What small mishap happened?",
         f"{child.id} bumped a shin on the ramp and got a small bruise. It was a little hurt, not a big disaster."),
        ("How did the family solve the problem?",
         f"They used teamwork: one steady hand, one rope, and careful steps. That kept the boat balanced and let everyone finish safely."),
    ]
    qa.append((
        "How did the story end?",
        f"It ended quietly at bedtime, with the boat safe by the water and {child.id} snug at home. The bruise was tiny, and the family had turned the tricky moment into a funny, kind memory."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a boat ramp?",
         "A boat ramp is a sloped place where people roll or carry a boat into the water. The slope makes it easier for boats to reach the lake or river."),
        ("Why can a wet ramp be tricky?",
         "A wet ramp can be slippery, so shoes can slide on it. Careful steps and teamwork help keep people safe."),
        ("What is a bruise?",
         "A bruise is a sore spot on the skin that can turn blue, purple, or dark after a bump. It usually gets better with time."),
        ("What is teamwork?",
         "Teamwork means people help each other do one job together. When everyone takes a part, the job can feel easier."),
        ("Why can humor help?",
         "Humor can make people smile when a job is hard or a little scary. A laugh can help a family stay calm and keep going."),
    ]


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
    lines.append("== (3) World knowledge ==")
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
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
bruise(child) :- bumped(child).
steady(boat) :- teamwork(child, helper), help(child), help(helper).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    # smoke test generate
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, action=None, comfort=None,
            child_name=None, child_gender=None, helper_name=None, helper_gender=None,
            parent_name=None, parent_gender=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP combos differ from Python combos")
        rc = 1
    else:
        print(f"OK: ASP matches Python for {len(valid_combos())} combos.")
    print("OK: generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], COMFORTS[params.comfort],
                 params.child_name, params.child_gender, params.helper_name,
                 params.helper_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("boat_ramp", "carry_boat", "blanket", "Mila", "girl", "Dad", "father", "Mom", "mother"),
    StoryParams("boat_ramp", "guide_boat", "teddy", "Finn", "boy", "Mom", "mother", "Dad", "father"),
    StoryParams("dock", "carry_boat", "pillow", "Ruby", "girl", "Dad", "father", "Mom", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.child_name}: {p.setting} / {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
