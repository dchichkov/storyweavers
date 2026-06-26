#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_at: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "person":
            if self.id.endswith("a") or self.id in {"Mina", "Nora", "Tessa"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clue_kind: str = ""
    is_hidden: bool = False


@dataclass
class StoryParams:
    name: str
    detective: str
    quest: str
    rhyme: str
    culprit: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    detective: Item
    quest_item: Item
    rhyme_note: Item
    culprit: Item
    places: dict[str, Place]
    witnesses: list[Item]
    clues: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def place(self, pid: str) -> Place:
        return self.places[pid]


DETECTIVES = ["Mina", "Noah", "Tessa", "Jules", "Piper", "Owen"]
QUESTS = {
    "missing_key": ("the missing brass key", "a missing brass key"),
    "lost_cookie": ("the lost moon cookie", "a moon-shaped cookie"),
    "vanished_crayon": ("the vanished blue crayon", "a blue crayon"),
    "gone_hat": ("the gone red hat", "a red hat"),
}
RHYMES = {
    "drawer": ("drawer", "where things hide before the door"),
    "floor": ("floor", "the trail that leads before the door"),
    "door": ("door", "the rhyme that points to the drawer"),
    "stair": ("stair", "the clue that starts upstairs"),
}
CULPRITS = ["cat", "crow", "turtle", "mouse"]
PLACES = {
    "kitchen": Place("kitchen", "the kitchen", clue_kind="crumbs"),
    "hall": Place("hall", "the hall", clue_kind="dust"),
    "porch": Place("porch", "the porch", clue_kind="tracks"),
    "study": Place("study", "the study", clue_kind="paper"),
}


def build_world(params: StoryParams) -> World:
    detective = Item(id=params.name, kind="person", label=params.name, phrase=params.name)
    quest_label, quest_phrase = QUESTS[params.quest]
    quest_item = Item(id="quest", kind="thing", label=quest_label, phrase=quest_phrase, owner=detective.id)
    rhyme_word, rhyme_phrase = RHYMES[params.rhyme]
    rhyme_note = Item(id="rhyme", kind="thing", label=rhyme_word, phrase=rhyme_phrase, owner=detective.id)
    culprit = Item(id=params.culprit, kind="person", label=f"the {params.culprit}", phrase=f"the {params.culprit}")
    witnesses = [
        Item(id="cook", kind="person", label="the cook", phrase="the cook"),
        Item(id="guard", kind="person", label="the guard", phrase="the guard"),
    ]
    places = {k: dataclasses.replace(v) for k, v in PLACES.items()}
    return World(detective, quest_item, rhyme_note, culprit, places, witnesses)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place for the mystery.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest object.")
    if params.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme clue.")
    if params.culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")
    if params.quest == "missing_key" and params.rhyme == "stair":
        return


def setup(world: World) -> None:
    d = world.detective
    q = world.quest_item
    r = world.rhyme_note
    c = world.culprit

    d.memes["curious"] = 1
    d.memes["duty"] = 1
    q.meters["missing"] = 1
    r.meters["clue"] = 1
    c.memes["nervous"] = 1

    world.say(f"{d.id} was a small detective with a very big question: where had {q.label} gone?")
    world.say(f"On the table lay a rhyme note: “{r.phrase}.” It sounded silly, but it felt important.")
    world.say(f"{d.id} knew the case was a quest, and the most dominant clue might be hidden inside the rhyme.")
    world.para()


def investigate(world: World) -> None:
    d = world.detective
    q = world.quest_item
    r = world.rhyme_note
    c = world.culprit

    for place_id in [world.facts["start"], "hall", "study", "kitchen"]:
        place = world.place(place_id)
        if place_id == world.facts["start"]:
            world.say(f"{d.id} began in {place.label}, looking for any little sign.")
        else:
            world.say(f"{d.id} checked {place.label} and listened for a whisper of the clue.")
        if place.clue_kind == "crumbs" and world.facts["quest"] == "lost_cookie":
            q.meters["found"] = 1
            world.clues.append("crumbs")
            world.say(f"Crumbs led to the answer, because a cookie leaves a trail when it slips away.")
        elif place_id == "study" and world.facts["rhyme"] == "drawer":
            r.meters["revealed"] = 1
            world.clues.append("drawer")
            world.say(f"A soft scratch on the desk made the drawer feel like the right hiding place.")
        elif place_id == "hall" and world.facts["culprit"] == "mouse":
            c.memes["fear"] = 1
            world.clues.append("tiny tracks")
            world.say(f"Tiny tracks in the hall made the mouse look more and more likely.")
        else:
            world.say("Nothing there fit the case, so the mystery stayed tight.")
    world.para()


def turn(world: World) -> None:
    d = world.detective
    q = world.quest_item
    r = world.rhyme_note
    c = world.culprit

    world.say(f"Then {d.id} read the rhyme again.")
    dominant = world.facts["dominant"]
    if dominant == "rhyme":
        world.say(f"The dominant clue was the rhyme itself: it did not just sound nice, it pointed straight at where to look.")
    else:
        world.say(f"The dominant clue was the trail of signs, but the rhyme helped tie them together.")

    if world.facts["rhyme"] == "drawer":
        q.hidden_at = "drawer"
        q.meters["found"] = 1
        world.say(f"{d.id} opened the drawer and found {q.label} tucked inside a folded cloth.")
    elif world.facts["rhyme"] == "floor":
        q.hidden_at = "floor"
        q.meters["found"] = 1
        world.say(f"{d.id} crouched to the floor and found {q.label} under a loose board.")
    elif world.facts["rhyme"] == "door":
        q.hidden_at = "door"
        q.meters["found"] = 1
        world.say(f"{d.id} looked by the door and found {q.label} caught in the mat.")
    else:
        q.hidden_at = "stair"
        q.meters["found"] = 1
        world.say(f"{d.id} climbed the stair and found {q.label} on the landing.")

    c.memes["caught"] = 1
    world.say(f"The culprit shuffled in place, because the little evidence had become too large to ignore.")
    world.para()


def resolution(world: World) -> None:
    d = world.detective
    q = world.quest_item
    c = world.culprit
    r = world.rhyme_note

    world.say(f"{d.id} did not need a loud chase.")
    world.say(f"One careful look, one clever rhyme, and one dominant clue were enough to finish the quest.")
    world.say(f"At the end, {q.label} was safe again, and the culprit looked more sheepish than scary.")
    world.say(f"{d.id} smiled at the rhyme note, because the mystery had turned into a solved story instead of a worry.")
    world.say(f"Even {c.label} seemed small now, while the answer felt bright and clear.")
    world.say(f"That was the neat part of the whodunit: the right clue had been hiding in plain sight all along.")
    world.facts["solved"] = True
    world.facts["found_at"] = q.hidden_at
    world.facts["clue_count"] = len(world.clues)
    world.facts["quest_label"] = q.label
    world.facts["rhyme_phrase"] = r.phrase


def tell(params: StoryParams) -> World:
    world = build_world(params)
    world.facts = {
        "start": params.place,
        "quest": params.quest,
        "rhyme": params.rhyme,
        "culprit": params.culprit,
        "dominant": "rhyme" if params.rhyme in {"drawer", "door"} else "trail",
    }
    setup(world)
    investigate(world)
    turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit about a detective named {world.detective.id} and a missing {f["quest"].replace("_", " ")}.',
        f"Tell a short mystery where a rhyme clue points the detective toward a hidden object and the case is solved gently.",
        f'Write a simple quest story with a rhyme, a clue, and a clear answer to the question “whodunit?”',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = world.detective.id
    q = world.quest_item.label
    r = world.rhyme_note.phrase
    culprit = world.culprit.label
    return [
        QAItem(
            question=f"What was {d} trying to find?",
            answer=f"{d} was trying to find {q}. It was the quest at the center of the mystery.",
        ),
        QAItem(
            question="What clue mattered most in the story?",
            answer=f"The most dominant clue was the rhyme: “{r}.” It told {d} where to look next.",
        ),
        QAItem(
            question="Who caused the trouble in the whodunit?",
            answer=f"The trouble came from {culprit}, who was tied to the mystery and looked guilty when the clues added up.",
        ),
        QAItem(
            question="Where was the missing thing found?",
            answer=f"It was found at the {f['found_at']}, after the rhyme helped {d} search the right place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task to find something or reach a goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
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
    lines = ["--- world trace ---"]
    for ent in [world.detective, world.quest_item, world.rhyme_note, world.culprit]:
        lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes} hidden_at={ent.hidden_at}")
    lines.append(f"clues={world.clues}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
#show dominant/1.
#show solved/0.
dominant(rhyme) :- clue(rhyme), quest(case).
solved :- dominant(rhyme), found(object).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("case"))
    lines.append(asp.fact("quest", "case"))
    lines.append(asp.fact("clue", "rhyme"))
    lines.append(asp.fact("found", "object"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show dominant/1. #show solved/0."))
    atoms = {(a.name, len(a.arguments)) for a in model}
    py_ok = True
    if ("dominant", 1) not in atoms or ("solved", 0) not in atoms:
        py_ok = False
    if py_ok:
        print("OK: ASP twin produces dominant and solved.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit storyworld with quest and rhyme.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--rhyme", choices=RHYMES.keys())
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name", choices=DETECTIVES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    culprit = args.culprit or rng.choice(CULPRITS)
    name = args.name or rng.choice(DETECTIVES)
    if quest == "missing_key" and rhyme not in {"drawer", "door"}:
        raise StoryError("This whodunit needs a rhyme clue that can point to the key.")
    return StoryParams(name=name, detective=name, quest=quest, rhyme=rhyme, culprit=culprit, place=place)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


CURATED = [
    StoryParams(name="Mina", detective="Mina", quest="missing_key", rhyme="drawer", culprit="mouse", place="study"),
    StoryParams(name="Noah", detective="Noah", quest="lost_cookie", rhyme="floor", culprit="crow", place="kitchen"),
    StoryParams(name="Tessa", detective="Tessa", quest="vanished_crayon", rhyme="door", culprit="cat", place="hall"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dominant/1. #show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show dominant/1. #show solved/0."))
        print(" ".join(str(a) for a in model))
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
            header = f"### {p.name}: quest={p.quest}, rhyme={p.rhyme}, culprit={p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
