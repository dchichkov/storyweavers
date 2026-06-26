#!/usr/bin/env python3
"""
A small fable-like suspense storyworld.

Theme:
- A careful little hero named Max faces a tense moment in a quiet place.
- The world models risk, fear, clues, and a wise turn toward patience.
- The ending proves what changed in both the physical scene and the mood.

This script follows the Storyweavers contract:
- standalone stdlib storyworld file
- StoryParams, registries, parser, resolve/generate/emit/main
- eager results import
- lazy ASP import only inside ASP helpers
- Python reasonableness gate plus inline ASP twin
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "hen"}
        male = {"boy", "father", "dad", "man", "king", "rooster", "rabbit", "mouse", "fox", "owl", "deer", "turtle"}
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
    indoor: bool = False
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
    weather: str
    keyword: str = ""


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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "wood": Setting(place="the wood", indoor=False, affords={"night_walk", "river_cross", "berry_run"}),
    "bridge": Setting(place="the old bridge", indoor=False, affords={"river_cross"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"berry_run", "night_walk"}),
    "hill": Setting(place="the hill", indoor=False, affords={"night_walk"}),
}

ACTIVITIES = {
    "night_walk": Activity(
        id="night_walk",
        verb="walk home at dusk",
        gerund="walking home at dusk",
        rush="run through the dark path",
        mess="fear",
        soil="full of fear",
        zone={"mind"},
        weather="dusk",
        keyword="shadow",
    ),
    "river_cross": Activity(
        id="river_cross",
        verb="cross the river",
        gerund="crossing the river",
        rush="dash onto the bridge",
        mess="wet",
        soil="wet and shivery",
        zone={"feet", "legs"},
        weather="misty",
        keyword="river",
    ),
    "berry_run": Activity(
        id="berry_run",
        verb="pick berries",
        gerund="picking berries",
        rush="rush to the berry patch",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs"},
        weather="clear",
        keyword="berries",
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little lantern with a warm flame",
        type="lantern",
        region="hands",
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a dark cloak",
        type="cloak",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="little boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "basket": Prize(
        label="basket",
        phrase="a small berry basket",
        type="basket",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="lantern",
        label="a lantern",
        covers={"mind"},
        guards={"fear"},
        prep="light the lantern first",
        tail="lit the lantern and took the careful path",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"wet", "muddy"},
        prep="put on rubber boots first",
        tail="buttoned up the boots and stepped more safely",
        plural=True,
    ),
    Gear(
        id="rope",
        label="a sturdy rope",
        covers={"hands"},
        guards={"wet"},
        prep="tie a sturdy rope to the post first",
        tail="held the rope and crossed one step at a time",
    ),
]

NAMES = ["Max", "Milo", "Mina", "Nora", "Toby", "Luna"]
HELPERS = ["owl", "turtle", "deer", "rabbit", "fox"]
HELPER_TYPES = {"owl", "turtle", "deer", "rabbit", "fox"}
TRAITS = ["careful", "curious", "patient", "brave", "gentle"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or (activity.id == "night_walk" and prize.label == "lantern")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    if activity.id == "night_walk":
        return GEAR[0]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Max's suspenseful fable storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("No honest fable can be told with that activity and prize.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit that gender in this little world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    if narrate and activity.id == "night_walk":
        world.say("The path grew dim, and every leaf seemed to keep a secret.")
    if narrate and activity.id == "river_cross":
        world.say("Below the bridge, the water moved fast and made the silence feel bigger.")
    if narrate and activity.id == "berry_run":
        world.say("The berry patch looked ordinary, yet the mud hid soft, slippery spots.")


def predict(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("fear", 0) >= THRESHOLD), "worry": sim.get(hero.id).memes.get("worry", 0.0)}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"worry": 0.0, "hope": 0.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural,
        meters={}, memes={},
    ))

    world.say(f"Once, {hero.id} was a small {hero.type} who liked quiet paths and careful thinking.")
    world.say(f"One dusk, {hero.id} carried {hero.pronoun('possessive')} {prize.label} and longed to {activity.verb}.")
    world.say(f"The air near {setting.place} felt still, as if it were holding its breath.")

    world.para()
    _do_activity(world, hero, activity)
    pred = predict(world, hero, activity, prize.id)
    if activity.id == "night_walk":
        world.say(f"{hero.id} heard a soft snap in the dark and froze.")
    elif activity.id == "river_cross":
        world.say(f"A swirl of water slapped the stones, and {hero.id} hesitated at the edge.")
    else:
        world.say(f"A sudden slip of mud sent a tiny shiver through {hero.id}'s paws.")
    world.say(f"{helper.id.capitalize()} saw the worry and said, \"Slow steps are still steps.\"")
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["hope"] += 1
    world.say(f"{hero.id} wanted to rush, but the little warning made {hero.pronoun('object')} think twice.")

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("This world only tells fables with a clear, wise turn.")
    if gear.id == "lantern":
        world.say(f"Then {helper.id} lifted a lantern and lit the path.")
    elif gear.id == "boots":
        world.say(f"Then {helper.id} pointed to some rubber boots by the door.")
    else:
        world.say(f"Then {helper.id} tied a rope where the crossing began.")
    world.say(f"{hero.id} listened, and {gear.prep}.")
    hero.memes["fear"] = 0.0
    hero.memes["calm"] = 1.0
    prize.meters["safe"] = 1.0
    world.say(f"At last, {gear.tail}, and the danger lost its teeth.")

    if activity.id == "night_walk":
        world.say(f"{hero.id} reached home with the lantern glowing like a little star.")
    elif activity.id == "river_cross":
        world.say(f"{hero.id} crossed the river without a splash on {hero.pronoun('possessive')} prize.")
    else:
        world.say(f"{hero.id} picked the berries carefully, and the basket stayed neat.")

    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear, predicted=pred, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short fable for young children about {hero.id} who wants to {act.verb} and learns to be careful.',
        f'Tell a suspenseful but gentle story where a {hero.type} named {hero.id} worries about {prize.phrase} while {act.keyword} makes the scene tense.',
        f'Write a simple moral story that includes the word "{act.keyword}" and ends with a safe, wise choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small {hero.type} who learns to stay calm when things feel tense.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the danger felt real?",
            answer=f"{hero.id} wanted to {act.verb}, but the moment grew suspenseful because the world felt uncertain.",
        ),
        QAItem(
            question=f"Who helped {hero.id} find a safer way?",
            answer=f"{helper.id.capitalize()} helped {hero.id} choose a careful plan so {hero.pronoun('possessive')} {prize.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something might go wrong, so you keep wondering what will happen next.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals or gentle lessons, that teaches a simple moral.",
        ),
    ]
    if world.facts["activity"].id == "night_walk":
        out.append(QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light in the dark so people can see the path more clearly.",
        ))
    if world.facts["activity"].id == "river_cross":
        out.append(QAItem(
            question="Why do people use boots near wet ground?",
            answer="Boots help keep feet dry and make it easier to walk through wet places.",
        ))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood", activity="night_walk", prize="lantern", name="Max", gender="boy", helper="owl"),
    StoryParams(place="bridge", activity="river_cross", prize="boots", name="Max", gender="boy", helper="turtle"),
    StoryParams(place="meadow", activity="berry_run", prize="basket", name="Max", gender="boy", helper="deer"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), guards(G,M), mess_of(A,M).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


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
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.helper)
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
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
