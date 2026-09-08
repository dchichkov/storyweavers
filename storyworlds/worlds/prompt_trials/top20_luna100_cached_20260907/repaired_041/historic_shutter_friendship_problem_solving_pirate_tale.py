#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle pirate tale about a historic shutter,
friendship, and problem solving.
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
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "the old harbor lighthouse"
SEED_WORDS = {"historic", "shutter"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("distance", "wind", "damage", "brightness", "weight"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "hope", "trust", "curiosity", "courage", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    captain: str = "Luna"
    friend: str = "Pip"
    parrot: str = "Breezy"
    trial: int = 0
    voice: int = 0
    lesson_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    treasure: str
    trouble: str
    clue: str
    wrong_idea: str
    question: str
    method: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        treasure="the lighthouse keeper's brass bell",
        trouble="the historic wooden shutter slammed shut and trapped the bell's moon-shaped key inside",
        clue="a bright scrape on the shutter hinge and a blue thread caught in the latch",
        wrong_idea="a trail of wet footprints leading toward the pier",
        question="Which mark could have touched the latch?",
        method="hold the shutter safely while the other follows the blue thread",
        discovery="found the key tucked behind the loose hinge plate",
        cause="had tugged the bell rope during a gust and knocked the hinge pin sideways",
        repair="straightened the hinge pin, tied the rope shorter, and oiled the shutter together",
        proof="the shutter opened gently and the bell rang without sticking",
        lesson="Friends solve problems best when they ask what each clue can truly prove.",
        ending="At sunset, the historic shutter glowed gold while the brass bell chimed over the sea.",
    ),
    Trial(
        treasure="a map of the harbor's first ships",
        trouble="the historic shutter fell across the map chest before the map could be rolled away",
        clue="a curl of red sailcloth wedged beneath the lower shutter board",
        wrong_idea="a gull feather beside an empty fish basket",
        question="Which object was close enough to pull the shutter?",
        method="check the fish basket while the other traces the red cloth beneath the boards",
        discovery="lifted the shutter and rescued the map from the chest's open lid",
        cause="had backed into the shutter while carrying a too-large basket of oranges",
        repair="moved the basket path, replaced the worn latch, and dried the map beneath smooth stones",
        proof="the map lay flat and the clear path left room for two sailors to pass",
        lesson="A careful question can turn a confusing accident into a useful plan.",
        ending="The first ships on the map seemed to sail again as the repaired shutter framed the harbor.",
    ),
    Trial(
        treasure="the captain's silver compass",
        trouble="a hard sea wind pinned the historic shutter against the compass shelf",
        clue="tiny grains of sand inside the shutter track",
        wrong_idea="a crooked flag pointing toward the rocks",
        question="What could make the shutter drag along its track?",
        method="watch the flag while the other brushes the sand from the lower track",
        discovery="slid the shutter aside and found the compass safe beneath a folded sail",
        cause="had left a bucket of beach sand beside the window and the wind pushed it into the track",
        repair="swept the sand, moved the bucket, and fitted a small wooden stop to the shutter",
        proof="the shutter moved smoothly even when the wind rattled the flags",
        lesson="The smallest physical detail may explain a much larger problem.",
        ending="Luna's compass pointed home while the historic shutter clicked softly in its new stop.",
    ),
    Trial(
        treasure="a pearl button from the harbor's first coat",
        trouble="the historic shutter creaked closed while the pearl button rolled beneath the sill",
        clue="a round dent in the dust and a loose cord hanging from the shutter hook",
        wrong_idea="a shiny shell near the tide pool",
        question="Which shiny object was the button, and which was only a shell?",
        method="compare the round dent while the other checks the tide pool without leaving the harbor gate",
        discovery="reached beneath the sill and lifted the pearl button from a crack",
        cause="had pulled the cord to shade the room and startled a box of old sewing things",
        repair="closed the box, tied the cord away from the hook, and swept the sill with a soft brush",
        proof="the button fit the old coat and the shutter stayed open on its catch",
        lesson="Good problem solving separates a tempting guess from evidence that matches the object.",
        ending="The pearl button shone on the old coat as friends watched the calm harbor through the shutter.",
    ),
    Trial(
        treasure="the lighthouse logbook",
        trouble="the historic shutter blocked the reading room just as a spray of rain blew across the open logbook",
        clue="a damp handprint on the shutter edge and a dry rectangle beneath the logbook",
        wrong_idea="a puddle beneath the welcome mat",
        question="Where had the logbook been protected from the rain?",
        method="check beneath the mat while the other follows the dry rectangle around the reading table",
        discovery="found the logbook tucked behind the shutter's inner brace",
        cause="had moved it there to make space for a leaking bucket and forgotten to tell the crew",
        repair="emptied the bucket, dried the pages, and added a labeled shelf beside the window",
        proof="the logbook opened flat, and no rain reached the new shelf",
        lesson="Sharing information is part of friendship, especially when a quick fix changes where something belongs.",
        ending="The old logbook rested safely by the window, recording one more bright day at sea.",
    ),
    Trial(
        treasure="a tiny wooden ship made by the first lighthouse keeper",
        trouble="the historic shutter rattled loose and nudged the ship toward the floor",
        clue="a fresh notch on the window ledge and a small wheel mark in the dust",
        wrong_idea="a toy boat floating in a rain barrel",
        question="Did the little ship roll, or did the wind push it?",
        method="inspect the barrel while the other measures the wheel mark from the ledge to the wall",
        discovery="caught the wooden ship behind a coil of rope",
        cause="had rolled the rope aside to reach a lantern and left the ledge crowded",
        repair="cleared the ledge, tied the rope on its peg, and placed a felt guard beneath the shutter",
        proof="the wooden ship stayed still while the shutter moved in the breeze",
        lesson="A safe solution changes the place or tool that caused the trouble, not only the final mess.",
        ending="The tiny ship sailed nowhere, yet its polished bow pointed proudly toward the historic sea.",
    ),
]


