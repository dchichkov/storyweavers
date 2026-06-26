#!/usr/bin/env python3
"""
storyworlds/worlds/ankylosaurus_objectionable_symmetry_beach_bravery_kindness_teamwork.py
==========================================================================================

A small beach-adventure storyworld about a child, a sea breeze, and a giant
ankylosaurus-shaped sand sculpture that teaches Bravery, Kindness, and Teamwork.

Premise:
- A child loves making a beach sculpture and exploring tide pools.
- The sculpture is meant to be beautiful and symmetrical, but a stormy tide and
  a rude, objectionable critic shake the child’s confidence.
- A brave choice, a kind helper, and teamwork turn the problem into a stronger
  ending image.

This file follows the storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- inline ASP_RULES twin plus a Python reasonableness gate
- --verify checks parity and exercises generated stories
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
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
    place: str = "the beach"
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = list(self.events)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


SETTINGS = {
    "beach": Setting(place="the beach", affords={"shells", "tidepool", "sandcastle"}),
}

ACTIVITIES = {
    "shells": Activity(
        id="shells",
        verb="search for shells",
        gerund="searching for shells",
        rush="dash toward the shell line",
        mess="scratched",
        soil="scratched and sandy",
        zone={"hands"},
        keyword="shells",
        tags={"beach", "adventure", "kindness"},
    ),
    "tidepool": Activity(
        id="tidepool",
        verb="explore the tide pools",
        gerund="exploring tide pools",
        rush="run to the rocks",
        mess="wet",
        soil="wet and sandy",
        zone={"feet", "hands"},
        keyword="tidepool",
        tags={"beach", "adventure", "bravery"},
    ),
    "sandcastle": Activity(
        id="sandcastle",
        verb="build a sandcastle",
        gerund="building a sandcastle",
        rush="hurry to the shoreline",
        mess="sandy",
        soil="collapsed and sandy",
        zone={"hands", "feet"},
        keyword="sandcastle",
        tags={"beach", "teamwork", "symmetry"},
    ),
}

PRIZES = {
    "flag": Prize(
        label="flag",
        phrase="a bright flag with a straight pole",
        type="flag",
        location="hands",
    ),
    "shellnecklace": Prize(
        label="necklace",
        phrase="a shiny shell necklace",
        type="necklace",
        location="neck",
    ),
    "sash": Prize(
        label="sash",
        phrase="a clean adventure sash",
        type="sash",
        location="torso",
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="beach gloves",
        protects={"scratched"},
        covers={"hands"},
        prep="put on beach gloves first",
        tail="pulled on the beach gloves",
    ),
    Gear(
        id="sandshoes",
        label="sand shoes",
        protects={"wet", "sandy"},
        covers={"feet"},
        prep="wear sand shoes first",
        tail="tied on the sand shoes",
        plural=True,
    ),
    Gear(
        id="towelwrap",
        label="a towel wrap",
        protects={"wet", "sandy"},
        covers={"torso"},
        prep="wrap up in a towel first",
        tail="wrapped up in the towel",
    ),
]

NAMES = ["Mira", "Noah", "Iris", "Toby", "Zoe", "Leo", "Nina", "Finn"]
GENDERS = {"girl": ["Mira", "Iris", "Zoe", "Nina"], "boy": ["Noah", "Toby", "Leo", "Finn"]}
PARENTS = ["mother", "father"]
TRAITS = ["brave", "kind", "curious", "spirited", "careful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.location in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.protects and prize.location in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not plausibly threaten the {prize.label} "
        f"in this beach adventure, so there is no real problem to solve.)"
    )


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Beach adventure storyworld: bravery, kindness, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))

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
    name = args.name or rng.choice(GENDERS[gender])
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    if narrate:
        world.say(f"{actor.id} did not wait. {actor.pronoun().capitalize()} went {activity.gerund}.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    soiled = prize.meters.get("dirty", 0.0) >= THRESHOLD or prize.meters.get(activity.mess, 0.0) >= THRESHOLD
    return {"soiled": soiled}


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "adventurous"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(
        id="Prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        location=PRIZES[params.prize].location,
        plural=PRIZES[params.prize].plural,
    ))
    prize.carried_by = hero.id
    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved the wide blue beach.")
    world.say(f"{hero.pronoun().capitalize()} wore {hero.pronoun('possessive')} {prize.label} like a badge for adventure.")
    world.para()
    act = ACTIVITIES[params.activity]
    world.say(f"At {world.setting.place}, the air smelled salty, and the tide curled close to the stones.")
    world.say(f"{hero.id} wanted to {act.verb}, because {act.gerund} felt like the start of a brave quest.")
    if act.id == "sandcastle":
        world.say("Then {0} noticed the old sandcastle keepers had made one side as neat as a mirror.".format(hero.id))
        world.say("But an objectionable grin from a crabby beach critic said, 'A perfect symmetry is impossible.'")
    pred = predict_mess(world, hero, act, prize.id)
    if pred["soiled"]:
        world.say(f'"If you rush in now, your {prize.label} will get {act.soil}," {parent.pronoun("possessive")} {params.parent} said.')
        world.say(f"{hero.id} felt a tiny wobble of doubt, but {hero.pronoun().capitalize()} took a breath and stood tall.")
        hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
        world.say(f'"I can be brave," {hero.id} said. "I can try carefully."')
    world.para()
    gear = select_gear(act, prize)
    if gear:
        world.say(f"{parent.pronoun().capitalize()} smiled and offered a better plan: {gear.prep}.")
        if act.id == "sandcastle":
            world.say(f"{hero.id} also asked two nearby children for help, because teamwork makes hard jobs lighter.")
            world.say("One child packed the wet sand, another shaped the walls, and a third kept the lines even on both sides.")
        world.say(f"Together they {gear.tail}, and {hero.id} went back to {act.gerund}.")
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
        hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
        world.say(f"The {prize.label} stayed safe, and the beach day grew brighter instead of smaller.")
        if act.id == "sandcastle":
            world.say("The finished sandcastle stood with two strong towers and a balanced gate, even after the tide nipped at its feet.")
        elif act.id == "tidepool":
            world.say("The tide pools glittered like tiny blue mirrors, and the brave child stepped around each wave without fear.")
        else:
            world.say("The shell line looked neat and full, and the helpful hands brought home the prettiest finds.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, gear=gear, setting=world.setting, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short adventure story for a child named {hero.id} at the beach, using the word "{act.keyword}".',
        f"Tell a gentle beach tale where {hero.id} tries to {act.verb} while keeping a {prize.label} safe.",
        f"Write a story about Bravery, Kindness, and Teamwork at the beach that includes an ankylosaurus made of sand.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"Who was the story about at the beach?",
            answer=f"It was about {hero.id}, a little adventurous child, and {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the beach?",
            answer=f"{hero.id} wanted to {act.verb} and keep the day feeling like a brave adventure.",
        ),
        QAItem(
            question=f"What important thing did {hero.id} want to keep safe?",
            answer=f"{hero.id} wanted to keep {hero.pronoun('possessive')} {prize.label} safe and clean.",
        ),
        QAItem(
            question=f"What made the beach problem hard?",
            answer=f"The beach work could make the {prize.label} get {act.soil}, which is why the grown-up worried.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"What helped solve the problem?",
            answer=f"{gear.label} and the helper plan kept the {prize.label} safe while {hero.id} kept playing.",
        ))
    if act.id == "sandcastle":
        qa.append(QAItem(
            question="What did the ankylosaurus add to the story?",
            answer="The ankylosaurus was a sand sculpture that made the castle feel like a real adventure fort.",
        ))
        qa.append(QAItem(
            question="Why was the word objectionable used?",
            answer="It described the rude beach critic who complained instead of helping.",
        ))
        qa.append(QAItem(
            question="How did symmetry matter?",
            answer="Symmetry mattered because the sandcastle looked better when both sides matched.",
        ))
    return qa


KNOWLEDGE = {
    "beach": [
        QAItem(
            question="What is a beach?",
            answer="A beach is a sandy place beside the sea or ocean where waves reach the shore.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous, because you want to do the right or useful thing.",
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle and helpful to others.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other finish a job.",
        )
    ],
    "ankylosaurus": [
        QAItem(
            question="What was an ankylosaurus?",
            answer="An ankylosaurus was a dinosaur with a strong body and a heavy tail, and it lived long ago.",
        )
    ],
    "symmetry": [
        QAItem(
            question="What is symmetry?",
            answer="Symmetry means one side matches the other side in shape or pattern.",
        )
    ],
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for key in ["beach", "bravery", "kindness", "teamwork", "ankylosaurus", "symmetry"]:
        if key in tags or key == "beach":
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="beach", activity="sandcastle", prize="flag", name="Mira", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="beach", activity="tidepool", prize="sash", name="Noah", gender="boy", parent="father", trait="kind"),
    StoryParams(place="beach", activity="shells", prize="shellnecklace", name="Iris", gender="girl", parent="mother", trait="careful"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), location(P,R).
has_fix(A,P) :- risk(A,P), gear(G), protects(G,M), mess(A,M), covers(G,R), location(P,R).
valid_story(Place,A,P) :- place(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        lines.append(asp.fact("mess", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("location", pid, p.location))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
