#!/usr/bin/env python3
"""A small detective-story world with a bad ending.

A child-friendly detective notices a strange thunk, follows clues, and tries to
restore accord between two friends or neighbors. The twist is that the final
choice goes wrong: the clue is misread, the wrong person is blamed, and the
ending leaves the neighborhood feeling off-balance.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # detective | suspect | witness | thing
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"detective", "suspect", "witness"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the little station"
    clue_place: str = "the alley"
    object_name: str = "tin box"
    sound: str = "thunk"
    accord_word: str = "accord"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    detective_name: str
    suspect_name: str
    witness_name: str
    place: str = "the little station"
    clue_place: str = "the alley"
    sound: str = "thunk"
    object_name: str = "tin box"
    case_id: int = 0
    opening_id: int = 0
    inquiry_id: int = 0
    dialogue_id: int = 0
    mistake_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


PLACES = {
    "the little station": Scene(place="the little station", clue_place="the alley", object_name="tin box", sound="thunk", accord_word="accord"),
    "the market corner": Scene(place="the market corner", clue_place="the stairwell", object_name="wooden crate", sound="thunk", accord_word="accord"),
    "the school yard": Scene(place="the school yard", clue_place="the shed", object_name="lunch pail", sound="thunk", accord_word="accord"),
}

DETECTIVE_NAMES = ["Mina", "Noel", "Tess", "Ivy", "Rowan", "Pip", "June", "Eli"]
SUSPECT_NAMES = ["Mr. Bell", "Aunt Ora", "Benji", "Nina", "Coach Sam", "Mrs. Lane"]
WITNESS_NAMES = ["Lulu", "Omar", "Ria", "Tom", "Mila", "Jae"]

CASES = [
    {
        "premise": "Neighbors were arranging a welcome display, and the last bundle of paper stars was stored in the {object}.",
        "witness": "{W} said the {object} jumped when a delivery cart passed.",
        "clue": "a strip of blue wool snagged on the lid",
        "suspicion": "{S}'s blue scarf",
        "truth": "the wool had torn from the cart driver's blanket",
        "proof": "a matching ragged corner still hung from the cart",
        "consequence": "The welcome display opened with a bare patch where the stars should have shone",
    },
    {
        "premise": "A jar of concert tickets vanished just before the children's music night, and the empty {object} rocked beside the wall.",
        "witness": "{W} remembered seeing {S} carry chairs past the {object}.",
        "clue": "a curl of silver ribbon under one corner",
        "suspicion": "the silver ribbon on {S}'s chair bundle",
        "truth": "a gust had rolled the ticket jar behind a curtain",
        "proof": "the jar made the same {sound} when the curtain tugged it back",
        "consequence": "The first song began before the waiting families received their tickets",
    },
    {
        "premise": "The seed-swap table needed its label cards, but they disappeared after a {sound} rattled the {object}.",
        "witness": "{W} had noticed muddy half-moons leading toward {S}.",
        "clue": "three muddy marks shaped like small heels",
        "suspicion": "the mud on {S}'s boots",
        "truth": "the marks came from a toppled flowerpot's curved rim",
        "proof": "the broken pot made identical half-moons in damp soil",
        "consequence": "Gardeners went home with seed packets whose names had been mixed up",
    },
    {
        "premise": "A painted direction sign fell moments before the neighborhood walk, landing beside the {object} with a {sound}.",
        "witness": "{W} said {S} had complained that the arrow pointed the wrong way.",
        "clue": "a short red thread caught on the signpost",
        "suspicion": "a red patch on {S}'s sleeve",
        "truth": "the thread came from a kite that had wrapped around the loose sign",
        "proof": "the kite's tail was missing one short red tassel",
        "consequence": "The walkers followed the fallen arrow and missed the lantern garden",
    },
    {
        "premise": "Two friends had promised to share a model bridge, but one wooden span disappeared from the open {object}.",
        "witness": "{W} heard the {sound} just after {S} borrowed a ruler.",
        "clue": "a dusting of pale sawdust near the latch",
        "suspicion": "the sawdust on {S}'s ruler case",
        "truth": "a mouse had dragged the light span behind a stack of boards",
        "proof": "tiny tooth marks crossed the hidden span",
        "consequence": "The bridge display sagged between its towers, and the two builders stood apart",
    },
    {
        "premise": "The town's accord bell was due to ring, yet its padded striker was missing from the {object}.",
        "witness": "{W} saw {S} reach near the bell rope before the {sound}.",
        "clue": "a smudge of green chalk on the clasp",
        "suspicion": "green chalk on {S}'s fingers",
        "truth": "the caretaker had moved the striker while marking a repair",
        "proof": "a chalk arrow beneath the shelf pointed to its safe hiding place",
        "consequence": "The hour for the accord bell passed in an uncomfortable silence",
    },
    {
        "premise": "A box of apology notes was meant to settle a playground quarrel, but the {object} tipped and the notes vanished.",
        "witness": "{W} said {S} had walked away from the writing table in a hurry.",
        "clue": "a square crease pressed into the dust",
        "suspicion": "the square notebook in {S}'s pocket",
        "truth": "the notes had slid through a gap into a folded tablecloth",
        "proof": "one paper corner peeked from the cloth's hem",
        "consequence": "The two quarreling teams left without reading one another's apologies",
    },
    {
        "premise": "The shared supper could not begin because the recipe card was gone from the {object} after a hollow {sound}.",
        "witness": "{W} recalled {S} saying the soup needed a different herb.",
        "clue": "a crushed leaf beside the handle",
        "suspicion": "the same herb tucked into {S}'s basket",
        "truth": "the recipe had stuck to the damp bottom of a serving tray",
        "proof": "backward letters from the card showed through the wet tray",
        "consequence": "The supper tables stayed empty while everyone argued about the missing recipe",
    },
    {
        "premise": "Children had built a message lantern for the evening parade, but its paper moon was gone when the {object} gave a {sound}.",
        "witness": "{W} had seen {S} fold a pale piece of paper nearby.",
        "clue": "a sprinkle of gold paste on the floor",
        "suspicion": "gold paste on {S}'s cuff",
        "truth": "the moon had clung to the back of a drying poster",
        "proof": "its round outline gleamed through the poster paper",
        "consequence": "The parade started with a dark lantern at its front",
    },
    {
        "premise": "A borrowed puzzle piece was due back before closing, but only the shut {object} remained after a sharp {sound}.",
        "witness": "{W} thought {S} had slipped something bright into a pocket.",
        "clue": "a tiny triangle of yellow card by the hinge",
        "suspicion": "a yellow library card in {S}'s pocket",
        "truth": "the puzzle piece had wedged beneath the {object}'s false bottom",
        "proof": "tilting the box made the hidden piece answer with a faint scrape",
        "consequence": "The puzzle's owner carried home an unfinished picture and no explanation",
    },
]

OPENINGS = [
    "{D} kept a notebook of small mysteries, but had never solved one with so many neighbors watching.",
    "Whenever neighbors disagreed at {place}, {D} listened for the detail everyone else had missed.",
    "{D}, the youngest detective near {place}, believed accord began with patient questions.",
    "Rain had polished the stones around {place} when {D} arrived with a pencil and a promise to be fair.",
    "A community notice at {place} asked for a careful detective, so {D} buttoned a little clue pouch and came running.",
    "The day had begun peacefully at {place}; {D} hoped to help it end in accord too.",
    "{D} was drawing a map of {place} when a worried crowd gathered around the detective's table.",
    "At {place}, people trusted {D} to notice quiet truths hidden beneath noisy guesses.",
]

INQUIRIES = [
    "{D} measured the clue, sketched where everyone had stood, and asked for the story in reverse.",
    "{D} rolled the {object} gently, compared its sound with the first {sound}, and checked the floor for a second trail.",
    "{D} made a timeline on three cards, but placed {S}'s card before checking the final minute.",
    "{D} inspected the latch with a magnifying glass and asked {W} to demonstrate exactly where the noise began.",
    "{D} dusted the clue with flour, held it to the light, and searched nearby corners for a matching mark.",
    "{D} asked each person the same three questions, then tested which nearby object could make a similar {sound}.",
    "{D} traced a circle around the clue, checked the wind, and listened beside the {object} without touching it.",
    "{D} photographed the scene in a notebook, examined the clue's edges, and asked what had changed since morning.",
    "{D} counted the steps from {clue_place}, tested the loose floorboards, and compared every answer twice.",
    "{D} tied a string from the clue to the {object}, hoping the straight line would reveal a simple answer.",
]

DIALOGUES = [
    ('"Please test the clue before you name anyone," {W} whispered.', '"It points straight to {S}," {D} replied, though one question remained.'),
    ('"I was nearby, but that is not the same as causing it," said {S}.', '"Nearby is enough for now," {D} said, closing the notebook.'),
    ('"Could two things leave the same mark?" {W} asked.', '"Not this time," said {D}, more certain than the evidence allowed.'),
    ('"Let me explain the last minute," {S} began.', '"The clue has already explained it," {D} answered.'),
    ('"Accord needs everyone to be heard," {W} reminded the detective.', '"We need an answer before we need another story," {D} said.'),
    ('"What if the {sound} came first and the clue came later?" asked {S}.', '"That would make everything harder," {D} admitted, and chose the easier guess.'),
    ('"There may be a second trail," said {W}.', '"One trail is plenty," {D} replied, pointing toward {S}.'),
    ('"Your map has an empty corner," {S} said softly.', '"Empty corners do not solve cases," {D} said, folding the map.'),
]

MISTAKES = [
    "Wanting the crowd to stop worrying, {D} treated {suspicion} as proof and publicly blamed {S}.",
    "When two neighbors demanded an answer, {D} skipped the last test and declared that {S} had caused the trouble.",
    "{D} circled {S}'s name in the notebook, mistaking a possible connection for a certain one.",
    "Because the clue fit the first guess neatly, {D} ignored the part of {W}'s account that did not fit and accused {S}.",
    "The fading daylight made {D} hurry; the detective announced {S}'s guilt before examining the clue's other side.",
    "{D} asked the crowd for a show of hands, and their worried guesses pushed the detective into blaming {S}.",
    "Instead of repeating the sound test, {D} trusted memory and told everyone that {S} was responsible.",
    "{D} saw {S} hesitate, called that hesitation suspicious, and made the accusation too soon.",
]

ENDINGS = [
    "But by then {S} had gone home unheard. {consequence}. {D}'s unopened apology lay beside the {object} as its lid settled with one last {sound}.",
    "{S} would not return that evening, and accord did not return either. {consequence}.",
    "The detective erased the accusation, but could not erase the hurt it had caused. {consequence}.",
    "The crowd drifted away before {D} could correct the story. No one was harmed, yet the unfair blame remained uncorrected that night. {consequence}.",
    "The discovery came after {S} had stopped answering the detective's questions. {consequence}. The clue notebook closed on a page with no accord at the bottom.",
    "The real explanation was gentle; the rushed accusation was not. {consequence}, while {S}'s empty place showed what the mistake had cost.",
    "{D} wrote 'I was wrong,' but {S} was no longer there to read it. {consequence}.",
    "The mystery was solved too late to mend the evening: {consequence}. {D} walked home carrying a very heavy, very quiet notebook.",
]


ASP_RULES = r"""
place(P) :- place_name(P).
clue(C) :- clue_name(C).
sound(S) :- sound_name(S).
object(O) :- object_name(O).

