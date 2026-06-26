#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/humorus_feature_epileptic_happy_ending_rhyming_story.py
===============================================================================================================

A tiny story world for a humorous, rhyming tale with a safe happy ending.

Premise:
- A child and a helper are preparing a small show.
- The show has a flashy "feature" that can become too bright or too fast.
- One character is epileptic and needs a calm, non-flickering version.
- The tension is resolved by swapping the risky feature for a gentle one.
- The ending is cheerful and rhyme-forward, with the show going well.

Seed words:
- humorus
- feature
- epileptic

Style:
- Rhyming Story
- Happy Ending
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


RHYME_ENDINGS = {
    "light": ["bright", "night", "light", "kite"],
    "song": ["song", "long", "strong", "gong"],
    "tune": ["moon", "tune", "spoon", "noon"],
    "smile": ["mile", "smile", "while", "style"],
}

FEATURES = {
    "glowshow": {
        "label": "glow show",
        "risk": "flicker",
        "safe": "steady glow",
        "meter_risk": "flashy",
        "meter_safe": "gentle",
        "tone": "sparkly",
        "setting": "the little stage",
        "problem": "too much flashing light",
        "fix": "turned the lights soft and slow",
    },
    "drumdash": {
        "label": "drum dash",
        "risk": "booming beats",
        "safe": "soft tapping",
        "meter_risk": "loud",
        "meter_safe": "quiet",
        "tone": "bouncy",
        "setting": "the cozy hall",
        "problem": "too much noise",
        "fix": "swapped the drums for tiny taps",
    },
    "balloonbounce": {
        "label": "balloon bounce",
        "risk": "rapid popping",
        "safe": "slow floating",
        "meter_risk": "jumpy",
        "meter_safe": "gentle",
        "tone": "silly",
        "setting": "the birthday room",
        "problem": "too many sudden pops",
        "fix": "let the balloons drift instead",
    },
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Ollie", "Zoe", "Theo"]
HELPERS = ["mom", "dad", "aunt", "uncle", "teacher", "big sister", "big brother"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, value: float = 1.0) -> None:
        self.meters[key] = self.m(key) + value

    def add_e(self, key: str, value: float = 1.0) -> None:
        self.memes[key] = self.e(key) + value

    def pronoun(self) -> str:
        return {"girl": "she", "boy": "he"}.get(self.type, "they")

    def possessive(self) -> str:
        return {"girl": "her", "boy": "his"}.get(self.type, "their")


@dataclass
class StoryParams:
    feature: str
    name: str
    helper: str
    gender: str
    seed: Optional[int] = None


@dataclass
class World:
    feature: dict
    hero: Entity
    helper: Entity
    prop: Entity
    stage: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous rhyming story with a safe happy ending.")
    ap.add_argument("--feature", choices=sorted(FEATURES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def _compat(feature_id: str, gender: Optional[str]) -> bool:
    return feature_id in FEATURES and (gender in (None, "girl", "boy"))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    feat = args.feature or rng.choice(sorted(FEATURES))
    if not _compat(feat, args.gender):
        raise StoryError("No reasonable story matches those choices.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(feature=feat, name=name, helper=helper, gender=gender)


def _make_world(params: StoryParams) -> World:
    f = FEATURES[params.feature]
    hero = Entity(id=params.name, kind="character", type=params.gender, traits=["humorous", "kind"])
    helper = Entity(id=params.helper, kind="character", type="adult", traits=["patient"])
    stage = Entity(id="stage", kind="place", type="place", label=f["setting"])
    prop = Entity(id="feature_prop", kind="thing", type="feature", label=f["label"], phrase=f["label"])
    world = World(feature=f, hero=hero, helper=helper, prop=prop, stage=stage)

    hero.add_e("hope", 1)
    hero.add_e("joy", 1)
    prop.add_m(f["meter_risk"], 1)
    return world


def _intro(world: World) -> None:
    hero = world.hero
    f = world.feature
    world.say(
        f"{hero.id} was a humorous little {hero.type} with a grin so wide; "
        f"{hero.pronoun().capitalize()} loved a shiny feature that made the whole room glide."
    )
    world.say(
        f"It was called the {f['label']}, and it lived on {f['setting']}; "
        f"{hero.id} thought its sparkle was a splendid sight to see."
    )


def _setup(world: World) -> None:
    hero = world.hero
    helper = world.helper
    f = world.feature
    world.para()
    world.say(
        f"One evening, {hero.id} and {helper.id} went to {f['setting']} with a tune in their feet. "
        f"They planned a tiny show that would be merry, bright, and sweet."
    )
    world.say(
        f"{hero.id} wanted the {f['label']} to blink and bounce and beam, "
        f"but {helper.id} knew a flashing crowd could break a gentle dream."
    )
    hero.add_e("desire", 1)
    helper.add_e("care", 1)


def _conflict(world: World) -> None:
    hero = world.hero
    helper = world.helper
    f = world.feature
    world.say(
        f"{helper.id} said, \"Your {f['label']} is fun, but the flicker may be rough; "
        f"for someone epileptic, bright-fast flashes can be too much.\""
    )
    hero.add_e("worry", 1)
    world.say(
        f"{hero.id} frowned a minute, then gave a tiny sigh; "
        f"{hero.pronoun().capitalize()} did not want the show to make a friend cry."
    )
    world.facts["risk"] = f["problem"]
    world.facts["safe"] = f["safe"]
    world.facts["fix"] = f["fix"]


def _turn(world: World) -> None:
    hero = world.hero
    helper = world.helper
    f = world.feature
    hero.add_e("insight", 1)
    hero.add_e("kindness", 1)
    world.say(
        f"Then {hero.id} had a humorus little idea as quick as a wink: "
        f"\"Let's change the feature to something safe, and make it make us think!\""
    )
    world.say(
        f"So {helper.id} helped the {f['label']} slow its shine and calm its beat; "
        f"the stage grew soft and steady, and the rhythm felt complete."
    )
    world.say(
        f"No more harsh little flickers, no more jumpy surprise; "
        f"just a mellow, moving glow that was easy on the eyes."
    )
    hero.add_e("relief", 1)
    helper.add_e("pride", 1)


def _ending(world: World) -> None:
    hero = world.hero
    helper = world.helper
    f = world.feature
    hero.add_e("joy", 2)
    world.para()
    world.say(
        f"At last the show went on, with a steady, friendly gleam; "
        f"{hero.id} bowed with {helper.id}, and the audience clapped in a stream."
    )
    world.say(
        f"The {f['label']} stayed safe and calm, and everyone could cheer; "
        f"that was the happy ending: fun for all, and no one had to fear."
    )


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _intro(world)
    _setup(world)
    _conflict(world)
    _turn(world)
    _ending(world)
    world.facts.update(
        name=params.name,
        helper=params.helper,
        feature=params.feature,
        feature_label=world.feature["label"],
        hero=world.hero,
        helper_entity=world.helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.feature
    return [
        f"Write a humorous rhyming story about {world.hero.id} and a {f['label']} with a happy ending.",
        f"Tell a child-friendly rhyme where a feature gets changed so an epileptic friend can enjoy the show.",
        f"Make a short playful poem-story about {world.hero.id}, {world.helper.id}, and a gentle stage feature.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.feature
    hero = world.hero
    helper = world.helper
    return [
        QAItem(
            question=f"What did {hero.id} want to use in the show?",
            answer=f"{hero.id} wanted to use the {f['label']} in the show.",
        ),
        QAItem(
            question=f"Why did {helper.id} ask for a safer change?",
            answer=(
                f"{helper.id} wanted to keep the show safe because flashing lights can bother "
                f"an epileptic friend."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily, with the feature changed to a calm version and everyone clapping."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does epileptic mean?",
            answer=(
                "Epileptic means a person has epilepsy, a medical condition that can make "
                "certain flashing lights or sudden patterns unsafe."
            ),
        ),
        QAItem(
            question="What makes a stage feature safer for someone sensitive to flashing?",
            answer=(
                "A safer stage feature uses steady, gentle light instead of fast flashing, so it is calmer to watch."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.prop, world.stage]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
feature_ok(F) :- feature(F).
safe_show(F) :- feature_ok(F), safe_version(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for fid, f in FEATURES.items():
        lines.append(asp.fact("feature", fid))
        lines.append(asp.fact("risk", fid, f["problem"]))
        lines.append(asp.fact("safe_version", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show safe_show/1."))
    clingo_set = set(asp.atoms(model, "safe_show"))
    py_set = {(fid,) for fid in FEATURES}
    if clingo_set == py_set:
        print(f"OK: ASP parity matched for {len(py_set)} features.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(clingo_set))
    print("  py :", sorted(py_set))
    return 1


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


CURATED = [
    StoryParams(feature="glowshow", name="Mia", helper="mom", gender="girl"),
    StoryParams(feature="drumdash", name="Leo", helper="dad", gender="boy"),
    StoryParams(feature="balloonbounce", name="Nora", helper="aunt", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_show/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as e:
            print(f"ASP unavailable: {e}")
            return
        model = asp.one_model(asp_program("#show safe_show/1."))
        print(sorted(set(asp.atoms(model, "safe_show"))))
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.feature} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
