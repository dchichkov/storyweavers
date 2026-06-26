#!/usr/bin/env python3
"""
A small Tall Tale storyworld about a prairie child, a stubborn trail, and a
twisty bridge of choices.

Seed words and instruments:
- bum
- transfix
- knuckle
- Twist
- Repetition
- Foreshadowing

The world is built around a child who wants to do something grand and risky, a
caretaker who sees the trouble ahead, and a fitting piece of gear that makes the
end possible without ruining the prized object.
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
            self.meters = {"wet": 0.0, "muddy": 0.0, "dusty": 0.0, "scratched": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "stubborn": 0.0, "wonder": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoor: bool
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "muddy", "dusty", "scratched"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                if item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1.0
                out.append(f"{actor.id}'s {item.label} came out {mess}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("wet", 0.0) >= THRESHOLD and item.caretaker:
            sig = ("worry", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            caretaker = world.get(item.caretaker)
            caretaker.memes["worry"] = caretaker.memes.get("worry", 0.0) + 1.0
            out.append(f"That would make more work for {caretaker.label}.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_worry,
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get(activity.mess, 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That place cannot host that stunt.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the air was still as a hatbox, but the fun was not."
    if activity.weather == "stormy":
        return f"The sky was as busy as a fiddler's elbow over {setting.place}."
    if setting.place == "the prairie":
        return "The prairie stretched long and golden, like a blanket somebody forgot to fold."
    return f"{setting.place.capitalize()} stood wide and waiting."


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    hero.memes["wonder"] += 1.0

    world.say(
        f"Once upon a prairie day, {hero.id} was a little {trait} {hero.type} with a "
        f"knuckle-strong grip and a heart full of tumble-wind."
    )
    world.say(
        f"{hero.id} loved to {activity.verb}, and folks said {activity.keyword or activity.id} "
        f"could transfix a crow on a fencepost."
    )
    world.say(
        f"{parent.label} had bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore "
        f"{prize.it()} like a treasure fit for a parade."
    )

    world.para()
    world.say(setting_detail(setting, activity))
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} "
        f"{parent.label} tipped a brow and said, "
        f"\"Mind the {prize.label}, or it'll get {activity.soil}.\""
    )
    world.say(
        f"{hero.id} tried to {activity.rush}, stubborn as a mule's bum on a Sunday wagon."
    )
    if activity.id == "river":
        world.say("And there, as sure as a sunset, the far bank looked twice as far as it was.")

    world.para()
    if prize_at_risk(activity, prize):
        world.say(
            f"The wind did what wind does, and the mud did what mud does, and the warning "
            f"kept ringing in the air like a dinner bell."
        )
        world.say(
            f"Then a shiny black beetle climbed over a fence nail and transfix'd the hero so "
            f"hard that {hero.id} stopped with one boot in the dust."
        )
        world.say(
            f"{parent.label} reached over, gentle as a feather, and said, "
            f"\"We can have a twist in the road without a twist in the rules.\""
        )

        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No sensible gear fits this tale.")
        offer = world.add(
            Entity(
                id=gear.id,
                type="gear",
                label=gear.label,
                owner=hero.id,
                caretaker=parent.id,
                protective=True,
                covers=set(gear.covers),
                plural=gear.plural,
            )
        )
        offer.worn_by = hero.id

        if predict_mess(world, hero, activity, prize.id)["soiled"]:
            del world.entities[offer.id]
            raise StoryError("That gear would not solve the problem.")

        world.say(
            f"So {parent.label} said, \"How about we {gear.prep}?\" and the whole worry "
            f"turned round like a wagon wheel."
        )
        hero.memes["worry"] = 0.0
        hero.memes["joy"] += 1.0
        world.say(
            f"{hero.id} grinned, because the same road that threatened {prize.label} could now "
            f"carry {hero.pronoun('object')} and {prize.it()} both."
        )
        world.say(
            f"They {gear.tail}, and soon {hero.id} was {activity.gerund}, while {prize.label} "
            f"stayed clean as a church hankie."
        )
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, resolved=True)
    else:
        world.say(
            f"That day, the tale turned easy, and the {prize.label} never got into trouble at all."
        )
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=None, resolved=False)

    return world


SETTINGS = {
    "prairie": Setting(place="the prairie", indoor=False, affords={"river", "hill", "barn"}),
    "riverbank": Setting(place="the riverbank", indoor=False, affords={"river", "hill"}),
    "barn": Setting(place="the barn", indoor=True, affords={"barn"}),
}

ACTIVITIES = {
    "river": Activity(
        id="river",
        verb="cross the river on a log",
        gerund="crossing the river",
        rush="dash for the log",
        mess="wet",
        soil="soaked through",
        zone={"feet", "legs"},
        weather="stormy",
        keyword="river",
        tags={"water", "wet", "twist", "foreshadowing"},
    ),
    "hill": Activity(
        id="hill",
        verb="climb the steep hill",
        gerund="climbing hills",
        rush="charge up the slope",
        mess="dusty",
        soil="dusty as a road map",
        zone={"feet", "legs", "torso"},
        weather="windy",
        keyword="hill",
        tags={"dust", "twist", "repetition"},
    ),
    "barn": Activity(
        id="barn",
        verb="haul hay up high",
        gerund="hauling hay",
        rush="swing the bale up",
        mess="scratched",
        soil="scratched and rough",
        zone={"hands", "arms", "torso"},
        weather="",
        keyword="hay",
        tags={"hay", "repetition", "foreshadowing"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="bright red boots", type="boots", region="feet", plural=True),
    "sash": Prize(label="sash", phrase="a silver sash", type="sash", region="torso"),
    "hat": Prize(label="hat", phrase="a fine straw hat", type="hat", region="head"),
}

GEAR = [
    Gear(id="slickers", label="oilcloth slickers", covers={"torso", "legs"}, guards={"wet"}, prep="put on oilcloth slickers", tail="walked back to the log in oilcloth slickers", plural=True),
    Gear(id="workgloves", label="work gloves", covers={"hands"}, guards={"scratched"}, prep="pull on work gloves", tail="went back to the hay with work gloves on", plural=True),
    Gear(id="dustcoat", label="a dust coat", covers={"torso", "legs"}, guards={"dusty"}, prep="button up a dust coat", tail="went back up the hill in a dust coat"),
]

GIRL_NAMES = ["Mabel", "June", "Nell", "Ruby", "Ada"]
BOY_NAMES = ["Hank", "Bo", "Seth", "Jasper", "Tom"]
TRAITS = ["bold", "curious", "stubborn", "cheerful", "lively"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "river": [("What is a river?", "A river is a moving ribbon of water that flows across the land.")],
    "hill": [("What is a hill?", "A hill is a raised place on the ground that you can climb or roll down.")],
    "hay": [("What is hay?", "Hay is dried grass and plants that farmers store for animals to eat.")],
    "wet": [("What does wet mean?", "Wet means something has water on it or in it.")],
    "dust": [("What is dust?", "Dust is tiny dry bits of dirt that can cling to clothes and shoes.")],
    "twist": [("What is a twist?", "A twist is a turn or change that makes a path or a story feel surprising.")],
    "repetition": [("What is repetition?", "Repetition means saying or doing something again to make it stick in your mind.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is a clue that hints something important may happen later.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a Tall Tale for a child named {hero.id} who wants to {act.verb} while wearing {prize.phrase}.',
        f"Tell a story with repetition, foreshadowing, and a twist where {parent.label} worries about {hero.id}'s {prize.label}.",
        f'Create a prairie adventure that uses the words "bum", "transfix", and "knuckle" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} could get {act.soil} if {hero.id} went ahead without protection.",
        ),
        QAItem(
            question=f"What was the twist that helped the story end well?",
            answer=f"The twist was that {parent.label} offered the right gear, so {hero.id} could keep going without ruining {prize.label}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"{gear.label} covered the part of {hero.id} that was at risk, so the bad mess never reached {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["twist", "repetition", "foreshadowing", "river", "hill", "hay", "wet", "dust"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("prairie", "river", "boots", "Mabel", "girl", "mother", "bold"),
    StoryParams("riverbank", "hill", "sash", "Hank", "boy", "father", "curious"),
    StoryParams("prairie", "barn", "boots", "June", "girl", "mother", "lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put {prize.label} in real trouble.)"
    return f"(No story: no gear in this world can sensibly protect {prize.label} from that stunt.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not set up for {gender}; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld: a prairie child, a warning, and a twisty fix.")
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
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
