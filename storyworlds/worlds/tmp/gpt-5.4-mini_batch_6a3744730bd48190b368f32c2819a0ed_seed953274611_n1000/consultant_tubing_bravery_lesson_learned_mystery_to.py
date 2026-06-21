#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consultant_tubing_bravery_lesson_learned_mystery_to.py
======================================================================================

A small superhero-style storyworld about a brave hero, a careful consultant,
and a mystery hidden inside a tangle of tubing. The child-facing story always
follows a state-driven arc: premise, suspicion, a brave inspection, the reveal,
and a lesson learned ending image.

Seed words: consultant, tubing
Features: Bravery, Lesson Learned, Mystery to Solve
Style: Superhero Story
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    mysterious: bool = False
    helpful: bool = False
    tangled: bool = False
    solved: bool = False

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class City:
    id: str
    label: str
    place: str
    scene: str
    trouble: str
    fixable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    suspect: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    title: str
    sentence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    city: str
    mystery: str
    tool: str
    consultant_name: str
    consultant_gender: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_gender: str
    lesson: str
    seed: Optional[int] = None


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
    apply: Callable[[World], list[str]]


def _r_tangle(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.meters["curiosity"] < THRESHOLD:
        return out
    if ("tangle",) in world.fired:
        return out
    world.fired.add(("tangle",))
    hero.memes["worry"] += 1
    out.append("__mystery__")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["bravery"] < THRESHOLD or hero.meters["investigation"] < THRESHOLD:
        return out
    if ("solve",) in world.fired:
        return out
    world.fired.add(("solve",))
    world.get("mystery").solved = True
    out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("tangle", _r_tangle), Rule("solve", _r_solve)]


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


def mystery_at_risk(city: City, mystery: Mystery) -> bool:
    return city.fixable and mystery.id in city.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, city in CITIES.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if mystery_at_risk(city, mystery):
                    combos.append((cid, mid, tid))
    return combos


def choose_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["curiosity"] += 1
    sim.get("hero").meters["investigation"] += 1
    propagate(sim, narrate=False)
    return {"solved": sim.get("mystery").solved, "worry": sim.get("hero").memes["worry"]}


def setup(world: World, city: City, hero: Entity, consultant: Entity, mentor: Entity, mystery: Mystery) -> None:
    hero.memes["bravery"] = 1.0
    hero.meters["curiosity"] = 1.0
    consultant.memes["care"] = 1.0
    mentor.memes["patience"] = 1.0
    world.say(
        f"On a bright afternoon in {city.place}, {hero.id} wore a tiny cape and watched the rooftop
        robots blink under the sun."
    )
    world.say(
        f"{consultant.id}, a consultant in a silver suit, arrived with a notebook and a calm smile."
    )
    world.say(
        f'"Something strange is happening," {mentor.id} said. "The {mystery.clue} keeps showing up."'
    )


def suspect(world: World, hero: Entity, consultant: Entity, tool: Tool, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} pointed at the tangled {tool.label}. " 
        f'"Could the tubing be hiding the clue?" {hero.pronoun()} asked.'
    )
    world.say(
        f"{consultant.id} nodded. " 
        f'"That is a mystery to solve. Brave heroes look closely instead of guessing."'
    )


def brave_inspect(world: World, hero: Entity, consultant: Entity, tool: Tool) -> None:
    hero.meters["investigation"] += 1
    hero.memes["bravery"] += 1
    tool_entity = world.get("tool")
    tool_entity.tangled = True
    world.say(
        f"{hero.id} took one deep breath, stepped beside the tubing, and followed it from one end to the other."
    )
    world.say(
        f"{consultant.id} held up a flashlight, and the shiny beam traced every bend like a rescue line."
    )


def reveal(world: World, city: City, mystery: Mystery, tool: Tool) -> None:
    world.get("mystery").solved = True
    world.say(
        f"At last, the answer popped out: {mystery.reveal}. {mystery.truth}"
    )
    world.say(
        f"The tubing was not scary at all; it was only part of the machine, and the missing clip made the noise."
    )
    world.say(
        f"The whole rooftop felt different now -- less puzzling, more peaceful."
    )


def lesson(world: World, mentor: Entity, hero: Entity, lesson_cfg: Lesson) -> None:
    hero.memes["confidence"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"Then {mentor.id} knelt beside {hero.id} and said, "
        f'"{lesson_cfg.sentence}"'
    )
    world.say(
        f'{hero.id} smiled and nodded. "I was brave, and I did not run away," {hero.pronoun()} said.'
    )


