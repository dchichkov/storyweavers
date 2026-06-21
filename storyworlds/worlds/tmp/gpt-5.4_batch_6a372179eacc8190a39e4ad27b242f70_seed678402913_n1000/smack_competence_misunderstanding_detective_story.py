#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py
===============================================================================

A standalone storyworld for a small child-facing detective tale built around a
misunderstanding. A young "detective" hears a suspicious smack, notices a clue,
and jumps to the wrong conclusion about a helpful person. The case resolves when
careful observation beats quick guessing.

Run it
------
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py --case bakery
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py --reveal check_high_shelf
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/smack_competence_misunderstanding_detective_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
_THIS = os.path.abspath(__file__)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS)))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian", "baker", "artist"}
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
class Case:
    id: str
    place: str
    item_label: str
    item_phrase: str
    item_the: str
    suspect_job: str
    suspect_type: str
    suspect_task: str
    material: str
    clue_text: str
    smack_text: str
    sound_source: str
    safe_spot: str
    safe_tag: str
    moved_reason: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RevealMethod:
    id: str
    label: str
    prompt_text: str
    action_text: str
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_form_theory(world: World) -> list[str]:
    hero = world.get("hero")
    suspect = world.get("suspect")
    if not world.facts.get("heard_smack"):
        return []
    if not world.facts.get("saw_clue"):
        return []
    sig = ("theory",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    hero.memes["certainty"] += 1
    suspect.memes["suspected"] += 1
    world.facts["misunderstanding"] = True
    return ["__theory__"]


def _r_accusation_hurts(world: World) -> list[str]:
    hero = world.get("hero")
    suspect = world.get("suspect")
    if hero.memes["accused"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    hero.memes["tension"] += 1
    return ["__hurt__"]


def _r_found_item_relief(world: World) -> list[str]:
    if not world.facts.get("item_found"):
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    suspect = world.get("suspect")
    hero.memes["relief"] += 1
    hero.memes["respect"] += 1
    helper.memes["pride"] += 1
    suspect.memes["forgiven"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="form_theory", tag="social", apply=_r_form_theory),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="found_item_relief", tag="social", apply=_r_found_item_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reveal_works(case: Case, method: RevealMethod) -> bool:
    return case.safe_tag in method.works_for


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cid, case in CASES.items():
        for rid, method in REVEALS.items():
            if reveal_works(case, method):
                combos.append((cid, rid))
    return combos


def predict_truth(world: World, case: Case, method: RevealMethod) -> dict:
    sim = world.copy()
    sim.facts["item_found"] = reveal_works(case, method)
    propagate(sim, narrate=False)
    return {
        "found": sim.facts["item_found"],
        "misunderstanding": sim.facts.get("misunderstanding", False),
    }


def introduce(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} opened their little detective office in {case.place}."
    )
    world.say(
        f"{hero.id} wore a paper hat with a penciled badge on it and carried {world.get('item').phrase}."
    )
    world.say(
        f'"A real detective needs sharp eyes and gentle manners," {helper.id} said, and {hero.id} nodded as if a great case might begin any minute.'
    )


def set_case(world: World, hero: Entity, case: Case) -> None:
    item = world.get("item")
    item.attrs["visible"] = True
    hero.memes["joy"] += 1
    world.say(
        f"Sure enough, a mystery came at once: when {hero.id} turned back from the window, {case.item_the} was gone from the small table."
    )
    world.say(
        f"Only a tiny clue remained there: {case.clue_text}."
    )


def hear_sound(world: World, hero: Entity, case: Case) -> None:
    world.facts["heard_smack"] = True
    world.facts["saw_clue"] = True
    world.say(
        f"Then {hero.id} heard {case.smack_text}. The sound made the whole room feel secret and important."
    )
    propagate(world, narrate=False)


def suspect_wrongly(world: World, hero: Entity, helper: Entity, suspect: Entity, case: Case) -> None:
    hero.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} gasped. "{suspect.id} must have taken it!" {hero.pronoun()} whispered. "The clue is {case.material}, and {suspect.id} has been {case.suspect_task}."'
    )
    if helper.memes["patience"] >= THRESHOLD:
        world.say(
            f'{helper.id} frowned a little. "Maybe," {helper.pronoun()} said, "but detectives should ask before they decide."'
        )
    world.say(
        f"Still, the idea felt so neat that {hero.id} held onto it."
    )


def question(world: World, hero: Entity, suspect: Entity, case: Case) -> None:
    world.say(
        f'{hero.id} marched over to {suspect.id}. "Did you take {case.item_the}?" {hero.pronoun()} asked.'
    )
    world.say(
        f"{suspect.id} blinked, surprised but calm."
    )


