#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wretched_beach_lesson_learned_dialogue_nursery_rhyme.py
=======================================================================================

A small storyworld set at the beach: a child finds a wretched little shell in the sand,
tries to keep it, gets a lesson from a calm helper through dialogue, and ends by
choosing a kinder, safer, cleaner way to play.

The tone aims for nursery-rhyme simplicity with a gentle rhythm, dialogue, and a clear
lesson learned at the end.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
    breeze: str
    sound: str


@dataclass
class Trifle:
    id: str
    label: str
    phrase: str
    wretched: bool = False
    shell: bool = False
    smell: bool = False
    tideline: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    comfort: str
    remedy: str
    sense: int
    power: int


@dataclass
class StoryParams:
    setting: str
    trifle: str
    helper: str
    child: str
    child_gender: str
    guide: str
    guide_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "beach": Setting(id="beach", place="the beach", breeze="salt", sound="the sea went swish-swish"),
}

TRIFLES = {
    "wretched_shell": Trifle(id="wretched_shell", label="a wretched little shell", phrase="a wretched little shell", wretched=True, shell=True),
    "sticky_algae": Trifle(id="sticky_algae", label="a sticky clump of algae", phrase="a sticky clump of algae", wretched=True, smell=True),
    "muddy_pebble": Trifle(id="muddy_pebble", label="a muddy pebble", phrase="a muddy pebble", wretched=True, tideline=True),
}

