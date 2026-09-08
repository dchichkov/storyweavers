#!/usr/bin/env python3
"""
Standalone storyworld: PomPom and the Cootie Detective.

A child-facing detective story in which a missing pompom creates a small
conflict, careful clues reveal the truth, and a lesson learned helps friends
repair their feelings.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise StoryError(f"Unknown entity: {eid}")
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
    detective: str
    friend: str
    pet_name: str = "PomPom"
    setting: int = 0
    case: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Theo", "Ari", "Zoe", "Ivy", "Sam"]
FRIEND_NAMES = ["Tess", "Noah", "Mina", "Owen", "Pia", "Ben", "Kai", "Ruby"]
GIRL_NAMES = {"Luna", "Nia", "Zoe", "Ivy", "Tess", "Mina", "Pia", "Ruby"}

SETTINGS = [
    {
        "place": "the little community garden",
        "detail": "where bean vines curled around painted sticks",
        "trail": "three yellow fibers beside the mint bed",
    },
    {
        "place": "the school art room",
        "detail": "where paper moons hung from the ceiling",
        "trail": "a streak of blue chalk beneath the drying rack",
    },
    {
        "place": "the rainy-day clubhouse",
        "detail": "where cushions made a maze across the floor",
        "trail": "two damp footprints beside the coat basket",
    },
    {
        "place": "the town library's reading corner",
        "detail": "where cardboard castles stood beside the story rug",
        "trail": "a tiny red thread caught on a book cart",
    },
    {
        "place": "the sunny playground shed",
        "detail": "where skipping ropes hung like bright snakes",
        "trail": "a round dust mark under the bench",
    },
]

CASES = [
    {
        "object": "a red pompom from the class puppet",
        "purpose": "the puppet show that afternoon",
        "conflict": "the pompom disappeared from the puppet's hat, and two friends blamed each other",
        "clue": "a loose blue thread led from the puppet shelf toward the costume basket",
        "false_lead": "a red smear on the table looked suspicious, but it was only strawberry jam",
        "method": "followed the thread, checked the basket, and asked what each person had carried",
        "truth": "the wind from an open window had rolled the pompom into a folded costume",
        "repair": "returned the pompom to the puppet and apologized for accusing one another",
        "image": "the red pompom bobbed on the puppet's hat while both friends made it bow",
        "lesson": "A detective checks evidence before choosing someone to blame.",
    },
    {
        "object": "a green pompom used as the cootie's lucky hat",
        "purpose": "the classroom bug parade",
        "conflict": "the cootie lost its hat, and one friend thought the other had hidden it as a joke",
        "clue": "a trail of green fluff crossed the windowsill",
        "false_lead": "a toy shovel beside the sandbox seemed guilty until they noticed it was covered in clean sand",
        "method": "measured the fluff trail with a ruler and searched every place where a breeze could reach",
        "truth": "a paper fan had blown the pompom behind a box of costumes",
        "repair": "freed the pompom, gave the cootie its hat, and replaced the sharp words with a shared laugh",
        "image": "the tiny cootie wore its green pompom like a crown as the parade marched past",
        "lesson": "A careful question can solve a conflict more kindly than a quick accusation.",
    },
    {
        "object": "a purple pompom prize from the reading club",
        "purpose": "the end-of-week mystery game",
        "conflict": "the prize vanished, and the players argued about who had touched the game box",
        "clue": "purple fuzz clung to the hinge of the old cupboard",
        "false_lead": "a muddy shoeprint pointed toward the door, but the print was from yesterday's rain",
        "method": "compared the fuzz, checked the cupboard hinge, and rebuilt the order of the afternoon",
        "truth": "the cupboard door had caught the pompom when someone closed it too quickly",
        "repair": "opened the cupboard gently, found the prize, and let everyone finish the game together",
        "image": "the purple pompom sat in the winner's palm while every player cheered",
        "lesson": "A lesson learned is stronger when everyone helps discover it.",
    },
    {
        "object": "a yellow pompom attached to a cardboard cootie",
        "purpose": "a science display about tiny creatures",
        "conflict": "the yellow pompom went missing, and the display team stopped speaking to one another",
        "clue": "a line of tiny paper legs pointed under the demonstration table",
        "false_lead": "a yellow crayon looked like the missing piece, but its flat shape did not fit",
        "method": "looked under the table, matched the shape, and listened to each teammate's account",
        "truth": "the cootie had tipped forward when the tablecloth was pulled",
        "repair": "repaired the cardboard legs, reattached the pompom, and invited every teammate back",
        "image": "the cardboard cootie stood tall again beneath a sign reading KIND QUESTIONS",
        "lesson": "When a group listens instead of sulking, a small clue can reopen a friendship.",
    },
]

OPENINGS = [
    "Luna loved mysteries, especially the kind small enough to fit in a pocket.",
    "The morning began quietly, until one round pompom rolled away from a very important cootie.",
    "At the start of club time, the room smelled of paper, crayons, and a mystery.",
    "Everyone expected an ordinary afternoon, but ordinary afternoons rarely leave fuzzy clues.",
    "Luna had brought her notebook, her pencil, and the detective face she used for serious cases.",
]

DIALOGUES = [
    '"I did not take it," said {friend}. "And I do not want you to think I did."',
    '"Let us ask what the clues say," {detective} replied. "Then we can ask what happened."',
    '"I was sure I knew the answer," said {detective}, "but I may have guessed too soon."',
    '"Can we search together?" asked {friend}. "I would rather solve this than stay cross."',
    '"A clue is not a culprit," {detective} reminded everyone.',
]

ENDINGS = [
    "The friends wrote the lesson in the casebook before closing it.",
    "After that, every mystery began with a question and ended with a thank-you.",
    "The cootie received a tiny bow, and the detective received a very serious high-five.",
    "By snack time, the conflict felt smaller than the pompom and much easier to carry.",
    "The room grew cheerful again, as if the missing color had returned to every corner.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story about a pompom, a cootie, and a lesson learned.")
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--pet-name", default="PomPom")
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
    detective = args.detective or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != detective] or FRIEND_NAMES)
    return StoryParams(
        detective=detective,
        friend=friend,
        pet_name=args.pet_name or "PomPom",
        setting=rng.randrange(len(SETTINGS)),
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if not params.detective.strip() or not params.friend.strip():
        raise StoryError("Detective and friend names must not be empty.")
    if params.detective == params.friend:
        raise StoryError("The detective and friend must have different names.")
    setting = SETTINGS[params.setting % len(SETTINGS)]
    world = World(setting["place"])
    world.add(Entity("Detective", "character", "girl" if params.detective in GIRL_NAMES else "person", params.detective, location=setting["place"]))
    world.add(Entity("Friend", "character", "girl" if params.friend in GIRL_NAMES else "person", params.friend, location=setting["place"]))
    world.add(Entity("PomPom", "object", "pompom", params.pet_name, location=setting["place"]))
    world.add(Entity("Cootie", "object", "cootie", "the cootie", location=setting["place"]))
    world.facts["params"] = params
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    case = CASES[params.case % len(CASES)]
    setting = SETTINGS[params.setting % len(SETTINGS)]
    detective = world.get("Detective")
    friend = world.get("Friend")
    pompom = world.get("PomPom")
    cootie = world.get("Cootie")

    world.facts["case"] = case
    world.facts["setting"] = setting

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"{detective.label} was the junior detective, and {friend.label} was the best helper in {setting['place']}, "
        f"{setting['detail']}. Together they cared for {cootie.label}, a tiny cardboard creature with a bright pompom."
    )

    world.para()
    world.say(f"The case began when {case['conflict']}. The missing object was {case['object']}, and it was needed for {case['purpose']}.")
    detective.memes["curious"] = 1
    friend.memes["worried"] = 1
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(detective=detective.label, friend=friend.label))
    world.say(f"The first search found {setting['trail']}, but it did not prove who had moved anything.")
    world.say(f"They also noticed a false lead: {case['false_lead']}.")

    world.para()
    world.say(
        f"{detective.label} opened the notebook and said, "
        f'"A real detective follows the evidence, not the loudest guess."'
    )
    world.say(f"With {friend.label} beside {detective.label}, they {case['method']}.")
    world.say(f"The truth was simple: {case['truth']}.")
    pompom.meters["found"] = 1
    cootie.meters["repaired"] = 1
    detective.memes["careful"] = 1
    friend.memes["relieved"] = 1
    world.say(f"Then they {case['repair']}.")
    world.say(
        f"{friend.label} said, 'Next time, I will ask before I accuse.' "
        f"{detective.label} answered, 'And I will remember that being certain is not the same as being right.'"
    )

    world.para()
    world.say(f"This was the lesson learned: {case['lesson']}")
    world.say(f"In the final scene, {case['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.facts.update(resolved=True, clue=case["clue"], truth=case["truth"], lesson=case["lesson"], ending_image=case["image"])


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly detective story about {params.detective}, {params.friend}, a pompom, and a cootie.",
        f"Build a mystery in which {case['object']} goes missing and a conflict must be solved with evidence.",
        f"End with a clear lesson learned: {case['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem("What went missing?", f"{case['object']} went missing from the cootie display."),
        QAItem("What clue helped solve the mystery?", f"The important clue was that {case['clue']}."),
        QAItem(f"How did {params.detective} investigate?", f"{params.detective} and {params.friend} {case['method']}."),
        QAItem("What was the truth?", f"The truth was that {case['truth']}."),
        QAItem("How was the conflict repaired?", f"They {case['repair']}."),
        QAItem("What lesson was learned?", f"The lesson learned was that {case['lesson']}"),
        QAItem("What final image showed the case was solved?", f"In the ending, {case['image']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pompom?", "A pompom is a small soft ball made from yarn, thread, or fluff."),
        QAItem("What is a cootie in this story?", "A cootie is a small handmade cardboard creature used in the display."),
        QAItem("What does a detective do?", "A detective gathers clues and checks evidence to understand what happened."),
        QAItem("What is a conflict?", "A conflict is a disagreement or problem between people."),
        QAItem("What does lesson learned mean?", "A lesson learned is an idea about what to do better after an experience."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.setting}"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(details) if details else '(quiet)'}")
    lines.append(f"resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_pompom.
clue_found :- missing_pompom.
truth_found :- clue_found.
repaired :- truth_found.
lesson_learned :- repaired.
#show clue_found/0.
#show truth_found/0.
#show repaired/0.
#show lesson_learned/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing_pompom"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    required = {"clue_found", "truth_found", "repaired", "lesson_learned"}
    if not required.issubset(names):
        raise StoryError("ASP parity failed: detective resolution atoms are missing.")
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError("Python parity failed: curated story did not resolve.")
        if "lesson" not in sample.story.lower():
            raise StoryError("Generated story did not include the lesson learned.")
    print("OK: ASP and Python both resolve the pompom conflict and record the lesson learned.")
    return 0


CURATED = [
    StoryParams("Luna", "Tess", setting=0, case=0, opening=0, dialogue=1, ending=0),
    StoryParams("Milo", "Mina", setting=1, case=1, opening=1, dialogue=3, ending=2),
    StoryParams("Zoe", "Owen", setting=3, case=2, opening=4, dialogue=2, ending=4),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.detective} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        raise SystemExit(2)
