#!/usr/bin/env python3
"""
A cautionary ghost-story world about a child, a spooky house, and a bad
midnight snack that makes them regurgitate.

The premise is intentionally small: a child is tempted by something ghostly,
a warning is given, a risky choice is made or avoided, and the ending proves
what changed in the world. The story stays close to a campfire-style ghost tale
while remaining child-facing and concrete.
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
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
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


@dataclass
class Setting:
    place: str
    eerie: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    name: str
    verb: str
    gerund: str
    smell: str
    consequence: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    name: str
    use: str
    tail: str
    prevents: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_recap(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    tempt = world.facts.get("temptation")
    if not child or not tempt:
        return out
    if child.meters.get("fear", 0) >= THRESHOLD and child.meters.get("warning", 0) >= THRESHOLD:
        sig = ("recap", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The house seemed to listen.")
    return out


def _r_regurgitate(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    tempt = world.facts.get("temptation")
    if not child or not tempt:
        return out
    if child.meters.get("queasy", 0) < THRESHOLD:
        return out
    if child.meters.get("regurgitated", 0) >= THRESHOLD:
        return out
    sig = ("regurgitate", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["regurgitated"] = 1
    child.meters["fear"] = child.meters.get("fear", 0) + 1
    out.append(f"{child.id} had to regurgitate into a bowl, and the ghostly room went very still.")
    return out


CAUSAL_RULES = [
    _r_recap,
    _r_regurgitate,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cautionary ghost story world: a haunted house, a warning, and a bad midnight choice."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


@dataclass
class StoryParams:
    place: str
    temptation: str
    remedy: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "old_house": Setting(place="the old house", eerie="the halls whispered back", affords={"potion", "candies"}),
    "attic": Setting(place="the attic", eerie="the rafters creaked like quiet feet", affords={"candies"}),
    "kitchen": Setting(place="the kitchen", eerie="the clock ticked too loud", affords={"potion"}),
}

TEMPTATIONS = {
    "potion": Temptation(
        id="potion",
        name="a glowing potion",
        verb="sip the glowing potion",
        gerund="sipping the glowing potion",
        smell="sweet and strange",
        consequence="felt queasy",
        caution="You should not sip strange glowing drinks in a ghost house",
        tags={"ghost", "spooky", "drink"},
    ),
    "candies": Temptation(
        id="candies",
        name="a dish of old candies",
        verb="eat the old candies",
        gerund="eating old candies",
        smell="sugary and dusty",
        consequence="felt sick",
        caution="You should not eat old candies from a spooky room",
        tags={"ghost", "spooky", "sweet"},
    ),
}

REMEDIES = {
    "water": Remedy(
        id="water",
        name="a glass of water",
        use="take slow sips of water",
        tail="the child kept the bowl nearby and sipped water until the nausea passed",
        prevents={"potion", "candies"},
    ),
    "bowl": Remedy(
        id="bowl",
        name="a wooden bowl",
        use="hold a bowl close by",
        tail="the wooden bowl was ready, and the child knew where to aim if the sickness came",
        prevents={"potion", "candies"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Maya", "June", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Owen", "Jack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for temp in setting.affords:
            for rem in REMEDIES:
                combos.append((place, temp, rem))
    return combos


def explain_invalid(args: argparse.Namespace) -> str:
    return "(No story: that combination would not make a believable cautionary ghost tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError(explain_invalid(args))
    place, temptation, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, temptation=temptation, remedy=remedy, name=name, gender=gender, parent=parent)


def _tell(setting: Setting, tempt: Temptation, remedy: Remedy, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="a thin ghost"))
    bowl = world.add(Entity(id="Bowl", type="bowl", label=remedy.name))
    world.facts.update(child=child, parent=parent, ghost=ghost, bowl=bowl, temptation=tempt, remedy=remedy)

    world.say(f"{child.id} was a little {next(t for t in child.traits if t != 'little')} {gender} who slept in {setting.place}.")
    world.say(f"That night, {setting.eerie}, and a thin ghost floated near the stairs.")
    world.say(f"It pointed at {tempt.name} and whispered that it smelled {tempt.smell}.")

    world.para()
    child.meters["fear"] = 1
    child.meters["warning"] = 1
    world.say(f"{child.id}'s {parent_type} gave a cautionary warning: \"{tempt.caution}.\"")
    world.say(f"{child.id} promised to listen, but the smell kept tugging at {child.pronoun('possessive')} nose.")

    world.para()
    child.meters["desire"] = 1
    world.say(f"Still, {child.id} reached for {tempt.name}.")
    world.say(f"The ghost shook its head, but the room felt quiet enough to tempt {child.id} anyway.")
    if setting.affords and tempt.id in setting.affords:
        child.meters["tried"] = 1
        child.meters["queasy"] = 1
        world.say(f"{child.id} took a taste and quickly felt queasy.")
    if remedy.id == "bowl":
        world.say(f"{parent_type.capitalize()} slid {remedy.name} close by before the trouble got worse.")
    else:
        world.say(f"{parent_type.capitalize()} brought {remedy.name} and told {child.id} to sip slowly.")

    propagate(world, narrate=True)

    if child.meters.get("regurgitated", 0) >= THRESHOLD:
        child.meters["relief"] = 1
        world.say(f"In the end, {child.id} was relieved to rest beside {remedy.name}, and the ghost never offered strange snacks again.")
    else:
        world.say(f"In the end, {child.id} chose the safe way, and the house stayed quiet through the dark.")

    world.facts.update(resolved=child.meters.get("regurgitated", 0) < THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short cautionary ghost story for a young child that includes the word "regurgitate".',
        f"Tell a spooky but gentle story where {f['child'].id} is warned not to {f['temptation'].verb} in {f['parent'].type}'s old house.",
        f"Write a ghost story about a child, a warning, and a strange snack, ending with a safe choice or a sick stomach.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    tempt = f["temptation"]
    remedy = f["remedy"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"Where was {child.id} when the ghost story happened?",
            answer=f"{child.id} was in {world.setting.place}, where the halls were spooky and the ghost could whisper nearby.",
        ),
        QAItem(
            question=f"What did the ghostly warning tell {child.id} not to do?",
            answer=f"The warning told {child.id} not to {tempt.verb}, because strange food or drinks in a ghost house can make a child sick.",
        ),
        QAItem(
            question=f"What helped {child.id} stay safe after the spooky trouble?",
            answer=f"{remedy.name} helped because the child could {remedy.use}, and that gave the stomach time to settle.",
        ),
    ]
    if not world.facts.get("resolved", True):
        qa.append(
            QAItem(
                question=f"Why did {child.id} have to regurgitate?",
                answer=f"{child.id} had to regurgitate because {child.pronoun('subject')} tried to {tempt.verb}, and the strange snack made {child.pronoun('object')} queasy.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"Why was the story cautionary?",
                answer=f"It was cautionary because {parent.id} gave a clear warning, and {child.id} listened before the ghost's trick could cause real trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means slowing down, listening to warnings, and avoiding choices that could cause harm.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about a ghost or a haunted place, usually told in a way that feels thrilling but safe.",
        ),
        QAItem(
            question="Why can strange old food make someone sick?",
            answer="Old or strange food can make someone sick because it may have gone bad or may not be safe to eat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
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
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
% A temptation is risky if the child tries it and the world marks it as afforded.
risky(T) :- temptation(T).

safe(T) :- remedy(R), prevents(R, T).

valid_story(P, T, R) :- place(P), temptation(T), remedy(R), affords(P, T), safe(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", p, t))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temptation", t))
    for r, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", r))
        for t in sorted(rem.prevents):
            lines.append(asp.fact("prevents", r, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
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
    world = _tell(SETTINGS[params.place], TEMPTATIONS[params.temptation], REMEDIES[params.remedy], params.name, params.gender, params.parent)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="old_house", temptation="candies", remedy="bowl", name="Mina", gender="girl", parent="mother"),
            StoryParams(place="attic", temptation="candies", remedy="water", name="Eli", gender="boy", parent="father"),
            StoryParams(place="kitchen", temptation="potion", remedy="water", name="Nora", gender="girl", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.temptation} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
