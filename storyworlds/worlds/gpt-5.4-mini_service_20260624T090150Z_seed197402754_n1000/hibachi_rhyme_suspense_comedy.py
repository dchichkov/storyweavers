#!/usr/bin/env python3
"""
A small stand-alone storyworld about a hibachi dinner with rhyme, suspense, and comedy.

Seed premise:
A child goes to a hibachi restaurant expecting a fun meal, but a tiny surprise on the grill creates suspense. The chef's showmanship, a little mix-up, and a friendly fix turn it into a funny evening with a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    parent: str
    chef: str
    friend: str
    dish: str
    garnish: str
    incident: int = 0
    premise: int = 0
    rhyme_form: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


NAMES = ["Mina", "Eli", "Nora", "Theo", "Lila", "Jun", "Ari", "Zoe"]
PARENTS = ["mom", "dad", "aunt", "uncle"]
CHEFS = ["Chef Sora", "Chef Bingo", "Chef Nori", "Chef Taro"]
FRIENDS = ["Max", "Pip", "Rae", "Toby", "Momo", "Bea"]
DISHES = ["fried rice", "noodles", "shrimp", "teriyaki chicken", "veggies"]
GARNISHES = ["a lemon wedge", "a tiny onion volcano", "a green pea", "a shiny cherry tomato"]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child(N) :- name(N).
parent(P) :- parent_name(P).
chef(C) :- chef_name(C).
friend(F) :- friend_name(F).
dish(D) :- dish_name(D).
garnish(G) :- garnish_name(G).

rhyme_pair(D, G) :- dish_rhyme(D, G).
suspense_pair(D, G) :- suspenseful(D, G).

valid(N, D, G) :- name(N), dish_name(D), garnish_name(G), rhyme_pair(D, G).
valid_story(N, D, G, P) :- valid(N, D, G), parent_name(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for p in PARENTS:
        lines.append(asp.fact("parent_name", p))
    for c in CHEFS:
        lines.append(asp.fact("chef_name", c))
    for f in FRIENDS:
        lines.append(asp.fact("friend_name", f))
    for d in DISHES:
        lines.append(asp.fact("dish_name", d))
    for g in GARNISHES:
        lines.append(asp.fact("garnish_name", g))
    for d, g in RHYMES:
        lines.append(asp.fact("dish_rhyme", d, g))
    for d, g in SUSPENSE:
        lines.append(asp.fact("suspenseful", d, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


RHYMES = [
    ("fried rice", "a green pea"),
    ("noodles", "a tiny onion volcano"),
    ("shrimp", "a lemon wedge"),
    ("teriyaki chicken", "a shiny cherry tomato"),
    ("veggies", "a green pea"),
]
SUSPENSE = [
    ("fried rice", "a tiny onion volcano"),
    ("noodles", "a shiny cherry tomato"),
    ("shrimp", "a tiny onion volcano"),
    ("teriyaki chicken", "a lemon wedge"),
    ("veggies", "a shiny cherry tomato"),
]

PREMISES = [
    "{name} had never sat around a hibachi grill before. With {parent} on one side and {friend} on the other, every shiny spatula looked like part of a magic show.",
    "It was {parent}'s birthday, and {name} had promised to help make dinner cheerful. At the hibachi table, {friend} pointed to the grill and whispered, 'The stage is hot!'",
    "Rain had canceled {name}'s picnic with {friend}, so {parent} chose a hibachi dinner instead. Soon the drumming spatulas made the storm outside seem very far away.",
    "{name} felt nervous about tasting {dish}. Then {chef} bowed beside the hibachi grill and promised that brave bites came with a first-row cooking show.",
    "{name} and {friend} arrived at hibachi wearing paper crowns made by {parent}. They expected supper, but {chef} announced, 'Tonight, every diner joins the act.'",
    "The restaurant was nearly quiet when {name}, {parent}, and {friend} took the last hibachi seats. One clang from {chef}'s spatula woke the whole table with a grin.",
]

INCIDENTS = [
    {
        "lead": "First, {chef} shaped the {dish} into a little hill and balanced {garnish} at its peak.",
        "trigger": "A puff of steam nudged the garnish downhill. It rolled toward the grill's edge, faster with every wobble.",
        "risk": "Everyone wondered whether it would tumble onto the floor.",
        "action": "{name} slid an empty sauce dish beside the cool rim. The garnish rolled neatly into it with a tiny clink.",
        "resolution": "{chef} thanked {name}, checked that the dish was safely away from the heat, and returned the garnish to the plate.",
        "cause": "a puff of steam sent the garnish rolling toward the edge",
        "deed": "placed an empty sauce dish at the cool rim and caught it",
        "result": "the garnish landed safely in the sauce dish",
    },
    {
        "lead": "{chef} stacked onion rings into a tower beside the {dish}, then tucked {garnish} near its base.",
        "trigger": "The tower hissed, but no flame appeared. Instead, its top ring began to lean over {friend}'s plate.",
        "risk": "The table went silent as the crooked tower tipped another inch.",
        "action": "{name} spotted a loose onion ring and told {chef}, who lifted it away before the tower could topple.",
        "resolution": "With a wider base, the rebuilt tower puffed one harmless cloud straight up, and everybody cheered.",
        "cause": "a loose onion ring made the steaming tower lean",
        "deed": "noticed the loose ring and warned the chef",
        "result": "the chef rebuilt a steady tower that puffed safely upward",
    },
    {
        "lead": "Beside the {dish}, {chef} balanced {garnish} on a spatula and flipped it toward {parent}'s waiting plate.",
        "trigger": "The garnish landed under an upside-down metal bowl. Something beneath it went tick-tick-scritch.",
        "risk": "Nobody knew whether the hidden thing was dinner, a spoon, or a very tiny visitor.",
        "action": "{name} listened closely and heard the garnish rolling in circles. 'Lift slowly,' {name} advised.",
        "resolution": "{chef} raised the bowl one finger-width at a time and found only the spinning garnish, perfectly clean and safe.",
        "cause": "the garnish rolled under a metal bowl and made a mysterious scratching sound",
        "deed": "listened to the sound and asked the chef to lift the bowl slowly",
        "result": "they discovered the harmless garnish spinning beneath the bowl",
    },
    {
        "lead": "{chef} drew a smiling face in the {dish}, with {garnish} perched where its nose should be.",
        "trigger": "Then the grill fan tugged a paper order slip toward the hot surface. It fluttered just beyond the spatula.",
        "risk": "For one breath, the little slip hovered over the heat like a white moth.",
        "action": "{name} pointed while {friend} called, 'Behind the plate!' {chef} covered the flame and pinned the slip with a cool plate.",
        "resolution": "The order stayed readable, the paper never touched the heat, and the smiling dinner kept its garnish nose.",
        "cause": "the grill fan blew a paper order slip toward the hot surface",
        "deed": "spotted the slip and helped direct the chef to it",
        "result": "the chef covered the flame and secured the slip with a cool plate",
    },
    {
        "lead": "{chef} made the spatulas tap a marching beat while the {dish} sizzled and {garnish} waited on a plate.",
        "trigger": "One spatula slipped from the rhythm and spun on the empty side of the grill, handle circling toward {chef}.",
        "risk": "The silver tool whirled once, twice, and seemed ready to spin right off its safe patch.",
        "action": "{name} called, 'Stop the drum!' {chef} froze the other spatula and trapped the spinning handle beneath it.",
        "resolution": "After checking the tool, {chef} began a slower beat, and {name} counted every careful tap.",
        "cause": "a spatula slipped and spun across an empty part of the grill",
        "deed": "called for the drumming to stop so the chef could trap the handle",
        "result": "the chef caught the spatula and restarted with a slower, safer rhythm",
    },
    {
        "lead": "A ribbon of noodles rose from {chef}'s spatula while the {dish} and {garnish} waited below.",
        "trigger": "The noodle ribbon looped around the pepper shaker and began pulling it toward the hot grill.",
        "risk": "The shaker crept closer, leaving a dotted trail of pepper behind it.",
        "action": "{name} held up a napkin as a signal. {chef} snipped the noodle loop with the spatula's edge and caught the shaker.",
        "resolution": "Then {parent} wiped the cool tabletop, and {chef} served a fresh noodle curl shaped like a question mark.",
        "cause": "a noodle loop tugged the pepper shaker toward the grill",
        "deed": "signaled the chef, who cut the noodle loop and caught the shaker",
        "result": "the shaker stayed safe and the tabletop was cleaned",
    },
    {
        "lead": "{chef} covered the {dish} with a lid and asked everyone to guess where {garnish} would appear.",
        "trigger": "When the lid rose, the garnish was gone. A small round bump traveled beneath {parent}'s folded napkin.",
        "risk": "The bump stopped. Then it moved again, as if dinner had learned to crawl.",
        "action": "{name} followed the damp little trail and gently unfolded the napkin over a clean plate.",
        "resolution": "Out rolled the missing garnish. {chef} replaced it with a fresh one and sent the runaway to the dish bin.",
        "cause": "the garnish slipped beneath a folded napkin and made a moving bump",
        "deed": "followed its trail and opened the napkin over a clean plate",
        "result": "they found the garnish and the chef replaced it with a fresh one",
    },
    {
        "lead": "For the grand trick, {chef} set a spoon bridge over the {dish} and placed {garnish} at one end.",
        "trigger": "A tap sent the garnish across, but it stopped in the middle while the spoon bridge trembled.",
        "risk": "Would it roll forward into the meal or backward toward the hot grill?",
        "action": "{name} asked everyone to stop bumping the table. In the sudden stillness, {chef} tilted the spoon toward the plate.",
        "resolution": "The garnish rolled the safe way and landed atop dinner as softly as a marble on a pillow.",
        "cause": "the garnish stalled on a trembling spoon bridge",
        "deed": "asked everyone to hold still while the chef tilted the spoon toward the plate",
        "result": "the garnish rolled safely onto the meal",
    },
]

RHYME_FORMS = [
    "{friend} clapped a beat: 'Slow by the glow; steady and ready!' The table repeated it until the worry shrank.",
    "{chef} sang, 'No crash, no splash; we saved supper in a flash!' Even {parent} answered with a drumroll on the table.",
    "'Was that a dinner disaster?' asked {friend}. 'No,' said {name}, 'just a platter that needed us faster!'",
    "{name} tried a tongue twister: 'Hibachi heroes handle hot hills.' Then came the rhyme, 'Slow with the show is the safest way to go!'",
    "{chef} called, 'What beats fright?' The diners answered, 'Thinking right!' Their call-and-response bounced around the table.",
    "{friend} made a tiny two-line poem: 'We waited in suspense tonight; then teamwork turned the trouble right.'",
    "'Knock, knock,' said {chef}. 'Who's there?' asked {name}. 'Dinner.' 'Dinner who?' 'Dinner is a winner, especially for a hungry beginner!'",
    "The table invented a menu rhyme together: 'A careful clue, a thing to do, and hibachi dinner coming through!'",
]

ENDINGS = [
    "At the end, {name} lifted the last bite of {dish}. In the clean plate below, {garnish} sat like a tiny medal for staying calm.",
    "Outside, the rain shone in the restaurant lights. {name} drew a smiling hibachi grill in the foggy window, complete with a safely parked garnish.",
    "Before leaving, {chef} folded a paper chef hat for {name}. Across its front, {friend} wrote, 'Chief Clue Finder of Table Seven.'",
    "The final wisp of steam curled into a question-mark shape above the empty plate. {name} laughed because this mystery now had a happy answer.",
    "On the ride home, {name} tapped the slow, safe spatula rhythm on both knees. Beside {name}, {parent} supplied the rhyme, and neither missed a beat.",
    "The table's last cheer made the little paper crowns wobble. Under them, {name} and {friend} grinned at a dinner saved by noticing and helping.",
    "{chef} placed one cool spatula beside the finished plate for a picture. It reflected four relieved smiles and not one runaway bite.",
    "As the restaurant lights dimmed, the polished grill reflected {name}'s wave. The garnish rested at the center of the finished plate, bright under the lamp.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hibachi storyworld with rhyme, suspense, and comedy.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--chef", choices=CHEFS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--garnish", choices=GARNISHES)
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


def valid_combos() -> list[tuple[str, str]]:
    return list(dict.fromkeys(RHYMES))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({(dish, garnish) for _, dish, garnish in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.dish and args.garnish:
        if (args.dish, args.garnish) not in combos:
            raise StoryError("No story: that dish and garnish do not make a believable rhyme-and-suspense pair.")
    if args.dish:
        combos = [c for c in combos if c[0] == args.dish]
    if args.garnish:
        combos = [c for c in combos if c[1] == args.garnish]
    if not combos:
        raise StoryError("No valid combo matches the given options.")
    dish, garnish = rng.choice(sorted(combos))
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        parent=args.parent or rng.choice(PARENTS),
        chef=args.chef or rng.choice(CHEFS),
        friend=args.friend or rng.choice(FRIENDS),
        dish=dish,
        garnish=garnish,
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        rhyme_form=rng.randrange(len(RHYME_FORMS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    """Give consecutive CLI seeds distinct combinations of narrative forms."""
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.rhyme_form = (seed // 3) % len(RHYME_FORMS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "name": params.name,
        "parent": params.parent,
        "chef": params.chef,
        "friend": params.friend,
        "dish": params.dish,
        "garnish": params.garnish,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    w = World()
    kid = w.add(Entity(id=params.name, kind="character", label=params.name))
    parent = w.add(Entity(id=params.parent, kind="character", label=params.parent))
    chef = w.add(Entity(id=params.chef, kind="character", label=params.chef))
    friend = w.add(Entity(id=params.friend, kind="character", label=params.friend))
    meal = w.add(Entity(id="meal", label=params.dish, meters={"hot": 0.0}, memes={"tension": 0.0}))
    garnish = w.add(Entity(id="garnish", label=params.garnish, meters={"spin": 0.0}, memes={"surprise": 0.0}))

    w.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    w.say(f"The air smelled like toasted sesame and {meal.label}, and {chef.label} reminded everyone to keep hands away from the hot grill.")
    w.say(incident["lead"].format(**values))

    w.para()
    meal.meters["hot"] = 1.0
    meal.memes["tension"] = 1.0
    garnish.meters["spin"] = 1.0
    garnish.memes["surprise"] = 1.0
    w.say(incident["trigger"].format(**values))
    w.say(incident["risk"].format(**values))
    w.say(incident["action"].format(**values))

    w.para()
    kid.memes["relief"] = 1.0
    kid.memes["joy"] = 1.0
    chef.memes["pride"] = 1.0
    friend.memes["joy"] = 1.0
    w.say(incident["resolution"].format(**values))
    w.say(RHYME_FORMS[params.rhyme_form % len(RHYME_FORMS)].format(**values))
    w.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    w.facts.update(
        kid=kid.id,
        parent=parent.id,
        chef=chef.id,
        friend=friend.id,
        dish=params.dish,
        garnish=params.garnish,
        incident=params.incident % len(INCIDENTS),
        suspense_cause=incident["cause"],
        helpful_action=incident["deed"],
        result=incident["result"],
        suspense=True,
        resolved=True,
    )

    prompts = [
        "Write a funny, rhyming story about a child at a hibachi restaurant where a small surprise creates suspense.",
        f"Tell a suspense-comedy story in which {params.name} visits hibachi with {params.parent} and helps {params.chef} solve a dinner problem.",
        f"Write a child-friendly hibachi story that includes {params.dish}, {params.garnish}, a causal solution, and a playful rhyme.",
    ]

    story_qa = [
        QAItem(
            question=f"Who went to the hibachi restaurant in the story?",
            answer=f"{params.name} went with {params.parent}, and they watched {params.chef} cook at the table.",
        ),
        QAItem(
            question=f"What made the moment feel suspenseful?",
            answer=f"The moment felt suspenseful because {incident['cause']}. Everyone had to wait and see what would happen next.",
        ),
        QAItem(
            question=f"What did {params.name} do to help?",
            answer=f"{params.name} {incident['deed']}. That careful action helped solve the problem.",
        ),
        QAItem(
            question=f"How was the problem resolved?",
            answer=f"In the end, {incident['result']}. The diners relaxed and turned the tense moment into a rhyme and a joke.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a hibachi grill?",
            answer="A hibachi grill is a hot cooking surface where a chef cooks food right in front of the diners.",
        ),
        QAItem(
            question="Why do people watch hibachi cooking?",
            answer="People watch hibachi cooking because it is exciting, and the chef often makes the meal feel like a show.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something might go wrong.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'pop' and 'flop.'",
        ),
        QAItem(
            question="Why can comedy help a suspenseful scene?",
            answer="Comedy can make a tense moment feel lighter by turning a problem into something silly and fun.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", parent="mom", chef="Chef Sora", friend="Max", dish="fried rice", garnish="a green pea", incident=0, premise=0, rhyme_form=0, ending=0),
        StoryParams(name="Theo", parent="dad", chef="Chef Bingo", friend="Rae", dish="noodles", garnish="a tiny onion volcano", incident=2, premise=2, rhyme_form=3, ending=3),
        StoryParams(name="Lila", parent="aunt", chef="Chef Nori", friend="Pip", dish="shrimp", garnish="a lemon wedge", incident=5, premise=4, rhyme_form=5, ending=5),
        StoryParams(name="Jun", parent="uncle", chef="Chef Taro", friend="Toby", dish="teriyaki chicken", garnish="a shiny cherry tomato", incident=7, premise=5, rhyme_form=7, ending=7),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (dish, garnish) combos:\n")
        for dish, garnish in triples:
            print(f"  {dish:18} -> {garnish}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            apply_seeded_structure(params, seed)
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
            header = f"### {p.name}: hibachi with {p.dish} and {p.garnish}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
