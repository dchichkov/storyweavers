#!/usr/bin/env python3
"""
bedtime story world with Surprise, Repetition, and Twist.

This world models a small bedtime scene where a child, a parent, a comforting
object, and a little surprise move the story from worry to calm sleep.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    type: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Surprise:
    id: str
    label: str
    event: str
    effect: str
    risk: str
    reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.scene: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.scene = self.scene
        return clone


def _repeat_phrase(turn: str, times: int = 2) -> str:
    return " ".join([turn] * times)


def _r_sleepiness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind == "character" and e.memes.get("sleepy", 0.0) >= THRESHOLD and e.memes.get("calm", 0.0) >= THRESHOLD:
            sig = ("sleep", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["asleep"] = 1.0
            out.append(f"{e.id} drifted into sleep.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    if not child:
        return out
    c = world.get(child.id)
    if c.memes.get("worry", 0.0) >= THRESHOLD and c.memes.get("comfort", 0.0) >= THRESHOLD:
        sig = ("calm", c.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        c.memes["worry"] = 0.0
        c.memes["calm"] = 1.0
        out.append(f"{c.id} felt safe again.")
    return out


CAUSAL_RULES = [_r_comfort, _r_sleepiness]


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


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    place: str
    comfort: str
    surprise: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"lullaby", "counting", "peek"}),
    "nursery": Setting(place="the nursery", affords={"lullaby", "counting", "peek"}),
}

COMFORTS = {
    "blanket": ComfortItem(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        type="blanket",
        helps={"worry", "cold"},
    ),
    "lamp": ComfortItem(
        id="lamp",
        label="nightlight",
        phrase="a little nightlight",
        type="lamp",
        helps={"dark"},
    ),
    "toy": ComfortItem(
        id="toy",
        label="stuffed bunny",
        phrase="a stuffed bunny with floppy ears",
        type="toy",
        helps={"worry"},
        plural=False,
    ),
}

SURPRISES = {
    "tap": Surprise(
        id="tap",
        label="tapping",
        event="a tiny tap at the window",
        effect="the room went quiet",
        risk="worry",
        reveal="it was only a branch tapping the glass",
        keyword="tap",
        tags={"sound", "night"},
    ),
    "rustle": Surprise(
        id="rustle",
        label="rustling",
        event="a soft rustle by the door",
        effect="the child held still",
        risk="worry",
        reveal="it was only the curtains moving in the air",
        keyword="rustle",
        tags={"sound", "night"},
    ),
    "twinkle": Surprise(
        id="twinkle",
        label="twinkling",
        event="a small twinkle on the shelf",
        effect="the child blinked twice",
        risk="worry",
        reveal="it was a fallen sticker catching the lamp light",
        keyword="twinkle",
        tags={"light", "night"},
    ),
}

CHILDREN = ["Mia", "Noah", "Lily", "Theo", "Ava", "Eli"]
TRAITS = ["sleepy", "curious", "gentle", "brave", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for comfort in COMFORTS:
            for surprise in SURPRISES:
                combos.append((place, comfort, surprise))
    return combos


def reason_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown bedtime setting.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown comfort item.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise event.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id=params.child_name, kind="character", type=params.child_type,
        traits=["little", "tired"],
        memes={"sleepy": 0.0, "worry": 0.0, "comfort": 0.0, "calm": 0.0, "joy": 0.0},
        meters={"awake": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent_type, label="parent",
        memes={"patience": 1.0, "love": 1.0},
    ))
    comfort_def = COMFORTS[params.comfort]
    comfort = world.add(Entity(
        id=comfort_def.id, type=comfort_def.type, label=comfort_def.label,
        phrase=comfort_def.phrase, owner=child.id, caretaker=parent.id,
    ))
    surprise_def = SURPRISES[params.surprise]

    world.facts.update(child=child, parent=parent, comfort=comfort, surprise=surprise_def)

    world.say(f"{child.id} was a little {next(t for t in child.traits if t != 'little')} {child.type} who lived in {world.setting.place}.")
    world.say(f"{child.id} loved {comfort.phrase} and kept it close at bedtime.")

    world.para()
    world.say(f"One night, {child.id} climbed into bed and the parent began a sleepy routine: \"Hush now,\" the parent whispered, and then again, \"Hush now.\"")
    world.say(f"{child.id} listened to the repetition, but then came {surprise_def.event}.")
    child.memes["worry"] += 1.0
    child.memes["sleepy"] += 1.0
    world.say(f"{surprise_def.effect}; {child.id}'s heart went bump-bump with worry.")

    world.para()
    world.say(f'The parent smiled and said, "First we look, then we listen, then we look again."')
    world.say(f'{child.id} peeked once, peeked twice, and peeked a third time.')
    world.say(f'And then the twist came out: {surprise_def.reveal}.')
    child.memes["comfort"] += 1.0
    child.memes["joy"] += 1.0
    child.meters["awake"] = 0.0
    child.memes["sleepy"] += 1.0
    propagate(world, narrate=False)

    world.para()
    world.say(f"{child.id} hugged the {comfort.label}, and the room felt smaller and safer.")
    world.say(f'The parent repeated, "Safe room, safe heart, sleepy child," and {child.id} repeated it back in a tiny whisper.')
    world.say(f"Then {child.id} was warm, calm, and already halfway into a dream.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    surprise = f["surprise"]
    comfort = f["comfort"]
    return [
        f'Write a bedtime story for a small child named {child.id} that includes the word "boostered".',
        f"Tell a gentle bedtime story with a surprise, a little repetition, and a twist where {child.id} uses {comfort.phrase}.",
        f"Write a cozy bedtime tale about {child.id}, the {surprise.keyword} sound, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    comfort = f["comfort"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.id}, a little {child.type} who was getting ready for sleep in {world.setting.place}.",
        ),
        QAItem(
            question=f"What comfort item helped {child.id} feel safe?",
            answer=f"The {comfort.label} helped {child.id} feel safe, because {comfort.phrase} stayed close during bedtime.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was {surprise.event}, and at first it made {child.id} worry a little.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {surprise.reveal}, so the scary moment turned into something harmless.",
        ),
        QAItem(
            question=f"How did the parent calm the child down?",
            answer=f"The parent used a calm bedtime routine, repeated soothing words, and helped {child.id} look carefully before worrying.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bedtime routine?",
            answer="A bedtime routine is a set of calm, repeated steps like washing, reading, or whispering good night before sleep.",
        ),
        QAItem(
            question="Why can repetition help at bedtime?",
            answer="Repetition can help because familiar words and actions feel steady, and steady things make it easier to relax.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_calm(C) :- worry(C), comfort(C), clue(C).
story_good(S) :- surprise(S), twist(S), child_calm(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for name in COMFORTS:
        lines.append(asp.fact("comfort", name))
    for name, s in SURPRISES.items():
        lines.append(asp.fact("surprise", name))
        lines.append(asp.fact("twist", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show surprise/1. #show twist/1.")
    model = asp.one_model(program)
    seen = set(asp.atoms(model, "surprise"))
    expected = {(k,) for k in SURPRISES}
    if seen == expected:
        print(f"OK: ASP sees {len(seen)} surprises.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("ASP:", sorted(seen))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world with surprise, repetition, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILDREN)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        child_name=name,
        child_type=gender,
        parent_type=parent,
        place=place,
        comfort=comfort,
        surprise=surprise,
    )


def generate(params: StoryParams) -> StorySample:
    reason_gate(params)
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show surprise/1. #show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show surprise/1. #show twist/1."))
        print("surprises:", sorted(asp.atoms(model, "surprise")))
        print("twists:", sorted(asp.atoms(model, "twist")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for comfort in COMFORTS:
                for surprise in SURPRISES:
                    params = StoryParams(
                        child_name="Mia",
                        child_type="girl",
                        parent_type="mother",
                        place=place,
                        comfort=comfort,
                        surprise=surprise,
                    )
                    samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
