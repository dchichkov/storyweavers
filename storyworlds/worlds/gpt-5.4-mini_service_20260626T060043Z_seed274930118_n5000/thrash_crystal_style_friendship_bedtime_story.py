#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thrash_crystal_style_friendship_bedtime_story.py
================================================================================================

A tiny bedtime-story world about friendship, a thrashy bedtime moment, and a
shimmering crystal keepsake.

Seed words:
- thrash
- crystal
- style

Story shape:
- a sleepy child and a friend
- a treasured crystal item in a gentle bedtime style
- a warning about thrashing
- a soft compromise
- a calm ending image proving the change

The world is intentionally small and constraint-checked: only a few plausible
stories are generated, and invalid explicit choices raise StoryError.
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
        for k in ["scratch", "lost", "rumple", "sleepiness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "care", "worry", "calm", "friendship", "defiance", "gratitude", "comfort"]:
            self.memes.setdefault(k, 0.0)

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
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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


def make_defaults() -> tuple[dict[str, Setting], dict[str, Activity], dict[str, Prize], list[Gear]]:
    settings = {
        "bedroom": Setting(place="the bedroom", indoors=True, affords={"thrash", "read"}),
        "nursery": Setting(place="the nursery", indoors=True, affords={"thrash", "sing"}),
        "moonroom": Setting(place="the moonlit room", indoors=True, affords={"thrash", "dream"}),
    }
    activities = {
        "thrash": Activity(
            id="thrash",
            verb="thrash on the bed",
            gerund="thrashing on the bed",
            rush="fling around on the blankets",
            risk="scratch",
            zone={"hands", "arms", "torso"},
            keyword="thrash",
            tags={"thrash", "bedtime"},
        ),
        "read": Activity(
            id="read",
            verb="read a story",
            gerund="reading under the covers",
            rush="turn the page too fast",
            risk="rumple",
            zone={"hands"},
            keyword="style",
            tags={"bedtime"},
        ),
        "sing": Activity(
            id="sing",
            verb="sing a sleepy song",
            gerund="singing softly",
            rush="bounce on the pillow",
            risk="rumple",
            zone={"torso"},
            keyword="style",
            tags={"bedtime"},
        ),
        "dream": Activity(
            id="dream",
            verb="dream by the window",
            gerund="dreaming quietly",
            rush="toss in sleep",
            risk="scratch",
            zone={"hands", "torso"},
            keyword="crystal",
            tags={"bedtime"},
        ),
    }
    prizes = {
        "bracelet": Prize(
            label="bracelet",
            phrase="a tiny crystal bracelet",
            type="bracelet",
            region="wrists",
        ),
        "pendant": Prize(
            label="pendant",
            phrase="a crystal pendant on a soft chain",
            type="pendant",
            region="torso",
        ),
        "hairpin": Prize(
            label="hairpin",
            phrase="a crystal hairpin",
            type="hairpin",
            region="hair",
            genders={"girl"},
        ),
    }
    gear = [
        Gear(
            id="pouch",
            label="a velvet pouch",
            covers={"wrists", "torso", "hair"},
            guards={"scratch"},
            prep="tuck the crystal treasure into a velvet pouch first",
            tail="placed the treasure in the velvet pouch beside the pillow",
        ),
        Gear(
            id="ribbon-wrap",
            label="a soft ribbon wrap",
            covers={"wrists"},
            guards={"scratch"},
            prep="wrap the bracelet in a soft ribbon first",
            tail="tied the bracelet safely in a soft ribbon wrap",
        ),
        Gear(
            id="hair-cap",
            label="a sleepy hair cap",
            covers={"hair"},
            guards={"scratch"},
            prep="put on a sleepy hair cap first",
            tail="pulled the sleepy hair cap down over the hairpin",
            plural=False,
        ),
    ]
    return settings, activities, prizes, gear


SETTINGS, ACTIVITIES, PRIZES, GEAR = make_defaults()

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Rose", "June"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Finn", "Max", "Noah"]
FRIEND_NAMES = ["Pip", "Bea", "Toby", "Milo", "Ada", "Sami"]
TRAITS = ["gentle", "curious", "sleepy", "kind", "shy", "brave"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.risk in g.guards and prize.region in g.covers:
            return g
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


def bedtime_detail(setting: Setting) -> str:
    if setting.place == "the bedroom":
        return "The lamp glowed softly, and the blanket made a little hill on the bed."
    if setting.place == "the nursery":
        return "The room was quiet except for a tiny nightlight and the hush of blankets."
    return "Moonlight rested on the floor like a silver ribbon, and the room felt ready for sleep."


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.meters.keys() if False) if False else hero.type} "
        f"who liked bedtime best when a friend was near."
    )
    world.say(
        f"{hero.id} and {friend.id} shared a gentle style of play: soft voices, warm blankets, and slow smiles."
    )


