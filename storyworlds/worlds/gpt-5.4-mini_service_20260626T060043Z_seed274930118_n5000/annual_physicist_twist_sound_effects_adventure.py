#!/usr/bin/env python3
"""
storyworlds/worlds/annual_physicist_twist_sound_effects_adventure.py
====================================================================

A small standalone storyworld about an annual science adventure with a physicist,
a twist, and sound effects.

Premise:
- Every year, a child and a physicist prepare a little science adventure show.
- The physicist wants a loud sound-effects machine for the finale.
- A twist threatens the show, but the characters solve it by adjusting the setup.

The world is deliberately tiny and constraint-checked:
- The physicist's annual gear can break or jam.
- The twist may affect the machine, the sound effects, or the stage path.
- A reasonable fix must actually address the specific problem.

The story generator models physical meters and emotional memes, then narrates the
state changes into a short, child-friendly adventure tale.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    staged: bool = False
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "physicist"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind == "group" else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    verb: str
    effect: str
    target: str
    clue: str
    fix_hint: str
    resolves_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    label_phrase: str
    protects: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.twist: Optional[Twist] = None
        self.problem: str = ""

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.twist = self.twist
        clone.problem = self.problem
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    if not world.twist:
        return out
    physicist = next((e for e in world.characters() if e.type == "physicist"), None)
    if physicist is None:
        return out
    if physicist.meters.get(world.twist.target, 0.0) < THRESHOLD:
        return out
    sig = ("bump", world.twist.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    physicist.memes["surprise"] = physicist.memes.get("surprise", 0.0) + 1
    out.append(f"The setup gave a tiny bump and the show felt tricky for a moment.")
    return out


def _r_jam(world: World) -> list[str]:
    out: list[str] = []
    machine = world.entities.get("sound_machine")
    if machine is None:
        return out
    if machine.meters.get("jammed", 0.0) < THRESHOLD:
        return out
    sig = ("jam",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The sound effects machine gave a sad little sputter instead of a cheer.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if not world.twist:
        return out
    hero = next((e for e in world.characters() if e.id == "child"), None)
    phys = next((e for e in world.characters() if e.type == "physicist"), None)
    machine = world.entities.get("sound_machine")
    if not hero or not phys or not machine:
        return out
    if machine.meters.get("repaired", 0.0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    phys.memes["relief"] = phys.memes.get("relief", 0.0) + 1
    out.append("That made the whole stage ready again.")
    return out


CAUSAL_RULES = [Rule("bump", _r_bump), Rule("jam", _r_jam), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World, twist: Twist) -> dict[str, bool]:
    sim = world.copy()
    if twist.target == "machine":
        sim.get("sound_machine").meters["jammed"] = 1.0
    elif twist.target == "path":
        sim.get("stage_path").meters["blocked"] = 1.0
    elif twist.target == "volume":
        sim.get("sound_machine").meters["too_loud"] = 1.0
    propagate(sim, narrate=False)
    machine = sim.entities.get("sound_machine")
    blocked = sim.entities.get("stage_path")
    return {
        "jammed": bool(machine and machine.meters.get("jammed", 0.0) >= THRESHOLD),
        "blocked": bool(blocked and blocked.meters.get("blocked", 0.0) >= THRESHOLD),
        "too_loud": bool(machine and machine.meters.get("too_loud", 0.0) >= THRESHOLD),
    }


def annual_luck() -> str:
    return "Once a year, the big science day came around again."


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return f"The {setting.place} was bright and cozy, with a small stage waiting in the middle."
    return f"The {setting.place} was open to the sky, with a small stage waiting in the middle."


def introduce(world: World, child: Entity, physicist: Entity) -> None:
    world.say(
        f"{child.id} loved the annual science day because {physicist.id} always "
        f"brought clever toys, bright buttons, and funny sound effects."
    )
    world.say(
        f"{physicist.id} was a patient physicist who liked to test ideas, "
        f"listen closely, and keep the show feeling like an adventure."
    )


def set_up(world: World, child: Entity, physicist: Entity) -> None:
    world.say(annual_luck())
    world.say(setting_line(world.setting))
    world.say(
        f"{child.id} and {physicist.id} rolled in their props and set the "
        f"sound effects machine beside the stage."
    )
    child.memes["excited"] = child.memes.get("excited", 0.0) + 1
    physicist.memes["hope"] = physicist.memes.get("hope", 0.0) + 1
    world.entities["sound_machine"].carried_by = physicist.id
    world.entities["sound_machine"].staged = True
    world.entities["stage_path"].staged = True


def reveal_twist(world: World, child: Entity, physicist: Entity, twist: Twist) -> None:
    world.problem = twist.target
    world.twist = twist
    if twist.target == "machine":
        world.entities["sound_machine"].meters["jammed"] = 1.0
    elif twist.target == "path":
        world.entities["stage_path"].meters["blocked"] = 1.0
    elif twist.target == "volume":
        world.entities["sound_machine"].meters["too_loud"] = 1.0

    world.say(
        f"Then came the twist: {twist.clue} {twist.verb}. "
        f"{child.id} blinked, and {physicist.id} paused to think."
    )
    if twist.target == "machine":
        world.say("The sound effects machine made a stubborn little click and would not start.")
    elif twist.target == "path":
        world.say("A pile of boxes blocked the path to the stage.")
    elif twist.target == "volume":
        world.say("The first test blast was much too loud for the tiny audience.")


def choose_fix(world: World, physicist: Entity, child: Entity, gear: Gear) -> None:
    if world.problem not in gear.protects:
        return
    if gear.id == "tape" and world.problem == "machine":
        world.entities["sound_machine"].meters["jammed"] = 0.0
        world.entities["sound_machine"].meters["repaired"] = 1.0
    elif gear.id == "cart" and world.problem == "path":
        world.entities["stage_path"].meters["blocked"] = 0.0
        world.entities["stage_path"].meters["cleared"] = 1.0
    elif gear.id == "earpads" and world.problem == "volume":
        world.entities["sound_machine"].meters["too_loud"] = 0.0
        world.entities["sound_machine"].meters["safe"] = 1.0
    physicist.memes["care"] = physicist.memes.get("care", 0.0) + 1
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(
        f"{physicist.id} smiled and reached for {gear.label_phrase}. "
        f'"{gear.prep}," {physicist.pronoun()} said, and {child.id} helped right away.'
    )
    world.say(
        f"They {gear.tail}, and soon the adventure could continue."
    )
    propagate(world, narrate=True)


def finish(world: World, child: Entity, physicist: Entity) -> None:
    machine = world.entities["sound_machine"]
    if machine.meters.get("repaired", 0.0) >= THRESHOLD or machine.meters.get("safe", 0.0) >= THRESHOLD:
        world.say(
            f"The next sound was perfect: a brave boom, a tiny whirr, and a happy pop."
        )
    else:
        world.say(
            f"The next sound was perfect: a brave boom, a tiny whirr, and a happy pop."
        )
    world.say(
        f"{child.id} laughed, {physicist.id} bowed, and the annual science day "
        f"ended with the whole stage shining like a little adventure map."
    )


def tell(setting: Setting, twist: Twist, hero_name: str = "Mina") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label=hero_name))
    physicist = world.add(Entity(id="physicist", kind="character", type="physicist", label="the physicist"))
    machine = world.add(Entity(
        id="sound_machine", kind="thing", type="machine",
        label="sound effects machine", phrase="a little sound effects machine",
        caretaker=physicist.id,
    ))
    path = world.add(Entity(
        id="stage_path", kind="thing", type="path", label="stage path",
        phrase="the path to the stage", caretaker=physicist.id
    ))

    introduce(world, child, physicist)
    world.para()
    set_up(world, child, physicist)
    world.para()
    reveal_twist(world, child, physicist, twist)
    world.para()
    gear = select_gear(twist, machine, path)
    if gear is None:
        raise StoryError("No reasonable fix exists for this twist.")
    choose_fix(world, physicist, child, gear)
    world.para()
    finish(world, child, physicist)

    world.facts.update(
        child=child,
        physicist=physicist,
        machine=machine,
        path=path,
        twist=twist,
        gear=gear,
        place=setting.place,
    )
    return world


def select_gear(twist: Twist, machine: Entity, path: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if twist.target in gear.protects:
            return gear
    return None


SETTINGS = {
    "lab": Setting(place="the bright lab", indoors=True, affords={"machine", "volume"}),
    "hall": Setting(place="the old hall", indoors=True, affords={"machine", "volume"}),
    "courtyard": Setting(place="the courtyard", indoors=False, affords={"path", "volume"}),
}

TWISTS = {
    "machine": Twist(
        id="machine",
        label="jammed machine",
        verb="the machine jammed",
        effect="jammed",
        target="machine",
        clue="just as the music began",
        fix_hint="sticky tape and a careful twist",
        resolves_with="tape",
        tags={"sound", "machine", "twist"},
    ),
    "path": Twist(
        id="path",
        label="blocked path",
        verb="the path got blocked",
        effect="blocked",
        target="path",
        clue="right before the show began",
        fix_hint="a small cart and a careful push",
        resolves_with="cart",
        tags={"path", "twist"},
    ),
    "volume": Twist(
        id="volume",
        label="too loud sound",
        verb="the sound was too loud",
        effect="too_loud",
        target="volume",
        clue="during the first test",
        fix_hint="soft ear pads and a smaller switch",
        resolves_with="earpads",
        tags={"sound", "volume", "twist"},
    ),
}

GEAR = [
    Gear(
        id="tape",
        label="sticky tape",
        label_phrase="a roll of sticky tape",
        protects={"machine"},
        helps={"jammed"},
        prep="Let's give the gears a careful twist and hold them steady",
        tail="they lined up the tiny gears and pressed the tape in place",
    ),
    Gear(
        id="cart",
        label="small cart",
        label_phrase="a small rolling cart",
        protects={"path"},
        helps={"blocked"},
        prep="Let's roll the boxes aside first",
        tail="they rolled the boxes away and opened the path",
    ),
    Gear(
        id="earpads",
        label="soft ear pads",
        label_phrase="a pair of soft ear pads",
        protects={"volume"},
        helps={"too_loud"},
        prep="Let's make the sound a little softer",
        tail="they lowered the switch and fitted the soft pads",
    ),
]

NAMES = ["Mina", "Luka", "Nia", "Toby", "June", "Eli", "Pia", "Owen"]
TRAITS = ["curious", "brave", "cheerful", "clever", "lively", "careful"]


@dataclass
class StoryParams:
    place: str
    twist: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for twist_id in setting.affords:
            combos.append((place, twist_id))
    return combos


KNOWLEDGE = {
    "physicist": [
        (
            "What does a physicist do?",
            "A physicist studies how the world moves and changes, like light, sound, force, and motion.",
        )
    ],
    "annual": [
        (
            "What does annual mean?",
            "Annual means something happens once every year, like a birthday or a yearly fair.",
        )
    ],
    "sound": [
        (
            "What are sound effects?",
            "Sound effects are special sounds that help a story, play, or show feel exciting and real.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise change that makes the story take a new turn.",
        )
    ],
    "machine": [
        (
            "What is a machine?",
            "A machine is something made from parts that work together to do a job.",
        )
    ],
    "path": [
        (
            "Why do people clear a path?",
            "People clear a path so they can walk or roll things safely without bumping into obstacles.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child featuring an annual {f["physicist"].type}, a twist, and sound effects.',
        f"Tell a gentle adventure where {f['child'].label} and the physicist prepare for a yearly show, face a surprise, and fix it together.",
        f'Write a child-friendly story that includes the words "annual" and "physicist" and ends with a happy science show.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    phys = f["physicist"]
    twist = f["twist"]
    gear = f["gear"]
    setting = f["place"]
    qa = [
        QAItem(
            question=f"Who went on the annual science adventure at {setting}?",
            answer=f"{child.label} and the physicist went together, and they were ready for a yearly show full of surprises.",
        ),
        QAItem(
            question="What problem showed up in the story?",
            answer=f"The twist was that {twist.label}, which made the show tricky for a moment.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used {gear.label} to help, and that made the tricky part safe and ready again.",
        ),
        QAItem(
            question="What made the story feel like an adventure?",
            answer="The story had a busy stage, a surprise twist, a careful fix, and happy sound effects at the end.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["twist"].tags) | {"annual", "physicist", "sound"}
    out: list[QAItem] = []
    for tag in ["annual", "physicist", "sound", "twist", "machine", "path"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.staged:
            bits.append("staged=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  problem: {world.problem}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, twist: Twist) -> str:
    return f"(No story: {twist.label} is not compatible with {setting.place}.)"


ASP_RULES = r"""
place(P) :- setting(P).
twist(T) :- twist_kind(T).
gear(G) :- gear_kind(G).

compatible(P, T) :- setting(P), twist_kind(T), affords(P, T).

valid(P, T) :- compatible(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, twist in TWISTS.items():
        lines.append(asp.fact("twist_kind", tid))
        lines.append(asp.fact("twist_target", tid, twist.target))
    for gid, gear in [(g.id, g) for g in GEAR]:
        lines.append(asp.fact("gear_kind", gid))
        for p in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Annual physicist twist sound-effects adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.twist is None or c[1] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, twist = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, twist=twist, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TWISTS[params.twist], params.name)
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
    StoryParams(place="lab", twist="machine", name="Mina", trait="curious"),
    StoryParams(place="hall", twist="volume", name="Luka", trait="brave"),
    StoryParams(place="courtyard", twist="path", name="Nia", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, t in combos:
            print(f"  {p:10} {t}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.twist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
