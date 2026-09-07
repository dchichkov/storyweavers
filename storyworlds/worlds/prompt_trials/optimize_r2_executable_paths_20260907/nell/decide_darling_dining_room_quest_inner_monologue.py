#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what kindness requires.

The story follows Darling, who must choose how to save a small celebration
when a treasured serving dish is missing its final piece. The simulation keeps
the quest, clue, suspense, spoken exchange, and ending state causal.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
for parent in _HERE.parents:
    candidate = parent / "results.py"
    if candidate.exists():
        sys.path.insert(0, str(parent))
        break

from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PROBLEMS = ("missing_cup", "spilled_soup", "dark_table", "lonely_place")
SOLUTIONS = ("ask_kindly", "make_alternative")
MOODS = ("tender", "bright", "quiet")
VOICES = ("gentle", "playful", "plain")
NAMES = ("Darling", "Mina", "Jo", "Lina")
MAX_ACTIONS = 16


@dataclass
class StoryParams:
    hero: str = "Darling"
    problem: str = "missing_cup"
    solution: str = "ask_kindly"
    mood: str = "tender"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = "dining_room"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Action:
    kind: str
    actor: str
    target: str = ""


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.fact_events: dict[str, int] = {}
        self.outcome = ""

    def snapshot(self) -> dict:
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind: str, actor: str, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs an earlier clue: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        event = Event(
            id=event_id,
            kind=kind,
            actor=actor,
            data=data,
            facts=tuple(facts),
            causes=causes,
            state=self.snapshot(),
        )
        self.history.append(event)
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    for value, choices, label in (
        (p.problem, PROBLEMS, "problem"),
        (p.solution, SOLUTIONS, "solution"),
        (p.mood, MOODS, "mood"),
        (p.voice, VOICES, "voice"),
    ):
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if not re.fullmatch(r"[A-Z][a-z]+", p.hero):
        raise StoryError("Hero name must be a simple capitalized name.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")
    if p.problem == "lonely_place" and p.solution == "ask_kindly":
        raise StoryError("A lonely place needs a welcoming arrangement before a request can help.")


PATHS = {
    ("missing_cup", "ask_kindly"): {
        "clue": "cup_location",
        "actions": ("ask_grandma", "find_cup", "set_cup"),
        "ending": "cup_returned",
    },
    ("missing_cup", "make_alternative"): {
        "clue": "cup_location",
        "actions": ("ask_grandma", "choose_mug", "set_mug"),
        "ending": "new_place_setting",
    },
    ("spilled_soup", "ask_kindly"): {
        "clue": "spill_seen",
        "actions": ("notice_spill", "ask_grandma", "clean_soup"),
        "ending": "table_clean",
    },
    ("spilled_soup", "make_alternative"): {
        "clue": "spill_seen",
        "actions": ("notice_spill", "choose_bread", "serve_bread"),
        "ending": "warm_bread",
    },
    ("dark_table", "ask_kindly"): {
        "clue": "darkness_seen",
        "actions": ("notice_darkness", "ask_grandma", "light_lamp"),
        "ending": "table_lit",
    },
    ("dark_table", "make_alternative"): {
        "clue": "darkness_seen",
        "actions": ("notice_darkness", "choose_candles", "light_candles"),
        "ending": "candle_glow",
    },
    ("lonely_place", "make_alternative"): {
        "clue": "empty_chair_seen",
        "actions": ("notice_empty_chair", "choose_card", "place_card"),
        "ending": "chair_welcomed",
    },
}


