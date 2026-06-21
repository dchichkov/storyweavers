#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py
==================================================================

A standalone storyworld for a small mythic domain:

A young hawk longs to understand how the little valley below can belong to the
same wide universe as the moon, stars, and sea. A patient elder shows that the
same patterns repeat in small and large things. The hawk then helps carry a
needed light or message to a dark place, proving the lesson in action.

The world uses repetition on purpose: "as above, so below" style echoing images
appear because the simulated state records observed patterns, belief, fear, and
the final act of help.

Run it
------
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py --sky stars --need ember
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py --lesson command
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py --all
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/hawk_relate_universe_repetition_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Sky:
    id: str
    dome: str
    light: str
    image: str
    vast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    speech: str
    repeat_line: str
    conclusion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    place: str
    lack: str
    carried: str
    solution: str
    success: str
    danger: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_pattern_belief(world: World) -> list[str]:
    out: list[str] = []
    hawk = world.get("hawk")
    elder = world.get("elder")
    if hawk.meters["pattern_seen"] >= THRESHOLD and hawk.memes["wonder"] >= THRESHOLD:
        sig = ("belief",)
        if sig not in world.fired:
            world.fired.add(sig)
            hawk.memes["belief"] += 1
            elder.memes["hope"] += 1
            out.append("__belief__")
    return out