def explain_truth(world: World, suspect: Entity, case: Case) -> None:
    suspect.memes["competence"] += 1
    world.say(
        f'"No," {suspect.id} said kindly. "{case.sound_source}. I moved {case.item_the} {case.moved_reason}."'
    )
    world.say(
        f'{suspect.pronoun().capitalize()} brushed {case.material} from {suspect.pronoun("possessive")} hands and added, "A clue is not the same as proof."'
    )


def reveal_item(world: World, hero: Entity, helper: Entity, case: Case, method: RevealMethod) -> None:
    pred = predict_truth(world, case, method)
    world.facts["predicted_found"] = pred["found"]
    world.say(method.prompt_text.format(hero=hero.id, helper=helper.id))
    world.say(method.action_text.format(
        hero=hero.id,
        helper=helper.id,
        item_the=case.item_the,
        safe_spot=case.safe_spot,
    ))
    world.facts["item_found"] = True
    world.get("item").attrs["visible"] = True
    propagate(world, narrate=False)


def apology_and_lesson(world: World, hero: Entity, helper: Entity, suspect: Entity, case: Case) -> None:
    hero.memes["apology"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'{hero.id} felt {hero.pronoun("possessive")} cheeks grow warm. "I am sorry," {hero.pronoun()} said. "I heard a smack, saw {case.material}, and guessed too fast."'
    )
    world.say(
        f'{suspect.id} smiled. "That happens. Real detective competence means looking twice and asking kindly."'
    )
    world.say(
        f'{helper.id} opened the notebook and wrote the new rule of the case: "Look again before you accuse."'
    )


def ending(world: World, hero: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} clipped the found treasure safely back in place and looked around with much quieter eyes."
    )
    world.say(case.ending_image)


def tell(case: Case, method: RevealMethod, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, adult_type: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=["curious", "dramatic"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        traits=["steady", "kind"],
    ))
    helper.memes["patience"] = 1.0
    suspect = world.add(Entity(
        id={"baker": "Mara", "librarian": "Nina", "artist": "Tess"}[case.suspect_type],
        kind="character",
        type=case.suspect_type,
        role="suspect",
        label=case.suspect_job,
        traits=["competent", "busy"],
        tags=set(case.tags),
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="object",
        label=case.item_label,
        phrase=case.item_phrase,
        role="missing_item",
        tags=set(case.tags),
    ))

    introduce(world, hero, helper, case)
    set_case(world, hero, case)

    world.para()
    hear_sound(world, hero, case)
    suspect_wrongly(world, hero, helper, suspect, case)
    question(world, hero, suspect, case)

    world.para()
    explain_truth(world, suspect, case)
    reveal_item(world, hero, helper, case, method)

    world.para()
    apology_and_lesson(world, hero, helper, suspect, case)
    ending(world, hero, case)

    world.facts.update(
        case=case,
        method=method,
        hero=hero,
        helper=helper,
        suspect=suspect,
        adult=adult,
        item=item,
        misunderstanding=world.facts.get("misunderstanding", False),
        resolved=world.facts.get("item_found", False),
    )
    return world


@dataclass
class StoryParams:
    case: str
    reveal: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    adult: str
    seed: Optional[int] = None


CASES = {
    "bakery": Case(
        id="bakery",
        place="the warm bakery kitchen",
        item_label="detective badge",
        item_phrase="a shiny tin detective badge",
        item_the="the detective badge",
        suspect_job="the baker",
        suspect_type="baker",
        suspect_task="patting bread dough flat",
        material="flour",
        clue_text="a little crescent of flour beside the empty spot",
        smack_text='a soft smack from the bread table in the next room',
        sound_source="The dough had landed on the board with a soft smack",
        safe_spot="on the top shelf by the clean mixing bowls",
        safe_tag="high_shelf",
        moved_reason="to the top shelf so it would not get dusted with flour",
        ending_image="Soon the badge shone above a page in the notebook that said, in large careful letters, DETECTIVES ASK FIRST.",
        tags={"bakery", "flour", "bread"},
    ),
    "library": Case(
        id="library",
        place="the quiet back corner of the library",
        item_label="clue card",
        item_phrase="a gold-bordered clue card",
        item_the="the clue card",
        suspect_job="the librarian",
        suspect_type="librarian",
        suspect_task="stamping return slips",
        material="blue ink",
        clue_text="a bright thumb mark of blue ink beside the empty spot",
        smack_text='a neat smack from the checkout desk',
        sound_source="The date stamp had hit a return slip with a tidy smack",
        safe_spot="inside the book cart's top tray",
        safe_tag="rolling_cart",
        moved_reason="into the book cart's top tray so it would not slide onto the floor",
        ending_image="The clue card rode safely home in the notebook pocket, and the case file ended with a blue-ink star beside the words BE FAIR TO YOUR CLUES.",
        tags={"library", "ink", "books"},
    ),
    "art_room": Case(
        id="art_room",
        place="the sunny art room",
        item_label="junior detective ribbon",
        item_phrase="a striped junior detective ribbon",
        item_the="the junior detective ribbon",
        suspect_job="the art teacher",
        suspect_type="artist",
        suspect_task="slapping clay onto a board",
        material="gray clay",
        clue_text="a thumb-smudge of gray clay near the empty spot",
        smack_text='a wet smack from the pottery table',
        sound_source="A slab of clay had landed on the board with a wet smack",
        safe_spot="on the drying rack above the sink",
        safe_tag="drying_rack",
        moved_reason="on the drying rack so it would stay clean and dry",
        ending_image="The ribbon fluttered above the sink while the notebook closed on the most important clue of all: KINDNESS HELPS A CASE.",
        tags={"art", "clay", "studio"},
    ),
}

