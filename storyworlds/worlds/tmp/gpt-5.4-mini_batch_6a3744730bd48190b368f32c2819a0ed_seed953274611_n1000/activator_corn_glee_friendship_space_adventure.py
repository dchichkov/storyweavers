#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/activator_corn_glee_friendship_space_adventure.py
=================================================================================

A tiny Storyweavers storyworld for a friendship-powered space adventure.

Premise:
- Two friends are preparing a small space mission.
- One eager child wants to use an "activator" to start the mission console.
- A shared snack of corn and a burst of glee help them cooperate.
- The adventure turns on whether they work together, ask for help, and safely
  activate the ship's systems.

This world is intentionally compact:
- typed entities with physical meters and emotional memes
- a forward-chaining world model
- a reasonableness gate
- inline ASP twin
- generated stories, prompts, grounded QA, and world knowledge QA

It is standalone stdlib Python, importing storyworlds/results eagerly and
storyworlds/asp lazily inside ASP helpers only.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GLEE_BOOST = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Theme:
    id: str
    scene: str
    ship: str
    goal: str
    sky: str
    adventure_verb: str
    send_off: str


@dataclass
class Activator:
    id: str
    label: str
    phrase: str
    effect: str
    where: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Corn:
    id: str
    label: str
    phrase: str
    crunch: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_glee(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.kind == "character"]
    if all(e.memes["glee"] >= THRESHOLD for e in crew) and crew:
        sig = ("glee",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in crew:
                e.memes["trust"] += 1
            out.append("__glee__")
    return out


def _r_activate(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("activated"):
        ship = world.entities.get("ship")
        if ship and ship.meters["spark"] >= THRESHOLD and ("spark",) not in world.fired:
            world.fired.add(("spark",))
            ship.meters["launch_ready"] += 1
            out.append("__spark__")
    return out


CAUSAL_RULES = [
    Rule("glee", "social", _r_glee),
    Rule("activate", "physical", _r_activate),
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


def is_reasonable(activator: Activator, corn: Corn) -> bool:
    return activator.safe and corn.safe


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for theme in THEMES:
        for act in ACTIVATORS:
            for c in CORN:
                if is_reasonable(ACTIVATORS[act], CORN[c]):
                    combos.append((theme, act))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: (r.sense, r.power))


def outcome_of(params: "StoryParams") -> str:
    if params.shared_plan:
        return "shared"
    return "launched" if RESPONSES[params.response].power >= params.delay + 1 else "stalled"


def predict(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "launch_ready": sim.get("ship").meters["launch_ready"],
        "trust": sum(e.memes["trust"] for e in sim.entities.values() if e.kind == "character"),
    }


def setup(world: World, a: Entity, b: Entity, theme: Theme, activator: Activator, corn: Corn) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    a.memes["glee"] += 1
    b.memes["glee"] += 1
    world.say(
        f"On a bright day among the stars, {a.id} and {b.id} turned their room into {theme.scene}. "
        f"{theme.ship}"
    )
    world.say(
        f'"We can reach {theme.goal}!" {a.id} shouted, grinning at the little {corn.label} bowl '
        f'and the shiny {activator.label}.'
    )


def friendship(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"{b.id} smiled back. {b.id} knew {a.id} loved the mission, and {a.id} knew "
        f"{b.id} never left a friend behind."
    )
    world.say(
        f"Together they made a plan to {theme.adventure_verb}, sharing the work like true friends."
    )


def tempt(world: World, a: Entity, activator: Activator, corn: Corn) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'{a.id} picked up the {activator.label} and said, "{activator.phrase}!" '
        f"Then {a.id} laughed, because even the {corn.label} crumbs seemed to sparkle like moons."
    )


def warn(world: World, b: Entity, a: Entity, theme: Theme, activator: Activator, corn: Corn) -> None:
    pred = predict(world)
    b.memes["care"] += 1
    world.facts["predicted_trust"] = pred["trust"]
    world.say(
        f'{b.id} touched {a.pronoun("possessive")} sleeve and said, '
        f'"Let\'s do this the safe way. The {activator.label} can help, but only if we use it together."'
    )
    world.say(
        f"{b.id} pointed at the map and at the {corn.label} bowl. "
        f"They wanted to keep the ship clean for {theme.goal}."
    )


def shared_plan(world: World, a: Entity, b: Entity, activator: Activator, corn: Corn, theme: Theme) -> None:
    world.facts["shared_plan"] = True
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f'{a.id} nodded. "{activator.label.capitalize()} first, then corn for a snack, and then we launch," '
        f'{a.id} said with glee.'
    )
    world.say(
        f"{b.id} laughed, and the two friends ate a little {corn.label} together while the console blinked green."
    )


def activate(world: World, a: Entity, b: Entity, activator: Activator, theme: Theme) -> None:
    world.facts["activated"] = True
    ship = world.get("ship")
    ship.meters["spark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last, {a.id} pressed the {activator.label}. {activator.effect} and the ship hummed softly."
    )
    world.say(
        f"A little light jumped across the control panel, like a star waking up to say hello."
    )


