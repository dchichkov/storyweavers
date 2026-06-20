#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fettuccini_sticky_dialogue_ghost_story.py
===========================================================================

A small standalone storyworld for a ghost-story-style kitchen mystery.

Seed premise:
- The words "fettuccini" and "sticky" must appear.
- The story should be dialogue-heavy.
- The style should feel like a gentle ghost story: a strange presence,
  a little tension, a reveal, and a comforting ending.

World idea:
A child and a grown-up hear a "sticky" whisper in the kitchen at night.
They follow the sound to a bowl of fettuccini that has been left on the stove.
The "ghost" turns out to be a chilly draft and a clinking spoon, and the child
learns to call for help instead of creeping alone in the dark.

This script is self-contained and uses only stdlib.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Setting:
    id: str
    place: str
    dark: str
    safe_light: str
    sound: str


@dataclass
class Hook:
    id: str
    whisper: str
    clue: str
    false_guess: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    sticky: bool = False
    edible: bool = False
    cold: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the dark corner by the sink", "the lamp over the table", "a soft clink"),
    "hall": Setting("hall", "the hallway", "the stairs at the end of the hall", "the light from the doorway", "a hush"),
    "cellar": Setting("cellar", "the cellar stairs", "the bottom step", "the lantern on the hook", "a cold drip"),
}

HOOKS = {
    "ghost": Hook("ghost", "Who is whispering?", "a whisper near the dark corner", "a hungry ghost in the walls", "it was only the wind moving through the window crack", {"ghost", "whisper", "wind"}),
    "plate": Hook("plate", "Why does something keep clinking?", "a clink near the stove", "a ghost tapping plates together", "it was a spoon inside the pasta bowl", {"clink", "spoon", "pasta"}),
    "sticky": Hook("sticky", "Why is the floor sticky?", "a sticky patch near the table", "a ghost spilling syrup", "it was spilled sauce from the fettuccini", {"sticky", "sauce"}),
}

OBJECTS = {
    "fettuccini": ObjectCfg("fettuccini", "fettuccini", sticky=True, edible=True, tags={"pasta", "sticky"}),
    "sauce": ObjectCfg("sauce", "tomato sauce", sticky=True, edible=True, tags={"sticky", "sauce"}),
    "candle": ObjectCfg("candle", "a candle", tags={"light"}),
}

GIRL_NAMES = ["Maya", "Luna", "Nina", "Ivy", "Rose"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Owen"]


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, hid) for sid in SETTINGS for hid in HOOKS]