heard_thunk(D) :- detective(D), sound(S), thunk_sound(S), hears(D, S).
has_clue(D) :- heard_thunk(D), clue_found(D).
bad_ending :- wrong_blame.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    lines.append(asp.fact("sound_name", "thunk"))
    lines.append(asp.fact("thunk_sound", "thunk"))
    for obj in {s.object_name for s in PLACES.values()}:
        lines.append(asp.fact("object_name", obj))
    for c in {s.clue_place for s in PLACES.values()}:
        lines.append(asp.fact("clue_name", c))
    lines.append(asp.fact("detective", "detective"))
    lines.append(asp.fact("hears", "detective", "thunk"))
    lines.append(asp.fact("clue_found", "detective"))
    lines.append(asp.fact("wrong_blame"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show bad_ending/0."))
    atoms = {str(a) for a in model}
    ok = "bad_ending" in atoms
    if ok:
        print("OK: ASP model confirms the bad ending.")
        return 0
    print("MISMATCH: ASP did not produce the expected bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--detective-name")
    ap.add_argument("--suspect-name")
    ap.add_argument("--witness-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    suspect_name = args.suspect_name or rng.choice(SUSPECT_NAMES)
    witness_name = args.witness_name or rng.choice(WITNESS_NAMES)
    if detective_name == suspect_name:
        raise StoryError("The detective and suspect must be different people.")
    if detective_name == witness_name or suspect_name == witness_name:
        raise StoryError("The witness must be a different person from the detective and suspect.")
    return StoryParams(
        detective_name=detective_name,
        suspect_name=suspect_name,
        witness_name=witness_name,
        place=scene.place,
        clue_place=scene.clue_place,
        sound=scene.sound,
        object_name=scene.object_name,
        case_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        inquiry_id=rng.randrange(len(INQUIRIES)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        mistake_id=rng.randrange(len(MISTAKES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = CASES[params.case_id % len(CASES)]
    world = World(scene)
    det = world.add(Entity(id="det", kind="detective", label=params.detective_name, role="detective"))
    sus = world.add(Entity(id="sus", kind="suspect", label=params.suspect_name, role="suspect"))
    wit = world.add(Entity(id="wit", kind="witness", label=params.witness_name, role="witness"))

    det.memes["curious"] = 1
    det.memes["hope"] = 1
    sus.memes["nervous"] = 1
    wit.memes["uneasy"] = 1

    values = {
        "D": det.label,
        "S": sus.label,
        "W": wit.label,
        "place": scene.place,
        "clue_place": scene.clue_place,
        "object": scene.object_name,
        "sound": scene.sound,
        "suspicion": case["suspicion"].format(S=sus.label),
        "truth": case["truth"].format(
            object=scene.object_name, sound=scene.sound
        ),
        "proof": case["proof"].format(
            object=scene.object_name, sound=scene.sound
        ),
        "consequence": case["consequence"],
    }

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(**values))
    world.say(case["premise"].format(**values))
    world.say(
        f"Then a clear {scene.sound} came from {scene.clue_place}, and talk of "
        f"{scene.accord_word} gave way to worried guesses."
    )

    world.para()
    world.say(case["witness"].format(**values))
    world.say(
        f"Near the {scene.object_name}, {det.label} found {case['clue']}. "
        f"It seemed to match {values['suspicion']}."
    )
    world.say(INQUIRIES[params.inquiry_id % len(INQUIRIES)].format(**values))

    world.para()
    exchange = DIALOGUES[params.dialogue_id % len(DIALOGUES)]
    world.say(exchange[0].format(**values))
    world.say(exchange[1].format(**values))
    world.say(MISTAKES[params.mistake_id % len(MISTAKES)].format(**values))

    world.para()
    world.say(
        f"A late check showed that {values['truth']}; {values['proof']}."
    )
    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(**values))

    world.facts.update(
        detective=det,
        suspect=sus,
        witness=wit,
        place=scene.place,
        clue_place=scene.clue_place,
        object_name=scene.object_name,
        sound=scene.sound,
        accord_word=scene.accord_word,
        mystery=case["premise"].format(**values),
        witness_statement=case["witness"].format(**values),
        clue=case["clue"],
        suspicion=values["suspicion"],
        inquiry=INQUIRIES[params.inquiry_id % len(INQUIRIES)].format(**values),
        true_cause=values["truth"],
        proof=values["proof"],
        consequence=case["consequence"],
        wrong_blame=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    wit = f["witness"]
    return [
        f"Write a short detective story for a young child that includes '{f['sound']}', accord, and a gentle bad ending.",
        f"Tell how {det.label} investigates {f['clue']} at {f['place']} but unfairly suspects {sus.label}.",
        f"Write a mystery about {det.label}, {sus.label}, and {wit.label}. Reveal this truth too late: {f['true_cause']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    wit = f["witness"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det.label}. {det.label} listened for clues and tried to keep things calm.",
        ),
        QAItem(
            question="What clue made the detective suspicious?",
            answer=f"{det.label} found {f['clue']}. It seemed to match {f['suspicion']}, but that resemblance did not prove anything.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {det.label} blamed {sus.label} before finishing the investigation. In truth, {f['true_cause']}, and {f['consequence'].lower()}.",
        ),
        QAItem(
            question="What evidence showed the first guess was wrong?",
            answer=f"The later evidence was that {f['proof']}. It showed why the clue did not fairly point to {sus.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is an accord?",
            answer="Accord means people are getting along and agreeing with one another.",
        ),
        QAItem(
            question="What does thunk sound like?",
            answer="Thunk is a short, heavy sound, like something small bumping or falling onto wood or stone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} role={e.role} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(
        detective_name="Mina", suspect_name="Mr. Bell", witness_name="Lulu",
        place="the little station", clue_place="the alley", sound="thunk",
        object_name="tin box", case_id=0, opening_id=0, inquiry_id=0,
        dialogue_id=0, mistake_id=0, ending_id=0,
    ),
    StoryParams(
        detective_name="Tess", suspect_name="Aunt Ora", witness_name="Omar",
        place="the market corner", clue_place="the stairwell", sound="thunk",
        object_name="wooden crate", case_id=4, opening_id=3, inquiry_id=5,
        dialogue_id=3, mistake_id=4, ending_id=3,
    ),
    StoryParams(
        detective_name="Ivy", suspect_name="Mrs. Lane", witness_name="Ria",
        place="the school yard", clue_place="the shed", sound="thunk",
        object_name="lunch pail", case_id=8, opening_id=6, inquiry_id=8,
        dialogue_id=6, mistake_id=7, ending_id=7,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show bad_ending/0."))
        print("bad ending atoms:", asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