def ending(world: World, city: City, hero: Entity, consultant: Entity) -> None:
    world.say(
        f"By sunset, {hero.id}, {consultant.id}, and {world.get('mentor').id} stood together above {city.place}, "
        f"watching the repaired tubing hum like a tiny, safe superhero signal."
    )
    world.say(
        f"{hero.id}'s cape fluttered in the warm wind, and the solved mystery felt lighter than air."
    )


def tell(city: City, mystery: Mystery, tool: Tool, lesson_cfg: Lesson,
         consultant_name: str = "Nova", consultant_gender: str = "girl",
         hero_name: str = "Pax", hero_gender: str = "boy",
         mentor_name: str = "Chief Ray", mentor_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    consultant = world.add(Entity(id="consultant", kind="character", type=consultant_gender, label=consultant_name))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_gender, label=mentor_name))
    mystery_ent = world.add(Entity(id="mystery", kind="thing", type="mystery", label=mystery.id, mysterious=True))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, tangled=True))
    world.facts.update(city=city, mystery=mystery, tool=tool, lesson=lesson_cfg)

    setup(world, city, hero, consultant, mentor, mystery)
    world.para()
    suspect(world, hero, consultant, tool, mystery)
    brave_inspect(world, hero, consultant, tool)
    propagate(world, narrate=True)
    world.para()
    reveal(world, city, mystery, tool)
    lesson(world, mentor, hero, lesson_cfg)
    ending(world, city, hero, consultant)
    return world


CITIES = {
    "skyport": City(
        id="skyport",
        label="Skyport",
        place="Skyport Tower",
        scene="a glittering rooftop lab",
        trouble="a strange hum inside the machine room",
        fixable=True,
        tags={"mystery", "tubing"},
    ),
    "harbor": City(
        id="harbor",
        label="Harbor City",
        place="Harbor City Dockworks",
        scene="a wind-tugged dock lab",
        trouble="a whisper from the pipe maze",
        fixable=True,
        tags={"mystery", "tubing"},
    ),
}

MYSTERIES = {
    "whistle": Mystery(
        id="whistle",
        clue="whistling tubing",
        reveal="the tubing was whistling because a tiny valve was loose",
        suspect="the valve",
        truth="A loose valve can make a tiny whistle, and tiny whistles can feel like big trouble.",
        tags={"mystery", "tubing"},
    ),
    "blink": Mystery(
        id="blink",
        clue="blinking tubing",
        reveal="the tubing was blinking because a control light was trapped behind it",
        suspect="the light",
        truth="A trapped light can blink through gaps and make a place feel mysterious.",
        tags={"mystery", "tubing"},
    ),
}

TOOLS = {
    "flashlight": Tool(id="flashlight", label="flashlight", phrase="a bright flashlight", safe=True, tags={"light"}),
    "camera": Tool(id="camera", label="inspection camera", phrase="a tiny inspection camera", safe=True, tags={"tool"}),
}

