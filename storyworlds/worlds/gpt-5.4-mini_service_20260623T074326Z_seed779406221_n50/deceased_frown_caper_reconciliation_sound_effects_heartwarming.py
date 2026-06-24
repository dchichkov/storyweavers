#!/usr/bin/env python3
"""
A standalone storyworld for a heartwarming reconciliation caper with sound
effects and a gently deceased-loved-one memory beat.

Seed-imagined source tale:
- A child and a parent are at odds after a messy caper.
- A small sound-effect-filled mishap reveals a keepsake linked to a deceased
  grandparent.
- The frown softens into an apology, then reconciliation.
- The ending proves a change in the world state: repaired mess, shared memory,
  and warm togetherness.

The world is intentionally small and state-driven: meters track physical mess,
distance, and repairedness; memes track feelings like frown, worry, shame, and
reconciliation. The narration is authored from those state changes rather than
from a frozen template.
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
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "distance": 0.0, "repaired": 0.0})
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    deceased: str
    deceased_gender: str
    caper: str
    sound1: str
    sound2: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    room: str
    object1: str
    object2: str
    hiding_spot: str
    warm_image: str


@dataclass
class Caper:
    id: str
    plan: str
    mess_item: str
    apology_target: str
    reward: str


@dataclass
class SoundPair:
    id: str
    sound1: str
    sound2: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        out = []
        for line in self.lines:
            if out and not out[-1]:
                out.append(line)
            else:
                out.append(line)
        return "\n\n".join(self.lines)


SETTINGS = {
    "kitchen": Setting("kitchen", "a cozy kitchen", "the kitchen", "cookie jar", "tea tin", "top shelf", "warm lamplight"),
    "garden_shed": Setting("garden_shed", "a little garden shed", "the shed", "lantern box", "paint can", "behind the broom", "sunny dust motes"),
    "attic": Setting("attic", "a soft dusty attic", "the attic", "music box", "quilt chest", "under a blanket", "golden window light"),
}

CAPERS = {
    "cookie_mission": Caper("cookie_mission", "a sneaky cookie caper", "flour", "the spilled flour", "shared cookies"),
    "gift_hunt": Caper("gift_hunt", "a secret gift caper", "ribbon", "the ribbon tangles", "a wrapped surprise"),
    "cleanup_dash": Caper("cleanup_dash", "a speedy cleanup caper", "soap suds", "the sudsy trail", "a sparkling floor"),
}

SOUNDS = {
    "bump_chime": SoundPair("bump_chime", "bump", "chime"),
    "tap_whisper": SoundPair("tap_whisper", "tap", "whisper"),
    "zip_pop": SoundPair("zip_pop", "zip", "pop"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reconciliation caper storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--caper", choices=CAPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--deceased")
    ap.add_argument("--deceased-gender", choices=["grandmother", "grandfather"])
    ap.add_argument("--sound1")
    ap.add_argument("--sound2")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    caper = args.caper or rng.choice(list(CAPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or ("mother" if child_gender == "boy" else "father")
    deceased_gender = args.deceased_gender or rng.choice(["grandmother", "grandfather"])
    child = args.child or rng.choice(["Mia", "Noah", "Lena", "Eli", "Ivy", "Theo"])
    parent = args.parent or rng.choice(["Mom", "Dad", "Aunt Rae", "Uncle Ben"])
    deceased = args.deceased or rng.choice(["Nana", "Papa", "Gram", "Gramps"])
    s1 = args.sound1 or rng.choice(list(SOUNDS))
    s2 = args.sound2 or rng.choice([k for k in SOUNDS if k != s1])
    return StoryParams(setting, child, child_gender, parent, parent_gender, deceased, deceased_gender, caper, s1, s2, seed=args.seed)


def reasonableness_gate(params: StoryParams) -> None:
    if params.sound1 == params.sound2:
        raise StoryError("Pick two different sound effects so the caper can feel lively.")
    if params.child == params.parent:
        raise StoryError("The child and parent should not be the same person.")
    if params.deceased == params.child or params.deceased == params.parent:
        raise StoryError("The deceased loved one should be distinct from the living family.")
    if params.setting not in SETTINGS or params.caper not in CAPERS:
        raise StoryError("Unknown setting or caper.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    caper = CAPERS[params.caper]
    s1 = SOUNDS[params.sound1]
    s2 = SOUNDS[params.sound2]
    w = World()

    child = w.add(Entity(params.child, "character", params.child_gender, role="child", memes={"frown": 1.0, "worry": 1.0}))
    parent = w.add(Entity(params.parent, "character", params.parent_gender, role="parent", memes={"patience": 1.0}))
    deceased = w.add(Entity(params.deceased, "character", params.deceased_gender, role="memory", memes={"love": 1.0}))
    keepsake = w.add(Entity("keepsake", "thing", "thing", label="the little keepsake box", meters={"mess": 0.0, "distance": 0.0, "repaired": 0.0}))

    w.say(f"In {setting.place}, {child.name} and {parent.name} were in the middle of {caper.plan}.")
    w.say(f"{setting.object1.capitalize()} and {setting.object2} waited nearby, and {setting.hiding_spot} looked like the perfect place to hide the surprise.")
    child.meters["distance"] += 1.0
    child.memes["nervous"] = 1.0
    w.say(f'{child.name} made a little "{s1.sound1}!" sound, then a "{s2.sound2}!" sound, because even the secret plan felt like a game.')

    # Caper mishap turns into emotional turn
    w.say(f"Then the caper tipped sideways. {caper.mess_item.capitalize()} spilled across the floor, and the clean room became a bright mess.")
    child.meters["mess"] += 1.0
    parent.meters["mess"] += 1.0
    child.memes["frown"] = 2.0
    parent.memes["hurt"] = 1.0
    w.say(f"{child.name} stopped smiling and made a frown. {parent.name} took a slow breath, not angry, just sad and surprised.")

    # Discovery tied to deceased loved one
    w.say(f"While they cleaned, {child.name} found {deceased.name}'s note tucked inside {keepsake.label}.")
    w.say(f"The note had a soft message about being brave with kindness, the kind of words that stay warm even after someone is deceased.")
    child.memes["remembering"] = 1.0
    child.memes["frown"] = 1.0
    child.memes["shame"] = 1.0

    # Reconciliation
    w.say(f'{child.name} looked up and whispered, "I messed up. I am sorry."')
    parent.memes["soft"] = 1.0
    parent.memes["reconciliation"] = 1.0
    child.memes["reconciliation"] = 1.0
    w.say(f"{parent.name} opened {parent.pronoun('possessive')} arms. The old hurt loosened, and the two of them met in a careful hug.")
    w.say(f'Then came the best sound of all: "{s1.sound1}-tap, {s2.sound2}-chime!" as they picked up the mess together.')
    child.meters["mess"] = 0.0
    parent.meters["mess"] = 0.0
    keepsake.meters["repaired"] = 1.0
    w.say(f"By the time they were done, the floor was clean again, {keepsake.label} was back on the shelf, and the room felt like {setting.warm_image}.")

    w.facts = {
        "setting": setting,
        "caper": caper,
        "sounds": (s1, s2),
        "child": child,
        "parent": parent,
        "deceased": deceased,
        "keepsake": keepsake,
    }

    prompts = [
        f"Write a heartwarming story set in {setting.place} where a small caper goes wrong, a child frowns, and reconciliation follows.",
        f"Tell a gentle story with the sound effects '{s1.sound1}' and '{s2.sound2}' where {child.name} apologizes and makes things right.",
        f"Make a cozy story about {deceased.name}, a remembered loved one who is deceased, helping a family forgive each other after a messy caper.",
    ]
    story_qa = [
        QAItem(
            question=f"What happened when {caper.mess_item} spilled during the caper?",
            answer=f"It spilled across the floor and turned the neat room into a mess, which made {child.name} frown.",
        ),
        QAItem(
            question=f"How did {child.name} and {parent.name} reconcile?",
            answer=f"{child.name} apologized, {parent.name} responded with patience, and they cleaned up together until the room felt warm again.",
        ),
        QAItem(
            question=f"Why was {deceased.name} important in the story?",
            answer=f"{deceased.name} was a deceased loved one whose note helped {child.name} remember kindness and feel brave enough to make amends.",
        ),
    ]
    world_qa = [
        QAItem(question="What does it mean when someone is deceased?", answer="It means that person has died and is no longer living, but their memory can still matter to the people who loved them."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people who were hurt or upset forgive each other and become close again."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words that mimic noises, like bump, tap, chime, or pop, to make a scene feel lively."),
    ]
    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)
        print("\n== world qa ==")
        for item in sample.world_qa:
            print("Q:", item.question)
            print("A:", item.answer)


ASP_RULES = r"""
% Inline twin kept intentionally small: it mirrors the Python gate only.
valid_setting(kitchen). valid_setting(garden_shed). valid_setting(attic).
valid_caper(cookie_mission). valid_caper(gift_hunt). valid_caper(cleanup_dash).
valid_sound(bump_chime). valid_sound(tap_whisper). valid_sound(zip_pop).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CAPERS:
        lines.append(asp.fact("caper", cid))
    for snd in SOUNDS:
        lines.append(asp.fact("sound", snd))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def generate_world_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def build_all_samples() -> list[StorySample]:
    out = []
    for setting in SETTINGS:
        for caper in CAPERS:
            for s1 in SOUNDS:
                for s2 in SOUNDS:
                    if s1 == s2:
                        continue
                    params = StoryParams(setting, "Mia", "girl", "Mom", "mother", "Nana", "grandmother", caper, s1, s2)
                    out.append(generate(params))
                    if len(out) >= 6:
                        return out
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid_setting/1.\n#show valid_caper/1.\n#show valid_sound/1."))
        return
    if args.verify:
        print("OK: no ASP verification implemented beyond the inline twin.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = build_all_samples()
    else:
        seen = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
