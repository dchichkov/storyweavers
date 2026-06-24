#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
===============================================================================================================================

A small heartwarming story world about a child, a frown, a caper, and a gentle
reconciliation after a surprise sound makes the whole day feel better.

The seed words are woven into the world model:
- deceased
- frown
- caper

The narrative instruments are:
- Reconciliation
- Sound Effects

The world is intentionally small and classical: one child worries, a playful
caper unfolds, a little misunderstanding softens, and the ending proves what
changed in the world.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    token: str
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False),
    "kitchen": Setting(place="the kitchen", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Nora", "Theo"]
HELPER_NAMES = ["Aunt Junie", "Grandpa", "Mom", "Dad", "Big Sam", "Aunt Rosa"]
CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "grandmother", "grandfather", "woman", "man"]
TOKENS = ["deceased", "frown", "caper"]


ASP_RULES = r"""
token(deceased). token(frown). token(caper).
heartwarming_story :- token(deceased), token(frown), token(caper).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("token", t) for t in TOKENS]
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show heartwarming_story/0."))
    ok = any(sym.name == "heartwarming_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the heartwarming seed.")
        return 0
    print("MISMATCH: ASP twin did not recognize the seed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world with a caper and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    child_name = args.name or rng.choice(CHILD_NAMES)
    child_type = rng.choice(CHILD_TYPES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = "mother" if "Mom" in helper_name else "father" if "Dad" in helper_name else rng.choice(HELPER_TYPES)
    token = rng.choice(TOKENS)
    return StoryParams(place=place, child_name=child_name, child_type=child_type,
                       helper_name=helper_name, helper_type=helper_type, token=token)


def _sound(text: str) -> str:
    return f"{text}"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    token = world.add(Entity(id="token", type="thing", label=params.token, phrase=f"the word {params.token}"))

    child.meters["worry"] = 1.0
    child.memes["frown"] = 1.0
    world.facts.update(child=child, helper=helper, token=token, params=params)

    world.say(
        f"{child.label} was a little {child.type} who had a soft frown after hearing the word "
        f"'{params.token}'."
    )
    world.say(
        f"At {world.setting.place}, {helper.label} noticed the frown and stayed close with a warm smile."
    )

    world.para()
    world.say(
        f"That afternoon, they planned a tiny caper: a surprise that would turn the quiet day into a kind one."
    )
    world.say(
        _sound("It went like this: tap-tap, hush, rustle, and then a bright little ding! ")
        + f"The sound made {child.label} look up."
    )

    world.para()
    world.say(
        f"{helper.label} explained that the word '{params.token}' had made the moment feel heavy, but it did not have to stay that way."
    )
    child.memes["sad"] = 1.0
    child.memes["hope"] = 1.0
    world.say(
        f"{child.label} listened, then nodded. The frown loosened, because {helper.label} was being gentle and clear."
    )

    world.para()
    child.memes["frown"] = 0.0
    child.memes["joy"] = 1.0
    child.meters["calm"] = 1.0
    world.say(
        f"Then came the reconciliation: {child.label} stepped closer, hugged {helper.label}, and whispered sorry for pulling away."
    )
    world.say(
        f"{helper.label} hugged back. Together they shared one more sound effect: chime-chime, soft and sweet."
    )
    world.say(
        f"By the end, {child.label}'s face was bright again, and the little caper had turned into a memory that felt safe to keep."
    )

    world.facts["reconciled"] = True
    world.facts["sound_effects"] = ["tap-tap", "ding", "chime-chime"]
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a heartwarming story for a young child where {p.child_name} hears '{p.token}', frowns, and then feels better.",
        f"Tell a gentle story about a tiny caper, warm help, and reconciliation at {world.setting.place}.",
        f"Create a simple story that includes the word '{p.token}' and ends with a soothing sound effect.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"Why did {p.child_name} start the story with a frown?",
            answer=f"{p.child_name} started with a frown because hearing the word '{p.token}' made the moment feel heavy and sad.",
        ),
        QAItem(
            question=f"What kind of small plan did {p.child_name} and {helper.label} make?",
            answer=f"They made a tiny caper, which was a playful little plan that led them toward a kinder moment.",
        ),
        QAItem(
            question=f"How did the story end for {p.child_name} and {helper.label}?",
            answer=f"It ended with reconciliation: {p.child_name} hugged {helper.label}, apologized, and felt bright and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frown?",
            answer="A frown is a facial expression where someone's mouth and eyebrows look worried or unhappy.",
        ),
        QAItem(
            question="What is a caper?",
            answer="A caper is a playful or slightly sneaky little adventure, usually meant to cause a surprise rather than real harm.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who felt upset make peace again, talk kindly, and feel close once more.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that imitate sounds, like tap-tap or chime-chime, so the reader can hear the moment in their head.",
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
        lines.append(f"  {e.id:8} ({e.type:12}) {e.label:12} {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show heartwarming_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show heartwarming_story/0."))
        print("heartwarming_story" if any(sym.name == "heartwarming_story" for sym in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="garden", child_name="Mia", child_type="girl", helper_name="Mom", helper_type="mother", token="deceased"),
            StoryParams(place="porch", child_name="Noah", child_type="boy", helper_name="Grandpa", helper_type="grandfather", token="frown"),
            StoryParams(place="kitchen", child_name="Luna", child_type="girl", helper_name="Aunt Rosa", helper_type="woman", token="caper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
