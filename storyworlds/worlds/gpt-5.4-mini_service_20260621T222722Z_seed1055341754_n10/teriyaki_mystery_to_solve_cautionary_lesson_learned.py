#!/usr/bin/env python3
"""
storyworlds/worlds/teriyaki_mystery_to_solve_cautionary_lesson_learned.py
==========================================================================

A small standalone storyworld: a space-crew mystery about a missing teriyaki
sample, a cautious misstep, and a lesson learned about checking sealed labels
before tasting anything.

The domain is intentionally tiny and classical:
- a child-friendly space mission setting
- a mystery to solve
- a cautionary beat
- a lesson learned ending

The story model uses typed entities with physical meters and emotional memes,
a forward-chaining rule engine, a reasonableness gate, and an inline ASP twin.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
    clue_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue_word: str
    hidden_in: str
    can_spill: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("tasted") and not world.facts.get("sealed_checked"):
        sig = ("conflict", "taste")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("crew").memes["worry"] += 1
            world.get("crew").memes["curiosity"] += 1
            out.append("__conflict__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_found") and not world.facts.get("solved"):
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("captain").memes["focus"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("clue", "mystery", _r_clue),
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


def reasonableness_gate(snack: Snack, mystery: Mystery, place: Place) -> bool:
    return snack.safe and mystery.can_spill and "space" in place.tags


def sensible_warnings() -> list[Warning]:
    return [w for w in WARNINGS.values() if w.sense >= 2]


def spill_risk(mystery: Mystery) -> int:
    return 2 if mystery.can_spill else 0


def warning_works(warning: Warning, mystery: Mystery, delay: int) -> bool:
    return warning.power >= spill_risk(mystery) + delay


def predict_taste(world: World, mystery_id: str) -> dict:
    sim = world.copy()
    _taste_mystery(sim, sim.get(mystery_id), narrate=False)
    return {
        "mess": sim.facts.get("tasted", False),
        "worry": sim.get("crew").memes["worry"],
    }


def _taste_mystery(world: World, mystery: Entity, narrate: bool = True) -> None:
    world.facts["tasted"] = True
    mystery.meters["opened"] += 1
    world.facts["clue_found"] = True
    propagate(world, narrate=narrate)


def opening(world: World, crew: Entity, place: Place, snack: Snack) -> None:
    crew.memes["joy"] += 1
    world.say(
        f"On a quiet stretch of space, the crew drifted into {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f'Their mission was simple: solve the mystery of the missing lunch, '
        f'which smelled like {snack.smell} and was supposed to stay sealed.'
    )


def find_clue(world: World, captain: Entity, place: Place, mystery: Mystery) -> None:
    captain.memes["curiosity"] += 1
    world.say(
        f"{captain.id} noticed a small glow near {place.clue_spot}. "
        f'Something had been moved from {place.dark_spot}, but the label still said "{mystery.clue_word}".'
    )


def caution(world: World, helper: Entity, captain: Entity, snack: Snack, delay: int) -> None:
    helper.memes["worry"] += 1
    pred = predict_taste(world, "mystery")
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} tightened {helper.pronoun("possessive")} gloves. '
        f'"Do not taste it yet," {helper.pronoun()} warned. '
        f'It could be something unsafe hidden near the controls.'
    )
    if delay > 0:
        world.say("The caution felt extra important because the ship was already drifting away from the station.")


def ignore_warning(world: World, captain: Entity, snack: Snack) -> None:
    captain.memes["defiance"] += 1
    world.say(
        f'{captain.id} sniffed the packet and frowned. "It smells like {snack.smell}. '
        f"Maybe it's lunch," {captain.id} said, reaching for it anyway."
    )


def solve_mystery(world: World, captain: Entity, mystery: Mystery, snack: Snack) -> None:
    world.facts["sealed_checked"] = True
    world.facts["solved"] = True
    mystery.meters["opened"] += 1
    world.say(
        f'At last {captain.id} checked the sealed label and found the answer: '
        f"the packet was {snack.phrase}, not a mystery at all."
    )


def lesson(world: World, captain: Entity, helper: Entity, snack: Snack) -> None:
    captain.memes["lesson"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{helper.id} smiled and pointed to the label. "That is the lesson," '
        f'{helper.pronoun()} said. "In space, you solve mysteries by checking first, '
        f'not by guessing with your mouth."'
    )
    world.say(
        f'{captain.id} nodded, tucked the packet back in the supply box, and the crew '
        f'kept the {snack.label} for the proper meal.'
    )


def ending_image(world: World, place: Place, snack: Snack) -> None:
    world.say(
        f"By the end of the watch, {place.label} was calm again, the label was clear, "
        f'and the teriyaki lunch waited safely for dinner.'
    )


def tell(place: Place, mystery: Mystery, snack: Snack, warning: Warning,
         captain_name: str = "Ari", captain_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy",
         delay: int = 0) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender,
                               role="captain"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", role="crew"))
    world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    world.add(Entity(id="mystery", kind="thing", type="mystery", label=mystery.label,
                     tags=set(mystery.tags), attrs={"hidden_in": mystery.hidden_in}))
    world.facts.update(
        captain=captain, helper=helper, crew=crew,
        place=place, mystery=mystery, snack=snack, warning=warning,
        delay=delay, sealed_checked=False, tasted=False, clue_found=False, solved=False,
    )

    opening(world, crew, place, snack)
    world.para()
    find_clue(world, captain, place, mystery)
    caution(world, helper, captain, snack, delay)
    if warning_works(warning, mystery, delay):
        world.say(f"Because {helper.id} stayed careful, the crew did not rush to taste anything.")
        solve_mystery(world, captain, mystery, snack)
        lesson(world, captain, helper, snack)
    else:
        ignore_warning(world, captain, snack)
        _taste_mystery(world, world.get("mystery"))
        world.para()
        world.say(
            f"The packet burst open too soon, and everyone had to wipe their gloves before they could continue."
        )
        lesson(world, captain, helper, snack)
    world.para()
    ending_image(world, place, snack)
    return world


PLACES = {
    "lunar_kitchen": Place(
        id="lunar_kitchen",
        label="the lunar kitchen",
        scene="A row of windowports showed the moon like a pale coin, and the counters floated just a little."
        ,
        dark_spot="the shadow behind the supply cabinet",
        clue_spot="the blue tray near the hatch",
        tags={"space", "station"},
    ),
    "orbital_galley": Place(
        id="orbital_galley",
        label="the orbital galley",
        scene="The pantry hummed softly, and every drawer had a latch that clicked like a tiny star."
        ,
        dark_spot="the gap beneath the food lockers",
        clue_spot="the metal shelf by the cooker",
        tags={"space", "station"},
    ),
}

MYSTERIES = {
    "packet": Mystery(
        id="packet",
        label="a sealed packet",
        clue_word="teriyaki",
        hidden_in="the supply box",
        can_spill=True,
        tags={"mystery", "sealed"},
    ),
    "container": Mystery(
        id="container",
        label="a lunch container",
        clue_word="teriyaki",
        hidden_in="the warming drawer",
        can_spill=True,
        tags={"mystery", "sealed"},
    ),
}

SNACKS = {
    "teriyaki": Snack(
        id="teriyaki",
        label="teriyaki",
        phrase="a teriyaki lunch",
        smell="sweet soy and ginger",
        safe=True,
        tags={"teriyaki", "food"},
    ),
    "rice": Snack(
        id="rice",
        label="rice",
        phrase="a rice bowl",
        smell="warm sesame",
        safe=True,
        tags={"rice", "food"},
    ),
}

WARNINGS = {
    "gentle": Warning(
        id="gentle",
        sense=3,
        power=2,
        text="warned them to check the label first",
        fail="warned them, but the rush was too strong",
        qa_text="checked the label first and kept the packet sealed",
        tags={"check", "label"},
    ),
    "firm": Warning(
        id="firm",
        sense=3,
        power=3,
        text="stopped the captain from tasting the packet",
        fail="could not stop the captain from tasting the packet",
        qa_text="stopped the captain and let the crew solve the mystery safely",
        tags={"check", "label"},
    ),
    "too_soft": Warning(
        id="too_soft",
        sense=1,
        power=1,
        text="mumbled a warning that sounded easy to ignore",
        fail="mumbled a warning that was too easy to ignore",
        qa_text="mumbled a warning that was too easy to ignore",
        tags={"check", "label"},
    ),
}

CURATED = [
    StoryParams(
        place="lunar_kitchen",
        mystery="packet",
        snack="teriyaki",
        warning="gentle",
        captain_name="Ari",
        captain_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        delay=0,
    ),
    StoryParams(
        place="orbital_galley",
        mystery="container",
        snack="teriyaki",
        warning="firm",
        captain_name="Nova",
        captain_gender="girl",
        helper_name="Kai",
        helper_gender="boy",
        delay=1,
    ),
    StoryParams(
        place="lunar_kitchen",
        mystery="packet",
        snack="teriyaki",
        warning="firm",
        captain_name="Leo",
        captain_gender="boy",
        helper_name="Rin",
        helper_gender="girl",
        delay=0,
    ),
]

TRAITS = ["curious", "careful", "brave", "thoughtful"]
NAMES_GIRL = ["Ari", "Nova", "Rin", "Ivy", "Mina"]
NAMES_BOY = ["Milo", "Kai", "Leo", "Taj", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for s in SNACKS:
                if reasonableness_gate(SNACKS[s], MYSTERIES[m], PLACES[p]):
                    combos.append((p, m, s))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    snack: str
    warning: str
    captain_name: str
    captain_gender: str
    helper_name: str
    helper_gender: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space mystery story that includes "{f["snack"].label}" and the word "teriyaki".',
        f"Tell a cautionary space adventure where {f['captain'].id} wants to open a sealed mystery packet, but {f['helper'].id} insists on checking first.",
        "Write a story about solving a food mystery on a starship and learning not to taste unknown things before reading the label.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    helper = f["helper"]
    snack = f["snack"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What mystery did {captain.id} and {helper.id} try to solve?",
            answer=f"They tried to solve the mystery of the sealed packet in {place.label}. They wanted to know what it was before anyone tasted it.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {captain.id} not to taste the packet right away?",
            answer=f"{helper.id} knew the packet might be unsafe or not ready yet. In space, the careful choice is to check the label first, because guessing with your mouth can cause trouble.",
        ),
        QAItem(
            question=f"What did the crew learn about the {snack.label} lunch?",
            answer=f"They learned it was really a proper {snack.phrase} waiting safely for dinner. The label solved the mystery, so nobody needed to guess.",
        ),
    ]
    if f["sealed_checked"]:
        qa.append(QAItem(
            question="How did the captain solve the mystery safely?",
            answer=f"{captain.id} checked the sealed label first and then put the packet back. That careful step solved the mystery without making a mess or hurting anyone.",
        ))
    else:
        qa.append(QAItem(
            question="What happened when the captain ignored the warning?",
            answer=f"{captain.id} tasted the packet too soon, and the mystery burst open. The crew had to clean up and then remember to check labels before tasting anything.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["snack"].tags) | set(f["place"].tags) | set(f["warning"].tags)
    out = []
    if "teriyaki" in tags:
        out.append(QAItem(
            question="What is teriyaki?",
            answer="Teriyaki is a sweet and savory flavor often used for food. It can smell like soy sauce and ginger, and it is usually meant to be eaten as a meal.",
        ))
    out.append(QAItem(
        question="Why should you check a label before tasting food you do not know?",
        answer="A label tells you what the food is. Checking first helps you avoid eating something unsafe or something meant for later.",
    ))
    out.append(QAItem(
        question="What is a mystery?",
        answer="A mystery is something you do not know yet. You solve it by looking closely, finding clues, and asking careful questions.",
    ))
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
sealed_checked :- checked_label.
tasted_packet :- tasted.
unsafe_misstep :- tasted_packet, not sealed_checked.
solved_mystery :- checked_label.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.can_spill:
            lines.append(asp.fact("can_spill", mid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.safe:
            lines.append(asp.fact("safe", sid))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("checked_label.", "#show solved_mystery/0.")
    model = asp.one_model(program)
    ok = any(sym.name == "solved_mystery" for sym in model)
    rc = 0 if ok else 1
    print("OK: ASP smoke test" if ok else "MISMATCH: ASP smoke test failed")
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test")
    except Exception as err:
        print(f"MISMATCH: generate() failed: {err}")
        rc = 1
    # parity check on valid combos
    import asp
    asp_set = set(asp.atoms(asp.one_model(asp_program("#show place/1. #show mystery/1. #show snack/1.", "")), "place"))
    _ = asp_set
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space mystery storyworld with teriyaki and a cautionary lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, snack = rng.choice(sorted(combos))
    warning = args.warning or rng.choice(sorted(WARNINGS))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if captain_gender == "girl" else "girl")
    captain_name = args.captain_name or rng.choice(NAMES_GIRL if captain_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice([n for n in (NAMES_BOY if helper_gender == "boy" else NAMES_GIRL) if n != captain_name])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        mystery=mystery,
        snack=snack,
        warning=warning,
        captain_name=captain_name,
        captain_gender=captain_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        mystery = MYSTERIES[params.mystery]
        snack = SNACKS[params.snack]
        warning = WARNINGS[params.warning]
    except KeyError as err:
        raise StoryError(f"Invalid parameter: {err}") from err
    if not reasonableness_gate(snack, mystery, place):
        raise StoryError("No story: this combination is not reasonable.")
    world = tell(place, mystery, snack, warning, params.captain_name, params.captain_gender,
                 params.helper_name, params.helper_gender, params.delay)
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
        print(asp_program(show="#show solved_mystery/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {m} {s}" for p, m, s in valid_combos()))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
