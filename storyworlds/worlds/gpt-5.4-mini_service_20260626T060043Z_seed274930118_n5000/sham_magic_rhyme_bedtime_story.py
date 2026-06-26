#!/usr/bin/env python3
"""
storyworlds/worlds/sham_magic_rhyme_bedtime_story.py
====================================================

A small bedtime-story world about a child, a pretend magic act, and a rhyme
that becomes real enough to matter.

Premise:
- A child loves a sparkly bedtime show.
- They try to make a "magic" moment with a sham trick and a rhyme.
- The trick doesn't work the way they hoped, and bedtime feelings wobble.

Turn:
- A parent notices the trouble, names the sham gently, and helps reshape the
  moment into a real rhyme that calms the room.

Resolution:
- The rhyme is simple, the magic is ordinary but warm, and bedtime ends with a
  peaceful image that proves what changed.

The world keeps both physical state ("meters") and emotional state ("memes")
for the child and the bedside objects.
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


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    shine: str
    sounds: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    prop: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _propagate(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    prop = world.entities.get("prop")
    parent = world.entities.get("parent")
    if not child or not prop or not parent:
        return out

    if child.meters.get("tired", 0.0) >= THRESHOLD and child.memes.get("worry", 0.0) >= THRESHOLD:
        if "shaky" not in world.fired:
            world.fired.add("shaky")
            child.memes["worry"] += 0.5
            out.append(f"{child.id}'s voice wobbled a little more.")

    if prop.meters.get("sham", 0.0) >= THRESHOLD and "sham_named" not in world.fired:
        world.fired.add("sham_named")
        child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
        out.append(f"The trick was only a sham, and the room went very quiet.")

    if child.memes.get("softness", 0.0) >= THRESHOLD and "settled" not in world.fired:
        world.fired.add("settled")
        child.memes["worry"] = 0.0
        child.meters["breath"] = child.meters.get("breath", 0.0) + 1
        out.append("The air felt slower and kinder.")

    return out


def _do_magic(world: World, child: Entity, prop: Prop, narrate: bool = True) -> None:
    prop_ent = world.get("prop")
    prop_ent.meters["shine"] = prop_ent.meters.get("shine", 0.0) + 1
    prop_ent.meters["sham"] = prop_ent.meters.get("sham", 0.0) + 1
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    child.meters["effort"] = child.meters.get("effort", 0.0) + 1
    if narrate:
        world.say(f"{child.id} lifted {prop.label} and whispered a tiny rhyme.")
        world.say(f"It looked magical, but the sparkle was mostly a sham.")
    _propagate(world)


def _sing_rhyme(world: World, child: Entity, parent: Entity, prop: Prop, narrate: bool = True) -> None:
    child.memes["softness"] = child.memes.get("softness", 0.0) + 1
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    parent.memes["warmth"] = parent.memes.get("warmth", 0.0) + 1
    if narrate:
        world.say(f"{parent.id} smiled and taught {child.id} a gentler rhyme.")
        world.say(f"The rhyme was simple, but it fit the sleepy room perfectly.")
    _propagate(world)


def tell_story(params: StoryParams) -> World:
    setting = Setting(place="the bedroom")
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "sleepy", "hopeful"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="parent"))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type=PROPS[params.prop].kind,
        label=PROPS[params.prop].label,
        phrase=PROPS[params.prop].phrase,
    ))

    world.facts.update(child=child, parent=parent, prop=prop, prop_cfg=PROPS[params.prop])

    child.meters["tired"] = 1
    child.memes["hope"] = 1
    child.memes["worry"] = 1

    world.say(f"At bedtime, {child.id} sat in {world.setting.place} with {prop.phrase}.")
    world.say(f"{child.id} loved the bright little show and wanted it to feel like real Magic.")

    world.para()
    world.say(f"{child.id} tried a Rhyme and a glowing wink.")
    _do_magic(world, child, PROPS[params.prop])

    world.para()
    world.say(f"Then the glow slipped away before it could truly change anything.")
    world.say(f"{child.id} frowned, because the lovely moment had turned out to be a sham.")

    world.para()
    world.say(f"{parent.id.capitalize()} came close and rested a hand on {child.pronoun('possessive')} shoulder.")
    world.say(f'"A rhyme can still be magic if it helps you feel safe," {parent.pronoun()} said.')
    _sing_rhyme(world, child, parent, PROPS[params.prop])

    world.para()
    world.say(f"{child.id} sang it again, slower this time.")
    world.say(f"The room felt softer, the blanket felt warmer, and the bedtime dark looked friendly.")
    world.say(f"In the end, {child.id} smiled, {prop.label} was tucked away, and the only sparkle left was the one in {child.pronoun('possessive')} eyes.")
    return world


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    shine: str
    sounds: list[str] = field(default_factory=list)


PROPS = {
    "wand": Prop(
        id="wand",
        label="wand",
        phrase="a glittery wand",
        kind="wand",
        shine="silver",
        sounds=["twinkle", "tap"],
    ),
    "lantern": Prop(
        id="lantern",
        label="lantern",
        phrase="a small lantern with star stickers",
        kind="lantern",
        shine="gold",
        sounds=["hum", "glow"],
    ),
    "blanket": Prop(
        id="blanket",
        label="blanket",
        phrase="a soft bedtime blanket",
        kind="blanket",
        shine="blue",
        sounds=["swish", "fluff"],
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Zoe", "Ivy"],
    "boy": ["Ben", "Theo", "Milo", "Finn", "Eli"],
}
PARENTS = ["mother", "father"]
PROPS_ORDER = ["wand", "lantern", "blanket"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a sham magic rhyme.")
    ap.add_argument("--name", choices=sorted(set(NAMES["girl"] + NAMES["boy"])))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--prop", choices=PROPS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("bedroom", prop) for prop in PROPS_ORDER]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    prop = args.prop or rng.choice(PROPS_ORDER)
    return StoryParams(name=name, gender=gender, parent=parent, prop=prop)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle bedtime story with the words "Magic", "Rhyme", and "sham".',
        f"Tell a bedtime story where {f['child'].id} tries pretend magic with {f['prop_cfg'].label} and learns a calmer rhyme.",
        "Write a cozy story about a child who discovers that a kind rhyme can feel magical at bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    prop_cfg = f["prop_cfg"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"What did {child.id} try to do at bedtime?",
            answer=f"{child.id} tried to make a magical moment with {prop_cfg.phrase}.",
        ),
        QAItem(
            question=f"Why did the first trick feel like a sham?",
            answer="It looked sparkly, but it did not really solve the sleepy worry in the room.",
        ),
        QAItem(
            question=f"What did {parent.id} do to help?",
            answer=f"{parent.id.capitalize()} taught {child.id} a gentler rhyme that made the room feel safe and calm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} felt calm, tucked {prop_cfg.label} away, and went to bed with a soft smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is for getting ready to sleep, resting your body, and making the room calm and cozy.",
        ),
        QAItem(
            question="What does a rhyme do?",
            answer="A rhyme is a little bit of repeated sound in words, and people often use rhymes in songs and poems.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="In a story, magic means something wondrous or surprising, even if it is only pretend.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
child(anna). child(ben).
prop(wand). prop(lantern). prop(blanket).

magical(P) :- prop(P).
sham(P) :- prop(P).
rhyme(P) :- prop(P).

shown_story(C,P) :- child(C), prop(P), sham(P), magical(P), rhyme(P).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bedroom")]
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    for g in ("girl", "boy"):
        for n in NAMES[g]:
            lines.append(asp.fact("name", g, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shown_story/2."))
    atoms = set(asp.atoms(model, "shown_story"))
    py = {(n, p) for n in ("anna", "ben") for p in PROPS}
    if atoms == py:
        print(f"OK: ASP gate matches Python registry ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python registry")
    print("ASP only:", sorted(atoms - py))
    print("PY only:", sorted(py - atoms))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show shown_story/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shown_story/2."))
        print(f"{len(asp.atoms(model, 'shown_story'))} ASP story pairs")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams(name="Mina", gender="girl", parent="mother", prop="wand"),
            StoryParams(name="Ben", gender="boy", parent="father", prop="lantern"),
            StoryParams(name="Ivy", gender="girl", parent="mother", prop="blanket"),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
