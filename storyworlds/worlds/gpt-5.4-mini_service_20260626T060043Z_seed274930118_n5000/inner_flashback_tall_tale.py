#!/usr/bin/env python3
"""
storyworlds/worlds/inner_flashback_tall_tale.py
================================================

A standalone story world for a small Tall Tale-style domain with a flashback:
a child wants to do something bold, an elder remembers an earlier lesson, and
a safer trick turns the trouble into a grin.

This world uses a compact simulation with physical meters and emotional memes.
The prose is authored from state changes, not from a frozen template.

Seed idea:
- A fearless child wants to race the wind across a big open place.
- The risk is real: loose paper, hats, and kites can be blown away.
- A flashback to an inner-pocket lesson reveals a clever fix.
- The ending proves what changed by showing the child using the fix.

The style leans Tall Tale: big images, concrete actions, and a memory that
matters in the present.
"""

from __future__ import annotations

import argparse
import copy
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"winded": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "wonder": 0.0, "flashback": 0.0}

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
    open_sky: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        return clone


SETTING = Setting(place="the open mesa", open_sky=True, affords={"kite", "whirl", "dust"})

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly the kite",
        gerund="flying kites",
        rush="run after the kite string",
        risk="might yank the paper sky-ribbon right out of hand",
        weather="windy",
        zone={"hands", "torso"},
        keyword="kite",
        tags={"wind", "kite"},
    ),
    "whirl": Activity(
        id="whirl",
        verb="spin with the wind",
        gerund="whirling like a pinwheel",
        rush="dash into the whirling breeze",
        risk="might send a hat spinning over the hills",
        weather="windy",
        zone={"head", "torso"},
        keyword="wind",
        tags={"wind"},
    ),
    "dust": Activity(
        id="dust",
        verb="dance in the dust",
        gerund="dancing in the dust",
        rush="stomp into the dust cloud",
        risk="might coat clothes and pockets with grit",
        weather="dry",
        zone={"legs", "torso"},
        keyword="dust",
        tags={"dust"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright red hat", type="hat", region="head"),
    "shirt": Prize(label="shirt", phrase="a clean blue shirt", type="shirt", region="torso"),
    "scarf": Prize(label="scarf", phrase="a long yarn scarf", type="scarf", region="torso"),
    "boots": Prize(label="boots", phrase="a pair of polished boots", type="boots", region="legs", plural=True),
}

GEAR = [
    Gear(
        id="inner-pocket-clasp",
        label="an inner-pocket clasp",
        covers={"torso"},
        guards={"dust", "wind"},
        prep="slip the map into an inner-pocket clasp first",
        tail="tucked the map into the inner pocket clasp",
    ),
    Gear(
        id="chin-strap",
        label="a chin strap",
        covers={"head"},
        guards={"wind"},
        prep="tie on a chin strap first",
        tail="buckled the chin strap snug under the chin",
    ),
    Gear(
        id="dust-wrap",
        label="a dust wrap",
        covers={"legs", "torso"},
        guards={"dust"},
        prep="wrap up in a dust wrap first",
        tail="went back for the dust wrap",
    ),
]

NAMES = {
    "girl": ["Mabel", "June", "Ruby", "Nell", "Cora", "Lena", "Ivy"],
    "boy": ["Benn", "Tate", "Rudy", "Hank", "Otis", "Finn", "Wade"],
}
TRAITS = ["bold", "bright-eyed", "stubborn", "lively", "curious", "spry"]


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in {"kite", "whirl"} and "wind" in gear.guards and prize.region in gear.covers:
            return gear
        if activity.id == "dust" and "dust" in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for act_id, act in ACTIVITIES.items():
        for prize_id, prize in PRIZES.items():
            if prize_at_risk(act, prize) and select_gear(act, prize):
                combos.append((act_id, prize_id))
    return combos


def activity_flair(activity: Activity) -> str:
    return {
        "kite": "The wind came in like a brass band and tugged at the clouds.",
        "whirl": "The breeze had a swagger to it, as if it owned the whole sky.",
        "dust": "The dust rolled over the mesa like a tan river with a funny grin.",
    }[activity.id]


def intro(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'bold')} {hero.type} who "
        f"loved tall adventures and big skies."
    )
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} and wore "
        f"{prize.it()} like a badge for the whole county to see."
    )
    world.say(activity_flair(activity))


