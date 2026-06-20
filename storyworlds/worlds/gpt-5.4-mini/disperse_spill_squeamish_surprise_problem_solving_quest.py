#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disperse_spill_squeamish_surprise_problem_solving_quest.py
=========================================================================================

A standalone storyworld for a small mystery-flavored quest about a surprise,
a spill, and a squeamish clue-hunter who learns to solve the problem by
dispersing a crowd and following careful clues.

The world is built as a small causal simulation with typed entities that carry
physical meters and emotional memes. The prose is generated from simulated
state rather than from a fixed paragraph template, and the QA sets are derived
from the world model.

Theme words:
- disperse
- spill
- squeamish

Narrative instruments:
- Surprise
- Problem Solving
- Quest

Style:
- Mystery
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hides: str
    clue_source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MysteryQuest:
    id: str
    goal: str
    question: str
    surprise: str
    clue: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spill:
    id: str
    label: str
    liquid: str
    spreads: str
    makes: str
    disperses: str
    messy: bool = True
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hall = world.entities.get("hall")
        if hall:
            hall.meters["mess"] += 1
        for char in world.characters():
            char.memes["concern"] += 1
        out.append("__spill__")
    return out


def _r_disperse(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.entities.get("crowd")
    if crowd and crowd.meters["crowded"] >= THRESHOLD and crowd.meters["dispersed"] < THRESHOLD:
        sig = ("disperse", crowd.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        crowd.meters["crowded"] = 0.0
        crowd.meters["dispersed"] = 1.0
        out.append("__disperse__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("disperse", "social", _r_disperse),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def need_careful_reason(spill: Spill, quest: MysteryQuest) -> bool:
    return spill.messy and "clue" in quest.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def solve_power(response: Response, spill: Spill, delay: int) -> bool:
    return response.power >= (2 + delay if spill.messy else 0)


def build_disperse(world: World, quest: MysteryQuest, crowd: Entity) -> None:
    world.say(
        f"At dusk, {quest.goal} began with a surprise in the old hall. "
        f"{quest.surprise}."
    )
    crowd.meters["crowded"] += 1
    world.get("clue").meters["hidden"] += 1
    world.say(
        f"Everyone stared at the strange scene, and the room felt full of whispers. "
        f"The mystery asked the children to {quest.question}."
    )


def notice_spill(world: World, hero: Entity, spill: Spill, setting: Setting) -> None:
    hero.memes["squeamish"] += 1
    world.say(
        f"{hero.id} was a little squeamish about the sticky {spill.label}. "
        f"It had spilled across the stone floor and glittered near {setting.hides}."
    )
    world.say(
        f'But {hero.id} did not run away. {hero.pronoun().capitalize()} took a slow breath '
        f'and looked for clues instead.'
    )


def warn_and_guess(world: World, sidekick: Entity, hero: Entity, spill: Spill, quest: MysteryQuest) -> None:
    world.say(
        f'{sidekick.id} pointed at the shine. "If we let the crowd stay packed in here, '
        f'the clue will disappear. We should disperse them and find the source of the spill."'
    )
    sidekick.memes["helpful"] += 1
    hero.memes["curious"] += 1


def do_spill(world: World, spill: Spill) -> None:
    world.get("clue").meters["visible"] = 1.0
    world.get("cup").meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The cup tipped with a small clink, and {spill.label} spilled over the floor. "
        f"For a moment, the puddle hid the next clue."
    )


def solve_problem(world: World, hero: Entity, helper: Entity, response: Response, spill: Spill, delay: int) -> bool:
    if not solve_power(response, spill, delay):
        world.say(
            f"{helper.id} tried to help, but {response.fail.replace('{spill}', spill.label)}"
        )
        return False
    world.say(
        f"Then {helper.id} came running and {response.text.replace('{spill}', spill.label)}."
    )
    return True


def conclude(world: World, hero: Entity, quest: MysteryQuest, setting: Setting, response: Response, success: bool) -> None:
    if success:
        world.say(
            f"At last the hidden clue was clear: {quest.clue}. The children solved the mystery "
            f"and followed the trail to {quest.ending_image}."
        )
        world.say(
            f"{hero.id} felt proud for staying calm, even while squeamish, and the hall grew quiet again."
        )
    else:
        world.say(
            "The puddle stayed too big, so the trail went cold. The children had to call a grown-up "
            "and begin again with fresh towels and a better plan."
        )


SETTING_REGISTRY = {
    "old_hall": Setting(
        "old_hall",
        "the old hall",
        "dusty and echoing",
        "a tall curtain",
        "the brass key",
        tags={"mystery", "hall"},
    ),
    "library": Setting(
        "library",
        "the library",
        "quiet and close",
        "the front desk",
        "the note",
        tags={"mystery", "library"},
    ),
    "garden_shed": Setting(
        "garden_shed",
        "the garden shed",
        "dim and creaky",
        "a stack of boxes",
        "the map",
        tags={"mystery", "shed"},
    ),
}

QUEST_REGISTRY = {
    "key_quest": MysteryQuest(
        "key_quest",
        "a mystery quest",
        "find who left the clue behind",
        "A brass key lay on the floor like a surprise",
        "a wet trail led under the curtain",
        "the key resting beside a lantern",
        tags={"quest", "mystery", "surprise"},
    ),
    "note_quest": MysteryQuest(
        "note_quest",
        "a mystery quest",
        "discover what the note means",
        "A folded note slipped from an envelope as a surprise",
        "the ink smudged where the spill had spread",
        "the note pinned safely to a board",
        tags={"quest", "mystery", "surprise"},
    ),
    "map_quest": MysteryQuest(
        "map_quest",
        "a mystery quest",
        "figure out where the map points",
        "A little box opened with a surprise inside",
        "the map showed a path past the spill",
        "the map spread open on a dry table",
        tags={"quest", "mystery", "surprise"},
    ),
}

SPILLS = {
    "juice": Spill("juice", "juice", "juice", "spread", "sticky", "disperse", True, {"spill", "sweet"}),
    "paint": Spill("paint", "paint", "paint", "spread", "bright", "disperse", True, {"spill", "paint"}),
    "ink": Spill("ink", "ink", "ink", "spread", "dark", "disperse", True, {"spill", "ink"}),
}

RESPONSES = {
    "towels": Response(
        "towels", 3, 3,
        "used clean towels to soak up the spill until the floor was dry",
        "used towels, but the spill was already too wide to soak up",
        "used clean towels to soak up the spill",
        tags={"solve", "spill"},
    ),
    "cones": Response(
        "cones", 2, 2,
        "set out bright cones and guided everyone back so the clue could be seen",
        "set out cones, but there was still too much mess to keep the trail clear",
        "set out bright cones and guided everyone back",
        tags={"solve", "disperse"},
    ),
    "tray": Response(
        "tray", 2, 4,
        "slid a dry tray under the wet patch and lifted the clue out of danger",
        "slid in a tray, but the spill had already soaked through",
        "slid a dry tray under the wet patch and lifted the clue out of danger",
        tags={"solve", "clue"},
    ),
    "broom": Response(
        "broom", 1, 1,
        "swept at the spill with a broom",
        "swept, but that only spread the mess around",
        "swept at the spill",
        tags={"solve", "weak"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Elsa", "June"]
BOY_NAMES = ["Theo", "Arlo", "Finn", "Evan", "Owen", "Max"]
TRAITS = ["careful", "brave", "quiet", "curious", "gentle", "clever"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    spill: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTING_REGISTRY.items():
        for qid, quest in QUEST_REGISTRY.items():
            for spill_id, spill in SPILLS.items():
                if not need_careful_reason(spill, quest):
                    continue
                combos.append((sid, qid, spill_id))
    return combos


def explain_rejection(spill: Spill, quest: MysteryQuest) -> str:
    return (
        f"(No story: this mystery needs a real spill that can hide or smear a clue. "
        f"Try a mess like juice, paint, or ink.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery quest storyworld with a spill, a surprise, and a squeamish clue-hunter.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spill and args.quest:
        if not need_careful_reason(SPILLS[args.spill], QUEST_REGISTRY[args.quest]):
            raise StoryError(explain_rejection(SPILLS[args.spill], QUEST_REGISTRY[args.quest]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.spill is None or c[2] == args.spill)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, spill = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    if helper == hero:
        helper = _pick_name(rng, helper_gender)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, quest, spill, response, hero, hero_gender, helper, helper_gender, trait, delay)


def _do_spill(world: World, spill: Spill) -> None:
    world.get("cup").meters["spilled"] += 1
    world.get("hall").meters["mess"] += 1
    world.get("clue").meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(f"Then the cup tipped, and {spill.label} spilled across the floor.")


def generate(params: StoryParams) -> StorySample:
    world = World()
    setting = SETTING_REGISTRY[params.setting]
    quest = QUEST_REGISTRY[params.quest]
    spill = SPILLS[params.spill]
    response = RESPONSES[params.response]
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="hero", traits=[params.trait, "squeamish"]))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper", traits=["helpful"]))
    crowd = world.add(Entity("crowd", "thing", "crowd"))
    hall = world.add(Entity("hall", "thing", "hall", attrs={"setting": setting.id}))
    clue = world.add(Entity("clue", "thing", "clue"))
    cup = world.add(Entity("cup", "thing", spill.label))
    build_disperse(world, quest, crowd)
    world.para()
    notice_spill(world, hero, spill, setting)
    warn_and_guess(world, helper, hero, spill, quest)
    _do_spill(world, spill)
    world.para()
    success = solve_problem(world, hero, helper, response, spill, params.delay)
    conclude(world, hero, quest, setting, response, success)
    world.facts.update(
        hero=hero, helper=helper, setting=setting, quest=quest, spill=spill,
        response=response, crowd=crowd, hall=hall, clue=clue, cup=cup,
        success=success, delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "disperse", "spill", and "squeamish".',
        f"Tell a quest story where {f['hero'].id} feels squeamish about a spill, but still solves the mystery with a helpful friend.",
        f"Write a surprise-and-problem-solving story in a mystery style about a clue hidden by a spill in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, setting, quest, spill = f["hero"], f["helper"], f["setting"], f["quest"], f["spill"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, who are trying to solve a mystery in {setting.place}."),
        ("Why was {hero} squeamish?".format(hero=hero.id),
         f"{hero.id} was squeamish because the {spill.label} looked sticky and strange on the floor. That made the clue hard to see at first."),
        ("What was the surprise?",
         f"The surprise was {quest.surprise.lower()}. It started the mystery and made everyone stop and look closely."),
    ]
    if f["success"]:
        qa.append((
            "How did they solve the problem?",
            f"They used {f['response'].id} to clear the spill and help the crowd disperse. That let the clue become visible again and kept the quest moving."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {quest.ending_image}. The mystery was solved, and the hall was calm again."
        ))
    else:
        qa.append((
            "How did they try to solve the problem?",
            f"They tried {f['response'].qa_text.replace('{spill}', spill.label)}, but it was not enough. The trail stayed muddy and the mystery had to wait."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest"].tags) | set(f["spill"].tags) | set(f["response"].tags)
    bank = {
        "spill": [("What is a spill?", "A spill happens when a liquid falls out of a cup or container and spreads across a surface.")],
        "squeamish": [("What does squeamish mean?", "Squeamish means a little uneasy about something messy, gross, or surprising.")],
        "disperse": [("What does disperse mean?", "To disperse means to spread apart or scatter so a crowd is no longer packed together.")],
        "quest": [("What is a quest?", "A quest is a journey or task where someone looks for something or tries to solve a goal.")],
        "mystery": [("What is a mystery?", "A mystery is something puzzling that you need clues to figure out.")],
        "problem": [("What is problem solving?", "Problem solving means thinking carefully, trying a plan, and changing it if needed.")],
        "surprise": [("What is a surprise?", "A surprise is something unexpected that makes people stop and look.")],
    }
    order = ["surprise", "spill", "squeamish", "disperse", "quest", "mystery", "problem"]
    out = []
    for key in order:
        if key in tags and key in bank:
            out.extend(bank[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
spill_hides_clue(S) :- spill(S), messy(S).
sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.
can_solve(R, S) :- sensible(R), spill_hides_clue(S), power(R, P), power_need(S, N), P >= N.
valid(St, Q, Sp) :- setting(St), quest(Q), spill(Sp), spill_hides_clue(Sp).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for qid in QUEST_REGISTRY:
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("power_need", qid, 2))
    for sid, s in SPILLS.items():
        lines.append(asp.fact("spill", sid))
        if s.messy:
            lines.append(asp.fact("messy", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x[0] for x in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: story generation failed.")
    else:
        print("OK: story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("old_hall", "key_quest", "juice", "towels", "Mina", "girl", "Theo", "boy", "careful", 0),
    StoryParams("library", "note_quest", "ink", "cones", "Arlo", "boy", "Nora", "girl", "curious", 1),
    StoryParams("garden_shed", "map_quest", "paint", "tray", "Ivy", "girl", "Max", "boy", "brave", 0),
]


def show_asp() -> None:
    print(asp_program("", "#show valid/3.\n#show sensible/1."))


def generate_story(params: StoryParams) -> World:
    world = World()
    setting = SETTING_REGISTRY[params.setting]
    quest = QUEST_REGISTRY[params.quest]
    spill = SPILLS[params.spill]
    response = RESPONSES[params.response]
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="hero", traits=[params.trait, "squeamish"]))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper", traits=["helpful"]))
    world.add(Entity("crowd", "thing", "crowd"))
    world.add(Entity("hall", "thing", "hall"))
    world.add(Entity("clue", "thing", "clue"))
    world.add(Entity("cup", "thing", "cup"))
    build_disperse(world, quest, world.get("crowd"))
    world.para()
    notice_spill(world, hero, spill, setting)
    warn_and_guess(world, helper, hero, spill, quest)
    do_spill(world, spill)
    world.para()
    success = solve_problem(world, hero, helper, response, spill, params.delay)
    conclude(world, hero, quest, setting, response, success)
    world.facts.update(hero=hero, helper=helper, setting=setting, quest=quest, spill=spill, response=response, success=success)
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery quest storyworld with a spill, a surprise, and squeamish problem solving.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.spill is None or c[2] == args.spill)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, spill = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    if helper == hero:
        helper = _pick_name(rng, helper_gender)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, quest, spill, response, hero, hero_gender, helper, helper_gender, trait, delay)


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for t in asp_valid_combos():
            print(" ".join(map(str, t)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.spill} in {p.setting} ({p.quest})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
