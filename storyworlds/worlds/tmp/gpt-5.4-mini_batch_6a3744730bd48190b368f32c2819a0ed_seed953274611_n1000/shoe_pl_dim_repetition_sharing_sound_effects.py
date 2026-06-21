#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shoe_pl_dim_repetition_sharing_sound_effects.py
===============================================================================

A tiny folk-tale storyworld about a pair of worn shoes, a dim path, a shared
lamplight, and the rhythm of repeating footsteps and sound effects.

Seed words:
- shoe-pl-dim

Features:
- Repetition
- Sharing
- Sound Effects

Style:
- Folk Tale

This script is self-contained, stdlib-only, and follows the Storyweavers world
contract closely enough for CLI, JSON, QA, trace, and ASP parity checks.
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

NAMES = ["Mira", "Pip", "Lina", "Jory", "Nell", "Tavi", "Suri", "Bram"]
HELPER_NAMES = ["Grandmother", "Old Ben", "Aunt Kira", "the miller", "the baker"]
PLACE_NAMES = ["the forest lane", "the hill path", "the river road", "the mossy track"]
SHARES = ["a lantern", "a candle lantern", "a little torch", "a warm lamp"]
SOUND_WORDS = ["plip-plop", "tap-tap", "clip-clop", "squeak-squeak", "pat-pat"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    wears: bool = False
    pair: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    dim: bool
    path_text: str
    repeated_step: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShoePair:
    id: str
    label: str
    phrase: str
    sound: str
    dim: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    glow: str
    warm: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    shoe_pair: str
    share_item: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "forest": Setting(
        id="forest",
        place="the forest lane",
        dim=True,
        path_text="The trees leaned close, and the path went dim under their boughs.",
        repeated_step="step-step, step-step",
        tags={"forest", "dim"},
    ),
    "hill": Setting(
        id="hill",
        place="the hill path",
        dim=True,
        path_text="The hill path wound up and down, and the evening made it dim and blue.",
        repeated_step="tap-tap, tap-tap",
        tags={"hill", "dim"},
    ),
    "river": Setting(
        id="river",
        place="the river road",
        dim=True,
        path_text="The river road shimmered by day, but at dusk it turned dim and quiet.",
        repeated_step="plip-plop, plip-plop",
        tags={"river", "dim"},
    ),
}

SHOE_PAIRS = {
    "worn_boots": ShoePair(
        id="worn_boots",
        label="worn boots",
        phrase="a pair of worn boots",
        sound="clop-clop",
        dim=True,
        tags={"shoes", "sound"},
    ),
    "soft_shoes": ShoePair(
        id="soft_shoes",
        label="soft shoes",
        phrase="a pair of soft shoes",
        sound="squeak-squeak",
        dim=True,
        tags={"shoes", "sound"},
    ),
    "little_clogs": ShoePair(
        id="little_clogs",
        label="little clogs",
        phrase="a pair of little clogs",
        sound="clip-clop",
        dim=True,
        tags={"shoes", "sound"},
    ),
}

