#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/overalls_rescue_cautionary_bedtime_story.py
===========================================================================

A standalone storyworld for a bedtime-style cautionary tale about a child in
overalls, a risky nighttime choice, and a grown-up rescue.

The domain is intentionally small:
- a child wants to keep playing after bedtime,
- their overalls make it tempting to climb where they should not,
- a small mishap leads to a rescue,
- the story ends with a calm lesson and a safe bedtime image.

This script follows the Storyweavers contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BEDTIME_LIMIT = 7
CAUTION_MIN = 1
RESCUE_POWER_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "stuck": 0.0, "wet": 0.0, "scraped": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"curious": 0.0, "worry": 0.0, "fear": 0.0, "relief": 0.0, "love": 0.0, "lesson": 0.0}

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
    moonlight: str
    bedtime_image: str
    quiet_nook: str
    dark_spot: str
    rescue_spot: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    risky: bool = False
    rescue_needed: bool = False
    rescue_target: bool = False
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
class Action:
    id: str
    want: str
    do_verb: str
    risk: str
    consequence: str
    rescue_text: str
    lesson_text: str
    power: int
    sense: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.meters["tired"] >= THRESHOLD and ("tired",) not in world.fired:
        world.fired.add(("tired",))
        child.memes["worry"] += 1
        out.append("__tired__")
    return out


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.meters["stuck"] >= THRESHOLD and ("stuck",) not in world.fired:
        world.fired.add(("stuck",))
        child.memes["fear"] += 1
        out.append("__stuck__")
    return out


CAUSAL_RULES = [
    _r_tired,
    _r_stuck,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(action: Action, obj: ObjectThing, setting: Setting) -> bool:
    return action.sense >= CAUTION_MIN and obj.risky and setting.id in {"garden", "yard", "backyard"}


def rescue_possible(action: Action, obj: ObjectThing) -> bool:
    return action.power >= RESCUE_POWER_MIN and obj.rescue_needed and obj.rescue_target


def bedtime_scene(world: World, child: Entity, parent: Entity) -> None:
    child.memes["curious"] += 1
    world.say(
        f"At bedtime, {child.id} still wore {child.pronoun('possessive')} overalls, "
        f"and the little house was as quiet as a held breath."
    )
    world.say(
        f"The moon laid a silver stripe across {world.setting.place}, and {world.setting.bedtime_image}."
    )
    world.say(
        f"{child.id} peeked toward {world.setting.dark_spot}, where {world.setting.quiet_nook} looked like a secret place."
    )


def want_to_play(world: World, child: Entity, action: Action) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{child.id} wanted to {action.want}, because the night felt soft and unfinished."
    )


def warn(world: World, parent: Entity, child: Entity, action: Action, obj: ObjectThing) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Not now," {parent.id} said gently. "That {obj.label} is {action.risk}, and bedtime is for rest."'
    )
    world.say(
        f"{parent.id} pointed to the dark corner and reminded {child.pronoun('object')} that small feet can slip when the ground is slick."
    )


def defy(world: World, child: Entity, action: Action) -> None:
    child.memes["curious"] += 1
    world.say(
        f"But {child.id} thought the overalls made the idea feel brave, so {child.pronoun()} went anyway."
    )
    world.say(
        f"{child.id} tried to {action.do_verb}, and the night air suddenly felt colder."
    )


def mishap(world: World, child: Entity, obj: ObjectThing, action: Action) -> None:
    child.meters["stuck"] += 1
    child.meters["scraped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {obj.label} caught on a little hook near the rescue spot, and {child.id} got stuck."
    )
    world.say(
        f"{action.consequence.capitalize()}, and the overalls tugged at {child.pronoun('possessive')} knees."
    )


def rescue(world: World, parent: Entity, child: Entity, action: Action, obj: ObjectThing) -> None:
    child.meters["stuck"] = 0.0
    child.meters["safe"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{parent.id} hurried over with a calm flashlight and helped {child.pronoun('object')} back carefully."
    )
    world.say(
        f"{action.rescue_text}. {parent.id} held {child.pronoun('object')} close until {child.id} could breathe easy again."
    )