@dataclass
class World:
    captain: Entity
    friend: Entity
    parrot: Entity
    shutter: Entity
    treasure: Entity
    lighthouse: Entity
    harbor: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_entity(
    eid: str,
    kind: str,
    type_: str,
    label: str,
    location: str = "",
) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams) -> World:
    if params.captain == params.friend:
        raise StoryError("The captain and friend must have different names.")
    if params.parrot in {params.captain, params.friend}:
        raise StoryError("The parrot must have a name different from both children.")

    captain = make_entity(params.captain, "character", "child", "the young captain", "lighthouse")
    friend = make_entity(params.friend, "character", "child", "the deckhand friend", "lighthouse")
    parrot = make_entity(params.parrot, "character", "bird", "the lookout parrot", "roof")
    shutter = make_entity("historic_shutter", "object", "shutter", "the historic shutter", "window")
    treasure = make_entity("harbor_treasure", "object", "relic", "the old harbor treasure", "reading room")
    lighthouse = make_entity("lighthouse", "place", "tower", "the old harbor lighthouse", "shore")
    harbor = make_entity("harbor", "place", "water", "the harbor", "shore")

    world = World(captain, friend, parrot, shutter, treasure, lighthouse, harbor)
    world.facts["theme"] = THEME
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    captain, friend, parrot = world.captain, world.friend, world.parrot
    shutter, treasure = world.shutter, world.treasure
    trial = TRIALS[params.trial % len(TRIALS)]

    captain.memes["worry"] = 1
    friend.memes["trust"] = 1
    parrot.memes["curiosity"] = 2
    shutter.meters["wind"] = 2
    shutter.meters["damage"] = 1
    treasure.meters["weight"] = 1

    openings = [
        f"At {THEME}, Captain {captain.id} polished the brass rail while {friend.id} checked the ropes and {parrot.id} watched from the roof.",
        f"The little pirate crew sailed no farther than {THEME} that morning. Captain {captain.id} carried a spyglass, and {friend.id} carried a coil of rope.",
        f"Sea mist curled around {THEME} as {captain.id}, {friend.id}, and {parrot.id} prepared to care for an important piece of harbor history.",
        f"Before the tide turned, Captain {captain.id} called the crew together at {THEME} for a careful treasure check.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"They were guarding {trial.treasure}, a small piece of the harbor's historic past.")
    world.say(f"Then {trial.trouble}.")
    world.say("The friends wanted to help without damaging the old building or blaming anyone.")

    world.para()
    world.say(f"Near the window, they noticed {trial.clue}.")
    world.say(f"Farther away, {trial.wrong_idea}.")
    world.say(f"{captain.id} studied both marks and asked, \"{trial.question}\"")
    friend_lines = [
        f"\"Let's test the clue instead of chasing a rumor,\" {friend.id} said.",
        f"\"I will stay beside you,\" {friend.id} replied. \"Friends can check different places and share what they learn.\"",
        f"{friend.id} nodded. \"A pirate crew needs courage, but it also needs careful eyes.\"",
        f"\"We can solve this,\" {friend.id} said. \"First we make a safe plan, then we follow it.\"",
    ]
    world.say(friend_lines[(params.voice + params.lesson_style) % len(friend_lines)])
    world.say(f"{parrot.id} squawked, \"Check the clue! Check the clue!\"")
    world.say(f"Together, they decided to {trial.method}.")

    world.para()
    captain.memes["curiosity"] += 2
    friend.memes["trust"] += 1
    shutter.meters["damage"] = 0
    world.say(
        f"They worked slowly. {captain.id} held the old wood steady while {friend.id} examined the latch, "
        f"and {parrot.id} called out whenever the wind changed."
    )
    world.say(f"The first idea explained one detail, but not the whole problem. Then the stronger clue led them to {trial.discovery}.")
    treasure.location = "captain's hands"
    treasure.carried_by = captain.id
    world.say(f"{captain.id} lifted the treasure carefully. \"It is safe,\" {captain.id} said.")
    world.say(f"{friend.id} smiled. \"And now we know what happened.\"")
    world.say(f"{parrot.id} flapped down and announced, \"Aha! A true answer!\"")
    world.say(f"The cause became clear: {trial.cause}.")
    captain.memes["hope"] += 2
    friend.memes["courage"] += 1

    world.para()
    world.say(f"The crew {trial.repair}.")
    world.say(f"Then they tested their work: {trial.proof}.")
    world.say(f"{captain.id} said, \"We solved it because we listened to one another.\"")
    world.say(f"{friend.id} answered, \"Friendship makes a hard job lighter, but our careful plan made it safe.\"")
    world.say(f"{parrot.id} chirped, \"Safe, steady, shipshape!\"")
    world.say(f"Their lesson was simple: {trial.lesson}")

    world.para()
    world.say(trial.ending)

    captain.memes["joy"] += 2
    friend.memes["joy"] += 2
    world.facts.update(
        trial=trial,
        treasure=trial.treasure,
        trouble=trial.trouble,
        clue=trial.clue,
        wrong_idea=trial.wrong_idea,
        question=trial.question,
        method=trial.method,
        discovery=trial.discovery,
        cause=trial.cause,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        ending=trial.ending,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    captain = world.captain.id
    friend = world.friend.id
    return [
        QAItem(
            question="What problem did the pirate friends face?",
            answer=f"They faced this problem: {world.facts['trouble']}. It put {world.facts['treasure']} at risk.",
        ),
        QAItem(
            question=f"How did {captain} and {friend} solve the problem?",
            answer=f"They followed the useful clue, worked together to {world.facts['method']}, and then {world.facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The cause was that someone {world.facts['cause']}. The friends learned the cause by comparing physical clues rather than guessing.",
        ),
        QAItem(
            question="How did friendship help the crew?",
            answer=f"{captain} and {friend} shared jobs, listened to each other, and {world.facts['repair']}. Their trust helped them stay calm and careful.",
        ),
        QAItem(
            question="How did they prove that the repair worked?",
            answer=f"They tested the result and saw that {world.facts['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a solid cover fitted over a window. It can block light, rain, or strong wind.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important in history or connected with the past.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which people trust, help, and enjoy time with one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding what went wrong, considering evidence, making a safe plan, and testing whether the plan works.",
        ),
        QAItem(
            question="What is a lighthouse?",
            answer="A lighthouse is a tower with a bright light that helps ships find the shore and avoid dangerous rocks.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly pirate tale at {THEME} in which {world.facts['treasure']} is threatened by a historic shutter.",
        f"Tell a friendship and problem-solving story using the clue {world.facts['clue']}. Include a safe repair and a bright ending image.",
        "Create a gentle pirate adventure with spoken dialogue, a historic object, and a shutter that causes a mystery.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    entities = [
        world.captain,
        world.friend,
        world.parrot,
        world.shutter,
        world.treasure,
        world.lighthouse,
        world.harbor,
    ]
    for entity in entities:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        if entity.carried_by:
            details.append(f"carried_by={entity.carried_by}")
        lines.append(f"  {entity.id:18} ({entity.kind:9}) {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor_lighthouse).
has_theme(harbor_lighthouse, historic).
has_theme(harbor_lighthouse, shutter).
has_feature(harbor_lighthouse, friendship).
has_feature(harbor_lighthouse, problem_solving).
style(harbor_lighthouse, pirate_tale).

valid_world(W) :-
    setting(W),
    has_theme(W, historic),
    has_theme(W, shutter),
    has_feature(W, friendship),
    has_feature(W, problem_solving),
    style(W, pirate_tale).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "harbor_lighthouse"),
            asp.fact("has_theme", "harbor_lighthouse", "historic"),
            asp.fact("has_theme", "harbor_lighthouse", "shutter"),
            asp.fact("has_feature", "harbor_lighthouse", "friendship"),
            asp.fact("has_feature", "harbor_lighthouse", "problem_solving"),
            asp.fact("style", "harbor_lighthouse", "pirate_tale"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_world/1."))
    ok = any(atom.name == "valid_world" for atom in models)
    if not ok:
        print("MISMATCH: ASP did not recognize the historic shutter pirate world.")
        return 1

    params = StoryParams(seed=17)
    sample = generate(params)
    required = ("historic", "shutter", "friendship", "problem")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative terms.")
        return 1
    if not sample.story_qa or not sample.world_qa:
        print("MISMATCH: generated story lacks QA coverage.")
        return 1

    print("OK: ASP and Python recognize the historic shutter friendship world.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--parrot", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    captain = args.captain or rng.choice(["Luna", "Mara", "Nell", "Tessa", "Ada"])
    friend = args.friend or rng.choice(["Pip", "Finn", "Jo", "Rafi", "Kit"])
    parrot = args.parrot or rng.choice(["Breezy", "Coco", "Skipper", "Feather", "Blue"])

    if captain == friend:
        raise StoryError("The captain and friend must have different names.")
    if parrot in {captain, friend}:
        raise StoryError("The parrot must have a different name from the children.")

    offset = sample_seed - base_seed
    return StoryParams(
        captain=captain,
        friend=friend,
        parrot=parrot,
        trial=offset % len(TRIALS),
        voice=(offset // len(TRIALS)) % 4,
        lesson_style=(offset // (len(TRIALS) * 4)) % 4,
        ending_style=(offset // (len(TRIALS) * 4 * 4)) % 3,
        seed=sample_seed,
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


CURATED = [
    StoryParams(captain="Luna", friend="Pip", parrot="Breezy", trial=0),
    StoryParams(captain="Mara", friend="Finn", parrot="Coco", trial=1),
    StoryParams(captain="Nell", friend="Jo", parrot="Skipper", trial=2),
    StoryParams(captain="Tessa", friend="Rafi", parrot="Blue", trial=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_world/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
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
