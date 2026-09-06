#!/usr/bin/env python3
"""
A standalone storyworld for a fairy-tale reading nook:
- setting: a reading nook
- features: kindness, happy ending
- seed words: stride, convenient
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A reading nook story is reasonable when a little problem can be solved kindly.
kind_story(S) :- setting(S), has_kindness(S), has_happy_ending(S).
useful_help(H) :- help(H), convenient(H).
good_turn(S) :- kind_story(S), helpful_choice(S).
"""

PLACE = "reading nook"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    visitor: str
    object: str
    help_kind: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    failed_try: str
    clue: str
    visitor_line: str
    repair: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A child needs a name for the story.")
    if params.help_kind not in {"book", "lamp", "blanket", "stool"}:
        raise StoryError("The helpful item must be something gentle and fitting for a reading nook.")
    if params.object not in {"page", "book", "ribbon", "cup"}:
        raise StoryError("The scene needs a small storybook object, not a wild or dangerous one.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "reading_nook"),
        asp.fact("has_kindness", "reading_nook"),
        asp.fact("has_happy_ending", "reading_nook"),
        asp.fact("helpful_choice", "reading_nook"),
        asp.fact("help", "book"),
        asp.fact("help", "lamp"),
        asp.fact("help", "blanket"),
        asp.fact("help", "stool"),
        asp.fact("convenient", "book"),
        asp.fact("convenient", "lamp"),
        asp.fact("convenient", "blanket"),
        asp.fact("convenient", "stool"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_help_choices() -> list[str]:
    return ["book", "lamp", "blanket", "stool"]


NAMES = ["Mina", "Nora", "Liam", "Eli", "Luna", "Ivy", "Omar", "Tess"]
VISITORS = ["little fox", "tiny owl", "small mouse", "young rabbit", "shy hedgehog", "young badger"]
OBJECTS = ["book", "page", "ribbon", "cup"]

SCENARIOS = [
    Scenario(
        key="mixed_pages",
        premise="was arranging a picture-story display for the afternoon reading circle",
        trouble="A breeze from the open window scattered the numbered pages across three cushions.",
        failed_try="scooping them up quickly mixed the middle of the tale even more",
        clue="a painted moon grew a little fuller on each page",
        visitor_line='"The moons can show us what comes next," the visitor whispered.',
        repair="laid the pages in moon order, checked the story aloud, and tied them with the ribbon",
        result="The pictures now carried the characters from sunset all the way to morning.",
        lesson="a careful clue can be more useful than hurried hands",
        ending="the ordered pages shone like a row of tiny windows under the reading light",
    ),
    Scenario(
        key="rain_leak",
        premise="had prepared the nook for a rainy-day tale",
        trouble="A slow drip appeared above the shelf and crept toward the waiting storybook.",
        failed_try="holding one cup beneath the drip left the nearby books exposed to splashes",
        clue="the wet marks formed a line leading from the window latch",
        visitor_line='"The rain is coming through that little gap," the visitor said.',
        repair="closed the latch, caught the last drops, and moved every dry book to the far shelf",
        result="The leak stopped before a single page was spoiled.",
        lesson="kindness sometimes means protecting what everyone shares",
        ending="three raindrops rested outside the glass while the dry book lay open inside",
    ),
    Scenario(
        key="lost_marker",
        premise="was saving a place in a long adventure before snack time",
        trouble="The ribbon marker slipped behind the shelf, and nobody remembered the last page they had read.",
        failed_try="guessing a chapter brought them to the ending before the mystery had begun",
        clue="a faint silver star marked every chapter they had already finished",
        visitor_line='"Let us follow the stars instead of guessing," the visitor suggested.',
        repair="found the final starred chapter, retrieved the ribbon safely, and marked the next page",
        result="They returned to the exact moment when the hidden door was about to open.",
        lesson="patient remembering can be a kind gift to a reading partner",
        ending="the rescued ribbon rested between two pages beside one small silver star",
    ),
    Scenario(
        key="wobbly_stack",
        premise="was building a low display of favorite tales",
        trouble="The stack leaned toward the visitor each time another book was added.",
        failed_try="pressing down on the top made the narrow base tilt farther",
        clue="the widest book was perched at the very top instead of underneath",
        visitor_line='"Wide things make steadier beginnings," the visitor observed.',
        repair="rebuilt the stack from widest to smallest and tested it with one gentle tap",
        result="The little tower stood straight and left a clear path beside it.",
        lesson="a sound beginning keeps a good idea from toppling",
        ending="the smallest red book sat squarely atop a calm staircase of stories",
    ),
    Scenario(
        key="dim_picture",
        premise="had chosen a book whose pictures hid clues in deep blue ink",
        trouble="The corner was too dim for the visitor to see the tiny map inside the cover.",
        failed_try="holding the page close blocked the little light that was already there",
        clue="the map appeared whenever light crossed the paper from the side",
        visitor_line='"Perhaps the picture needs light, not closer eyes," the visitor said.',
        repair="turned the light gently, flattened the page, and traced the map without touching the ink",
        result="A silver path appeared between the painted trees.",
        lesson="help works best when it answers the problem that is really there",
        ending="a slim silver trail glimmered across the open map between their paws and hands",
    ),
    Scenario(
        key="noisy_hinge",
        premise="was about to begin the quietest part of a bedtime story",
        trouble="The little cupboard squeaked at every turn and startled the visitor out of the tale.",
        failed_try="opening it faster produced an even louder screech",
        clue="a loose wooden peg trembled whenever the door moved",
        visitor_line='"That peg is asking to be snug," the visitor said with a smile.',
        repair="pressed the peg into place, moved the door slowly, and tucked the needed supplies nearby",
        result="The cupboard opened with only a soft wooden sigh.",
        lesson="gentle attention can quiet a problem that force makes louder",
        ending="the cupboard stood peacefully ajar while the final sentence floated through the nook",
    ),
    Scenario(
        key="shy_reader",
        premise="had invited everyone to take one turn reading aloud",
        trouble="The visitor knew the words but froze when the reading circle looked their way.",
        failed_try="promising that the page was easy only made the visitor clutch it more tightly",
        clue="the visitor quietly mouthed every line when nobody interrupted",
        visitor_line='"Could we read the first part together?" the visitor asked.',
        repair="read in a soft duet, paused at each picture, and let the visitor choose the final line",
        result="By the last page, the visitor spoke one brave sentence alone.",
        lesson="kindness makes room for courage instead of demanding it",
        ending="two fingers pointed to the final word as the circle answered with quiet smiles",
    ),
    Scenario(
        key="torn_corner",
        premise="was opening an old story that many children loved",
        trouble="A brittle page corner caught on the cover and tore with a papery whisper.",
        failed_try="pulling the page free widened the tiny split",
        clue="the tear stopped whenever the page lay perfectly flat",
        visitor_line='"Let us keep it still before we mend it," the visitor said.',
        repair="flattened the page, placed a clear repair strip along the edge, and turned it from the middle",
        result="The words stayed readable, and the repaired corner flexed without tearing.",
        lesson="caring for an old thing lets many new friends enjoy it",
        ending="the mended corner caught a warm square of light without hiding a single letter",
    ),
    Scenario(
        key="rolling_cup",
        premise="had set water beside the cushions for a long chapter",
        trouble="The round cup rolled from a sloping tray toward the open book.",
        failed_try="catching the cup while balancing the book sent the tray sliding too",
        clue="one folded corner of the tray sat higher than the others",
        visitor_line='"We should level the tray before we fill the cup again," the visitor said.',
        repair="set the book safely aside, leveled the tray, and placed the cup in its deep holder",
        result="The next careful test left both cup and pages perfectly still.",
        lesson="solving the cause is kinder than blaming the thing that rolled",
        ending="a round reflection trembled inside the steady cup beside the dry book",
    ),
    Scenario(
        key="blocked_path",
        premise="was preparing a surprise shelf for the youngest readers",
        trouble="A basket of returned books blocked the visitor's short path into the nook.",
        failed_try="squeezing around it knocked a loose ribbon onto the floor",
        clue="three empty shelf spaces matched the labels on the returned books",
        visitor_line='"If we put these stories home, everyone gets a path," the visitor said.',
        repair="sorted the returns by label, shelved them together, and moved the basket under the table",
        result="A broad, convenient path opened between the doorway and the cushions.",
        lesson="tidying can be kindness when it makes a shared place welcoming",
        ending="the visitor took an easy stride down the clear path toward a green cushion",
    ),
    Scenario(
        key="missing_voice",
        premise="was rehearsing a story with a different voice for every character",
        trouble="The card naming the final character vanished just before the visitor's favorite scene.",
        failed_try="inventing a random voice made the brave captain sound like the sleepy dragon",
        clue="a triangle of blue paper peeked from beneath the cushion seam",
        visitor_line='"The captain card had a blue hat," the visitor remembered.',
        repair="lifted the cushion together, matched the blue card to the picture, and practiced the scene once",
        result="The captain returned with a bright voice just in time for the rescue.",
        lesson="listening to another person's memory can complete your own",
        ending="the blue character card stood beside the book as both friends gave a final bow",
    ),
    Scenario(
        key="drafty_corner",
        premise="had planned to finish a winter tale before the library bell",
        trouble="A chilly draft kept flipping the page whenever they reached the important riddle.",
        failed_try="pinning one corner with a finger let the other corner flutter shut",
        clue="the air slipped through a narrow space beneath the curtain",
        visitor_line='"We can stop the breeze without covering the pictures," the visitor said.',
        repair="blocked the low draft, steadied the open book, and read the riddle one line at a time",
        result="The page stayed open long enough for them to solve the snowy riddle together.",
        lesson="a small comfort can give a friend room to think",
        ending="the curtain rested still above two warm cushions and an open snowy page",
    ),
]

OPENINGS = [
    "Morning light made a golden square in the reading nook when {name} arrived.",
    "Just before story hour, {name} heard a hopeful rustle in the reading nook.",
    "The reading nook was quiet enough to hear one page turn as {name} stepped inside.",
    "On a drizzly afternoon, {name} saved the coziest corner of the reading nook for a guest.",
    "A paper sign beside the reading nook promised, 'Every reader belongs here.'",
    "The library bell had barely chimed when {name} entered the reading nook with a gentle stride.",
    "Between two tall shelves, the reading nook waited for {name} and one small visitor.",
    "Story hour was nearly ready, but the reading nook still held one problem to solve.",
]

REACTIONS = [
    "{name}'s first impulse was to hurry, but kindness asked for a better look.",
    '"We will not rush past your worry," {name} promised.',
    "{name} took one slow breath and asked what the visitor had noticed.",
    '"A convenient answer should also be a careful one," {name} said.',
    "Instead of taking over, {name} invited the visitor to inspect the problem too.",
    "For a moment {name} felt stuck; then the visitor's worried face made the next choice clear.",
    '"Let us solve the cause, not merely hide the mess," {name} decided.',
    "{name} stopped, listened, and made space for the visitor's idea.",
]

AID_ACTIONS = {
    "book": "opened the spare book as a sturdy guide and reference",
    "lamp": "angled the lamp toward the important clue",
    "blanket": "spread the blanket beneath their work to protect the books and cushion their knees",
    "stool": "placed the stool firmly on the level floor so they could work at a convenient height",
}

PLANS = [
    "They named one safe step each and agreed to check the result together.",
    "They divided the work: one watched the clue while the other handled the repair.",
    "Before moving anything, they cleared a convenient working space beside the cushions.",
    "They tried the smallest useful change first and watched what happened.",
    "Together they counted to three, then moved slowly enough to notice every change.",
    "They placed the fragile things out of harm's way before beginning the repair.",
    "They repeated the clue aloud so their plan answered the real problem.",
    "They chose roles that let both friends contribute instead of leaving one to watch.",
]

CELEBRATIONS = [
    "Neither friend needed a grand reward; seeing the worry disappear was enough.",
    "Their smiles came from the shared solution, not from being the one who was right.",
    "The visitor thanked {name}, and {name} thanked the visitor for the clue.",
    "They tested their work once more, then bumped elbows in a tiny celebration.",
    "Other readers noticed the result and quietly helped keep the nook welcoming.",
    "The solution felt warmer because both friends had shaped it.",
    "They left a small note explaining the kind fix for the next reader.",
    "The visitor's relieved grin made {name}'s careful stride feel lighter.",
]


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        visitor=rng.choice(VISITORS),
        object=rng.choice(OBJECTS),
        help_kind=rng.choice(valid_help_choices()),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale reading nook storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--visitor")
    ap.add_argument("--object")
    ap.add_argument("--help-kind", choices=valid_help_choices())
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.visitor:
        params.visitor = args.visitor
    if args.object:
        params.object = args.object
    if args.help_kind:
        params.help_kind = args.help_kind
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    visitor = world.add(Entity(id="visitor", kind="character", label=params.visitor))
    object_ent = world.add(Entity(id="object", kind="thing", label=params.object))
    helper = world.add(Entity(id="helper", kind="thing", label=params.help_kind))
    world.facts.update(
        hero=hero,
        visitor=visitor,
        object=object_ent,
        helper=helper,
        place=PLACE,
        kindness=True,
        happy_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    visitor = world.get("visitor")
    object_ent = world.get("object")
    helper = world.get("helper")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(name=hero.label)
    reaction = rng.choice(REACTIONS).format(name=hero.label)
    plan = rng.choice(PLANS)
    celebration = rng.choice(CELEBRATIONS).format(name=hero.label)
    aid_action = AID_ACTIONS[helper.label]

    hero.bump_meme("kindness")
    visitor.bump_meme("hope")

    world.say(opening)
    world.say(
        f"A {visitor.label} arrived carrying a {object_ent.label}, and {hero.label} welcomed the guest "
        f"with kindness. Together they settled in; {hero.label} {scenario.premise}."
    )
    world.para()
    world.say(scenario.trouble)
    world.say(f"At first, {hero.label} tried the quickest answer, but {scenario.failed_try}.")
    world.say(reaction)
    world.para()

    hero.bump_meme("care")
    visitor.bump_meme("curiosity")
    world.say(f"Then they found the useful clue: {scenario.clue}.")
    world.say(scenario.visitor_line)
    world.say(plan)
    world.para()

    helper.bump_meter("use", 1)
    world.say(
        f"With a calm stride, {hero.label} brought the {helper.label} closer and {aid_action}."
    )
    world.say(f"Working side by side, they {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    visitor.bump_meme("joy")
    hero.bump_meme("joy")
    world.say(celebration)
    world.say(f"They decided that {scenario.lesson}.")
    world.say(
        f"The thoughtful repair made the reading nook convenient for the next reader too. "
        f"As their happy ending, they shared the {object_ent.label}; {scenario.ending}."
    )
    world.facts.update(
        stride=True,
        convenient=True,
        scenario=scenario.key,
        premise=scenario.premise,
        trouble=scenario.trouble,
        failed_try=scenario.failed_try,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        lesson=scenario.lesson,
        ending_image=scenario.ending,
        aid_action=aid_action,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    visitor = f["visitor"].label
    helper = f["helper"].label
    scenario = str(f["scenario"]).replace("_", " ")
    return [
        f'Write a fairy-tale story set in a reading nook where {hero} helps {visitor} with kindness.',
        f"Tell a gentle story that uses the words stride and convenient and ends happily.",
        f"Write a child-friendly story about a {scenario} problem and a kind solution involving a {helper}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    visitor = f["visitor"].label
    helper = f["helper"].label
    obj = f["object"].label
    return [
        QAItem(
            question="What problem interrupted the visit to the reading nook?",
            answer=str(f["trouble"]),
        ),
        QAItem(
            question=f"What clue did {hero} and the {visitor} notice?",
            answer=f"They noticed that {f['clue']}.",
        ),
        QAItem(
            question=f"How did the {helper} help the friends carry out their plan?",
            answer=f"{hero} {f['aid_action']}, and together they {f['repair']}.",
        ),
        QAItem(
            question="What changed after the friends worked together?",
            answer=str(f["result"]),
        ),
        QAItem(
            question=f"What showed that the story had a happy ending?",
            answer=f"The friends shared the {obj}, and {f['ending_image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone cares about others and chooses to help in a gentle way.",
        ),
        QAItem(
            question="What does convenient mean?",
            answer="Convenient means easy to use or close by, so something can be done without much trouble.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the worry gets solved and the story finishes in a good, warm way.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


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


def asp_verify() -> int:
    import asp

    program = asp_program("#show kind_story/1.\n#show useful_help/1.\n#show good_turn/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(arg.name if arg.type != 1 else arg.string for arg in sym.arguments)) for sym in model)
    expected = {
        ("kind_story", ("reading_nook",)),
        ("useful_help", ("book",)),
        ("useful_help", ("lamp",)),
        ("useful_help", ("blanket",)),
        ("useful_help", ("stool",)),
        ("good_turn", ("reading_nook",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_turn/1."))
    return sorted(set(asp.atoms(model, "good_turn")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
    StoryParams(name="Mina", visitor="little fox", object="book", help_kind="lamp", seed=11),
    StoryParams(name="Nora", visitor="tiny owl", object="page", help_kind="stool", seed=29),
    StoryParams(name="Liam", visitor="small mouse", object="ribbon", help_kind="blanket", seed=47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_turn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible reading nook stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
