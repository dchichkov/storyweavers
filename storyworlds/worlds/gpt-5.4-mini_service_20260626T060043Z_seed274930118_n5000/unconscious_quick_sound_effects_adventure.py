#!/usr/bin/env python3
"""
storyworlds/worlds/unconscious_quick_sound_effects_adventure.py
===============================================================

A small Adventure-style story world about a quick rescue, a noisy plan, and a
child-friendly turn from worry to relief.

Premise:
- A brave child explorer and a small companion head out on a quick adventure.
- They hear strange sound effects in a windy place.
- They discover a friend who is unconscious after a tumble.
- The explorer uses simple, loud sound effects to call for help and wake the friend.
- The story ends with the group safely together and the adventure continuing.

This world is intentionally narrow: only a few plausible combinations are
considered reasonable, so the stories stay strong and causal.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the windy ridge"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    risk: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_attracts(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["alert"] += 1
        out.append(f"The noise made {actor.id} look around fast.")
    return out


def _r_unconscious_to_awake(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["unconscious"] < THRESHOLD:
            continue
        if actor.meters["help"] < THRESHOLD:
            continue
        sig = ("wake", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["unconscious"] = 0.0
        actor.memes["awake"] += 1
        out.append(f"{actor.id} stirred and blinked awake.")
    return out


def _r_help_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["awake"] < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] += 1
        out.append(f"{actor.id} felt safer now.")
    return out


CAUSAL_RULES = [
    Rule("noise_attracts", "social", _r_noise_attracts),
    Rule("unconscious_to_awake", "social", _r_unconscious_to_awake),
    Rule("help_brings_relief", "social", _r_help_brings_relief),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hero_line(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    return f"{hero.id} was a little {trait} {hero.type} who loved adventures."


def setting_line(setting: Setting, action: Action) -> str:
    if setting.indoors:
        return f"The {setting.place} was dark and echoey, and every footstep came back like {action.sound}."
    return f"The {setting.place} was open to the sky, and the wind carried little sound effects through the rocks."


def action_line(hero: Entity, action: Action) -> str:
    return f"{hero.id} loved {action.gerund}, especially when the day felt like a quest."


def warning_line(parent: Entity, hero: Entity, tool: Entity, action: Action) -> str:
    return (
        f'{hero.pronoun("possessive").capitalize()} {parent.label or parent.type} said, '
        f'"If someone is hurt, we use the {tool.label} and stay quick."'
    )


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters["noise"] += 1
    actor.meters["speed"] += 1
    actor.memes["excited"] += 1
    world.zone = set(action.zone)
    propagate(world, narrate=narrate)


def quick_rescue(world: World, hero: Entity, friend: Entity, tool: Entity, action: Action) -> None:
    hero.meters["help"] += 1
    friend.meters["help"] += 1
    friend.memes["unconscious"] += 1
    world.say(
        f"{hero.id} gave a quick {tool.phrase}, and the sound bounced off the rocks like {action.sound}."
    )
    propagate(world, narrate=True)


SETTINGS = {
    "ridge": Setting(place="the windy ridge", indoors=False, affords={"echo", "call"}),
    "cave": Setting(place="the echo cave", indoors=True, affords={"echo", "call"}),
    "harbor": Setting(place="the little harbor", indoors=False, affords={"call", "signal"}),
}

ACTIONS = {
    "echo": Action(
        id="echo",
        verb="explore the echoing path",
        gerund="exploring echoing paths",
        rush="run to the next bend",
        sound="tap-tap",
        risk="a fall in the dark",
        zone={"feet", "torso"},
        keyword="echo",
        tags={"sound", "adventure"},
    ),
    "call": Action(
        id="call",
        verb="call through the rocks",
        gerund="calling into the wind",
        rush="shout across the gap",
        sound="clap-clap",
        risk="getting separated",
        zone={"torso"},
        keyword="call",
        tags={"sound", "adventure"},
    ),
    "signal": Action(
        id="signal",
        verb="signal for help",
        gerund="signaling for help",
        rush="wave the lantern fast",
        sound="ding-ding",
        risk="missing the rescue boat",
        zone={"hands", "torso"},
        keyword="signal",
        tags={"sound", "adventure"},
    ),
}

TOOLS = {
    "whistle": Tool(
        id="whistle",
        label="whistle",
        phrase="quick whistle notes",
        helps={"call", "signal"},
    ),
    "clapper": Tool(
        id="clapper",
        label="wooden clapper",
        phrase="sharp clack-clack beats",
        helps={"echo", "call"},
    ),
    "bell": Tool(
        id="bell",
        label="little bell",
        phrase="bright ring-ring sounds",
        helps={"signal", "echo"},
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Luna", "Ivy", "Nora", "Zoe"]
BOY_NAMES = ["Pico", "Jasper", "Toby", "Finn", "Ravi", "Owen"]
TRAITS = ["curious", "brave", "quick", "lively", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if act_id in tool.helps:
                    combos.append((place, act_id, tool_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def explain_rejection(action: Action, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} does not fit this adventure. "
        f"It helps with {', '.join(sorted(tool.helps))}, not with {action.id}.)"
    )


def explain_gender(gender: str, tool: str) -> str:
    return f"(No story: try a different gender or tool combination for the {tool}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world about a quick rescue and loud sound effects."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.action and args.tool:
        action = ACTIONS[args.action]
        tool = TOOLS[args.tool]
        if args.action not in tool.helps:
            raise StoryError(explain_rejection(action, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, action=action, tool=tool_id, name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    action = ACTIONS[params.action]
    tool_def = TOOLS[params.tool]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "quick"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    friend = world.add(Entity(id="Pebble", kind="character", type="boy", label="the friend"))
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, phrase=tool_def.phrase, owner=hero.id))
    tool.carried_by = hero.id
    friend.memes["unconscious"] = 1.0
    friend.meters["hurt"] = 1.0

    world.say(hero_line(hero))
    world.say(action_line(hero, action))
    world.say(
        f"One quick day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}."
    )
    world.say(setting_line(setting, action))
    world.para()
    world.say(
        f"Then {hero.id} heard a strange {action.sound} from behind a stone."
    )
    world.say(
        f"It was {friend.label}, lying still and unconscious after a tumble."
    )
    world.say(warning_line(parent, hero, tool, action))
    world.say(
        f"{hero.id} stayed calm, took a quick breath, and {action.rush}."
    )
    quick_rescue(world, hero, friend, tool, action)
    world.say(
        f"{hero.id} used the {tool.label} again: {tool.phrase}, {tool.phrase}, {tool.phrase}."
    )
    world.say(
        f"At last, {friend.id} opened {friend.pronoun('possessive')} eyes and smiled."
    )
    world.para()
    world.say(
        f"Together they followed the echoing trail home, and the adventure felt brave instead of scary."
    )

    world.facts.update(hero=hero, parent=parent, friend=friend, tool=tool, action=action, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    tool = f["tool"]
    return [
        f'Write an adventure story for a young child about {hero.id}, who makes quick sound effects to help a friend.',
        f'Tell a story where "{action.keyword}" sounds lead to a rescue and a {tool.label} helps.',
        f'Write a short, child-friendly adventure with an unconscious friend, a quick decision, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    friend = f["friend"]
    action = f["action"]
    tool = f["tool"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who went on the adventure at {place}?",
            answer=f"{hero.id} went with {hero.pronoun('possessive')} {parent.label} to {place}, and {friend.id} was the friend they found."
        ),
        QAItem(
            question=f"What did {hero.id} hear before finding {friend.id}?",
            answer=f"{hero.id} heard a strange {action.sound} and followed it to the stone."
        ),
        QAItem(
            question=f"How did the {tool.label} help?",
            answer=f"The {tool.label} made quick {tool.phrase}, and those sounds helped call attention and bring the friend back awake."
        ),
        QAItem(
            question=f"Why was the friend scary at first?",
            answer=f"{friend.id} was unconscious after a tumble, so {hero.id} had to stay calm and help quickly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off a wall, cliff, or cave and comes back to you."
        ),
        QAItem(
            question="Why are whistles useful on adventures?",
            answer="Whistles make clear, quick sounds that are easy to hear from far away."
        ),
        QAItem(
            question="What does it mean to be quick?",
            answer="Being quick means moving or acting fast when the moment matters."
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", action="echo", tool="clapper", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="ridge", action="call", tool="whistle", name="Ravi", gender="boy", parent="father", trait="brave"),
    StoryParams(place="harbor", action="signal", tool="bell", name="Toby", gender="boy", parent="mother", trait="quick"),
]


ASP_RULES = r"""
valid(Place, Action, Tool) :- place(Place), affords(Place, Action), tool(Tool), helps(Tool, Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for z in sorted(action.zone):
            lines.append(asp.fact("zone", aid, z))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, action, tool) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.action} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
