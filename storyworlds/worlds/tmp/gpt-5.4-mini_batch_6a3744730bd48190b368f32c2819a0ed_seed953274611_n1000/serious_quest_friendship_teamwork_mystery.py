#!/usr/bin/env python3
"""
Standalone storyworld: serious quest friendship teamwork mystery.

A small child-facing mystery domain: a little team searches for a missing clue
during a serious quest. Friendship keeps them calm, teamwork helps them solve
it, and the ending proves what changed in the world.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"found": 0.0, "dusty": 0.0, "moved": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0}

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
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    darkness: str
    detail: str
    clue_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    serious_line: str
    quest_line: str
    teamwork_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_find(world: World) -> list[str]:
    out = []
    for clue in world.entities.values():
        if clue.kind != "clue" or clue.meters["found"] < THRESHOLD:
            continue
        sig = ("found", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["joy"] += 0.5
        out.append(f"The team knew the clue mattered now.")
    return out


def _r_teamwork(world: World) -> list[str]:
    if world.facts.get("helped") and ("teamwork",) not in world.fired:
        world.fired.add(("teamwork",))
        for ch in world.characters():
            ch.memes["trust"] += 0.5
            ch.memes["joy"] += 0.5
        return ["__teamwork__"]
    return []


RULES = [Rule("find", _r_find), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get(clue_id).meters["found"] += 1
    propagate(sim, narrate=False)
    return {"found": sim.get(clue_id).meters["found"] >= THRESHOLD}


def search(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f"On a serious evening, {hero.id} and {friend.id} stood in {world.setting.place}. "
        f"{world.setting.detail} {world.setting.darkness} The missing thing was {clue.phrase}."
    )
    world.say(f'"We have a quest," {hero.id} said. "{clue.label} must be found."')
    hero.memes["curiosity"] += 1
    friend.memes["worry"] += 0.5


def warn(world: World, friend: Entity, hero: Entity, clue: Clue) -> None:
    pred = predict_mystery(world, clue.id)
    if pred["found"]:
        world.say(
            f'{friend.id} pointed to {clue.hidden_in}. "Look carefully," {friend.id} said. '
            f'"A clue can hide where nobody thinks to look."'
        )
    else:
        world.say(f"{friend.id} stayed close, ready to help.")


def work_together(world: World, hero: Entity, friend: Entity, clue: Clue, tool: Tool) -> None:
    world.facts["helped"] = True
    hero.memes["trust"] += 0.5
    friend.memes["trust"] += 0.5
    world.say(
        f"{hero.id} held the {tool.label}, and {friend.id} moved the box aside with both hands. "
        f"Together they used {tool.use}."
    )
    clue_ent = world.get(clue.id)
    clue_ent.meters["found"] += 1
    clue_ent.meters["dusty"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {clue.reveal}.")


def ending(world: World, hero: Entity, friend: Entity, mystery: Mystery, clue: Clue) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{mystery.ending_line} {hero.id} and {friend.id} smiled at the clue, "
        f"because teamwork had turned the serious search into a solved mystery."
    )


def tell(setting: Setting, clue: Clue, tool: Tool, mystery: Mystery,
         hero_name: str = "Maya", hero_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id=clue.id, kind="clue", type="thing", label=clue.label))

    search(world, hero, friend, clue)
    world.para()
    warn(world, friend, hero, clue)
    world.para()
    world.say(mystery.serious_line)
    world.say(mystery.quest_line)
    work_together(world, hero, friend, clue, tool)
    world.para()
    world.say(mystery.teamwork_line)
    ending(world, hero, friend, mystery, clue)

    world.facts.update(hero=hero, friend=friend, clue=clue, tool=tool, mystery=mystery, setting=setting)
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old library",
        darkness="The back shelf was dim and quiet.",
        detail="Dusty books leaned together like sleepy towers.",
        clue_spot="behind the tallest atlas",
        tags={"library", "mystery"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        darkness="The corners were shadowy and still.",
        detail="Boxes sat in a row under the rafters.",
        clue_spot="inside the taped box",
        tags={"attic", "mystery"},
    ),
    "garden_shed": Setting(
        id="garden_shed",
        place="the garden shed",
        darkness="The small window let in almost no light.",
        detail="Old pots and rakes stood in a quiet pile.",
        clue_spot="under the folded tarp",
        tags={"shed", "mystery"},
    ),
}

CLUES = {
    "map_piece": Clue(
        id="map_piece",
        label="a map piece",
        phrase="a torn map piece",
        hidden_in="behind the tallest atlas",
        reveal="a torn map piece slid free from behind the atlas",
        tags={"map", "quest"},
    ),
    "key": Clue(
        id="key",
        label="a tiny key",
        phrase="a tiny brass key",
        hidden_in="inside the taped box",
        reveal="a tiny brass key sparkled in the dust",
        tags={"key", "quest"},
    ),
    "note": Clue(
        id="note",
        label="a folded note",
        phrase="a folded note with a blue corner",
        hidden_in="under the folded tarp",
        reveal="a folded note with a blue corner was tucked under the tarp",
        tags={"note", "quest"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        use="a warm lantern beam",
        reveals="shows hidden edges",
        tags={"light", "mystery"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        use="a magnifying glass",
        reveals="makes tiny marks easy to see",
        tags={"glass", "mystery"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        use="gloves for lifting dusty things",
        reveals="keeps hands clean while searching",
        tags={"helper", "mystery"},
    ),
}

MYSTERIES = {
    "silent": Mystery(
        id="silent",
        serious_line="The room felt serious, like it was waiting to tell the truth.",
        quest_line="They kept looking because a quest is not done until the clue is found.",
        teamwork_line="Working together made the search feel braver and kinder.",
        ending_line="At last the mystery was no longer hiding.",
        tags={"mystery", "quest", "friendship", "teamwork"},
    ),
    "echo": Mystery(
        id="echo",
        serious_line="Everything was quiet enough to hear a soft echo.",
        quest_line="The friends followed the clues one careful step at a time.",
        teamwork_line="Each helper had a job, and that made the hard part easier.",
        ending_line="The answer fit perfectly, like a key in a lock.",
        tags={"mystery", "quest", "friendship", "teamwork"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo"]
TRAITS = ["serious", "kind", "careful", "brave"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    mystery: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="library", clue="map_piece", tool="lantern", mystery="silent",
                hero_name="Maya", hero_gender="girl", friend_name="Noah", friend_gender="boy",
                trait="serious"),
    StoryParams(setting="attic", clue="key", tool="magnifier", mystery="echo",
                hero_name="Lily", hero_gender="girl", friend_name="Eli", friend_gender="boy",
                trait="careful"),
    StoryParams(setting="garden_shed", clue="note", tool="gloves", mystery="silent",
                hero_name="Theo", hero_gender="boy", friend_name="Nora", friend_gender="girl",
                trait="brave"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                for m in MYSTERIES:
                    combos.append((s, c, t, m))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the mystery pieces do not fit this request.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Serious quest friendship teamwork mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)
              and (args.mystery is None or c[3] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, tool, mystery = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, tool=tool, mystery=mystery,
                       hero_name=hero_name, hero_gender=hero_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a serious mystery story about a friendship quest in {f["setting"].place}.',
        f"Tell a child-friendly story where {f['hero'].id} and {f['friend'].id} solve a clue together.",
        f'Write a story that includes the word "serious" and ends with teamwork paying off.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    clue = f["clue"]
    tool = f["tool"]
    return [
        QAItem(
            question="Why was the story serious?",
            answer=f"It was serious because the clue was missing and the friends needed to solve the mystery. They stayed calm so they could finish the quest together."
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do to solve the problem?",
            answer=f"They used {tool.label} and worked side by side until {clue.reveal}. Teamwork helped them search carefully instead of getting distracted."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the clue found and the friends smiling together. The mystery was solved, so the quest could move forward."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something hidden or not yet understood. People solve it by looking for clues."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and do jobs together. It makes hard things easier to finish."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. It often has a goal and a problem to solve."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} kind={e.kind}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,T,M) :- setting(S), clue(C), tool(T), mystery(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, tool=None, mystery=None,
            hero_name=None, hero_gender=None, friend_name=None, friend_gender=None,
            trait=None
        ), random.Random(777)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: generate smoke test failed: {e}")
    if ok:
        print("OK: ASP parity and generate smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.tool not in TOOLS or params.mystery not in MYSTERIES:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(SETTINGS[params.setting], CLUES[params.clue], TOOLS[params.tool], MYSTERIES[params.mystery],
                 hero_name=params.hero_name, hero_gender=params.hero_gender,
                 friend_name=params.friend_name, friend_gender=params.friend_gender)
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
