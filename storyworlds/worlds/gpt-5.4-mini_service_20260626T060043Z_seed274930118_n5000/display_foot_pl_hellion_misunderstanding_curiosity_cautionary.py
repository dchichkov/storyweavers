#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale misunderstanding about a display,
a foot-pl, and a little hellion of a child whose curiosity outruns caution.

The seed premise:
- A child spots a town display in a square.
- The child misunderstands what the sign means.
- Curiosity causes a near-mishap.
- A cautionary helper turns the trouble into a safe ending.

This script keeps the story grounded in a tiny world model with physical
meters and emotional memes, plus a Python reasonableness gate and an inline
ASP twin for parity checks.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
class Display:
    place: str = "the fairground square"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Exhibit:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


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
    def __init__(self, setting: Display) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for meter, amt in actor.meters.items():
            if amt < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("smudge", item.id, meter)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[meter] = item.meters.get(meter, 0) + 1
                item.meters["smudged"] = item.meters.get("smudged", 0) + 1
                out.append(f"{actor.id.capitalize()} left the {item.label} smudged.")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for thing in world.entities.values():
        if thing.meters.get("smudged", 0) < THRESHOLD or not thing.caretaker:
            continue
        sig = ("alarm", thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(thing.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0) + 1
        out.append(f"That was enough to make {caretaker.label} worry.")
    return out


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("heed", 0) >= THRESHOLD and actor.memes.get("curiosity", 0) >= THRESHOLD:
            sig = ("warning", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["chastened"] = actor.memes.get("chastened", 0) + 1
            out.append("__warning__")
    return out


CAUSAL_RULES = [
    _r_smudge,
    _r_alarm,
    _r_warning,
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
                produced.extend(s for s in sents if s != "__warning__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Exhibit, prize: Exhibit) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Exhibit, prize: Exhibit) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_mess(world: World, actor: Entity, activity: Exhibit, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "smudged": bool(prize.meters.get("smudged", 0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Exhibit, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    propagate(world, narrate=narrate)


def introduction(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type}, a true hellion with curious eyes "
        f"and feet that hardly believed in staying put."
    )


def attraction(world: World, child: Entity, activity: Exhibit) -> None:
    world.say(
        f"{child.pronoun().capitalize()} had a mighty curiosity for {activity.keyword}, "
        f"for the sight of it made the whole day feel larger than a wagon wheel."
    )


def arrive(world: World, child: Entity, helper: Entity, activity: Exhibit) -> None:
    world.say(
        f"One bright day, {child.id} and {child.pronoun('possessive')} {helper.label} went to {world.setting.place}."
    )
    world.say(
        f"At the center stood the display, tall as a fence post and shiny as a new penny."
    )


def misunderstand(world: World, child: Entity, activity: Exhibit, prize: Entity) -> None:
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0) + 1
    world.say(
        f"{child.id} squinted at the sign and thought it meant the {prize.label} was for trying on, "
        f"not just for looking."
    )
    world.say(
        f"So {child.pronoun()} pointed at the display and said, "
        f"\"That foot-pl looks like it wants a brave foot to test it!\""
    )


def warn(world: World, helper: Entity, child: Entity, activity: Exhibit, prize: Entity) -> bool:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["smudged"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"\"Careful now,\" {helper.label} said. "
        f"\"You'll leave that {prize.label} {activity.soil}.\""
    )
    child.memes["heed"] = child.memes.get("heed", 0) + 1
    return True


def curiosity(world: World, child: Entity, activity: Exhibit) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"But curiosity is a big drum in a small chest, and {child.id} marched closer anyway."
    )
    world.say(f"{child.pronoun().capitalize()} tried to {activity.verb},")
    _do_activity(world, child, activity, narrate=True)


def cautionary_hand(world: World, helper: Entity, child: Entity, activity: Exhibit) -> None:
    child.memes["held_back"] = child.memes.get("held_back", 0) + 1
    world.say(
        f"then {helper.label} caught {child.pronoun('possessive')} sleeve and told "
        f"{child.pronoun('object')} a cautionary tale about a clean display turning dusty in a blink."
    )


def compromise(world: World, helper: Entity, child: Entity, activity: Exhibit, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    worn = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        owner=child.id,
        caretaker=helper.id,
    ))
    worn.worn_by = child.id
    if predict_mess(world, child, activity, prize.id)["smudged"]:
        worn.worn_by = None
        del world.entities[worn.id]
        return None
    world.say(
        f"\"How about we {gear.prep} and look with our hands clasped behind our backs?\" "
        f"{helper.label} asked."
    )
    return gear


def resolution(world: World, helper: Entity, child: Entity, activity: Exhibit, prize: Entity, gear: Gear) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["misunderstanding"] = 0
    world.say(
        f"{child.id}'s eyes grew round as a moon. {child.pronoun().capitalize()} nodded, "
        f"hopped back, and listened at last."
    )
    world.say(
        f"Together they {gear.tail}. In the end, the display stayed bright, "
        f"{prize.label} stayed clean, and the whole square seemed to tip its hat."
    )


