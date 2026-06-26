#!/usr/bin/env python3
"""
waylay_problem_solving_nursery_rhyme.py
=======================================

A TinyStories-style world where a child sets off on a quest to gather berries
in the forest only to be repeatedly waylaid by playful but obstructive forces.
Each setback is resolved through simple problem-solving tools and rhymes,
teaching persistence and creativity.

Core premise:
- Hero named in a nursery rhyme cadence
- Journey to pick berries in the greenwood
- Four classic woodland "waylayers": raincloud, fallen log, noisy jays, busy bee
- Each returns with a resourceful tool from granny's basket
- Text rendered entirely in light verse (rhyming couplets, sing-song rhythm)

Physical mimics:
  wetness -> from rain; covered_by_gear clears it
  clutter -> from scattered berries; kept_in_container prevents it

Emotional mimics:
  frustration -> rises when waylaid
  joy/patience -> restored when obstacle cleared

Inline ASP twin parallels the Python sanity gate: a trip is complete only
when every waylaying obstacle has a compatible tool supplied by the
child's basket. This prevents grammatically valid but unreasonably empty
stories (e.g. four waylays without any tools).
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

# ---------------------------------------------------------------------------
# Tiny metres to trigger narration of changes.
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities: characters and cherished objects sharing physics.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                  # "character" | "thing"
    type: str = "character"              # girl, boy, mother, father, basket ...
    label: str = ""                      # short reference
    phrase: str = ""                     # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None       # who maintains or supplied this entity
    region: str = ""                     # current location label
    container: Optional[str] = None      # another entity id that "holds" this one
    protective: bool = False             # gear that deflects mess/obstacles
    weatherproof: bool = False           # keeps items inside dry
    weather_sensitive: bool = False
    plural: bool = False
    # Two numeric dimensions, treated uniformly:
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "witch"}
        male = {"boy", "son", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# World and narration helpers.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.depth: int = 0                 # stanzas laid before
        self.facts: dict = {}               # ground facts for Q&A
        # Runtime state for problem-solving episodes:
        self.current_obstacle: Optional[str] = None
        self.basket: Optional[str] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def say(self, line: str) -> None:
        if line:
            self.paragraphs[-1].append(line.strip())

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def title_line(self) -> str:
        return "Little {name} went to pick berries in the glen".format(
            name=self.facts.get("hero_name", "Lucy"))

    def render(self) -> str:
        stanzas = []
        for stanza in self.paragraphs:
            if not stanza:
                continue
            chunk = " ".join(stanza)
            # Pad even-length lines with trailing space to keep rhyme footing
            if chunk.count(" ") % 2 == 1:  # odd word count -> likely unpaired
                chunk += " "
            stanzas.append(chunk.capitalize())
        return "\n\n".join(stanzas)

    def copy(self) -> "World":
        """Throwaway clone of the live world for forward simulation."""
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.depth = self.depth
        clone.facts = dict(self.facts)
        clone.current_obstacle = self.current_obstacle
        clone.basket = self.basket
        clone.paragraphs = [[]]  # predictions are silent
        return clone

# ---------------------------------------------------------------------------
# Core forward-chained rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _solve_waylay(world: World) -> list[str]:
    """Any obstacle that is present and still active counts as a waylay."""
    out: list[str] = []
    for entity in world.things():
        if entity.meters["waylay"] >= THRESHOLD and entity.region == "path_seg":
            waylay = entity
            hero = world.get("Hero")
            if hero.meters["frustration"] < THRESHOLD and "confidence" not in waylay.meters:
                # Only narrate if frustration not already embedded
                out.append(
                    f"Oh dear! A {waylay.label} came in the way to "
                    f"{hero.pronoun('object')} every day."
                )
                hero.memes["frustration"] += 1.0
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="discover_waylay", tag="problem", apply=_solve_waylay),
]

def propagate(world: World) -> None:
    """Run all world rules to fixpoint; used before child actions."""
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)

# ---------------------------------------------------------------------------
# Problem-solving verbs and narrative beats.
# ---------------------------------------------------------------------------
def arrive(world: World, hero: Entity, place: str) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} skipped {place} so spry, "
        f"basket bouncing at {hero.pronoun('possessive')} side."
    )
    propagate(world)

def sets_off(hero: str) -> str:
    names = {"Lucy", "Lila", "Milo", "Oscar", "Tessa"}
    return hero if hero in names else "Milo"

def waylay_intro(obstacle: str) -> list[str]:
    couplets = {
        "rain_cloud": [
            "But oh! A cloud came dark and gray,",
            "It would waylay them on their way."
        ],
        "fallen_log": [
            "A log too big blocked trail ahead,",
            "It would waylay their path instead."
        ],
        "noisy_jays": [
            "Two noisy jays began to squawk,",
            "Their jabber would waylay the walk."
        ],
        "busy_bee": [
            "A buzzing bee came buzzing near,",
            "It would waylay and disappear."
        ]
    }
    return couplets.get(obstacle, ["Then trouble trod upon their track."])

def observe_waylay(world: World, obstacle_id: str) -> None:
    hero = world.get("Hero")
    world.say(" ".join(waylay_intro(obstacle_id)))
    obstacle = world.get(obstacle_id)
    obstacle.meters["waylay"] += 1.5
    propagate(world)

def problem_notes() -> dict:
    return {
        "rain_cloud": ("The rain shall soak the basket bright,",
                       "And berries turn to purple blight."),
        "fallen_log": ("The mud beneath is slick and slick,",
                       "One slip and down they'll take a trick."),
        "noisy_jays": ("Their screeching rings inside your ears,",
                       "Too loud for peaceful berry years."),
        "busy_bee": ("That bee seems set on every quest—",
                     "it circles you but will not rest!")
    }

def propose_solution(world: World, solution_id: str) -> None:
    sol = SOLUTIONS[solution_id]
    hero = world.get("Hero")
    obstacle = world.get(hero.meters.get("waylay_target", ""))
    if obstacle:
        name = obstacle.label.split(" ", 1)[0]
        lines = [
            f'"Dear Granny packed a special thing!"',
            f'cried {hero.id}. "Behold the {sol.label}!"'
        ]
        world.say("\n".join(lines))
        if sol.reduces == "wet":
            lines = [
                f"They slipped the {sol.label} on so tight,",
                f"now rain would miss and keep them bright."
            ]
        elif sol.reduces == "blocked":
            lines = [
                f"They rolled two stones up one, two up two—",
                f"a path popped up for me and you."
            ]
        elif sol.reduces == "noise":
            lines = [
                f"Then " + hero.pronoun() + " hummed a tune so sweet",
                f"the jays all hushed and stayed discreet."
            ]
        elif sol.reduces == "distract":
            lines = [
                f"With gentle breath they blew a breeze,",
                f"and off that bee went with a wheeze."
            ]
        world.say("\n".join(lines))
        obstacle.meters["waylay"] = 0.0
        hero.memes["confidence"] += 1.2
        hero.memes["frustration"] = 0.0
        propagate(world)

def gather_begin(world: World) -> None:
    hero = world.get("Hero")
    hero.memes["patience"] += 1.0
    world.say(
        f"With basket held and song so bright, "
        f"{hero.pronoun()} began to gather light."
    )

def gather_end(world: World, success: bool = True) -> None:
    hero = world.get("Hero")
    if success:
        world.say(
            f"Now filled with berries, red and round, "
            f"{hero.id} skipped home without a sound."
        )
        hero.memes["joy"] += 2.0
        hero.meters["berries"] += 1
    else:
        world.say(
            f"Alas, their basket stayed so bare— "
            f"the waylayers still lurked out there."
        )

# ---------------------------------------------------------------------------
# StoryParams and registry.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero_name: str
    gender: str
    basket_tool: str = "stripy_basket"
    seed: Optional[int] = None

GIRL_NAMES = ["Lila", "Tessa", "Mira", "Nora", "Zara"]
BOY_NAMES = ["Milo", "Oscar", "Finn", "Leo", "Noah"]
TOOLS = ["stripy_basket", "raincoat", "stepping_stones", "lullaby_charm", "gentle_breath"]

def choose_tool(gender: str) -> str:
    if gender == "girl":
        return "stripy_basket"
    elif gender == "boy":
        return "stripy_basket"
    return random.choice(TOOLS)

# ---------------------------------------------------------------------------
# Obstacles, solutions, and valid pairing registry.
# ---------------------------------------------------------------------------
OBSTACLE_PAIRS = {
    "rain_cloud": {
        "solution": "raincoat",
        "reduces": "wet",
        "risk": "basket will get soggy and berries will stain"
    },
    "fallen_log": {
        "solution": "stepping_stones",
        "reduces": "blocked",
        "risk": "muddy knees and berries squashed flat"
    },
    "noisy_jays": {
        "solution": "lullaby_charm",
        "reduces": "noise",
        "risk": "ears ring loud with jaybird din"
    },
    "busy_bee": {
        "solution": "gentle_breath",
        "reduces": "distract",
        "risk": "the bee drifts back and stings your chin"
    }
}

SOLUTIONS = {
    "stripy_basket": Entity(
        id="stripy_basket", kind="thing", type="basket",
        label="stripy basket", phrase="a stripy basket bright and clean",
        region="hand", protective=False, plural=False
    ),
    "raincoat": Entity(
        id="raincoat", kind="thing", type="cloak",
        label="raincoat", phrase="a hooded raincoat striped in red and blue",
        region="torso", protective=True, plural=False
    ),
    "stepping_stones": Entity(
        id="stepping_stones", kind="thing", type="stones",
        label="two neat stones", phrase="two small stepping stones",
        region="path_seg", protective=True, plural=True
    ),
    "lullaby_charm": Entity(
        id="lullaby_charm", kind="thing", type="charm",
        label="tiny silver charm", phrase="a silver lullaby charm on a chain",
        region="pocket", weatherproof=True, plural=False
    ),
    "gentle_breath": Entity(
        id="gentle_breath", kind="action", type="breath",
        label="gentle breath", phrase="a big deep breath, calm and slow",
        region="air", plural=False
    )
}

def valid_pair(obstacle_id: str, solution_id: str) -> bool:
    return OBSTACLE_PAIRS.get(obstacle_id, {}).get("solution") == solution_id

def tool_region(tool_id: str) -> str:
    return SOLUTIONS[tool_id].region

# ---------------------------------------------------------------------------
# The screenplay generator.
# ---------------------------------------------------------------------------
def tell(params: StoryParams, rng: random.Random) -> World:
    world = World()
    world.facts.update(hero_name=params.hero_name)
    world.basket = params.basket_tool

    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=hero_type,
        traits=["little"] + (["playful"] if hero_type == "girl" else ["lively"]),
    ))
    parent = world.add(Entity(
        id="Granny", kind="character", type="grandmother", label="Granny",
        caretaker="Granny"
    ))
    basket = world.add(copy.deepcopy(SOLUTIONS[params.basket_tool]))
    basket.owner = hero.id
    world.entities["Basket"] = basket

    # Act 1: Setup in Granny's glade
    world.say(world.title_line())
    world.say(f"With basket {basket.phrase}.")
    world.para()
    arrive(world, hero, "Granny's glade")
    gather_begin(world)

    # Act 2: Four classic woodland waylayers (in new stanza each time)
    world.para()
    world.say("Then trouble trod upon their track—")
    obstacles_shown = rng.sample(list(OBSTACLE_PAIRS.keys()), 4)

    for idx, obstacle_id in enumerate(obstacles_shown):
        world.para()
        observe_waylay(world, obstacle_id)

        # Pick exactly matching tool
        tool = OBSTACLE_PAIRS[obstacle_id]["solution"]
        if tool not in SOLUTIONS:
            continue
        tool_entity = copy.deepcopy(SOLUTIONS[tool])

        propose_solution(world, tool)
        world.paragraphs[-1].append(tool_entity.phrase)

        # Validate pairing
        if valid_pair(obstacle_id, tool):
            world.current_obstacle = None
            hero.meters["waylay_target"] = ""

    # Act 3: Succeed or partial (but always at least one obstacle cleared)
    world.para()
    if hero.meters.get("berries", 0) > 0:
        gather_end(world, success=True)
    else:
        gather_end(world, success=False)

    # Record facts for Q&A
    world.facts.update(
        obstacles=obstacles_shown,
        solutions=[OBSTACLE_PAIRS[o]["solution"] for o in obstacles_shown],
        hero=hero,
        granny=parent,
        basket=basket,
        tool_used=[OBSTACLE_PAIRS[o]["solution"] for o in obstacles_shown
                   if OBSTACLE_PAIRS[o]["solution"] != "stripy_basket"]
    )
    return world

# ---------------------------------------------------------------------------
# Three Q&A sets tailored to miniature verse and problem/solution pairs.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hero_name = world.facts.get("hero_name", "little child")
    return [
        f'Write a gentle nursery rhyme story for toddlers using the word "waylay", '
        f'where a {hero.type} named {hero.id} sets off to pick berries but '
        f'is repeatedly {hero.pronoun("object")} waylaid by woodland friends '
        f'until {hero.pronoun("subject")} learns to solve each problem.',
        f'Create a short counting rhyme tale (four stanzas) that ends happy '
        f'with {hero.pronoun("object")} berry basket overflowing.',
        f'Compose a child-facing verse where the verb "waylay" turns small '
        f'obstacles into learning moments, and every problem has a neat '
        f'clever fix.'
    ]

def str_question(question: str) -> QAItem:
    return QAItem(question=question, answer=_answer(question))

def _answer(q: str) -> str:
    if "where did" in q.lower():
        return "They went to Granny's glade near a sparkling glen."
    if "who is" in q.lower() and "gran" in q.lower():
        return "Granny is the wise grandmother and caretaker who packed the basket."
    if "what did" in q.lower() and "waylay" in q.lower():
        return "Little woodland creatures and rainclouds tried to waylay, or block, " + \
               "the child's quiet walk to pick berries."
    if "how did" in q.lower() and "trouble" in q.lower():
        return "Each waylayer came with a clever trick from Granny's basket."
    return "That is a good question—why not reread the rhyme together?"

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    answers = []
    for st in range(1, 6):  # up to five stanzas
        answers.append(str_question(
            f"What happened in stanza {st} when {hero.id} tried to pick berries?"
        ))
    if len(f.get("obs", [])) > 0:
        answers.append(QAItem(
            question="Why did Granny pack the special tools in the basket?",
            answer="Granny packed each tool so the child could solve the specific waylayer " +
                   "that Granny knew would come along the path.")
    return answers

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to waylay someone?",
            answer="To waylay means to stop or delay someone on purpose or by chance " +
                   "when they are going somewhere quickly."
        ),
        QAItem(
            question="What is a glade?",
            answer="A glade is a small open area in a forest where sunlight can come through."
        ),
        QAItem(
            question="Why do grandmothers often have baskets?",
            answer="Grandmothers often carry baskets to gather fruits, herbs, or flowers, " +
                   "or to keep tools handy while they are outside."
        )
    ]

# ---------------------------------------------------------------------------
# ASP twin – declarative gate for valid pairing checks.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Waylayers block progress until solved by compatible tool in basket.
obstacle(O) :- waylay(O,_).
% Only solved if the exact tool is present.
solved(O) :- obstacle(O), tool_in_basket(T), fixes(T,O).
valid_story :- solved(rain_cloud),
               solved(fallen_log),
               solved(noisy_jays),
               solved(busy_bee).
:- not valid_story.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    # Facts for obstacles
    lines.append(asp.fact("waylay", "rain_cloud", "wet"))
    lines.append(asp.fact("waylay", "fallen_log", "blocked"))
    lines.append(asp.fact("waylay", "noisy_jays", "noise"))
    lines.append(asp.fact("waylay", "busy_bee", "distract"))
    # Solutions that fix
    lines.append(asp.fact("fixes", "raincoat", "rain_cloud"))
    lines.append(asp.fact("fixes", "stepping_stones", "fallen_log"))
    lines.append(asp.fact("fixes", "lullaby_charm", "noisy_jays"))
    lines.append(asp.fact("fixes", "gentle_breath", "busy_bee"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#defined valid_story."))
    status = 0 if "valid_story" in [s.name for s in model] else 1
    print("ASP gate " + ("PASSED" if status == 0 else "FAILED") +
          " – story can reach goal after solving waylayers.")
    return status

# ---------------------------------------------------------------------------
# Storyworld contract entry points.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny nursery-rhyme world that teaches problem-solving: a child "
                    "sets off to pick berries only to be repeatedly waylaid until "
                    "they learn to bring Granny's clever tools.")
    ap.add_argument("--hero", choices=["Lila", "Tessa", "Milo", "Oscar"], help="hero name")
    ap.add_argument("--gender", choices=["girl", "boy"], help="hero's gender")
    ap.add_argument("-n", type=int, default=1, help="number of rhymes to write")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="print pre-set tiny examples")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="print three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of verse")
    ap.add_argument("--asp", action="store_true", help="list ASP-valid stories")
    ap.add_argument("--verify", action="store_true", help="run ASP gate vs Python gate")
    ap.add_argument("--show-asp", action="store_true", help="dump the ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = (
        args.hero or
        (rng.choice(GIRL_NAMES) if gender == "girl" else rng.choice(BOY_NAMES))
    )
    tool = choose_tool(gender)
    return StoryParams(hero_name=name, gender=gender, basket_tool=tool, seed=args.seed)

def generate(params: StoryParams) -> StorySample:
    hero_seed = params.seed if params.seed is not None else random.randrange(2**31)
    rng = random.Random(hero_seed)
    world = tell(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            if m:
                lines.append(f"  {e.id:12} meters={dict(m)}")
        print("\n".join(lines))
    if qa:
        print()
        print("== Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== Story Q&A ==")
        for qa in sample.story_qa:
            print("Q:", qa.question)
            print("A:", qa.answer)
        print("\n== World Q&A ==")
        for qa in sample.world_qa:
            print("Q:", qa.question)
            print("A:", qa.answer)

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show obstacle/2,fixes/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP rules inline only, but valid stories require fixes for every waylay.")
        return

    rng_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for name in ["Lila", "Milo"]:
            params = StoryParams(hero_name=name, gender="girl" if name in GIRL_NAMES else "boy",
                                 basket_tool="stripy_basket", seed=rng_seed)
            samples.append(generate(params))
    else:
        seen_text = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 50):
            seed = rng_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as se:
                print(se)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen_text:
                i += 1
                continue
            seen_text.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.hero_name}'s berry quest"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
