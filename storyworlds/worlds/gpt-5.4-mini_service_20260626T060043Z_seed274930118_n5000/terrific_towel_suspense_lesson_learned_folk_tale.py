#!/usr/bin/env python3
"""
terrific_towel_suspense_lesson_learned_folk_tale.py
===================================================

A small folk-tale storyworld about a terrific towel, a little bit of suspense,
and a lesson learned.

Premise:
- A child or small animal in a village is tempted to use a beloved terrific towel
  in a risky way near water, mud, or wind.
- A careful elder warns that the towel may be lost, soaked, or snagged.
- Suspense grows while the towel is carried, hidden, dried, or swapped.
- The story ends with a lesson learned: cherish good things and use them wisely.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    near_water: bool = False
    windy: bool = False
    muddy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather_word: str
    zone: set[str]
    mess: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    cherished: str = "beloved"


@dataclass
class Helper:
    id: str
    label: str
    action: str
    lesson: str


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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def _narrative_verb(activity: Activity, setting: Setting) -> str:
    if activity.id == "river":
        return "splash in the river"
    if activity.id == "storm":
        return "dash through the storm"
    if activity.id == "wash":
        return "wash the old blanket"
    return activity.verb


def _predict_loss(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return bool(prize.meters.get("soaked", 0) >= THRESHOLD or prize.meters.get("lost", 0) >= THRESHOLD)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot host {activity.id}.)")
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    if activity.id in {"river", "storm"}:
        for e in world.entities.values():
            if e.owner == actor.id and e.label == "towel":
                if "body" in activity.zone:
                    e.meters["soaked"] = e.meters.get("soaked", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} went to {_narrative_verb(activity, world.setting)}.")
        if activity.id == "storm":
            world.say("The clouds were dark, and the wind kept tugging at the cloth.")
        elif activity.id == "river":
            world.say("The water flashed and whispered by the stones.")
        elif activity.id == "wash":
            world.say("The basin was warm, and the soap made little silver bubbles.")


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"Once in a small village, there lived a little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} had a {prize.cherished} {prize.label}, "
        f"so bright and soft that everyone called it a terrific towel."
    )
    world.say(
        f"{hero.id} liked to carry {hero.pronoun('possessive')} {prize.label} everywhere, "
        f"and {helper.label} often reminded {hero.pronoun('object')} to keep it dry and safe."
    )


def suspense_build(world: World, hero: Entity, activity: Activity, prize: Prize) -> None:
    world.para()
    world.say(
        f"One day, {hero.id} heard that the {_narrative_verb(activity, world.setting)} might "
        f"make the terrific towel wet, muddy, or lost."
    )
    world.say(
        f"{hero.id} wanted to go anyway, but {hero.pronoun('possessive')} heart beat fast, "
        f"for {activity.risk} could spoil the towel before sunset."
    )


def warning(world: World, helper: Entity, hero: Entity, prize: Prize, activity: Activity) -> bool:
    if not _predict_loss(world, hero, activity, prize.label):
        return False
    world.say(
        f'"Take care," said {helper.label}, "for if you {_narrative_verb(activity, world.setting)}, '
        f"your {prize.label} may be {activity.risk}."'
    )
    return True


def temptation(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wanting"] = hero.memes.get("wanting", 0.0) + 1.0
    world.say(
        f"{hero.id} still walked closer, because the river-song was sweet and the wind seemed to call."
    )
    world.say(f"{hero.pronoun().capitalize()} even reached for the path at once, ready to {activity.rush}.")


def pause_and_choose(world: World, helper: Entity, hero: Entity, prize: Prize, activity: Activity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(
        f"Then {hero.id} paused, held the terrific towel tight, and listened to {helper.label}."
    )
    world.say(
        f'"A good thing can still be a good thing when used wisely," said {helper.label}. '
        f'"Let us keep the {prize.label} high and dry, then choose the safer way."'
    )
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0


def resolution(world: World, hero: Entity, helper: Entity, prize: Prize, activity: Activity) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.para()
    world.say(
        f"So {hero.id} listened, and the two of them found a dry branch, a clean hook, or a warm sill "
        f"where the terrific towel could rest."
    )
    world.say(
        f"They still {_narrative_verb(activity, world.setting)}, but they kept the towel safe, "
        f"and {hero.id} learned that treasures last longer when folk use them with care."
    )
    world.say(
        f"By dusk, the terrific towel was safe and bright, and {hero.id} smiled like someone who had learned a lesson well."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "riverbank": Setting(place="the riverbank", near_water=True, windy=False, muddy=False, affords={"river", "wash"}),
    "hilltop": Setting(place="the hilltop", near_water=False, windy=True, muddy=False, affords={"storm"}),
    "farmyard": Setting(place="the farmyard", near_water=False, windy=False, muddy=True, affords={"storm", "wash"}),
}

ACTIVITIES = {
    "river": Activity(
        id="river",
        verb="play by the river",
        gerund="playing by the river",
        rush="run down to the water",
        risk="soaked",
        weather_word="water",
        zone={"body"},
        mess="splash",
        keyword="river",
    ),
    "storm": Activity(
        id="storm",
        verb="dance in the storm wind",
        gerund="dancing in the storm wind",
        rush="run after the flying cloth",
        risk="blown away",
        weather_word="wind",
        zone={"body"},
        mess="wind",
        keyword="storm",
    ),
    "wash": Activity(
        id="wash",
        verb="wash the towel in warm water",
        gerund="washing in warm water",
        rush="carry it to the basin",
        risk="damp",
        weather_word="soap",
        zone={"hands"},
        mess="soap",
        keyword="wash",
    ),
}

PRIZES = {
    "towel": Prize(label="towel", phrase="a terrific towel", region="hands", plural=False, cherished="terrific"),
}

HELPERS = {
    "grandmother": Helper(
        id="grandmother",
        label="Grandmother Reed",
        action="warned",
        lesson="A cherished thing should be protected before the trouble begins.",
    ),
    "goatherd": Helper(
        id="goatherd",
        label="the old goatherd",
        action="advised",
        lesson="A wise path keeps both joy and treasure together.",
    ),
}

HERO_NAMES = ["Mina", "Jory", "Pip", "Nell", "Bram", "Lila", "Toma", "Runa"]
HERO_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    hero_type: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    helper_cfg = HELPERS[params.helper]

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type="elder", label=helper_cfg.label))
    prize = world.add(Entity(
        id=prize_cfg.label,
        kind="thing",
        type="towel",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    introduce(world, hero, helper, prize)
    suspense_build(world, hero, activity, prize_cfg)
    world.para()
    if warning(world, helper, hero, prize_cfg, activity):
        temptation(world, hero, activity)
        pause_and_choose(world, helper, hero, prize_cfg, activity)
        _do_activity(world, hero, activity, narrate=True)
        resolution(world, hero, helper, prize_cfg, activity)
    else:
        world.say(
            f"But the elder saw no real danger, so the evening stayed calm and the towel was never at risk."
        )

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    helper = f["helper"]
    return [
        f"Write a folk tale about {hero.id} and a terrific towel, with a little suspense and a lesson learned.",
        f"Tell a gentle story where {hero.id} wants to {_narrative_verb(activity, f['setting'])} but {helper.label} worries about the terrific towel.",
        f"Make a short child-friendly tale in which a treasured towel is kept safe after a warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who loved a terrific towel and had to choose a safer way.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id}?",
            answer=f"{helper.label} warned {hero.id} because {_narrative_verb(activity, f['setting'])} could leave the terrific towel {activity.risk}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that a cherished {prize.label} should be cared for, and that wise choices keep good things safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a towel for?",
            answer="A towel is for drying hands, faces, or other things after water makes them wet.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means paying attention so you do not hurt something or let it get lost or broken.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next when something may go wrong.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A towel is at risk if the activity can soak, blow away, or dampen it.
at_risk(A,P) :- activity(A), prize(P), danger(A,P).

% A helpful choice is valid if it keeps the prize safe.
valid_story(Place, A, P) :- setting(Place), affords(Place, A), at_risk(A, P).

% Inline safety logic for the storyworld.
danger(river, towel).
danger(storm, towel).
danger(wash, towel).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    out = []
    for place, setting in SETTINGS.items():
        for a in setting.affords:
            if a in {"river", "storm", "wash"}:
                out.append((place, a, "towel"))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python validity ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and python:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Terrific towel folk tale with suspense and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    if activity not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {place} cannot host {activity}.)")
    prize = args.prize or "towel"
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, activity=activity, prize=prize, name=name, hero_type=hero_type, helper=helper)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="riverbank", activity="river", prize="towel", name="Mina", hero_type="girl", helper="grandmother"),
    StoryParams(place="hilltop", activity="storm", prize="towel", name="Bram", hero_type="boy", helper="goatherd"),
    StoryParams(place="farmyard", activity="wash", prize="towel", name="Lila", hero_type="girl", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid story combos:\n")
        for place, act, prize in combos:
            print(f"  {place:10} {act:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
