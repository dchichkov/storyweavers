#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vaseline_cranapple_twist_nursery_rhyme.py
==========================================================================

A tiny standalone storyworld for a nursery-rhyme style tale about a child,
a sticky mix-up, a twist, and a bright repair.

Seed idea
---------
A little child wants to make something shiny for a fair or a gift, reaches for
vaseline and cranapple, makes a muddle, then learns a safer, sweeter way after a
Twist: the helper changes the plan and the ending becomes neat and cheerful.

Domain
------
- vaseline: a slick, sealing balm used by a grown-up
- cranapple: a sweet red fruit paste / jam for a snack or topping
- Twist: the story beat where the plan turns from sticky trouble to a tidy fix

This world keeps the prose close to a nursery rhyme: simple, rhythmic, concrete,
and child-facing, while still being driven by an explicit simulated world model.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/vaseline_cranapple_twist_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/vaseline_cranapple_twist_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/vaseline_cranapple_twist_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/vaseline_cranapple_twist_nursery_rhyme.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
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
    mood: str
    rhyme_image: str
    affords: set[str] = field(default_factory=set)

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
class Activity:
    id: str
    verb: str
    line: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    flavor: str
    plural: bool = False
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
class TwistOption:
    id: str
    line: str
    fix_line: str
    makes_sense: int
    power: int
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
        self.zone: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sticky"] < THRESHOLD:
            continue
        sig = ("smear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trouble"] += 1
        if "bowl" in world.entities:
            world.get("bowl").meters["mess"] += 1
        out.append("__smear__")
    return out


