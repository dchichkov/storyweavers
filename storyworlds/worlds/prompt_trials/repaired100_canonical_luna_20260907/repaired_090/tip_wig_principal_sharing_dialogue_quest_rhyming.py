#!/usr/bin/env python3
"""
A small rhyming storyworld about a helpful tip, a surprising wig, and a
principal who learns that sharing a clear dialogue can guide a quest.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    principal: str
    trait: str
    quest: str
    mode: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestCard:
    title: str
    trouble: str
    first_try: str
    clue: str
    sharing: str
    turn: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


QUESTS = [
    QuestCard(
        title="the windy wig",
        trouble="A gust lifted the principal's bright wig and sent it sailing past the school sign.",
        first_try="Luna chased it alone, but the wig skittered faster each time she ran.",
        clue="A tiny tip on the playground map showed a sheltered path behind the garden gate.",
        sharing="Luna shared the tip with the principal and two classmates instead of keeping the clue to herself.",
        turn="The shared tip changed the quest from a wild chase into a careful circle around the windy field.",
        resolution="One friend held the gate, another watched the path, and the principal caught the wig beside the quiet shed.",
        lesson="A useful tip grows stronger when people share it and listen to one another.",
        ending="The wig rested on the principal's head, while four smiling helpers stood in a safe little ring.",
        question="What clue helped the group catch the wig?",
        answer="A tiny tip on the playground map showed a sheltered path behind the garden gate.",
    ),
    QuestCard(
        title="the missing tip",
        trouble="The principal had promised a tip for finding the lost reading-room key, but the first clue was smudged.",
        first_try="Luna guessed at the words and searched beneath every chair in a hurried blur.",
        clue="The librarian remembered that the clue ended with 'near the pear.'",
        sharing="Luna shared that remembered line with the principal, who repeated it slowly so everyone could hear.",
        turn="The dialogue revealed that 'pear' meant the old pear tree, not a pair of chairs.",
        resolution="They found the key in a blue cup beneath the tree and returned it to the reading-room door.",
        lesson="Speaking clearly can turn a fuzzy clue into a path that everyone can follow.",
        ending="The blue cup gleamed under the pear tree as the reading-room door swung open.",
        question="How did the dialogue fix the confusing clue?",
        answer="The principal repeated the line slowly, and the group understood that 'pear' meant the old pear tree.",
    ),
    QuestCard(
        title="the borrowed wig",
        trouble="A costume wig was needed for the school play, but its box had vanished before rehearsal.",
        first_try="Luna looked in the stage cupboard and almost blamed the nearest class.",
        clue="The principal found a sharing chart showing that the art club had borrowed the box.",
        sharing="Luna spoke with the art club and shared the chart instead of making an accusation.",
        turn="The chart changed the mystery into a friendly return: the art club had placed the box by the paint sink.",
        resolution="The clubs carried the box back together, and the principal thanked both groups for telling the truth.",
        lesson="Sharing facts kindly makes a quest fairer for everyone.",
        ending="The wig waited on its stand beneath a paper moon while both clubs practiced their lines.",
        question="What did the sharing chart reveal?",
        answer="It revealed that the art club had borrowed the wig box and placed it by the paint sink.",
    ),
    QuestCard(
        title="the whispering tip",
        trouble="A whispering tip said the principal's wig was hiding near the bell, but nobody knew which bell.",
        first_try="Luna pointed at the lunch bell and dashed toward it before asking more.",
        clue="The principal invited each listener to say what they had actually heard.",
        sharing="Everyone shared one small detail: the bell was outside, green, and beside a stone.",
        turn="The dialogue joined the details into one clear picture of the garden bell.",
        resolution="They found the wig looped over the garden bell and carried it back on a clean hook.",
        lesson="Listening to many small pieces can build one dependable answer.",
        ending="The green bell shone under the wig's purple brim as the garden grew quiet again.",
        question="How did the group identify the correct bell?",
        answer="They shared the details that it was outside, green, and beside a stone, identifying the garden bell.",
    ),
]


NAMES = ["Luna", "Mira", "Nora", "Zoe", "Tia"]
TRAITS = ["curious", "kind", "cheerful", "careful", "brave"]
OPENINGS = [
    "Tip-tap went the morning rain, and a quest began again.",
    "At school beneath a silver sky, a little mystery hurried by.",
    "A wig, a tip, and a principal made a rhyme-ready riddle.",
    "The bell rang bright; the day took flight.",
    "Before the first class could start, a puzzling quest knocked at the heart.",
]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "school" and activity == "share" and prize == "wig"


ASP_RULES = r"""
place(school).
activity(share).
prize(wig).
feature(sharing).
feature(dialogue).
feature(quest).

compatible(P,A,R) :-
    place(P), activity(A), prize(R),
    P = school, A = share, R = wig.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "school"),
            asp.fact("activity", "share"),
            asp.fact("prize", "wig"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "quest"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("school", "share", "wig")]