def flashback(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["flashback"] += 1
    world.say(
        f"Then {parent.id} paused, and the story took a long step backward."
    )
    world.say(
        f"Long ago, when {hero.id} was smaller than a fence post, {parent.id} had "
        f"shown {hero.pronoun('object')} a clever trick: keep the important thing in "
        f"an inner pocket when the wind starts bragging."
    )
    world.say(
        f"{hero.id} remembered that lesson clear as a bell on a cold morning."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    world.facts["risk"] = activity.risk
    world.say(
        f'"If you try to {activity.verb}, {activity.risk}," {parent.pronoun("possessive")} '
        f"{parent.type} said."
    )
    return True


def choose_gear(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    world.say(
        f"{hero.id} grinned and remembered the old lesson. {parent.id} helped "
        f"{hero.pronoun('object')} {gear.prep}."
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"Then {hero.id} struck out across {world.setting.place} with the wind at "
        f"{hero.pronoun('possessive')} back."
    )
    world.say(
        f"The trick held fast, so {hero.pronoun('possessive')} {prize.label} stayed safe, "
        f"and the whole scene looked fit for a song."
    )
    world.say(
        f"By sunset, {hero.id} was {activity.gerund}, and the old inner-pocket lesson "
        f"had saved the day again."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    world.weather = ACTIVITIES[params.activity].weather

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"trait_word": params.trait, "joy": 0.0, "fear": 0.0, "wonder": 1.0, "flashback": 0.0},
    ))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=PRIZES[params.prize].region,
        plural=PRIZES[params.prize].plural,
    ))
    prize.worn_by = hero.id
    activity = ACTIVITIES[params.activity]

    intro(world, hero, parent, prize, activity)
    world.para()
    world.say(f"One day, {hero.id} and {parent.id} climbed out to {world.setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the trouble was plain as dust.")
    warn(world, parent, hero, activity, prize)
    flashback(world, hero, parent, prize, activity)
    gear = choose_gear(world, hero, parent, activity, prize)
    world.para()
    if gear:
        resolve(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short tall tale for a child named {hero.id} on an open mesa with the word "inner".',
        f"Tell a story where {hero.id} wants to {act.verb} but must remember an inner-pocket lesson about {prize.label}.",
        f"Write a lively flashback story with a huge wind, a brave child, and a safe trick that keeps {prize.label} from getting ruined.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} on the mesa?",
            answer=f"{hero.id}, the {hero.memes.get('trait_word', 'bold')} {hero.type}, wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about {hero.id}'s {prize.label}?",
            answer=f"{parent.id} worried because {act.risk}, so the {prize.label} could have been blown or dirtied.",
        ),
        QAItem(
            question="What old memory helped solve the problem?",
            answer="The flashback reminded the child to use an inner pocket for the important thing when the wind started showing off.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {prize.label}?",
            answer=f"They used {gear.label} and the {prize.label} stayed safe while the child kept playing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly steps back to an earlier time to explain something important now.",
        ),
        QAItem(
            question="What does an inner pocket do?",
            answer="An inner pocket helps hold something close to the body so it is less likely to slip out in a fuss or a strong wind.",
        ),
        QAItem(
            question="Why can wind make things hard to carry?",
            answer="Wind can tug, lift, and spin light things, so hats, papers, and kites can get away from you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(activity="kite", prize="hat", name="Mabel", gender="girl", parent="mother", trait="bold"),
    StoryParams(activity="dust", prize="shirt", name="Otis", gender="boy", parent="father", trait="lively"),
    StoryParams(activity="whirl", prize="scarf", name="Ruby", gender="girl", parent="mother", trait="curious"),
    StoryParams(activity="kite", prize="boots", name="Hank", gender="boy", parent="father", trait="stubborn"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} is not at risk in {activity.gerund}.)"
    if select_gear(activity, prize) is None:
        return f"(No story: no gear in this world can safely handle {activity.gerund} with {prize.label}.)"
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld with a flashback and an inner-pocket trick.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    choices = [c for c in combos
               if (args.activity is None or c[0] == args.activity)
               and (args.prize is None or c[1] == args.prize)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    act_id, prize_id = rng.choice(sorted(choices))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(activity=act_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,Kind), needs(A,Kind), covers(G,R), worn_on(P,R), splashes(A,R).
valid(A,P) :- prize_at_risk(A,P), protects(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("needs", aid, "wind" if aid in {"kite", "whirl"} else "dust"))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/2.\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
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
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
