#!/usr/bin/env python3
"""
storyworlds/worlds/compost_vocabulary_peanut_dialogue_problem_solving_mystery.py
================================================================================

A small storyworld about a child, a compost bin, a tricky missing peanut, and
a mystery solved through careful dialogue and practical problem solving.

Premise:
- A curious child is helping sort scraps into a compost bin.
- A peanut-themed snack goes missing, and strange clues appear near the compost.
- The child and a grown-up talk through the clues, test a few ideas, and solve
  the mystery by noticing what compost can and cannot do.

This world is designed to produce short, child-facing mystery stories with:
- Dialogue
- Problem solving
- A gentle investigative tone

The seed words are woven into the domain:
- compost
- vocabulary
- peanut
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
class Location:
    place: str = "the garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    reveals: str
    suspicious: bool = False


@dataclass
class MysteryAction:
    id: str
    verb: str
    search: str
    consequence: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    purpose: str
    plural: bool = False


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues_seen: list[str] = []

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


SETTINGS = {
    "garden": Location(place="the garden", indoors=False, affords={"search_compost", "sort_scraps", "inspect_shells"}),
    "backyard": Location(place="the backyard", indoors=False, affords={"search_compost", "sort_scraps"}),
    "kitchen": Location(place="the kitchen", indoors=True, affords={"sort_scraps", "inspect_shells"}),
}

ACTIONS = {
    "compost_mystery": MysteryAction(
        id="compost_mystery",
        verb="look in the compost",
        search="check the compost bin",
        consequence="the clue points back to the snack shelf",
        clue="peanut_shell",
        tags={"compost", "peanut"},
    ),
    "vocabulary_sorting": MysteryAction(
        id="vocabulary_sorting",
        verb="sort the vocabulary cards",
        search="check the word cards",
        consequence="the clue shows which word is missing",
        clue="word_card",
        tags={"vocabulary"},
    ),
}

CLUES = {
    "peanut_shell": Clue(
        id="peanut_shell",
        label="a peanut shell",
        hint="It had a neat crack in it, like something had been opened by hand.",
        reveals="someone had eaten a peanut snack nearby and left the shell behind",
        suspicious=True,
    ),
    "word_card": Clue(
        id="word_card",
        label="a vocabulary card",
        hint="The card had the word compost written in big letters, but one corner was smudged.",
        reveals="the child had been practicing the word compost near the bin",
        suspicious=False,
    ),
    "crumb_trail": Clue(
        id="crumb_trail",
        label="a trail of crumbs",
        hint="The crumbs led from the bench to the compost bin.",
        reveals="the missing peanut snack had been eaten while the child was learning words outside",
        suspicious=True,
    ),
}

GEAR = [
    Gear(id="gloves", label="garden gloves", purpose="keep hands clean", plural=True),
    Gear(id="basket", label="a little basket", purpose="carry the clues", plural=False),
]

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "June", "Ada"]
BOY_NAMES = ["Ezra", "Owen", "Milo", "Theo", "Nico", "Finn"]


@dataclass
class StoryParams:
    setting: str
    action: str
    clue: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")


def compatible_story(action: MysteryAction, clue: Clue, location: Location) -> bool:
    if action.id == "compost_mystery":
        return location.place in {"the garden", "the backyard"} and clue.id in {"peanut_shell", "crumb_trail"}
    if action.id == "vocabulary_sorting":
        return clue.id in {"word_card", "crumb_trail"} and location.indoors is False or location.place == "the kitchen"
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, loc in SETTINGS.items():
        for aid, act in ACTIONS.items():
            for cid, clue in CLUES.items():
                if compatible_story(act, clue, loc):
                    out.append((sid, aid, cid))
    return out


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(location: Location, action: MysteryAction, clue: Clue, hero_name: str, gender: str, parent: str) -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    grownup = world.add(Entity(id="grownup", kind="character", type=parent, label=f"the {parent}"))
    basket = world.add(Entity(id="basket", type="basket", label="a little basket", owner=hero.id))
    gloves = world.add(Entity(id="gloves", type="gloves", label="garden gloves", owner=hero.id, plural=True))

    world.facts.update(hero=hero, grownup=grownup, basket=basket, gloves=gloves, action=action, clue=clue)

    world.say(
        f"{hero.id} was a curious little {gender} who loved the word compost, and "
        f"{hero.pronoun('possessive')} pockets were full of vocabulary cards."
    )
    world.say(
        f"One afternoon, {hero.id} found a peanut snack on the bench and carried it close while "
        f"looking at the compost bin."
    )

    world.para()
    world.say(
        f"\"Did you put the peanut there?\" {grownup.label} asked."
    )
    world.say(
        f"\"No,\" {hero.id} said. \"I was just practicing my vocabulary. Then I noticed something strange.\""
    )
    world.say(
        f"At {location.place}, {hero.id} could see {action.search} and compare every clue with care."
    )

    world.para()
    if clue.id == "peanut_shell":
        world.say(
            f"{hero.id} lifted {clue.label} with {gloves.label}. \"This looks important,\" {hero.pronoun()} said."
        )
        world.say(f"\"What does it tell us?\" asked {grownup.label}.")
        world.say(
            f"\"It means someone ate a peanut snack here,\" {hero.id} said. \"The compost did not make this shell. The shell is the clue.\""
        )
        world.say(
            f"{grownup.label} nodded. \"Good thinking. Compost helps broken plant scraps turn into soil, but it does not chew peanut shells.\""
        )
        world.say(
            f"Together they followed the crumbs and found the snack wrapper near the garden stool."
        )
    elif clue.id == "word_card":
        world.say(
            f"{hero.id} picked up {clue.label} and read it aloud. \"Com-post,\" {hero.id} said carefully."
        )
        world.say(f"\"That word fits the bin,\" said {grownup.label}.")
        world.say(
            f"Then {hero.id} noticed the crumbs. \"Wait,\" {hero.id} said, \"the peanut snack was eaten near my cards.\""
        )
        world.say(
            f"{grownup.label} smiled. \"So the mystery is not about the compost being bad. It is about a snack, a smudge, and a messy bench.\""
        )
        world.say(
            f"They put the cards in {basket.label} and cleaned the bench before the next lesson."
        )
    else:
        world.say(
            f"{hero.id} followed {clue.label} step by step. \"This trail starts at the bench,\" {hero.id} said."
        )
        world.say(
            f"\"And it ends by the compost bin,\" said {grownup.label}. \"So the peanut snack came first, and the compost got blamed by mistake.\""
        )
        world.say(
            f"{hero.id} grinned. \"Then the answer is simple: the compost was only the place where the crumbs landed.\""
        )
        world.say(
            f"They swept the path, saved the vocabulary cards, and left the compost bin ready for scraps again."
        )

    world.para()
    world.say(
        f"In the end, {hero.id} solved the mystery by asking good questions, using {gloves.label}, and checking each clue one by one."
    )
    world.say(
        f"The peanut was not in the compost at all, and the word compost stayed on the cards where it belonged."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    clue = f["clue"]
    return [
        f"Write a short mystery story for a child named {hero.id} about compost, a peanut clue, and careful dialogue.",
        f"Tell a gentle problem-solving story where {hero.id} asks questions, checks {clue.label}, and learns the word compost.",
        f"Write a child-facing mystery using the words compost, vocabulary, and peanut, with a clear clue and a solved ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    clue = f["clue"]
    grownup = f["grownup"]

    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and the compost bin?",
            answer=f"It is a small mystery story with dialogue and problem solving, where {hero.id} looks carefully at a compost clue.",
        ),
        QAItem(
            question=f"What clue did {hero.id} examine to solve the problem?",
            answer=f"{hero.id} examined {clue.label}, and that clue helped show what really happened near the compost.",
        ),
        QAItem(
            question=f"Why did {grownup.label} and {hero.id} talk instead of guessing right away?",
            answer=f"They talked so they could compare clues, rule out wrong ideas, and solve the mystery carefully.",
        ),
        QAItem(
            question=f"What happened to the peanut snack in the story?",
            answer=f"The peanut snack was eaten near the bench, and the shell or crumbs helped explain the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is compost?",
            answer="Compost is old plant scraps and food scraps breaking down into dark soil that helps gardens grow.",
        ),
        QAItem(
            question="What is vocabulary?",
            answer="Vocabulary means the words a person knows and uses.",
        ),
        QAItem(
            question="What is a peanut?",
            answer="A peanut is a small edible seed that people often eat as a snack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is relevant when it points to the action or to the peanut.
relevant(C) :- clue(C), suspicious(C).
relevant(word_card) :- clue(word_card).

% The mystery is valid if the setting can host the action and a clue fits.
valid_story(S,A,C) :- setting(S), action(A), clue(C), compatible(S,A,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, loc in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if loc.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.suspicious:
            lines.append(asp.fact("suspicious", cid))
    for sid, aid, cid in valid_combos():
        lines.append(asp.fact("compatible", sid, aid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return sorted(valid_combos())


def asp_verify() -> int:
    import asp
    py = set(asp_valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    expected = py
    if cl == expected:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - expected:
        print("  only in clingo:", sorted(cl - expected))
    if expected - cl:
        print("  only in python:", sorted(expected - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: compost, vocabulary, peanut, and a small mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = valid_combos()
    if args.place is not None:
        combos = [c for c in combos if c[0] == args.place]
    if args.action is not None:
        combos = [c for c in combos if c[1] == args.action]
    if args.clue is not None:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, action, clue = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, action=action, clue=clue, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], CLUES[params.clue], params.name, params.gender, params.parent)
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
    StoryParams(setting="garden", action="compost_mystery", clue="peanut_shell", name="Mina", gender="girl", parent="mother"),
    StoryParams(setting="backyard", action="compost_mystery", clue="crumb_trail", name="Ezra", gender="boy", parent="father"),
    StoryParams(setting="kitchen", action="vocabulary_sorting", clue="word_card", name="June", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print("  ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.setting} (clue: {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
