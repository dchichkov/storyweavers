#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/poem_country_testicle_suspense_nursery_rhyme.py
==============================================================================================================

A tiny nursery-rhyme story world about a child, a country walk, and a tense
little missing thing that must be found before a poem can be sung.

This world is built from the seed words:
- poem
- country
- testicle

The domain is intentionally small: one child, one caregiver, one beloved poem,
one country setting, and one suspenseful problem with a gentle resolution.
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

GENDERS = ("girl", "boy")
PARENTS = {"mother", "father", "grandmother", "grandfather"}
PLACES = {
    "country_lane": "the country lane",
    "country_meadow": "the country meadow",
    "country_cottage": "the country cottage",
}
MOODS = ("gentle", "cheery", "brave", "curious", "tiny")
OBJECTS = {
    "bell": {
        "label": "little silver bell",
        "phrase": "a little silver bell",
        "region": "hand",
        "type": "bell",
    },
    "ribbon": {
        "label": "blue ribbon",
        "phrase": "a blue ribbon tied in a bow",
        "region": "head",
        "type": "ribbon",
    },
    "book": {
        "label": "poem book",
        "phrase": "a small poem book with a yellow cover",
        "region": "hand",
        "type": "book",
    },
}

NAMES_GIRL = ["Maya", "Lily", "Nora", "Ruby", "Hazel", "Mina"]
NAMES_BOY = ["Theo", "Ben", "Finn", "Eli", "Robin", "Otis"]


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
    suspense: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _risk(world: World, actor: Entity, prize: Entity, activity: Activity) -> bool:
    return prize.region in activity.zone and not world.covered(actor, prize.region)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} did {activity.gerund}, and the little air felt bright and quick.")


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("fumble", 0.0) >= THRESHOLD and actor.memes.get("fear", 0.0) >= THRESHOLD:
            sig = ("tremble", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["suspense"] = actor.memes.get("suspense", 0.0) + 1
                out.append(f"{actor.id} held still and listened for the missing sound.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**e.__dict__}) for k, e in world.entities.items()}
    sim.zone = set(world.zone)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize2 = sim.get(prize.id)
    return {"lost": _risk(sim, sim.get(actor.id), prize2, activity), "fear": actor.memes.get("fear", 0.0)}


def introduce(world: World, hero: Entity, mood: str) -> None:
    world.say(
        f"{hero.id} was a little {mood} {hero.type}, and {hero.pronoun()} loved to sing a poem in a soft, sweet tone."
    )


def setup_poem(world: World, hero: Entity, poem: Entity) -> None:
    poem.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} poem book and carried {poem.it()} everywhere in the country."
    )


def arrive(world: World, hero: Entity, caregiver: Entity, setting: Setting) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {caregiver.type} went to {setting.place}, where the grass stood green and quiet."
    )


def want(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} little {prize.label} began to feel important and hard to keep safe."
    )