def _r_belief_courage(world: World) -> list[str]:
    out: list[str] = []
    hawk = world.get("hawk")
    if hawk.memes["belief"] >= THRESHOLD and hawk.meters["task_seen"] >= THRESHOLD:
        sig = ("courage",)
        if sig not in world.fired:
            world.fired.add(sig)
            hawk.memes["courage"] += 1
            out.append("__courage__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="pattern_belief", tag="insight", apply=_r_pattern_belief),
    Rule(name="belief_courage", tag="action", apply=_r_belief_courage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SKIES = {
    "stars": Sky(
        id="stars",
        dome="the night sky",
        light="stars",
        image="each star looked like a bright seed strewn across dark velvet",
        vast="the wide universe",
        tags={"stars", "universe"},
    ),
    "moon": Sky(
        id="moon",
        dome="the blue-black sky",
        light="the moon",
        image="the moon hung like a silver feather above the hills",
        vast="the silent universe",
        tags={"moon", "universe"},
    ),
    "dawn": Sky(
        id="dawn",
        dome="the early sky",
        light="the red dawn",
        image="the red dawn spread in rings like a flower opening in the dark",
        vast="the waking universe",
        tags={"dawn", "universe"},
    ),
}

LESSONS = {
    "echo": Lesson(
        id="echo",
        speech="What the sky does in greatness, the valley does in smallness.",
        repeat_line="As above, so below.",
        conclusion="The universe likes to repeat its shapes where patient eyes can relate them.",
        tags={"pattern", "relate"},
    ),
    "feather": Lesson(
        id="feather",
        speech="One feather holds the curve of the wind, and one pool holds the curve of the sky.",
        repeat_line="One feather, one pool; one pool, one sky.",
        conclusion="So the little and the large belong to each other, and wise hearts relate them.",
        tags={"pattern", "relate"},
    ),
    "command": Lesson(
        id="command",
        speech="Remember this old saying: what circles in the heavens circles in the nest.",
        repeat_line="Circle above, circle below.",
        conclusion="That is how the hawks of the ridge relate their lives to the universe.",
        tags={"pattern", "relate"},
    ),
}

NEEDS = {
    "ember": Need(
        id="ember",
        place="the cedar shrine",
        lack="its dawn fire had gone out",
        carried="a red ember in a clay shell",
        solution="carry a small ember from the sun-stone altar",
        success="the shrine flame rose again, small as a seed and bright as a star",
        danger="the path crossed a windy gap where careless wings could spill the ember",
        tags={"fire", "help"},
    ),
    "message": Need(
        id="message",
        place="the shell tower by the sea",
        lack="the watchers there had not heard that the fog was coming",
        carried="a knotted reed message",
        solution="carry a warning message over the cliffs",
        success="the watchers lit their blue lamps before the fog arrived",
        danger="the path bent through sea gusts that could tear the reed away",
        tags={"message", "help"},
    ),
    "water": Need(
        id="water",
        place="the hilltop fig tree",
        lack="its roots were thirsty after many hot days",
        carried="a dripping moss cup",
        solution="bring spring water from the shaded rocks",
        success="the fig leaves lifted again and shone like little green hands",
        danger="the climb was steep, and one quick turn could spill the water",
        tags={"water", "help"},
    ),
}


def valid_combo(sky: Sky, lesson: Lesson, need: Need) -> bool:
    if sky.id == "dawn" and need.id == "ember":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sky_id, sky in SKIES.items():
        for lesson_id, lesson in LESSONS.items():
            for need_id, need in NEEDS.items():
                if valid_combo(sky, lesson, need):
                    combos.append((sky_id, lesson_id, need_id))
    return combos


@dataclass
class StoryParams:
    sky: str
    lesson: str
    need: str
    hawk_name: str
    elder_name: str
    seed: Optional[int] = None


HAWK_NAMES = ["Aru", "Sori", "Tala", "Ivo", "Neri", "Ketu", "Luma", "Rin"]
ELDER_NAMES = ["Old Wind", "Stone-Eye", "Ash-Wing", "River-Feather", "Cloud-Talon"]

CURATED = [
    StoryParams(
        sky="stars",
        lesson="echo",
        need="ember",
        hawk_name="Aru",
        elder_name="Old Wind",
    ),
    StoryParams(
        sky="moon",
        lesson="feather",
        need="message",
        hawk_name="Sori",
        elder_name="Stone-Eye",
    ),
    StoryParams(
        sky="dawn",
        lesson="command",
        need="water",
        hawk_name="Tala",
        elder_name="Ash-Wing",
    ),
]


def explain_rejection(sky: Sky, need: Need) -> str:
    if sky.id == "dawn" and need.id == "ember":
        return ("(No story: at dawn the world already has rising fire in the sky, "
                "so carrying an ember as the central sacred task feels redundant "
                "in this myth. Choose another sky or another need.)")
    return "(No story: this combination does not fit the myth's logic.)"


def observe_patterns(world: World, sky: Sky, lesson: Lesson) -> None:
    hawk = world.get("hawk")
    elder = world.get("elder")
    hawk.memes["wonder"] += 1
    hawk.meters["pattern_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the first days, when the ridges were still teaching their names to the wind, "
        f"there lived a young hawk called {hawk.id}. {hawk.id} flew beneath {sky.dome}, "
        f"and {sky.image}."
    )
    world.say(
        f"Yet the young hawk was troubled. 'How can this small valley relate to {sky.vast}?' "
        f"{hawk.pronoun()} asked. 'The nest is little, the river is little, and the universe is so wide.'"
    )
    world.say(
        f"Then {elder.id}, the oldest hawk on the ridge, settled beside {hawk.pronoun('object')} and said, "
        f'"{lesson.speech}"'
    )
    world.say(
        f"{elder.id} pointed with one dark wing. 'Look well,' {elder.pronoun()} said. "
        f'"{lesson.repeat_line}"'
    )
    world.say(
        f"So {hawk.id} looked once at the curve of a feather, once at the curve of a pool, "
        f"and once at the curve of the sky. Once at the feather, once at the pool, once at the sky."
    )


def present_need(world: World, need: Need, lesson: Lesson) -> None:
    hawk = world.get("hawk")
    elder = world.get("elder")
    hawk.meters["task_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That same day a cry rose from {need.place}: {need.lack}. The people below looked upward, "
        f"for only a hawk could {need.solution} before the hour turned."
    )
    world.say(
        f"{hawk.id} trembled. {need.danger}. The young hawk had swift wings, but not yet a steady heart."
    )
    if hawk.memes["courage"] >= THRESHOLD:
        world.say(
            f"Then {hawk.id} remembered the elder's words. '{lesson.repeat_line}' "
            f"The pattern returned like a drumbeat in {hawk.pronoun('possessive')} chest."
        )


def decide(world: World) -> None:
    hawk = world.get("hawk")
    elder = world.get("elder")
    if hawk.memes["courage"] < THRESHOLD:
        raise StoryError("The hawk never reached courage enough to act.")
    hawk.meters["flight"] += 1
    hawk.memes["resolve"] += 1
    world.say(
        f'"If the great sky can hold its light, then I can hold one small gift," {hawk.id} said.'
    )
    world.say(
        f"{elder.id} bowed {elder.pronoun('possessive')} head. "
        f'"Go, then. Relate the small to the great with your wings."'
    )


def perform_task(world: World, sky: Sky, need: Need, lesson: Lesson) -> None:
    hawk = world.get("hawk")
    hawk.meters["helped"] += 1
    world.say(
        f"{hawk.id} took {need.carried} and climbed into the high air. Above {hawk.pronoun('object')} was "
        f"{sky.light}; below {hawk.pronoun('object')} was the waiting earth. Above and below, below and above."
    )
    world.say(
        f"{hawk.pronoun().capitalize()} flew the windy gap without spilling, without dropping, without turning back."
    )
    world.say(
        f"When {hawk.pronoun()} reached {need.place}, {need.success}. Then the young hawk understood "
        f"{lesson.conclusion}"
    )


def closing_image(world: World, sky: Sky, lesson: Lesson, need: Need) -> None:
    hawk = world.get("hawk")
    elder = world.get("elder")
    hawk.memes["peace"] += 1
    world.say(
        f"From that day on, whenever {hawk.id} circled the ridge, {hawk.pronoun()} spoke the old line softly: "
        f'"{lesson.repeat_line}"'
    )
    world.say(
        f"And the children in the valley would point upward at the hawk and say that even a small wing "
        f"can teach how the universe holds together."
    )
    world.say(
        f"So the myth remembers {hawk.id}: once the seeker, then the helper, then the teller who could "
        f"relate sky and stone, great and small, above and below."
    )
    world.facts["ending_image"] = f"{hawk.id} circling beneath {sky.dome} above {need.place}"
    world.facts["elder"] = elder


def tell(sky: Sky, lesson: Lesson, need: Need, hawk_name: str, elder_name: str) -> World:
    if not valid_combo(sky, lesson, need):
        raise StoryError(explain_rejection(sky, need))

    world = World()
    hawk = world.add(Entity(id=hawk_name, kind="character", type="hawk", role="hero", label="young hawk"))
    elder = world.add(Entity(id="Elder", kind="character", type="hawk", role="elder", label="elder hawk"))
    elder.id = elder_name
    del world.entities["Elder"]
    world.entities[elder.id] = elder

    observe_patterns(world, sky, lesson)
    world.para()
    present_need(world, need, lesson)
    decide(world)
    world.para()
    perform_task(world, sky, need, lesson)
    closing_image(world, sky, lesson, need)

    world.facts.update(
        sky=sky,
        lesson=lesson,
        need=need,
        hawk=hawk,
        elder=elder,
        understood=hawk.memes["belief"] >= THRESHOLD,
        helped=hawk.meters["helped"] >= THRESHOLD,
        repeated=lesson.repeat_line,
    )
    return world


KNOWLEDGE = {
    "hawk": [
        (
            "What is a hawk?",
            "A hawk is a bird of prey with sharp eyes and strong wings. It can glide high above the ground and notice small things below."
        )
    ],
    "universe": [
        (
            "What does universe mean?",
            "The universe means everything there is: sky, stars, earth, water, and all the space around them. In stories, the word can make the world feel very large and full of wonder."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old-style story that explains the world with symbols, repeated lines, and memorable images. It often tells how people learned a lesson that feels bigger than one day."
        )
    ],
    "pattern": [
        (
            "What is a pattern?",
            "A pattern is something that repeats in a shape, sound, or action. Seeing a pattern helps you relate one thing to another."
        )
    ],
    "ember": [
        (
            "What is an ember?",
            "An ember is a small glowing piece of fire left after a flame burns down. It can still carry heat and light."
        )
    ],
    "message": [
        (
            "What is a message?",
            "A message is words sent from one place to another so someone can know something important. Messages help people act in time."
        )
    ],
    "water": [
        (
            "Why do trees need water?",
            "Trees need water because their roots drink it from the ground. Water helps leaves stay alive and green."
        )
    ],
}

KNOWLEDGE_ORDER = ["hawk", "universe", "myth", "pattern", "ember", "message", "water"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hawk = f["hawk"]
    sky = f["sky"]
    lesson = f["lesson"]
    need = f["need"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the words "hawk", "relate", and "universe".',
        f"Tell a mythic story where a young hawk learns that small things and great things repeat the same pattern, then uses that lesson to help at {need.place}.",
        f'Write a story with repetition, including the line "{lesson.repeat_line}", and end with a child-friendly image of the sky over the world below.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hawk = f["hawk"]
    elder = f["elder"]
    sky = f["sky"]
    lesson = f["lesson"]
    need = f["need"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young hawk named {hawk.id} and the elder hawk {elder.id}. The story follows how the younger bird learns and then helps others."
        ),
        (
            f"What question did {hawk.id} ask at the beginning?",
            f"{hawk.id} wondered how the small valley could relate to {sky.vast}. That question began the whole myth because the hawk wanted to understand how little things and great things belong together."
        ),
        (
            f"What did {elder.id} teach {hawk.id}?",
            f"{elder.id} taught that patterns repeat in small and large things, and said, '{lesson.repeat_line}' The lesson helped {hawk.id} see the universe as connected instead of broken into separate pieces."
        ),
        (
            "Why is the line repeated in the story?",
            f"The line is repeated because the hawk keeps remembering the lesson while looking, thinking, and flying. The repetition makes the idea feel old, strong, and easy to carry in the heart."
        ),
    ]
    if f["helped"]:
        qa.append(
            (
                f"How did {hawk.id} use the lesson to help?",
                f"{hawk.id} carried {need.carried} to {need.place}. The hawk became brave by thinking that if the great sky can hold its light, then one small wing can carry one small gift."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hawk.id} circling the ridge and softly repeating, '{lesson.repeat_line}' That ending image shows that the hawk truly changed, because the old question has become a lived lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hawk", "universe", "myth", "pattern"}
    need = f["need"]
    if need.id == "ember":
        tags.add("ember")
    elif need.id == "message":
        tags.add("message")
    elif need.id == "water":
        tags.add("water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, L, N) :- sky(S), lesson(L), need(N), not invalid(S, N).
invalid(dawn, ember).

understood :- observed_pattern, wondered.
courage :- understood, task_seen.

helped :- courage.
outcome(helped) :- helped.

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sky_id in SKIES:
        lines.append(asp.fact("sky", sky_id))
    for lesson_id in LESSONS:
        lines.append(asp.fact("lesson", lesson_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            "observed_pattern.",
            "wondered.",
            "task_seen.",
            f"chosen_sky({params.sky}).",
            f"chosen_lesson({params.lesson}).",
            f"chosen_need({params.need}).",
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def python_outcome(params: StoryParams) -> str:
    if not valid_combo(SKIES[params.sky], LESSONS[params.lesson], NEEDS[params.need]):
        return "invalid"
    return "helped"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a mythic hawk learns to relate the small world to the universe."
    )
    ap.add_argument("--sky", choices=SKIES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--hawk-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sky and args.need:
        sky = SKIES[args.sky]
        need = NEEDS[args.need]
        if not valid_combo(sky, LESSONS[args.lesson] if args.lesson else next(iter(LESSONS.values())), need):
            raise StoryError(explain_rejection(sky, need))

    combos = [
        c for c in valid_combos()
        if (args.sky is None or c[0] == args.sky)
        and (args.lesson is None or c[1] == args.lesson)
        and (args.need is None or c[2] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sky_id, lesson_id, need_id = rng.choice(sorted(combos))
    hawk_name = args.hawk_name or rng.choice(HAWK_NAMES)
    elder_name = args.elder_name or rng.choice([n for n in ELDER_NAMES if n != hawk_name])
    return StoryParams(
        sky=sky_id,
        lesson=lesson_id,
        need=need_id,
        hawk_name=hawk_name,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sky not in SKIES:
        raise StoryError(f"Unknown sky: {params.sky}")
    if params.lesson not in LESSONS:
        raise StoryError(f"Unknown lesson: {params.lesson}")
    if params.need not in NEEDS:
        raise StoryError(f"Unknown need: {params.need}")

    world = tell(
        sky=SKIES[params.sky],
        lesson=LESSONS[params.lesson],
        need=NEEDS[params.need],
        hawk_name=params.hawk_name,
        elder_name=params.elder_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        ao = asp_outcome(params)
        po = python_outcome(params)
        if ao != po:
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={ao} python={po}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sky, lesson, need) combos:\n")
        for sky, lesson, need in combos:
            print(f"  {sky:8} {lesson:8} {need}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hawk_name}: {p.sky}, {p.lesson}, {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