def introduce_clean(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"Each night, {hero.id} loved the shimmer of {hero.pronoun('possessive')} {prize.label} "
        f"because {friend.id} had called it a crystal treasure."
    )


def start_scene(world: World, activity: Activity) -> None:
    world.say(
        f"One sleepy evening, {bedtime_detail(world.setting)} "
        f"{activity.gerund.capitalize()} felt fun, but it was not a very careful style."
    )


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"If you {activity.verb}, you may scrape your {prize.label}," {parent.pronoun("subject").capitalize() if parent.type else "She"} said softly. '
        f'"That crystal treasure is too pretty for rough thrashing."'
    )


def friend_help(world: World, friend: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{friend.id} scooted closer and smiled. "
        f'"We can keep the thrash out of the treasure," {friend.id} said. '
        f'"Let’s make a sleepy style instead."'
    )
    world.say(
        f"{hero.id} liked that idea, because being kind to a friend felt even nicer than flopping around."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    ent.worn_by = hero.id
    world.say(
        f"{parent.id} smiled and suggested a kinder plan: {gear.prep}. "
        f"Then {hero.id} could still enjoy the bedtime moment without hurting the crystal thing."
    )
    return gear


def accept(world: World, hero: Entity, friend: Entity, prize: Entity, gear: Gear, activity: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["calm"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["calm"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} nodded, tucked the treasure safely away, and laughed with {friend.id}. "
        f"They chose a dreamy style instead of a wild thrash."
    )
    world.say(
        f"Before long, {hero.id} was {activity.gerund}, {gear.tail}, and the little room felt peaceful again."
    )
    world.say(
        f"{hero.id} fell asleep smiling, with {friend.id} nearby and the crystal treasure safe and shining."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, friend_name: str,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="treasure", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    introduce(world, hero, friend)
    introduce_clean(world, hero, friend, prize)
    world.para()
    start_scene(world, activity)
    warning(world, parent, hero, activity, prize)
    friend_help(world, friend, hero, activity)
    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear is not None:
        accept(world, hero, friend, prize, gear, activity)

    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a bedtime story about friendship that includes the word "{activity.keyword}" and the word "crystal".',
        f"Tell a soft story where {hero.id} wants to {activity.verb}, but {friend.id} helps keep {hero.id}'s {prize.label} safe.",
        f"Write a child-friendly story in a gentle bedtime style about a sleepy child, a friend, and a shiny crystal treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} choose a safer bedtime style?",
            answer=f"{friend.id} helped {hero.id} choose a gentler plan.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"The parent worried because thrashing could scratch the crystal {prize.label}.",
        ),
        QAItem(
            question=f"What kept the {prize.label} safe?",
            answer=f"{gear.label if gear else 'The soft plan'} kept the crystal {prize.label} safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} calm, {friend.id} nearby, and the crystal treasure safe and shining.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does crystal mean in a bedtime story?",
            answer="Crystal means something clear, bright, and sparkly, like a little treasure that glints in the lamp light.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and feel happy to play together.",
        ),
        QAItem(
            question="What is a bedtime style?",
            answer="A bedtime style is a calm way of acting before sleep, with soft voices, gentle movements, and cozy choices.",
        ),
        QAItem(
            question="What does thrash mean?",
            answer="Thrash means to move around hard and quickly, like flopping or kicking without being careful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
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
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about friendship, crystal, and a thrashy moment.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
            raise StoryError("No story: that crystal treasure would not have a sensible soft fix in this bedtime world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.friend,
        params.parent,
    )
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
    StoryParams(place="bedroom", activity="thrash", prize="bracelet", name="Mia", friend="Pip", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="nursery", activity="thrash", prize="pendant", name="Ben", friend="Bea", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="moonroom", activity="thrash", prize="hairpin", name="Luna", friend="Ada", gender="girl", parent="mother", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:8} {prize:10} [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