SHARE_ITEMS = {
    "lantern": ShareItem(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="glowed gold and steady",
        warm=True,
        tags={"sharing", "light"},
    ),
    "lamp": ShareItem(
        id="lamp",
        label="lamp",
        phrase="a warm lamp",
        glow="glowed soft and bright",
        warm=True,
        tags={"sharing", "light"},
    ),
    "candle": ShareItem(
        id="candle",
        label="candle",
        phrase="a candle in a tin cup",
        glow="shone with a tiny brave flame",
        warm=True,
        tags={"sharing", "light"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for shoe_id, shoe in SHOE_PAIRS.items():
            if not shoe.dim or not setting.dim:
                continue
            for item_id, item in SHARE_ITEMS.items():
                if item.warm:
                    combos.append((sid, shoe_id, item_id))
    return combos


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about a dim path, shared light, and repeating footsteps."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shoe-pair", dest="shoe_pair", choices=SHOE_PAIRS)
    ap.add_argument("--share-item", dest="share_item", choices=SHARE_ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
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
              and (args.shoe_pair is None or c[1] == args.shoe_pair)
              and (args.share_item is None or c[2] == args.share_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, shoe_pair, share_item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(
        setting=setting,
        shoe_pair=shoe_pair,
        share_item=share_item,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def _setup(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    shoes = SHOE_PAIRS[params.shoe_pair]
    share = SHARE_ITEMS[params.share_item]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="walker"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    path = world.add(Entity(id="path", type="place", label=setting.place))
    shoes_ent = world.add(Entity(id="shoes", type="thing", label=shoes.label, pair=True))
    light_ent = world.add(Entity(id="light", type="thing", label=share.label))
    world.facts.update(setting=setting, shoes=shoes, share=share, hero=hero, helper=helper, path=path, shoes_ent=shoes_ent, light_ent=light_ent)
    hero.meters["tired"] = 0.0
    helper.memes["kind"] = 1.0


def _r_repeat(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    setting = world.facts["setting"]
    shoes = world.facts["shoes"]
    sig = ("repeat", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["journey"] = hero.meters.get("journey", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    out.append(f"step-step, step-step, the little shoes went on.")
    out.append(f"{shoes.sound}! The old road answered with a small sound of its own.")
    out.append(f"{setting.repeated_step} went the feet, and the dim lane felt less lonely.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    share = world.facts["share"]
    sig = ("share", hero.id, helper.id)
    if sig in world.fired:
        return out
    if hero.meters.get("journey", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    helper.memes["kind"] = helper.memes.get("kind", 0.0) + 1
    out.append(f"Then {helper.id} lifted {share.phrase} and said they could use it together.")
    out.append(f"{share.glow.capitalize()}, and the dark path was not so dim anymore.")
    return out


def _r_finish(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    share = world.facts["share"]
    sig = ("finish", hero.id, helper.id)
    if sig in world.fired:
        return out
    if helper.memes.get("kind", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    hero.meters["arrival"] = 1.0
    helper.meters["arrival"] = 1.0
    out.append(f"So they went on by {share.label} and by {hero.id}'s brave little steps.")
    out.append(f"At the end of the lane, the two of them stood smiling in the lamp-glow.")
    return out


CAUSAL_RULES = [_r_repeat, _r_share, _r_finish]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    collected: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                collected.extend(lines)
    if narrate:
        for line in collected:
            world.say(line)


def tell(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    setting = world.facts["setting"]
    shoes = world.facts["shoes"]
    share = world.facts["share"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]

    world.say(
        f"Once upon a dusk, {hero.id} put on {shoes.phrase} and listened to the road."
    )
    world.say(setting.path_text)
    world.para()
    world.say(
        f"{hero.id} went on with {shoes.sound}, {shoes.sound}, and every step was a little song."
    )
    world.say(
        f"But the lane was dim, and {hero.id} wished for a light."
    )
    world.para()
    world.say(
        f"Then {helper.id} came along with {share.phrase}."
    )
    world.say(
        f'"Come share this with me," {helper.id} said, and the two walked side by side.'
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In that small folk tale way, the shoes kept their rhythm, the light was shared, and the dim path grew friendly."
    )
    world.say(
        f"Step-step, step-step, they went home together under the warm glow."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale that includes the word "shoe-pl-dim" and uses repeated footsteps and sound effects.',
        f"Tell a short story where {f['hero'].id} walks a dim path, shares a light with {f['helper'].id}, and the shoes make clear sounds.",
        f'Write a gentle story with repetition, sharing, and sound words about {f["shoes"].label} on a dim road.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    shoes = f["shoes"]
    share = f["share"]
    return [
        QAItem(
            question=f"What did {hero.id} wear on the road?",
            answer=f"{hero.id} wore {shoes.phrase}. The shoes helped make the walking sound steady and old-timey."
        ),
        QAItem(
            question=f"Why did {hero.id} want the light?",
            answer=f"The path was dim, so {hero.id} wanted help seeing the way. When {helper.id} shared {share.phrase}, the road felt less lonely."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the two of them walking home together in the shared glow. The repeated steps and the sound of the shoes turned the dim path into a friendly one."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is only a little light. Things can still be seen, but not as clearly as in bright daylight."
        ),
        QAItem(
            question="Why do people share a lantern on a dark path?",
            answer="They share a lantern so everyone can see the way and stay together. One light helps the whole group move safely through the dark."
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that let you hear the action in your mind, like clip-clop or tap-tap. They make the story feel lively."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting(S).
shoe_pair(S) :- shoe_pair(S).
share_item(I) :- share_item(I).

dim_story(S, P, I) :- setting(S), shoe_pair(P), share_item(I), dim_setting(S), dim_shoes(P), warm_item(I).
valid(S, P, I) :- dim_story(S, P, I).

story_ok(S, P, I) :- valid(S, P, I), sharing(I), soundy(P), folk(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dim:
            lines.append(asp.fact("dim_setting", sid))
        if "folk" in s.tags:
            lines.append(asp.fact("folk", sid))
    for pid, p in SHOE_PAIRS.items():
        lines.append(asp.fact("shoe_pair", pid))
        if p.dim:
            lines.append(asp.fact("dim_shoes", pid))
        if "sound" in p.tags:
            lines.append(asp.fact("soundy", pid))
    for iid, item in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", iid))
        if item.warm:
            lines.append(asp.fact("warm_item", iid))
        if "sharing" in item.tags:
            lines.append(asp.fact("sharing", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1

    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, shoe_pair=None, share_item=None,
            hero=None, hero_gender=None, helper=None, helper_gender=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1

    try:
        out = asp.one_model(asp_program("#show valid/3."))
        if not out:
            raise RuntimeError("no ASP model")
        print("OK: ASP smoke test passed.")
    except Exception as exc:
        print(f"ASP SMOKE TEST FAILED: {exc}")
        rc = 1

    return rc


def explain_rejection() -> str:
    return "(No story: this tiny folk tale wants dim shoes, a shared light, and a path that can be made friendly.)"


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.shoe_pair not in SHOE_PAIRS:
        raise StoryError("Unknown shoe pair.")
    if params.share_item not in SHARE_ITEMS:
        raise StoryError("Unknown share item.")
    if (params.setting, params.shoe_pair, params.share_item) not in valid_combos():
        raise StoryError(explain_rejection())

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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for setting, shoe_pair, share_item in combos:
            print(f"  {setting:8} {shoe_pair:12} {share_item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="forest", shoe_pair="worn_boots", share_item="lantern", hero="Mira", hero_gender="girl", helper="Grandmother", helper_gender="girl"),
            StoryParams(setting="hill", shoe_pair="soft_shoes", share_item="lamp", hero="Pip", hero_gender="boy", helper="Old Ben", helper_gender="boy"),
            StoryParams(setting="river", shoe_pair="little_clogs", share_item="candle", hero="Lina", hero_gender="girl", helper="Aunt Kira", helper_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero} walking through {p.setting} with {p.shoe_pair} and {p.share_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
