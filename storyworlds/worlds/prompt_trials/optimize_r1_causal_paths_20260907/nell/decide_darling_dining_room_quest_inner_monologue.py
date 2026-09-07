#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what kindness requires."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PROBLEMS = ("missing_placecard", "spilled_soup", "dark_room", "lost_locket")
SOLUTIONS = ("ask_grandmother", "follow_clues", "share_task", "trust_memory")
VOICES = ("gentle", "playful", "plain")
MOODS = ("hopeful", "nervous", "tender")
NAMES = ("Nell", "Mara", "Pip", "Lina")
MAX_STEPS = 16


@dataclass
class StoryParams:
    hero: str = "Nell"
    problem: str = "missing_placecard"
    solution: str = "ask_grandmother"
    voice: str = "gentle"
    mood: str = "hopeful"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = "dining_room"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


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
    def __init__(self, p: StoryParams):
        self.params = p
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.facts: dict[str, int] = {}
        self.relations: set[tuple[str, str, str]] = set()
        self.outcome = ""

    def snapshot(self):
        return {
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "relations": sorted(self.relations),
            "outcome": self.outcome,
        }

    def record(self, kind, actor, facts=(), needs=(), **data):
        missing = [f for f in needs if f not in self.facts]
        if missing:
            raise StoryError(f"{kind} needs missing evidence: {', '.join(missing)}.")
        causes = tuple(sorted({self.facts[f] for f in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes, self.snapshot())
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id


def validate_params(p: StoryParams):
    if p.problem not in PROBLEMS:
        raise StoryError(f"Unknown dining-room problem: {p.problem!r}.")
    if p.solution not in SOLUTIONS:
        raise StoryError(f"Unknown quest solution: {p.solution!r}.")
    if p.voice not in VOICES or p.mood not in MOODS:
        raise StoryError("Unknown voice or mood.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")
    if not p.hero or not p.hero[0].isupper() or not p.hero.isalpha():
        raise StoryError("The hero name must be a simple capitalized name.")


def compatible(p: StoryParams) -> bool:
    return {
        "missing_placecard": {"ask_grandmother", "follow_clues"},
        "spilled_soup": {"share_task", "ask_grandmother"},
        "dark_room": {"share_task", "trust_memory"},
        "lost_locket": {"follow_clues", "trust_memory"},
    }[p.problem].__contains__(p.solution)


def build_world(p: StoryParams) -> World:
    validate_params(p)
    if not compatible(p):
        raise StoryError(f"The solution {p.solution!r} cannot resolve {p.problem!r}.")
    w = World(p)
    w.entities = {
        "hero": Entity("hero", p.hero, "character", memes={"care": 1, "worry": 0.5}),
        "darling": Entity("darling", "Darling", "character", memes={"hope": 1, "worry": 0.5}),
        "grandmother": Entity("grandmother", "Grandmother", "character", memes={"patience": 1}),
        "table": Entity("table", "the long dining table", "furniture", meters={"seats": 4}),
        "lamp": Entity("lamp", "the little lamp", "thing", meters={"lit": 0}),
        "soup": Entity("soup", "the tomato soup", "food", meters={"warm": 1, "spilled": 0}),
        "placecard": Entity("placecard", "the blue place card", "thing", owner="darling"),
        "locket": Entity("locket", "the silver locket", "thing", owner="grandmother"),
        "napkin": Entity("napkin", "the folded napkin", "thing", meters={"dry": 1}),
        "drawer": Entity("drawer", "the shallow drawer", "furniture"),
        "window": Entity("window", "the dining-room window", "thing"),
    }
    w.record("opening", "hero", facts=("quest_started",), problem=p.problem, solution=p.solution)
    return w


def choose_action(w: World):
    p = w.params
    if "kindness_done" in w.facts:
        return "close"
    if p.problem == "missing_placecard":
        if "clue_seen" not in w.facts and p.solution == "follow_clues":
            return "notice_blue_thread"
        if "truth_known" not in w.facts:
            return "ask_grandmother"
        return "place_card"
    if p.problem == "spilled_soup":
        if "spill_seen" not in w.facts:
            return "discover_spill"
        if p.solution == "ask_grandmother" and "advice_known" not in w.facts:
            return "ask_grandmother"
        return "clean_soup"
    if p.problem == "dark_room":
        if "dark_seen" not in w.facts:
            return "discover_darkness"
        if p.solution == "trust_memory" and "memory_shared" not in w.facts:
            return "remember_lights"
        return "light_lamp"
    if p.problem == "lost_locket":
        if "clue_seen" not in w.facts and p.solution == "follow_clues":
            return "notice_clue"
        if "truth_known" not in w.facts:
            return "ask_grandmother"
        return "find_locket"
    raise StoryError("No action can resolve this quest.")


def execute(w: World, action: str):
    p = w.params
    h, d, g = w.entities["hero"], w.entities["darling"], w.entities["grandmother"]
    if action == "notice_blue_thread":
        h.beliefs["clue"] = "drawer"
        w.record(action, "hero", facts=("clue_seen",), needs=("quest_started",))
    elif action == "ask_grandmother":
        if p.problem == "missing_placecard":
            h.beliefs["truth"] = "darling_made_it"
        elif p.problem == "spilled_soup":
            h.beliefs["advice"] = "blot_then_wipe"
        elif p.problem == "lost_locket":
            h.beliefs["truth"] = "locket_near_window"
        else:
            h.beliefs["truth"] = "grandmother_can_help"
        g.memes["relief"] = 1
        w.record(action, "hero", facts=("truth_known" if p.problem != "spilled_soup" else "advice_known",),
                 needs=("quest_started",))
    elif action == "place_card":
        if p.solution == "follow_clues" and "clue_seen" not in w.facts:
            raise StoryError("The card's hiding place must be discovered first.")
        w.entities["placecard"].location = "table"
        w.entities["placecard"].owner = "darling"
        d.beliefs["welcome"] = "felt"
        w.outcome = "darling_welcomed"
        w.record(action, "hero", facts=("kindness_done",), needs=("truth_known",) if p.solution == "ask_grandmother" else ("clue_seen",))
    elif action == "discover_spill":
        w.entities["soup"].meters["spilled"] = 1
        d.memes["worry"] = 1
        w.record(action, "darling", facts=("spill_seen",), needs=("quest_started",))
    elif action == "clean_soup":
        if p.solution == "ask_grandmother" and "advice_known" not in w.facts:
            raise StoryError("The careful cleaning plan has not been learned.")
        w.entities["soup"].meters["spilled"] = 0
        w.entities["napkin"].location = "table"
        w.outcome = "meal_saved"
        w.record(action, "hero", facts=("kindness_done",), needs=("spill_seen",))
    elif action == "discover_darkness":
        w.entities["lamp"].meters["lit"] = 0
        d.memes["worry"] = 1
        w.record(action, "darling", facts=("dark_seen",), needs=("quest_started",))
    elif action == "remember_lights":
        h.beliefs["memory"] = "lamp_switch_by_window"
        w.record(action, "hero", facts=("memory_shared",), needs=("dark_seen",))
    elif action == "light_lamp":
        if p.solution == "trust_memory" and "memory_shared" not in w.facts:
            raise StoryError("The remembered location of the switch must guide the search.")
        w.entities["lamp"].meters["lit"] = 1
        w.outcome = "room_bright"
        w.record(action, "hero", facts=("kindness_done",), needs=("dark_seen",))
    elif action == "notice_clue":
        h.beliefs["clue"] = "window"
        w.record(action, "hero", facts=("clue_seen",), needs=("quest_started",))
    elif action == "find_locket":
        if p.solution == "follow_clues" and "clue_seen" not in w.facts:
            raise StoryError("The locket's trail must be followed.")
        w.entities["locket"].location = "grandmother"
        w.outcome = "memory_returned"
        w.record(action, "hero", facts=("kindness_done",), needs=("clue_seen",) if p.solution == "follow_clues" else ("truth_known",))
    elif action == "close":
        if not w.outcome:
            raise StoryError("The story cannot close before the problem is solved.")
        w.record("close", "hero", facts=("ending",), needs=("kindness_done",))
    else:
        raise StoryError(f"Unknown action {action!r}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_STEPS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            validate_world(w)
            return w
    raise StoryError("The dining-room quest did not reach an ending.")


def validate_world(w: World):
    if not w.outcome or "ending" not in w.facts:
        raise StoryError("A complete story needs a resolved outcome.")
    if w.entities["lamp"].meters["lit"] < 0:
        raise StoryError("Lamp state is invalid.")


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines = []
        self.qa = []
        self.turns = 0

    def say(self, *choices):
        self.lines.append(self.rng.choice(choices))

    def dialogue(self, choices):
        pair = self.rng.choice(choices)
        self.lines.extend(pair)
        self.turns += len(pair)

    def run(self):
        for e in self.w.history:
            self.render(e)
        if self.turns < 2:
            raise StoryError("Every story needs a back-and-forth exchange.")
        return "\n\n".join(self.lines), self.qa

    def render(self, e: Event):
        p = self.p
        hero = p.hero
        if e.kind == "opening":
            self.say(
                f"In the dining room, {hero} was setting four spoons beside the long table when Darling tugged at her sleeve.",
                f"The dining room smelled of bread and warm tomatoes. {hero} looked up as Darling hurried to her chair.",
            )
            self.dialogue([
                (f'"{hero}, please help me decide what to do," Darling said.', '"I am here," said Darling.'),
                (f'"Darling, what is wrong?" asked {hero}.', '"I do not know what to do," Darling whispered.'),
            ])
            self.say(
                "A small quest had begun, and the grown-ups were still in the kitchen.",
                "For one quiet moment, the dining room seemed to hold its breath.",
            )
            self.qa.append(QAItem(
                "Where did the quest begin?",
                f"It began in the dining room while {hero} was helping prepare the table.",
            ))
        elif e.kind == "notice_blue_thread":
            self.say(
                f"{hero} noticed a blue thread peeking from the shallow drawer.",
                "A tiny blue thread curled beside the drawer handle, like a path left by a careful hand.",
            )
            self.dialogue([
                ('"Should we follow it?" asked Darling.', '"Yes," said the child, "but gently."'),
                ('"That looks like a clue," said Darling.', f'"Then we will not guess," {hero} replied.'),
            ])
            self.qa.append(QAItem(
                "What clue did they notice?",
                "They noticed a blue thread leading toward the shallow drawer.",
            ))
        elif e.kind == "ask_grandmother":
            if p.problem == "missing_placecard":
                self.say(
                    f"{hero} asked Grandmother whether Darling had made the blue place card.",
                    "Instead of guessing, the child carried the question to Grandmother.",
                )
                self.dialogue([
                    ('"Did I make a mistake?" Darling asked.', '"No, darling," Grandmother said. "You made a welcome."'),
                    ('"Whose card is it?" asked Darling.', '"Yours," said Grandmother. "You made it for yourself."'),
                ])
                self.qa.append(QAItem(
                    "What did Grandmother explain about the card?",
                    "She explained that Darling had made the blue card as a welcome for herself.",
                ))
            elif p.problem == "spilled_soup":
                self.say(
                    f"{hero} asked Grandmother how to save the soup-stained cloth.",
                    "The red soup spread across the cloth, and {hero} asked for a careful plan.",
                )
                self.dialogue([
                    ('"Do we scrub it?" asked Darling.', '"Not yet," said Grandmother. "Blot first."'),
                    ('"I want to fix it," said Darling.', '"Then begin softly," Grandmother replied.'),
                ])
                self.qa.append(QAItem(
                    "What cleaning advice did Grandmother give?",
                    "She said to blot the soup first and then wipe gently.",
                ))
            else:
                self.say(
                    f"{hero} asked Grandmother where the silver locket had last been seen.",
                    "When the locket was nowhere in sight, {hero} chose a question instead of a guess.",
                )
                self.dialogue([
                    ('"Was it near the window?" asked {hero}.', '"Yes," said Grandmother. "The sun touched it there."'),
                    ('"Can you remember the last place?" Darling asked.', '"By the window," Grandmother said.'),
                ])
                self.qa.append(QAItem(
                    "What did Grandmother remember?",
                    "She remembered seeing the silver locket near the dining-room window.",
                ))
        elif e.kind == "place_card":
            self.say(
                f"{hero} placed the blue card at Darling's seat. Its letters faced the empty chair like a small open door.",
                "The card returned to the table, where Darling could see that the seat had been saved with love.",
            )
            self.dialogue([
                ('"You saved my place," Darling said.', f'"I wanted you to know it," {hero} answered.'),
                ('"May I sit here?" asked Darling.', '"That is exactly what the card says," said {hero}.'),
            ])
        elif e.kind == "discover_spill":
            self.say(
                "Darling reached for the soup and tipped the bowl. Red drops hurried across the white cloth.",
                "The bowl wobbled, and tomato soup splashed onto the dining table.",
            )
            self.dialogue([
                ('"Oh no!" cried Darling.', f'"Stay with me," said {hero}.'),
                ('"I ruined dinner," Darling whispered.', '"You made a spill, not a ruin," {hero} replied.'),
            ])
        elif e.kind == "clean_soup":
            self.say(
                f"{hero} blotted the soup before wiping the cloth. The red mark faded, and Darling helped hold the napkin flat.",
                "Together they cleaned the table gently. The dining room smelled of bread again instead of worry.",
            )
            self.dialogue([
                ('"I did not make it worse," Darling said.', '"You helped make it better," {hero} replied.'),
                ('"Can dinner still happen?" asked Darling.', '"It can happen because we cared for the table," said {hero}.'),
            ])
        elif e.kind == "discover_darkness":
            self.say(
                "A cloud covered the evening sun, and the dining room slipped into blue shadow.",
                "The first dinner bell rang just as the lamp went dark.",
            )
            self.dialogue([
                ('"I cannot see my chair," Darling said.', '"We will find the light together," {hero} answered.'),
                ('"The room changed," whispered Darling.', '"Only for a moment," said {hero}.'),
            ])
        elif e.kind == "remember_lights":
            self.say(
                f"{hero} remembered that the lamp switch waited beside the window, beneath the little brass hook.",
                "The darkness made the room unfamiliar, but {hero} remembered the switch by the window.",
            )
            self.dialogue([
                ('"How do you know?" asked Darling.', '"I noticed it yesterday," said {hero}.'),
                ('"Can memory be a lantern?" Darling asked.', '"Sometimes it shows where to reach," {hero} replied.'),
            ])
        elif e.kind == "light_lamp":
            self.say(
                f"{hero} found the switch and lit the lamp. Gold light spilled across the table and Darling's worried face.",
                "The lamp blinked awake, turning the spoons into little moons.",
            )
            self.dialogue([
                ('"You found it!" said Darling.', '"You remembered where to look," {hero} answered.'),
                ('"The room feels warm again," Darling said.', '"Then let us set the table," said {hero}.'),
            ])
        elif e.kind == "notice_clue":
            self.say(
                "A faint silver glimmer shone beside the dining-room window.",
                f"{hero} followed a thin trail of moonlight toward the window.",
            )
            self.dialogue([
                ('"Is that the locket?" asked Darling.', '"It may be," said {hero}. "Let us look carefully."'),
                ('"I see something silver," said Darling.', '"Then we have a place to begin," {hero} replied.'),
            ])
        elif e.kind == "find_locket":
            self.say(
                "The silver locket rested beneath the curtain hem. {hero} lifted it and carried it back to Grandmother.",
                "They found the locket by the window, where the last sunbeam had hidden its shine.",
            )
            self.dialogue([
                ('"You found my memory," Grandmother said.', '"It was waiting for us," {hero} replied.'),
                ('"May I hold it?" asked Darling.', '"After Grandmother does," said {hero}.'),
            ])
        elif e.kind == "close":
            self.say(
                f"At last, the dining room was ready. {hero} and Darling sat beside one another while Grandmother brought in the bread.",
                "The quest ended with warm plates, close chairs, and no one left alone with a worry.",
            )
            self.dialogue([
                ('"You helped me decide," Darling said.', f'"You helped me notice what mattered," {hero} replied.'),
                ('"What made you brave?" asked Darling.', '"Knowing we could ask, remember, and try again," said {hero}.'),
            ])
            self.say(
                "Darling reached across the table, and the little dining room grew bright with belonging.",
                "The table held its meal, its stories, and two hands clasped gently beneath the lamp.",
            )
            self.qa.append(QAItem(
                "How did the quest end?",
                "The dining room became ready for dinner, and Darling felt welcomed and safe beside the others.",
            ))


ASP_RULES = """
problem(missing_placecard;spilled_soup;dark_room;lost_locket).
solution(ask_grandmother;follow_clues;share_task;trust_memory).
compatible(missing_placecard,ask_grandmother).
compatible(missing_placecard,follow_clues).
compatible(spilled_soup,share_task).
compatible(spilled_soup,ask_grandmother).
compatible(dark_room,share_task).
compatible(dark_room,trust_memory).
compatible(lost_locket,follow_clues).
compatible(lost_locket,trust_memory).
#show compatible/2.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [fact("problem", p) for p in PROBLEMS]
        + [fact("solution", s) for s in SOLUTIONS]
        + [fact("compatible", p, s) for p in PROBLEMS for s in SOLUTIONS if compatible(StoryParams(problem=p, solution=s))]
    )


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).run()
    return StorySample(
        params=params,
        story=story,
        prompts=[f"Write a heartwarming dining-room quest in which {params.hero} helps Darling decide what to do."],
        story_qa=qa,
        world_qa=[
            QAItem("Where is the story set?", "It is set in a dining room."),
            QAItem("What makes it a quest?", "The characters follow a small problem toward a caring, practical resolution."),
        ],
        world=world,
    )


def verify():
    from asp import atoms, one_model
    expected = {(p, s) for p in PROBLEMS for s in SOLUTIONS if compatible(StoryParams(problem=p, solution=s))}
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about compatible quests.")
    count = 0
    for problem, solution in expected:
        p = StoryParams(problem=problem, solution=solution)
        sample = generate(p)
        if "darling" not in sample.story.lower() or "dining" not in sample.story.lower():
            raise StoryError("Generated prose lost a required story fact.")
        count += 1
    print(f"OK: {count} compatible quests; ASP parity; dialogue and endings verified.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    parser.add_argument("--mood", choices=MOODS, default="hopeful")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
        mood=args.mood,
    )
    registries = {
        "hero": NAMES,
        "problem": PROBLEMS,
    }
    for name, choices in registries.items():
        chosen = getattr(args, name)
        setattr(p, name, chosen if chosen is not None else (rng.choice(choices) if sample else getattr(p, name)))
    if args.solution is not None:
        p.solution = args.solution
    else:
        p.solution = rng.choice(tuple({
            "missing_placecard": ("ask_grandmother", "follow_clues"),
            "spilled_soup": ("share_task", "ask_grandmother"),
            "dark_room": ("share_task", "trust_memory"),
            "lost_locket": ("follow_clues", "trust_memory"),
        }[p.problem])) if sample else {
            "missing_placecard": "ask_grandmother",
            "spilled_soup": "share_task",
            "dark_room": "trust_memory",
            "lost_locket": "follow_clues",
        }[p.problem]
    validate_params(p)
    return p


def emit(sample, trace=False, qa=False, header=""):
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
            "history": [asdict(e) for e in sample.world.history],
        }, indent=2))


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
            params = [
                StoryParams(problem=problem, solution=solution, world_seed=args.world_seed + i,
                            prose_seed=args.prose_seed + i, voice=args.voice, mood=args.mood)
                for i, (problem, solution) in enumerate(
                    (p, s) for p in PROBLEMS for s in SOLUTIONS if compatible(StoryParams(problem=p, solution=s))
                )
            ]
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, p in enumerate(params):
                emit(generate(p), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
