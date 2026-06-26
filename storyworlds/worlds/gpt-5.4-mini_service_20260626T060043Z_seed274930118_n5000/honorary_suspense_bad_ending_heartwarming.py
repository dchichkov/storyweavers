#!/usr/bin/env python3
"""
storyworlds/worlds/honorary_suspense_bad_ending_heartwarming.py
===============================================================

A small story world about an honorary title, a tense wait, and a tender
ending that does not quite fix the loss.

Seed premise:
- A child receives an honorary token for being especially kind.
- They take it to a lively place where wind, water, or movement can carry it
  away.
- The adults worry, the child hopes, and the token is lost.
- The ending is bad in the practical sense, but warm in the emotional sense:
  the honor still matters, even without the object.

This script is intentionally self-contained and uses only the standard library
plus the shared result containers.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", indoor=False, affords={"wind"}),
    "garden": Setting(place="the garden", indoor=False, affords={"sprinkles"}),
    "hall": Setting(place="the town hall", indoor=True, affords={"crowd"}),
}

ACTIVITIES = {
    "wind": Activity(
        id="wind",
        verb="watch the flags flap",
        gerund="watching the flags flap",
        rush="run to the railing",
        hazard="blown away",
        zone={"hands", "torso"},
        weather="windy",
        keyword="wind",
        tags={"wind", "suspense"},
    ),
    "sprinkles": Activity(
        id="sprinkles",
        verb="dance in the sprinklers",
        gerund="dancing in the sprinklers",
        rush="dash across the wet grass",
        hazard="smeared and soggy",
        zone={"feet", "torso"},
        weather="rainy",
        keyword="sprinkles",
        tags={"water", "suspense"},
    ),
    "crowd": Activity(
        id="crowd",
        verb="help hand out programs",
        gerund="handing out programs",
        rush="hurry between the chairs",
        hazard="creased and crumpled",
        zone={"hands", "torso"},
        weather="",
        keyword="crowd",
        tags={"busy", "suspense"},
    ),
}

PRIZES = {
    "pin": Prize(
        label="honorary pin",
        phrase="a small honorary pin",
        type="pin",
        region="torso",
    ),
    "ribbon": Prize(
        label="honorary ribbon",
        phrase="a bright honorary ribbon",
        type="ribbon",
        region="torso",
    ),
    "sash": Prize(
        label="honorary sash",
        phrase="a soft honorary sash",
        type="sash",
        region="torso",
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Lina", "Rosa", "Nia", "Pia", "Ivy", "Mara"]
BOY_NAMES = ["Noel", "Evan", "Owen", "Jude", "Finn", "Milo", "Theo", "Ezra"]
TRAITS = ["kind", "gentle", "brave", "patient", "sweet", "helpful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not put the {prize.label} at risk, "
        f"so there is no real suspense and no honest bad ending to tell.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this honor is not typical for a {gender} here; try --gender {ok}.)"


def setting_line(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was busy and bright, with chairs and footsteps everywhere."
    if activity.weather == "windy":
        return f"The air at {setting.place} kept tugging at sleeves and paper."
    return f"{setting.place.capitalize()} waited under a soft, watchful sky."


def predict_loss(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return bool(prize.meters.get("lost", 0) >= THRESHOLD)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.id] = actor.meters.get(activity.id, 0.0) + 1
    actor.memes["anticipation"] = actor.memes.get("anticipation", 0.0) + 1
    prize = world.facts["prize"]
    if prize.region in activity.zone and not prize.plural:
        prize.meters["risk"] = prize.meters.get("risk", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} began {activity.gerund}, and the moment felt full of suspense.")


def introduce(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved to help."
    )
    world.say(
        f"One afternoon, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} "
        f"{prize.phrase} for being so kind."
    )


def honor_celebration(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} wore {prize.it()} carefully and stood a little taller, because an honorary token "
        f"can make a child feel seen."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One day, "
    go = "went to" if not world.setting.indoor else "were at"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_line(world.setting, activity))


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, even though the air and the crowd made everyone hold still and listen."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    if predict_loss(world, hero, activity, prize.id):
        world.facts["predicted_loss"] = True
        world.say(
            f"'{prize.phrase} could get {activity.hazard},' {parent.pronoun('possessive')} {parent.label_word} said softly."
        )
        world.say(
            f"{hero.id} nodded, but the wish to go on tugged just as hard as the warning."
        )


def suspense(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} took a breath and stepped toward the fun, with {activity.keyword} in the air and worry in the corners."
    )
    world.say(
        f"Then {hero.id} tried to {activity.rush}, and everything felt like it might change in a blink."
    )


def loss(world: World, prize: Entity, activity: Activity) -> None:
    prize.meters["lost"] = prize.meters.get("lost", 0.0) + 1
    prize.worn_by = None
    world.say(
        f"The little honor was {activity.hazard}, and before anyone could catch it, {prize.label} slipped away."
    )


def comfort(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.id}'s eyes went shiny, and {hero.pronoun('possessive')} {parent.label_word} hugged {hero.pronoun('object')} close."
    )
    world.say(
        f'"The pin is gone, but what it means is still here," {parent.pronoun("possessive")} {parent.label_word} said. '
        f'"You were honored because you were kind."'
    )
    world.say(
        f"{hero.id} held that thought like a warm pebble in a pocket, even though {prize.label} was still missing."
    )


def ending(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"At the end, {hero.id} did not get the {prize.label} back."
    )
    world.say(
        f"But {hero.id} walked home with {hero.pronoun('possessive')} {parent.label_word}, still brave, still loved, and still honorary in the way that mattered."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["kind", "quiet"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)

    introduce(world, hero, parent, prize)
    honor_celebration(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    suspense(world, hero, activity)
    _do_activity(world, hero, activity)
    loss(world, prize, activity)

    world.para()
    comfort(world, parent, hero, prize)
    ending(world, hero, parent, activity, prize)
    return world


KNOWLEDGE = {
    "honorary": [
        (
            "What does honorary mean?",
            "Honorary means someone is given an honor, title, or special place because people want to show respect or thanks."
        )
    ],
    "wind": [
        (
            "Why can wind be tricky for paper things?",
            "Wind can be tricky because it can snatch light paper, flutter ribbons, and carry small things away."
        )
    ],
    "water": [
        (
            "Why do wet things get harder to hold?",
            "Wet things can become slippery, heavy, or soggy, so they are easier to drop or lose."
        )
    ],
    "crowd": [
        (
            "Why do busy crowds feel tense?",
            "Busy crowds can feel tense because many people are moving at once, and it is easy for things to get bumped or dropped."
        )
    ],
    "kind": [
        (
            "What does it mean to be kind?",
            "Being kind means using gentle words and helpful actions to make things better for other people."
        )
    ],
}

KNOWLEDGE_ORDER = ["honorary", "wind", "water", "crowd", "kind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about an "honorary" prize that is lost during {activity.keyword} at {world.setting.place}.',
        f"Tell a suspenseful but gentle story where {hero.id} receives {prize.phrase}, then worries start when {hero.pronoun('possessive')} {parent.label_word} notices it could be lost.",
        f"Write a short children's story with a bad ending that still feels warm and kind, using the word honorary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type}, and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What honorary thing did {hero.id} receive?",
            answer=f"{hero.id} received {prize.phrase} because {hero.pronoun('subject')} was kind and helpful.",
        ),
        QAItem(
            question=f"Why did the mood feel tense when {hero.id} went to {world.setting.place}?",
            answer=f"The mood felt tense because {prize.label} could get {activity.hazard} during {activity.gerund}, and everyone worried it might be lost.",
        ),
        QAItem(
            question=f"What happened to the honorary prize at the end?",
            answer=f"It was lost, and {hero.id} did not get it back.",
        ),
        QAItem(
            question=f"How did {hero.id}'s {parent.label_word} comfort {hero.id}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label_word} said that the honor still mattered, even though {prize.label} was gone.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("honorary")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", activity="wind", prize="ribbon", name="Mina", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="garden", activity="sprinkles", prize="sash", name="Noel", gender="boy", parent="father", trait="helpful"),
    StoryParams(place="hall", activity="crowd", prize="pin", name="Lina", gender="girl", parent="mother", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: honorary suspense with a heartwarming but bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:9} {act:12} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
