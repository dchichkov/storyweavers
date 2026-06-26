#!/usr/bin/env python3
"""
storyworlds/worlds/provoke_moral_value_misunderstanding_comedy.py
===================================================================

A small classical storyworld about a playful provocation, a moral value
misunderstanding, and a comic turn toward making things right.

Premise:
- A child or animal character is in a tiny public place with a clear rule.
- A second character misreads the rule after a teasing provocation.
- The misunderstanding causes a funny scramble.
- The moral value is not "winning" the joke, but fixing the mix-up kindly.

This world is intentionally small and constraint-checked. It generates one
self-contained story from a simulated world model and offers matching QA,
trace, JSON, and ASP parity checks.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affordance: str  # the rule / object that can be misunderstood


@dataclass
class RuleCard:
    """A small printed rule that can be misunderstood as a joke."""
    id: str
    text: str
    clue: str
    moral_value: str
    comic_false_reading: str


@dataclass
class StoryParams:
    setting: str
    rulecard: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, card: RuleCard) -> None:
        self.setting = setting
        self.card = card
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting, self.card)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bakery": Setting(place="the bakery", indoors=True, affordance="counter"),
    "classroom": Setting(place="the classroom", indoors=True, affordance="board"),
    "library": Setting(place="the library", indoors=True, affordance="desk"),
}

RULECARDS = {
    "wait-turn": RuleCard(
        id="wait-turn",
        text="Please wait your turn.",
        clue="A neat line of footprints leads to the counter.",
        moral_value="patience",
        comic_false_reading="Please take one, then wink at everyone.",
    ),
    "quiet": RuleCard(
        id="quiet",
        text="Please keep your voice low.",
        clue="A tiny whisper sign hangs beside the shelf.",
        moral_value="respect",
        comic_false_reading="Please tell your loudest joke.",
    ),
    "share": RuleCard(
        id="share",
        text="Please share the crayons.",
        clue="A cup of bright crayons sits in the middle of the table.",
        moral_value="sharing",
        comic_false_reading="Please hide the crayons in your hat.",
    ),
}

TRAITS = ["curious", "playful", "silly", "cheerful", "mischievous", "lively"]
GIRL_NAMES = ["Mia", "Lina", "Zoe", "Pia", "Nora", "Ava"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Finn", "Leo", "Max"]


# ---------------------------------------------------------------------------
# Validity helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SETTINGS for r in RULECARDS]


def reasonableness_gate(setting: Setting, card: RuleCard) -> bool:
    return bool(setting.place and card.text and card.moral_value)


def explain_rejection(setting: Setting, card: RuleCard) -> str:
    return f"(No story: the setting '{setting.place}' and rule '{card.id}' do not make a believable comic misunderstanding.)"


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------

def is_female(gender: str) -> bool:
    return gender == "girl"


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    card = RULECARDS[params.rulecard]
    world = World(setting, card)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"curiosity": 0.0, "silliness": 0.0, "embarrassment": 0.0, "joy": 0.0},
        memes={"confusion": 0.0, "kindness": 0.0, "mischief": 0.0, "understanding": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
        meters={"calm": 1.0},
        memes={"patience": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="teacher" if params.setting == "classroom" else "baker",
        label="helper",
        meters={"busy": 0.0},
        memes={"kindness": 1.0},
    ))
    rule = world.add(Entity(
        id="RuleCard",
        type="card",
        label="rule card",
        phrase=card.text,
    ))

    world.facts.update(hero=hero, parent=parent, helper=helper, rule=rule, card=card, setting=setting)
    return world


def _r_provoke(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    if hero.memes["mischief"] < THRESHOLD:
        return out
    sig = ("provoke", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["silliness"] += 1
    world.facts["provoked"] = True
    out.append(f"{hero.id} tried to be funny and poked at the situation just a little too much.")
    return out


def _r_misunderstand(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    helper = world.get(world.facts["helper"].id)
    if hero.meters["silliness"] < THRESHOLD or hero.memes["confusion"] < THRESHOLD:
        return out
    sig = ("misunderstand", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["embarrassment"] += 1
    helper.meters["busy"] += 1
    world.facts["misunderstanding"] = True
    out.append(f"That made {hero.id} read the rule the wrong way and set off a little mix-up.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    parent = world.get(world.facts["parent"].id)
    helper = world.get(world.facts["helper"].id)
    if hero.meters["embarrassment"] < THRESHOLD:
        return out
    sig = ("fix", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["understanding"] += 1
    hero.memes["kindness"] += 1
    hero.meters["embarrassment"] = 0.0
    world.facts["resolved"] = True
    out.append(f"{parent.label_word.capitalize()} helped clear it up, and {helper.label_word} smiled because the good fix was the honest one.")
    return out


RULES = [
    _r_provoke,
    _r_misunderstand,
    _r_fix,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_outcome(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_hero.memes["mischief"] += 1
    sim_hero.memes["confusion"] += 1
    sim_hero.meters["silliness"] += 1
    propagate(sim, narrate=False)
    return {
        "misunderstanding": bool(sim.facts.get("misunderstanding")),
        "resolved": bool(sim.facts.get("resolved")),
    }


# ---------------------------------------------------------------------------
# Story functions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in [hero.type] if t), "child")
    world.say(f"{hero.id} was a little {trait} who loved a good laugh at {world.setting.place}.")


def love_rule(world: World, hero: Entity) -> None:
    card = world.facts["card"]
    hero.memes["kindness"] += 0.5
    world.say(f"On the wall was a card that said, “{card.text}”")
    world.say(f"It was meant to teach {card.moral_value}, but it also sounded funny to {hero.id}.")


def setup_scene(world: World, hero: Entity, parent: Entity) -> None:
    where = "inside" if world.setting.indoors else "outside"
    world.say(f"One day, {hero.id} and {parent.label_word} were {where} at {world.setting.place}.")
    world.say(f"Nearby, the little rule card was easy to see, and that was where the trouble started.")


def provoke_misread(world: World, hero: Entity, parent: Entity) -> None:
    card = world.facts["card"]
    hero.memes["mischief"] += 1
    hero.memes["confusion"] += 1
    world.say(
        f'{hero.id} grinned and said, “What if the rule means {card.comic_false_reading}” '
        f"just to provoke a laugh."
    )
    propagate(world, narrate=True)


def comic_scramble(world: World, hero: Entity, helper: Entity) -> None:
    card = world.facts["card"]
    if not world.facts.get("misunderstanding"):
        return
    world.say(
        f"Then the mix-up grew so big that {helper.label_word} had to pause the room and look at the card again."
    )
    world.say(
        f"It turned out the card really said, “{card.text}” and not the silly version."
    )
    world.say(
        f"Everyone blinked, then laughed, because the misunderstanding had been caused by one very wiggly joke."
    )


def resolve(world: World, hero: Entity, parent: Entity, helper: Entity) -> None:
    card = world.facts["card"]
    hero.memes["understanding"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} explained that the moral value was {card.moral_value}: "
        f"being kind enough to wait, listen, or share."
    )
    world.say(
        f"{hero.id} nodded, apologized for the teasing, and helped put things right."
    )
    world.say(
        f"By the end, the room was calm again, and the funny little rule had become a useful lesson."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.name)
    parent = world.get("Parent")
    helper = world.get("Helper")

    world.say(f"{hero.id} was a {params.trait} {params.gender} who noticed small things very quickly.")
    love_rule(world, hero)
    world.para()
    setup_scene(world, hero, parent)
    provoke_misread(world, hero, parent)
    world.para()
    comic_scramble(world, hero, helper)
    resolve(world, hero, parent, helper)

    world.facts.update(
        provoked=bool(world.facts.get("provoked")),
        misunderstanding=bool(world.facts.get("misunderstanding")),
        resolved=bool(world.facts.get("resolved")),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    card = f["card"]
    return [
        f'Write a short comic story for a young child where {hero.id} tries to provoke a funny reaction but learns the value of {card.moral_value}.',
        f'Create a gentle, funny story about a misunderstanding at {world.setting.place} involving the rule "{card.text}".',
        f'Write a TinyStories-style story in which a teasing remark causes a mix-up, then an honest explanation fixes it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    helper = f["helper"]
    card = f["card"]

    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do when the trouble began?",
            answer=f"{hero.id} was trying to provoke a laugh by teasing the rule in a silly way.",
        ),
        QAItem(
            question=f"What rule was written on the card at {world.setting.place}?",
            answer=f'The card said, “{card.text}”',
        ),
        QAItem(
            question=f"What moral value did the card really teach?",
            answer=f"It taught {card.moral_value}, which means being fair and thoughtful instead of making a joke at someone else's expense.",
        ),
    ]
    if f.get("misunderstanding"):
        qa.append(
            QAItem(
                question=f"Why did the misunderstanding happen?",
                answer=f"It happened because {hero.id} twisted the rule into a silly false reading, and that made everyone pause and look again.",
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How was the mix-up fixed?",
                answer=f"{parent.label_word.capitalize()} explained the real meaning, and {helper.label_word} helped everyone settle down so {hero.id} could apologize and make things right.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    card = world.facts["card"]
    if card.moral_value == "patience":
        answer = "Patience means waiting calmly without rushing."
    elif card.moral_value == "respect":
        answer = "Respect means caring about other people's space, feelings, and rules."
    else:
        answer = "Sharing means letting other people use something too, instead of keeping it all to yourself."
    return [
        QAItem(
            question=f"What does {card.moral_value} mean?",
            answer=answer,
        ),
        QAItem(
            question="Why is it funny when someone misunderstands a sign?",
            answer="It can be funny because the wrong idea sounds dramatic or silly, and then the real meaning makes everything clear again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
rulecard(R) :- rule_text(R,_).

valid(S,R) :- setting(S), rulecard(R), afford(S,R).

% A provocation is reasonable when it can lead to confusion and a later fix.
provocation(S,R) :- valid(S,R), moral_value(R,M), M = patience.
provocation(S,R) :- valid(S,R), moral_value(R,M), M = respect.
provocation(S,R) :- valid(S,R), moral_value(R,M), M = sharing.

misunderstanding(S,R) :- provocation(S,R).
resolved(S,R) :- misunderstanding(S,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        lines.append(asp.fact("afford", sid, "rulecard"))
    for rid, r in RULECARDS.items():
        lines.append(asp.fact("rulecard", rid))
        lines.append(asp.fact("rule_text", rid, r.text))
        lines.append(asp.fact("moral_value", rid, r.moral_value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SETTINGS for r in RULECARDS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy storyworld about provocation, misunderstanding, and a moral lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rulecard", choices=RULECARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rulecard is None or c[1] == args.rulecard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rulecard = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, rulecard=rulecard, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/rulecard combos:")
        for s, r in combos:
            print(f"  {s:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for setting, rulecard in valid_combos():
            params = StoryParams(
                setting=setting,
                rulecard=rulecard,
                name="Milo",
                gender="boy",
                parent="mother",
                trait="curious",
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
