#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/teak_lunge_bravery_quest_dialogue_adventure.py
===============================================================================

A standalone storyworld for a small adventure quest about brave kids, a teak
bridge, and a risky lunge that becomes a lesson. The domain is built to read
like a TinyStories-style adventure: a quest begins, a problem appears, dialogue
shapes the choice, bravery is tested, and the ending proves what changed.

Seed words:
- teak
- lunge

Features:
- Bravery
- Quest
- Dialogue

Style:
- Adventure
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
BRAVERY_START = 5.0
CAREFUL_TRAITS = {"careful", "steady", "thoughtful", "cautious"}


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
class Place:
    id: str
    label: str
    bridge: str
    danger: str
    sound: str
    route: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    needed: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    scout = world.entities.get("scout")
    if not scout:
        return out
    if scout.memes["bravery"] < THRESHOLD:
        return out
    sig = ("brave", scout.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.memes["resolve"] += 1
    out.append("__resolve__")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    plank = world.entities.get("bridge")
    if not plank:
        return out
    if plank.meters["split"] < THRESHOLD:
        return out
    sig = ("risk", plank.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] += 1
    out.append("__risk__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("brave", _r_brave), Rule("risk", _r_risk)]


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


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def bridge_is_dangerous(place: Place) -> bool:
    return "swing" in place.danger or "gap" in place.danger


def action_fits(place: Place, item: QuestItem) -> bool:
    return item.needed in place.route or item.needed in place.tags


def choose_action(action: Action) -> bool:
    return action.sense >= 2


def brave_enough(trait: str) -> float:
    return 6.0 if trait in CAREFUL_TRAITS else 4.0


def would_choose_lunge(relation: str, scout_age: int, guide_age: int, trait: str) -> bool:
    if relation != "siblings":
        return True
    older_guide = guide_age > scout_age
    authority = (2.0 if trait in CAREFUL_TRAITS else 1.0) + (3.0 if older_guide else 0.0)
    return not (older_guide and authority > BRAVERY_START)


def predict_trip(world: World) -> dict:
    sim = world.copy()
    _do_lunge(sim, narrate=False)
    return {"split": sim.get("bridge").meters["split"], "fear": sum(e.memes["fear"] for e in sim.characters())}


def _do_lunge(world: World, narrate: bool = True) -> None:
    bridge = world.get("bridge")
    bridge.meters["split"] += 1
    propagate(world, narrate=narrate)


def start_adventure(world: World, scout: Entity, guide: Entity, place: Place, item: QuestItem) -> None:
    scout.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"At the edge of the forest, {scout.id} and {guide.id} found {place.label}. "
        f"The path smelled of leaves, and the old teak bridge waited over the water."
    )
    world.say(
        f'They were on a quest for {item.phrase}. "{item.clue}" {scout.id} said, '
        f"peering toward the far bank."
    )


def need_crossing(world: World, guide: Entity, place: Place, item: QuestItem) -> None:
    world.say(
        f"But the {place.bridge} was the only way across. Beyond it, the trail bent "
        f"toward the place where {item.label} could be found."
    )
    world.say(f'"We need a safe way over," {guide.id} said.')


def tempt_lunge(world: World, scout: Entity, action: Action) -> None:
    scout.memes["bravery"] = BRAVERY_START
    world.say(
        f'{scout.id} took a deep breath. "I can do it," {scout.pronoun()} whispered, '
        f'and looked ready to {action.id}.'
    )


def warn(world: World, guide: Entity, scout: Entity, place: Place, item: QuestItem) -> None:
    pred = predict_trip(world)
    guide.memes["care"] += 1
    world.facts["predicted_split"] = pred["split"]
    world.say(
        f'"Careful," {guide.id} said. "That teak board is old, and if it splits, '
        f"we'll be stuck on the wrong side of the river.""
    )


def answer_dialogue(world: World, scout: Entity, guide: Entity, place: Place, action: Action) -> None:
    scout.memes["resolve"] += 1
    world.say(
        f'"Then we do it together," {scout.id} said. '
        f'"We take the slow step, not the wild {action.id}."'
    )


def accept_calm(world: World, guide: Entity, scout: Entity, item: QuestItem) -> None:
    scout.memes["bravery"] += 1
    scout.memes["fear"] = 0.0
    world.say(
        f'{guide.id} nodded. "That is bravery too," {guide.id} said. '
        f'"Bravery is not rushing when rushing would break the bridge."'
    )


def cross_safely(world: World, scout: Entity, guide: Entity, place: Place, item: QuestItem) -> None:
    scout.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"So they crossed one careful step at a time. The teak boards held, the river "
        f"glimmered below, and the quest stayed on track."
    )
    world.say(
        f"On the far side, {item.phrase} waited as if it had been there all along, "
        f"and the two travelers smiled at the simple, steady way they had found it."
    )