def lesson(world: World, parent: Entity, child: Entity, action: Action, obj: ObjectThing) -> None:
    child.memes["love"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'"We can be brave and still listen," {parent.id} said softly. "{action.lesson_text}"'
    )
    world.say(
        f"{child.id} nodded, and the overalls no longer felt like a license to ignore bedtime."
    )


def safe_ending(world: World, child: Entity, parent: Entity) -> None:
    child.meters["safe"] += 1
    world.say(
        f"After that, {child.id} went to bed, and the moon watched over the little room."
    )
    world.say(
        f"{parent.id} smoothed the blanket, and {child.id}'s overalls hung by the chair, waiting for daylight."
    )


def tell(setting: Setting, action: Action, obj: ObjectThing, child_name: str = "Nina",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=6))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    target = world.add(Entity(id="rescue", type="thing", label=obj.label, attrs={"object": obj.id}))

    child.meters["tired"] += 1
    bedtime_scene(world, child, parent)
    world.para()
    want_to_play(world, child, action)
    warn(world, parent, child, action, obj)
    world.para()
    defy(world, child, action)
    mishap(world, child, obj, action)
    if rescue_possible(action, obj):
        world.para()
        rescue(world, parent, child, action, obj)
        lesson(world, parent, child, action, obj)
    world.para()
    safe_ending(world, child, parent)

    world.facts.update(
        child=child,
        parent=parent,
        action=action,
        obj=obj,
        setting=setting,
        rescued=True,
        stuck=child.meters["stuck"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        moonlight="The moon laid a silver stripe over the garden path.",
        bedtime_image="the bean trellis made a long sleepy shadow",
        quiet_nook="the little gate by the shed",
        dark_spot="the far end of the garden",
        rescue_spot="a narrow path near the old trellis",
        tags={"garden", "night"},
    ),
    "yard": Setting(
        id="yard",
        place="the yard",
        moonlight="The moon turned the grass pale and still.",
        bedtime_image="the porch steps looked like a tidy row of sleepy teeth",
        quiet_nook="the corner by the rain barrel",
        dark_spot="the back of the yard",
        rescue_spot="the fence line",
        tags={"yard", "night"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        moonlight="Moonlight spilled across the fence and made everything silver-blue.",
        bedtime_image="the swing moved once in the breeze and then rested",
        quiet_nook="the path beside the rose bush",
        dark_spot="the shed door",
        rescue_spot="the climbing frame",
        tags={"backyard", "night"},
    ),
}

OBJECTS = {
    "rope": ObjectThing(
        id="rope",
        label="rope",
        phrase="a long garden rope",
        risky=True,
        rescue_needed=True,
        rescue_target=True,
        tags={"rope", "night", "rescue"},
    ),
    "cart": ObjectThing(
        id="cart",
        label="little cart",
        phrase="a little cart with squeaky wheels",
        risky=True,
        rescue_needed=True,
        rescue_target=True,
        tags={"cart", "night", "rescue"},
    ),
    "lantern": ObjectThing(
        id="lantern",
        label="lantern",
        phrase="a lantern with a bright glass door",
        risky=True,
        rescue_needed=True,
        rescue_target=True,
        tags={"lantern", "night", "rescue"},
    ),
}

ACTIONS = {
    "climb": Action(
        id="climb",
        want="climb the old trellis",
        do_verb="climb the trellis",
        risk="twisty and slippery after dusk",
        consequence="one foot slipped on a damp step",
        rescue_text="With one careful lift, the parent rescued the child from the hook and set both feet on solid ground",
        lesson_text="A bedtime game can wait until morning, when hands can see where to hold",
        power=2,
        sense=2,
        tags={"climb", "night", "cautionary"},
    ),
    "dash": Action(
        id="dash",
        want="dash toward the dark corner",
        do_verb="dash to the dark corner",
        risk="too dark to see well",
        consequence="a heel bumped the edge of a stone",
        rescue_text="The parent rescued the child by wrapping an arm around the waist and turning the child away from the dark corner",
        lesson_text="Night is not the best time for a fast game near stones and hooks",
        power=2,
        sense=2,
        tags={"dash", "night", "cautionary"},
    ),
    "reach": Action(
        id="reach",
        want="reach for the hidden lantern",
        do_verb="reach over the fence",
        risk="too close to the fence wire",
        consequence="the overalls snagged on a nail",
        rescue_text="The parent rescued the child by freeing the snag with steady fingers and a quiet voice",
        lesson_text="If something is out of reach at bedtime, a grown-up should help instead of climbing",
        power=1,
        sense=1,
        tags={"reach", "night", "cautionary"},
    ),
}


GIRL_NAMES = ["Nina", "Maya", "Lily", "Zoe", "Ava", "June"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Ben", "Sam"]


@dataclass
class StoryParams:
    setting: str
    action: str
    object: str
    child: str
    gender: str
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

CURATED = [
    StoryParams("garden", "climb", "rope", "Nina", "girl", "mother", seed=1),
    StoryParams("yard", "dash", "cart", "Eli", "boy", "father", seed=2),
    StoryParams("backyard", "reach", "lantern", "Maya", "girl", "mother", seed=3),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                if reasonable(action, obj, setting):
                    combos.append((sid, aid, oid))
    return combos


def explain_rejection(action: Action, obj: ObjectThing) -> str:
    return (
        f"(No story: the chosen risk does not support a believable bedtime rescue. "
        f"Try a safer match between the action and the object so the mishap can happen naturally.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime cautionary storyworld about overalls and rescue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
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
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, action, obj, child, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "overalls" and ends with a calm rescue.',
        f"Tell a cautionary bedtime story where {f['child'].id} wants to {f['action'].want} but gets into trouble, and a grown-up rescues {f['child'].pronoun('object')}.",
        f'Write a gentle story with moonlight, overalls, and a warning that bedtime play can go wrong near {f["obj"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    action = f["action"]
    obj = f["obj"]
    items = [
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {action.want}. It felt exciting because the night was quiet and the overalls made the idea seem brave."
        ),
        QAItem(
            question=f"Why did {parent.id} warn {child.id}?",
            answer=f"{parent.id} warned {child.id} because {obj.label} was {action.risk}. The grown-up could see that bedtime was not a safe time for that choice."
        ),
        QAItem(
            question=f"How was {child.id} rescued?",
            answer=f"{parent.id} rescued {child.id} by using calm hands and a calm voice. That helped {child.id} get back to solid ground and stop feeling stuck."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are overalls?",
            answer="Overalls are a kind of clothes that cover your body and usually have straps over the shoulders. People wear them for work or play, and they can make climbing feel extra sturdy."
        ),
        QAItem(
            question="Why is bedtime a time to slow down?",
            answer="Bedtime is for rest, so the body can get sleepy and safe. Quiet things help children settle down and keep accidents from happening in the dark."
        ),
        QAItem(
            question="What does a rescue mean?",
            answer="A rescue means helping someone out of a tight or risky spot. A rescue should be calm and careful so the person can feel safe again."
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(str(x) for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, O) :- setting(S), action(A), object(O), risky(O), caution(A), backyardish(S).
story(S, A, O) :- valid(S, A, O).
caution(A) :- action(A), sense(A, N), min_sense(M), N >= M.
backyardish(garden).
backyardish(yard).
backyardish(backyard).
risky(O) :- object(O), rescue_needed(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.risky:
            lines.append(asp.fact("risky", oid))
        if o.rescue_needed:
            lines.append(asp.fact("rescue_needed", oid))
    lines.append(asp.fact("min_sense", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, object=None, parent=None, gender=None, child=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], OBJECTS[params.object], params.child, params.gender, params.parent)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
