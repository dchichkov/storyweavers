#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/eyer_borrow_mesmerize_repetition_sharing_conflict_ghost.py
==============================================================================================================

A standalone *story world* sketch for a ghost story about a ghost who borrows
a child's eyes to see the world, told with repetition, sharing, and conflict.

Initial story (used to build a world model):
---
Once upon a time, there was a little girl named Elara who lived in a quiet
village at the edge of a misty forest. Every night, a ghost named Wisp would
drift through the village, mesmerized by the lights in the windows but unable
to see them clearly. Wisp had no eyes of his own.

One evening, Wisp drifted to Elara's window. He tapped on the glass, and
Elara, who was brave and kind, opened it. "Please," whispered Wisp, "may I
borrow your eyes, just for a little while? I want to see the fireflies and
the stars." Elara felt a shiver of fear but also pity. "Will you give them
back?" she asked. "I promise," said Wisp.

Elara closed her eyes, and Wisp took them. He saw the world for the first
time—the golden fireflies, the silver moon, the deep purple night. He was
mesmerized. But when it was time to return, Wisp hesitated. The sight was so
beautiful. "Just one more minute," he whispered, but the minute stretched
into many. Elara cried out in the darkness, "Please, give them back!"

Wisp felt a conflict in his heart. He wanted to keep the eyes, but he also
remembered his promise. With great effort, he returned the eyes to Elara.
She opened them and saw Wisp's sad, grateful face. "It was selfish of me,"
said Wisp. "But thank you for sharing your sight." Elara smiled. "You can
borrow them again sometime," she said. "Just remember to share the seeing
with me." And from then on, whenever Wisp borrowed Elara's eyes, he always
came back and told her everything he had seen, and they watched the world
together, one pair of eyes between them.

Causal state updates:
---
    borrow eyes                 -> ghost.vision += 1, child.trust -= 1
    keep eyes too long          -> ghost.selfishness += 1, child.fear += 1
    return eyes                 -> ghost.gratitude += 1, child.trust += 1
    share what was seen         -> ghost.joy += 1, child.joy += 1, friendship += 1
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