def risky_lunge(world: World, scout: Entity, place: Place, action: Action) -> None:
    scout.memes["defiance"] += 1
    world.say(
        f'"Don't worry," {scout.id} said, and in one daring moment {scout.pronoun()} '
        f"tried to {action.id} across the teak bridge."
    )


def alarm(world: World, guide: Entity, place: Place) -> None:
    world.say(f'"{guide.id}! The teak bridge!" {guide.id} cried.')
    world.say(f'"It cracked!"')


def rescue(world: World, guide: Entity, action: Action) -> None:
    bridge = world.get("bridge")
    bridge.meters["split"] = 0.0
    world.say(
        f"{guide.label_word.capitalize()} grabbed the scout back before the gap grew. "
        f"In a blink, {guide.id} pulled {action.qa_text} into a safer plan."
    )


def lesson(world: World, guide: Entity, scout: Entity, item: QuestItem) -> None:
    scout.memes["resolve"] += 1
    world.say(
        f"For a moment, nobody moved. Then {guide.id} smiled and said, "
        f'"A quest can wait. Bravery means keeping the team safe."'
    )
    world.say(
        f'"We promise," {scout.id} said, and they both looked back at the teak bridge '
        f"with new respect."
    )
    world.say(
        f"The next trail was quieter, and the quest felt even better because they had "
        f"chosen the wise path together."
    )


def tell(place: Place, item: QuestItem, action: Action,
         scout_name: str = "Nina", scout_gender: str = "girl",
         guide_name: str = "Milo", guide_gender: str = "boy",
         guide_trait: str = "careful", relation: str = "friends",
         scout_age: int = 6, guide_age: int = 8) -> World:
    world = World()
    scout = world.add(Entity(id=scout_name, kind="character", type=scout_gender, role="scout"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide",
                             traits=[guide_trait], attrs={"relation": relation}))
    bridge = world.add(Entity(id="bridge", label=place.bridge, kind="thing"))
    bridge.meters["strength"] = 1.0

    start_adventure(world, scout, guide, place, item)
    world.para()
    need_crossing(world, guide, place, item)
    tempt_lunge(world, scout, action)
    warn(world, guide, scout, place, item)

    averted = would_choose_lunge(relation, scout_age, guide_age, guide_trait)
    if averted:
        answer_dialogue(world, scout, guide, place, action)
        accept_calm(world, guide, scout, item)
        world.para()
        cross_safely(world, scout, guide, place, item)
        outcome = "averted"
    else:
        risky_lunge(world, scout, place, action)
        world.para()
        world.get("bridge").meters["split"] += 1
        alarm(world, guide, place)
        rescue(world, guide, action)
        lesson(world, guide, scout, item)
        world.para()
        cross_safely(world, scout, guide, place, item)
        outcome = "contained"

    world.facts.update(
        scout=scout, guide=guide, place=place, item=item, action=action,
        outcome=outcome, averted=averted
    )
    return world


PLACES = {
    "forest": Place(
        id="forest",
        label="a forest path",
        bridge="teak bridge",
        danger="swinging gap",
        sound="the river below",
        route="crossing",
        tags={"forest", "bridge", "teak"},
    ),
    "island": Place(
        id="island",
        label="a tiny island camp",
        bridge="teak bridge",
        danger="wobbly gap",
        sound="the water below",
        route="crossing",
        tags={"island", "bridge", "teak"},
    ),
    "canyon": Place(
        id="canyon",
        label="a canyon trail",
        bridge="teak bridge",
        danger="deep gap",
        sound="the wind below",
        route="crossing",
        tags={"canyon", "bridge", "teak"},
    ),
}

QUESTS = {
    "map": QuestItem(
        id="map",
        label="lost map",
        phrase="the lost map",
        needed="crossing",
        clue="The map is past the bridge!",
        tags={"quest", "map"},
    ),
    "drum": QuestItem(
        id="drum",
        label="silver drum",
        phrase="the silver drum",
        needed="crossing",
        clue="The silver drum waits beyond the teak path!",
        tags={"quest", "drum"},
    ),
    "lantern": QuestItem(
        id="lantern",
        label="sun lantern",
        phrase="the sun lantern",
        needed="crossing",
        clue="The sun lantern is on the far side!",
        tags={"quest", "lantern"},
    ),
}

