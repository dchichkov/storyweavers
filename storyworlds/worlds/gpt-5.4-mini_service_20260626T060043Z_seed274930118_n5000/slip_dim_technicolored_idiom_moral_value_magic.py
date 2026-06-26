#!/usr/bin/env python3
"""
storyworlds/worlds/slip_dim_technicolored_idiom_moral_value_magic.py
=====================================================================

A small rhyming storyworld about a magic idiom, a slip-dim mishap, a
technicolored mess, and a bad ending that teaches a moral value too late.

Seed ingredients:
- slip-dim
- technicolored
- idiom

Story shape:
- A child finds a magic idiom in a bright little setting.
- The charm is tempting, but it spills technicolored magic onto a prized thing.
- The floor turns slip-dim, the plan goes wrong, and the ending is bad.
- The moral value is named in the aftermath, as the world stays changed.

This world is intentionally small and constraint-checked. Invalid combinations
raise StoryError with a readable reason.
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
    region: str = ""
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
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicAct:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    rhyme: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act_kind in MESS_KINDS:
            if actor.meters.get(act_kind, 0.0) < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.kind == "thing" and item.owner == actor.id and item.region in world.zone:
                    sig = ("soil", item.id, act_kind)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[act_kind] = item.meters.get(act_kind, 0.0) + 1
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                    out.append(f"{actor.id}'s {item.label} got {act_kind} and dirty.")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slip_dim", 0.0) < THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["wobble"] = actor.memes.get("wobble", 0.0) + 1
        out.append(f"The floor went slip-dim, and {actor.id} began to wobble and sway.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_slip,
]


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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setting_line(setting: Setting) -> str:
    return {
        "attic": "The attic was dim, but the lantern gleam made the shadows trim.",
        "kitchen": "The kitchen was bright, with spoons that shone in the morning light.",
        "garden": "The garden was green, with little paths between.",
        "classroom": "The classroom stood neat, with chalk dust soft beneath each seat.",
    }[setting.place]


def act_rhyme(act: MagicAct) -> str:
    return act.rhyme


def introduce(world: World, hero: Entity, value: Entity, act: MagicAct) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved a twinkly trick and a rhyming pick."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a moral value in mind: {value.label}, kind and kind."
    )
    world.say(
        f"And tucked in a book was a magic idiom, bright as a spark and quick as a plum."
    )
    world.say(
        f'"{act.verb}," the page said low, "and technicolored petals will glow."'
    )


def arrive(world: World, hero: Entity, prize: Entity, act: MagicAct) -> None:
    world.say(
        f"One day in {world.setting.place}, {hero.id} spotted {prize.phrase} and smiled so wide."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, though the little rhyme warned, " + f"'{act.rhyme}'."
    )


def cast_magic(world: World, hero: Entity, prize: Entity, act: MagicAct) -> None:
    hero.meters[act.mess] = hero.meters.get(act.mess, 0.0) + 1
    hero.meters["slip_dim"] = hero.meters.get("slip_dim", 0.0) + 1
    world.zone = set(act.zone)
    world.say(
        f"{hero.id} whispered the idiom and the room went technicolored bright."
    )
    world.say(
        f"But the shine turned sly; the floor turned slip-dim, and the play lost its light."
    )
    propagate(world, narrate=True)


def bad_ending(world: World, hero: Entity, prize: Entity, value: Entity, act: MagicAct) -> None:
    if prize.meters.get("dirty", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.id}'s {prize.label} got {act.soil}, and the pretty glow could not be stayed."
        )
    else:
        world.say(
            f"The magic still spilled, and the technicolored tint would not fade."
        )
    world.say(
        f"{hero.id} tried to laugh, but the room grew quiet, and the ending felt bad."
    )
    world.say(
        f"At last {hero.id} learned {value.label} means telling the truth, even when you feel sad."
    )


def tell(setting: Setting, act: MagicAct, prize_cfg: Prize, value: str, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    moral = world.add(Entity(id="value", kind="thing", type="value", label=value))

    introduce(world, hero, moral, act)
    world.para()
    world.say(setting_line(setting))
    arrive(world, hero, prize, act)
    cast_magic(world, hero, prize, act)
    world.para()
    bad_ending(world, hero, prize, moral, act)

    world.facts.update(hero=hero, parent=parent, prize=prize, value=moral, act=act, setting=setting)
    return world


SETTINGS = {
    "attic": Setting(place="attic", indoor=True, affords={"twirl", "chant"}),
    "kitchen": Setting(place="kitchen", indoor=True, affords={"chant", "glimmer"}),
    "garden": Setting(place="garden", indoor=False, affords={"twirl", "glimmer"}),
    "classroom": Setting(place="classroom", indoor=True, affords={"chant", "twirl"}),
}

ACTIVITIES = {
    "twirl": MagicAct(
        id="twirl",
        verb="twirl the charm",
        gerund="twirling the charm",
        rush="spin too quick",
        mess="technicolored",
        soil="technicolored and smudged",
        zone={"torso", "hands"},
        keyword="technicolored",
        rhyme="A twirl too bright may blur the night.",
    ),
    "chant": MagicAct(
        id="chant",
        verb="chant the idiom",
        gerund="chanting the idiom",
        rush="speak too fast",
        mess="magic",
        soil="magic-stained",
        zone={"hands", "face"},
        keyword="idiom",
        rhyme="A chant too proud may shout too loud.",
    ),
    "glimmer": MagicAct(
        id="glimmer",
        verb="glimmer the ribbon",
        gerund="glimmering the ribbon",
        rush="glow too bold",
        mess="slip_dim",
        soil="dim and slippery",
        zone={"feet", "floor"},
        keyword="slip-dim",
        rhyme="A glimmer thin may let you slip in.",
    ),
}

PRIZES = {
    "ribbon": Prize(label="ribbon", phrase="a technicolored ribbon", type="ribbon", region="hands"),
    "cookie": Prize(label="cookie", phrase="a sweet frosted cookie", type="cookie", region="hands"),
    "shoes": Prize(label="shoes", phrase="shiny little shoes", type="shoes", region="feet", plural=True),
}

VALUES = {
    "honesty": "honesty",
    "care": "care",
    "patience": "patience",
    "sharing": "sharing",
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "Mila", "Tess", "Zara"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Noah", "Theo", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    value: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld of magic, a slip-dim mishap, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def explain_rejection(act: MagicAct, prize: Prize) -> str:
    return (
        f"(No story: {act.gerund} does not reach {prize.label} in the right way, "
        f"so the magic would not create the slip-dim technicolored mess this world needs.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if prize.region not in act.zone:
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    value = args.value or rng.choice(sorted(VALUES))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize_id, value=value, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for children about "{f["act"].keyword}", a magic idiom, and a bad ending.',
        f"Tell a gentle tale where {f['hero'].id} tries to {f['act'].verb} near {f['setting'].place} and the result turns slip-dim.",
        f"Write a simple story with technicolored magic, a moral value, and an ending that goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, act, value = f["hero"], f["prize"], f["act"], f["value"]
    return [
        QAItem(
            question=f"What did {hero.id} try to do with the magic idiom?",
            answer=f"{hero.id} tried to {act.verb}.",
        ),
        QAItem(
            question=f"What happened to the floor in the story?",
            answer="The floor turned slip-dim, so the room became wobbly and hard to trust.",
        ),
        QAItem(
            question=f"What got ruined by the technicolored magic?",
            answer=f"{hero.id}'s {prize.label} got {act.soil}.",
        ),
        QAItem(
            question=f"What moral value did the story mention at the end?",
            answer=f"The story named {value.label} and said it matters even when the ending is bad.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(question="What is a magic idiom?", answer="A magic idiom is a special phrase that is meant to be spoken just so, like a little spell."),
        QAItem(question="What does technicolored mean?", answer="Technicolored means full of many bright colors, like a rainbow made into one thing."),
        QAItem(question="What does slip-dim mean?", answer="Slip-dim means the floor or path is dim and slippery, so it is easy to slide or wobble."),
        QAItem(question="What is a moral value?", answer="A moral value is a good lesson about how to act, like honesty or care."),
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="twirl", prize="ribbon", value="honesty", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="kitchen", activity="chant", prize="cookie", value="care", name="Finn", gender="boy", parent="father"),
    StoryParams(place="classroom", activity="glimmer", prize="shoes", value="patience", name="Lina", gender="girl", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], VALUES[params.value], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(format_qa(sample))


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), prize_region(P,R).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