def warn(world: World, caregiver: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict(world, hero, activity, prize)
    if pred["lost"]:
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
        world.facts["warning"] = True
        world.say(
            f'"If you {activity.verb}, you might lose {prize.it()} in the {world.setting.place.replace("the ", "")}," '
            f"{caregiver.pronoun('subject')} said, with a hush as soft as a nursery tune."
        )
    else:
        world.say(f"{caregiver.pronoun('subject').capitalize()} smiled, for the little plan seemed safe.")


def fumble(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    hero.meters["fumble"] = hero.meters.get("fumble", 0.0) + 1
    world.say(
        f"{hero.id} took a tiny step, then another, and the air felt hold-your-breath still."
    )
    world.say(f"{hero.id} tried to {activity.rush}, but paused when the path went dark under the hedge.")


def find_solution(world: World, caregiver: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=caregiver.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"Then {caregiver.id} found {gear_def.label} and said, '{gear_def.prep}.'"
    )
    world.say(
        f"{hero.id} listened, wore {gear_def.label}, and the little {prize.label} stayed safe."
    )
    world.say(
        f"{gear_def.tail.capitalize()}, and the poem could breathe again."
    )


def ending(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At the end, {hero.id} was {activity.gerund}, {prize.label} tucked snug and neat, and the country path felt like a tune."
    )


SETTINGS = {
    "lane": Setting(place=PLACES["country_lane"], outdoors=True, affords={"sing", "run"}),
    "meadow": Setting(place=PLACES["country_meadow"], outdoors=True, affords={"sing", "dance"}),
    "cottage": Setting(place=PLACES["country_cottage"], outdoors=True, affords={"sing"}),
}

ACTIVITIES = {
    "sing": Activity(
        id="sing",
        verb="sing the poem",
        gerund="singing the poem",
        rush="hurry to the hill and sing",
        mess="strain",
        soil="all hoarse",
        zone={"voice"},
        keyword="poem",
        tags={"poem", "suspense", "nursery"},
        suspense="The poem must be finished before the sky turns dim.",
    ),
    "run": Activity(
        id="run",
        verb="run down the lane",
        gerund="running down the lane",
        rush="dash past the gate",
        mess="scatter",
        soil="all scattered",
        zone={"hand"},
        keyword="country",
        tags={"country", "suspense"},
        suspense="The little road is winding, and one small thing could slip away.",
    ),
    "dance": Activity(
        id="dance",
        verb="dance in a ring",
        gerund="dancing in a ring",
        rush="spin and skip",
        mess="flutter",
        soil="all fluttery",
        zone={"hand"},
        keyword="rhyme",
        tags={"nursery", "suspense"},
        suspense="The beat is quick, and the step must be careful.",
    ),
}

PRIZES = {
    "book": Prize(label="book", phrase="a small poem book with a yellow cover", type="book", region="hand"),
    "bell": Prize(label="bell", phrase="a little silver bell", type="bell", region="hand"),
    "ribbon": Prize(label="ribbon", phrase="a blue ribbon tied in a bow", type="ribbon", region="head"),
}

GEAR = [
    Gear(
        id="pocket",
        label="a deep pocket",
        covers={"hand"},
        guards={"scatter"},
        prep="put the book in a deep pocket first",
        tail="they tucked the book safely inside a deep pocket",
    ),
    Gear(
        id="scarf",
        label="a soft scarf",
        covers={"voice"},
        guards={"strain"},
        prep="wrap a soft scarf around the throat first",
        tail="they wrapped the scarf gently and the voice stayed warm",
    ),
    Gear(
        id="ribbon_tie",
        label="a ribbon tie",
        covers={"head"},
        guards={"flutter"},
        prep="tie the ribbon tight before the dance",
        tail="they tied the ribbon tight and it did not fly away",
    ),
]

KNOWLEDGE = {
    "poem": [
        (
            "What is a poem?",
            "A poem is a small piece of writing or song with careful words and a special beat.",
        )
    ],
    "country": [
        (
            "What does country mean?",
            "Country means the land outside towns and cities, with fields, lanes, animals, and open air.",
        )
    ],
    "suspense": [
        (
            "What is suspense?",
            "Suspense is the feeling of wondering what will happen next when something is not settled yet.",
        )
    ],
    "nursery": [
        (
            "What is a nursery rhyme?",
            "A nursery rhyme is a short, simple rhyme or song for children, often with a steady beat and playful words.",
        )
    ],
    "testicle": [
        (
            "What is a testicle?",
            "A testicle is one of two body parts in the male body that make sperm and hormones.",
        )
    ],
}

KNOWLEDGE_ORDER = ["poem", "country", "testicle", "suspense", "nursery"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "sing" and prize == "book":
                    combos.append((place, act, prize))
                elif act == "run" and prize in {"bell", "ribbon"}:
                    combos.append((place, act, prize))
                elif act == "dance" and prize in {"ribbon", "bell"}:
                    combos.append((place, act, prize))
    return combos


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caregiver, prize, act = f["hero"], f["caregiver"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {world.setting.place}?",
            answer=f"{hero.id} was trying to {act.verb} while keeping {hero.pronoun('possessive')} {prize.label} safe.",
        ),
        QAItem(
            question=f"Why did {caregiver.id} speak so gently?",
            answer=f"{caregiver.id} spoke gently because the {prize.label} could be lost during {act.gerund}.",
        ),
        QAItem(
            question=f"What happened after the helper gear came out?",
            answer=f"After the helper gear came out, {hero.id} could keep going and the little trouble went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("testicle")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, act = f["hero"], f["prize"], f["activity"]
    return [
        f'Write a short nursery rhyme about a child named {hero.id}, the {world.setting.place}, and a tiny suspenseful problem.',
        f"Tell a gentle country story where {hero.id} wants to {act.verb} and must keep {hero.pronoun('possessive')} {prize.label} safe.",
        'Write a simple poem-story that uses the words "poem", "country", and "testicle" in a child-safe way.',
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP gates:")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
        return 1
    print(f"OK: ASP and Python agree on {len(py)} valid combos.")
    sample = generate(resolve_params(argparse.Namespace(place=None, activity=None, prize=None, gender=None, parent=None, name=None), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generated story is empty.")
        return 1
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with country suspense and a tiny poem problem.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=sorted(PARENTS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(sorted(PARENTS))
    mood = rng.choice(MOODS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, mood=mood)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.parent, label=params.parent))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=caregiver.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, params.mood)
    setup_poem(world, hero, world.add(Entity(id="poem", type="book", label="poem book", phrase="a small poem book with a yellow cover", owner=hero.id)))
    world.para()
    arrive(world, hero, caregiver, setting)
    want(world, hero, activity, prize)
    warn(world, caregiver, hero, activity, prize)
    fumble(world, hero, activity)
    if activity.id == "sing":
        gear = GEAR[1]
    elif activity.id == "run":
        gear = GEAR[0]
    else:
        gear = GEAR[2]
    find_solution(world, caregiver, hero, prize, gear)
    world.para()
    ending(world, hero, prize, activity)

    world.facts.update(hero=hero, caregiver=caregiver, prize=prize, activity=activity, setting=setting)
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
    StoryParams(place="lane", activity="sing", prize="book", name="Maya", gender="girl", parent="mother", mood="gentle"),
    StoryParams(place="meadow", activity="run", prize="bell", name="Theo", gender="boy", parent="grandmother", mood="curious"),
    StoryParams(place="cottage", activity="dance", prize="ribbon", name="Ruby", gender="girl", parent="father", mood="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        stories = valid_story_combos()
        print(f"{len(combos)} valid combos ({len(stories)} gendered):")
        for place, act, prize in combos:
            print(f"  {place:10} {act:6} {prize:6}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
