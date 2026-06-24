#!/usr/bin/env python3
"""
storyworlds/worlds/negligent_googoo_cautionary_suspense_rhyming_story.py
=======================================================================

A tiny, self-contained storyworld for a rhyming, cautionary suspense tale
built from the seed words "negligent" and "googoo".

Premise:
- A little child loves a risky plaything.
- A careful grown-up notices a danger before it becomes trouble.
- The child nearly rushes ahead, then accepts a safer plan.
- The ending proves the change through the new state of the world.

The world model uses:
- physical meters for mess, breakage, and protective gear
- emotional memes for worry, stubbornness, relief, joy, and caution

The prose leans rhythmic and rhyme-friendly, but the simulation still drives
the story: what gets warned about, what nearly goes wrong, and what the safe
compromise actually changes.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "dirty", "broken", "rattle", "shine"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "stubborn", "relief", "caution", "love", "fear"]:
            self.memes.setdefault(k, 0.0)

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


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
    "nursery": Setting(place="the nursery", indoor=True, affords={"blocks", "paint", "kite"}),
    "yard": Setting(place="the yard", indoor=False, affords={"kite", "bubbles"}),
    "porch": Setting(place="the porch", indoor=False, affords={"bubbles", "paint"}),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly the kite",
        gerund="flying a kite",
        rush="dash for the fence",
        mess="snagged",
        soil="torn and tangled",
        zone={"hands", "head"},
        weather="windy",
        keyword="kite",
        tags={"wind", "kite", "string"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a sign",
        gerund="painting bright signs",
        rush="grab the paint",
        mess="painted",
        soil="spotted with paint",
        zone={"hands", "torso"},
        weather="",
        keyword="paint",
        tags={"paint", "color"},
    ),
    "bubbles": Activity(
        id="bubbles",
        verb="blow bubbles",
        gerund="blowing bubbles",
        rush="run to the bowl",
        mess="wet",
        soil="wet and sticky",
        zone={"hands", "feet"},
        weather="breezy",
        keyword="bubbles",
        tags={"wet", "bubble"},
    ),
    "blocks": Activity(
        id="blocks",
        verb="build a tower",
        gerund="building tall towers",
        rush="reach for the blocks",
        mess="bumped",
        soil="knocked loose",
        zone={"hands"},
        weather="",
        keyword="blocks",
        tags={"blocks", "stack"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean little shirt", "shirt", "torso"),
    "shoes": Prize("shoes", "shiny white shoes", "shoes", "feet", plural=True),
    "hat": Prize("hat", "a soft yellow hat", "hat", "head"),
    "apron": Prize("apron", "a neat blue apron", "apron", "torso"),
}

GEAR = [
    Gear("raincoat", "a raincoat", {"torso"}, {"wet"}, "put on a raincoat", "came back with the raincoat"),
    Gear("gloves", "little gloves", {"hands"}, {"painted", "snagged"}, "pull on little gloves", "came back with the little gloves", True),
    Gear("cap", "a snug cap", {"head"}, {"snagged"}, "put on a snug cap", "came back with the snug cap"),
    Gear("boots", "rain boots", {"feet"}, {"wet"}, "put on rain boots", "came back with the rain boots", True),
]

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Luna"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Finn", "Owen"]
TRAITS = ["curious", "brave", "playful", "tiny", "bouncy"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or (activity.id == "kite" and prize.region == "head")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
        if activity.id == "kite" and prize.region == "head" and "snagged" in gear.guards and "head" in gear.covers:
            return gear
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not touch a {prize.label}, so there is no real warning or fix.)"
    return f"(No story: nothing in the gear shelf can safely cover a {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


def activity_detail(activity: Activity, setting: Setting) -> str:
    if activity.id == "kite":
        return "The wind tugged at the string and made the sky feel awake."
    if activity.id == "paint":
        return "The colors looked bright, but they could smear in a blink."
    if activity.id == "bubbles":
        return "The soap made round, shining little moons."
    return f"{setting.place.capitalize()} was quiet, with room for careful play."


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in list(world.entities.values()):
        if item.owner == actor.id and item.region in world.zone and not item.protective:
            if item.region not in actor.meters:  # harmless
                pass
        if item.owner == actor.id and item.region in world.zone and not world.covered(actor, item.region):
            sig = ("mess", item.id, activity.mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            item.meters[activity.mess] += 1
    if narrate:
        pass


def propagate(world: World) -> None:
    for item in list(world.entities.values()):
        if item.meters["dirty"] >= THRESHOLD and item.caretaker:
            sig = ("work", item.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.get(item.caretaker).memes["worry"] += 1


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait_word', 'child')} who loved rhyme and play.")


def setup_lines(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} {parent.type} watched with a careful eye."
    )
    world.say(f"On a bright day, {parent.id} bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} cherished {hero.pronoun('possessive')} {prize.label}, and wore {prize.it()} with pride.")


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    parent.memes["caution"] += 1
    world.say(
        f'"Be not negligent," {parent.id} said with a sigh, '
        f'"or {hero.pronoun("possessive")} {prize.label} may be {activity.soil}."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} gave a goo-goo grin and tried to {activity.rush}, all quick as a bee.")


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f"Then {parent.id} held {hero.pronoun('possessive')} hand, so the trouble could not be.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[g.id]
        return None
    world.say(
        f"\"Let's take {gear.label} first,\" said {parent.id}. "
        f"\"Then you may {activity.verb}, and keep your {prize.label} clean and free.\""
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id} smiled, soft and slow, and nodded yes to the safer show."
    )
    world.say(
        f"They {gear.tail}, and soon {hero.id} was {activity.gerund}, while {prize.label} stayed neat and bright as snow."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.memes["trait_word"] = trait
    world.weather = activity.weather

    world.say(f"{hero.id} was a little {trait} {hero.type}, a child with a googoo gleam.")
    world.say(f"{hero.id} loved {activity.gerund}, like a tune from a dream.")
    world.say(f"{parent.id} bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} with esteem.")

    world.para()
    world.say(f"At {setting.place}, the wind or the light made a shivery scene.")
    world.say(activity_detail(activity, setting))
    warning(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    grab(world, parent, hero)
    world.para()
    gear = offer(world, parent, hero, activity, prize)
    if gear:
        resolve(world, hero, parent, activity, prize, gear)
    propagate(world)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, resolved=gear is not None, conflict=True)
    return world


KNOWLEDGE = {
    "kite": [("What does a kite do?", "A kite catches the wind and lifts up, pulling on its string as it flies.")],
    "wind": [("What is wind?", "Wind is moving air. It can tug on hair, leaves, and kites.")],
    "paint": [("Why can paint be messy?", "Paint can drip and smear, so it can stain clothes and hands.")],
    "wet": [("What does wet mean?", "Wet means covered with water or another liquid.")],
    "bubble": [("What is a bubble?", "A bubble is a round ball of air or soap that can pop with a tiny puff.")],
    "blocks": [("Why do blocks stack well?", "Blocks have flat sides, so they can sit on top of one another.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a cautionary rhyming story for a little child about "{act.keyword}" and a "{prize.label}".',
        f"Tell a suspenseful, child-friendly rhyme where {hero.id} wants to {act.verb} but {parent.id} worries about the {prize.label}.",
        f'Write a gentle story that includes the word "negligent" and the word "googoo" without sounding scary.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.memes['trait_word']} {hero.type} who wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id}?",
            answer=f"{parent.id} warned {hero.id} because {hero.pronoun('possessive')} {prize.label} could be {act.soil} if the risky play went ahead.",
        ),
        QAItem(
            question=f"What made the ending safer?",
            answer=f"They chose {f['gear'].label} first, so {hero.id} could {act.verb} and the {prize.label} stayed clean.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because the safer plan let the fun happen without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ["kite", "wind", "paint", "wet", "bubble", "blocks", "raincoat", "gloves", "cap", "boots"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
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


def valid_story_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary suspense rhyming storyworld about a child, a risky plaything, and a safer plan.")
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


CURATED = [
    StoryParams(place="yard", activity="kite", prize="hat", name="Luna", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", activity="paint", prize="apron", name="Leo", gender="boy", parent="father", trait="bouncy"),
    StoryParams(place="porch", activity="bubbles", prize="shirt", name="Mia", gender="girl", parent="mother", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = valid_combos()
        stories = valid_story_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
