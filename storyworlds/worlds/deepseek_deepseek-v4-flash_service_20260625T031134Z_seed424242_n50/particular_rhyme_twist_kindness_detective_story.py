#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/particular_rhyme_twist_kindness_detective_story.py
============================================================================================================

A standalone story world sketch for a particular rhyme twist kindness detective story
and close, constraint-checked variations of it.

A child detective follows rhyming clues to solve a small mystery, but the obvious
suspect turns out to be the victim of a misunderstanding. The kindness twist:
the detective solves it by helping, not blaming.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mom"}
        male = {"boy", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Clue:
    id: str
    text: str
    rhyme_word: str
    location: str
    hidden_by: Optional[str] = None
    is_planted: bool = False
    leads_to: Optional[str] = None


@dataclass
class Mystery:
    id: str
    victim_id: str
    lost_item: str
    lost_phrase: str
    setting: str
    false_suspect_id: str
    real_returner_id: str
    misunderstanding: str
    kindness_resolution: str


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, mystery: Mystery) -> None:
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_found: list[str] = []
        self.accused_wrong_person: bool = False
        self.understood_twist: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.mystery)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.clues_found = list(self.clues_found)
        clone.accused_wrong_person = self.accused_wrong_person
        clone.understood_twist = self.understood_twist
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Settings, mysteries, clues
# ---------------------------------------------------------------------------
SETTINGS = {
    "bakery": "the little bakery on Maple Street",
    "library": "the town library with creaky floors",
    "park": "the old park near the fountain",
    "school": "the sunny schoolyard at recess time",
    "garden": "Miss Rose's garden full of daisies",
}

MYSTERIES = {
    "missing_recipe": Mystery(
        id="missing_recipe",
        victim_id="Baker Ben",
        lost_item="recipe book",
        lost_phrase="a worn recipe book with a red cover",
        setting="bakery",
        false_suspect_id="Chef Carla",
        real_returner_id="Teacher Tim",
        misunderstanding="Chef Carla had borrowed it to copy a cake recipe but forgot to tell anyone",
        kindness_resolution="Teacher Tim returned it with new recipe notes as an apology",
    ),
    "lost_locket": Mystery(
        id="lost_locket",
        victim_id="Lily the librarian",
        lost_item="silver locket",
        lost_phrase="a silver locket with a tiny daisy engraved",
        setting="library",
        false_suspect_id="Max the handyman",
        real_returner_id="Nina the gardener",
        misunderstanding="Max had found it and put it in a drawer for safekeeping, but no one knew",
        kindness_resolution="Nina brought it back after finding it among the flowerpots",
    ),
    "stolen_chalk": Mystery(
        id="stolen_chalk",
        victim_id="Teacher Tilly",
        lost_item="box of rainbow chalk",
        lost_phrase="a box of rainbow chalk that squeaked when you drew",
        setting="school",
        false_suspect_id="Sam the janitor",
        real_returner_id="Pablo the painter",
        misunderstanding="Sam had moved the chalk box to the supply closet during cleaning",
        kindness_resolution="Pablo painted a mural with the chalk and gave it back with a thank-you note",
    ),
    "hidden_gloves": Mystery(
        id="hidden_gloves",
        victim_id="Gardener Gina",
        lost_item="gardening gloves",
        lost_phrase="soft green gardening gloves with flower patches",
        setting="garden",
        false_suspect_id="Wally the mailman",
        real_returner_id="Dora the neighbor",
        misunderstanding="Wally had borrowed them to prune his rose bush but forgot to return them",
        kindness_resolution="Dora brought them back with a bouquet of roses",
    ),
}

