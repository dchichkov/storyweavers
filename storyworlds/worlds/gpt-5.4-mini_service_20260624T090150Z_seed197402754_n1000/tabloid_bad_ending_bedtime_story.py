#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Tabloid:
    id: str
    headline: str
    rumor: str
    fear_word: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    tabloid: str
    comfort: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "bedroom": Setting(place="the bedroom", afford={"read"}),
    "living_room": Setting(place="the living room", afford={"read"}),
    "camp_room": Setting(place="the bunk room", afford={"read"}),
}

TABLOIDS = {
    "ghost": Tabloid(
        id="ghost",
        headline="Ghost Seen at Midnight!",
        rumor="a ghost was hiding in the hall",
        fear_word="spooky",
        twist="the shadow was only a coat on a hook",
        tags={"night", "shadow", "ghost"},
    ),
    "thief": Tabloid(
        id="thief",
        headline="Sneaky Thief Near the Window!",
        rumor="a thief was peeking through the window",
        fear_word="worrisome",
        twist="the window tapping came from a branch",
        tags={"window", "thief", "branch"},
    ),
    "storm": Tabloid(
        id="storm",
        headline="Storm Shakes the House!",
        rumor="a giant storm was rushing closer",
        fear_word="loud",
        twist="the rattle was only soft rain on the roof",
        tags={"storm", "rain", "roof"},
    ),
    "monster": Tabloid(
        id="monster",
        headline="Monster Under the Bed!",
        rumor="a monster was under the bed",
        fear_word="shivery",
        twist="the bump was only a dropped pillow",
        tags={"bed", "monster", "pillow"},
    ),
}