def build_world(p: StoryParams) -> World:
    validate_params(p)
    path = PATHS.get((p.problem, p.solution))
    if path is None:
        raise StoryError("That solution does not fit the dining-room problem.")
    w = World(p)
    w.entities = {
        "hero": Entity(
            "hero",
            p.hero,
            "character",
            memes={"care": 1, "worry": 0.3, "courage": 0.4},
            beliefs={"goal": "make_dinner_welcoming"},
        ),
        "grandma": Entity(
            "grandma",
            "Grandma",
            "character",
            owner="family",
            memes={"love": 1, "tired": 0.2},
            beliefs={"truth": "help_is_welcome"},
        ),
        "table": Entity(
            "table",
            "the long dining table",
            meters={"seats": 5, "light": 1, "clean": 1},
            memes={"welcome": 0.4},
        ),
        "cup": Entity(
            "cup",
            "the blue cup",
            owner="family",
            location="pantry",
            meters={"whole": 1},
        ),
        "mug": Entity(
            "mug",
            "the yellow mug",
            owner="family",
            location="shelf",
            meters={"whole": 1},
        ),
        "soup": Entity(
            "soup",
            "the spilled soup",
            location="table",
            meters={"mess": 1},
        ),
        "lamp": Entity(
            "lamp",
            "the little lamp",
            location="sideboard",
            meters={"lit": 0},
        ),
        "candles": Entity(
            "candles",
            "two stubby candles",
            location="drawer",
            meters={"lit": 0},
        ),
        "card": Entity(
            "card",
            "a folded welcome card",
            location="drawer",
            meters={"written": 1},
        ),
        "chair": Entity(
            "chair",
            "the empty chair",
            location="table",
            meters={"ready": 0},
        ),
    }
    w.record(
        "opening",
        "hero",
        facts=("quest_started",),
        problem=p.problem,
        solution=p.solution,
    )
    return w


def choose_action(w: World) -> Action:
    if "ending" in w.fact_events:
        return Action("finish", "grandma")
    path = PATHS[(w.params.problem, w.params.solution)]
    for kind in path["actions"]:
        if not any(event.kind == kind for event in w.history):
            actor = "grandma" if kind == "ask_grandma" else "hero"
            return Action(kind, actor)
    raise StoryError("The path has no remaining action but is not resolved.")