def launch(world: World, theme: Theme) -> None:
    ship = world.get("ship")
    ship.meters["launch_ready"] += 1
    world.say(
        f"The friends held hands and watched the ship glow. {theme.send_off.capitalize()}."
    )
    world.say(
        f"Outside the window, {theme.sky} looked wide and friendly, as if the whole space wanted them to succeed."
    )


def stall(world: World, a: Entity, b: Entity) -> None:
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"The buttons blinked, but nothing important started. So {a.id} and {b.id} took a breath and tried again together."
    )


THEMES = {
    "orbit": Theme(
        id="orbit",
        scene="a little moon base",
        ship="A tiny tin ship waited by the wall, with a round window and a paper-rocket nose.",
        goal="the silver moon ridge",
        sky="the black sky",
        adventure_verb="explore the moon ridge",
        send_off="Their pretend ship slid forward with a happy whirr",
    ),
    "comet": Theme(
        id="comet",
        scene="a comet lookout",
        ship="Their cardboard ship sat beside a map of shining tails and tiny stars.",
        goal="the comet tail",
        sky="the bright comet trail",
        adventure_verb="follow the comet tail",
        send_off="The ship seemed to bounce with excitement",
    ),
    "garden": Theme(
        id="garden",
        scene="a star garden",
        ship="A blanket ship sat under glowing stickers, ready for a space trip at once.",
        goal="the farthest star patch",
        sky="the violet night",
        adventure_verb="visit the star patch",
        send_off="The pretend engines sighed and then sang",
    ),
}

ACTIVATORS = {
    "activator": Activator(
        id="activator",
        label="activator",
        phrase="I found the activator!",
        effect="The activator clicked, glowed, and woke the little ship console",
        where="on the table",
        safe=True,
        tags={"activator"},
    ),
    "button": Activator(
        id="button",
        label="starter button",
        phrase="This starter button can help us",
        effect="The starter button blinked a soft blue",
        where="by the map",
        safe=True,
        tags={"activator"},
    ),
}

CORN = {
    "corn": Corn(
        id="corn",
        label="corn",
        phrase="a bowl of corn",
        crunch="crunch-crunch",
        safe=True,
        tags={"corn"},
    ),
    "popcorn": Corn(
        id="popcorn",
        label="corn",
        phrase="a little bowl of corn",
        crunch="pop-pop",
        safe=True,
        tags={"corn"},
    ),
}

