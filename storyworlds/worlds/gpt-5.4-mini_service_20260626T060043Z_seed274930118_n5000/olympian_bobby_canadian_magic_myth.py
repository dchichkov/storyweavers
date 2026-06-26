#!/usr/bin/env python3
"""
storyworlds/worlds/olympian_bobby_canadian_magic_myth.py
========================================================

A small mythic storyworld about an Olympian Bobby from Canada who meets a
magic trial, makes an honest mistake, and finds a wiser ending by using care,
humility, and help.

The seed words suggest a child-friendly myth:
- olympian
- bobby
- canadian
- magic
- myth

This script models a tiny legend with physical and emotional state. Bobby can
carry a magic charm, face a ceremonial task, spill pride, and then repair the
day with a respectful turn.
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
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shine": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "pride": 0.0, "fear": 0.0, "gratitude": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "goddess"}
        male = {"boy", "father", "man", "king", "god", "olympian"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the mountain hall"
    affords: set[str] = field(default_factory=set)
    sacred: bool = True


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    remedy: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    blessed: bool = False


@dataclass
class Gift:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trial: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.trial = self.trial
        return clone

    def worn_or_carried(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id or e.carries == actor.id]


def _r_tarnish(world: World) -> list[str]:
    out: list[str] = []
    trial = TRIALS[world.trial]
    for actor in world.entities.values():
        if actor.kind != "character" or actor.meters["shine"] < THRESHOLD:
            continue
        for item in world.worn_or_carried(actor):
            if item.kind != "thing":
                continue
            if item.label and item.label == "the story":
                continue
            sig = ("tarnish", actor.id, item.id, trial.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if item.label == "crown":
                item.meters["wear"] += 1
                out.append(f"{actor.id}'s crown dimmed under the strange magic.")
            elif item.label == "laurel wreath":
                item.meters["wear"] += 1
                out.append(f"{actor.id}'s laurel wreath lost a little of its bright green.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.memes["fear"] < THRESHOLD or actor.memes["hope"] < THRESHOLD:
            continue
        sig = ("fear_turns", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["courage"] += 1
        out.append(f"{actor.id} took one slow breath and stood a little straighter.")
    return out


CAUSAL_RULES = [
    _r_tarnish,
    _r_fear,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, trial: Trial) -> str:
    return f"{setting.place.capitalize()} waited in a hush, as if it had been carved for {trial.keyword}."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} Olympian from Canada, and the hills had taught {hero.pronoun('object')} to listen."
    )


def loves(world: World, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the old stories of thunder, snow, and star-bright games."
    )


def receives(world: World, hero: Entity, relic: Entity) -> None:
    relic.owner = hero.id
    world.say(
        f"Before the trial, a keeper placed {hero.pronoun('object')} {relic.phrase}, and {hero.id} held it as carefully as a secret."
    )


def arrives(world: World, hero: Entity, guide: Entity, trial: Trial) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} guide climbed to {world.setting.place} for the {trial.keyword} rite."
    )
    world.say(setting_detail(world.setting, trial))


def wants(world: World, hero: Entity, trial: Trial) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wanted to {trial.verb} at once, because the bells of victory were already ringing in {hero.pronoun('possessive')} mind."
    )


def warns(world: World, guide: Entity, hero: Entity, trial: Trial, relic: Entity) -> bool:
    hero.memes["fear"] += 1
    world.say(
        f'"Careful," {guide.id} said. "The {trial.keyword} magic can {trial.danger}, and even a shining heart can be tested."'
    )
    return True


def rushes(world: World, hero: Entity, trial: Trial) -> None:
    hero.memes["pride"] += 1
    world.say(f"{hero.id} still tried to {trial.rush}, and the air around {hero.pronoun('object')} began to hum.")


def mistake(world: World, hero: Entity, trial: Trial, relic: Entity) -> None:
    hero.meters["shine"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the magic flared, and {hero.pronoun('possessive')} {relic.label} flashed too brightly, as if the sky had noticed {hero.id} was hurrying."
    )


def turn(world: World, guide: Entity, hero: Entity, trial: Trial, relic: Entity, gift: Optional[Entity]) -> None:
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    hero.memes["gratitude"] += 1
    world.say(
        f"{guide.id} smiled and said, \"A true hero does not wrestle magic; a true hero asks it to walk beside them.\""
    )
    if gift is not None:
        world.say(
            f"So {hero.id} accepted the {gift.label}, and the two of them tried again, this time with calm hands."
        )


def resolve(world: World, hero: Entity, trial: Trial, relic: Entity, gift: Optional[Entity]) -> None:
    hero.memes["hope"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"This time, {hero.id} {trial.gerund}, and the {relic.label} stayed bright, not broken."
    )
    if gift is not None:
        world.say(
            f"The {gift.label} kept the wild magic in its place, and {hero.id} finished the rite with a steady heart."
        )
    world.say(
        f"At the end, {hero.id} stood under the open sky of Canada, still an Olympian, but now wiser than pride."
    )


def select_gift(trial: Trial, relic: Relic) -> Optional[Gift]:
    for g in GIFTS:
        if trial.keyword in g.wards and relic.region in g.covers:
            return g
    return None


def predict(world: World, hero: Entity, trial: Trial, relic: Relic) -> dict:
    sim = world.copy()
    _do_trial(sim, sim.get(hero.id), trial, narrate=False)
    return {
        "broken": sim.get(relic.id).meters["wear"] >= THRESHOLD,
        "fear": sim.get(hero.id).memes.get("fear", 0.0),
    }


def _do_trial(world: World, hero: Entity, trial: Trial, narrate: bool = True) -> None:
    if trial.id not in world.setting.affords:
        return
    hero.meters["shine"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, trial: Trial, relic_cfg: Relic,
         hero_name: str = "Bobby", hero_type: str = "olympian",
         hero_traits: Optional[list[str]] = None, guide_name: str = "Aunt Maple") -> World:
    world = World(setting)
    world.trial = trial.id
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "stubborn"])))
    guide = world.add(Entity(id=guide_name, kind="character", type="woman", label="guide"))
    relic = world.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label,
                             phrase=relic_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, guide=guide, relic=relic, trial=trial, setting=setting)

    introduce(world, hero)
    loves(world, hero)
    receives(world, hero, relic)

    world.para()
    arrives(world, hero, guide, trial)
    wants(world, hero, trial)
    warns(world, guide, hero, trial, relic)
    rushes(world, hero, trial)
    mistake(world, hero, trial, relic)

    world.para()
    gift = select_gift(trial, relic)
    if gift is not None:
        gift_ent = world.add(Entity(
            id=gift.id,
            type="thing",
            label=gift.label,
            owner=hero.id,
            plural=gift.plural,
        ))
        gift_ent.carries = hero.id
    else:
        gift_ent = None
    turn(world, guide, hero, trial, relic, gift_ent)
    resolve(world, hero, trial, relic, gift_ent)

    world.facts["gift"] = gift_ent
    return world


SETTINGS = {
    "mountain_hall": Setting(place="the mountain hall", affords={"torch", "river", "snow"}),
    "frozen_lake": Setting(place="the frozen lake", affords={"skate", "river", "snow"}),
    "cedar_grove": Setting(place="the cedar grove", affords={"torch", "wind"}),
    "sky_ring": Setting(place="the sky ring", affords={"torch", "wind", "river"}),
}

TRIALS = {
    "torch": Trial(
        id="torch",
        verb="lift the sun-torch",
        gerund="lifting the sun-torch",
        rush="raise the sun-torch high",
        danger="blind the unready",
        remedy="steady the flame",
        keyword="torch",
        tags={"fire", "light", "magic"},
    ),
    "river": Trial(
        id="river",
        verb="cross the river of singing water",
        gerund="crossing the singing river",
        rush="dash through the water",
        danger="pull the careless under",
        remedy="guide the current",
        keyword="river",
        tags={"water", "magic", "journey"},
    ),
    "snow": Trial(
        id="snow",
        verb="call the snow star down",
        gerund="calling down the snow star",
        rush="reach for the star-snow",
        danger="freeze a hasty hand",
        remedy="warm the vow",
        keyword="snow",
        tags={"snow", "magic", "winter"},
    ),
    "skate": Trial(
        id="skate",
        verb="glide the silver ice",
        gerund="gliding on silver ice",
        rush="rush onto the ice",
        danger="spin a proud heart",
        remedy="balance the step",
        keyword="ice",
        tags={"ice", "magic", "winter"},
    ),
    "wind": Trial(
        id="wind",
        verb="speak to the four winds",
        gerund="speaking to the winds",
        rush="call aloud to the storm",
        danger="scatter careless words",
        remedy="choose the right name",
        keyword="wind",
        tags={"wind", "magic", "sky"},
    ),
}

RELICS = {
    "crown": Relic(label="crown", phrase="a little golden crown", type="crown", region="head"),
    "cloak": Relic(label="cloak", phrase="a blue cloak stitched with stars", type="cloak", region="torso"),
    "boots": Relic(label="boots", phrase="bronze boots with moon clasps", type="boots", region="feet", plural=True),
    "vase": Relic(label="vase", phrase="a round clay vase from the shrine", type="vase", region="hands"),
}

GIFTS = [
    Gift(id="moss_cloth", label="moss cloth", covers={"head", "torso"}, wards={"wind", "torch"}, prep="wrap the relic in moss cloth", tail="wrapped the relic in moss cloth"),
    Gift(id="river_stone", label="river stone charm", covers={"hands"}, wards={"river"}, prep="hold the river stone charm first", tail="held the river stone charm first"),
    Gift(id="snow_cap", label="a snow cap", covers={"head"}, wards={"snow", "wind"}, prep="wear the snow cap for the rite", tail="wore the snow cap for the rite"),
    Gift(id="bronze_guard", label="bronze guards", covers={"feet", "hands"}, wards={"ice", "river"}, prep="lace on the bronze guards", tail="laced on the bronze guards"),
]

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "Zoe", "Iris"]
BOY_NAMES = ["Bobby", "Theo", "Leo", "Finn", "Noah", "Max"]
TRAITS = ["bold", "curious", "stubborn", "gentle", "steady", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trial_id in setting.affords:
            trial = TRIALS[trial_id]
            for rid, relic in RELICS.items():
                if trial.keyword in {"torch", "river", "snow", "ice", "wind"} and select_gift(trial, relic):
                    combos.append((place, trial_id, rid))
    return combos


@dataclass
class StoryParams:
    place: str
    trial: str
    relic: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What is magic?", "Magic is a made-up power in old stories that can do surprising things, often with spells, charms, or special rules.")],
    "myth": [("What is a myth?", "A myth is an old story people told to explain the world, teach a lesson, or praise a hero.")],
    "olympian": [("Who is an Olympian?", "An Olympian is an athlete who competes in the Olympic Games, which are big sports events with teams from many countries.")],
    "canada": [("What is Canada?", "Canada is a country in North America, known for cold winters, forests, lakes, and friendly towns.")],
    "torch": [("What does a torch do?", "A torch gives light. In stories, it can also stand for courage or a guiding flame.")],
    "river": [("What is a river?", "A river is a long stream of moving water that flows across land to a bigger body of water.")],
    "snow": [("What is snow?", "Snow is frozen water that falls from clouds as soft white flakes.")],
    "wind": [("What is wind?", "Wind is moving air. You can feel it on your face and hear it in trees.")],
    "ice": [("What is ice?", "Ice is frozen water. It is hard and slippery when it covers the ground.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, trial, relic = f["hero"], f["guide"], f["trial"], f["relic"]
    return [
        f'Write a short myth for a young child about {hero.id}, a Canadian Olympian, and a magic trial with "{trial.keyword}".',
        f"Tell a gentle legend where {hero.id} wants to {trial.verb} but {guide.id} warns about {relic.phrase}.",
        f'Write a child-friendly myth that includes an Olympian from Canada, a magic danger, and a wiser second try.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, trial, relic = f["hero"], f["guide"], f["trial"], f["relic"]
    trait = next((t for t in hero.traits if t != "little"), "brave")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {trait} Olympian from Canada who meets a magic trial.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {trial.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {guide.id} worry about the trial?",
            answer=f"{guide.id} worried because the {trial.keyword} magic could {trial.danger}, and {relic.phrase} needed care.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {hero.id} was calmer and wiser, and the {relic.label} stayed bright instead of being ruined.",
        ),
    ]
    if f.get("gift"):
        gift = f["gift"]
        qa.append(
            QAItem(
                question=f"How did the {gift.label} help?",
                answer=f"The {gift.label} helped because it let {hero.id} use the magic in a safer, steadier way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trial"].tags)
    tags.add("magic")
    tags.add("myth")
    tags.add("olympian")
    if "Canada" or True:
        tags.add("canada")
    out: list[QAItem] = []
    for key in ["magic", "myth", "olympian", "canada", "torch", "river", "snow", "wind", "ice"]:
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mountain_hall", trial="torch", relic="crown", name="Bobby", gender="boy", guide="Aunt Maple", trait="bold"),
    StoryParams(place="frozen_lake", trial="snow", relic="cloak", name="Bobby", gender="boy", guide="Uncle Reed", trait="steady"),
    StoryParams(place="sky_ring", trial="wind", relic="vase", name="Bobby", gender="boy", guide="Aunt Maple", trait="curious"),
]


def explain_rejection(trial: Trial, relic: Relic) -> str:
    return f"(No story: the {trial.keyword} trial would not reasonably threaten a {relic.label}, so the myth has no honest turn.)"


def explain_gender(relic_id: str, gender: str) -> str:
    return f"(No story: {RELICS[relic_id].label} does not depend on gender here; try a different constraint.)"


ASP_RULES = r"""
trial_at_risk(T, R) :- trial(T), danger(T, D), relic(R), needs(R, D).
has_gift(T, R) :- trial_at_risk(T, R), gift(G), wards(G, T), covers(G, P), needs_region(R, P).
valid_story(Place, T, R) :- affords(Place, T), trial_at_risk(T, R), has_gift(T, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("danger", tid, t.danger))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("needs_region", rid, r.region))
        lines.append(asp.fact("needs", rid, "the_magic"))
    for g in GIFTS:
        lines.append(asp.fact("gift", g.id))
        for w in sorted(g.wards):
            lines.append(asp.fact("wards", g.id, w))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny myth world about Bobby, a Canadian Olympian, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--guide")
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
    if args.trial and args.relic:
        trial = TRIALS[args.trial]
        relic = RELICS[args.relic]
        if select_gift(trial, relic) is None:
            raise StoryError(explain_rejection(trial, relic))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trial is None or c[1] == args.trial)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trial_id, relic_id = rng.choice(sorted(combos))
    trial = TRIALS[trial_id]
    gender = args.gender or "boy"
    name = args.name or (rng.choice(BOY_NAMES) if gender == "boy" else rng.choice(GIRL_NAMES))
    guide = args.guide or rng.choice(["Aunt Maple", "Uncle Reed", "Grandmother Pine"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial_id, relic=relic_id, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TRIALS[params.trial], RELICS[params.relic],
                 hero_name=params.name, hero_type="olympian",
                 hero_traits=[params.trait], guide_name=params.guide)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, trial, relic) combos:\n")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.trial} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