REVEALS = {
    "check_high_shelf": RevealMethod(
        id="check_high_shelf",
        label="check the high shelf",
        prompt_text='"Let us look where careful hands would put something safe," {helper} said.',
        action_text='{hero} stood on tiptoe, and {helper} pointed up. There was {item_the}, resting {safe_spot}.',
        works_for={"high_shelf"},
        tags={"look_up"},
    ),
    "check_book_cart": RevealMethod(
        id="check_book_cart",
        label="check the book cart",
        prompt_text='"Maybe the clue wants us to look where work is being done," {helper} said.',
        action_text='{hero} peered into the cart. There was {item_the}, tucked {safe_spot}.',
        works_for={"rolling_cart"},
        tags={"cart"},
    ),
    "check_drying_rack": RevealMethod(
        id="check_drying_rack",
        label="check the drying rack",
        prompt_text='"If someone wanted it clean, where would they set it?" {helper} asked.',
        action_text='{hero} looked above the sink. There was {item_the}, waiting {safe_spot}.',
        works_for={"drying_rack"},
        tags={"look_up"},
    ),
    "under_rug": RevealMethod(
        id="under_rug",
        label="look under the rug",
        prompt_text='"Maybe mysteries always hide under rugs," {hero} said hopefully.',
        action_text='{hero} lifted the rug, but there was only dust and no sign of {item_the}.',
        works_for=set(),
        tags={"bad_guess"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo"]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "smack" and the word "competence".',
        f"Tell a gentle mystery where {hero.id} hears a suspicious smack, sees a clue made of {case.material}, and wrongly suspects a helpful grown-up before learning the truth.",
        f"Write a child-facing detective story with a misunderstanding, a missing {case.item_label}, and an ending where {helper.id} helps the detective learn to ask before accusing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    method = world.facts["method"]
    out = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little detective, and {helper.id}, the calm helper beside {hero.pronoun('object')}. It is also about {suspect.id}, the busy {case.suspect_job} who was misunderstood."
        ),
        (
            f"What mystery started the case?",
            f"{case.item_the.capitalize()} went missing from the table, and only {case.clue_text} was left behind. That small clue made the case feel bigger than it really was."
        ),
        (
            f"Why did {hero.id} suspect {suspect.id}?",
            f"{hero.id} heard {case.smack_text} and saw {case.material} at the empty spot. Because {suspect.id} had been {case.suspect_task}, the clue seemed to point straight at {suspect.pronoun('object')}."
        ),
        (
            "What was the misunderstanding?",
            f"The misunderstanding was thinking the clue proved stealing, when it only showed who had been working nearby. The smack and the messy mark were real, but the guess about what they meant was wrong."
        ),
        (
            f"Where was the missing thing really?",
            f"It was {case.safe_spot}. {suspect.id} had moved it there {case.moved_reason.removeprefix('to ').removeprefix('into ').removeprefix('on ')}."
        ),
        (
            f"How was the mystery solved?",
            f"{helper.id} suggested they {method.label}, and that revealed the truth. The case was solved by looking carefully in the safe place instead of holding onto the first guess."
        ),
        (
            "What did the detective learn?",
            f"{hero.id} learned that real detective competence means asking kindly and checking clues twice. A clue can begin a case, but it should not end the thinking."
        ),
    ]
    return out


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to solve a mystery. Good detectives are careful, patient, and fair."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. A clue can help, but it does not always tell the whole story by itself."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what something means, but they are wrong. Talking and checking can clear it up."
        )
    ],
    "competence": [
        (
            "What does competence mean?",
            "Competence means being good at doing something because you use care and skill. In a mystery, competence means noticing details and thinking before you blame someone."
        )
    ],
    "flour": [
        (
            "Why does flour get on things in a bakery?",
            "Flour is light and powdery, so it can puff onto tables and hands when people bake. That is why flour can leave little white clues."
        )
    ],
    "ink": [
        (
            "Why can ink make thumb marks?",
            "Ink is wet when it first touches paper or skin, so it can leave a mark behind. That is why stamp pads can make bright clues."
        )
    ],
    "clay": [
        (
            "Why does clay leave smudges?",
            "Clay is soft and a little sticky, so it can smear onto fingers and tables. A clay smudge can show where someone was working."
        )
    ],
    "bread": [
        (
            "Why might dough make a smack sound?",
            "Soft dough can make a little smack when it lands on a board or table. The sound is harmless, but it can surprise you."
        )
    ],
    "stamp": [
        (
            "Why does a stamp make a smack sound?",
            "A hand stamp can make a quick smack when it presses paper. It is just the tool doing its job."
        )
    ],
    "drying_rack": [
        (
            "What is a drying rack for?",
            "A drying rack is a place where wet art can sit safely until it dries. People use it to keep things clean and out of the way."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "clue",
    "misunderstanding",
    "competence",
    "flour",
    "ink",
    "clay",
    "bread",
    "stamp",
    "drying_rack",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case"]
    tags = {"detective", "clue", "misunderstanding", "competence"}
    if case.id == "bakery":
        tags |= {"flour", "bread"}
    elif case.id == "library":
        tags |= {"ink", "stamp"}
    elif case.id == "art_room":
        tags |= {"clay", "drying_rack"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(k for k, v in world.facts.items() if v)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="bakery",
        reveal="check_high_shelf",
        hero="Lily",
        hero_type="girl",
        helper="Ben",
        helper_type="boy",
        adult="mother",
    ),
    StoryParams(
        case="library",
        reveal="check_book_cart",
        hero="Max",
        hero_type="boy",
        helper="Mia",
        helper_type="girl",
        adult="father",
    ),
    StoryParams(
        case="art_room",
        reveal="check_drying_rack",
        hero="Zoe",
        hero_type="girl",
        helper="Theo",
        helper_type="boy",
        adult="mother",
    ),
]


def explain_rejection(case: Case, method: RevealMethod) -> str:
    return (
        f"(No story: {method.label} does not reasonably uncover an item hidden {case.safe_spot}. "
        f"Pick a reveal that matches the safe place for this case.)"
    )


ASP_RULES = r"""
works(C, R) :- case(C), reveal(R), safe_tag(C, T), reveal_for(R, T).
valid(C, R) :- works(C, R).

resolved(C, R) :- valid(C, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("safe_tag", cid, case.safe_tag))
    for rid, method in REVEALS.items():
        lines.append(asp.fact("reveal", rid))
        for tag in sorted(method.works_for):
            lines.append(asp.fact("reveal_for", rid, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_resolved(case_id: str, reveal_id: str) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_case", case_id),
        asp.fact("chosen_reveal", reveal_id),
        "chosen_resolved :- chosen_case(C), chosen_reveal(R), resolved(C, R).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_resolved/0."))
    return bool(asp.atoms(model, "chosen_resolved"))


def outcome_of(params: StoryParams) -> str:
    case = CASES[params.case]
    method = REVEALS[params.reveal]
    return "resolved" if reveal_works(case, method) else "unresolved"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    for sample_params in CURATED:
        py = outcome_of(sample_params) == "resolved"
        cl = asp_resolved(sample_params.case, sample_params.reveal)
        if py != cl:
            rc = 1
            print(f"MISMATCH in resolved outcome for {sample_params.case}/{sample_params.reveal}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective hears a suspicious smack, misunderstands a clue, and learns careful competence."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible case/reveal pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.reveal:
        case = CASES[args.case]
        method = REVEALS[args.reveal]
        if not reveal_works(case, method):
            raise StoryError(explain_rejection(case, method))

    combos = [
        combo for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.reveal is None or combo[1] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, reveal_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_type)
    helper = args.helper or _pick_name(rng, helper_type, avoid=hero)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        case=case_id,
        reveal=reveal_id,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Invalid case: {params.case})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Invalid reveal: {params.reveal})")
    case = CASES[params.case]
    method = REVEALS[params.reveal]
    if not reveal_works(case, method):
        raise StoryError(explain_rejection(case, method))

    world = tell(
        case=case,
        method=method,
        hero_name=params.hero,
        hero_type=params.hero_type,
        helper_name=params.helper,
        helper_type=params.helper_type,
        adult_type=params.adult,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, reveal) pairs:\n")
        for case_id, reveal_id in combos:
            print(f"  {case_id:9} {reveal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.case}: {p.hero} with {p.helper} ({p.reveal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