COMFORTS = {
    "night_light": Comfort(
        id="night_light",
        label="a little night-light",
        action="turn on",
        effect="made a small warm circle of light",
        tags={"night", "dark"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="a soft blanket",
        action="pull up",
        effect="wrapped the child in a cozy puff of warmth",
        tags={"bed", "cozy"},
    ),
    "story": Comfort(
        id="story",
        label="a sleepy storybook",
        action="read from",
        effect="gave the room a hush like falling snow",
        tags={"book", "sleep"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Lily", "Theo"]
TRAITS = ["sleepy", "curious", "brave", "gentle", "thoughtful", "small"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, c) for s in SETTINGS for t in TABLOIDS for c in COMFORTS]


@dataclass
class Reasoning:
    fear: float = 0.0
    sleep: float = 1.0
    relief: float = 0.0


def _scare(world: World, child: Entity, tabloid: Tabloid) -> list[str]:
    if child.meters.get("read", 0) < 1:
        return []
    if child.memes.get("fear", 0) >= 1:
        return []
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.meters["sleep"] = max(0.0, child.meters.get("sleep", 1.0) - 0.7)
    return [f"{child.id}'s eyes went wide, and {child.pronoun('possessive')} heart beat fast."]


def _restless(world: World, child: Entity) -> list[str]:
    if child.meters.get("sleep", 1.0) > 0.2:
        return []
    if child.memes.get("restless", 0) >= 1:
        return []
    child.memes["restless"] = 1
    return [f"{child.id} could not settle down again."]


def _comfort_fails(world: World, child: Entity, parent: Entity, comfort: Comfort, tabloid: Tabloid) -> list[str]:
    if child.memes.get("fear", 0) < 1:
        return []
    if child.memes.get("relief", 0) >= 1:
        return []
    child.memes["relief"] = 1
    child.meters["sleep"] = max(0.0, child.meters.get("sleep", 1.0) - 0.1)
    return [f"{parent.id} tried to help, but the worry stayed in the room."]


def propagate(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    tabloid = world.facts["tabloid"]
    comfort = world.facts["comfort"]
    out = []
    out.extend(_scare(world, child, tabloid))
    out.extend(_comfort_fails(world, child, parent, comfort, tabloid))
    out.extend(_restless(world, child))
    for s in out:
        world.say(s)
    return out


def get_hero_phrase(name: str, gender: str) -> str:
    trait = "little"
    return f"{trait} {gender} {name}"


def tell(setting: Setting, tabloid: Tabloid, comfort: Comfort, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, meters={"sleep": 1.0}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    paper = world.add(Entity(id="tabloid", type="tabloid", label="tabloid", phrase=tabloid.headline))
    world.facts["tabloid"] = tabloid
    world.facts["comfort"] = comfort
    world.facts["child"] = child
    world.facts["parent"] = parent

    world.say(f"At {setting.place}, {name} was a sleepy child who liked the quiet before bed.")
    world.say(f"One evening, {name} found a tabloid with the headline '{tabloid.headline}'.")
    world.say(f"It said {tabloid.rumor}, which felt {tabloid.fear_word} in the dim room.")
    world.para()
    child.meters["read"] = 1
    propagate(world)
    world.say(f"{parent.id.capitalize()} tried to be calm and {comfort.action} {comfort.label}.")
    world.say(f"{comfort.effect}, but the bad idea from the tabloid still clung to {name}.")
    world.para()
    world.say(f"By the end of bedtime, {name} was still awake, listening hard to every small sound.")
    world.say(f"The final bump turned out to be {tabloid.twist}, but {name} did not feel brave enough to sleep.")
    world.facts["ending_bad"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    tab = world.facts["tabloid"]
    com = world.facts["comfort"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        "Write a short bedtime story with a tabloid, a frightened child, and a bad ending.",
        f"Tell a gentle but unsettling bedtime story where {child.label} reads a tabloid about {tab.rumor} and {parent.id} tries {com.label}.",
        f"Write a child-friendly story in which a tabloid headline makes bedtime harder instead of better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    tab = world.facts["tabloid"]
    com = world.facts["comfort"]
    return [
        QAItem(
            question=f"What did {c.label} find at bedtime?",
            answer=f"{c.label} found a tabloid with the headline '{tab.headline}'.",
        ),
        QAItem(
            question=f"Why did {c.label} feel scared?",
            answer=f"{c.label} felt scared because the tabloid said {tab.rumor}.",
        ),
        QAItem(
            question=f"What did {p.id.capitalize()} try to do to help?",
            answer=f"{p.id.capitalize()} tried to {com.action} {com.label}, but it did not fully chase the worry away.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {c.label} was still awake and uneasy at bedtime, even after the helper tried to comfort them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tab = world.facts["tabloid"]
    com = world.facts["comfort"]
    out = [
        QAItem(
            question="What is a tabloid?",
            answer="A tabloid is a newspaper or magazine that uses loud, attention-grabbing headlines.",
        ),
        QAItem(
            question="Why can a scary headline bother someone at night?",
            answer="A scary headline can make a person imagine danger in the dark, which makes it harder to relax and fall asleep.",
        ),
    ]
    if "night" in tab.tags:
        out.append(QAItem(
            question="What is a night-light for?",
            answer="A night-light gives a small soft light that helps a room feel less dark at bedtime.",
        ))
    if "bed" in com.tags:
        out.append(QAItem(
            question="What is a blanket for?",
            answer="A blanket keeps someone warm and cozy while they rest.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for tid, t in TABLOIDS.items():
        lines.append(asp.fact("tabloid", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("helps_with", cid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,T,C) :- setting(S), tabloid(T), comfort(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with a tabloid and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tabloid", choices=TABLOIDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.tabloid:
        combos = [c for c in combos if c[1] == args.tabloid]
    if args.comfort:
        combos = [c for c in combos if c[2] == args.comfort]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tabloid, comfort = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, tabloid=tabloid, comfort=comfort, name=name, gender=args.gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TABLOIDS[params.tabloid], COMFORTS[params.comfort], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for s, t, c in combos:
            print(f"  {s} {t} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for t in TABLOIDS:
                for c in COMFORTS:
                    p = StoryParams(setting=s, tabloid=t, comfort=c, name=NAMES[0], gender="girl", parent="mother")
                    samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