ACTIONS = {
    "lunge": Action(
        id="lunge",
        sense=3,
        power=2,
        text="lunge across the teak bridge",
        fail="reached for the bridge but the old board shook too hard",
        qa_text="slowly crossed the bridge",
        tags={"lunge", "teak", "quest"},
    ),
    "step": Action(
        id="step",
        sense=4,
        power=3,
        text="step carefully across",
        fail="stepped too fast and slipped",
        qa_text="stepped carefully",
        tags={"quest", "teak"},
    ),
    "wait": Action(
        id="wait",
        sense=5,
        power=4,
        text="wait and look first",
        fail="waited too long and lost the trail",
        qa_text="waited and looked first",
        tags={"quest", "dialogue"},
    ),
}

GIRL_NAMES = ["Nina", "Mira", "Lina", "Tia", "Aria", "Zoe"]
BOY_NAMES = ["Milo", "Oren", "Jace", "Pico", "Theo", "Ravi"]
TRAITS = ["careful", "steady", "thoughtful", "cautious", "bold"]


@dataclass
class StoryParams:
    place: str
    quest: str
    action: str
    scout_name: str
    scout_gender: str
    guide_name: str
    guide_gender: str
    guide_trait: str
    relation: str = "friends"
    scout_age: int = 6
    guide_age: int = 8
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for quest in QUESTS:
            for action in ACTIONS:
                if action_fits(PLACES[place], QUESTS[quest]) and choose_action(ACTIONS[action]):
                    combos.append((place, quest, action))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: teak, lunge, quest, dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--action", choices=ACTIONS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, action = rng.choice(sorted(combos))
    scout_gender = rng.choice(["girl", "boy"])
    guide_gender = "boy" if scout_gender == "girl" else "girl"
    scout_name = rng.choice(GIRL_NAMES if scout_gender == "girl" else BOY_NAMES)
    guide_name = rng.choice(BOY_NAMES if guide_gender == "boy" else GIRL_NAMES)
    guide_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        quest=quest,
        action=action,
        scout_name=scout_name,
        scout_gender=scout_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
        guide_trait=guide_trait,
        relation=rng.choice(["friends", "siblings"]),
        scout_age=rng.randint(5, 7),
        guide_age=rng.randint(6, 9),
    )


def _story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scout, guide, place, item, action = f["scout"], f["guide"], f["place"], f["item"], f["action"]
    return [
        ("What were they looking for?",
         f"They were on a quest for {item.phrase}. The clue led them toward the far side of {place.label}."),
        ("Why did the guide warn the scout?",
         f"{guide.id} warned {scout.id} because the teak bridge was old and could split. The warning mattered because a risky lunge could trap them on the wrong side."),
        ("What did the scout do at the end?",
         f"{scout.id} chose a slower way across and kept the quest going. That was brave because it protected the team and still moved the story forward."),
    ]


def _world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is teak?",
         "Teak is a hard kind of wood. People use it for strong boards, like the old bridge in this story."),
        ("What is a lunge?",
         "A lunge is a quick, reaching movement. It can be useful, but on a weak bridge it can be risky."),
        ("What is a quest?",
         "A quest is a search for something important. In adventure stories, a quest gives the characters a goal."),
        ("What is dialogue?",
         "Dialogue is when characters speak to each other. It helps the story show choices and feelings."),
        ("What is bravery?",
         "Bravery means doing the hard thing with a steady heart. Sometimes bravery is charging ahead, and sometimes it is choosing the safer step."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child that includes the words "teak" and "lunge" and shows a quest with dialogue.',
        f"Tell a brave quest story where {f['scout'].id} wants to lunge across a teak bridge, but words from {f['guide'].id} change the choice.",
        f"Write a short adventure with a teak bridge, a risky lunge, and a calm ending that proves bravery can be careful.",
    ]


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


ASP_RULES = r"""
valid(P,Q,A) :- place(P), quest(Q), action(A), fits(P,Q), sensible(A).
outcome(averted) :- older_guide, careful_guide.
outcome(contained) :- not outcome(averted).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, act.sense))
        if choose_action(act):
            lines.append(asp.fact("sensible", aid))
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            if action_fits(place, quest):
                lines.append(asp.fact("fits", pid, qid))
    lines.append(asp.fact("bravery_start", int(BRAVERY_START)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest not in QUESTS or params.action not in ACTIONS:
        raise StoryError("Invalid parameters.")
    world = tell(
        PLACES[params.place],
        QUESTS[params.quest],
        ACTIONS[params.action],
        scout_name=params.scout_name,
        scout_gender=params.scout_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        guide_trait=params.guide_trait,
        relation=params.relation,
        scout_age=params.scout_age,
        guide_age=params.guide_age,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in _story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in _world_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(e.id, meters, memes)
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
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, quest=q, action=a, scout_name="Nina", scout_gender="girl", guide_name="Milo", guide_gender="boy", guide_trait="careful")) for p, q, a in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False) if len(samples) > 1 else samples[0].to_json())
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