RESPONSES = {
    "careful": Response(
        id="careful",
        sense=3,
        power=3,
        text="carefully lined up the controls, checked the map, and pressed the right switch",
        fail="pressed the wrong switch again and again, but the ship still stayed quiet",
        qa_text="carefully lined up the controls, checked the map, and pressed the right switch",
        tags={"help", "friendship"},
    ),
    "together": Response(
        id="together",
        sense=4,
        power=4,
        text="asked for help, and together they pressed the right switch at the same time",
        fail="kept trying alone, but the ship would not answer",
        qa_text="asked for help and pressed the right switch together",
        tags={"help", "friendship"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Nia", "Luna", "Ivy"]
BOY_NAMES = ["Noah", "Leo", "Eli", "Kai", "Finn", "Theo"]


@dataclass
class StoryParams:
    theme: str
    activator: str
    corn: str
    response: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    delay: int = 0
    shared_plan: bool = False
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship-powered space adventure storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--activator", choices=ACTIVATORS)
    ap.add_argument("--corn", choices=CORN)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the console resists")
    ap.add_argument("--shared-plan", action="store_true")
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


def valid_pair(a: str, b: str) -> bool:
    return a != b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activator and args.activator not in ACTIVATORS:
        raise StoryError("Unknown activator.")
    if args.corn and args.corn not in CORN:
        raise StoryError("Unknown corn option.")
    if args.activator and args.corn:
        if not is_reasonable(ACTIVATORS[args.activator], CORN[args.corn]):
            raise StoryError("That activator/corn combination is not reasonable for this story.")
    theme = args.theme or rng.choice(list(THEMES))
    activator = args.activator or rng.choice(list(ACTIVATORS))
    corn = args.corn or rng.choice(list(CORN))
    response = args.response or rng.choice(list(RESPONSES))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or ("boy" if gender_a == "girl" else "girl")
    if not valid_pair(args.name_a or "A", args.name_b or "B"):
        raise StoryError("The two friends need different names.")
    name_a = args.name_a or rng.choice(GIRL_NAMES if gender_a == "girl" else BOY_NAMES)
    name_b = args.name_b or rng.choice([n for n in (GIRL_NAMES if gender_b == "girl" else BOY_NAMES) if n != name_a])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    shared_plan = bool(args.shared_plan or rng.choice([False, True, False]))
    return StoryParams(
        theme=theme,
        activator=activator,
        corn=corn,
        response=response,
        friend_a=name_a,
        friend_a_gender=gender_a,
        friend_b=name_b,
        friend_b_gender=gender_b,
        delay=delay,
        shared_plan=shared_plan,
    )


def tell(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.theme]
    activator = ACTIVATORS[params.activator]
    corn = CORN[params.corn]
    response = RESPONSES[params.response]

    a = world.add(Entity(id=params.friend_a, kind="character", type=params.friend_a_gender, role="friend"))
    b = world.add(Entity(id=params.friend_b, kind="character", type=params.friend_b_gender, role="friend"))
    ship = world.add(Entity(id="ship", type="ship", label="ship"))

    setup(world, a, b, theme, activator, corn)
    world.para()
    friendship(world, a, b, theme)
    tempt(world, a, activator, corn)
    warn(world, b, a, theme, activator, corn)

    if params.shared_plan:
        shared_plan(world, a, b, activator, corn, theme)
        activate(world, a, b, activator, theme)
        launch(world, theme)
        outcome = "shared"
    else:
        a.memes["defiance"] += 1
        world.say(f"{a.id} paused, then nodded at {b.id}. Friendship made the choice feel easy.")
        world.para()
        activate(world, a, b, activator, theme)
        if response.power >= params.delay + 1:
            world.say(
                f"{b.id} grinned and used {response.qa_text}. The ship answered at once."
            )
            launch(world, theme)
            outcome = "launched"
        else:
            stall(world, a, b)
            outcome = "stalled"

    world.facts.update(
        friend_a=a,
        friend_b=b,
        theme=theme,
        activator=activator,
        corn=corn,
        response=response,
        ship=ship,
        outcome=outcome,
        shared_plan=params.shared_plan,
        activated=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "{f["activator"].label}", "{f["corn"].label}", and "glee".',
        f"Tell a friendship story where {f['friend_a'].id} and {f['friend_b'].id} prepare a tiny ship, share corn, and make a brave choice together.",
        f'Write a gentle space story with two friends, a console activator, and a happy ending that feels full of glee.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    activator = f["activator"]
    corn = f["corn"]
    theme = f["theme"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two friends who turn an ordinary day into a small space adventure. Their friendship is what keeps the mission cheerful and safe.",
        ),
        QAItem(
            question="Why did they need the activator?",
            answer=f"They needed the {activator.label} to wake the tiny ship console. It helped start the mission without making the adventure feel scary.",
        ),
        QAItem(
            question="Why was the corn important?",
            answer=f"The corn gave them a happy pause in the middle of their planning. Sharing it helped them stay calm, and that calm made their teamwork easier.",
        ),
    ]
    if f["shared_plan"]:
        qa.append(
            QAItem(
                question="How did they solve the problem?",
                answer=f"They made a shared plan: activate the console together, enjoy the corn, and then go on with the trip. Working together turned the moment into glee instead of a problem.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the ship ready and the friends smiling at each other. The last image is the little ship waiting for {theme.goal}, while friendship keeps everything steady.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an activator?",
            answer="An activator is something that helps start a machine or device. In this story, it wakes up the tiny ship console.",
        ),
        QAItem(
            question="What is corn?",
            answer="Corn is a food made of many yellow kernels on a cob or in a bowl. It is crunchy, sweet, and easy to share.",
        ),
        QAItem(
            question="What does glee mean?",
            answer="Glee means bright, happy delight. It is the kind of joy that makes a smile feel too big to hide.",
        ),
        QAItem(
            question="Why is friendship important on an adventure?",
            answer="Friends help each other stay calm, solve problems, and feel brave. On a space adventure, that teamwork matters even more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="orbit", activator="activator", corn="corn", response="together",
                friend_a="Mia", friend_a_gender="girl", friend_b="Noah", friend_b_gender="boy",
                delay=0, shared_plan=True),
    StoryParams(theme="comet", activator="button", corn="popcorn", response="careful",
                friend_a="Ava", friend_a_gender="girl", friend_b="Leo", friend_b_gender="boy",
                delay=1, shared_plan=False),
]


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for aid, a in ACTIVATORS.items():
        lines.append(asp.fact("activator", aid))
        if a.safe:
            lines.append(asp.fact("safe", aid))
    for cid, c in CORN.items():
        lines.append(asp.fact("corn", cid))
        if c.safe:
            lines.append(asp.fact("safe_corn", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(A,C) :- activator(A), corn(C), safe(A), safe_corn(C).
valid(T,A,C) :- theme(T), activator(A), corn(C), reasonable(A,C).
"""
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError("Invalid theme.")
    if params.activator not in ACTIVATORS:
        raise StoryError("Invalid activator.")
    if params.corn not in CORN:
        raise StoryError("Invalid corn.")
    if params.response not in RESPONSES:
        raise StoryError("Invalid response.")
    if not is_reasonable(ACTIVATORS[params.activator], CORN[params.corn]):
        raise StoryError("That story combination is not reasonable.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t, a, c in asp_valid_combos():
            print(t, a, c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
