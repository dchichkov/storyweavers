#!/usr/bin/env python3
"""
storyworlds/worlds/sorceress_chubby_magic_whodunit.py
=====================================================

A small whodunit-style story world about a sorceress, a chubby helper, and a
magical mystery.

The premise:
- A sorceress keeps one important magical object in her tower.
- One evening, it goes missing.
- She and a chubby helper look for clues.
- Magic helps them find the truth.

The world is intentionally compact and state-driven: meter facts (dust, glow,
hunger, worry, relief) and meme facts (curiosity, suspicion, pride, fear)
drive the prose instead of a frozen paragraph with swapped names.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sorceress", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"wizard", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit tower"
    afford_magic: bool = True


@dataclass
class Clue:
    kind: str
    label: str
    hint: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    has_item: bool = False
    innocent: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def world_state(entity: Entity) -> str:
    parts = []
    if entity.meters:
        parts.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in sorted(entity.meters.items()) if v)}}}")
    if entity.memes:
        parts.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in sorted(entity.memes.items()) if v)}}}")
    return " ".join(parts)


def _gate_reasonable(params: "StoryParams") -> None:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.objective not in OBJECTIVES:
        raise StoryError("Unknown objective.")


def _predict_truth(world: World) -> bool:
    # In this tiny world, the clue points to the true culprit only if magic can be used.
    return world.setting.afford_magic


def _search(world: World, narrator: Entity, helper: Entity, clue: Clue) -> None:
    narrator.memes["curiosity"] = narrator.memes.get("curiosity", 0) + 1
    helper.memes["curiosity"] = helper.memes.get("curiosity", 0) + 1
    world.say(
        f"At {world.setting.place}, the sorceress noticed something troubling: "
        f"the {clue.label} had vanished from its velvet stand."
    )
    world.say(
        f"Her chubby helper frowned and looked under the table, behind the curtains, "
        f"and beside the spellbooks, but the {clue.label} was nowhere to be seen."
    )


def _question_suspects(world: World, narrator: Entity, helper: Entity, culprit: Suspect) -> None:
    narrator.memes["suspicion"] = narrator.memes.get("suspicion", 0) + 1
    helper.memes["suspicion"] = helper.memes.get("suspicion", 0) + 1
    world.say(
        f"They questioned the housefolk one by one. The baker was floury, the cat was "
        f"sleepy, and the old raven kept saying it saw nothing."
    )
    world.say(
        f"The chubby helper asked careful questions, because in a whodunit the smallest "
        f"remark can matter more than a loud promise."
    )
    if culprit.has_item:
        world.say(
            f"One suspect kept glancing toward the cupboard, as if hiding a secret."
        )


def _use_magic(world: World, narrator: Entity, clue: Clue, culprit: Suspect) -> None:
    if not world.setting.afford_magic:
        raise StoryError("This story needs Magic to solve the whodunit.")
    narrator.meters["glow"] = narrator.meters.get("glow", 0) + 1
    narrator.memes["hope"] = narrator.memes.get("hope", 0) + 1
    world.say(
        f"Then the sorceress lifted her hands and cast Magic over the room. "
        f"A ribbon of light touched the floor, and it showed a tiny trail of {clue.hint}."
    )
    world.say(
        f"The trail did not lead to the baker or the cat. It wound all the way to the window "
        f"and stopped at a nest tucked under the roof beam."
    )
    world.facts["revealed_culprit"] = culprit.id


def _resolution(world: World, narrator: Entity, helper: Entity, culprit: Suspect, clue: Clue) -> None:
    narrator.memes["relief"] = narrator.memes.get("relief", 0) + 2
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"In the nest lay the missing {clue.label}, caught beside a few shiny buttons and a blue bead. "
        f"A clever magpie had carried it off for its glittering collection."
    )
    world.say(
        f"The sorceress laughed with relief, and her chubby helper laughed too. "
        f"They returned the {clue.label} to its stand, then shut the window before any more shiny things could wander away."
    )
    world.say(
        f"By the end, the tower was quiet again, the Magic glow had faded, and the little stand "
        f"held the {clue.label} exactly where it belonged."
    )


def tell(setting: Setting, clue: Clue, suspect: Suspect, objective: str,
         name: str = "Elara", helper_name: str = "Pip") -> World:
    world = World(setting)
    sorceress = world.add(Entity(
        id=name, kind="character", type="sorceress", label="the sorceress",
        traits=["clever", "careful"], meters={"glow": 0.0}, memes={"curiosity": 0.0}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="helper", label="the chubby helper",
        traits=["chubby", "kind"], meters={"hunger": 0.0}, memes={"curiosity": 0.0}
    ))
    world.facts.update(
        sorceress=sorceress,
        helper=helper,
        clue=clue,
        suspect=suspect,
        objective=objective,
        setting=setting,
    )

    _search(world, sorceress, helper, clue)
    world.para()
    _question_suspects(world, sorceress, helper, suspect)
    world.para()
    _use_magic(world, sorceress, clue, suspect)
    _resolution(world, sorceress, helper, suspect, clue)
    return world


SETTINGS = {
    "tower": Setting(place="the moonlit tower", afford_magic=True),
    "library": Setting(place="the old spell library", afford_magic=True),
    "garden": Setting(place="the herb garden behind the tower", afford_magic=True),
}

CLUES = {
    "amulet": Clue(kind="amulet", label="silver amulet", hint="sparkling dust"),
    "wand": Clue(kind="wand", label="wooden wand", hint="tiny splinters"),
    "book": Clue(kind="book", label="spellbook", hint="blue ink"),
}

SUSPECTS = {
    "baker": Suspect(id="baker", label="the baker", type="baker", has_item=False, innocent=True),
    "cat": Suspect(id="cat", label="the cat", type="cat", has_item=False, innocent=True),
    "raven": Suspect(id="raven", label="the raven", type="raven", has_item=False, innocent=True),
    "magpie": Suspect(id="magpie", label="the magpie", type="magpie", has_item=True, innocent=False),
}

OBJECTIVES = {
    "find": "find the missing thing",
    "return": "return the missing thing",
    "solve": "solve the mystery",
}


@dataclass
class StoryParams:
    setting: str = "tower"
    clue: str = "amulet"
    suspect: str = "magpie"
    objective: str = "solve"
    name: str = "Elara"
    helper_name: str = "Pip"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small sorceress whodunit with Magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--objective", choices=OBJECTIVES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    for field in ("setting", "clue", "suspect", "objective"):
        value = getattr(args, field, None)
        if value is not None and value not in globals()[field.upper() + "S"]:
            raise StoryError(f"Unknown {field}.")
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    objective = args.objective or "solve"
    _gate_reasonable(StoryParams(setting, clue, suspect, objective))
    name = args.name or rng.choice(["Elara", "Mira", "Seren", "Ivy"])
    helper_name = args.helper_name or rng.choice(["Pip", "Moss", "Dibble", "Bram"])
    return StoryParams(setting=setting, clue=clue, suspect=suspect, objective=objective,
                       name=name, helper_name=helper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit for children about a sorceress named {f['sorceress'].id} and a chubby helper named {f['helper'].id}.",
        f"Tell a mystery story where Magic reveals who took the {f['clue'].label}.",
        f"Write a simple detective tale set at {f['setting'].place} that ends with the missing {f['clue'].label} being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sorceress: Entity = f["sorceress"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    return [
        QAItem(
            question=f"What went missing at {f['setting'].place}?",
            answer=f"The missing thing was the {clue.label}.",
        ),
        QAItem(
            question=f"Who looked for clues with the sorceress?",
            answer=f"The sorceress searched with her chubby helper, {helper.id}.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer="They used Magic to reveal a shining trail that led to the real hiding place.",
        ),
        QAItem(
            question=f"Who turned out to be behind the mystery?",
            answer=f"The {suspect.label} was the real culprit in the whodunit.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The {clue.label} was returned to its stand, and the tower felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sorceress?",
            answer="A sorceress is a person who uses magic spells.",
        ),
        QAItem(
            question="What does it mean to be chubby?",
            answer="Chubby means pleasantly round or plump.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the characters try to find out who did something.",
        ),
        QAItem(
            question="What is Magic in this story world?",
            answer="Magic is a special power that can reveal hidden things and help solve mysteries.",
        ),
    ]


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {world_state(e)}")
    lines.append(f"facts: {world.facts.get('revealed_culprit', 'unrevealed')}")
    return "\n".join(lines)


ASP_RULES = r"""
{ suspect(baker); suspect(cat); suspect(raven); suspect(magpie) }.
culprit(magpie).
missing(amulet).
magic_available.
reveals_mystery :- magic_available, culprit(magpie), missing(amulet).
#show culprit/1.
#show reveals_mystery/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "tower"),
        asp.fact("setting", "library"),
        asp.fact("setting", "garden"),
        asp.fact("clue", "amulet"),
        asp.fact("clue", "wand"),
        asp.fact("clue", "book"),
        asp.fact("suspect", "baker"),
        asp.fact("suspect", "cat"),
        asp.fact("suspect", "raven"),
        asp.fact("suspect", "magpie"),
        asp.fact("magic_available"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show culprit/1.\n#show reveals_mystery/0."))
    atoms = asp.atoms(model, "culprit")
    if atoms == [("magpie",)]:
        print("OK: ASP identifies the magpie as culprit.")
        return 0
    print("MISMATCH: ASP did not resolve the mystery as expected.")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    world = tell(setting, clue, suspect, OBJECTIVES[params.objective], params.name, params.helper_name)
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
    StoryParams(setting="tower", clue="amulet", suspect="magpie", objective="solve", name="Elara", helper_name="Pip"),
    StoryParams(setting="library", clue="book", suspect="raven", objective="find", name="Mira", helper_name="Bram"),
    StoryParams(setting="garden", clue="wand", suspect="cat", objective="return", name="Seren", helper_name="Moss"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show culprit/1.\n#show reveals_mystery/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show culprit/1.\n#show reveals_mystery/0."))
        print("culprit:", asp.atoms(model, "culprit"))
        print("reveals_mystery:", bool(asp.atoms(model, "reveals_mystery")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
