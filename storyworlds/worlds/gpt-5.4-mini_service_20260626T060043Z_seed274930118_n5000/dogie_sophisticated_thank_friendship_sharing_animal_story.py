#!/usr/bin/env python3
"""
A small animal story world about a dogie who learns friendship through sharing.

Premise:
A sophisticated little dogie wants a shiny ball. A friend also wants to play
with it. The dogie must choose between keeping the toy and keeping the friend.

World model:
- typed entities with meters and memes
- physical state: who owns the toy, who holds it, who shares it
- emotional state: joy, want, worry, gratitude, friendship
- causal turn: if the toy is held too long, the friend feels left out
- resolution: the dogie shares, says thank you, and friendship grows
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    friend_name: str
    toy: str
    setting: str = "the sunny yard"
    seed: Optional[int] = None


NAMES = ["Milo", "Pip", "Coco", "Toby", "Benny", "Luna", "Daisy", "Poppy"]
TOYS = [
    ("red ball", "a shiny red ball"),
    ("yellow rope", "a bright yellow rope"),
    ("blue ring", "a blue ring toy"),
]
SETTINGS = ["the sunny yard", "the little park", "the quiet garden"]


# ---------------------------------------------------------------------------
# Narrative plans
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StoryArc:
    title: str
    premise: str
    selfish_choice: str
    consequence: str
    friend_line: str
    shared_action: str
    result: str
    ending: str


ARCS = (
    StoryArc(
        "runaway hill",
        "A breeze sent {toy} wobbling toward the little hill, and both friends dashed after it.",
        "{dog} reached it first and tucked it beneath one paw, refusing {friend}'s offer to guard the lower path.",
        "The next gust slipped under that paw, and the toy bounded toward a patch of prickly burdock.",
        '"One pup cannot block a whole hill," {friend} called. "Let me help before it gets stuck!"',
        "{dog} rolled the toy sideways while {friend} made a soft wall of leaves; together they steered it to level ground.",
        "Neither could have saved it alone, but their two-part plan worked.",
        "They rested nose to nose beside the rescued toy as two neat trails curved down the hill behind them.",
    ),
    StoryArc(
        "rain shelter",
        "A quick silver rain began tapping the leaves just as the friends brought out {toy}.",
        "Wanting the driest spot, {dog} carried both the toy and the only broad leaf beneath the bench.",
        "{friend} stayed in the drizzle, and soon the wet ground made the game slippery and glum.",
        '"The leaf is wide enough for friendship," {friend} said quietly. "Could we hold it together?"',
        "They each gripped one edge of the leaf, sheltered the toy between them, and invented a gentle rainy-day passing game.",
        "Sharing the shelter kept both friends dry enough to play and made the pattering rain sound merry.",
        "At sunset, two damp tails curled from beneath one green roof while the toy waited safely between them.",
    ),
    StoryArc(
        "wobbly bridge",
        "Beside a shallow stream, {friend} proposed carrying {toy} across a bridge made from three flat boards.",
        "{dog} insisted on crossing first with the toy, although one board rocked under every step.",
        "The loose board tipped; the toy stopped at the edge, and {dog} froze in the middle.",
        '"Pass it to me, then keep your paws still," {friend} said. "We can solve this from both sides."',
        "{dog} passed the toy across. {friend} held the board steady while {dog} stepped down, and then they crossed side by side.",
        "Trusting a friend turned a frightening crossing into a careful piece of teamwork.",
        "On the far bank, the toy sat on a warm stone while two sets of pawprints dried beside the sparkling stream.",
    ),
    StoryArc(
        "muddy treasure",
        "During a lively game, {toy} landed with a plop in a stripe of soft mud.",
        "Embarrassed that the fine toy looked messy, {dog} hid it behind a flowerpot and claimed the game was over.",
        "{friend} searched alone and began to think the missing toy was somehow their fault.",
        '"I would rather wash it with you than wonder alone," {friend} said after spotting one muddy track.',
        "{dog} admitted what happened. One friend pumped water while the other brushed away the mud, and they traded jobs halfway through.",
        "The honest explanation and shared work cleaned both the toy and the misunderstanding.",
        "Soon four clean paws framed the drying toy, which shone in a puddle like a small moon.",
    ),
    StoryArc(
        "secret hiding place",
        "The friends planned a finding game in which one would hide {toy} and the other would follow clues.",
        "{dog} chose every hiding place and kept every clue, hoping to look like the cleverest player.",
        "With no real turn to take, {friend} stopped guessing and sat beneath a fern.",
        '"A mystery needs two minds," {friend} explained. "May I hide it and make clues too?"',
        "They divided the game fairly: {dog} drew a pawprint map, {friend} tied grass markers, and each solved the other's trail.",
        "The toy became more exciting once cleverness was something they could exchange.",
        "Their last two clues crossed beneath the fern, where both friends found the toy and burst into laughter together.",
    ),
    StoryArc(
        "new pup",
        "A shy new pup lingered near the gate while {dog} and {friend} prepared to play with {toy}.",
        "{dog} whispered that two players already made a perfectly orderly game and turned away from the newcomer.",
        "The new pup's ears drooped, and even {friend}'s happiest toss landed without a cheer.",
        '"Good manners should make room, not close it," {friend} reminded {dog}.',
        "{dog} invited the pup to begin. The three made a passing triangle, calling each name before sending the toy onward.",
        "Giving away the first turn did not shrink the game; it gave the friendship a new side.",
        "Three tails swept the grass in a triangle while the toy traveled from friend to friend beneath the gate's long shadow.",
    ),
    StoryArc(
        "tender paw",
        "{friend} arrived eager to play but had a tender front paw and could not chase {toy} safely.",
        "{dog} raced through the usual game alone, certain that watching such graceful speed should be entertaining enough.",
        "Each fast lap left {friend} farther outside the fun, despite a brave little smile.",
        '"I can still aim and count," {friend} said. "Could our game use those jobs?"',
        "{dog} slowed down and shared every decision: {friend} chose targets and kept score while {dog} fetched and returned the toy.",
        "Changing the rules let each friend's different strength matter.",
        "When the final point was counted, the toy rested beside {friend}'s bandaged paw and both names filled the scorecard.",
    ),
    StoryArc(
        "picnic wind",
        "At a small animal picnic, a gust lifted three napkins and sent them skittering past {toy}.",
        "{dog} hugged the toy and chased only the napkin nearest their own bowl.",
        "The other napkins sailed toward the pond while {friend} scrambled after both.",
        '"Please roll me the toy," {friend} cried. "It can pin one napkin while we catch the other!"',
        "{dog} shared it at once. {friend} blocked one napkin with the toy, and {dog} caught the last beneath a careful paw.",
        "Using a prized thing to help everyone saved the picnic and felt better than merely guarding it.",
        "That evening, three napkins fluttered safely on the line and the toy held down the picnic cloth between two bowls.",
    ),
    StoryArc(
        "twilight path",
        "The game lasted until twilight, when the path home became a ribbon of blue shadow.",
        "Because {toy} caught the final light, {dog} kept it close and hurried several paces ahead.",
        "Behind them, {friend} missed a root and whispered that the dark path felt too large.",
        '"Could we carry the bright toy between us?" {friend} asked. "Then we can both see."',
        "They walked shoulder to shoulder with the toy between their paws, taking turns pointing out roots and stones.",
        "Sharing its glimmer made the path safer, and listening made each friend braver.",
        "At the gate, the last light gleamed on the toy between two touching paws, with no one left in the dark.",
    ),
    StoryArc(
        "garden gate",
        "A fallen twig jammed the garden gate just as {toy} rolled through to the other side.",
        "{dog} squeezed beneath the gate alone and guarded the toy, pleased to have won the race.",
        "The gate settled lower, leaving {friend} outside with no safe way through.",
        '"Winning is not much fun from opposite sides," {friend} said. "Will you help lift while I pull the twig?"',
        "{dog} set down the toy and lifted the gate. {friend} tugged the twig free, then held the gate so {dog} could return.",
        "They chose being together over possessing the winning side, and the game could begin again.",
        "The open gate clicked softly in the breeze as the toy rolled back and forth across its shadow.",
    ),
    StoryArc(
        "rhythm game",
        "{friend} discovered that tapping {toy} made a funny rhythm for a marching game.",
        "{dog} took over as conductor, choosing every beat and correcting every playful sound.",
        "The march grew polished but joyless, and {friend}'s paws became still.",
        '"Sophisticated music can listen as well as lead," {friend} said. "May my rhythm answer yours?"',
        "{dog} tapped a soft pattern, {friend} answered with a bouncy one, and they shared the toy between each musical reply.",
        "The two rhythms made a livelier song because neither friend had to disappear inside the other's plan.",
        "Their final notes faded under the trees while the toy sat between them like the round dot at the end of a tune.",
    ),
    StoryArc(
        "birthday gift",
        "The newest birthday gift for {dog} was {toy}, and {friend} came carrying a handmade card.",
        "Afraid of a scratch, {dog} displayed the toy on a stump but would not let {friend} touch it.",
        "The careful display made the visit feel like a museum where only one friend belonged.",
        '"I brought the card to celebrate with you," {friend} said, "not only to look from far away."',
        "{dog} spread the card beneath the toy as a safe play mat, offered {friend} the first turn, and showed how to handle it gently.",
        "Clear care and generous sharing protected the gift without pushing the friend away.",
        "Before bedtime, the card and toy stood together on the shelf, and two tiny paw marks signed the day's memory.",
    ),
)


OPENINGS = (
    "In {setting}, {dog} arrived early to arrange a proper game with {friend}.",
    "{friend} heard a cheerful bark in {setting}: {dog} had brought something special for their afternoon together.",
    "The best-kept whiskers in {setting} belonged to {dog}, who was meeting {friend} for a game.",
    "A game with {friend} was marked neatly on {dog}'s little schedule for that day in {setting}.",
    "In {setting}, {dog} polished one muddy paw on the grass before greeting {friend} with a careful bow.",
)

REALIZATIONS = (
    "For the first time, {dog} noticed that careful manners were hollow if a friend still felt shut out.",
    "{dog} looked from the guarded toy to {friend}'s face and understood that fairness needed an action, not merely a fine word.",
    "A sophisticated plan, {dog} realized, should care for every player rather than make one pup feel important.",
    "The quiet between them helped {dog} see the real problem: the toy was being protected while the friendship was not.",
    "{dog} remembered that friendship grows through shared choices, then took one slow breath and changed the plan.",
)

GRATITUDE_LINES = (
    '"Thank you for telling me what you needed," {dog} said. "Let us mend this together."',
    '"I was guarding the wrong thing," {dog} admitted. "Thank you for giving me another chance."',
    '"Thank you for being patient," {dog} said. "Your idea makes room for both of us."',
    '"I understand now," {dog} said. "Thank you for speaking honestly, my friend."',
    '"Thank you for helping me choose friendship," {dog} said, nudging the toy into the middle.',
)


def _toy_phrase(label: str) -> str:
    return dict(TOYS).get(label, f"a {label}")


def _story_choices(params: StoryParams) -> tuple[StoryArc, str, str, str]:
    seed = params.seed if params.seed is not None else 0
    arc = ARCS[seed % len(ARCS)]
    opening = OPENINGS[(seed // len(ARCS)) % len(OPENINGS)]
    realization = REALIZATIONS[(seed // (len(ARCS) * len(OPENINGS))) % len(REALIZATIONS)]
    gratitude = GRATITUDE_LINES[(seed // (len(ARCS) * len(OPENINGS) * len(REALIZATIONS))) % len(GRATITUDE_LINES)]
    return arc, opening, realization, gratitude


def build_world(params: StoryParams) -> World:
    world = World()
    dogie = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="dogie",
            label="dogie",
            traits=["sophisticated", "kind"],
            meters={"calm": 1.0},
            memes={"joy": 1.0, "friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="dogie",
            label="friend",
            traits=["gentle", "playful"],
            meters={"calm": 1.0},
            memes={"joy": 1.0, "friendship": 1.0},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            kind="thing",
            type="toy",
            label=params.toy,
            phrase=_toy_phrase(params.toy),
            owner=dogie.id,
            held_by=dogie.id,
            meters={"clean": 1.0},
        )
    )

    arc, opening, realization, gratitude = _story_choices(params)
    values = {
        "dog": dogie.id,
        "friend": friend.id,
        "toy": toy.phrase,
        "setting": params.setting,
    }

    world.say(opening.format(**values))
    world.say(
        f"{dogie.id} was a sophisticated little dogie: observant, orderly, and fond of graceful solutions. "
        "Sophisticated did not mean knowing everything; it meant trying to think with care."
    )
    world.para()
    world.say(arc.premise.format(**values))
    dogie.memes["want"] = dogie.memes.get("want", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    world.say(arc.selfish_choice.format(**values))
    world.say(arc.consequence.format(**values))
    world.say(arc.friend_line.format(**values))
    world.para()
    world.say(realization.format(**values))
    world.say(gratitude.format(**values))
    world.say(arc.shared_action.format(**values))
    dogie.memes["kindness"] = dogie.memes.get("kindness", 0) + 1
    dogie.memes["thank"] = dogie.memes.get("thank", 0) + 1
    dogie.memes["friendship"] = dogie.memes.get("friendship", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    toy.held_by = None
    world.para()
    world.say(arc.result.format(**values))
    world.say(
        "The dogie had learned that sharing is not losing a treasure. It is choosing to let friendship shape what happens next."
    )
    world.say(arc.ending.format(**values))

    world.facts.update(
        dogie=dogie,
        friend=friend,
        toy=toy,
        setting=params.setting,
        arc=arc,
        conflict=arc.consequence.format(**values),
        friend_line=arc.friend_line.format(**values),
        shared_action=arc.shared_action.format(**values),
        result=arc.result.format(**values),
        ending=arc.ending.format(**values),
        gratitude=gratitude.format(**values),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dogie: Entity = f["dogie"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    toy: Entity = f["toy"]  # type: ignore[assignment]
    setting = f["setting"]
    arc: StoryArc = f["arc"]  # type: ignore[assignment]
    return [
        f'Write a short animal story about a sophisticated dogie named {dogie.id} who learns to thank a friend.',
        f"Tell a gentle story set in {setting} where {dogie.id} and {friend.id} share {toy.phrase}.",
        f'Create a child-friendly {arc.title} story about friendship and sharing with the words "dogie", "sophisticated", and "thank".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dogie: Entity = f["dogie"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    toy: Entity = f["toy"]  # type: ignore[assignment]
    setting = f["setting"]
    conflict = str(f["conflict"])
    friend_line = str(f["friend_line"])
    shared_action = str(f["shared_action"])
    result = str(f["result"])
    ending = str(f["ending"])
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {dogie.id}, a sophisticated little dogie, and {friend.id}, the friend who played with {toy.phrase} in {setting}.",
        ),
        QAItem(
            question=f"What went wrong after {dogie.id} tried to control the game?",
            answer=conflict,
        ),
        QAItem(
            question=f"How did {friend.id} help {dogie.id} understand the problem?",
            answer=f"{friend.id} spoke honestly about what the friends needed. In the story, {friend_line}",
        ),
        QAItem(
            question=f"What sharing plan solved the problem with the {toy.label}?",
            answer=f"The friends solved it together. {shared_action} {result}",
        ),
        QAItem(
            question="What final image shows that their friendship changed?",
            answer=ending,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, so everyone can take part.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm connection between friends who care about each other and like spending time together.",
        ),
        QAItem(
            question="Why is saying thank you polite?",
            answer="Saying thank you is polite because it shows you notice kindness and feel grateful for help or gifts.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: friendship and sharing.")
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--toy", choices=[t[0] for t in TOYS])
    ap.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(NAMES)
    friend_choices = [n for n in NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friend_choices)
    toy = args.toy or rng.choice([t[0] for t in TOYS])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(name=name, friend_name=friend_name, toy=toy, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(sunny_yard).
setting(little_park).
setting(quiet_garden).

character(D) :- dogie(D).
character(F) :- friend(F).

shares(D, T) :- dogie(D), toy(T).
happy_end(D, F, T) :- shares(D, T), friend(F), dogie(D).

#show happy_end/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("dogie", n))
        lines.append(asp.fact("friend", n))
    for toy, _phrase in TOYS:
        lines.append(asp.fact("toy", toy))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s.replace("the ", "").replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # This world has a simple declarative twin; verify the program parses and solves.
    import asp
    model = asp.one_model(asp_program("#show happy_end/3."))
    if model is not None:
        print("OK: ASP twin solved successfully.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (toy, _phrase) in enumerate(TOYS):
            params = StoryParams(
                name=NAMES[i % len(NAMES)],
                friend_name=NAMES[(i + 1) % len(NAMES)],
                toy=toy,
                setting=SETTINGS[i % len(SETTINGS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
