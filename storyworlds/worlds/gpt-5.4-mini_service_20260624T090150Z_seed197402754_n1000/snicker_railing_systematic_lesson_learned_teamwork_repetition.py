#!/usr/bin/env python3
"""
storyworlds/worlds/snicker_railing_systematic_lesson_learned_teamwork_repetition.py
===================================================================================

A small, self-contained storyworld about a strange railing, a few nervous
snickers, and a lesson learned through teamwork and repetition.

The tale style leans ghost-story: dim hallways, a creaky stair rail, a careful
little mystery, and a gentle ending where the characters prove they can face the
problem together.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

TOPIC_WORDS = ("snicker", "railing", "systematic")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    affords: set[str] = field(default_factory=lambda: {"inspect", "listen", "shine_light"})


@dataclass
class StoryParams:
    name: str
    helper_name: str
    parent_name: str
    mystery: int = 0
    plan: int = 0
    roles: int = 0
    refrain: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    place: str
    first_sound: str
    clue: str
    cause: str
    first_test: str
    second_test: str
    repair: str
    ending: str


MYSTERIES = [
    Mystery("the old house", "three quick snickers whenever the stair light dimmed", "a bright thread caught beneath the third spindle", "a loose scarf fringe brushing the wood", "held the light still while the other watched the spindles", "moved the scarf and heard the same three sounds", "tucked the scarf safely onto its hook", "the scarf hung still above a silent railing"),
    Mystery("the library loft", "a snicker each time someone climbed the last stair", "tiny wheel tracks in the dust", "a wind-up mouse trapped behind the bottom post", "marked each stair and climbed them one at a time", "pressed the marked steps again in reverse order", "lifted the toy mouse into its basket", "the toy mouse slept in its basket beside the quiet stairs"),
    Mystery("the rainy porch", "a wet little snicker after every gust", "three drops trembling on one iron curl", "a rain chain tapping a hollow railing cap", "watched one gust while counting each tap", "held the rain chain away and repeated the count", "fastened the chain to its proper ring", "raindrops slid silently down the chain into a blue barrel"),
    Mystery("the school theater", "a snicker whenever the curtain swayed", "a silver bell string peeking through the railing", "a costume bell caught between two posts", "tested the curtain, floor, and railing separately", "pulled the curtain twice while listening at each post", "freed the bell and returned it to the jester hat", "the jester hat waited onstage while the railing shone in peace"),
    Mystery("the moonlit museum", "a papery snicker beside the balcony railing", "a corner of a label fluttering near an air vent", "a loose exhibit label scraping the rail", "closed nearby doors one by one to trace the draft", "opened only the vent and heard the scrape return", "secured the label beneath its clear cover", "the label lay flat while moonlight striped the silent balcony"),
    Mystery("the seaside inn", "a salty snicker whenever the tide rose", "a line of sand beneath the seaward post", "a shell wedged in a crack and rocked by the wind", "listened at each post from the door toward the sea", "covered the crack, uncovered it, and compared the sounds", "set the shell on the windowsill and sealed the crack", "the shell gleamed on the sill above a calm, quiet railing"),
    Mystery("the clockmaker's landing", "a neat snicker at every quarter hour", "a brass spring glinting behind the newel post", "a toy clock spring clicking against the railing", "timed the sound against the hallway clock", "stopped the toy clock and waited through the next quarter hour", "returned the spring to the clockmaker's tray", "the hallway clock chimed over a railing that made no reply"),
    Mystery("the winter lodge", "a dry snicker whenever the heater woke", "warm air lifting one curled wood shaving", "a wood shaving fluttering inside the hollow rail", "checked the posts with the heater off", "turned the heater on and followed the flutter upward", "brushed out the shaving and fitted the cap snugly", "snow pressed the windows while the smooth railing stayed still"),
    Mystery("the garden observatory", "a leafy snicker as the dome turned", "a green tendril looped around the outer rail", "a pea vine dragging across the railing", "turned the dome in four small measured steps", "trimmed one loose leaf and repeated the four steps", "guided the vine onto a bamboo support", "the vine curled around its bamboo while stars filled the dome"),
    Mystery("the ferry's upper deck", "a snicker under the railing when the engine slowed", "a red ribbon flicking through a drainage slot", "a luggage ribbon snapping against the rail", "checked the rail once at cruising speed and once while slowing", "held the ribbon still during the next change of speed", "tied the ribbon firmly around its suitcase handle", "the red bow rode quietly above the silver wake"),
    Mystery("the community pool", "a bubbly snicker after each splash", "a row of bubbles escaping below the handrail", "a foam diving ring lodged over a water jet", "watched the jets in order from shallow end to deep", "lifted the ring, replaced it, and heard the bubbles return", "carried the diving ring back to the equipment bin", "blue ripples winked beneath a quiet, dripping handrail"),
    Mystery("the tree-house stair", "a nutty snicker whenever a squirrel crossed the roof", "acorn crumbs balanced on the top post", "an acorn rolling through the hollow bamboo railing", "tapped each bamboo section from bottom to top", "tipped the top section twice and followed the rolling sound", "shook out the acorn and capped the bamboo", "the acorn rested on a stump while sunset warmed the silent rail"),
]

PLANS = [
    ("make a numbered checklist from the first post to the last", "checked off each place only after both agreed on what they heard"),
    ("draw a simple map and divide the railing into four sections", "placed a chalk dot beside every section they had tested"),
    ("set out three cards marked LOOK, LISTEN, and TEST", "turned over one card after completing that step at every spot"),
    ("agree to change only one thing during each test", "wrote down what changed and what stayed the same"),
]

ROLE_PATTERNS = [
    ("held the lantern and called out each numbered place", "looked closely and recorded every clue", "swapped jobs halfway so each could check the other's work"),
    ("performed each careful test", "kept the checklist and compared the sounds", "paused after every test to agree before moving on"),
    ("watched the railing", "tested the nearby objects that might touch it", "shared their observations and chose the next test together"),
]

REFRAINS = [
    ("Look, listen, test", "They said it before every new check, and the steady words kept worry from rushing them."),
    ("One place, one change", "They repeated the rule whenever either child wanted to guess too soon."),
    ("Try it, note it, try once more", "The little chant helped them compare the first result with the second."),
    ("Together, then again", "Each repetition gave one child a turn to act and the other a turn to notice."),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_snicker(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    rail = world.entities.get("Railing")
    if not child or not rail:
        return out
    if child.memes.get("uneasy", 0.0) < 1.0:
        return out
    sig = ("snicker",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rail.memes["mysterious"] = rail.memes.get("mysterious", 0.0) + 1
    mystery = world.facts["mystery"]
    out.append(f"Then the sound came again, clearly this time: {mystery.first_sound}.")
    return out


def _r_systematic(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    helper = world.entities.get("Helper")
    rail = world.entities.get("Railing")
    if not child or not helper or not rail:
        return out
    if child.memes.get("determination", 0.0) < 1.0 or helper.memes.get("teamwork", 0.0) < 1.0:
        return out
    if rail.meters.get("checked", 0.0) < 3.0:
        return out
    sig = ("systematic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rail.memes["safe"] = rail.memes.get("safe", 0.0) + 1
    plan_finish = world.facts["plan"][1]
    out.append(f"That systematic plan worked: they {plan_finish}.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    rail = world.entities.get("Railing")
    helper = world.entities.get("Helper")
    if not rail or not helper:
        return out
    if rail.meters.get("checked", 0.0) < 2.0:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    refrain, meaning = world.facts["refrain"]
    out.append(f'"{refrain}," they repeated. {meaning}')
    return out


CAUSAL_RULES = [_r_snicker, _r_repetition, _r_systematic]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery % len(MYSTERIES)]
    plan = PLANS[params.plan % len(PLANS)]
    roles = ROLE_PATTERNS[params.roles % len(ROLE_PATTERNS)]
    refrain = REFRAINS[params.refrain % len(REFRAINS)]
    setting = Setting(place=mystery.place)
    world = World(setting)
    child = world.add(Entity(id="Child", kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type="girl", label=params.helper_name))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=params.parent_name))
    rail = world.add(Entity(id="Railing", kind="thing", type="railing", label="the railing"))

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        rail=rail,
        setting=setting,
        mystery=mystery,
        plan=plan,
        roles=roles,
        refrain=refrain,
    )

    world.say(
        f"Near bedtime in {setting.place}, {child.label} stopped beside {rail.label}. "
        "From somewhere below came a faint, secretive sound."
    )
    world.say(
        f'"That sounds like a sneaky snicker," {child.label} whispered. The mystery made his feet feel heavy.'
    )
    child.memes["uneasy"] = 1.0
    propagate(world, narrate=True)
    world.para()

    world.say(
        f"{helper.label} did not laugh at him or make a wild guess. She proposed a plan: they would {plan[0]}."
    )
    world.say(
        f'"Systematic means careful and in order," she said. "We will know why each test matters."'
    )
    child.memes["determination"] = 1.0
    helper.memes["teamwork"] = 1.0
    rail.meters["checked"] = 1.0

    world.para()
    world.say(
        f"Their teamwork gave each child a useful role. {child.label} {roles[0]}; {helper.label} {roles[1]}."
    )
    world.say(
        f"First they {mystery.first_test}. They noticed {mystery.clue}."
    )
    rail.meters["checked"] = 2.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Next they {mystery.second_test}. This time the result matched the clue."
    )
    world.say(f"They {roles[2]}. Soon they discovered the real cause: {mystery.cause}.")
    rail.meters["checked"] = 3.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"They explained every test to {parent.label}, then all three worked together and {mystery.repair}."
    )
    world.say(
        f"When they repeated the first test, the snicker did not return. {child.label}'s heavy feeling was gone."
    )
    world.say(
        f"He had learned a lasting lesson: repetition is useful when each careful try teaches the team something."
    )
    world.say(f"Before they left, they looked back. {mystery.ending.capitalize()}.")
    world.facts["lesson"] = "Careful repetition helps a team compare clues instead of repeating guesses."
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    return [
        f"Write a gentle mystery for a small child about {child.label}, a snicker, and a railing in {f['setting'].place}.",
        f"Tell a short story where systematic teamwork and repetition reveal {mystery.cause}.",
        "Write a simple lesson-learned story in which repeated tests solve a spooky railing sound without a real ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    rail = f["rail"]
    mystery = f["mystery"]
    refrain = f["refrain"][0]
    return [
        QAItem(
            question=f"Why did {child.label} feel nervous near {rail.label}?",
            answer=f"{child.label} felt nervous because {mystery.first_sound} seemed to come from {rail.label}. He did not yet know what caused it.",
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} solve the problem?",
            answer=f"They worked systematically, repeated a controlled test, and compared their observations. That evidence led them to {mystery.cause}.",
        ),
        QAItem(
            question=f"Why did the children repeat, '{refrain}'?",
            answer=f"The repeated words kept their teamwork orderly while they tested one clue at a time. Repetition helped them compare results instead of guessing.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn after the team found the cause?",
            answer=f"{child.label} learned that careful repetition helps a team compare clues instead of repeating guesses. The team proved the lesson when they {mystery.repair}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a railing?",
            answer="A railing is a bar or fence that people can hold onto, especially on stairs or porches.",
        ),
        QAItem(
            question="What does systematic mean?",
            answer="Systematic means doing something in an orderly, careful way, one step after another.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same action again and again, which can help you notice small details.",
        ),
        QAItem(
            question="What is a snicker?",
            answer="A snicker is a small quiet laugh, often the kind that sounds sneaky or silly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "snicker"),
            asp.fact("topic", "railing"),
            asp.fact("topic", "systematic"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("feature", "teamwork"),
            asp.fact("feature", "repetition"),
            asp.fact("place", "old_house"),
            asp.fact("affords", "old_house", "inspect"),
            asp.fact("affords", "old_house", "listen"),
            asp.fact("affords", "old_house", "shine_light"),
        ]
    )


ASP_RULES = r"""
topic(snicker).
topic(railing).
topic(systematic).
feature(lesson_learned).
feature(teamwork).
feature(repetition).

needs_repetition(repetition).
needs_teamwork(teamwork).
has_lesson(lesson_learned) :- needs_repetition(repetition), needs_teamwork(teamwork).

story_ok :- topic(snicker), topic(railing), topic(systematic), has_lesson(lesson_learned).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the story world.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a snickering railing and a lesson learned.")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent-name")
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


GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Ada", "Ruby"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Milo", "Jude"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Ben"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        name=name,
        helper_name=helper_name,
        parent_name=parent_name,
        mystery=rng.randrange(len(MYSTERIES)),
        plan=rng.randrange(len(PLANS)),
        roles=rng.randrange(len(ROLE_PATTERNS)),
        refrain=rng.randrange(len(REFRAINS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(sym.name == "story_ok" for sym in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(name="Mina", helper_name="Luna", parent_name="Mom")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        seen_structures: set[tuple[int, int, int, int]] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            structure = (params.mystery, params.plan, params.roles, params.refrain)
            if sample.story in seen or structure in seen_structures:
                continue
            seen.add(sample.story)
            seen_structures.add(structure)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