EMOTION_KEYS = {"fear", "trust", "joy", "selfishness", "gratitude", "sadness", "hope"}
PHYSICAL_KEYS = {"vision", "voice"}


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    is_ghost: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the village"
    night_time: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class BorrowAct:
    id: str
    verb: str
    gerund: str
    thing: str
    description: str
    magnetic: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    borrow_act: str
    gift: str
    child_name: str
    ghost_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_borrow_conflict(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.is_ghost and actor.memes["borrowed_eyes"] >= THRESHOLD:
            child = [e for e in world.characters() if not e.is_ghost]
            if child and child[0].memes["fear"] >= THRESHOLD:
                sig = ("conflict_borrow", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append("__conflict__")
    return out


def _r_keep_too_long(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.is_ghost and actor.memes["kept_eyes"] >= THRESHOLD:
            actor.memes["selfishness"] += 1
            child = [e for e in world.characters() if not e.is_ghost]
            if child:
                child[0].memes["fear"] += 1
                sig = ("kept_long", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f"The ghost kept the eyes too long, and the child grew afraid.")
    return out


def _r_return_eyes(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.is_ghost and actor.memes["returned_eyes"] >= THRESHOLD:
            actor.memes["gratitude"] += 1
            child = [e for e in world.characters() if not e.is_ghost]
            if child:
                child[0].memes["trust"] += 1
                sig = ("returned", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append("The ghost returned what was borrowed.")
    return out


def _r_share_story(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.is_ghost and actor.memes["shared_story"] >= THRESHOLD:
            actor.memes["joy"] += 1
            child = [e for e in world.characters() if not e.is_ghost]
            if child:
                child[0].memes["joy"] += 1
                sig = ("shared", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append("The ghost shared everything he had seen, and they both felt joy.")
    return out


CAUSAL_RULES = [
    Rule(name="borrow_conflict", apply=_r_borrow_conflict),
    Rule(name="keep_too_long", apply=_r_keep_too_long),
    Rule(name="return_eyes", apply=_r_return_eyes),
    Rule(name="share_story", apply=_r_share_story),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "village": Setting(place="a quiet village at the edge of a misty forest", night_time=True, affords={"eyes"}),
    "cottage": Setting(place="a lonely cottage by the dark lake", night_time=True, affords={"eyes"}),
    "town": Setting(place="an old town with cobblestone streets", night_time=True, affords={"eyes"}),
}

BORROW_ACTS = {
    "eyes": BorrowAct(
        id="eyes",
        verb="borrow your eyes",
        gerund="borrowing eyes",
        thing="eyes",
        description="the golden fireflies, the silver moon, the deep purple night",
        magnetic="mesmerized by the sight",
        keyword="eyes",
        tags={"sight", "borrow"},
    ),
}

GIFTS = {
    "eyes": Gift(
        label="eyes",
        phrase="her bright, curious eyes",
        type="eyes",
        plural=True,
    ),
}

CHILD_NAMES = ["Elara", "Mira", "Lena", "Sophie", "Clara", "Ivy", "Rose", "Hazel"]
GHOST_NAMES = ["Wisp", "Shade", "Glimmer", "Echo", "Flicker", "Vapor", "Dusk", "Nimbus"]
TRAITS = ["brave", "kind", "curious", "gentle", "fearless", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id in BORROW_ACTS:
            for gift_id in GIFTS:
                combos.append((place, act_id, gift_id))
    return combos


def tell(setting: Setting, borrow_act: BorrowAct, gift_cfg: Gift,
         child_name: str = "Elara", child_gender: str = "girl",
         child_traits: Optional[list[str]] = None, ghost_name: str = "Wisp") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender,
        traits=["little"] + (child_traits or ["brave", "kind"]),
    ))
    ghost = world.add(Entity(
        id=ghost_name, kind="character", type="ghost",
        is_ghost=True,
        traits=["lonely", "curious", "gentle"],
        label="the ghost",
    ))
    gift = world.add(Entity(
        id="gift", type=gift_cfg.type, label=gift_cfg.label,
        phrase=gift_cfg.phrase, owner=child.id,
        plural=gift_cfg.plural,
    ))

    # Act 1: Introduction
    world.say(f"Once upon a time, there was a little {child_gender} named {child_name} "
              f"who lived in {setting.place}.")
    world.say(f"Every night, a ghost named {ghost_name} would drift through the village, "
              f"mesmerized by the lights in the windows but unable to see them clearly.")
    world.say(f"{ghost_name} had no {borrow_act.thing} of his own.")

    world.para()

    # Act 2: The Borrowing
    world.say(f"One evening, {ghost_name} drifted to {child_name}'s window.")
    world.say(f"He tapped on the glass, and {child_name}, who was "
              f"{' and '.join(child_traits or ['brave', 'kind'])}, opened it.")
    world.say(f'"Please," whispered {ghost_name}, "may I {borrow_act.verb}, '
              f'just for a little while? I want to see the world."')
    ghost.memes["borrowed_eyes"] += 1
    child.memes["fear"] += 0.5

    world.say(f'{child_name} felt a shiver of fear but also pity. '
              f'"Will you give them back?" she asked.')
    world.say(f'"I promise," said {ghost_name}.')

    world.para()

    # Act 3: The Mesmerizing
    world.say(f"{child_name} closed her eyes, and {ghost_name} took them.")
    ghost.memes["vision"] += 2
    ghost.memes["joy"] += 1
    world.say(f"He {borrow_act.gerund} and saw {borrow_act.description}. "
              f"He was {borrow_act.magnetic}.")

    world.para()

    # Act 4: The Conflict
    world.say(f"But when it was time to return, {ghost_name} hesitated. "
              f"The sight was so beautiful.")
    ghost.memes["kept_eyes"] += 1
    propagate(world)

    # Repetition for effect
    world.say(f'"Just one more minute," he whispered.')
    world.say(f'"Just one more minute," he whispered again.')
    world.say(f"But the minute stretched into many.")
    ghost.memes["selfishness"] += 1
    child.memes["fear"] += 1
    propagate(world)

    world.say(f'{child_name} cried out in the darkness, "Please, give them back!"')

    # Act 5: The Resolution
    world.say(f'{ghost_name} felt a conflict in his heart. He wanted to keep the eyes, '
              f'but he also remembered his promise.')
    propagate(world)

    ghost.memes["returned_eyes"] += 1
    propagate(world)
    world.say(f'With great effort, he returned the eyes to {child_name}.')
    world.say(f'She opened them and saw {ghost_name}\'s sad, grateful face.')
    ghost.memes["gratitude"] += 1
    child.memes["trust"] += 1

    world.para()

    # Act 6: Sharing
    ghost.memes["shared_story"] += 1
    propagate(world)
    world.say(f'"It was selfish of me," said {ghost_name}. '
              f'"But thank you for sharing your sight."')
    world.say(f'{child_name} smiled. "You can borrow them again sometime," she said. '
              f'"Just remember to share the seeing with me."')
    world.say(f'And from then on, whenever {ghost_name} borrowed {child_name}\'s eyes, '
              f'he always came back and told her everything he had seen, '
              f'and they watched the world together, one pair of eyes between them.')

    world.facts.update(child=child, ghost=ghost, gift=gift, gift_cfg=gift_cfg,
                       borrow_act=borrow_act, setting=setting,
                       conflict=ghost.memes["selfishness"] >= THRESHOLD,
                       resolved=ghost.memes["gratitude"] >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, ghost, act = f["child"], f["ghost"], f["borrow_act"]
    kw = act.keyword
    return [
        f'Write a short ghost story for a 3-to-5-year-old about a ghost who '
        f'wants to {act.verb} and learns about sharing.',
        f'Tell a gentle story where a ghost named {ghost.id} {act.gerund} from '
        f'a child named {child.id} and must return what was borrowed.',
        f'Write a simple story using the word "{kw}" about repetition, sharing, '
        f'and making things right.',
    ]


KNOWLEDGE = {
    "sight": [("What does it mean to see?",
               "Seeing is using your eyes to know what is around you, like colors, shapes, and light.")],
    "borrow": [("What does borrow mean?",
                "Borrow means you take something that belongs to someone else and promise to give it back.")],
    "ghost": [("What is a ghost in a story?",
               "In stories, a ghost is a spirit that may be lonely or curious, often transparent and gentle.")],
    "promise": [("Why is a promise important?",
                 "A promise is a word you give that you will do something. Keeping a promise builds trust.")],
    "sharing": [("Why is sharing good?",
                 "Sharing means letting someone have part of what you have. It makes both people happy.")],
}
KNOWLEDGE_ORDER = ["sight", "borrow", "ghost", "promise", "sharing"]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, act = f["child"], f["ghost"], f["borrow_act"]
    traits = ', '.join(child.traits)
    qa = [
        QAItem(
            question=f"Who is the story about when {child.id} meets {ghost.id} at night?",
            answer=f"It is about a little {child.type} named {child.id} and a ghost named {ghost.id}. "
                   f"{child.id} is {traits} and lives in {world.setting.place}."
        ),
        QAItem(
            question=f"What did {ghost.id} want to borrow from {child.id}?",
            answer=f"{ghost.id} wanted to {act.verb} from {child.id} to see the beautiful night world. "
                   f"He was mesmerized by the sights he had never seen."
        ),
        QAItem(
            question=f"What happened when {ghost.id} did not want to give back what he borrowed?",
            answer=f"{ghost.id} kept the eyes too long, and {child.id} grew scared and cried out. "
                   f"The ghost felt a conflict between wanting to keep the beauty and keeping his promise."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {ghost.id} and {child.id} solve their problem?",
            answer=f"{ghost.id} returned the eyes and apologized. Then they agreed that "
                   f"{ghost.id} would always share what he saw by telling {child.id} about it. "
                   f"That way they enjoyed the world together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["borrow_act"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", borrow_act="eyes", gift="eyes",
                child_name="Elara", ghost_name="Wisp", child_gender="girl", trait="brave"),
    StoryParams(place="cottage", borrow_act="eyes", gift="eyes",
                child_name="Mira", ghost_name="Shade", child_gender="girl", trait="kind"),
    StoryParams(place="town", borrow_act="eyes", gift="eyes",
                child_name="Lena", ghost_name="Glimmer", child_gender="girl", trait="curious"),
]


ASP_RULES = r"""
valid(Place, A, G) :- setting(Place), borrow_act(A), gift(G).
"""


def asp_facts() -> str:
    import asp as _asp
    lines = []
    for pid in SETTINGS:
        lines.append(_asp.fact("setting", pid))
    for aid in BORROW_ACTS:
        lines.append(_asp.fact("borrow_act", aid))
    for gid in GIFTS:
        lines.append(_asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid/3."))
    return sorted(set(_asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story: borrowing eyes, sharing sight.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--borrow-act", choices=BORROW_ACTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--ghost-name")
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
              and (args.borrow_act is None or c[1] == args.borrow_act)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("No valid combination matches.")
    place, borrow_act, gift_id = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    child_gender = args.child_gender or "girl"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, borrow_act=borrow_act, gift=gift_id,
        child_name=child_name, ghost_name=ghost_name,
        child_gender=child_gender, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], BORROW_ACTS[params.borrow_act],
                 GIFTS[params.gift], params.child_name, params.child_gender,
                 [params.trait], params.ghost_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for place, act, gift in combos:
            print(f"  {place:9} {act:8} {gift:8}")
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
            header = f"### {p.child_name}: {p.borrow_act} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