def tell(params: StoryParams) -> World:
    quest = QUESTS[int(params.quest.rsplit("_", 1)[1])]
    opening = OPENINGS[int(params.mode.rsplit("_", 1)[1])]
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.gender,
            label=params.name,
            memes={"curiosity": 1.0, "sharing": 0.0, "confidence": 0.0},
        )
    )
    principal = world.add(
        Entity(
            id="principal",
            kind="character",
            type="adult",
            label=params.principal,
            memes={"patience": 1.0},
        )
    )
    tip = world.add(
        Entity(
            id="tip",
            kind="clue",
            type="tip",
            label="tip",
            meters={"clarity": 0.5},
        )
    )
    wig = world.add(
        Entity(
            id="wig",
            kind="costume",
            type="wig",
            label="wig",
            meters={"wind": 1.0},
        )
    )
    world.facts.update(child=child, principal=principal, tip=tip, wig=wig, quest=quest)

    world.say(opening)
    world.say(
        f"{params.name}, a {params.trait} {params.gender}, met {params.principal}, the principal, "
        "beside the school gate."
    )
    world.say(
        f'"Today we have a quest," said {params.principal}. '
        f'"We must find the wig, and every good tip should be shared."'
    )
    world.say(f'"I will help," said {params.name}. "But tell me what to do, and I will listen too."')
    world.para()

    world.say(quest.trouble)
    world.say(quest.first_try)
    child.memes["confidence"] += 1.0
    world.say(
        f'"I have a tip, but should I keep it?" {params.name} asked. '
        f'"No," said {params.principal}. "A shared clue can help us choose a safer route."'
    )
    world.para()

    world.say(quest.clue)
    tip.meters["clarity"] = 1.0
    world.say(quest.sharing)
    child.memes["sharing"] = 1.0
    world.say(quest.turn)
    world.fired.add("shared_tip")
    world.para()

    world.say(quest.resolution)
    world.say(
        f'"Your words changed our plan," said {params.principal}. '
        f'"And your listening helped," {params.name} replied.'
    )
    world.say(quest.lesson)
    world.say(quest.ending)
    world.facts.update(
        title=quest.title,
        clue=quest.clue,
        turn=quest.turn,
        resolution=quest.resolution,
        lesson=quest.lesson,
        ending=quest.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    quest = world.facts["quest"]
    return [
        "Write a child-friendly rhyming story featuring a tip, a wig, and a principal.",
        f"Tell a rhyming quest where {child.label} solves {quest.title} through sharing and dialogue.",
        f"Make this clue change the plan: {quest.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    principal = world.facts["principal"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"Who joined {child.label} on the quest?",
            answer=f"{principal.label}, the principal, joined {child.label} and helped guide the quest.",
        ),
        QAItem(
            question=f"What was the important tip in {quest.title}?",
            answer=quest.answer,
        ),
        QAItem(
            question=f"How did sharing change {child.label}'s plan?",
            answer=quest.sharing,
        ),
        QAItem(
            question=f"What did the dialogue help the group understand?",
            answer=quest.turn,
        ),
        QAItem(
            question=f"What final image showed that {quest.title} was solved?",
            answer=quest.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tip?",
            answer="A tip is a small piece of advice or information that can help someone.",
        ),
        QAItem(
            question="Why can sharing help during a quest?",
            answer="Sharing lets people combine clues, notice more details, and choose a better plan together.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a back-and-forth exchange of spoken words between characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "school":
        raise StoryError("This storyworld only supports the school setting.")
    if args.activity and args.activity != "share":
        raise StoryError("This storyworld only supports the share activity.")
    if args.prize and args.prize != "wig":
        raise StoryError("This storyworld only supports the wig quest prize.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    principal = args.principal or rng.choice(["Principal Reed", "Principal Vale", "Principal Kim"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="school",
        activity="share",
        prize="wig",
        name=name,
        gender=gender,
        principal=principal,
        trait=trait,
        quest=f"quest_{seed % len(QUESTS):02d}",
        mode=f"mode_{(seed // len(QUESTS)) % len(OPENINGS):02d}",
        seed=seed,
    )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming storyworld about a tip, a wig, a principal, and a sharing quest."
    )
    parser.add_argument("--place", choices=["school"])
    parser.add_argument("--activity", choices=["share"])
    parser.add_argument("--prize", choices=["wig"])
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--principal")
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP compatibility gates.")
        print("Only in Python:", sorted(python_combos - asp_combos))
        print("Only in ASP:", sorted(asp_combos - python_combos))
        return 1

    sample = generate(
        StoryParams(
            place="school",
            activity="share",
            prize="wig",
            name="Luna",
            gender="girl",
            principal="Principal Reed",
            trait="curious",
            quest="quest_00",
            mode="mode_00",
            seed=0,
        )
    )
    required = ["tip", "wig", "principal"]
    if not all(word in sample.story.lower() for word in required):
        print("Generated story failed required-word verification.")
        return 1
    if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
        print("Generated story failed QA verification.")
        return 1
    print(f"OK: ASP/Python parity holds ({len(python_combos)} combo).")
    print("OK: generated story and QA checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
