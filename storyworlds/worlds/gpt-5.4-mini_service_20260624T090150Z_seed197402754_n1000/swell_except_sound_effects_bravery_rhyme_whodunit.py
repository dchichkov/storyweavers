#!/usr/bin/env python3
"""
A small whodunit-style storyworld about a child detective, a swelling clue,
sound effects, rhyme, and a brave little reveal.

Premise:
- A curious child hears odd sounds in a quiet place and notices one clue that
  keeps swelling with importance.
- The child investigates by comparing sounds, matching rhymes, and asking who
  could have moved the missing thing.

Tension:
- Every suspect has a reason to seem guilty except one, and the wrong clue
  sounds convincing at first.
- The hero must stay brave enough to keep looking.

Turn:
- The clue that swelled points to a harmless explanation: a little animal, a
  windy corner, or a dropped toy depending on the chosen setup.

Resolution:
- The hero solves the mystery, explains it clearly, and ends with a tidy image
  proving the truth.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    sounds: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    sound: str
    rhyme: str
    swells_with: str
    points_to: str
    innocent_explanation: str
    suspicious: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    sound: str
    rhyme: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", sounds=["rustle", "tap", "swish"]),
    "kitchen": Setting(place="the kitchen", mood="busy", sounds=["clink", "sizzle", "plink"]),
    "garden": Setting(place="the garden", mood="still", sounds=["buzz", "swish", "pat"]),
}

CLUES = {
    "clock": Clue(
        id="clock",
        label="the little clock",
        kind="clock",
        sound="tick-tick",
        rhyme="lock",
        swells_with="attention",
        points_to="wind",
        innocent_explanation="A draft nudged the clock and made it tick louder.",
        suspicious="It sounded like somebody sneaking around.",
    ),
    "cookie": Clue(
        id="cookie",
        label="the crumbly cookie tin",
        kind="tin",
        sound="clang",
        rhyme="swing",
        swells_with="rumble",
        points_to="cat",
        innocent_explanation="A hungry cat bumped the tin while chasing a ribbon.",
        suspicious="It looked like someone had opened it in secret.",
    ),
    "balloon": Clue(
        id="balloon",
        label="the round balloon",
        kind="balloon",
        sound="fwoomp",
        rhyme="moon",
        swells_with="air",
        points_to="fan",
        innocent_explanation="The fan puffed air and made the balloon lift and sway.",
        suspicious="It floated like a clue from a sneaky party.",
    ),
    "shoe": Clue(
        id="shoe",
        label="the muddy shoe",
        kind="shoe",
        sound="plop",
        rhyme="blue",
        swells_with="mud",
        points_to="duck",
        innocent_explanation="A duck stepped in a puddle and left the shoe near the door.",
        suspicious="It looked like a thief had hurried away.",
    ),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", type="cat", alibi="it was napping on a rug", sound="mrrp", rhyme="hat"),
    "wind": Suspect(id="wind", label="the wind", type="wind", alibi="it was slipping through a crack", sound="whoosh", rhyme="window"),
    "fan": Suspect(id="fan", label="the fan", type="fan", alibi="it was spinning by the table", sound="whirr", rhyme="pan"),
    "duck": Suspect(id="duck", label="the duck", type="duck", alibi="it was paddling near the steps", sound="quack", rhyme="luck"),
}

HERO_NAMES = ["Mila", "Noah", "Tess", "Ivy", "Leo", "Nia", "Owen", "Ruby"]
TRAITS = ["brave", "curious", "quick", "sharp", "calm", "kind"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with sound effects, bravery, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def rhyme_word(word: str) -> str:
    return word


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, trait=trait)


def hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.name, hero_type(params.gender), params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def tell(setting: Setting, clue: Clue, name: str, gender_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender_type, traits=["little", trait, "brave"]))
    world.facts["hero"] = hero
    world.facts["clue"] = clue
    world.facts["setting"] = setting

    suspect = SUSPECTS[clue.points_to]
    world.facts["suspect"] = suspect

    world.say(
        f"{name} was a little {trait} {gender_type} who loved a good mystery."
    )
    world.say(
        f"At {setting.place}, the air felt {setting.mood}, and every small sound seemed to matter."
    )
    world.say(
        f"{name} heard {clue.sound} from {clue.label}; the sound had a rhyme with '{clue.rhyme}', which made {name} pause."
    )
    world.say(
        f"Something about it felt like it could {clue.swells_with}, and the clue seemed to swell in {name}'s mind."
    )

    world.para()
    world.say(
        f"Then came a second sound: {setting.sounds[0]}! {name} looked toward the corner and saw {suspect.label}."
    )
    world.say(
        f"It was a tempting suspect because {suspect.alibi}, but the sound was not a real confession."
    )
    world.say(
        f"{name} kept brave and listened again. {name} could hear {suspect.sound}, but that did not match the first clue."
    )

    world.para()
    world.say(
        f"{name} checked the room, one clue at a time. {name} noticed that {clue.label} was close to {setting.place}."
    )
    world.say(
        f"At last, {name} found the honest answer: {clue.innocent_explanation}"
    )
    world.say(
        f"So the mystery was solved, and the suspicious story turned out to be only {clue.suspicious.lower()}"
    )

    world.para()
    world.say(
        f"{name} smiled, because being brave had helped {name} tell the truth from the trick."
    )
    world.say(
        f"By the end, {clue.label} was calm again, {setting.place} was tidy, and the last little sound was only a gentle {setting.sounds[-1]}."
    )

    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    hero: Entity = f["hero"]
    setting: Setting = f["setting"]
    return [
        f"Write a short whodunit for a child named {hero.id} set in {setting.place} that includes the sound effect {clue.sound}.",
        f"Tell a brave little mystery story where a clue rhymes with '{clue.rhyme}' and the answer turns out harmless.",
        f"Write a rhyme-tinted detective story about {hero.id}, a swelling clue, and a surprise that is not truly guilty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    suspect: Suspect = f["suspect"]
    return [
        QAItem(
            question=f"Where did {hero.id} hear the first odd sound?",
            answer=f"{hero.id} heard the odd sound at {setting.place}, where the mystery began.",
        ),
        QAItem(
            question=f"What sound did the clue make?",
            answer=f"The clue made a {clue.sound} sound.",
        ),
        QAItem(
            question=f"Who seemed suspicious at first?",
            answer=f"{suspect.label} seemed suspicious at first, but that was not the true answer.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going?",
            answer=f"{hero.id}'s bravery helped {hero.id} keep listening and solving the mystery.",
        ),
        QAItem(
            question=f"What was the real explanation for the clue?",
            answer=clue.innocent_explanation,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps a detective figure out what happened.",
        ),
        QAItem(
            question="Why do sound effects matter in a whodunit?",
            answer="Sound effects matter because they can hint at who moved, bumped, or dropped something.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means staying steady and trying hard even when something feels tricky or scary.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when two words sound alike at the end, like moon and tune.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place} in this story?",
            answer=f"{setting.place.capitalize()} is a quiet place where a small mystery can be heard clearly.",
        ),
        QAItem(
            question=f"Why might something '{clue.swells_with}' in a mystery?",
            answer=f"It can feel bigger and more important as more clues point toward the answer.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


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


ASP_RULES = r"""
clue_in_place(C, S) :- clue(C), setting(S), clue_setting(C, S).
odd_sound(C) :- clue(C).
brave(H) :- hero(H).
solved(C) :- clue(C), clue_answer(C, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_setting", cid, clue.points_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show clue_in_place/2."))
    atoms = set(asp.atoms(model, "clue_in_place"))
    py = {(cid, clue.points_to) for cid, clue in CLUES.items()}
    if atoms == py:
        print(f"OK: clingo gate matches Python facts ({len(atoms)} clues).")
        return 0
    print("MISMATCH between clingo and Python facts.")
    print("clingo only:", sorted(atoms - py))
    print("python only:", sorted(py - atoms))
    return 1


def build_parser_for_asp() -> argparse.ArgumentParser:
    return build_parser()


CURATED = [
    StoryParams(setting="library", clue="clock", name="Mila", gender="girl", trait="brave"),
    StoryParams(setting="kitchen", clue="cookie", name="Leo", gender="boy", trait="curious"),
    StoryParams(setting="garden", clue="shoe", name="Tess", gender="girl", trait="sharp"),
]


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
        print(asp_program("#show clue_in_place/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}")
        model = asp.one_model(asp_program("#show clue_in_place/2."))
        print(sorted(asp.atoms(model, "clue_in_place")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
