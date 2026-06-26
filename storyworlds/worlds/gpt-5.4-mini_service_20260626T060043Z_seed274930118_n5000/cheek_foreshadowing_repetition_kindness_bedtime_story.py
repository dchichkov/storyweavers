#!/usr/bin/env python3
"""
storyworlds/worlds/cheek_foreshadowing_repetition_kindness_bedtime_story.py
============================================================================

A tiny bedtime-story world about a child, a softly foreshadowed cheek, a gentle
problem at night, and a kind resolution with repetition in the prose.

Initial story seed:
---
A child gets ready for bed. Earlier in the day, their cheek was a little warm,
and that small detail quietly foreshadows that they may not feel well later.
At bedtime, the child tries to settle down, repeating a small sleepy phrase
while a parent notices the red cheek. With kindness, the family brings a cool
cloth, a cup of water, and a gentle kiss. The child falls asleep feeling safe.
---

World model:
---
    parent notices warm cheek earlier   -> concern += 1, foresight += 1
    bedtime routine repeated            -> calm += 1, sleepiness += 1
    kind care given                     -> comfort += 2, concern -= 1
    cool cloth on cheek                 -> warmth -= 1, sleepiness += 1
    lullaby repetition                  -> calm += 1, love += 1
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=lambda: {"bedtime", "lullaby"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    keyword: str
    kind: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str]
    kind: str = "comfort"


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_warm_cheek(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters.get("warm_cheek", 0.0) < THRESHOLD:
        return out
    sig = ("notice_warm_cheek",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["concern"] = child.memes.get("concern", 0.0) + 1
    out.append("The warm cheek made the parent look twice.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes.get("concern", 0.0) < THRESHOLD:
        return out
    if parent.meters.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness_soothes",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["comfort"] = child.memes.get("comfort", 0.0) + 2
    child.memes["concern"] = max(0.0, child.memes.get("concern", 0.0) - 1)
    out.append("Kind hands brought comfort to the tired face.")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("comfort", 0.0) < THRESHOLD:
        return out
    sig = ("sleep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sleepiness"] = child.meters.get("sleepiness", 0.0) + 1
    out.append("The child grew sleepy and still.")
    return out


CAUSAL_RULES = [_r_warm_cheek, _r_kindness, _r_sleep]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadow(world: World, child: Entity, action: Action) -> None:
    child.meters["warm_cheek"] = child.meters.get("warm_cheek", 0.0) + 1
    child.memes["foresight"] = child.memes.get("foresight", 0.0) + 1
    world.say(
        f"Earlier that day, {child.id}'s cheek felt a little warm, and that small "
        f"feeling quietly hinted that bedtime might need extra care."
    )


def bedtime_routine(world: World, child: Entity, parent: Entity, action: Action) -> None:
    child.memes["sleepiness"] = child.memes.get("sleepiness", 0.0) + 1
    parent.memes["kindness"] = parent.memes.get("kindness", 0.0) + 1
    world.say(
        f"At bedtime, {child.id} climbed under the blanket again and again, "
        f"whispering, \"Sleepy now, sleepy now,\" because repeating the words made "
        f"the room feel softer."
    )
    world.say(
        f"{parent.pronoun().capitalize()} tucked the blanket twice, once for the pillow "
        f"and once for the quiet moonlight at {world.setting.place}."
    )


def check_cheek(world: World, parent: Entity, child: Entity) -> None:
    world.say(
        f"{parent.pronoun().capitalize()} touched {child.pronoun('possessive')} cheek "
        f"and noticed it was warm."
    )
    propagate(world, narrate=True)


def kindness(world: World, parent: Entity, child: Entity, comfort: Comfort) -> None:
    parent.meters["kindness"] = parent.meters.get("kindness", 0.0) + 1
    child.memes["comfort"] = child.memes.get("comfort", 0.0) + 1
    world.say(
        f"With kindness, {parent.id} brought {comfort.phrase}, a sip of water, and a "
        f"gentle kiss on the cheek."
    )
    world.say(
        f"\"There, there,\" {parent.pronoun().capitalize()} said, and the soft voice "
        f"matched the slow ticking of the night."
    )
    propagate(world, narrate=True)


def repeat_lullaby(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["love"] = parent.memes.get("love", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    world.say(
        f"\"Hush now, hush now,\" {parent.id} sang, and then sang it again: "
        f"\"Hush now, hush now.\""
    )


def tell(setting: Setting, hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "mother", seed: Optional[int] = None) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="parent"))
    blanket = world.add(Entity(id="blanket", label="blanket"))
    cloth = world.add(Entity(id="cloth", label="cool cloth", phrase="a cool cloth"))
    child.location = setting.place
    parent.location = setting.place
    blanket.location = setting.place
    cloth.location = setting.place

    action = ACTIONS["bedtime"]
    comfort = COMFORTS["cloth"]

    world.say(
        f"{hero_name} was a little {hero_type} who liked the hush of {setting.place} "
        f"when the day was done."
    )
    world.say(
        f"All afternoon, {hero_name} had been bright and busy, and every now and then "
        f"{hero_name}'s cheek felt just a tiny bit warm."
    )
    foreshadow(world, child, action)

    world.para()
    bedtime_routine(world, child, parent, action)
    check_cheek(world, parent, child)
    world.say(
        f"{child.id} tried to stay brave, but the warm cheek made the pillow feel less "
        f"soft for a moment."
    )

    world.para()
    kindness(world, parent, child, comfort)
    repeat_lullaby(world, parent, child)
    world.say(
        f"The cool cloth rested on the cheek for a little while, and the warmth slipped "
        f"away like a mouse behind a curtain."
    )
    world.say(
        f"Then {child.id} smiled, sank deeper into the blanket, and fell asleep while "
        f"{parent.id} kept watch beside the bed."
    )

    world.facts.update(
        child=child,
        parent=parent,
        action=action,
        comfort=comfort,
        setting=setting,
    )
    return world


ACTIONS = {
    "bedtime": Action(
        id="bedtime",
        verb="go to bed",
        gerund="going to bed",
        keyword="sleepy",
        kind="routine",
        effect="calm",
        tags={"bedtime", "sleep", "moon"},
    )
}

COMFORTS = {
    "cloth": Comfort(
        id="cloth",
        label="cool cloth",
        phrase="a cool cloth",
        helps={"warm_cheek"},
    )
}

SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"bedtime"}),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Clara"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Finn", "Jasper"]


@dataclass
class StoryParams:
    setting: str = "bedroom"
    name: str = "Milo"
    gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a gentle bedtime story that includes the word "cheek".',
        f"Tell a bedtime story about {child.label} feeling warm-cheeked, where "
        f"{f['parent'].label} responds with kindness and the ending is calm.",
        "Write a small story with a little foreshadowing, a repeated sleepy phrase, "
        "and a kind act before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"Why did {child.label} need extra care at bedtime?",
            answer=(
                f"{child.label}'s cheek felt warm earlier, and that little sign "
                f"foreshadowed that {child.label} might not feel fully well at night."
            ),
        ),
        QAItem(
            question=f"What kind thing did {parent.label} do for {child.label}?",
            answer=(
                f"{parent.label} brought a cool cloth, gave a gentle kiss, and stayed "
                f"close while {child.label} settled under the blanket."
            ),
        ),
        QAItem(
            question=f"What repeated words helped the room feel sleepy?",
            answer=(
                f"{parent.label} sang, \"Hush now, hush now,\" and then sang the same "
                f"little line again."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=(
                f"{child.label} felt comforted, grew sleepy, and fell asleep safely "
                f"while {parent.label} watched beside the bed."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cheek?",
            answer=(
                "A cheek is the soft part of your face on the side of your mouth. "
                "People can smile with their cheeks, and cheeks can get warm or red."
            ),
        ),
        QAItem(
            question="What does foreshadowing mean?",
            answer=(
                "Foreshadowing is a hint that something important may happen later in "
                "the story."
            ),
        ),
        QAItem(
            question="Why do people repeat lullabies at bedtime?",
            answer=(
                "People repeat lullabies because steady, familiar words can feel calm "
                "and safe and help a child relax."
            ),
        ),
        QAItem(
            question="What does kindness mean?",
            answer=(
                "Kindness means choosing to help, comfort, or care for someone in a "
                "gentle way."
            ),
        ),
    ]


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% If the cheek is warm, there is something to notice.
needs_care(child) :- warm_cheek(child).

% Kindness reduces concern and increases comfort.
comforted(child) :- needs_care(child), kindness(parent).

% A story is valid when it contains bedtime, foreshadowing, repetition, and kindness.
valid_story(setting) :- setting(bedroom), foreshadowed(child), repeated_lullaby(parent), kindness(parent).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("tagged", aid, "bedtime"))
        lines.append(asp.fact("tagged", aid, "sleep"))
        lines.append(asp.fact("tagged", aid, "moon"))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    lines.append(asp.fact("word", "cheek"))
    lines.append(asp.fact("feature", "foreshadowing"))
    lines.append(asp.fact("feature", "repetition"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    print("OK: ASP twin is present and the story world is reasonable.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small bedtime story world about cheek warmth, foreshadowing, repetition, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    setting = args.setting or "bedroom"
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.gender, params.parent, params.seed)
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
    StoryParams(setting="bedroom", name="Milo", gender="boy", parent="mother"),
    StoryParams(setting="bedroom", name="Luna", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:")
        print(sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
