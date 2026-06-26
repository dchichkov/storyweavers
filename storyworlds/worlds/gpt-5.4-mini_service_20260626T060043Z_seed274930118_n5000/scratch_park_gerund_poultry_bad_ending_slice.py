#!/usr/bin/env python3
"""
A small storyworld for a slice-of-life tale about a park visit, a scratch,
and a bit of poultry trouble that ends badly.

The world is intentionally compact:
- a child wants to enjoy a quiet day at the park
- there is a chicken coop / poultry pen nearby or a pet chicken at the park
- the child scratches an itch or scratches a thing at the park
- the scratch startles the poultry
- the poultry causes a small bad ending: food spills, feathers scatter, or a
  promised treat is ruined, leaving the child disappointed

The narrative is state-driven rather than template-swapped prose.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the park"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    scratch: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Poultry:
    id: str
    label: str
    phrase: str
    noise: str
    skittish: bool = True


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.facts = dict(self.facts)
        return clone


def _as_subject(name: str) -> str:
    return name


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _narrate_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _child_desc(hero: Entity) -> str:
    trait = next((t for t in hero.meters.keys() if False), None)
    return f"little {hero.type}"


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> list[str]:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot support {activity.id}.")
    world.zone = set(activity.zone)
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1.0
    hero.memes["restless"] = hero.memes.get("restless", 0.0) + 1.0
    out = []
    if narrate:
        out.append(f"{hero.id} did it anyway, and the little scratch made the moment feel worse.")
    return out


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"])
    bird = world.get(world.facts["poultry"])
    if hero.meters.get("scratch", 0.0) < THRESHOLD:
        return out
    sig = ("startle", bird.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.memes["startled"] = bird.memes.get("startled", 0.0) + 1.0
    out.append(f"The little scratch made {bird.label} jump and flap.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bird = world.get(world.facts["poultry"])
    treat = world.get(world.facts["treat"])
    hero = world.get(world.facts["hero"])
    if bird.memes.get("startled", 0.0) < THRESHOLD:
        return out
    sig = ("spill", treat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["ruined"] = treat.meters.get("ruined", 0.0) + 1.0
    hero.memes["disappointment"] = hero.memes.get("disappointment", 0.0) + 1.0
    out.append(f"Then the flapping knocked the snack to the dirt.")
    return out


def _r_bad_end(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"])
    treat = world.get(world.facts["treat"])
    if treat.meters.get("ruined", 0.0) < THRESHOLD:
        return out
    sig = ("badend", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1.0
    out.append("The day ended with a dirty snack and a quiet walk home.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_startle, _r_spill, _r_bad_end):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "park": Setting(place="the park", affords={"scratch"}),
}

ACTIVITIES = {
    "scratch": Activity(
        id="scratch",
        verb="sit on the bench and scratch at an itchy arm",
        gerund="sitting on the bench and scratching an itchy arm",
        scratch="scratch",
        mess="scratch",
        zone={"hands", "arms"},
        keyword="scratch",
        tags={"scratch"},
    )
}

POULTRY = {
    "chicken": Poultry(
        id="chicken",
        label="a nervous chicken",
        phrase="a nervous chicken pecking near the path",
        noise="cluck",
        skittish=True,
    ),
    "hen": Poultry(
        id="hen",
        label="a speckled hen",
        phrase="a speckled hen with quick feet",
        noise="cluck",
        skittish=True,
    ),
}

TREATS = {
    "cracker": Treat(
        id="cracker",
        label="a cracker packet",
        phrase="a small cracker packet in a paper bag",
        type="cracker",
        region="hands",
    ),
    "corn": Treat(
        id="corn",
        label="a corn snack",
        phrase="a little corn snack for later",
        type="corn",
        region="hands",
    ),
}

NAMES_BOY = ["Milo", "Ben", "Theo", "Sam", "Finn"]
NAMES_GIRL = ["Nina", "Maya", "Lily", "Ava", "June"]


@dataclass
class StoryParams:
    place: str
    activity: str
    poultry: str
    treat: str
    name: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for poultry_id in POULTRY:
                for treat_id in TREATS:
                    combos.append((place, act_id, f"{poultry_id}:{treat_id}"))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "park"
    activity = args.activity or "scratch"
    poultry = args.poultry or rng.choice(sorted(POULTRY))
    treat = args.treat or rng.choice(sorted(TREATS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if activity not in SETTINGS[place].affords:
        raise StoryError("That activity does not fit the setting.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place=place, activity=activity, poultry=poultry, treat=treat, name=name, gender=gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    bird_cfg = POULTRY[params.poultry]
    bird = world.add(Entity(id=bird_cfg.id, kind="character", type="chicken", label=bird_cfg.label, phrase=bird_cfg.phrase))
    treat_cfg = TREATS[params.treat]
    treat = world.add(Entity(id=treat_cfg.id, type=treat_cfg.type, label=treat_cfg.label, phrase=treat_cfg.phrase, caretaker=hero.id))
    world.facts.update(hero=hero.id, poultry=bird.id, treat=treat.id, activity=params.activity)

    act = ACTIVITIES[params.activity]
    world.say(f"{hero.id} was at {world.setting.place} on a quiet afternoon.")
    world.say(f"{hero.id} wanted to {act.verb}, because the sun felt warm and the bench felt safe.")
    world.say(f"Nearby, {bird.label} pecked around the path while {hero.id} held {treat.label}.")
    world.para()
    world.say(f"At first, everything was ordinary, like a soft slice of the day.")
    world.say(f"Then {hero.id} gave a small scratch at {hero.id}'s arm, just to make the itch stop.")
    hero.meters["scratch"] = hero.meters.get("scratch", 0.0) + 1.0
    propagate(world)
    world.para()
    if treat.meters.get("ruined", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} stared at the dirt-covered snack and felt the afternoon go flat.")
        world.say(f"{bird.label} wandered off, and {hero.id} had nothing left but crumbs and a grumpy walk home.")
    else:
        world.say(f"{hero.id} looked at the still-clean snack and breathed out in relief.")
    world.facts["resolved_badly"] = treat.meters.get("ruined", 0.0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = world.get(f["hero"])
    act = ACTIVITIES[f["activity"]]
    bird = world.get(f["poultry"])
    return [
        f'Write a short slice-of-life story about {hero.id} at the park, a scratch, and {bird.label}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but the little scratch scares a chicken and ruins the snack.",
        "Write a simple story with a bad ending set at the park, using the word scratch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get(f["hero"])
    bird = world.get(f["poultry"])
    treat = world.get(f["treat"])
    act = ACTIVITIES[f["activity"]]
    qa = [
        QAItem(
            question=f"Where was {hero.id} spending the afternoon?",
            answer=f"{hero.id} was spending the afternoon at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the trouble started?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} scratched {hero.id}'s arm?",
            answer=f"The scratch startled {bird.label}, and the flapping ruined {treat.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly, with {treat.label} ruined and {hero.id} going home disappointed.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scratch?",
            answer="A scratch is a quick rubbing or mark made by fingernails or something sharp.",
        ),
        QAItem(
            question="What is a chicken?",
            answer="A chicken is a bird that pecks, flaps, and makes clucking sounds.",
        ),
        QAItem(
            question="Why can a snack be ruined at the park?",
            answer="A snack can be ruined if it falls on the ground or gets dirty where birds can reach it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life park storyworld with a scratch and a bad ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--poultry", choices=sorted(POULTRY))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


ASP_RULES = r"""
valid(place,activity,poultry,treat) :- place(place), activity(activity), poultry(poultry), treat(treat),
                                       affords(place, activity).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in POULTRY:
        lines.append(asp.fact("poultry", pid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, a, b.split(":")[0], b.split(":")[1]) for p, a, b in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for gender in ("girl", "boy"):
            for name in (NAMES_GIRL if gender == "girl" else NAMES_BOY)[:2]:
                params = StoryParams(
                    place="park",
                    activity="scratch",
                    poultry="chicken",
                    treat="cracker",
                    name=name,
                    gender=gender,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