def execute(w: World, action: Action):
    k = action.kind
    p = w.params
    hero = w.entities["hero"]
    grandma = w.entities["grandma"]
    table = w.entities["table"]

    def require(condition: bool, message: str):
        if not condition:
            raise StoryError(message)

    if k == "ask_grandma":
        require("quest_started" in w.fact_events, "The quest must begin before advice is requested.")
        hero.beliefs["help_is_welcome"] = "yes"
        w.record(
            k,
            action.actor,
            facts=("permission_heard",),
            needs=("quest_started",),
            words="Grandma welcomes help",
        )
    elif k == "notice_spill":
        require(p.problem == "spilled_soup", "There is no soup spill to notice.")
        hero.beliefs["mess_needs_attention"] = "yes"
        w.entities["hero"].memes["worry"] = 0.8
        w.record(k, action.actor, facts=("spill_seen",), needs=("quest_started",))
    elif k == "notice_darkness":
        require(p.problem == "dark_table", "The dining room is not dark in this path.")
        hero.beliefs["light_needed"] = "yes"
        w.record(k, action.actor, facts=("darkness_seen",), needs=("quest_started",))
    elif k == "notice_empty_chair":
        require(p.problem == "lonely_place", "There is no lonely place to notice.")
        hero.beliefs["chair_needs_welcome"] = "yes"
        w.record(k, action.actor, facts=("empty_chair_seen",), needs=("quest_started",))
    elif k == "find_cup":
        require(p.problem == "missing_cup" and p.solution == "ask_kindly", "The blue cup is not this path's answer.")
        require("permission_heard" in w.fact_events, "Darling must hear that asking is welcome.")
        w.entities["cup"].location = "table"
        w.record(k, action.actor, facts=("cup_found",), needs=("permission_heard",))
    elif k == "set_cup":
        require("cup_found" in w.fact_events, "The cup must be found first.")
        table.meters["welcome"] = 1
        w.outcome = "cup_returned"
        w.record(k, action.actor, facts=("ending",), needs=("cup_found",))
    elif k == "choose_mug":
        require(p.problem == "missing_cup" and p.solution == "make_alternative", "The mug is not this path's answer.")
        w.entities["mug"].location = "table"
        hero.beliefs["alternative_is_kind"] = "yes"
        w.record(k, action.actor, facts=("mug_chosen",), needs=("quest_started",))
    elif k == "set_mug":
        require("mug_chosen" in w.fact_events, "The mug must be chosen first.")
        table.meters["welcome"] = 1
        w.outcome = "new_place_setting"
        w.record(k, action.actor, facts=("ending",), needs=("mug_chosen",))
    elif k == "clean_soup":
        require("spill_seen" in w.fact_events and p.solution == "ask_kindly", "The spill must be seen before it can be cleaned.")
        w.entities["soup"].meters["mess"] = 0
        table.meters["clean"] = 1
        w.outcome = "table_clean"
        w.record(k, action.actor, facts=("ending",), needs=("spill_seen", "permission_heard"))
    elif k == "choose_bread":
        require("spill_seen" in w.fact_events and p.solution == "make_alternative", "The spill must be noticed first.")
        hero.beliefs["bread_can_help"] = "yes"
        w.record(k, action.actor, facts=("bread_chosen",), needs=("spill_seen",))
    elif k == "serve_bread":
        require("bread_chosen" in w.fact_events, "The bread must be chosen first.")
        w.entities["soup"].meters["mess"] = 0
        table.meters["welcome"] = 1
        w.outcome = "warm_bread"
        w.record(k, action.actor, facts=("ending",), needs=("bread_chosen",))
    elif k == "light_lamp":
        require("darkness_seen" in w.fact_events and p.solution == "ask_kindly", "Darkness must be noticed before the lamp is chosen.")
        w.entities["lamp"].meters["lit"] = 1
        table.meters["light"] = 1
        w.outcome = "table_lit"
        w.record(k, action.actor, facts=("ending",), needs=("darkness_seen", "permission_heard"))
    elif k == "choose_candles":
        require("darkness_seen" in w.fact_events and p.solution == "make_alternative", "Darkness must be noticed first.")
        hero.beliefs["candles_can_help"] = "yes"
        w.record(k, action.actor, facts=("candles_chosen",), needs=("darkness_seen",))
    elif k == "light_candles":
        require("candles_chosen" in w.fact_events, "The candles must be chosen first.")
        w.entities["candles"].meters["lit"] = 1
        table.meters["light"] = 1
        w.outcome = "candle_glow"
        w.record(k, action.actor, facts=("ending",), needs=("candles_chosen",))
    elif k == "place_card":
        require("card_chosen" in w.fact_events, "The card must be chosen first.")
        w.entities["card"].location = "chair"
        w.entities["chair"].meters["ready"] = 1
        table.meters["welcome"] = 1
        w.outcome = "chair_welcomed"
        w.record(k, action.actor, facts=("ending",), needs=("card_chosen",))
    elif k == "choose_card":
        require("empty_chair_seen" in w.fact_events, "The empty chair must be noticed first.")
        hero.beliefs["card_can_help"] = "yes"
        w.record(k, action.actor, facts=("card_chosen",), needs=("empty_chair_seen",))
    elif k == "finish":
        require(bool(w.outcome), "The dining-room quest is not resolved.")
        w.record(k, action.actor, facts=("closed",), needs=("ending",))
    else:
        raise StoryError(f"Unknown action {k!r}.")


def validate_world(w: World):
    if not w.outcome or "ending" not in w.fact_events:
        raise StoryError("A complete story needs a resolved ending.")
    table = w.entities["table"]
    meter = "clean" if w.outcome == "table_clean" else "light" if w.outcome in {"table_lit", "candle_glow"} else "welcome"
    if table.meters[meter] < 1:
        raise StoryError("The changed table must show the chosen solution's effect.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")
    if not any(
        e.kind in {"ask_grandma", "choose_mug", "choose_bread", "choose_candles", "choose_card"}
        for e in w.history
    ):
        raise StoryError("The story needs a meaningful decision.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "closed" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The dining-room quest did not finish.")


