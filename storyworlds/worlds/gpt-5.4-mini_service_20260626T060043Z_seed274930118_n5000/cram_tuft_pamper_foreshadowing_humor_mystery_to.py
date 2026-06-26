#!/usr/bin/env python3
"""
storyworlds/worlds/cram_tuft_pamper_foreshadowing_humor_mystery_to.py
======================================================================

A small slice-of-life story world built from the seed words:
- cram
- tuft
- pamper

The world supports a light mystery, gentle foreshadowing, and a funny
everyday resolution. The core premise is simple: a child and caregiver are
getting ready for an ordinary outing, but something small has gone missing.
A tuft of fluff, a stuffed bag, and a pampered pet point toward the answer.

The story model uses physical meters and emotional memes:
- meters track mess, fullness, and hiding
- memes track worry, delight, curiosity, and relief

The prose is driven by simulated world state rather than a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Pet:
    label: str
    type: str
    grooming: str
    trait: str
    noise: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    pet: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"cram", "pamper", "tuft"}),
    "livingroom": Setting(place="the living room", indoors=True, affords={"cram", "pamper", "tuft"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"cram", "pamper", "tuft"}),
}

ACTIVITIES = {
    "cram": Activity(
        id="cram",
        verb="cram the bag with too many things",
        gerund="cramming the bag full",
        rush="stuff the last things into the bag",
        mess="overflow",
        soil="too full",
        keyword="cram",
        tags={"bag", "stuff", "busy"},
    ),
    "tuft": Activity(
        id="tuft",
        verb="follow the tuft",
        gerund="following the tuft",
        rush="lean close to inspect the tuft",
        mess="fluff",
        soil="fluffy",
        keyword="tuft",
        tags={"tuft", "clue", "mystery"},
    ),
    "pamper": Activity(
        id="pamper",
        verb="pamper the pet",
        gerund="pampering the pet",
        rush="gather the brush and blanket",
        mess="care",
        soil="soft and cared for",
        keyword="pamper",
        tags={"pet", "care", "soft"},
    ),
}

PRIZES = {
    "backpack": Prize(
        label="backpack",
        phrase="a small blue backpack",
        type="backpack",
        region="back",
    ),
    "lunchbox": Prize(
        label="lunchbox",
        phrase="a bright lunchbox",
        type="lunchbox",
        region="hand",
    ),
    "box": Prize(
        label="box",
        phrase="a cardboard box",
        type="box",
        region="floor",
    ),
}

PETS = {
    "cat": Pet(label="cat", type="cat", grooming="brush", trait="fluffy", noise="purr"),
    "dog": Pet(label="dog", type="dog", grooming="wipe", trait="bouncy", noise="wag"),
    "rabbit": Pet(label="rabbit", type="rabbit", grooming="comb", trait="soft", noise="twitch"),
}

GIRL_NAMES = ["Mia", "Nina", "Lila", "Zoe", "Ava", "June", "Iris"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Max", "Owen", "Eli", "Finn"]
TRAITS = ["curious", "gentle", "busy", "cheerful", "silly", "careful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                for pet in PETS:
                    combos.append((place, act, prize, pet))
    return combos


def prune_invalid(explicit: StoryParams) -> None:
    if explicit.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if explicit.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if explicit.pet not in PETS:
        raise StoryError("Unknown pet.")
    if explicit.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if explicit.activity == "pamper" and explicit.pet not in {"cat", "dog", "rabbit"}:
        raise StoryError("That pet cannot be pampered here.")


def _add(ent: Entity, **meters: float) -> Entity:
    ent.meters.update(meters)
    return ent


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "overflow": prize.meters.get("overflow", 0.0) >= THRESHOLD,
        "curiosity": sum(e.memes.get("curiosity", 0.0) for e in sim.entities.values()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id == "cram":
        actor.meters["overflow"] = actor.meters.get("overflow", 0.0) + 1
        actor.memes["excited"] = actor.memes.get("excited", 0.0) + 1
        bag = world.facts["prize"]
        bag.meters["overflow"] = bag.meters.get("overflow", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} crammed the bag until it looked round and puffed up.")
    elif activity.id == "tuft":
        actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
        clue = world.facts["clue"]
        clue.meters["noticed"] = clue.meters.get("noticed", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} leaned in to follow the tuft, because little clues do not wait politely.")
    elif activity.id == "pamper":
        pet = world.facts["pet"]
        pet.memes["content"] = pet.memes.get("content", 0.0) + 1
        pet.meters["groomed"] = pet.meters.get("groomed", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} pampered the {pet.label} with a soft brush and a warm blanket.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        pet = world.facts["pet"]
        child = world.facts["hero"]
        clue = world.facts["clue"]
        if pet.meters.get("groomed", 0.0) >= THRESHOLD and ("purr" not in world.fired):
            world.fired.add(("purr",))
            produced.append(f"The {pet.label} made a cozy purr, like a tiny motor starting up.")
            changed = True
        if clue.meters.get("noticed", 0.0) >= THRESHOLD and ("solve" not in world.fired):
            if pet.meters.get("hidden", 0.0) >= THRESHOLD:
                world.fired.add(("solve",))
                clue.meters["found"] = clue.meters.get("found", 0.0) + 1
                child.memes["relief"] = child.memes.get("relief", 0.0) + 1
                produced.append("The tuft was just the cat's fluffy tail brushing a lost mitten under the couch.")
                changed = True
    if narrate:
        for line in produced:
            world.say(line)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, pet_cfg: Pet,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "little"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(_add(Entity(id="bag", type=prize_cfg.type, label=prize_cfg.label,
                                  phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id),
                           overflow=0.0))
    pet = world.add(_add(Entity(id="Pet", kind="character", type=pet_cfg.type,
                                label=pet_cfg.label, traits=[pet_cfg.trait]), groomed=0.0))
    clue = world.add(_add(Entity(id="Clue", type="thing", label="tuft", phrase="a tiny tuft of fluff"),
                          noticed=0.0, found=0.0))
    mitten = world.add(_add(Entity(id="Mitten", type="thing", label="mitten",
                                   phrase="a striped mitten", owner=hero.id), hidden=1.0))

    world.facts.update(hero=hero, parent=parent, prize=prize, pet=pet, clue=clue, mitten=mitten,
                       activity=activity, setting=setting)

    world.say(f"{hero.id} was a {trait} {hero_type} who liked ordinary afternoons and tidy corners.")
    world.say(f"{hero.id}'s {parent.label_word} had bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wanted to {activity.verb}.")
    if activity.id == "pamper":
        world.say(f"The {pet.label} had a {pet_cfg.trait} tuft on the tail, and it loved a good {pet_cfg.grooming}.")
    elif activity.id == "cram":
        world.say(f"A small tuft of fluff sat on the floor like it was waiting to be noticed.")
    else:
        world.say(f"A little tuft near the couch looked important, but nobody said why yet.")

    world.para()
    world.say(f"Inside {setting.place}, {hero.id} started to {activity.verb}.")
    _do_activity(world, hero, activity, narrate=True)
    if activity.id == "cram":
        world.say(f"{hero.id} tried to cram one more thing in, but the bag bulged like it was hiding a joke.")
    elif activity.id == "tuft":
        world.say(f"{hero.id} followed the tuft past the couch and the basket, because it kept appearing like a breadcrumb trail.")
    else:
        world.say(f"{hero.id} wanted to pamper the pet first, before anything else could begin.")

    world.para()
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"Then {hero.id} noticed something funny: the tuft was not on the floor anymore; it was snagged near the couch.")
    world.say(f"{parent.id} said that little mysteries often start with a missing mitten and end with a silly face.")
    world.say(f"{hero.id} looked under the couch, and the {pet.label} blinked like it had not done a thing.")

    if activity.id != "pamper":
        world.say(f"That was the clue: the {pet.label} had been sleeping on the mitten and dragging tufts of blanket stuffing around.")
    else:
        world.say(f"That was the clue: the {pet.label} had rolled in the blanket and tucked the mitten beside its paws.")

    propagate(world, narrate=True)

    world.para()
    world.say(f"{parent.id} laughed, because the mystery had a very ordinary answer and a very fluffy witness.")
    world.say(f"After that, {hero.id} {activity.gerund} again, but more carefully, while {parent.id} {pet_cfg.grooming}d the {pet.label} and set the mitten back where it belonged.")
    world.say(f"By the end, the bag was packed, the tuft was explained, and the {pet.label} was pampered and proud.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    pet = f["pet"]
    return [
        f"Write a short slice-of-life story about {hero.id} trying to {activity.verb} while a tiny tuft becomes an important clue.",
        f"Tell a gentle mystery where a child notices a tuft, pampers a pet, and solves a small missing-object problem before going out.",
        f"Write a funny everyday story about a {pet.label} and a bag that gets crammed too full, ending with the mystery explained.",
        f"Write a child-friendly story that includes the word '{activity.keyword}' and a {prize.label}, and ends with a warm family moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    pet = f["pet"]
    act = f["activity"]
    clue = f["clue"]
    mitten = f["mitten"]

    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {act.verb}. That was the first thing on the child's mind.",
        ),
        QAItem(
            question=f"What small clue did {hero.id} notice?",
            answer=f"{hero.id} noticed a tuft, and it turned out to matter because it pointed to the missing mitten.",
        ),
        QAItem(
            question=f"Why did the story feel a little mysterious?",
            answer=f"It felt mysterious because the tuft and the missing mitten did not match up at first, so {hero.id} had to follow the clues.",
        ),
        QAItem(
            question=f"What did the family do for the {pet.label}?",
            answer=f"They pampered the {pet.label} with a soft brush, which helped the pet settle down and made the ending cozy.",
        ),
        QAItem(
            question=f"What was the silly part of the story?",
            answer=f"The silly part was that the {pet.label} looked innocent even though it was the one lying on the mitten and dragging fluff around.",
        ),
        QAItem(
            question=f"What was packed or prepared by the end?",
            answer=f"By the end, the {prize.label} was ready, the mitten was back in place, and the family could leave with everything in order.",
        ),
    ]


KNOWLEDGE = {
    "cram": [
        QAItem(
            question="What does it mean to cram something into a bag?",
            answer="To cram something into a bag means to push in too many things so the bag gets very full.",
        )
    ],
    "tuft": [
        QAItem(
            question="What is a tuft?",
            answer="A tuft is a small clump of hair, fluff, or fabric sticking up from something.",
        )
    ],
    "pamper": [
        QAItem(
            question="What does it mean to pamper a pet?",
            answer="To pamper a pet means to give it gentle care, like brushing, cuddling, or making it comfy.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["cram", "tuft", "pamper"]:
        out.extend(KNOWLEDGE[key])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        q = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if q:
            bits.append(f"memes={q}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="cram", prize="backpack", pet="cat", name="Mia", parent="mother", trait="curious"),
    StoryParams(place="livingroom", activity="tuft", prize="lunchbox", pet="dog", name="Ben", parent="father", trait="careful"),
    StoryParams(place="bedroom", activity="pamper", prize="box", pet="rabbit", name="Lila", parent="mother", trait="gentle"),
]


ASP_RULES = r"""
valid(Place, Act, Prize, Pet) :- setting(Place), activity(Act), prize(Prize), pet(Pet).
has_clue(Act) :- activity(Act), Act = tuft.
has_pamper(Act) :- activity(Act), Act = pamper.
has_cram(Act) :- activity(Act), Act = cram.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for pet in PETS:
        lines.append(asp.fact("pet", pet))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="Slice-of-life mystery story world with a tuft, a cram, and a pamper.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.activity and args.activity not in SETTINGS[args.place].affords:
        raise StoryError("That activity does not fit the chosen place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.pet is None or c[3] == args.pet)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize, pet = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, pet=pet, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 PETS[params.pet], params.name, params.gender if hasattr(params, "gender") else "girl",
                 params.parent, params.trait)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combinations:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = []
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
