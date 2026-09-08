#!/usr/bin/env python3
"""
A gentle ghost story about a comment, curiosity, an inner monologue,
and a misunderstanding that is solved by listening.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    child: str
    ghost: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Encounter:
    sound: str
    object_detail: str
    comment: str
    mistaken_belief: str
    hidden_cause: str
    test: str
    repair: str
    lesson: str
    ending: str


ENCOUNTERS = [
    Encounter(
        "three soft taps",
        "a silver button resting on the nursery floor",
        '"Do not come closer," read the comment scratched on the door.',
        "the ghost wanted to frighten everyone away",
        "the ghost was tapping from inside the old music box to ask for help",
        "placed the button beside the music box and waited for the taps to answer",
        "wound the music box and returned its missing button",
        "A frightening comment may hide a frightened voice.",
        "a quiet tune curled through the moonlit room",
    ),
    Encounter(
        "a whisper beneath the stairs",
        "a blue ribbon caught on a dusty nail",
        '"Leave this place," said the lonely comment on the wall.',
        "the ghost was angry with anyone who entered",
        "the ghost had written the comment while trying to warn visitors about a loose stair",
        "held a lantern low and checked each stair instead of running away",
        "tied the ribbon around the loose board so nobody would step there",
        "Curiosity is safest when it moves slowly and checks the facts.",
        "the ribbon fluttered gently above a repaired stair",
    ),
    Encounter(
        "a hollow knock from the attic",
        "a small wooden moon beside an empty cradle",
        '"I am watching," announced the comment on the dusty mirror.',
        "the ghost was spying on the child",
        "the ghost was watching the moon charm because it belonged to a lost baby brother",
        "asked a calm question and listened for the knock to repeat near the cradle",
        "hung the wooden moon where the ghost could see it",
        "An inner thought can sound certain before it knows the whole story.",
        "the mirror reflected one smiling face and one friendly pale glow",
    ),
    Encounter(
        "a curtain lifting with no breeze",
        "a paper comment pinned beneath the window",
        '"Go home before midnight," the message warned.',
        "the ghost planned to chase the child out",
        "the ghost was trying to protect the child from a branch scraping the roof",
        "opened the curtain and compared the scraping sound with the branch outside",
        "trimmed the branch and thanked the ghost for the warning",
        "A misunderstanding can change when someone shares the missing reason.",
        "the curtain rested still while stars shone through the clean window",
    ),
    Encounter(
        "a bell ringing once in the empty hall",
        "a warm scarf folded beside the coat stand",
        '"Someone forgot me," said the comment in the guest book.',
        "the ghost was blaming the child for leaving",
        "the ghost had mistaken the scarf for a lost person it once knew",
        "showed the ghost the scarf's owner arriving at the front door",
        "placed the scarf on its owner's chair",
        "Questions are kinder than guesses about what someone means.",
        "the bell gave one happy ring as the scarf was wrapped around warm shoulders",
    ),
    Encounter(
        "a pale shape crossing the kitchen wall",
        "a floury handprint beside the pantry",
        '"Do not open this door," read the comment in chalk.',
        "the ghost was guarding a secret treasure",
        "the ghost was warning about a jar balanced on the pantry shelf",
        "opened the door only a crack and watched which jar trembled",
        "moved the jar to a safe lower shelf",
        "Careful curiosity can turn a scary mystery into a useful discovery.",
        "the chalk comment was washed away beneath a bright kitchen lamp",
    ),
]


PLACES = {
    "old_house": "the old house",
    "moonlit_inn": "the moonlit inn",
    "quiet_museum": "the quiet museum",
    "hilltop_cottage": "the hilltop cottage",
}

CHILDREN = ["Luna", "Mara", "Theo", "Nia", "Pip", "Elio"]
GHOSTS = ["the pale ghost", "the attic ghost", "the window ghost", "the little ghost"]
OBJECTS = ["brass key", "glass lantern", "red umbrella", "wooden moon"]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__())))
    rng = random.Random(seed ^ 0x91C7)
    encounter = rng.choice(ENCOUNTERS)

    world = World(PLACES[params.place])
    child = world.add(Entity("child", "character", "child", params.child))
    ghost = world.add(Entity("ghost", "character", "ghost", params.ghost))
    object_ent = world.add(Entity("object", "thing", "object", params.object_name))
    room = world.add(Entity("room", "place", "room", world.place))

    child.memes.update(curiosity=1.0, worry=0.0, understanding=0.0)
    ghost.memes.update(fear=1.0, loneliness=1.0, relief=0.0)
    object_ent.meters.update(present=1.0, useful=0.0)
    room.meters.update(dark=1.0, safe=0.0)

    world.say(f"At dusk, {params.child} entered {world.place}, where the windows shone like gray eyes.")
    world.say(f"{params.child} had brought a {params.object_name} and a curious question: who had left the strange comment?")
    world.say(f"Then {encounter.sound} came from nearby.")
    world.para()
    world.say(f"On the wall, {params.child} found {encounter.comment}")
    world.say(f"The words made {params.child}'s inner monologue race: \"The ghost must be angry with me.\"")
    world.say(f"That was a misunderstanding, but it felt real because {encounter.mistaken_belief}.")
    child.memes["worry"] = 1.0
    world.fired.add("misunderstanding")
    world.para()
    world.say(f"Curiosity was stronger than fear. {params.child} noticed {encounter.object_detail}.")
    world.say(f'"Are you trying to tell me something?" {params.child} asked.')
    world.say(f'"Not frighten," whispered {params.ghost}. "Please listen."')
    world.say(f'"Then show me one clear clue," said {params.child}.')
    world.say(f"{params.ghost} answered with the same sound, and {params.child} {encounter.test}.")
    world.say(f"The test explained everything: {encounter.hidden_cause}.")
    child.memes["understanding"] = 1.0
    ghost.memes["loneliness"] = 0.0
    ghost.memes["relief"] = 1.0
    object_ent.meters["useful"] = 1.0
    world.fired.add("curiosity_test")
    world.para()
    world.say(f"Together they {encounter.repair}.")
    world.say(f"{params.child} read the comment again and understood that it had been a frightened request, not a threat.")
    world.say(f'"I am glad you asked me," said {params.ghost}.')
    world.say(f'"I am glad you answered," said {params.child}.')
    world.say(f"{encounter.lesson}")
    world.say(f"By midnight, {encounter.ending}.")
    room.meters["dark"] = 0.0
    room.meters["safe"] = 1.0
    world.fired.add("resolved")

    world.facts.update(
        child=child,
        ghost=ghost,
        object=object_ent,
        place=world.place,
        encounter=encounter,
        comment=encounter.comment,
        mistaken_belief=encounter.mistaken_belief,
        hidden_cause=encounter.hidden_cause,
        test=encounter.test,
        repair=encounter.repair,
        lesson=encounter.lesson,
        ending=encounter.ending,
    )
    return world


ASP_RULES = r"""
curious(C) :- child(C), wants_clue(C).
misunderstood(C) :- child(C), believes_angry(C).
resolved(C) :- curious(C), tested(C), understood(C), safe(C).
#show curious/1.
#show misunderstood/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child", "luna"),
        asp.fact("wants_clue", "luna"),
        asp.fact("believes_angry", "luna"),
        asp.fact("tested", "luna"),
        asp.fact("understood", "luna"),
        asp.fact("safe", "luna"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle ghost story about curiosity and a misunderstanding.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child")
    parser.add_argument("--ghost")
    parser.add_argument("--object-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        child=args.child or rng.choice(CHILDREN),
        ghost=args.ghost or rng.choice(GHOSTS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story set in {f['place']} about {f['child'].label}'s curiosity.",
        f"Include this comment: {f['comment']}",
        f"Show how a misunderstanding is solved when {f['child'].label} tests the ghost's meaning.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    ghost = f["ghost"].label
    return [
        QAItem(f"What comment did {child} find?", f"{child} found the comment, {f['comment']}."),
        QAItem("Why was the comment misunderstood?", f"It was misunderstood because {f['mistaken_belief']}."),
        QAItem(f"How did {child} discover what {ghost} meant?", f"{child} tested the clue by {f['test']}."),
        QAItem("What was the real cause of the ghost's message?", f"The real cause was that {f['hidden_cause']}."),
        QAItem("How did the story end?", f"The story ended when they {f['repair']}; then {f['ending']}."),
        QAItem("What lesson did the child learn?", f"{f['lesson']}"),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem("What is curiosity?", "Curiosity is a wish to learn or discover something."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea about what another person means."),
        QAItem("Why can asking a question help?", "Asking a question can reveal missing information and replace a guess with understanding."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: kind={entity.kind} type={entity.type} meters={entity.meters} memes={entity.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show misunderstood/1.\n#show resolved/1."))
    names = {sym.name for sym in model}
    required = {"curious", "misunderstood", "resolved"}
    if not required.issubset(names):
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams("old_house", "Luna", "the pale ghost", "brass key", 7))
    if "comment" not in sample.story.lower() or "curiosity" not in sample.story.lower():
        print("Story verification failed.")
        return 1
    print("OK: ASP parity and story generation verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show curious/1.\n#show misunderstood/1.\n#show resolved/1."))
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            StoryParams("old_house", "Luna", "the pale ghost", "brass key", base_seed),
            StoryParams("moonlit_inn", "Mara", "the window ghost", "glass lantern", base_seed + 1),
            StoryParams("quiet_museum", "Theo", "the attic ghost", "wooden moon", base_seed + 2),
            StoryParams("hilltop_cottage", "Nia", "the little ghost", "red umbrella", base_seed + 3),
        ]
        samples = [generate(p) for p in choices]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