def spoken_exchange(p: StoryParams, moment: str) -> tuple[str, str]:
    if moment == "opening":
        if p.voice == "playful":
            return (f'"Darling, what are you searching for?" Grandma asked.',
                    '"I am deciding how to make dinner feel right," Darling said.')
        if p.voice == "plain":
            return (f'"What troubles you, darling?" Grandma asked.',
                    '"I want to help," {0} said.'.format(p.hero))
        return (f'"You look thoughtful, darling," Grandma said.',
                f'"I am deciding what kindness needs," {p.hero} replied.')
    if p.solution == "ask_kindly":
        return (f'"May I change something?" {p.hero} asked.',
                '"Yes, darling. Thank you for asking," Grandma said.')
    if p.problem == "lonely_place":
        return (f'"The chair looks lonely," {p.hero} said.',
                '"Then give it a welcome," Grandma answered.')
    return (f'"This is not what we planned," {p.hero} said.',
            '"No," Grandma replied, "but it can still be good."')


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.paragraphs: list[str] = []
        self.qa: list[QAItem] = []

    def say(self, text: str):
        self.paragraphs.append(text)

    def render(self) -> tuple[str, list[QAItem]]:
        p = self.p
        hero = p.hero
        self.say(random_choice(self.rng, (
            f"In the dining room, {hero} stood beside the long table while evening gathered at the windows.",
            f"The dining room was almost ready for dinner, but {hero} saw one small trouble waiting on the table.",
            f"Warm smells drifted through the dining room. {hero} looked around and felt a little worry tug at the celebration.",
        )))
        self.paragraphs.extend(spoken_exchange(p, "opening"))
        self.say(random_choice(self.rng, (
            f"Inside, {hero} wondered whether helping meant following the plan or finding a kinder one.",
            f"{hero} took a breath. The quest was small, but someone's comfort might depend on the choice.",
            f"The room was quiet enough for {hero} to hear the old clock tick. A decision was waiting.",
        )))

        for event in self.world.history[1:]:
            self.render_event(event)

        return "\n\n".join(self.paragraphs), self.qa

    def render_event(self, event: Event):
        p = self.p
        hero = p.hero
        k = event.kind
        if k == "ask_grandma":
            self.say(f"{hero} looked to Grandma instead of guessing.")
            self.paragraphs.extend(spoken_exchange(p, "decision"))
            self.say("The answer did not erase the suspense, but it made the next step feel safe.")
            self.qa.append(QAItem(
                question="Why did Darling ask Grandma before acting?",
                answer="Darling asked because helping kindly meant checking what Grandma wanted instead of changing the dining room by guesswork.",
            ))
        elif k == "notice_spill":
            self.say(f"{hero} saw soup shining across the tablecloth. The bowls were ready, but the spill could stain the place where everyone would eat.")
            self.qa.append(QAItem(
                question="What problem did Darling notice?",
                answer="Darling noticed soup spilled across the dining table and understood that the mess needed attention before dinner.",
            ))
        elif k == "notice_darkness":
            self.say("The dining room grew dim before the meal began. Faces at the table would soon be hard to see.")
            self.qa.append(QAItem(
                question="Why did the dining room need light?",
                answer="Evening darkness was gathering, so the people at the table would need light to see one another and their dinner.",
            ))
        elif k == "notice_empty_chair":
            self.say(f"{hero} noticed an empty chair at the table. It looked less like furniture and more like someone had been forgotten.")
            self.qa.append(QAItem(
                question="What made the empty chair important?",
                answer="The empty chair made the table feel as if someone had been forgotten, so Darling decided to make it welcoming.",
            ))
        elif k == "find_cup":
            self.say("Grandma's answer gave Darling courage to search the pantry. Behind a jar of rice, the blue cup waited in a stripe of moonlight.")
            self.qa.append(QAItem(
                question="Where did Darling find the missing cup?",
                answer="Darling found the blue cup in the pantry, behind a jar of rice.",
            ))
        elif k == "set_cup":
            self.say("Darling placed the blue cup beside Grandma's plate. The setting was complete, and the table seemed to breathe out.")
            self.qa.append(QAItem(
                question="How was the missing-cup problem solved?",
                answer="Darling found the blue cup in the pantry and placed it beside Grandma's plate after asking if help was welcome.",
            ))
        elif k == "choose_mug":
            self.say("The blue cup was still missing, so Darling chose the yellow mug instead. It was not the planned cup, but it was clean, bright, and ready.")
            self.qa.append(QAItem(
                question="Why did Darling choose the yellow mug?",
                answer="Darling chose the yellow mug as a useful alternative because the planned blue cup was missing and the meal still needed a place for Grandma's drink.",
            ))
        elif k == "set_mug":
            self.say("Darling set the yellow mug beside Grandma's plate. Grandma smiled at its sunny handle, and the unplanned place setting felt specially hers.")
            self.qa.append(QAItem(
                question="What changed when Darling set out the mug?",
                answer="The yellow mug gave Grandma a complete place setting even though the blue cup was missing, turning the problem into a warm surprise.",
            ))
        elif k == "clean_soup":
            self.say("With Grandma's permission, Darling carried a cloth from the sideboard and wiped the soup away. The tablecloth dried beneath a clean plate.")
            self.qa.append(QAItem(
                question="How did Darling solve the spill?",
                answer="Darling asked before changing the table, then wiped the spilled soup away so the clean tablecloth could hold the dinner plates.",
            ))
        elif k == "choose_bread":
            self.say("Darling decided not to chase the spill with panic. A basket of warm bread could fill the empty spot while the table was made ready.")
            self.qa.append(QAItem(
                question="What alternative did Darling choose after seeing the spill?",
                answer="Darling chose warm bread as a welcoming alternative, giving the table something comforting while the meal was adjusted.",
            ))
        elif k == "serve_bread":
            self.say("Darling set the bread in the cleared place. Its warm smell drew everyone closer, and the mistake became part of dinner.")
            self.qa.append(QAItem(
                question="What proved the bread solution worked?",
                answer="The bread filled the cleared place and brought everyone closer, so the spill no longer kept the dining room from feeling welcoming.",
            ))
        elif k == "light_lamp":
            self.say("After Grandma nodded, Darling switched on the little lamp. Gold light spread over the plates and made every face clear again.")
            self.qa.append(QAItem(
                question="How did Darling brighten the dining room?",
                answer="Darling asked first and then switched on the little lamp, spreading warm light across the table.",
            ))
        elif k == "choose_candles":
            self.say("Darling found two stubby candles in the drawer. The lamp was not the only way to bring brightness to the table.")
            self.qa.append(QAItem(
                question="Why did Darling choose candles?",
                answer="Darling chose candles as a different way to brighten the dark table when the usual plan was not enough.",
            ))
        elif k == "light_candles":
            self.say("The two candles flickered beside the plates. Their little flames made the dining room feel close and golden.")
            self.qa.append(QAItem(
                question="What changed after Darling lit the candles?",
                answer="The candle flames spread gentle light across the plates and made the dark dining room feel warm and intimate.",
            ))
        elif k == "choose_card":
            self.say("Darling found a folded card in the drawer and wrote, 'There is always room for you.'")
            self.qa.append(QAItem(
                question="What did Darling put on the welcome card?",
                answer="Darling wrote, 'There is always room for you,' so the empty chair would feel meant for someone.",
            ))
        elif k == "place_card":
            self.say("Darling placed the card on the empty chair. When Grandma read it, she pulled the chair closer to the table.")
            self.qa.append(QAItem(
                question="How did the card change the empty chair?",
                answer="The card told the absent guest there was always room, and Grandma pulled the chair closer so the place felt welcoming rather than forgotten.",
            ))
        elif k == "finish":
            self.say(random_choice(self.rng, (
                f"At last, {hero} sat beside Grandma. The dining room held the small proof of the decision: a cup, mug, bread basket, golden light, or welcome waiting where it was needed.",
                f"Everyone gathered around the changed table. {hero} felt the suspense loosen into happiness because the room now welcomed people, not just a perfect plan.",
                f"The clock kept ticking, but the worry had gone. In the dining room, {hero} and Grandma shared the first warm moment of dinner.",
            )))
            self.paragraphs.extend((
                f'"You decided well, darling," Grandma said.',
                f'"I listened to what the room needed," {hero} replied.',
            ))
            self.qa.append(QAItem(
                question="What did Darling learn?",
                answer="Darling learned that a loving decision can follow the real need in front of you, even when the original plan changes.",
            ))
        else:
            raise StoryError(f"No rendering for event {k!r}.")