HELPERS = {
    "mother": Helper(id="mother", label="mom", phrase="Mom", comfort="a soft towel", remedy="washed the hands and sang a calm song", sense=3, power=3),
    "father": Helper(id="father", label="dad", phrase="Dad", comfort="a warm bucket of water", remedy="showed how to rinse the sand away", sense=3, power=3),
    "lifeguard": Helper(id="lifeguard", label="the lifeguard", phrase="the lifeguard", comfort="a bright whistle", remedy="guided the child to a clean place and showed a better way to help", sense=4, power=4),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Theo", "Max", "Finn", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("beach", tid, hid) for tid in TRIFLES for hid in HELPERS]


def explain_rejection(setting: str, trifle: str, helper: str) -> str:
    if setting not in SETTINGS:
        return "(No story: this world only knows the beach.)"
    if trifle not in TRIFLES:
        return "(No story: that little thing is not in the beach basket.)"
    if helper not in HELPERS:
        return "(No story: that helper is not in the beach tale.)"
    return "(No story: that combination does not fit this small beach world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme beach storyworld with a lesson learned and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trifle", choices=TRIFLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy", "mother", "father", "woman", "man"])
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
    if args.setting and args.setting != "beach":
        raise StoryError("(No story: this nursery-rhyme world is set at the beach.)")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    if args.trifle and args.trifle not in TRIFLES:
        raise StoryError("(No story: unknown beach trifle.)")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("(No story: unknown helper.)")
    setting = "beach"
    trifle = args.trifle or rng.choice(list(TRIFLES))
    helper = args.helper or rng.choice(list(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guide = args.guide or HELPERS[helper].phrase
    guide_gender = args.guide_gender or helper
    return StoryParams(
        setting=setting,
        trifle=trifle,
        helper=helper,
        child=child,
        child_gender=child_gender,
        guide=guide,
        guide_gender=guide_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    trifle = TRIFLES[params.trifle]
    helper_cfg = HELPERS[params.helper]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    tr = world.add(Entity(id="trifle", kind="thing", type="thing", label=trifle.label))

    child.memes["curiosity"] = 1.0
    child.memes["want"] = 1.0
    if trifle.wretched:
        child.memes["disgust"] = 1.0
    if trifle.smell:
        tr.meters["smell"] = 1.0
    if trifle.tideline:
        tr.meters["wet"] = 1.0

    world.say(
        f"By the bright blue sea, {child.id} went skipping along. "
        f"{setting.sound}, and the sand sparkled soft and long."
    )
    world.say(
        f"Then {child.id} found {trifle.phrase} in the sand. "
        f'"Oh dear," {child.pronoun()} cried, "it looks so wretched in my hand."'
    )

    world.para()
    world.say(
        f'"May I keep it?" asked {child.id}. "May I take it home with me?"'
    )
    world.say(
        f'"No, no," said {helper_cfg.phrase}. "{trifle.label} belongs to the beach and the breezy sea."'
    )

    child.memes["upset"] = 1.0
    helper.memes["calm"] = 1.0

    world.para()
    world.say(
        f'"But it is mine now," said {child.id}, "and I want it in my toy box too."'
    )
    world.say(
        f'"Listen, little one," said {helper_cfg.phrase}, "there is a kinder choice for you to do."'
    )
    world.say(
        f'"What choice?" asked {child.id}. "What choice can there be?"'
    )
    world.say(
        f'"We can leave it with the shells," said {helper_cfg.phrase}, '
        f'"and clean your hands with {helper_cfg.comfort} by the sea."'
    )

    child.memes["lesson"] = 1.0
    child.memes["upset"] = 0.0
    child.memes["joy"] = 1.0
    world.para()
    world.say(
        f'{child.id} paused, then smiled. "Oh! I see, I see." '
        f'"A beach thing stays on the beach. That is the right thing for me."'
    )
    world.say(
        f'"Yes," said {helper_cfg.phrase}, and {helper_cfg.remedy}."'
    )
    world.say(
        f'So {child.id} set {trifle.label} back on the sand, waved to the waves, '
        f'and washed the salt away.'
    )
    world.say(
        f'And there by the shining tide, {child.id} felt wiser, kinder, and no longer wretched inside.'
    )

    world.facts.update(
        child=child,
        helper=helper,
        trifle=tr,
        setting=setting,
        trifle_cfg=trifle,
        helper_cfg=helper_cfg,
        lesson_learned=child.memes.get("lesson", 0.0) >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style beach story that includes the word "wretched" and a clear lesson learned.',
        f"Tell a small dialogue story set at {f['setting'].place} where {f['child'].id} wants to keep {f['trifle_cfg'].label}, but a calm helper explains a better choice.",
        f'Write a child-friendly story with seaside rhythm where a wretched little thing is found, talked about, and left behind kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper_cfg = f["helper_cfg"]
    trifle = f["trifle_cfg"]
    return [
        QAItem(
            question="What did the child find?",
            answer=f"{child.id} found {trifle.label} in the sand. It looked wretched, but it was only a little beach thing that did not belong in a toy box."
        ),
        QAItem(
            question="What did the helper say?",
            answer=f"{helper_cfg.phrase} said that the thing belonged to the beach and that {child.id} should leave it there. Then {helper_cfg.phrase} showed a kinder way to clean up and move on."
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson was that some things belong where they are found. It is kinder to leave beach things on the beach and choose a cleaner, safer play instead."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beach?",
            answer="A beach is a place by the sea with sand, waves, and salty air. People can walk there and watch the water."
        ),
        QAItem(
            question="What does wretched mean?",
            answer="Wretched means very unpleasant, miserable, or pitiful. It can describe something that looks sad and scruffy."
        ),
        QAItem(
            question="Why should some beach things stay on the beach?",
            answer="Because they may be wet, sandy, or part of the place where they belong. Leaving them there keeps them safe and keeps hands cleaner too."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.setting == "beach" and params.trifle in TRIFLES and params.helper in HELPERS


ASP_RULES = r"""
valid(S,T,H) :- setting(S), trifle(T), helper(H), beach(S).
"""


def asp_facts() -> str:
    import asp
    out = [asp.fact("beach", "beach")]
    for tid in TRIFLES:
        out.append(asp.fact("trifle", tid))
    for hid in HELPERS:
        out.append(asp.fact("helper", hid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
        print("python only:", sorted(p - a))
        print("asp only:", sorted(a - p))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trifle=None, helper=None, child=None, child_gender=None, guide=None, guide_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {err}")
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


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("(No story: invalid beach story parameters.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="beach", trifle="wretched_shell", helper="mother", child="Mia", child_gender="girl", guide="Mom", guide_gender="mother"),
    StoryParams(setting="beach", trifle="sticky_algae", helper="father", child="Leo", child_gender="boy", guide="Dad", guide_gender="father"),
    StoryParams(setting="beach", trifle="muddy_pebble", helper="lifeguard", child="Nora", child_gender="girl", guide="the lifeguard", guide_gender="lifeguard"),
]


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    trifle = args.trifle or rng.choice(list(TRIFLES))
    helper = args.helper or rng.choice(list(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guide_map = {"mother": "Mom", "father": "Dad", "lifeguard": "the lifeguard"}
    guide = args.guide or guide_map[helper]
    guide_gender = args.guide_gender or helper
    return StoryParams(
        setting="beach",
        trifle=trifle,
        helper=helper,
        child=child,
        child_gender=child_gender,
        guide=guide,
        guide_gender=guide_gender,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_from_args(args, random.Random(seed))
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child} by the {p.helper} at the beach"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