@dataclass
class StoryParams:
    setting: str
    hook: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS or params.hook not in HOOKS:
        raise StoryError("(No story: unknown setting or hook.)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story kitchen tale with dialogue and fettuccini.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hook", choices=HOOKS)
    ap.add_argument("--child")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hook = args.hook or rng.choice(sorted(HOOKS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    params = StoryParams(setting=setting, hook=hook, child=child, child_gender=gender, parent=parent)
    reasonableness_gate(params)
    return params


def _do_shadow(world: World, child: Entity, parent: Entity, setting: Setting, hook: Hook) -> None:
    child.memes["unease"] += 1
    world.say(f'At night, {child.id} whispered, "Did you hear that?"')
    world.say(f'{parent.label_word.capitalize()} said, "Hear what?"')
    world.say(f'From {setting.dark}, there came {setting.sound}. {child.id} clutched the edge of the doorway.')
    if hook.id == "ghost":
        world.say(f'"It sounds like a ghost," {child.id} breathed.')
        world.say(f'"Maybe," {parent.id} said, "but let\'s look with the light on."')
    elif hook.id == "plate":
        world.say(f'"It sounds like something tapping," {child.id} said.')
        world.say(f'"A kitchen can make funny noises," {parent.id} answered. "Stay close."')
    else:
        world.say(f'"Something feels sticky," {child.id} said.')
        world.say(f'"That smell could be sauce," {parent.id} said. "Let\'s be brave together."')


def _reveal(world: World, child: Entity, parent: Entity, setting: Setting, hook: Hook) -> None:
    world.say(f'They followed the clue to the table, where a bowl of fettuccini waited in the dim light.')
    world.say(f'The air was sticky with sauce, and that was the whole mystery.')
    world.say(f'"It was not a ghost," {child.id} said.')
    world.say(f'"No," {parent.id} smiled. "{hook.reveal}."')
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.get("pasta").meters["sticky"] += 1
    if "sauce" in world.entities:
        world.get("sauce").meters["sticky"] += 1
    world.get("room").meters["calm"] += 1
    world.say(f'They wiped the table, turned on the lamp, and the kitchen looked like itself again.')


def tell(setting: Setting, hook: Hook, child_name: str = "Maya", child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="parent"))
    room = world.add(Entity("room", type="room", label=setting.place))
    pasta = world.add(Entity("pasta", type="food", label="fettuccini"))
    sauce = world.add(Entity("sauce", type="thing", label="sauce"))

    child.memes["curiosity"] += 1
    child.memes["courage"] += 1

    world.say(f'One night in {setting.place}, {child.id} heard a strange little sound near the dark corner.')
    world.say(f'"{hook.whisper}," {child.id} asked. "{setting.sound}... is somebody there?"')
    world.say(f'"Stay with me," {parent.id} said. "We can listen first and be smart."')

    world.para()
    _do_shadow(world, child, parent, setting, hook)

    world.para()
    _reveal(world, child, parent, setting, hook)

    world.para()
    world.say(f'"What was it really?" {child.id} asked.')
    world.say(f'"Just supper," {parent.id} said. "A bowl of {pasta.label}, a little sticky sauce, and a spoon that went clink in the dark."')
    world.say(f'{child.id} laughed, and the kitchen felt warm instead of spooky.')

    world.facts.update(setting=setting, hook=hook, child=child, parent=parent, room=room, pasta=pasta, sauce=sauce)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hook = f["hook"]
    setting = f["setting"]
    child = f["child"]
    return [
        f'Write a gentle ghost story set in {setting.place} that includes the words "fettuccini" and "sticky".',
        f'Tell a dialogue-heavy story where {child.id} hears a spooky sound, thinks of a ghost, and discovers the answer in a kitchen.',
        f'Write a child-friendly ghost story with a small mystery, a parent, and a reveal that makes the room feel safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    hook = f["hook"]
    return [
        QAItem(
            question=f"What did {child.id} think they heard?",
            answer=f'{child.id} thought something spooky was whispering or clinking in the dark. {parent.id} stayed close and helped {child.pronoun()} listen safely instead of guessing alone.'
        ),
        QAItem(
            question="What was the mystery really about?",
            answer="It was only supper in the kitchen. The sound came from a spoon, and the sticky smell came from fettuccini with sauce."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f'The strange sound turned out to be harmless, so {child.id} relaxed and laughed. The kitchen felt warm and safe again after they found the fettuccini.'
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fettuccini?",
            answer="Fettuccini is a kind of pasta made of flat noodles. People often eat it with sauce."
        ),
        QAItem(
            question="What does sticky mean?",
            answer="Sticky means something clings a little and feels hard to wipe off. Sauce, syrup, and jam can be sticky."
        ),
        QAItem(
            question="Why can a dark kitchen feel spooky?",
            answer="A dark kitchen can make ordinary sounds seem strange. When you cannot see well, a little clink or whisper can feel ghostly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S, H) :- setting(S), hook(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HOOKS:
        lines.append(asp.fact("hook", h))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HOOKS[params.hook], params.child, params.child_gender, params.parent)
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
    StoryParams("kitchen", "ghost", "Maya", "girl", "mother"),
    StoryParams("hall", "plate", "Noah", "boy", "father"),
    StoryParams("kitchen", "sticky", "Ivy", "girl", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