def random_choice(rng: random.Random, values):
    return rng.choice(tuple(values))


ASP_RULES = """
compatible(missing_cup,ask_kindly).
compatible(missing_cup,make_alternative).
compatible(spilled_soup,ask_kindly).
compatible(spilled_soup,make_alternative).
compatible(dark_table,ask_kindly).
compatible(dark_table,make_alternative).
compatible(lonely_place,make_alternative).
#show compatible/2.
"""


def valid_combos():
    return set(PATHS)


def asp_facts():
    from asp import fact
    return "\n".join(
        fact("problem", value) for value in PROBLEMS
    ) + "\n" + "\n".join(fact("solution", value) for value in SOLUTIONS)


def asp_combos():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return {(a, b) for a, b in atoms(model, "compatible")}


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).render()
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a heartwarming dining-room quest in which {params.hero} must decide how to help.",
            "Use suspense, an inner monologue, and a brief spoken exchange.",
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                question="What makes a helpful decision kind?",
                answer="A helpful decision is kind when it responds to the real need and respects the people involved.",
            )
        ],
        world=world,
    )


def verify():
    if valid_combos() != asp_combos():
        raise StoryError("Python and ASP disagree about compatible paths.")
    for problem, solution in sorted(valid_combos()):
        p = StoryParams(problem=problem, solution=solution)
        sample = generate(p)
        if not sample.story or not sample.story_qa:
            raise StoryError("A generated path lacks story or grounded QA.")
        if p.hero not in sample.story:
            raise StoryError("The hero name is missing from the story.")
        if '"' not in sample.story:
            raise StoryError("The story lacks spoken dialogue.")
        if any(token in sample.story for token in ("{hero}", "{problem}", "{solution}")):
            raise StoryError("Unresolved template field in story.")
        if sample.world.outcome != PATHS[(problem, solution)]["ending"]:
            raise StoryError("The executed path reached the wrong ending.")
    print(f"OK: {len(valid_combos())} executable paths; ASP parity; grounded dialogue and QA.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--mood", choices=MOODS, default="tender")
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        mood=args.mood,
        voice=args.voice,
    )
    for name, choices in (
        ("hero", NAMES),
        ("problem", PROBLEMS),
        ("solution", SOLUTIONS),
    ):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else (rng.choice(choices) if sample else getattr(p, name)))
    if (p.problem, p.solution) not in PATHS:
        if sample:
            compatible = [pair for pair in PATHS if pair[0] == p.problem]
            if not compatible:
                compatible = list(PATHS)
            p.problem, p.solution = rng.choice(compatible)
        else:
            raise StoryError("That problem and solution pair is not compatible.")
    validate_params(p)
    return p


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, ensure_ascii=False, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for problem, solution in sorted(PATHS):
                if args.problem is not None and args.problem != problem:
                    continue
                if args.solution is not None and args.solution != solution:
                    continue
                params.append(StoryParams(
                    hero=args.hero or "Darling",
                    problem=problem,
                    solution=solution,
                    mood=args.mood,
                    voice=args.voice,
                    world_seed=args.world_seed + len(params),
                    prose_seed=args.prose_seed + len(params),
                ))
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, params_item in enumerate(params):
                emit(
                    generate(params_item),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
