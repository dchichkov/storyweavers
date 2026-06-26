#!/usr/bin/env python3
"""
storyworlds/worlds/naval_going_rhyme_bad_ending_heartwarming.py
===============================================================

A small heartwarming naval-going storyworld with a rhyme tilt and a gentle
bad-ending turn: the planned trip goes wrong, but the ending image still holds
care, warmth, and connection.

The core tale this world imagines:
- A child is going out on a little naval boat with a grown-up helper.
- They carry something dear that they hope to show or deliver.
- A rhyme-like mishap makes the trip fail: the water turns rough, the trip is
  cut short, and the prize does not reach its intended place.
- Even so, the helper makes the child feel safe, seen, and loved.

The world is built as a tiny simulation with physical meters and emotional
memes. The prose follows state changes instead of swapping nouns into a fixed
template.
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
    ridden_by: Optional[str] = None
    plural: bool = False
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
    place: str
    affords: set[str] = field(default_factory=set)
    naval: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    carried: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wet(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("sea", 0.0) < THRESHOLD:
            continue
        if ("wet", actor.id) in world.fired:
            continue
        world.fired.add(("wet", actor.id))
        actor.meters["wet"] = actor.meters.get("wet", 0.0) + 1
        actor.memes["shiver"] = actor.memes.get("shiver", 0.0) + 1
        out.append(f"{actor.id} got wet as the sea spray leapt up.")
    return out


def _r_heart(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("hurt", 0.0) < THRESHOLD:
            continue
        if ("heart", actor.id) in world.fired:
            continue
        world.fired.add(("heart", actor.id))
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
        out.append(f"Still, {actor.id} held on to a warm little hope.")
    return out


CAUSAL_RULES = [Rule("wet", _r_wet), Rule("heart", _r_heart)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def predict_trip(world: World, actor: Entity, act: Activity) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.weather = world.weather
    hero = sim.get(actor.id)
    hero.meters["sea"] = hero.meters.get("sea", 0.0) + 1
    if act.id == "storm":
        hero.meters["storm"] = hero.meters.get("storm", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "soaked": hero.meters.get("wet", 0.0) >= THRESHOLD,
        "failed": hero.meters.get("storm", 0.0) >= THRESHOLD,
    }


def setting_line(setting: Setting, act: Activity) -> str:
    if setting.naval:
        return "The little naval harbor glimmered beside the dock, tidy and bright."
    return f"{setting.place.capitalize()} waited quietly, with room for a small going-out day."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved going on boat days.")


def love_rhyme(world: World, hero: Entity, act: Activity) -> None:
    world.say(
        rhyme_line(
            f"{hero.id} liked the steady sway",
            f"and the soft, bright start of a going day",
        )
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {act.gerund}, because the waves could sing "
        f"like a lullaby."
    )


def bring_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.ridden_by = hero.id
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} as carefully as a tiny treasure.")


def depart(world: World, hero: Entity, helper: Entity, act: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.type} went to {world.setting.place} "
        f"to {act.verb}."
    )
    world.say(setting_line(world.setting, act))


def warn(world: World, helper: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    pred = predict_trip(world, hero, act)
    if not pred["failed"]:
        return False
    world.facts["warned"] = True
    world.say(
        f'"The sky is turning gray," {helper.pronoun("subject")} said. '
        f'"If we keep {act.verb}, your {prize.label} may end up {act.hazard}."'
    )
    return True


def rush(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["eager"] = hero.memes.get("eager", 0.0) + 1
    world.say(f"{hero.id} still wanted to go on, so {hero.pronoun()} tried to {act.rush}.")


def storm_turn(world: World, hero: Entity, act: Activity) -> None:
    hero.meters["sea"] = hero.meters.get("sea", 0.0) + 1
    hero.meters["storm"] = hero.meters.get("storm", 0.0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    propagate(world, narrate=True)
    world.say(f"Then a splashy gust made the boat bob too hard, and the plan went all wrong.")


def return_home(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    helper.memes["tender"] = helper.memes.get("tender", 0.0) + 1
    world.say(
        f"{helper.id} wrapped an arm around {hero.id} and said they could turn back. "
        f"The trip was a bad ending, but not a bad love."
    )
    world.say(
        f"They went home with the {prize.label} still dry, and {helper.id} made warm tea for the cold hands."
    )


def comfort_end(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"Later, {hero.id} leaned against {helper.pronoun('possessive')} side and smiled at the {prize.label}. "
        f"It was still the same little treasure, and now it felt safer than ever."
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting("the harbor", affords={"row", "sail"}, naval=True),
    "dock": Setting("the dock", affords={"row", "sail"}, naval=True),
    "bay": Setting("the bay", affords={"row", "sail"}, naval=True),
}

ACTIVITIES = {
    "row": Activity("row", "go rowing", "going rowing", "row toward the little buoy", "soaked", "gray clouds", "rowing", {"water"}),
    "sail": Activity("sail", "go sailing", "going sailing", "sail past the rocks", "tossed and soggy", "windy clouds", "sailing", {"water"}),
    "storm": Activity("storm", "go out in the storm", "going out in the storm", "push toward the dark water", "splashed and lost", "stormy sky", "storm", {"water", "storm"}),
}

PRIZES = {
    "flag": Prize("flag", "a bright little flag", "flag"),
    "lantern": Prize("lantern", "a round brass lantern", "lantern"),
    "toy_boat": Prize("boat", "a painted toy boat", "toy boat"),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "captain": "captain",
}

GIRL_NAMES = ["Mina", "Lina", "Ruby", "Nora", "Ivy", "Sally"]
BOY_NAMES = ["Finn", "Otis", "Bram", "Leo", "Milo", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection() -> str:
    return "(No story: that exact naval-going choice does not make a good rhyme-and-turn tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming naval-going rhyme world with a gentle bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
        raise StoryError(explain_rejection())
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.weather = ACTIVITIES[params.activity].weather
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper))
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=helper.id))
    act = ACTIVITIES[params.activity]

    introduce(world, hero)
    love_rhyme(world, hero, act)
    bring_prize(world, hero, prize)

    world.para()
    depart(world, hero, helper, act)
    warn(world, helper, hero, act, prize)
    rush(world, hero, act)
    storm_turn(world, hero, act)

    world.para()
    return_home(world, helper, hero, prize)
    comfort_end(world, helper, hero, prize)

    world.facts.update(hero=hero, helper=helper, prize=prize, act=act, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["act"]
    prize = f["prize"]
    return [
        f'Write a short heartwarming story about {hero.id} going {act.keyword} by the naval water.',
        f'Tell a rhyming story where a child wants to {act.verb} but the weather turns bad near the {prize.label}.',
        f'Write a gentle story with a bad ending that still feels loving, using the word "{act.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["act"]
    return [
        QAItem(
            question=f"Where were {hero.id} and the helper going?",
            answer=f"They were going to {world.setting.place} to {act.verb}.",
        ),
        QAItem(
            question=f"What was {hero.id} carrying?",
            answer=f"{hero.id} was carrying {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did the trip turn into a bad ending?",
            answer=f"The weather and water turned rough, so the plan for {act.gerund} could not keep going the way they hoped.",
        ),
        QAItem(
            question=f"How did the helper make the ending feel warm?",
            answer=f"The helper brought {hero.id} home, wrapped {hero.id} in care, and made the child feel safe even though the trip failed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does naval mean?",
            answer="Naval means it has to do with ships, boats, or the sea.",
        ),
        QAItem(
            question="What is going?",
            answer="Going means moving from one place to another, often with a plan to get somewhere.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and night.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
good_trip(P,A,Z) :- place(P), activity(A), prize(Z).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for z in PRIZES:
        lines.append(asp.fact("prize", z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show good_trip/3."))
    combos = sorted(set(asp.atoms(model, "good_trip")))
    py = sorted(valid_combos())
    if combos:
        print(f"OK: ASP produced {len(combos)} generic trip facts.")
        return 0
    print("MISMATCH: ASP produced no model.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show good_trip/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("harbor", "row", "flag", "Mina", "girl", "mother"),
            StoryParams("dock", "sail", "lantern", "Finn", "boy", "father"),
            StoryParams("bay", "row", "toy_boat", "Lina", "girl", "captain"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