def _r_tidy(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    if not bowl or bowl.meters["mess"] < THRESHOLD:
        return out
    sig = ("tidy", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("counter").meters["clean"] += 1
    out.append("__tidy__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["worry"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return out
    sig = ("twist", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    helper.memes["pride"] += 1
    out.append("__twist__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_smear, _r_tidy, _r_twist):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(twist: TwistOption, prize: Prize) -> bool:
    return twist.makes_sense >= SENSE_MIN and prize.region in {"mouth", "hands", "counter"}


def best_twist() -> TwistOption:
    return max(TWISTS.values(), key=lambda t: t.makes_sense)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "mess": sim.get(prize_id).meters["mess"],
        "trouble": sim.get(actor.id).memes["trouble"],
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["sticky"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def start(world: World, child: Entity, helper: Entity, setting: Setting, prize: Prize) -> None:
    world.say(
        f"On a bright little day in {setting.place}, {child.id} and {helper.id} "
        f"began a rhyme to play."
    )
    world.say(
        f"The air was {setting.mood}, and {setting.rhyme_image}."
    )
    world.say(
        f"{child.id} loved {setting.place} games and sweet things, and {helper.id} "
        f"kept the bowls and spoons in rings."
    )
    world.say(
        f"{child.id} eyed {prize.phrase} with a grin so wide."
    )


def want(world: World, child: Entity, activity: Activity, prize: Prize) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Let me {activity.verb}," said {child.id}, "and make {prize.phrase} shine!"'
    )
    world.say(f"It seemed like a merry plan, but it was not the tidy kind.")


def warn(world: World, helper: Entity, child: Entity, activity: Activity, prize: Prize) -> None:
    child.memes["worry"] += 1
    pred = predict_mess(world, child, activity, prize.id)
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'"Oh no," said {helper.id}, "that could make the {prize.label} a mess. '
        f"{prize.label.capitalize()} should stay neat, not sticky as glue."
    )


def defy(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubborn"] += 1
    world.say(f"But {child.id} skipped ahead with a hop and a twirl.")
    world.say(f"Off {child.id} went to {activity.rush} in a whirl.")


def spill(world: World, bowl: Entity, prize: Prize, activity: Activity) -> None:
    bowl.meters["mess"] += 1
    world.say(
        f"The bowl got a sticky surprise, and {prize.label} began to smear. "
        f"The sweet red shine looked funny, then suddenly unclear."
    )
    world.say(
        f"The room felt small and fussy, like a rhyme gone wrong."
    )


def rescue(world: World, helper: Entity, child: Entity, twist: TwistOption, prize: Prize) -> None:
    helper.memes["calm"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"Then came the Twist: {twist.line}"
    )
    world.say(
        f"{helper.id} smiled and {twist.fix_line}."
    )
    world.say(
        f"The bowl was wiped, the counter shone, and {prize.label} stayed just right."
    )


def ending(world: World, child: Entity, helper: Entity, prize: Prize) -> None:
    child.memes["joy"] += 1
    world.say(
        f"So {child.id} and {helper.id} laughed, and the little day grew light."
    )
    world.say(
        f"{prize.label.capitalize()} sat neat as a button, red and sweet and bright."
    )
    world.say(
        "That is how the twist made tidy things from a sticky start."
    )


def tell(setting: Setting, activity: Activity, prize: Prize, twist: TwistOption,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Mama", helper_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    bowl = world.add(Entity(id="bowl", type="thing", label="the bowl"))
    counter = world.add(Entity(id="counter", type="thing", label="the counter"))

    start(world, child, helper, setting, prize)
    world.para()
    want(world, child, activity, prize)
    warn(world, helper, child, activity, prize)
    defy(world, child, activity)
    world.para()
    _do_activity(world, child, activity, narrate=False)
    spill(world, bowl, prize, activity)
    rescue(world, helper, child, twist, prize)
    ending(world, child, helper, prize)

    world.facts.update(
        child=child, helper=helper, bowl=bowl, counter=counter,
        setting=setting, activity=activity, prize=prize, twist=twist,
        outcome="twisted",
        twisted=child.memes["hope"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "warm and sunny", "a spoon was tapping on a tin", {"mix"}),
    "parlor": Setting("parlor", "the parlor", "quiet and bright", "the lamp was blinking like a star", {"mix"}),
    "garden": Setting("garden", "the garden table", "fresh and fair", "the birds were peeping from the pear tree", {"mix"}),
}

ACTIVITIES = {
    "mix": Activity(
        "mix",
        "mix it up",
        "mixing it up",
        "stir to make it rush",
        "sticky",
        {"hands", "counter", "mouth"},
        "mix",
        {"sticky"},
    ),
}

PRIZES = {
    "toast": Prize("toast", "toast", "the toast", "mouth", "plain", False, {"food"}),
    "bowl": Prize("bowl_prize", "the little bowl", "the little bowl", "hands", "plain", False, {"object"}),
    "jam": Prize("jam", "cranapple jam", "the cranapple jam", "counter", "sweet", False, {"food"}),
    "cake": Prize("cake", "a tiny cake", "the tiny cake", "counter", "sweet", False, {"food"}),
}

TWISTS = {
    "wipe": TwistOption("wipe", "the helper fetched a cloth and gave the bowl a flip", "wiped the bowl clean with a cloth", 3, 3, {"cloth"}),
    "swap": TwistOption("swap", "the helper swapped the sticky spoon for a clean one", "picked a clean spoon and stirred again", 2, 2, {"spoon"}),
    "share": TwistOption("share", "the helper set out a little plate for the cranapple treat", "set out a plate and served the cranapple treat", 3, 3, {"plate"}),
}

NAMES = ["Mina", "Lia", "Tess", "Nora", "June", "Ivy", "Finn", "Ben", "Theo", "Ada"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                if reasonableness_gate(best_twist(), PRIZES[p]):
                    out.append((s, a, p))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    twist: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


KNOWLEDGE = {
    "vaseline": [("What is vaseline?", "Vaseline is a smooth, slippery balm grown-ups use to protect skin. It is not a toy.")],
    "cranapple": [("What is cranapple?", "Cranapple is a sweet red fruit treat, like a jam or spread made from cranberries and apples.")],
    "twist": [("What does a twist mean in a story?", "A twist is a turn in the plan. Something changes, and the story goes in a new direction.")],
    "sticky": [("Why can sticky things be messy?", "Sticky things cling to fingers and bowls, so they can make a clean place look smeared.")],
    "clean": [("Why do people keep things clean?", "Clean things are easier to use and nicer to look at, and they are simpler to share.")],
}
KNOWLEDGE_ORDER = ["vaseline", "cranapple", "twist", "sticky", "clean"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story using the words "{f["activity"].keyword}", "vaseline", and "cranapple".',
        f"Tell a small story where {f['child'].id} tries to {f['activity'].verb} with cranapple, but a helper makes a Twist and saves the day.",
        f"Write a sing-song story about a sticky mistake, a calm helper, and a neat ending with cranapple.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, prize, activity = f["child"], f["helper"], f["prize"], f["activity"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who are busy with a small kitchen task."),
        ("What did the child want to do?", f"{child.id} wanted to {activity.verb}, hoping to make {prize.phrase} shine."),
        ("What happened after the child ignored the warning?", f"The bowl got sticky and the {prize.label} started to smear. The room turned messy before the Twist fixed it."),
        ("How did the helper fix the problem?", f"The helper made a Twist, used a clean cloth, and turned the sticky mess into a tidy table again."),
        ("How did the story end?", f"It ended with {prize.label.capitalize()} neat and bright, and the child happy and calm."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["activity"].tags) | set(world.facts["prize"].tags) | set(world.facts["twist"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


CURATED = [
    StoryParams("kitchen", "mix", "jam", "wipe", "Mina", "girl", "Mama", "mother"),
    StoryParams("parlor", "mix", "toast", "swap", "Lia", "girl", "Mama", "mother"),
    StoryParams("garden", "mix", "cake", "share", "Ben", "boy", "Dad", "father"),
]


ASP_RULES = r"""
valid(S, A, P) :- setting(S), activity(A), prize(P), sense_ok(P).
sense_ok(P) :- prize(P), region(P, R), R = mouth; R = hands; R = counter.
outcome(twisted) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("sense", tid, t.makes_sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, activity=None, prize=None, twist=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: vaseline, cranapple, and a Twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice(["Mama", "Mara", "Nana", "Papa", "Dada"])
    return StoryParams(setting, activity, prize, twist, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        TWISTS[params.twist],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, a, p in asp_valid_combos():
            print(f"  {s:8} {a:6} {p}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
