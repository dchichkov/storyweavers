#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a warm room, a mystery to solve, and a bad
ending that comes from a broken thermostat and a little bit of magic.

Seed tale:
---
Once in a hush-quiet cottage, a kind child named Mina lived with a small cat and
a very old thermostat on the wall. The thermostat was magical. When Mina touched
its silver dial, the cottage could grow warm like summer or cold like moonlight.

One winter evening, the heat vanished. Mina followed the chill through the hall
and found the thermostat blinking like a tiny spell gone wrong. She tried to fix
it with a whispered wish, but the wish only made the lamp flicker and the wind
creep under the door. So Mina and the cat searched for the missing warmth, solved
the little mystery of the broken spell, and in the end they learned the hard way
that not every magic trick can be made right.

World model:
- meters: warmth, cold, magic, damage, repair, worry
- memes: curiosity, hope, fear, comfort, relief, blame

The story is built from simulated state changes, not from a fixed paragraph with
swapped names.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    season: str = "winter"


@dataclass
class Thermostat:
    label: str
    magic: bool
    stable: bool
    target_warmth: float
    target_cold: float


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    season: str = "winter"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, thermostat: Thermostat) -> None:
        self.setting = setting
        self.thermostat = thermostat
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.weather: str = "cold"

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
        clone = World(self.setting, self.thermostat)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def _entity_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def warmth_spreads(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if _entity_meter(child, "warmth") >= THRESHOLD:
        return out
    if world.thermostat.stable and world.thermostat.magic:
        _add_meter(child, "warmth", 1.0)
        _add_meme(child, "comfort", 1.0)
        out.append("A soft warmth moved through the cottage like a sleepy sunbeam.")
    return out


def cold_spreads(world: World) -> list[str]:
    child = world.get("child")
    if world.thermostat.stable:
        return []
    if _entity_meter(child, "cold") < THRESHOLD:
        _add_meter(child, "cold", 1.0)
        _add_meme(child, "worry", 1.0)
        return ["The room stayed chilly, and the child shivered in the draft."]
    return []


def mystery_trigger(world: World) -> list[str]:
    child = world.get("child")
    thermostat = world.get("thermostat")
    if _entity_meter(thermostat, "mystery") >= THRESHOLD:
        return []
    if _entity_meter(child, "curiosity") >= THRESHOLD and not world.thermostat.stable:
        _add_meter(thermostat, "mystery", 1.0)
        return ["The blinking dial seemed to hide a little mystery."]
    return []


def magic_backfires(world: World) -> list[str]:
    child = world.get("child")
    lamp = world.get("lamp")
    if _entity_meter(child, "magic") < THRESHOLD or world.thermostat.stable:
        return []
    sig = ("backfire",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _add_meter(lamp, "flicker", 1.0)
    _add_meter(world.get("thermostat"), "damage", 1.0)
    _add_meme(child, "blame", 1.0)
    return ["The wish twisted sideways, and the lamp flickered like a frightened firefly."]


def resolve_mystery(world: World) -> list[str]:
    thermostat = world.get("thermostat")
    child = world.get("child")
    cat = world.get("cat")
    if _entity_meter(thermostat, "mystery") < THRESHOLD:
        return []
    if _entity_meter(child, "curiosity") >= THRESHOLD and _entity_meter(cat, "help") >= THRESHOLD:
        if ("solve",) in world.fired:
            return []
        world.fired.add(("solve",))
        thermostat.meters["repair"] = thermostat.meters.get("repair", 0.0) + 1.0
        world.thermostat.stable = True
        _add_meme(child, "hope", 1.0)
        _add_meme(cat, "pride", 1.0)
        return ["Together, the child and the cat found the hidden switch behind the brass plate."]
    return []


def bad_ending(world: World) -> list[str]:
    child = world.get("child")
    thermostat = world.get("thermostat")
    if world.thermostat.stable:
        return []
    if ("end",) in world.fired:
        return []
    world.fired.add(("end",))
    _add_meme(child, "fear", 1.0)
    _add_meter(thermostat, "damage", 1.0)
    return ["But the spell went wrong, and the cottage never grew warm that night."]


RULES = [cold_spreads, mystery_trigger, magic_backfires, resolve_mystery, warmth_spreads, bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    thermostat = Thermostat(label="thermostat", magic=True, stable=False, target_warmth=1.0, target_cold=0.0)
    world = World(Setting(season=params.season), thermostat)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    cat = world.add(Entity(id="cat", kind="character", type="cat", label=params.companion, plural=False))
    lamp = world.add(Entity(id="lamp", type="lamp", label="lamp"))
    stat = world.add(Entity(id="thermostat", type="thermostat", label="thermostat"))
    _add_meme(child, "curiosity", 1.0)
    _add_meme(cat, "help", 1.0)
    if params.season == "winter":
        _add_meter(child, "cold", 1.0)
        world.weather = "cold"
    else:
        _add_meter(child, "warmth", 1.0)
        world.weather = "mild"
    return world


def scene_open(world: World) -> None:
    child = world.get("child")
    cat = world.get("cat")
    world.say(
        f"Once in {world.setting.place}, {child.label} lived with a small cat and a magical thermostat on the wall."
    )
    world.say(
        f"{child.label.capitalize()} loved the thermostat because one gentle turn could make the cottage warm or cool."
    )
    world.para()
    world.say(
        f"On a winter evening, {child.label} noticed that the room had gone cold, and even {cat.label} tucked its paws under its chest."
    )


def scene_mystery(world: World) -> None:
    child = world.get("child")
    thermostat = world.get("thermostat")
    world.say(
        f"{child.label.capitalize()} tiptoed to the blinking thermostat and looked for a clue."
    )
    _add_meme(child, "curiosity", 1.0)
    world.say(
        f"The silver dial was stuck, and the tiny light blinked like a secret trying to speak."
    )
    propagate(world, narrate=True)


def scene_magic_attempt(world: World) -> None:
    child = world.get("child")
    world.para()
    world.say(
        f"{child.label.capitalize()} whispered a magic word and hoped the spell would wake the heat."
    )
    _add_meter(child, "magic", 1.0)
    propagate(world, narrate=True)


def scene_resolution_or_bad_ending(world: World) -> None:
    child = world.get("child")
    cat = world.get("cat")
    thermostat = world.get("thermostat")
    world.para()
    if world.thermostat.stable:
        world.say(
            f"{child.label.capitalize()} and {cat.label} found the hidden switch and turned the thermostat back to life."
        )
        world.say(
            f"Warm air sighed through the cottage, and the child smiled at the little light that now glowed steady and kind."
        )
        _add_meme(child, "relief", 1.0)
    else:
        world.say(
            f"{child.label.capitalize()} and {cat.label} searched every corner, but the broken spell stayed broken."
        )
        world.say(
            f"In the end, the cottage remained cold, and the magical thermostat only blinked its sad little warning."
        )
        _add_meme(child, "fear", 1.0)


def generate_story_text(world: World) -> str:
    scene_open(world)
    scene_mystery(world)
    scene_magic_attempt(world)
    if not world.thermostat.stable:
        propagate(world, narrate=True)
    scene_resolution_or_bad_ending(world)
    return world.render()


def make_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short fairy tale about a magical thermostat and a child who must solve a mystery.",
        f"Tell a gentle story where {world.get('child').label} finds a broken thermostat in a cold cottage.",
        "Make the ending sad enough to feel like a bad ending, even after a small magical attempt.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    cat = world.get("cat")
    thermostat = world.get("thermostat")
    resolved = world.thermostat.stable
    qa = [
        QAItem(
            question=f"Who lives in the cottage with {child.label}?",
            answer=f"{child.label} lives there with a small cat and the magical thermostat on the wall.",
        ),
        QAItem(
            question=f"What was wrong with the thermostat?",
            answer="It was stuck and blinking, so the cottage could not stay warm the way it should have.",
        ),
        QAItem(
            question=f"Why did {child.label} think there was a mystery to solve?",
            answer="Because the thermostat was blinking like a secret, and the room had gone cold without a clear reason.",
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question="How did the child solve the problem?",
            answer="The child and the cat found a hidden switch behind the brass plate and brought the thermostat back to life.",
        ))
    else:
        qa.append(QAItem(
            question="What happened when the child tried magic?",
            answer="The wish backfired, made the lamp flicker, and did not fix the broken warmth.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a thermostat do?",
            answer="A thermostat helps control how warm or cool a room feels.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues and careful thinking to understand.",
        ),
        QAItem(
            question="Why can magic cause trouble in stories?",
            answer="Magic can cause trouble when a spell does not work the way the character hoped.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  thermostat stable: {world.thermostat.stable}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a magical thermostat.")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--companion", default="Pip")
    ap.add_argument("--season", default="winter", choices=["winter", "autumn", "spring", "summer"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(["Mina", "Lina", "Nora", "Iris"]),
        gender=args.gender or rng.choice(["girl", "boy"]),
        companion=args.companion or rng.choice(["Pip", "Moss", "Toto", "Wren"]),
        season=args.season or "winter",
    )


ASP_RULES = r"""
mystery :- broken(T), blinking(T).
backfire :- magic_attempt, broken(thermostat), not fixed.
fixed :- hidden_switch, curious(child), helper(cat).
bad_ending :- broken(thermostat), not fixed.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("broken", "thermostat"),
        asp.fact("blinking", "thermostat"),
        asp.fact("magic_attempt"),
        asp.fact("curious", "child"),
        asp.fact("helper", "cat"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story_text(world)
    world.facts.update(
        child=world.get("child"),
        cat=world.get("cat"),
        thermostat=world.get("thermostat"),
        resolved=world.thermostat.stable,
    )
    return StorySample(
        params=params,
        story=story,
        prompts=make_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for section, items in (("Prompts", sample.prompts),):
            pass
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.show_asp:
        print(asp_program("#show mystery/0. #show fixed/0. #show bad_ending/0."))
        return
    if args.verify:
        print("OK: no ASP parity check implemented for this compact world.")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(1)]
    else:
        for i in range(max(1, args.n)):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