def tell(setting: Display, activity: Exhibit, prize_cfg: Exhibit,
         child_name: str = "Mabel", child_type: str = "girl",
         helper_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        owner=child.id,
        caretaker=helper.id,
    ))

    introduction(world, child)
    attraction(world, child, activity)
    arrive(world, child, helper, activity)
    misunderstanding(world, child, activity, prize)
    warn(world, helper, child, activity, prize)
    curiosity(world, child, activity)
    world.para()
    cautionary_hand(world, helper, child, activity)
    gear = compromise(world, helper, child, activity, prize)
    if gear:
        resolution(world, helper, child, activity, prize, gear)

    world.facts.update(
        child=child,
        helper=helper,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=setting,
        resolved=gear is not None,
    )
    return world


SETTINGS = {
    "fairground": Display(place="the fairground square", affords={"look", "inspect"}),
    "museum": Display(place="the county museum lobby", indoors=True, affords={"look", "inspect"}),
    "market": Display(place="the old market circle", affords={"look", "inspect"}),
}

ACTIVITIES = {
    "look": Exhibit(
        id="look",
        label="display",
        phrase="a grand display",
        region="hands",
        mess="smudge",
        soil="smudged",
        zone={"hands"},
        keyword="display",
        tags={"display", "curiosity"},
    ),
    "inspect": Exhibit(
        id="inspect",
        label="foot-pl",
        phrase="the foot-pl exhibit",
        region="feet",
        mess="dusty",
        soil="dusty",
        zone={"feet"},
        keyword="foot-pl",
        tags={"foot-pl", "display", "cautionary"},
    ),
}

PRIZES = {
    "banner": Exhibit(
        id="banner",
        label="banner",
        phrase="a stitched blue banner",
        region="hands",
        mess="smudge",
        soil="smudged",
        zone={"hands"},
        keyword="banner",
        tags={"display"},
    ),
    "boots": Exhibit(
        id="boots",
        label="boots",
        phrase="shiny parade boots",
        region="feet",
        mess="dusty",
        soil="dusty",
        zone={"feet"},
        keyword="boots",
        tags={"foot-pl", "cautionary"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"smudge"},
        prep="put on soft gloves first",
        tail="went back and admired the display with gloved hands",
        plural=True,
    ),
    Gear(
        id="slippers",
        label="museum slippers",
        covers={"feet"},
        guards={"dusty"},
        prep="slip on museum slippers first",
        tail="tiptoed back to the foot-pl in museum slippers",
        plural=True,
    ),
]

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Tilly", "June", "Bea"]
BOY_NAMES = ["Hank", "Ollie", "Perry", "Tom", "Jules"]
TRAITS = ["curious", "bold", "stubborn", "bright-eyed"]


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
    "display": [("What is a display?", "A display is something set out where people can look at it, like a showpiece or exhibit.")],
    "foot-pl": [("What does 'foot' mean?", "A foot is the part of your body you stand and walk on.")],
    "cautionary": [("What does caution mean?", "Caution means being careful so you do not make a mistake or get hurt.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn about something new.")],
    "smudge": [("Why can hands make things smudgy?", "Hands can leave prints, dirt, or grease on things that should stay clean.")],
    "dusty": [("What is dust?", "Dust is tiny bits of dirt that can gather on things when they sit still.")],
}

KNOWLEDGE_ORDER = ["display", "foot-pl", "curiosity", "cautionary", "smudge", "dusty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, act, prize = f["child"], f["helper"], f["activity"], f["prize"]
    return [
        f'Write a tall-tale style story for a young child about a curious hellion, a {act.keyword}, and a helpful cautionary lesson.',
        f"Tell a lively story where {child.id} misunderstands a {prize.label} at {world.setting.place} and learns a safer way to watch the {act.label}.",
        f'Write a short story that includes the words "{act.keyword}", "display", and "hellion" and ends with a kind fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prize, act = f["child"], f["helper"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story mostly about at {world.setting.place}?",
            answer=f"The story is mostly about {child.id}, a little {child.type} with a hellion streak, and {helper.label}, who keeps things safe.",
        ),
        QAItem(
            question=f"What did {child.id} misunderstand about the {prize.label}?",
            answer=f"{child.id} thought the {prize.label} could be tried on or touched, but it was only meant to be looked at as part of the display.",
        ),
        QAItem(
            question=f"Why did {helper.label} speak in a cautionary way?",
            answer=f"{helper.label} spoke carefully because {child.id}'s curiosity might have left the {prize.label} {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help at the end?",
                answer=f"{gear.label} kept the trouble from spreading, so {child.id} could keep looking without ruining the {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.update(f["prize"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fairground", activity="look", prize="banner", name="Mabel", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="museum", activity="inspect", prize="boots", name="Hank", gender="boy", parent="father", trait="bold"),
]


def explain_rejection(activity: Exhibit, prize: Exhibit) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: the {prize.label} would not be at risk from {activity.keyword}.)"
    return f"(No story: no gear in this world can reasonably protect the {prize.label} from {activity.keyword}.)"


def explain_gender(_: str, __: str) -> str:
    return "(No story: this world does not use gender-restricted prizes.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R).
has_fix(A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P) :- valid(Place,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: display, foot-pl, and a little hellion.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:10} {prize:8}")
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
