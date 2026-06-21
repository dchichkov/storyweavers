#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gum_dim_dialogue_curiosity_rhyming_story.py
===========================================================================

A small standalone storyworld for a rhyming, dialogue-rich curiosity tale about
a child, a dim glow, and a piece of gum that turns out to be a clue.

Premise
-------
A child follows a puzzling dim light, asks questions out loud, and discovers
that the clue is not scary at all. The story turns on curiosity: the child
investigates, the helper explains, and the ending reveals that the dim thing
was simply gum stuck under a lantern, causing the strange glow. The world is
built so the state changes drive the prose, not the other way around.

Core beats
----------
1. A child notices a gum-dim mystery in a cozy place.
2. Dialogue and curiosity push them to inspect it.
3. A helper or parent explains the clue.
4. The child cleans it up or moves it, and the dim glow becomes bright again.
5. The ending image proves what changed.

The style aims for short, child-facing rhyming prose with conversation.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/gum_dim_dialogue_curiosity_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/gum_dim_dialogue_curiosity_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/gum_dim_dialogue_curiosity_rhyming_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/gum_dim_dialogue_curiosity_rhyming_story.py --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    dim_place: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    weird: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cleanup:
    id: str
    label: str
    sense: int
    action: str
    result: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_curious(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curious",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["wonder"] += 1
    clue.meters["noticed"] += 1
    out.append("__curious__")
    return out


def _r_clean(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    light = world.entities.get("light")
    if not clue or not light:
        return out
    if clue.meters["sticky"] < THRESHOLD:
        return out
    sig = ("clean",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["sticky"] = 0
    light.meters["dim"] = 0
    light.meters["bright"] += 1
    out.append("__clean__")
    return out


CAUSAL_RULES = [Rule("curious", "social", _r_curious), Rule("clean", "physical", _r_clean)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(clue: Clue, setting: Setting) -> bool:
    return "gum-dim" in clue.tags and "dim" in setting.tags


def curious_enough(child: Entity) -> bool:
    return child.memes["curiosity"] >= THRESHOLD


def story_setup(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f"At {world.setting.place}, {child.id} saw a gum-dim glow and gave a curious little sigh."
    )
    world.say(
        f'"Why is the lamp so dim?" asked {child.id}. "{helper.id}, do you know?"'
    )
    child.memes["curiosity"] += 1
    helper.memes["gentle"] += 1
    clue.meters["sticky"] += 1


def inspect(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f'"Let us peek," said {helper.id}, "and check the streaks that cling."'
    )
    world.say(
        f'{child.id} leaned in close, not to boast, but to learn what the odd glow might mean.'
    )
    propagate(world, narrate=False)
    if curious_enough(child):
        world.say(f"{child.id} looked and looked, with eyes like bright beans in a dream.")
    clue.memes["mystery"] += 1


def reveal(world: World, helper: Entity, clue: Clue) -> None:
    world.say(
        f'"Ah-ha," said {helper.id}, "that sticky old gum is the reason the lamp looks glum."'
    )
    world.say(
        f'"It caught the shine and dimmed the line; now let us wipe it clean."'
    )
    clue.meters["sticky"] = 0
    clue.meters["revealed"] += 1
    world.get("light").meters["bright"] += 1
    world.get("light").meters["dim"] = 0


def cleanup(world: World, child: Entity, helper: Entity, cleanup: Cleanup) -> None:
    world.say(
        f'Together they used {cleanup.label}, as tidy as a rhyme, and {cleanup.action}.'
    )
    world.say(
        f'In no time, {cleanup.result}, and the room felt right again.'
    )
    child.memes["pride"] += 1
    helper.memes["pride"] += 1


def ending(world: World) -> None:
    world.say(
        f"{world.setting.ending_image}"
    )


def tell(setting: Setting, clue: Clue, cleanup: Cleanup, child_name: str = "Maya",
         child_gender: str = "girl", helper_name: str = "Dad",
         helper_gender: str = "father") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="curious"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    light = world.add(Entity(id="light", type="thing", label="lamp", tags={"light"}))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, tags=set(clue.tags)))
    world.add(Entity(id="room", type="room", label=setting.place))
    world.facts.update(child=child, helper=helper, clue=clue, cleanup=cleanup, light=light)
    story_setup(world, child, helper, clue)
    world.para()
    inspect(world, child, helper, clue)
    world.para()
    reveal(world, helper, clue)
    cleanup(world, child, helper, cleanup)
    world.para()
    ending(world)
    world.facts.update(
        child=child,
        helper=helper,
        clue=clue_ent,
        cleanup=cleanup,
        outcome="bright",
    )
    return world


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        dim_place="the dim nursery nook",
        ending_image="Then the lamp shone bright, and the nursery glowed soft and warm.",
        tags={"dim", "room"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        dim_place="the dim playroom corner",
        ending_image="Then the lamp shone bright, and the playroom sparkled like a sunny song.",
        tags={"dim", "room"},
    ),
}

CLUES = {
    "gum-dim": Clue(
        id="gum-dim",
        label="gum-dim",
        phrase="a sticky gum-dim smear",
        weird="glum and dim",
        reveal="sticky gum makes the light look dim",
        tags={"gum-dim"},
    ),
}

CLEANUPS = {
    "wipe": Cleanup(
        id="wipe",
        label="a soft cloth",
        sense=3,
        action="they wiped the smear away",
        result="the lamp grew bright and clear",
        tags={"clean"},
    ),
    "peel": Cleanup(
        id="peel",
        label="a gentle scraper",
        sense=2,
        action="they peeled the gum-dim off with care",
        result="the shine came back with a cheerful flare",
        tags={"clean"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    clue: str
    cleanup: str
    child_name: str = "Maya"
    child_gender: str = "girl"
    helper_name: str = "Dad"
    helper_gender: str = "father"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(
        setting="nursery",
        clue="gum-dim",
        cleanup="wipe",
        child_name="Maya",
        child_gender="girl",
        helper_name="Dad",
        helper_gender="father",
        seed=None,
    ),
    StoryParams(
        setting="playroom",
        clue="gum-dim",
        cleanup="peel",
        child_name="Finn",
        child_gender="boy",
        helper_name="Mom",
        helper_gender="mother",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for uid, cleanup in CLEANUPS.items():
                if reasonableness_gate(clue, setting) and cleanup.sense >= 2:
                    combos.append((sid, cid, uid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming curiosity storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.cleanup is None or c[2] == args.cleanup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, cleanup = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(["Maya", "Finn", "Lila", "Owen"])
    helper_name = args.helper or rng.choice(["Mom", "Dad"])
    child_gender = "girl" if child_name in {"Maya", "Lila"} else "boy"
    helper_gender = "mother" if helper_name == "Mom" else "father"
    return StoryParams(setting=setting, clue=clue, cleanup=cleanup,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.cleanup not in CLEANUPS:
        raise StoryError("Invalid StoryParams values.")
    world = tell(SETTINGS[params.setting], CLUES[params.clue], CLEANUPS[params.cleanup],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a rhyming story that includes the word "{world.facts["clue"].id}" and a child asking questions.',
        f"Tell a curious little dialogue story where {world.facts['child'].id} asks why the lamp is dim.",
        "Write a gentle rhyme about a child, a sticky clue, and a bright ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    clue = world.facts["clue"]
    cleanup = world.facts["cleanup"]
    return [
        ("What did the child notice?", f"{child.id} noticed a dim lamp and a sticky gum-dim clue."),
        ("Why was the lamp dim?", f"The lamp looked dim because sticky gum-dim was clinging to it. The gum made the light seem glum until they cleaned it."),
        ("How did they fix it?", f"{helper.id} helped {child.id} clean the gum away with {cleanup.label}. Then the lamp grew bright again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does curiosity do?", "Curiosity makes someone ask questions and look closely. It helps them learn what a strange thing really is."),
        ("What is gum?", "Gum is a chewy snack people sometimes chew. If it sticks somewhere, it can make a mess."),
        ("What happens when a lamp is clean?", "A clean lamp can shine more brightly. Nothing blocks the light, so the room looks clearer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("gum_dim", cid))
    for uid, cleanup in CLEANUPS.items():
        lines.append(asp.fact("cleanup", uid))
        lines.append(asp.fact("sense", uid, cleanup.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, U) :- setting(S), clue(C), cleanup(U), gum_dim(C), sense(U, N), N >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
