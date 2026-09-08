#!/usr/bin/env python3
"""
Story world: Curiosity investigates a strange swim-school mystery.

The story begins with a small task, a safe reminder about novocaine, and a
curious detective-style search. Curiosity learns that careful questions and
kind teamwork solve more than hurried guesses.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"pool_distance": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "confidence": 0.0}
    )


@dataclass
class Object:
    name: str
    label: str
    kind: str
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(
        default_factory=lambda: {"pool_distance": 0.0, "depth": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"importance": 0.0}
    )


@dataclass
class World:
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper_name: str = "Coach Mira"
    item_name: str = "blue swim badge"
    witness_name: str = "Pip"
    setting: str = "swim school"


@dataclass(frozen=True)
class CaseArc:
    key: str
    opening_clue: str
    wrong_move: str
    consequence: str
    careful_method: str
    cause: str
    recovery: str
    lesson: str
    ending_image: str


CASE_ARCS = [
    CaseArc(
        key="locker_echo",
        opening_clue="a soft clink echoed from the row of lockers after everyone had left the changing room",
        wrong_move="opened every locker at once and scattered towels across the benches",
        consequence="the noise grew louder, but the badge was still missing and the changing room became hard to search",
        careful_method="listened at each locker with one ear while the coach kept the room quiet",
        cause="the badge had slipped through a vent in a locker door and landed in the empty basket beneath it",
        recovery="lifted the basket carefully and used a towel to draw the badge out",
        lesson="a detective changes one thing at a time so clues do not get mixed up",
        ending_image="the towels were folded again, and the blue badge shone on the coach's clipboard",
    ),
    CaseArc(
        key="kickboard_trail",
        opening_clue="three wet crescent marks curved away from the kickboards toward the shallow end",
        wrong_move="followed the marks at a run and kicked the whole stack of boards apart",
        consequence="water splashed over the floor and erased the last mark",
        careful_method="placed dry markers beside each remaining crescent and compared their direction",
        cause="a loose strap on the badge bag had dragged through the water behind a floating kickboard",
        recovery="asked a grown-up to lift the kickboard while Luna reached with the pool net",
        lesson="curiosity works best when it protects the clues it is following",
        ending_image="the kickboards stood in a neat rainbow while drops sparkled on the restored badge bag",
    ),
    CaseArc(
        key="whistle_pattern",
        opening_clue="the safety whistle gave one tiny chirp whenever the lane rope bumped the wall",
        wrong_move="blew several loud whistles to make the hidden object answer",
        consequence="everyone covered their ears and the useful little pattern disappeared",
        careful_method="waited for the pool to grow quiet and counted the lane-rope bumps",
        cause="the badge had caught on a lane-rope float, which tapped the wall in a regular rhythm",
        recovery="stopped the lesson safely and used the long pool hook to bring the float close",
        lesson="patient listening can turn a strange sound into a useful clue",
        ending_image="the lane rope rested still, and the badge hung beside the whistle in a bright little pair",
    ),
    CaseArc(
        key="towel_shadow",
        opening_clue="a silver shape appeared beneath the towel cart whenever the overhead lights moved",
        wrong_move="pulled every towel out to chase the shape",
        consequence="the cart rolled a little, and a tall pile of towels leaned dangerously",
        careful_method="held the cart steady and watched the shadow from three safe places",
        cause="the badge was caught on the cart's lower wheel, reflecting light across the tiles",
        recovery="asked the coach to lock the cart before sliding the badge free with a ruler",
        lesson="safety comes before solving, especially when a clue is near heavy equipment",
        ending_image="the towel cart was locked in place, its clean stack crowned by the recovered badge",
    ),
    CaseArc(
        key="novocaine_note",
        opening_clue="a folded health note sat beside the first-aid box, while a shiny badge was nowhere on the sign-in table",
        wrong_move="guessed that the note and badge belonged to the same mystery and carried the first-aid box across the room",
        consequence="the box blocked the walkway and the guess explained nothing",
        careful_method="asked the coach what the note meant before touching medical supplies",
        cause="the note was only a reminder that novocaine belongs to a qualified health professional, not a swim-school game; the badge had slipped behind the sign-in folder",
        recovery="returned the first-aid box to its safe place and lifted the folder with the coach",
        lesson="good detectives ask what a clue means instead of inventing a frightening connection",
        ending_image="the health note stayed beside the first-aid box while the blue badge marked the day's finished task",
    ),
]


NAMES = ["Luna", "Milo", "Nia", "Tess", "Owen"]
HELPERS = ["Coach Mira", "Coach Sam", "Coach Jo", "Coach Ada"]
ITEMS = ["blue swim badge", "silver lane token", "yellow star clip", "red diving ring"]
WITNESSES = ["Pip", "Bubbles", "Kai", "Rae"]

OPENINGS = [
    "On a bright afternoon",
    "Before the last lesson of the day",
    "While sunlight trembled on the pool",
    "Just after the beginner class climbed out",
]

DIALOGUES = [
    (
        '"Every case begins with a question," {hero} said.',
        '"Then ask one that keeps everyone safe," replied {helper}.',
    ),
    (
        '"I have a clue, but not an answer," {hero} whispered.',
        '"Good detectives separate those two things," said {helper}.',
    ),
    (
        '"May I check the evidence again?" {hero} asked.',
        '"Yes," said {helper}. "Carefully, and with a partner."',
    ),
]


def build_world(params: StoryParams) -> World:
    if params.setting != "swim school":
        raise StoryError("This storyworld is set only in swim school.")
    world = World(setting=params.setting)
    hero = world.add_character(
        Character(params.name, "curious young detective", "learner")
    )
    helper = world.add_character(
        Character(params.helper_name, "patient swim coach", "grown-up")
    )
    witness = world.add_character(
        Character(params.witness_name, "young swimmer", "witness")
    )
    item = world.add_object(
        Object(params.item_name, params.item_name, "badge", hidden=True)
    )
    health_note = world.add_object(
        Object("novocaine health note", "novocaine health note", "safety note")
    )
    world.facts.update(hero=hero, helper=helper, witness=witness, item=item, health_note=health_note)
    return world


def narrate_story(world: World, seed: int) -> None:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    witness: Character = world.facts["witness"]
    item: Object = world.facts["item"]
    note: Object = world.facts["health_note"]

    rng = random.Random(seed ^ 0x29A7C1)
    arc = rng.choice(CASE_ARCS)
    opening = rng.choice(OPENINGS)
    hero_line, helper_line = rng.choice(DIALOGUES)
    detective_tool = rng.choice(
        [
            "a small notebook",
            "three dry pool markers",
            "a pencil and a folded lesson map",
            "a row of bottle caps",
        ]
    )

    hero.memes["curiosity"] += 1.0
    world.facts.update(arc=arc, tool=detective_tool)

    world.say(f"{opening}, {hero.name} arrived at the swim school for a simple task.")
    world.say(
        f"The task was to help {helper.name} check the lesson table before the next swimmers arrived."
    )
    world.say(
        f"{hero.name} loved Curiosity, the bright feeling that makes a person notice small details and ask kind questions."
    )
    world.say(
        f"Then {arc.opening_clue}. The {item.label} for the class was missing."
    )
    world.say(
        f"Near the sign-in table, {hero.name} also noticed a {note.label}. It mentioned novocaine, so {helper.name} explained that medical numbing medicine belongs with qualified health professionals and was not part of a pool game."
    )

    world.para()
    world.say(hero_line.format(hero=hero.name, helper=helper.name))
    world.say(f"{hero.name} {arc.wrong_move}.")
    hero.memes["worry"] += 1.0
    world.say(f"{arc.consequence}.")
    world.say(
        f"{witness.name} watched from the bench and said, \"The first guess made the clues harder to see.\""
    )

    world.para()
    world.say(
        f"{helper.name} joined the search and asked {hero.name} to describe exactly what had been noticed."
    )
    world.say(helper_line.format(hero=hero.name, helper=helper.name))
    world.say(
        f"Together, {hero.name} and {helper.name} used {detective_tool} and {arc.careful_method}."
    )
    world.say(
        f"{witness.name} pointed toward the last clear clue. \"That mark was there before the towels moved,\" {witness.name} said."
    )
    world.say(f"The careful pattern revealed the cause: {arc.cause}.")

    world.para()
    item.hidden = False
    item.found = True
    item.memes["importance"] = 1.0
    hero.memes["confidence"] += 1.0
    world.say(f"To finish the task, {hero.name} {arc.recovery}.")
    world.say(
        f"The recovered {item.label} proved that the mystery had been solved with evidence, not a lucky guess."
    )
    world.say(f"{hero.name} learned that {arc.lesson}.")
    world.say(
        f"At the next lesson, {arc.ending_image}. {hero.name} felt Curiosity glow calmly, ready for another safe question."
    )


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    item: Object = world.facts["item"]
    return [
        f"Write a detective story for children about {hero.name} completing a task at swim school.",
        f"Include a missing {item.label}, Curiosity, a safe explanation of novocaine, and a careful investigation.",
        "Show a wrong guess, a clue-based turn, brief dialogue, and an ending image proving what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    item: Object = world.facts["item"]
    arc: CaseArc = world.facts["arc"]
    return [
        QAItem(
            question=f"What task did {hero.name} have at swim school?",
            answer=f"{hero.name} helped {helper.name} check the lesson table before the next swimmers arrived.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing object was the {item.label}.",
        ),
        QAItem(
            question="How was novocaine connected to the story?",
            answer="A health note mentioned novocaine, and the coach explained that it is medical numbing medicine for qualified health professionals, not part of a swim-school game.",
        ),
        QAItem(
            question=f"What mistake did {hero.name} make first?",
            answer=f"{hero.name} {arc.wrong_move}. That made the clues harder to see.",
        ),
        QAItem(
            question="What lesson did Curiosity help the detective learn?",
            answer=f"The lesson was that {arc.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swim school?",
            answer="A swim school is a place where learners practice water skills with trained instructors and safety rules.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is a wish to notice, ask questions, and learn more.",
        ),
        QAItem(
            question="Why should a detective protect clues?",
            answer="Protecting clues keeps important evidence from being changed or mixed up before it can be understood.",
        ),
        QAItem(
            question="What is novocaine?",
            answer="Novocaine is a name associated with a local anesthetic used by qualified medical or dental professionals to numb an area. It is not a toy, game prop, or swim-school treatment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(swim_school).
hero(H) :- hero_name(H).
coach(C) :- coach_name(C).
badge(B) :- badge_name(B).
missing(B) :- badge(B), hidden(B).
safe_search(H) :- hero(H), clue_protected(H), coach_present.
task_complete(H) :- hero(H), safe_search(H), found_badge.
curiosity_used(H) :- hero(H), asked_question(H).
novocaine_note_present :- safety_note(novocaine).

#show setting/1.
#show missing/1.
#show safe_search/1.
#show task_complete/1.
#show curiosity_used/1.
#show novocaine_note_present/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("coach_name", "coach_mira"),
            asp.fact("badge_name", "blue_swim_badge"),
            asp.fact("hidden", "blue_swim_badge"),
            asp.fact("coach_present"),
            asp.fact("clue_protected", "luna"),
            asp.fact("found_badge"),
            asp.fact("asked_question", "luna"),
            asp.fact("safety_note", "novocaine"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = """
#show setting/1.
#show missing/1.
#show safe_search/1.
#show task_complete/1.
#show curiosity_used/1.
#show novocaine_note_present/0.
"""
    model = asp.one_model(asp_program(show))
    actual = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("setting", ("swim_school",)),
        ("missing", ("blue_swim_badge",)),
        ("safe_search", ("luna",)),
        ("task_complete", ("luna",)),
        ("curiosity_used", ("luna",)),
        ("novocaine_note_present", ()),
    }
    if actual == expected:
        sample = generate(StoryParams(seed=17))
        required = ["novocaine", "task", "Curiosity", "swim school"]
        if all(word.lower() in sample.story.lower() for word in required):
            print("OK: ASP/Python parity and story exercise passed.")
            return 0
        print("MISMATCH: generated story omitted a required narrative instrument.")
        return 1
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(actual))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Curiosity detective story at swim school."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--item", dest="item_name", choices=ITEMS)
    parser.add_argument("--witness", choices=WITNESSES)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        item_name=args.item_name or rng.choice(ITEMS),
        witness_name=args.witness or rng.choice(WITNESSES),
        setting="swim school",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: role={character.role} "
            f"meters={dict(character.meters)} memes={dict(character.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: kind={obj.kind} hidden={obj.hidden} found={obj.found} "
            f"meters={dict(obj.meters)} memes={dict(obj.memes)}"
        )
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(
            asp_program(
                """
#show setting/1.
#show missing/1.
#show safe_search/1.
#show task_complete/1.
#show curiosity_used/1.
#show novocaine_note_present/0.
"""
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                """
#show setting/1.
#show missing/1.
#show safe_search/1.
#show task_complete/1.
#show curiosity_used/1.
#show novocaine_note_present/0.
"""
            )
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(
                seed=base_seed,
                name="Luna",
                helper_name="Coach Mira",
                item_name="blue swim badge",
                witness_name="Pip",
            ),
            StoryParams(
                seed=base_seed + 1,
                name="Milo",
                helper_name="Coach Sam",
                item_name="silver lane token",
                witness_name="Bubbles",
            ),
            StoryParams(
                seed=base_seed + 2,
                name="Nia",
                helper_name="Coach Jo",
                item_name="yellow star clip",
                witness_name="Kai",
            ),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
