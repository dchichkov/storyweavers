#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gulp_ambidextrous_laser_children_s_museum_teamwork.py
======================================================================================

A small standalone storyworld for a children's museum adventure with teamwork and
a quest. Two children explore a playful museum trail, face a little problem with a
museum gadget, cooperate to solve it, and finish with a bright change in the room
and in themselves.

Seed words: gulp, ambidextrous, laser
Setting: children's museum
Features: Teamwork, Quest
Style: Adventure
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
    supports: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)
    playful: bool = False

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
class Setting:
    id: str
    place: str
    scene: str
    quest: str
    challenge: str
    call: str
    theme: str = "adventure"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Puzzle:
    id: str
    label: str
    phrase: str
    trouble: str
    spread: int
    risky: bool = True
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


@dataclass
class StoryParams:
    setting: str
    puzzle: str
    response: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None
    delay: int = 0


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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["buzzing"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for child in world.children():
            child.memes["worry"] += 1
        out.append("__buzz__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


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


SETTINGS = {
    "museum": Setting(
        id="museum",
        place="the children's museum",
        scene="a grand quest through the children's museum",
        quest="the map room",
        challenge="the dark exhibit hall",
        call="a glowing tunnel map",
    ),
    "science": Setting(
        id="science",
        place="the children's museum",
        scene="a space quest through the children's museum",
        quest="the star wall",
        challenge="the shadow tunnel",
        call="a blinking floor map",
    ),
    "art": Setting(
        id="art",
        place="the children's museum",
        scene="a paint-splashed quest through the children's museum",
        quest="the color bridge",
        challenge="the mirror cave",
        call="a bright clue card",
    ),
}

TOOLS = {
    "laser": Tool(
        id="laser",
        label="laser pointer",
        phrase="a little laser pointer",
        use="point at the hidden clues",
        safe=True,
        tags={"laser", "tool", "light"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        use="shine on the path",
        safe=True,
        tags={"light", "tool"},
    ),
}

PUZZLES = {
    "laser": Puzzle(
        id="laser",
        label="laser gate",
        phrase="a red laser gate",
        trouble="the beam blocked the clue box",
        spread=2,
        risky=True,
        tags={"laser", "beam"},
    ),
    "mirror": Puzzle(
        id="mirror",
        label="mirror maze",
        phrase="a shiny mirror maze",
        trouble="the reflections made the map hard to read",
        spread=1,
        risky=True,
        tags={"mirror"},
    ),
}

RESPONSES = {
    "together": Response(
        id="together",
        sense=3,
        power=3,
        text="worked together: one child held the clue card while the other guided the laser to the right spot",
        fail="worked together, but the clue box stayed stubborn and the beam kept sliding away",
        qa_text="worked together by holding the clue card steady and guiding the laser to the right spot",
        tags={"teamwork", "laser"},
    ),
    "careful": Response(
        id="careful",
        sense=2,
        power=2,
        text="kept calm, stepped back, and used the flashlight to follow the map without touching the beam",
        fail="kept calm, but the puzzle needed more than a careful look",
        qa_text="kept calm and used the flashlight to follow the map without touching the beam",
        tags={"light"},
    ),
    "swap": Response(
        id="swap",
        sense=3,
        power=3,
        text="swapped jobs with a grin so each child could use the hand that fit best and the clue clicked into place",
        fail="swapped jobs, but the gate was still too tricky",
        qa_text="swapped jobs so each child could use the hand that fit best",
        tags={"teamwork"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Ava", "Zoe", "Ella", "Mia", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Noah", "Max", "Theo", "Eli", "Jack", "Ben"]
TRAITS = ["brave", "curious", "careful", "clever", "quick", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PUZZLES:
            if sid == "museum" and pid == "laser":
                combos.append((sid, pid))
            if sid == "science" and pid in {"laser", "mirror"}:
                combos.append((sid, pid))
            if sid == "art" and pid == "mirror":
                combos.append((sid, pid))
    return combos


def hazard_at_risk(puzzle: Puzzle, tool: Tool) -> bool:
    return puzzle.id == "laser" and tool.id == "laser"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_contained(response: Response, puzzle: Puzzle, delay: int) -> bool:
    return response.power >= puzzle.spread + delay


def tell(setting: Setting, puzzle: Puzzle, tool: Tool, response: Response,
         child1: str, child1_gender: str,
         child2: str, child2_gender: str,
         adult: str, trait: str, delay: int = 0) -> World:
    world = World()
    leader = world.add(Entity(id=child1, kind="character", type=child1_gender, role="leader",
                              traits=[trait], attrs={"setting": setting.id}))
    helper = world.add(Entity(id=child2, kind="character", type=child2_gender, role="helper",
                              traits=["ambidextrous", "helpful"], attrs={"setting": setting.id}))
    grownup = world.add(Entity(id=adult, kind="character", type="mother", label="the guide", role="adult"))
    gate = world.add(Entity(id="gate", type="thing", label=puzzle.label))
    clue = world.add(Entity(id="clue", type="thing", label="clue box", requires={"laser"}))
    world.facts["setting"] = setting
    world.facts["puzzle"] = puzzle
    world.facts["tool"] = tool
    world.facts["response"] = response
    world.facts["gate"] = gate
    world.facts["leader"] = leader
    world.facts["helper"] = helper
    world.facts["adult"] = grownup
    world.facts["delay"] = delay

    leader.memes["quest"] = 1
    helper.memes["teamwork"] = 1
    leader.memes["joy"] = 1
    helper.memes["joy"] = 1

    world.say(
        f"At {setting.place}, {leader.id} and {helper.id} started a grand quest. "
        f"{setting.scene} shimmered with clues, and {setting.call} pointed the way."
    )
    world.say(
        f'They hurried toward {setting.quest}, because the whole hall felt like a map waiting to be solved.'
    )
    world.para()
    leader.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Then they reached {puzzle.phrase}. {puzzle.trouble}, and {leader.id} gave a small gulp."
    )
    world.say(
        f'"We can solve it," said {helper.id}. "{helper.id} was ambidextrous, so {helper.pronoun("subject")} could guide the clue with either hand."'
    )
    world.say(
        f"{leader.id} lifted {tool.phrase} and tried to {tool.use}, while {helper.id} held the map steady."
    )
    world.para()
    if hazard_at_risk(puzzle, tool):
        gate.meters["buzzing"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The {puzzle.label} glowed with red lines, and the clue box stayed just out of reach."
        )
        if response.id == "together":
            world.say(
                f"{adult} hurried over and smiled. {adult} {response.text}."
            )
            world.say(
                f"The beam blinked off the glass, the clue box clicked open, and the children found the star token."
            )
            world.say(
                f"{leader.id} and {helper.id} high-fived, their quest solved by teamwork."
            )
        elif is_contained(response, puzzle, delay):
            world.say(
                f"{adult} came to help and {adult} {response.text}."
            )
            world.say(
                f"With a careful swap of hands and a steady map, the puzzle opened at last."
            )
            world.say(
                f"The children grinned at the bright token in their hands."
            )
        else:
            world.say(
                f"{adult} came quickly, but {adult} {response.fail}."
            )
            world.say(
                f"The red lines kept dancing, and the quest had to stop for the day."
            )
            world.say(
                f"Still, the children stayed together and promised to return and try again."
            )
    else:
        world.say(
            f"The clue box opened without trouble, and the quest ended in a flash of easy luck."
        )

    world.facts["outcome"] = "done"
    world.facts["score"] = leader.memes["joy"] + helper.memes["joy"]
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old set in the children\'s museum, and include the word "{f["tool"].id}".',
        f"Tell a teamwork quest where two children solve a museum puzzle with an ambidextrous helper and a laser pointer.",
        f'Write a short museum adventure that includes the words "gulp" and "laser" and ends with the friends solving the clue together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader, helper, adult = f["leader"], f["helper"], f["adult"]
    puzzle, tool, setting = f["puzzle"], f["tool"], f["setting"]
    return [
        ("Where does the story happen?",
         f"It happens at the children's museum. The whole adventure stays inside the museum halls and clue rooms."),
        ("Why did {0} give a gulp?".format(leader.id),
         f"{leader.id} gave a gulp because {puzzle.phrase} looked tricky and the red beam blocked the clue box. The puzzle felt big at first, but the children did not give up."),
        ("How did the children solve the quest?",
         f"They solved it by working together. One child held the map steady, the ambidextrous helper guided the laser, and that teamwork opened the clue box."),
        ("What did the guide do?",
         f"{adult.id} came over to help when the puzzle needed a grown-up touch. {adult.id} smiled, explained the next step, and helped the children finish the quest."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["puzzle"].tags) | {"teamwork"}
    out: list[tuple[str, str]] = []
    if "laser" in tags:
        out.append(("What is a laser pointer?",
                    "A laser pointer makes a tiny bright dot of light. People use it to point at things, not to play roughly with other children."))
    if "teamwork" in tags:
        out.append(("What is teamwork?",
                    "Teamwork means people help each other and share the work. When teammates each do a part, a hard job can become much easier."))
    out.append(("What does ambidextrous mean?",
                "Ambidextrous means someone can use both hands well. That can be handy when a job needs one hand to hold and the other to point."))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="museum", puzzle="laser", response="together", child1="Mina", child1_gender="girl",
                child2="Theo", child2_gender="boy", adult="Guide", trait="curious", delay=0),
    StoryParams(setting="science", puzzle="mirror", response="swap", child1="Noah", child1_gender="boy",
                child2="Ava", child2_gender="girl", adult="Guide", trait="brave", delay=0),
    StoryParams(setting="museum", puzzle="laser", response="careful", child1="Lia", child1_gender="girl",
                child2="Ben", child2_gender="boy", adult="Guide", trait="patient", delay=1),
]


def explain_rejection(setting: Setting, puzzle: Puzzle) -> str:
    return "(No story: this museum quest needs the laser puzzle to fit the seed words and the teamwork turn.)"


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.puzzle is None or c[1] == args.puzzle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, puzzle = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    if response not in RESPONSES:
        raise StoryError("Unknown response.")
    c1 = args.child1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    c1g = args.child1_gender or rng.choice(["girl", "boy"])
    c2 = args.child2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != c1])
    c2g = args.child2_gender or rng.choice(["girl", "boy"])
    adult = args.adult or "Guide"
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, puzzle=puzzle, response=response,
                       child1=c1, child1_gender=c1g, child2=c2, child2_gender=c2g,
                       adult=adult, trait=trait, delay=args.delay if args.delay is not None else 0)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.puzzle not in PUZZLES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], PUZZLES[params.puzzle], TOOLS["laser"], RESPONSES[params.response],
                 params.child1, params.child1_gender, params.child2, params.child2_gender,
                 params.adult, params.trait, params.delay)
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


ASP_RULES = r"""
valid(S,P) :- setting(S), puzzle(P), compatible(S,P).
compatible(museum,laser).
compatible(science,laser).
compatible(science,mirror).
compatible(art,mirror).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PUZZLES:
        lines.append(asp.fact("puzzle", p))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Children's museum adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.setting and args.puzzle and (args.setting, args.puzzle) not in valid_combos():
        raise StoryError(explain_rejection(SETTINGS[args.setting], PUZZLES[args.puzzle]))
    return valid_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p in asp_valid_combos():
            print(f"  {s} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