LESSONS = {
    "brave_look": Lesson(
        id="brave_look",
        title="Brave Look",
        sentence="Bravery does not mean guessing. It means looking carefully until the truth shows itself.",
        tags={"bravery", "lesson"},
    ),
    "ask_help": Lesson(
        id="ask_help",
        title="Ask for Help",
        sentence="When a mystery feels too big, a brave hero asks for help and keeps going.",
        tags={"lesson"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Zia", "Tess", "Luna", "Ivy"]
BOY_NAMES = ["Pax", "Reed", "Jules", "Milo", "Kai", "Tate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "{f["consultant"].id}" and "tubing".',
        f"Tell a brave mystery story where {f['hero'].id} and {f['consultant'].id} inspect tubing and solve what is wrong.",
        f"Write a story with a consultant, tubing, a mystery to solve, and a lesson learned ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    city, mystery, tool, lesson_cfg = f["city"], f["mystery"], f["tool"], f["lesson"]
    hero = world.get("hero")
    consultant = world.get("consultant")
    mentor = world.get("mentor")
    qa = [
        QAItem(
            question="Who helped solve the mystery?",
            answer=(
                f"{hero.label_word.capitalize()} solved it with {consultant.id} and {mentor.id}. "
                f"They worked together so the strange tubing could be checked safely."
            ),
        ),
        QAItem(
            question="What was the mystery about?",
            answer=(
                f"It was about the tubing making a strange clue at {city.place}. "
                f"The answer was simple, but they had to look closely to find it."
            ),
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=(
                f"{lesson_cfg.sentence} {hero.label_word.capitalize()} learned that brave choices mean careful choices too."
            ),
        ),
    ]
    if world.get("mystery").solved:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"The mystery was solved, the tubing was safe, and the heroes stood together feeling proud. "
                    f"It ended with a calm sky and a neat, fixed machine."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does a consultant do?",
            answer="A consultant helps people think through a problem and find a good plan. They often notice details that others miss.",
        ),
        QAItem(
            question="What is tubing?",
            answer="Tubing is a long hollow tube that can carry air, water, or other things. It often bends around machines or buildings.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous. A brave person keeps going and uses good judgment.",
        ),
    ]
    if world.get("mystery").solved:
        out.append(
            QAItem(
                question="Why is asking for help smart in a mystery?",
                answer="Asking for help can make a mystery easier to solve because more eyes notice more clues. It also keeps the search calm and safe.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.mysterious:
            bits.append("mysterious")
        if e.tangled:
            bits.append("tangled")
        if e.solved:
            bits.append("solved")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(city="skyport", mystery="whistle", tool="flashlight", consultant_name="Nova", consultant_gender="girl", hero_name="Pax", hero_gender="boy", mentor_name="Chief Ray", mentor_gender="boy", lesson="brave_look"),
    StoryParams(city="harbor", mystery="blink", tool="camera", consultant_name="Mira", consultant_gender="girl", hero_name="Kai", hero_gender="boy", mentor_name="Captain Sol", mentor_gender="boy", lesson="ask_help"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    city = args.city or rng.choice(list(CITIES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    tool = args.tool or rng.choice(list(TOOLS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    consultant_gender = args.consultant_gender or rng.choice(["girl", "boy"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["girl", "boy"])
    consultant_name = args.consultant_name or choose_name(rng, consultant_gender)
    hero_name = args.hero_name or choose_name(rng, hero_gender, avoid=consultant_name)
    mentor_name = args.mentor_name or choose_name(rng, mentor_gender, avoid=hero_name)
    if not CITIES[city].fixable or not mystery_at_risk(CITIES[city], MYSTERIES[mystery]):
        raise StoryError("(No story: that city does not support a real mystery to solve.)")
    return StoryParams(
        city=city, mystery=mystery, tool=tool,
        consultant_name=consultant_name, consultant_gender=consultant_gender,
        hero_name=hero_name, hero_gender=hero_gender,
        mentor_name=mentor_name, mentor_gender=mentor_gender,
        lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    for name, table, key in [("city", CITIES, params.city), ("mystery", MYSTERIES, params.mystery), ("tool", TOOLS, params.tool), ("lesson", LESSONS, params.lesson)]:
        if key not in table:
            raise StoryError(f"(No story: unknown {name} '{key}'.)")
    world = tell(
        CITIES[params.city], MYSTERIES[params.mystery], TOOLS[params.tool], LESSONS[params.lesson],
        params.consultant_name, params.consultant_gender,
        params.hero_name, params.hero_gender,
        params.mentor_name, params.mentor_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


ASP_RULES = r"""
mystery_possible(C, M) :- city(C), mystery(M), fixable(C), tags_city(C, mystery), tags_mystery(M, mystery).
solve_bravely :- bravery(hero), investigate(hero), consultant(consultant), mystery_possible(C, M).
ending(solved) :- solve_bravely.
ending(lesson) :- ending(solved), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city", cid))
        if city.fixable:
            lines.append(asp.fact("fixable", cid))
        for tag in city.tags:
            lines.append(asp.fact("tags_city", cid, tag))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in mystery.tags:
            lines.append(asp.fact("tags_mystery", mid, tag))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    lines.append(asp.fact("bravery", "hero"))
    lines.append(asp.fact("investigate", "hero"))
    lines.append(asp.fact("consultant", "consultant"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_possible/2."))
    return sorted(set(asp.atoms(model, "mystery_possible")))


def asp_verify() -> int:
    try:
        _ = generate(CURATED[0])
    except Exception as exc:
        print(f"FAILED: generate smoke test crashed: {exc}")
        return 1
    cset = set(asp_valid_combos())
    pset = set((c, m) for c, m, _ in valid_combos())
    if cset:
        print(f"OK: ASP gate produced {len(cset)} mystery combos.")
    else:
        print("FAILED: ASP gate produced no combos.")
        return 1
    if pset:
        print(f"OK: Python gate produced {len(pset)} mystery combos.")
    else:
        print("FAILED: Python gate produced no combos.")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero mystery storyworld with consultant and tubing.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--consultant-name")
    ap.add_argument("--consultant-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_possible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("mystery combos:")
        for c, m in asp_valid_combos():
            print(f"  {c} {m}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
