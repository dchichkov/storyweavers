#!/usr/bin/env python3
"""
storyworlds/worlds/group_jewish_destructor_sharing_rhyme_twist_animal.py
========================================================================

A small animal-story world about a group of animals, a sharing problem,
a rhyme helper, and a twist that changes what the destroyer actually wants.

Seed idea:
- A little animal group is preparing for a Jewish celebration.
- One animal called the destructor keeps ruining the shared items.
- The group discovers a rhyme that helps them share safely.
- A twist reveals the destructor was not trying to be mean; it was trying to
  join the group and wanted its own turn.

The world is intentionally small, classical, and constraint-checked:
- typed entities with meters and memes
- state-driven prose, not a template swap
- explicit invalid combinations raise StoryError
- ASP facts/rules mirror the Python reasonableness gate
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "synagogue_yard": Setting(place="the synagogue yard", indoor=False, affords={"sharing", "rhyme", "twist"}),
    "apple_tree": Setting(place="the apple tree", indoor=False, affords={"sharing", "rhyme", "twist"}),
    "barn_corner": Setting(place="the barn corner", indoor=False, affords={"sharing", "rhyme", "twist"}),
}

ACTIVITIES = {
    "sharing": Activity(
        id="sharing",
        verb="share the basket",
        gerund="sharing the basket",
        rush="grab the basket",
        mess="scattered",
        soil="scattered everywhere",
        zone={"ground"},
        weather="sunny",
        keyword="share",
        tags={"share", "sharing"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="say the rhyme",
        gerund="saying the rhyme",
        rush="blurt out the next line",
        mess="tangled",
        soil="tangled up",
        zone={"voice"},
        weather="sunny",
        keyword="rhyme",
        tags={"rhyme", "song"},
    ),
    "twist": Activity(
        id="twist",
        verb="try the twist step",
        gerund="twisting in a funny step",
        rush="spin too fast",
        mess="knocked",
        soil="knocked over",
        zone={"ground", "voice"},
        weather="sunny",
        keyword="twist",
        tags={"twist", "turn"},
    ),
}

PRIZES = {
    "cookies": Prize(label="cookies", phrase="small honey cookies", type="cookies", region="ground", plural=True),
    "books": Prize(label="books", phrase="little prayer books", type="books", region="ground", plural=True),
    "bell": Prize(label="bell", phrase="a shiny hand bell", type="bell", region="voice"),
}

GEAR = [
    Gear(
        id="basket_lid",
        label="a basket lid",
        covers={"ground"},
        guards={"scattered", "knocked"},
        prep="put the basket lid on first",
        tail="closed the basket with the lid",
    ),
    Gear(
        id="gentle_chime",
        label="a gentle chime card",
        covers={"voice"},
        guards={"tangled"},
        prep="use a gentle chime card",
        tail="held the chime card up",
    ),
    Gear(
        id="soft_ring",
        label="a soft ring game",
        covers={"ground", "voice"},
        guards={"scattered", "tangled", "knocked"},
        prep="play with the soft ring game first",
        tail="played the soft ring game",
    ),
]

GIRL_NAMES = ["Miri", "Leah", "Nina", "Tali", "Ava"]
BOY_NAMES = ["Noam", "Eli", "Ari", "Sam", "Uri"]
ANIMAL_TYPES = ["rabbit", "mouse", "fox", "cat", "goat", "duck"]
TRAITS = ["curious", "gentle", "busy", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    species: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
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
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
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
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _activity_delight(activity: Activity) -> str:
    return {
        "sharing": "the basket looked bigger when everyone helped",
        "rhyme": "the rhyme bounced like a happy pebble",
        "twist": "the twist step felt silly and light",
    }.get(activity.id, "the moment felt bright")


def _predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters[activity.mess] = 1
    _propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return bool(prize.meters.get("dirty", 0) >= THRESHOLD or prize.meters.get(activity.mess, 0) >= THRESHOLD)


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        # no cascading rules beyond the simple conflict markers, but keep shape
        for e in world.characters():
            if e.memes.get("conflict", 0) >= THRESHOLD and ("conflict", e.id) not in world.fired:
                world.fired.add(("conflict", e.id))
                changed = True
                out.append(f"{e.id} felt upset.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    _propagate(world)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, species: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=species, traits=["little", trait, "animal"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
    ))
    destructor = world.add(Entity(
        id="destructor",
        kind="character",
        type=random.choice(ANIMAL_TYPES),
        label="the destructor",
        traits=["mischievous", "loud"],
    ))
    world.facts.update(hero=hero, parent=parent, prize=prize, destructor=destructor, activity=activity)

    # Setup
    world.say(f"{hero.id} was a little {trait} {species} who lived with a warm little group of friends.")
    world.say(f"The group liked to sing, share snacks, and keep things fair.")
    world.say(f"That morning, {hero.id}'s {parent_type} brought out {prize.phrase}.")
    world.say(f"{hero.id} loved the {prize.label}, and the whole group wanted to use it together.")

    # Conflict
    world.para()
    world.say(f"Later, at {setting.place}, everyone gathered for {activity.gerund}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the {prize.label} could get {activity.soil}.")
    if _predict_mess(world, hero, activity, "prize"):
        world.say(f"\"Careful,\" said {parent.label}, because the {prize.label} would get ruined if the group rushed.")
    world.say(f"Then the destructor darted in and tried to {activity.rush}.")
    world.say(f"The basket went {activity.soil} and the group gasped.")
    destructor.memes["trouble"] = destructor.memes.get("trouble", 0) + 1

    # Turn
    world.para()
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No reasonable sharing fix exists for this activity and prize.")
    if not prize_at_risk(activity, prize_cfg):
        raise StoryError("The prize is not actually at risk, so the story has no honest problem.")
    world.say(f"Then the parent held up {gear.label} and said, \"Let's slow down and share with a rhyme.\"")
    world.say(f'They sang, "Take a turn, then let it earn; pass it round and keep it found."')
    world.say(f"{gear.prep.capitalize()}, and the group took turns carefully.")
    world.say(f"The rhyme helped everyone wait, and the {prize.label} stayed safe.")

    # Twist / resolution
    world.para()
    world.say(f"At last, the destructor lowered its ears and squeaked that it did not want to ruin anything.")
    world.say(f"It only wanted a turn in the group and to hear the rhyme again.")
    world.say(f"The group smiled, shared the last turn, and let the destructor join in with a tiny chime.")
    world.say(f"In the end, {hero.id} was {activity.gerund}, {prize.label} was still nice, and the whole group was laughing together.")

    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "share": [("What does it mean to share?", "To share means to let other people or animals use something too, one turn at a time.")],
    "sharing": [("Why do groups share?", "Groups share so everyone gets a turn and nobody is left out.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like cat and hat.")],
    "twist": [("What is a twist?", "A twist is a turning motion, often with a playful spin or bend.")],
    "animal": [("What is an animal?", "An animal is a living creature like a cat, rabbit, dog, bird, or fox.")],
    "jewish": [("What does Jewish mean?", "Jewish refers to the Jewish people, their faith, and their traditions.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f"Write an animal story about a group, a {prize.label}, and a clever rhyme that helps everyone share.",
        f"Tell a gentle story where {hero.id} and a little group face a destructor, then solve the problem with {activity.keyword} and sharing.",
        f"Write a short story for young children that includes the words group, jewish, destructor, rhyme, and twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    destructor = f["destructor"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, a little {hero.type}, and the group around {hero.id}.",
        ),
        QAItem(
            question=f"Why did the parent worry when everyone wanted to {activity.verb}?",
            answer=f"The parent worried because the {prize.label} could get {activity.soil} if the group rushed or grabbed it too fast.",
        ),
        QAItem(
            question=f"What did the destructor really want?",
            answer=f"The destructor did not really want to break things; it wanted to join the group and get a turn.",
        ),
        QAItem(
            question=f"How did the group keep the {prize.label} safe?",
            answer=f"They used {gear.label} and sang a rhyme that helped everyone take turns and share carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the destructor was included in the group, the {prize.label} stayed safe, and everyone was laughing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("animal")
    tags.add("jewish")
    out: list[QAItem] = []
    for key in ["animal", "share", "sharing", "rhyme", "twist", "jewish"]:
        if key in tags or key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(key, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="synagogue_yard", activity="sharing", prize="cookies", name="Miri", species="rabbit", parent="mother", trait="gentle"),
    StoryParams(place="apple_tree", activity="rhyme", prize="bell", name="Noam", species="cat", parent="father", trait="curious"),
    StoryParams(place="barn_corner", activity="twist", prize="books", name="Leah", species="fox", parent="mother", trait="patient"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the {prize.label} is not honestly at risk during {activity.gerund}, so there is no real problem to solve.)"


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.activity is None or c[1] == args.activity
              if args.prize is None or c[2] == args.prize]
    # The above list-comprehension with stacked ifs isn't valid Python syntax, so we won't use it.
    raise StoryError("internal selection error")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about sharing, rhyme, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=ANIMAL_TYPES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    species = args.species or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if species in {"rabbit"} else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, species=species, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.species, params.parent, params.trait)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