CLUE_SETS: dict[str, list[Clue]] = {
    "missing_recipe": [
        Clue(id="clue1", text="A crumb on the counter, a smear of sweet cream,\nSomeone was baking a cake, or a dream.",
             rhyme_word="cream", location="counter", is_planted=False, leads_to="counter"),
        Clue(id="clue2", text="A note in the drawer said 'Borrow, don't take,\nWith sugar and butter, a new cake to make.'",
             rhyme_word="take", location="drawer", hidden_by="Chef Carla", leads_to="notebook"),
        Clue(id="clue3", text="A footprint in flour, not wide but small,\nLeading to a shelf against the wall.",
             rhyme_word="small", location="floor", is_planted=False, leads_to="shelf"),
        Clue(id="clue4", text="A whisper in the kitchen, soft and kind:\n'Finders keepers? No, return what you find.'",
             rhyme_word="kind", location="kitchen", leads_to="resolution"),
    ],
    "lost_locket": [
        Clue(id="clue1", text="A glint by the window, a flash of old light,\nSomething silver hid out of sight.",
             rhyme_word="light", location="windowsill", is_planted=False, leads_to="windowsill"),
        Clue(id="clue2", text="A drawer half-open, a rag nearby,\nSomeone cleaned and put things by.",
             rhyme_word="by", location="desk", hidden_by="Max the handyman", leads_to="desk"),
        Clue(id="clue3", text="A flowerpot shifted, the soil disturbed,\nA secret the gardener had never perturbed.",
             rhyme_word="disturbed", location="pot", leads_to="garden"),
        Clue(id="clue4", text="A daisy bent low, pointing the way:\n'Ask the gardener what she found today.'",
             rhyme_word="way", location="flowerbed", leads_to="resolution"),
    ],
    "stolen_chalk": [
        Clue(id="clue1", text="A squeak on the board, a rainbow smear,\nSomeone was drawing, and drew very near.",
             rhyme_word="smear", location="blackboard", is_planted=False, leads_to="blackboard"),
        Clue(id="clue2", text="A bucket on wheels, a mop in a pail,\nSomeone cleaned and left a trail.",
             rhyme_word="pail", location="hallway", hidden_by="Sam the janitor", leads_to="closet"),
        Clue(id="clue3", text="A closet door ajar, a box on the floor,\nNot stolen, just moved—nothing to deplore.",
             rhyme_word="floor", location="supply_closet", leads_to="supply_closet"),
        Clue(id="clue4", text="A rainbow mural on the playground wall:\n'Who made this?' The answer will enthral.",
             rhyme_word="wall", location="playground", leads_to="resolution"),
    ],
    "hidden_gloves": [
        Clue(id="clue1", text="A petal on the path, a rosebush trimmed neat,\nSomeone was pruning, using quick feet.",
             rhyme_word="neat", location="path", is_planted=False, leads_to="path"),
        Clue(id="clue2", text="A green thread caught on a thorny stem,\nA gardener left a clue for them.",
             rhyme_word="stem", location="rosebush", hidden_by="Wally the mailman", leads_to="rosebush"),
        Clue(id="clue3", text="A mailbag open, a glove peeking out,\n'I meant to return it, there is no doubt.'",
             rhyme_word="out", location="mailbag", leads_to="mailbag"),
        Clue(id="clue4", text="A note tucked in gloves: 'I am sorry, my friend.\nThe kindness of giving makes all sorrows end.'",
             rhyme_word="end", location="glove_pocket", leads_to="resolution"),
    ],
}


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_find_clue(world: World) -> list[str]:
    out = []
    for clue in CLUE_SETS.get(world.mystery.id, []):
        if clue.id not in world.clues_found:
            sig = ("find", clue.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.clues_found.append(clue.id)
            out.append(f"Detective {world.facts['detective'].id} found a clue: {clue.text}")
    return out


def _r_accuse_false(world: World) -> list[str]:
    """If enough clues found but not all, detective accuses the wrong person."""
    if len(world.clues_found) >= 2 and not world.accused_wrong_person:
        sig = ("accuse", world.mystery.false_suspect_id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.accused_wrong_person = True
        suspect = world.entities.get(world.mystery.false_suspect_id)
        if suspect:
            suspect.memes["accused"] += 1
            return [f"But wait! The clues pointed at {suspect.label}. Was it {suspect.label}?"]
    return []


def _r_twist_kindness(world: World) -> list[str]:
    """When all clues found, the twist reveals the truth with kindness."""
    expected = len(CLUE_SETS.get(world.mystery.id, []))
    if len(world.clues_found) >= expected and not world.understood_twist:
        sig = ("twist", world.mystery.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.understood_twist = True
        returner = world.entities.get(world.mystery.real_returner_id)
        if returner:
            returner.memes["helper"] += 1
            return [
                f"Then the detective understood! {returner.label} had found the {world.mystery.lost_item} "
                f"and {world.mystery.misunderstanding}. "
                f"And with {world.mystery.kindness_resolution}, everyone forgave each other."
            ]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="find_clue", tag="investigation", apply=_r_find_clue),
    Rule(name="accuse_false", tag="tension", apply=_r_accuse_false),
    Rule(name="twist_kindness", tag="resolution", apply=_r_twist_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(mystery_id: str, detective_name: str = "Dot",
         detective_type: str = "girl", partner_type: str = "mother") -> World:
    mystery = MYSTERIES[mystery_id]
    world = World(mystery)
    setting_name = mystery.setting
    setting_phrase = SETTINGS[setting_name]

    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_type,
        traits=["curious", "clever", "kind"],
        label=f"Detective {detective_name}",
        phrase=f"a {detective_type} detective with a notebook and a big heart",
    ))
    partner = world.add(Entity(
        id="Partner", kind="character", type=partner_type,
        label=partner_type,
        phrase=f"{detective_name}'s {partner_type} and partner in solving mysteries",
    ))
    victim = world.add(Entity(
        id=mystery.victim_id, kind="character", type="person",
        label=mystery.victim_id,
        phrase=f"the kind {mystery.victim_id.split()[-1].lower()} who lost the {mystery.lost_item}",
    ))
    false_suspect = world.add(Entity(
        id=mystery.false_suspect_id, kind="character", type="person",
        label=mystery.false_suspect_id,
        phrase=f"the {mystery.false_suspect_id.split()[-1].lower()} who everyone suspected",
    ))
    returner = world.add(Entity(
        id=mystery.real_returner_id, kind="character", type="person",
        label=mystery.real_returner_id,
        phrase=f"the {mystery.real_returner_id.split()[-1].lower()} who found the {mystery.lost_item}",
    ))

    world.facts["detective"] = detective
    world.facts["partner"] = partner
    world.facts["victim"] = victim
    world.facts["false_suspect"] = false_suspect
    world.facts["returner"] = returner
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting_phrase
    world.facts["rhyme_clues"] = CLUE_SETS[mystery_id]

    # Act 1: The mystery is announced
    world.say(
        f"In {setting_phrase}, something particular had happened.\n"
        f"{victim.label} lost {mystery.lost_phrase}.\n"
        f'"Oh no!" cried {victim.label}. "I need it for today!"'
    )
    world.say(
        f"Detective {detective_name} put on {detective.pronoun('possessive')} thinking cap.\n"
        f'"We will solve this case," {detective.pronoun()} said to {partner.label}.'
    )

    # Act 2: Finding clues with rhymes
    world.para()
    clues = CLUE_SETS[mystery_id]
    for i, clue in enumerate(clues):
        world.say(
            f"{detective_name} looked {clue.location}. "
            f"{detective.pronoun('possessive').capitalize()} eyes grew wide.\n"
            f'"Aha! A clue!" {detective.pronoun()} cried.'
        )
        world.say(clue.text)

    # Act 3: The false accusation and twist
    world.para()
    world.say(
        f'"I think it was {false_suspect.label}!" said {detective_name}.\n'
        f"Everyone gasped. But {false_suspect.label} looked sad."
    )
    world.say(
        f'Then {detective_name} found one more clue, hidden in plain sight.\n'
        f'"Wait," {detective.pronoun()} said. "I was wrong!"'
    )
    world.say(
        f'{returner.label} stepped forward. "I have the {mystery.lost_item}," '
        f'{returner.pronoun()} said softly.\n'
        f'{mystery.kindness_resolution}.'
    )
    world.say(
        f"{false_suspect.label} smiled. 'I forgive you,' {false_suspect.pronoun()} said.\n"
        f"And {detective_name} learned that sometimes, the real clue is kindness."
    )

    # Record facts for QA
    world.facts.update(
        clues_found=len(clues),
        wrong_accusation=True,
        twist_resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mystery: str
    detective_name: str
    detective_gender: str
    partner: str
    seed: Optional[int] = None


DETECTIVE_NAMES = {
    "girl": ["Dot", "Meg", "Pip", "Zoe", "Nell", "Flo", "Bess", "Tess", "Quinn", "Rue"],
    "boy": ["Max", "Finn", "Ace", "Jake", "Rex", "Cole", "Miles", "Ollie", "Sam", "Gus"],
}

PARTNER_TYPES = ["mother", "father", "aunt", "uncle", "grandma", "grandpa"]


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "detective": [
        ("What does a detective do?",
         "A detective is someone who solves mysteries by looking for clues and asking questions."),
        ("What is a clue?",
         "A clue is a piece of information or an object that helps solve a mystery."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when two words end with the same sound, like 'cat' and 'hat' or 'smear' and 'near'."),
    ],
    "kindness": [
        ("Why is kindness important?",
         "Kindness helps people feel better when they are sad or confused. "
         "It turns arguments into hugs and makes everyone feel safe."),
    ],
    "twist": [
        ("What is a story twist?",
         "A twist is when the story surprises you and the answer is not what you first thought."),
    ],
}

KNOWLEDGE_ORDER = ["detective", "rhyme", "kindness", "twist"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    detective = f["detective"]
    partner = f["partner"]
    return [
        f'Write a short rhyming detective story for a 3-to-5-year-old '
        f'where a {detective.type} detective named {detective.id} solves '
        f'the case of the missing {mystery.lost_item} with kindness.',
        f'Tell a gentle mystery story with a twist: the person everyone '
        f'suspected was not the one who took the {mystery.lost_item}.',
        f'Write a story with rhyming clues that teaches a lesson about '
        f'kindness and forgiveness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    mystery = f["mystery"]
    victim = f["victim"]
    false_suspect = f["false_suspect"]
    returner = f["returner"]
    partner = f["partner"]
    sub = detective.pronoun("subject")
    obj = detective.pronoun("object")
    pos = detective.pronoun("possessive")

    qa = [
        QAItem(
            question=f"Who was the particular detective in this story, and what was {pos} partner called?",
            answer=f"The detective was {detective.id}, a {detective.type} with a kind heart. "
                   f"{pos.capitalize()} partner was {partner.label}.",
        ),
        QAItem(
            question=f"What did {victim.label} lose, and where did it happen?",
            answer=f"{victim.label} lost {mystery.lost_phrase} at {SETTINGS[mystery.setting]}.",
        ),
        QAItem(
            question=f"Who did {detective.id} first think took the {mystery.lost_item}, and who really had it?",
            answer=f"{detective.id.capitalize()} first thought {false_suspect.label} took it, "
                   f"but really {returner.label} had it. "
                   f"{mystery.kindness_resolution}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  clues found: {world.clues_found}")
    lines.append(f"  wrong accusation: {world.accused_wrong_person}")
    lines.append(f"  twist understood: {world.understood_twist}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Valid combos
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(mystery="missing_recipe", detective_name="Dot", detective_gender="girl", partner="mother"),
    StoryParams(mystery="lost_locket", detective_name="Max", detective_gender="boy", partner="father"),
    StoryParams(mystery="stolen_chalk", detective_name="Meg", detective_gender="girl", partner="aunt"),
    StoryParams(mystery="hidden_gloves", detective_name="Finn", detective_gender="boy", partner="grandma"),
]


def valid_mysteries() -> list[str]:
    return list(MYSTERIES.keys())


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is valid if there is a setting and clues exist.
mystery_setting(M, S) :- mystery(M), setting_of(M, S).
has_clues(M) :- mystery(M), clue_count(M, C), C > 0.
valid_mystery(M) :- mystery(M), mystery_setting(M, _), has_clues(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("setting_of", mid, m.setting))
        clue_count = len(CLUE_SETS.get(mid, []))
        lines.append(asp.fact("clue_count", mid, clue_count))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_mystery/1."))
    return sorted(set(asp.atoms(model, "valid_mystery")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_mysteries())
    python_set = {(m,) for m in valid_mysteries()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches ({len(clingo_set)} mysteries).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a particular rhyme twist kindness detective story.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--detective-name")
    ap.add_argument("--partner", choices=PARTNER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories")
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
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError(f"No such mystery: {args.mystery}")

    mystery = args.mystery or rng.choice(valid_mysteries())
    gender = args.detective_gender or rng.choice(["girl", "boy"])
    name = args.detective_name or rng.choice(DETECTIVE_NAMES[gender])
    partner = args.partner or rng.choice(PARTNER_TYPES)
    return StoryParams(
        mystery=mystery,
        detective_name=name,
        detective_gender=gender,
        partner=partner,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.mystery, params.detective_name,
                 params.detective_gender, params.partner)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mystery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        valid = asp_valid_mysteries()
        print(f"{len(valid)} valid mysteries:")
        for (m,) in valid:
            print(f"  {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.detective_name}: {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
