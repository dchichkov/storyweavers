#!/usr/bin/env python3
"""
storyworlds/worlds/atlas_notion_bad_ending_suspense_fable.py
============================================================

A small fable-style story world about an atlas, a notion, and a suspenseful
wrong turn that ends badly.

Premise:
- A young traveler carries an atlas that points to a safe path home.
- A tempting notion suggests a shortcut through a risky place.

Suspense:
- The sky darkens, a sound follows in the brush, and the traveler must choose
  between the careful atlas and the hasty notion.

Bad ending:
- The shortcut is wrong.
- The atlas is damaged and the traveler ends the tale still lost.

This world is intentionally narrow: a few plausible configurations are better
than many weak ones.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    gloom: str
    sounds: list[str]
    affords: set[str]


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    activity: str
    item: str
    name: str
    title: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


def pronounce_title(title: str) -> str:
    return {"fox": "fox", "hare": "hare", "mouse": "mouse", "otter": "otter"}.get(title, title)


SETTINGS = {
    "moor": Setting(
        place="the moor",
        gloom="The moor was open and gray, and the wind kept combing the grass flat.",
        sounds=["a far caw", "the hush of reeds", "a low whistle in the grass"],
        affords={"shortcut", "crossing"},
    ),
    "wood": Setting(
        place="the wood",
        gloom="The wood was dim and close, and the branches knitted the light into strips.",
        sounds=["a twig snap", "the soft tap of a hollow nut", "a rustle behind the ferns"],
        affords={"shortcut", "crossing"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        gloom="The riverbank smelled wet and cold, and the water kept muttering over stones.",
        sounds=["water over stone", "a drip from the reeds", "a hidden splash"],
        affords={"shortcut", "crossing"},
    ),
}

ACTIVITIES = {
    "shortcut": Activity(
        id="shortcut",
        verb="take the shortcut",
        gerund="taking the shortcut",
        rush="hurry into the narrow path",
        risk="the path might vanish in the dark",
        mess="lost",
        zone={"path"},
        keyword="shortcut",
    ),
    "crossing": Activity(
        id="crossing",
        verb="cross the rough ground",
        gerund="crossing the rough ground",
        rush="step into the rough ground",
        risk="the ground might snag the traveler and tear the pages",
        mess="torn",
        zone={"ground"},
        keyword="crossing",
    ),
}

ITEMS = {
    "atlas": Item(
        label="atlas",
        phrase="a small atlas with a blue cover",
        type="atlas",
        region="hands",
    ),
    "notion": Item(
        label="notion",
        phrase="a quick notion about a shortcut",
        type="notion",
        region="mind",
    ),
}

NAMES = ["Milo", "Tara", "Iris", "Ned", "Pia", "Juno", "Otis", "Lena"]
TITLES = ["fox", "hare", "mouse", "otter"]
TRAITS = ["careful", "curious", "proud", "hasty", "small", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_name, setting in SETTINGS.items():
        for a_id in setting.affords:
            for item_id in ITEMS:
                if a_id == "shortcut" and item_id == "atlas":
                    out.append((s_name, a_id, item_id))
                if a_id == "crossing" and item_id == "atlas":
                    out.append((s_name, a_id, item_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world of an atlas, a notion, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    return StoryParams(setting=setting, activity=activity, item=item, name=name, title=title)


def predict_bad_end(world: World, hero: Entity, act: Activity, item: Entity) -> dict:
    sim = world.copy()
    simulate(sim, hero.id, act.id, narrate=False)
    atlas = sim.get(item.id)
    return {
        "lost": bool(sim.facts.get("lost")),
        "torn": atlas.meters.get("torn", 0.0) >= THRESHOLD,
    }


def simulate(world: World, hero_id: str, activity_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    act = ACTIVITIES[activity_id]
    atlas = world.get("atlas")
    notion = world.get("notion")

    hero.memes["worry"] = hero.memes.get("worry", 0) + 0.5
    if narrate:
        world.say(f"{hero.id} looked at {atlas.label} and felt the little pull of {notion.label}.")
        world.say(f"The {world.setting.place} was near enough to tempt {hero.pronoun('object')}, but the sky was already dim.")

    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    atlas.meters["safe"] = atlas.meters.get("safe", 0) + 0  # keep the atlas as a physical object in play

    if activity_id == "shortcut":
        world.facts["suspense_sound"] = random.choice(world.setting.sounds)
        if narrate:
            world.say(f"{world.setting.gloom} Near {hero.pronoun('object')}, {world.facts['suspense_sound']} made {hero.pronoun('object')} pause.")
            world.say(f"But the notion was quick and bright, and {hero.id} chose to {act.verb}.")
        hero.memes["hurry"] = hero.memes.get("hurry", 0) + 1
        hero.meters["off_path"] = 1
        atlas.meters["wet"] = atlas.meters.get("wet", 0) + 1
        atlas.meters["torn"] = atlas.meters.get("torn", 0) + 1
        world.facts["lost"] = True
        if narrate:
            world.say(f"The ground shifted under {hero.pronoun('object')}, and the {atlas.label} snagged on a thorn.")
            world.say(f"By the time {hero.id} understood, the pages were damp and folded wrong, and the way home had gone quiet.")
    else:
        if narrate:
            world.say(f"{world.setting.gloom} {hero.id} tried to {act.verb}, but the rough ground made every step uncertain.")
            world.say(f"{hero.id} held the atlas tight anyway, yet the uneven way still caught the edge of {hero.pronoun('possessive')} map.")
        atlas.meters["torn"] = atlas.meters.get("torn", 0) + 1
        world.facts["lost"] = True

    world.facts["ending"] = "bad"


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    act = ACTIVITIES[params.activity]
    item = ITEMS[params.item]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.title))
    atlas = world.add(Entity(id="atlas", type="atlas", label="atlas", phrase=item.phrase, owner=hero.id))
    notion = world.add(Entity(id="notion", type="notion", label="notion", phrase="a quick notion about a shortcut"))
    world.facts.update(hero=hero, atlas=atlas, notion=notion, activity=act, setting=setting)

    world.say(f"Once, there was a little {pronounce_title(params.title)} named {hero.id}, and {hero.id} carried an atlas home from the hill.")
    world.say(f"{hero.id} also kept a notion in mind: maybe the shortcut would be faster.")
    world.say(f"But old tales say a bright notion can be a poor guide when the road grows dark.")

    simulate(world, hero.id, act.id, narrate=True)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    atlas: Entity = f["atlas"]
    act: Activity = f["activity"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a small {hero.type} who carried an atlas and tried to trust a notion."
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {act.verb}, even though the atlas pointed to the safer way home."
        ),
        QAItem(
            question="What happened to the atlas by the end?",
            answer="The atlas was damaged. Its pages ended damp and torn, so it could not guide the traveler home cleanly."
        ),
    ]
    if f.get("lost"):
        qa.append(QAItem(
            question=f"Why was the ending suspenseful and bad?",
            answer=(
                f"The ending was suspenseful because the road grew uncertain and a sound in the dark made {hero.id} hesitate. "
                f"It was bad because {hero.id} followed the notion instead of the atlas, got lost, and the atlas was ruined."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an atlas?",
            answer="An atlas is a book of maps that helps you find places and paths."
        ),
        QAItem(
            question="What is a notion?",
            answer="A notion is an idea that comes into your mind, like a thought about what to do next."
        ),
        QAItem(
            question="Why can a shortcut be risky?",
            answer="A shortcut can be risky because it may be hard to follow, especially when the light is fading or the ground is rough."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    act: Activity = f["activity"]
    setting: Setting = f["setting"]
    return [
        f'Write a short fable for young children about an atlas and a notion in {setting.place}.',
        f"Tell a suspenseful story where {hero.id} wants to {act.verb} and the choice ends badly.",
        f"Write a gentle moral tale that uses the words 'atlas' and 'notion' and ends with a wrong turn.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
good_path(S,A,I) :- setting(S), affords(S,A), item(I), A = shortcut, I = atlas.
suspense(S) :- setting(S).
bad_ending(S,A,I) :- good_path(S,A,I), lost.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for a in sorted(SETTINGS[s].affords):
            lines.append(asp.fact("affords", s, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_path/3."))
    return sorted(set(asp.atoms(model, "good_path")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
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
    StoryParams(setting="moor", activity="shortcut", item="atlas", name="Milo", title="hare"),
    StoryParams(setting="wood", activity="shortcut", item="atlas", name="Tara", title="fox"),
    StoryParams(setting="riverbank", activity="crossing", item="atlas", name="Iris", title="mouse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_path/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_path/3."))
        combos = sorted(set(asp.atoms(model, "good_path")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
            except StoryError as err:
                print(err)
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
            header = f"### {p.name}: {p.activity} at {p.setting} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
